"""Add subcommand for agr - install resources from GitHub."""

from pathlib import Path
from typing import Annotated, List, Optional

import typer
from rich.console import Console

from agr.cli.common import handle_add_bundle, handle_add_resource, handle_add_unified
from agr.config import LocalResourceSpec, get_or_create_config
from agr.fetcher import ResourceType

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


def _detect_local_type(path: Path) -> str | None:
    """Detect resource type from a local path.

    Returns "skill", "command", or None if unknown.
    """
    if path.is_dir() and (path / "SKILL.md").exists():
        return "skill"
    if path.is_file() and path.suffix == ".md":
        return "command"
    return None


def handle_add_local(
    local_path: str,
    resource_type: str | None,
    package: str | None = None,
) -> None:
    """Handle adding a local resource to agr.toml."""
    path = Path(local_path)

    if not path.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(1)

    if not resource_type:
        resource_type = _detect_local_type(path)
        if not resource_type:
            console.print(
                f"[red]Error: Could not detect resource type for '{path}'.[/red]\n"
                "Use --type to specify: skill, command, or agent"
            )
            raise typer.Exit(1)

    name = path.stem if path.is_file() else path.name
    config_path, config = get_or_create_config()

    spec = LocalResourceSpec(path=local_path, type=resource_type, package=package)
    config.add_local(name, spec)
    config.save(config_path)

    console.print(f"[green]Added local {resource_type} '{name}' to agr.toml[/green]")
    console.print(f"  path: {local_path}")
    if package:
        console.print(f"  package: {package}")
    console.print("\n[dim]Run 'agr sync' to install to .claude/[/dim]")


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
            help="Explicit resource type: skill, command, agent, or bundle",
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
            help="Add local resource to a package namespace",
        ),
    ] = None,
) -> None:
    """Add a resource from a GitHub repository or local path.

    REFERENCE format:
      - username/name: installs from github.com/username/agent-resources
      - username/repo/name: installs from github.com/username/repo
      - ./path/to/resource: adds local path to agr.toml [local] section

    Auto-detects the resource type (skill, command, agent, or bundle).
    Use --type to explicitly specify when a name exists in multiple types.

    Examples:
      agr add kasperjunge/hello-world
      agr add kasperjunge/my-repo/hello-world --type skill
      agr add kasperjunge/productivity --global
      agr add ./custom/skill --type skill
      agr add ./scripts/deploy.md --type command --to my-toolkit
    """
    # Extract --type/-t and --to from args if captured there (happens when options come after ref)
    cleaned_args, resource_type, to_package = extract_options_from_args(args, resource_type, to_package)

    if not cleaned_args:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    first_arg = cleaned_args[0]

    # Handle local paths
    if _is_local_path(first_arg):
        handle_add_local(first_arg, resource_type, to_package)
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
