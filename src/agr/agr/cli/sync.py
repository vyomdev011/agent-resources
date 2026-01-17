"""Sync command for agr."""

import shutil
from pathlib import Path

import typer
from rich.console import Console

from agr.config import AgrConfig, find_config
from agr.discovery import discover_local_resources
from agr.exceptions import AgrError, RepoNotFoundError, ResourceNotFoundError
from agr.fetcher import RESOURCE_CONFIGS, ResourceType, fetch_resource
from agr.github import get_username_from_git_remote
from agr.local_sync import sync_local_resources
from agr.cli.common import DEFAULT_REPO_NAME, fetch_spinner, get_base_path

app = typer.Typer()
console = Console()

# Mapping from type string to ResourceType enum
TYPE_STRING_TO_ENUM = {
    "skill": ResourceType.SKILL,
    "command": ResourceType.COMMAND,
    "agent": ResourceType.AGENT,
}


def _parse_dependency_ref(ref: str) -> tuple[str, str, str]:
    """Parse a dependency reference from agr.toml.

    Supports:
    - "username/name" -> username, DEFAULT_REPO_NAME, name
    - "username/repo/name" -> username, repo, name
    """
    parts = ref.split("/")
    if len(parts) == 2:
        return parts[0], DEFAULT_REPO_NAME, parts[1]
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
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
    return TYPE_STRING_TO_ENUM.get(type_str.lower())


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


def _remove_path(path: Path) -> None:
    """Remove a file or directory and clean up empty parent."""
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()
    else:
        return
    _cleanup_empty_parent(path)


def _remove_namespaced_resource(username: str, name: str, base_path: Path) -> None:
    """Remove a namespaced resource from disk."""
    # Try each resource type in order
    paths_to_try = [
        base_path / "skills" / username / name,
        base_path / "commands" / username / f"{name}.md",
        base_path / "agents" / username / f"{name}.md",
    ]

    for path in paths_to_try:
        if path.exists():
            _remove_path(path)
            return


def _find_repo_root() -> Path | None:
    """Find the repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def _sync_local_authoring_resources(base_path: Path, prune: bool) -> tuple[int, int, int, int]:
    """Sync local authoring resources to .claude directory.

    Returns:
        Tuple of (installed, updated, pruned, failed) counts
    """
    repo_root = _find_repo_root() or Path.cwd()

    username = get_username_from_git_remote(repo_root)
    if not username:
        console.print("[yellow]Warning: Could not determine username from git remote.[/yellow]")
        console.print("[yellow]Using 'local' as namespace. Configure git remote for proper namespacing.[/yellow]")
        username = "local"

    context = discover_local_resources(repo_root)
    if context.is_empty:
        return (0, 0, 0, 0)

    result = sync_local_resources(
        context=context,
        username=username,
        base_path=base_path,
        root_path=repo_root,
        prune=prune,
    )

    # Print results
    for name in result.installed:
        console.print(f"[green]Installed local resource '{name}'[/green]")
    for name in result.updated:
        console.print(f"[blue]Updated local resource '{name}'[/blue]")
    for name in result.removed:
        console.print(f"[yellow]Pruned local resource '{name}'[/yellow]")
    for name, error in result.errors:
        console.print(f"[red]Failed to sync '{name}': {error}[/red]")

    return (
        len(result.installed),
        len(result.updated),
        len(result.removed),
        len(result.errors),
    )


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
    local_only: bool = typer.Option(
        False, "--local",
        help="Only sync local authoring resources (skills/, commands/, etc.)",
    ),
    remote_only: bool = typer.Option(
        False, "--remote",
        help="Only sync remote dependencies from agr.toml",
    ),
) -> None:
    """Synchronize installed resources with agr.toml and local authoring paths.

    By default, syncs both local resources (skills/, commands/, agents/, packages/)
    and remote dependencies from agr.toml.

    Use --local to only sync local authoring resources.
    Use --remote to only sync remote dependencies.
    """
    base_path = get_base_path(global_install)
    total_installed, total_updated, total_pruned, total_failed = 0, 0, 0, 0

    # Sync local authoring resources
    if not remote_only:
        installed, updated, pruned, failed = _sync_local_authoring_resources(base_path, prune)
        total_installed += installed
        total_updated += updated
        total_pruned += pruned
        total_failed += failed

    # Sync remote dependencies
    if not local_only:
        config_path = find_config()
        if config_path:
            config = AgrConfig.load(config_path)
            installed, _skipped, failed, pruned = _sync_remote_dependencies(config, base_path, prune)
            total_installed += installed
            total_pruned += pruned
            total_failed += failed
        elif not remote_only:
            console.print("[dim]No agr.toml found. Skipping remote dependencies.[/dim]")

    # Print summary
    _print_sync_summary(total_installed, total_updated, total_pruned, total_failed)

    if total_failed > 0:
        raise typer.Exit(1)


def _print_sync_summary(installed: int, updated: int, pruned: int, failed: int) -> None:
    """Print a summary of sync results."""
    if not (installed or updated or pruned or failed):
        console.print("[dim]Nothing to sync.[/dim]")
        return

    parts = []
    if installed:
        parts.append(f"{installed} installed")
    if updated:
        parts.append(f"{updated} updated")
    if pruned:
        parts.append(f"{pruned} pruned")
    if failed:
        parts.append(f"[red]{failed} failed[/red]")
    console.print(f"[dim]Sync complete: {', '.join(parts)}[/dim]")


def _sync_remote_dependencies(
    config: AgrConfig,
    base_path: Path,
    prune: bool,
) -> tuple[int, int, int, int]:
    """Sync remote dependencies from agr.toml.

    Returns:
        Tuple of (installed, skipped, failed, pruned) counts
    """
    installed_count, skipped_count, failed_count, pruned_count = 0, 0, 0, 0

    for dep_ref, spec in config.dependencies.items():
        try:
            username, repo_name, name = _parse_dependency_ref(dep_ref)
        except ValueError as e:
            console.print(f"[yellow]Skipping invalid dependency '{dep_ref}': {e}[/yellow]")
            continue

        resource_type = _type_string_to_enum(spec.type) if spec.type else ResourceType.SKILL

        if _is_resource_installed(username, name, resource_type, base_path):
            skipped_count += 1
            continue

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

    if prune:
        pruned_count = _prune_unlisted_remote_resources(config, base_path)

    return (installed_count, skipped_count, failed_count, pruned_count)


def _prune_unlisted_remote_resources(config: AgrConfig, base_path: Path) -> int:
    """Remove installed resources that are not in the config."""
    expected_refs = set()
    for dep_ref in config.dependencies.keys():
        try:
            username, _, name = _parse_dependency_ref(dep_ref)
            expected_refs.add(f"{username}/{name}")
        except ValueError:
            continue

    installed_refs = _discover_installed_namespaced_resources(base_path)
    pruned_count = 0

    for ref in installed_refs:
        if ref not in expected_refs:
            parts = ref.split("/")
            if len(parts) == 2:
                username, name = parts
                _remove_namespaced_resource(username, name, base_path)
                console.print(f"[yellow]Pruned '{ref}'[/yellow]")
                pruned_count += 1

    return pruned_count
