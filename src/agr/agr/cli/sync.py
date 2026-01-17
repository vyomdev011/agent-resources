"""Sync command for agr."""

import shutil
from pathlib import Path

import typer
from rich.console import Console

from agr.config import AgrConfig, find_config
from agr.exceptions import (
    AgrError,
    RepoNotFoundError,
    ResourceNotFoundError,
)
from agr.fetcher import (
    RESOURCE_CONFIGS,
    ResourceType,
    fetch_resource,
)
from agr.cli.common import (
    DEFAULT_REPO_NAME,
    fetch_spinner,
    get_base_path,
)

app = typer.Typer()
console = Console()


def _parse_dependency_ref(ref: str) -> tuple[str, str, str]:
    """
    Parse a dependency reference from agr.toml.

    Supports:
    - "username/name" -> username, DEFAULT_REPO_NAME, name
    - "username/repo/name" -> username, repo, name

    Returns:
        Tuple of (username, repo_name, resource_name)
    """
    parts = ref.split("/")
    if len(parts) == 2:
        return parts[0], DEFAULT_REPO_NAME, parts[1]
    elif len(parts) == 3:
        return parts[0], parts[1], parts[2]
    else:
        raise ValueError(f"Invalid dependency reference: {ref}")


def _is_resource_installed(
    username: str,
    name: str,
    resource_type: ResourceType,
    base_path: Path,
) -> bool:
    """Check if a resource is installed at the namespaced path."""
    config = RESOURCE_CONFIGS[resource_type]

    if config.is_directory:
        # Skills: .claude/skills/username/name/SKILL.md
        resource_path = base_path / config.dest_subdir / username / name
        return resource_path.is_dir() and (resource_path / "SKILL.md").exists()
    else:
        # Commands/Agents: .claude/commands/username/name.md
        resource_path = base_path / config.dest_subdir / username / f"{name}.md"
        return resource_path.is_file()


def _type_string_to_enum(type_str: str) -> ResourceType | None:
    """Convert type string to ResourceType enum, or None if unknown."""
    type_map = {
        "skill": ResourceType.SKILL,
        "command": ResourceType.COMMAND,
        "agent": ResourceType.AGENT,
    }
    return type_map.get(type_str.lower())


def _discover_installed_namespaced_resources(
    base_path: Path,
) -> set[str]:
    """
    Discover all installed namespaced resources.

    Returns set of dependency refs like "username/name".
    """
    installed = set()

    # Check skills
    skills_dir = base_path / "skills"
    if skills_dir.is_dir():
        for username_dir in skills_dir.iterdir():
            if username_dir.is_dir():
                for skill_dir in username_dir.iterdir():
                    if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                        installed.add(f"{username_dir.name}/{skill_dir.name}")

    # Check commands
    commands_dir = base_path / "commands"
    if commands_dir.is_dir():
        for username_dir in commands_dir.iterdir():
            if username_dir.is_dir():
                for cmd_file in username_dir.glob("*.md"):
                    installed.add(f"{username_dir.name}/{cmd_file.stem}")

    # Check agents
    agents_dir = base_path / "agents"
    if agents_dir.is_dir():
        for username_dir in agents_dir.iterdir():
            if username_dir.is_dir():
                for agent_file in username_dir.glob("*.md"):
                    installed.add(f"{username_dir.name}/{agent_file.stem}")

    return installed


def _cleanup_empty_parent(path: Path) -> None:
    """Remove the parent directory if it's empty."""
    parent = path.parent
    if parent.exists() and not any(parent.iterdir()):
        parent.rmdir()


def _remove_namespaced_resource(
    username: str,
    name: str,
    base_path: Path,
) -> None:
    """Remove a namespaced resource from disk."""
    # Try removing as skill (directory)
    skill_path = base_path / "skills" / username / name
    if skill_path.is_dir():
        shutil.rmtree(skill_path)
        _cleanup_empty_parent(skill_path)
        return

    # Try removing as command (file)
    command_path = base_path / "commands" / username / f"{name}.md"
    if command_path.is_file():
        command_path.unlink()
        _cleanup_empty_parent(command_path)
        return

    # Try removing as agent (file)
    agent_path = base_path / "agents" / username / f"{name}.md"
    if agent_path.is_file():
        agent_path.unlink()
        _cleanup_empty_parent(agent_path)


@app.command()
def sync(
    global_install: bool = typer.Option(
        False, "--global", "-g",
        help="Sync to global ~/.claude/ directory",
    ),
    prune: bool = typer.Option(
        False, "--prune",
        help="Remove resources not listed in agr.toml",
    ),
) -> None:
    """
    Synchronize installed resources with agr.toml.

    Installs any missing dependencies and optionally removes
    resources not listed in agr.toml.
    """
    # Find agr.toml
    config_path = find_config()
    if not config_path:
        console.print("[red]Error: No agr.toml found.[/red]")
        console.print("Run 'agr add <ref>' to create one, or create it manually.")
        raise typer.Exit(1)

    config = AgrConfig.load(config_path)
    base_path = get_base_path(global_install)

    # Track stats
    installed_count = 0
    skipped_count = 0
    failed_count = 0
    pruned_count = 0

    # Install missing dependencies
    for dep_ref, spec in config.dependencies.items():
        try:
            username, repo_name, name = _parse_dependency_ref(dep_ref)
        except ValueError as e:
            console.print(f"[yellow]Skipping invalid dependency '{dep_ref}': {e}[/yellow]")
            continue

        # Determine resource type
        resource_type = None
        if spec.type:
            resource_type = _type_string_to_enum(spec.type)

        # For now, default to skill if no type specified
        # In future, could auto-detect from repo
        if resource_type is None:
            resource_type = ResourceType.SKILL

        # Check if already installed
        if _is_resource_installed(username, name, resource_type, base_path):
            skipped_count += 1
            continue

        # Install the resource
        try:
            res_config = RESOURCE_CONFIGS[resource_type]
            dest = base_path / res_config.dest_subdir

            with fetch_spinner():
                fetch_resource(
                    username, repo_name, name, [name], dest, resource_type,
                    overwrite=False, username=username,
                )
            console.print(f"[green]Installed {resource_type.value} '{name}'[/green]")
            installed_count += 1
        except (RepoNotFoundError, ResourceNotFoundError, AgrError) as e:
            console.print(f"[red]Failed to install '{dep_ref}': {e}[/red]")
            failed_count += 1

    # Prune unlisted resources if requested
    if prune:
        # Get all dependencies as short refs (username/name)
        expected_refs = set()
        for dep_ref in config.dependencies.keys():
            try:
                username, _, name = _parse_dependency_ref(dep_ref)
                expected_refs.add(f"{username}/{name}")
            except ValueError:
                continue

        # Find installed namespaced resources
        installed_refs = _discover_installed_namespaced_resources(base_path)

        # Remove resources not in toml
        for ref in installed_refs:
            if ref not in expected_refs:
                parts = ref.split("/")
                if len(parts) == 2:
                    username, name = parts
                    _remove_namespaced_resource(username, name, base_path)
                    console.print(f"[yellow]Pruned '{ref}'[/yellow]")
                    pruned_count += 1

    # Print summary
    if installed_count > 0 or skipped_count > 0 or pruned_count > 0:
        parts = []
        if installed_count > 0:
            parts.append(f"{installed_count} installed")
        if skipped_count > 0:
            parts.append(f"{skipped_count} up-to-date")
        if pruned_count > 0:
            parts.append(f"{pruned_count} pruned")
        if failed_count > 0:
            parts.append(f"[red]{failed_count} failed[/red]")
        console.print(f"[dim]Sync complete: {', '.join(parts)}[/dim]")
    else:
        console.print("[dim]Nothing to sync.[/dim]")

    if failed_count > 0:
        raise typer.Exit(1)
