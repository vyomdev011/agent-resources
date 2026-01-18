"""List command for agr - show installed dependencies."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from agr.config import AgrConfig, Dependency, find_config
from agr.cli.common import TYPE_TO_SUBDIR, console, find_repo_root, get_base_path
from agr.github import get_username_from_git_remote
from agr.utils import compute_flattened_skill_name, compute_path_segments_from_skill_path

app = typer.Typer(
    help="List installed dependencies from agr.toml.",
)


def _is_installed(dep: Dependency, base_path: Path, username: str) -> bool:
    """Check if a dependency is installed in .claude/.

    Uses centralized handle module for consistent path construction
    between add/remove/list operations.
    """
    from agr.handle import parse_handle, toml_handle_to_skill_dirname

    subdir = TYPE_TO_SUBDIR.get(dep.type, "skills")

    if dep.is_local and dep.path:
        # Local dependency - check if installed
        source_path = Path(dep.path)

        if dep.type in ("skill", "package"):
            # Skills use flattened colon-namespaced directory names
            # e.g., .claude/skills/kasperjunge:commit/
            path_segments = compute_path_segments_from_skill_path(source_path)
            flattened_name = compute_flattened_skill_name(username, path_segments)
            installed_path = base_path / subdir / flattened_name
            return installed_path.is_dir()
        else:
            # Commands/agents use nested paths: .claude/commands/username/name.md
            name = source_path.stem if source_path.is_file() else source_path.name
            installed_path = base_path / subdir / username / f"{name}.md"
            return installed_path.is_file()

    elif dep.is_remote and dep.handle:
        # Remote dependency - use centralized handle parsing
        parsed = parse_handle(dep.handle)

        if dep.type == "skill":
            # Skills use flattened colon-namespaced directory names
            # e.g., .claude/skills/dsjacobsen:golang-pro/
            skill_dirname = toml_handle_to_skill_dirname(dep.handle)
            installed_path = base_path / subdir / skill_dirname
            return installed_path.is_dir() and (installed_path / "SKILL.md").exists()
        else:
            # Commands/agents use nested paths
            if parsed.username:
                installed_path = base_path / subdir / parsed.username / f"{parsed.simple_name}.md"
                return installed_path.is_file()

    return False


def _format_table(
    deps: list[Dependency],
    base_path: Path,
    username: str,
) -> Table:
    """Format dependencies as a rich table."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Source", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Handle/Path", style="white")
    table.add_column("Status", style="green")

    for dep in deps:
        source = "local" if dep.is_local else "remote"
        identifier = dep.path if dep.is_local else dep.handle
        installed = _is_installed(dep, base_path, username)
        status = "[green]installed[/green]" if installed else "[red]not installed[/red]"

        table.add_row(source, dep.type, identifier or "", status)

    return table


def _format_simple(
    deps: list[Dependency],
    base_path: Path,
    username: str,
) -> str:
    """Format dependencies as simple text."""
    lines = []
    for dep in deps:
        identifier = dep.path if dep.is_local else dep.handle
        installed = _is_installed(dep, base_path, username)
        status = "installed" if installed else "not installed"
        lines.append(f"{identifier} ({dep.type}) - {status}")
    return "\n".join(lines)


def _format_json(
    deps: list[Dependency],
    base_path: Path,
    username: str,
) -> str:
    """Format dependencies as JSON."""
    data = []
    for dep in deps:
        installed = _is_installed(dep, base_path, username)
        entry = {
            "type": dep.type,
            "source": "local" if dep.is_local else "remote",
            "installed": installed,
        }
        if dep.path:
            entry["path"] = dep.path
        if dep.handle:
            entry["handle"] = dep.handle
        data.append(entry)
    return json.dumps(data, indent=2)


@app.callback(invoke_without_command=True)
def list_dependencies(
    ctx: typer.Context,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: table, simple, or json",
        ),
    ] = "table",
    local_only: Annotated[
        bool,
        typer.Option(
            "--local",
            help="Only show local dependencies",
        ),
    ] = False,
    remote_only: Annotated[
        bool,
        typer.Option(
            "--remote",
            help="Only show remote dependencies",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Check installation in ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """List all dependencies from agr.toml with their install status.

    Shows both local path dependencies and remote GitHub dependencies.

    Examples:
      agr list                  # Show all dependencies as table
      agr list --format json    # Output as JSON
      agr list --local          # Show only local dependencies
      agr list --remote         # Show only remote dependencies
    """
    config_path = find_config()
    if not config_path:
        console.print("[dim]No agr.toml found. Nothing to list.[/dim]")
        console.print("[dim]Use 'agr add' to add dependencies first.[/dim]")
        return

    config = AgrConfig.load(config_path)

    if not config.dependencies:
        console.print("[dim]No dependencies in agr.toml.[/dim]")
        console.print("[dim]Use 'agr add' to add dependencies.[/dim]")
        return

    # Filter dependencies
    deps = config.dependencies
    if local_only:
        deps = config.get_local_dependencies()
    elif remote_only:
        deps = config.get_remote_dependencies()

    if not deps:
        console.print("[dim]No matching dependencies found.[/dim]")
        return

    # Get base path and username for install status check
    base_path = get_base_path(global_install)
    repo_root = find_repo_root()
    username = get_username_from_git_remote(repo_root) or "local"

    # Format output
    if format == "json":
        console.print(_format_json(deps, base_path, username))
    elif format == "simple":
        console.print(_format_simple(deps, base_path, username))
    else:
        table = _format_table(deps, base_path, username)
        console.print(table)

    # Summary
    total = len(deps)
    installed = sum(1 for d in deps if _is_installed(d, base_path, username))
    console.print(f"\n[dim]{installed}/{total} installed[/dim]")
