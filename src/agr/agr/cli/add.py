"""Add subcommand for agr - install resources from GitHub."""

from typing import Annotated

import typer

from agr.cli.common import handle_add_bundle, handle_add_resource
from agr.fetcher import ResourceType

app = typer.Typer(
    help="Add skills, commands, or agents from GitHub.",
    no_args_is_help=True,
)


@app.command("skill")
def add_skill(
    skill_ref: Annotated[
        str,
        typer.Argument(
            help="Skill reference: <username>/<skill-name> or <username>/<repo>/<skill-name>",
            metavar="REFERENCE",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing skill if it exists.",
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
) -> None:
    """Add a skill from a GitHub repository.

    REFERENCE format:
      - username/skill-name: installs from github.com/username/agent-resources
      - username/repo/skill-name: installs from github.com/username/repo

    Examples:
      agr add skill kasperjunge/hello-world
      agr add skill kasperjunge/my-repo/hello-world --global
    """
    handle_add_resource(skill_ref, ResourceType.SKILL, "skills", overwrite, global_install)


@app.command("command")
def add_command(
    command_ref: Annotated[
        str,
        typer.Argument(
            help="Command reference: <username>/<command-name> or <username>/<repo>/<command-name>",
            metavar="REFERENCE",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing command if it exists.",
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
) -> None:
    """Add a slash command from a GitHub repository.

    REFERENCE format:
      - username/command-name: installs from github.com/username/agent-resources
      - username/repo/command-name: installs from github.com/username/repo

    Examples:
      agr add command kasperjunge/hello
      agr add command kasperjunge/my-repo/hello --global
    """
    handle_add_resource(command_ref, ResourceType.COMMAND, "commands", overwrite, global_install)


@app.command("agent")
def add_agent(
    agent_ref: Annotated[
        str,
        typer.Argument(
            help="Agent reference: <username>/<agent-name> or <username>/<repo>/<agent-name>",
            metavar="REFERENCE",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing agent if it exists.",
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
) -> None:
    """Add a sub-agent from a GitHub repository.

    REFERENCE format:
      - username/agent-name: installs from github.com/username/agent-resources
      - username/repo/agent-name: installs from github.com/username/repo

    Examples:
      agr add agent kasperjunge/hello-agent
      agr add agent kasperjunge/my-repo/hello-agent --global
    """
    handle_add_resource(agent_ref, ResourceType.AGENT, "agents", overwrite, global_install)


@app.command("bundle")
def add_bundle(
    bundle_ref: Annotated[
        str,
        typer.Argument(
            help="Bundle reference: <username>/<bundle-name> or <username>/<repo>/<bundle-name>",
            metavar="REFERENCE",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing resources if they exist.",
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
) -> None:
    """Add a bundle of resources from a GitHub repository.

    A bundle installs all skills, commands, and agents from a named directory.

    REFERENCE format:
      - username/bundle-name: installs from github.com/username/agent-resources
      - username/repo/bundle-name: installs from github.com/username/repo

    Bundle structure in source repo:
      .claude/skills/{bundle-name}/*/SKILL.md     -> skills
      .claude/commands/{bundle-name}/*.md         -> commands
      .claude/agents/{bundle-name}/*.md           -> agents

    Resources are installed with the bundle name as a prefix:
      .claude/skills/{bundle-name}/{skill-name}/
      .claude/commands/{bundle-name}/{command-name}.md
      .claude/agents/{bundle-name}/{agent-name}.md

    Examples:
      agr add bundle kasperjunge/productivity
      agr add bundle kasperjunge/my-repo/productivity --global
    """
    handle_add_bundle(bundle_ref, overwrite, global_install)
