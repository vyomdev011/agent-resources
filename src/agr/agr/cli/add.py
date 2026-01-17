"""Add subcommand for agr - install resources from GitHub."""

import glob
import shutil
from pathlib import Path
from typing import Annotated, List, Optional

import typer
from rich.console import Console

from agr.cli.common import handle_add_bundle, handle_add_resource, handle_add_unified, get_base_path
from agr.config import Dependency, get_or_create_config
from agr.fetcher import ResourceType
from agr.github import get_username_from_git_remote

console = Console()

# Deprecated subcommand names
DEPRECATED_SUBCOMMANDS = {"skill", "command", "agent", "bundle"}

# Mapping for deprecated subcommands to their handlers
DEPRECATED_TYPE_HANDLERS = {
    "skill": (ResourceType.SKILL, "skills"),
    "command": (ResourceType.COMMAND, "commands"),
    "agent": (ResourceType.AGENT, "agents"),
}


def extract_options_from_args(
    args: list[str] | None,
    explicit_type: str | None,
    explicit_to: str | None,
) -> tuple[list[str], str | None, str | None]:
    """Extract --type/-t and --to options from args list if present.

    When options appear after the resource reference, Typer captures them
    as part of the variadic args list. This function extracts them.
    """
    if not args:
        return [], explicit_type, explicit_to

    cleaned_args = []
    resource_type = explicit_type
    to_package = explicit_to

    i = 0
    while i < len(args):
        arg = args[i]
        has_next = i + 1 < len(args)

        if arg in ("--type", "-t") and has_next and resource_type is None:
            resource_type = args[i + 1]
            i += 2
        elif arg == "--to" and has_next and to_package is None:
            to_package = args[i + 1]
            i += 2
        else:
            cleaned_args.append(arg)
            i += 1

    return cleaned_args, resource_type, to_package

def _is_local_path(ref: str) -> bool:
    """Check if a reference is a local path."""
    return ref.startswith(("./", "/", "../"))


def _is_glob_pattern(ref: str) -> bool:
    """Check if a reference contains glob patterns."""
    return "*" in ref or "?" in ref or "[" in ref


def _detect_local_type(path: Path) -> str | None:
    """Detect resource type from a local path.

    Returns "skill", "command", "agent", "package", or None if unknown.
    Auto-detects based on:
    - Directory with SKILL.md -> skill
    - File with .md extension -> command (or agent if in agents/ dir)
    - Directory in packages/ -> package
    - Directory with skills/, commands/, or agents/ subdirs -> package
    """
    path_str = str(path)

    # Check if in packages/ directory
    if "packages/" in path_str or path_str.startswith("packages"):
        if path.is_dir():
            # Check if it's a package directory (has subdirs for resources)
            has_subdirs = any(
                (path / d).is_dir() for d in ["skills", "commands", "agents"]
            )
            if has_subdirs:
                return "package"
            # Might be a skill inside a package
            if (path / "SKILL.md").exists():
                return "skill"
        return "package"

    # Check for skill directory
    if path.is_dir() and (path / "SKILL.md").exists():
        return "skill"

    # Check for command/agent file
    if path.is_file() and path.suffix == ".md":
        # Detect agent vs command from parent directory name
        if path.parent.name == "agents" or "agents/" in path_str:
            return "agent"
        return "command"

    # Check for package directory
    if path.is_dir():
        has_subdirs = any(
            (path / d).is_dir() for d in ["skills", "commands", "agents"]
        )
        if has_subdirs:
            return "package"

    return None


def _find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def _install_local_resource(
    source_path: Path,
    resource_type: str,
    username: str,
    base_path: Path,
) -> None:
    """Install a local resource to .claude/ directory.

    Args:
        source_path: Path to the source resource
        resource_type: Type of resource (skill, command, agent, package)
        username: Username for namespacing
        base_path: Base .claude/ path
    """
    type_to_subdir = {
        "skill": "skills",
        "command": "commands",
        "agent": "agents",
        "package": "packages",
    }
    subdir = type_to_subdir.get(resource_type, "skills")

    if resource_type == "skill" or resource_type == "package":
        # Skills and packages are directories
        name = source_path.name
        dest_path = base_path / subdir / username / name
    else:
        # Commands and agents are files
        name = source_path.stem
        dest_path = base_path / subdir / username / f"{name}.md"

    # Remove existing if present
    if dest_path.exists():
        if dest_path.is_dir():
            shutil.rmtree(dest_path)
        else:
            dest_path.unlink()

    # Create parent directories
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy resource
    if source_path.is_dir():
        shutil.copytree(source_path, dest_path)
    else:
        shutil.copy2(source_path, dest_path)


def handle_add_local(
    local_path: str,
    resource_type: str | None,
    global_install: bool = False,
) -> None:
    """Handle adding a local resource to agr.toml and installing to .claude/."""
    path = Path(local_path)

    if not path.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(1)

    if not resource_type:
        resource_type = _detect_local_type(path)
        if not resource_type:
            console.print(
                f"[red]Error: Could not detect resource type for '{path}'.[/red]\n"
                "Use --type to specify: skill, command, agent, or package"
            )
            raise typer.Exit(1)

    name = path.stem if path.is_file() else path.name

    # Get username for namespacing
    repo_root = _find_repo_root()
    username = get_username_from_git_remote(repo_root)
    if not username:
        username = "local"

    # Add to agr.toml
    config_path, config = get_or_create_config()
    config.add_local(local_path, resource_type)
    config.save(config_path)

    # Install to .claude/
    base_path = get_base_path(global_install)
    _install_local_resource(path, resource_type, username, base_path)

    console.print(f"[green]Added local {resource_type} '{name}'[/green]")
    console.print(f"  path: {local_path}")
    console.print(f"  installed to: .claude/{resource_type}s/{username}/{name}")


def handle_add_glob(
    pattern: str,
    resource_type: str | None,
    global_install: bool = False,
) -> None:
    """Handle adding multiple local resources via glob pattern.

    Args:
        pattern: Glob pattern like "./commands/*.md"
        resource_type: Optional explicit resource type
        global_install: If True, install to ~/.claude/
    """
    # Expand glob pattern
    matches = list(glob.glob(pattern, recursive=True))

    if not matches:
        console.print(f"[red]Error: No files match pattern: {pattern}[/red]")
        raise typer.Exit(1)

    # Filter to only existing files/dirs
    paths = [Path(m) for m in matches if Path(m).exists()]

    if not paths:
        console.print(f"[red]Error: No valid paths match pattern: {pattern}[/red]")
        raise typer.Exit(1)

    console.print(f"Found {len(paths)} matching path(s)")

    # Get username for namespacing
    repo_root = _find_repo_root()
    username = get_username_from_git_remote(repo_root)
    if not username:
        username = "local"

    config_path, config = get_or_create_config()
    base_path = get_base_path(global_install)

    added_count = 0
    for path in paths:
        # Detect or use explicit type
        detected_type = resource_type or _detect_local_type(path)
        if not detected_type:
            console.print(f"[yellow]Skipping '{path}': Could not detect type[/yellow]")
            continue

        # Make path relative for storage
        try:
            rel_path = path.relative_to(Path.cwd())
            path_str = f"./{rel_path}"
        except ValueError:
            path_str = str(path)

        # Add to config
        config.add_local(path_str, detected_type)

        # Install to .claude/
        _install_local_resource(path, detected_type, username, base_path)

        name = path.stem if path.is_file() else path.name
        console.print(f"[green]Added {detected_type} '{name}'[/green]")
        added_count += 1

    # Save config
    config.save(config_path)

    console.print(f"\n[dim]Added {added_count} resource(s) to agr.toml[/dim]")


app = typer.Typer(
    help="Add skills, commands, or agents from GitHub.",
)


@app.callback(invoke_without_command=True)
def add_unified(
    ctx: typer.Context,
    args: Annotated[
        Optional[List[str]],
        typer.Argument(help="Resource reference and optional arguments"),
    ] = None,
    resource_type: Annotated[
        Optional[str],
        typer.Option(
            "--type",
            "-t",
            help="Explicit resource type: skill, command, agent, package, or bundle",
        ),
    ] = None,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing resource if it exists.",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
    to_package: Annotated[
        Optional[str],
        typer.Option(
            "--to",
            help="(Deprecated) Add local resource to a package namespace",
        ),
    ] = None,
) -> None:
    """Add a resource from a GitHub repository or local path.

    REFERENCE format:
      - username/name: installs from github.com/username/agent-resources
      - username/repo/name: installs from github.com/username/repo
      - ./path/to/resource: adds local path and installs to .claude/
      - ./path/*.md: glob pattern to add multiple resources

    Auto-detects the resource type (skill, command, agent, package, or bundle).
    Use --type to explicitly specify when needed.

    Examples:
      agr add kasperjunge/hello-world
      agr add kasperjunge/my-repo/hello-world --type skill
      agr add kasperjunge/productivity --global
      agr add ./skills/my-skill
      agr add ./commands/deploy.md
      agr add ./commands/*.md
      agr add ./packages/my-toolkit --type package
    """
    # Extract --type/-t and --to from args if captured there (happens when options come after ref)
    cleaned_args, resource_type, to_package = extract_options_from_args(args, resource_type, to_package)

    if not cleaned_args:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    first_arg = cleaned_args[0]

    # Handle glob patterns
    if _is_local_path(first_arg) and _is_glob_pattern(first_arg):
        handle_add_glob(first_arg, resource_type, global_install)
        return

    # Handle local paths
    if _is_local_path(first_arg):
        handle_add_local(first_arg, resource_type, global_install)
        return

    # Handle deprecated subcommand syntax: agr add skill <ref>
    if first_arg in DEPRECATED_SUBCOMMANDS:
        _handle_deprecated_add(first_arg, cleaned_args, overwrite, global_install)
        return

    # Normal unified add: agr add <ref>
    handle_add_unified(first_arg, resource_type, overwrite, global_install)


def _handle_deprecated_add(
    subcommand: str,
    args: list[str],
    overwrite: bool,
    global_install: bool,
) -> None:
    """Handle deprecated agr add <type> <ref> syntax."""
    if len(args) < 2:
        console.print(f"[red]Error: Missing resource reference after '{subcommand}'.[/red]")
        raise typer.Exit(1)

    resource_ref = args[1]
    console.print(
        f"[yellow]Warning: 'agr add {subcommand}' is deprecated. "
        f"Use 'agr add {resource_ref}' instead.[/yellow]"
    )

    if subcommand == "bundle":
        handle_add_bundle(resource_ref, overwrite, global_install)
        return

    res_type, subdir = DEPRECATED_TYPE_HANDLERS[subcommand]
    handle_add_resource(resource_ref, res_type, subdir, overwrite, global_install)
