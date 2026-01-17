---
title: CLI reference
---

# CLI reference

## Global help

```bash
agr --help
```

## agr add

Add resources from GitHub with auto-detection.

### Syntax

```bash
agr add <username>/<name>
agr add <username>/<repo>/<name>
```

The resource type (skill, command, agent, or bundle) is automatically detected.

### Options

- `--type`, `-t`: Explicit resource type (`skill`, `command`, `agent`, `bundle`)
- `--global`, `-g`: Install to `~/.claude/` instead of the current directory
- `--overwrite`: Replace an existing resource

### Examples

```bash
# Auto-detect resource type
agr add kasperjunge/hello-world

# From a custom repository
agr add acme/tools/review --global

# With explicit type (for disambiguation)
agr add kasperjunge/hello --type skill

# Nested paths
agr add username/backend:hello-world

# Bundles (auto-detected)
agr add kasperjunge/anthropic
```

### Where resources go

Resources install to namespaced paths organized by username:

```
.claude/
└── skills/
    └── kasperjunge/
        └── hello-world/
```

### Dependency tracking

When you add a resource, it's automatically recorded in `agr.toml`:

```toml
[dependencies]
"kasperjunge/hello-world" = {}
```

### Disambiguation

If the same name exists in multiple resource types, `agr add` will prompt you to use `--type`:

```
Error: Resource 'hello' found in multiple types: skill, command.
Use --type to specify which one to install:
  agr add kasperjunge/hello --type skill
  agr add kasperjunge/hello --type command
```

## agr sync

Synchronize installed resources with `agr.toml`.

### Syntax

```bash
agr sync
agr sync --prune
agr sync --global
```

### Options

- `--global`, `-g`: Sync resources in `~/.claude/` instead of the current directory
- `--prune`, `-p`: Remove namespaced resources not listed in `agr.toml`

### Examples

```bash
# Install missing resources from agr.toml
agr sync

# Install missing and remove unlisted resources
agr sync --prune

# Sync global resources
agr sync --global
```

### Behavior

| Scenario | Action |
|----------|--------|
| Resource in agr.toml, not installed | Installs the resource |
| Resource in agr.toml, already installed | Skips (no action) |
| Resource installed, not in agr.toml | Keeps (unless `--prune`) |
| `--prune` with unlisted resource | Removes namespaced resources only |

### Output

```
Syncing resources from agr.toml...
✓ Installed kasperjunge/hello-world (skill)
• Skipped madsnorgaard/drupal-expert (already installed)
✓ Pruned acme/old-resource

Summary: 1 installed, 1 skipped, 1 pruned, 0 failed
```

!!! note
    Pruning only affects resources in namespaced paths (e.g., `.claude/skills/username/`). Resources installed with older versions of agr in flat paths are preserved.

## agr update

Re-fetch resources from GitHub to get the latest version.

### Commands

```bash
agr update skill <reference>
agr update command <reference>
agr update agent <reference>
agr update bundle <reference>
```

### Options

- `--global`, `-g`: Update in `~/.claude/` instead of the current directory

### Examples

```bash
agr update skill kasperjunge/hello-world
agr update command kasperjunge/my-repo/hello --global
agr update agent kasperjunge/hello-agent
agr update bundle kasperjunge/anthropic
```

## agr remove

Remove resources from the local installation with auto-detection.

### Syntax

```bash
agr remove <name>
agr remove <username>/<name>
```

Auto-detects the resource type from installed files.

### Options

- `--type`, `-t`: Explicit resource type (`skill`, `command`, `agent`, `bundle`)
- `--global`, `-g`: Remove from `~/.claude/` instead of the current directory

### Examples

```bash
# Auto-detect resource type
agr remove hello-world

# Remove by full reference
agr remove kasperjunge/hello-world

# With explicit type (for disambiguation)
agr remove hello --type skill

# Remove from global installation
agr remove hello-world --global

# Remove a bundle
agr remove anthropic --type bundle
```

### Dependency tracking

When you remove a resource, it's automatically removed from `agr.toml`.

### Disambiguation

If the same name exists in multiple resource types, `agr remove` will prompt you to use `--type`:

```
Error: Resource 'hello' found in multiple types: skill, command.
Use --type to specify which one to remove:
  agr remove hello --type skill
  agr remove hello --type command
```

!!! warning
    Resources are removed immediately without confirmation.

## agrx

Run skills and commands temporarily without permanent installation.

### Syntax

```bash
agrx <username>/<name>
agrx <username>/<name> "<prompt>"
agrx <username>/<repo>/<name>
```

The resource type (skill or command) is automatically detected. The resource is downloaded, executed, and cleaned up afterwards.

### Options

- `--type`, `-t`: Explicit resource type (`skill` or `command`)
- `--interactive`, `-i`: Start an interactive Claude session
- `--global`, `-g`: Install temporarily to `~/.claude/` instead of `./.claude/`

### Examples

```bash
# Auto-detect and run
agrx kasperjunge/hello-world

# Run with a prompt
agrx kasperjunge/hello-world "analyze this code"

# Interactive mode
agrx kasperjunge/hello-world -i

# With explicit type
agrx kasperjunge/hello --type skill

# From a custom repository
agrx acme/tools/review
```

### Disambiguation

If the same name exists as both a skill and a command, `agrx` will prompt you to use `--type`:

```
Error: Resource 'hello' found in multiple types: skill, command.
Use --type to specify which one to run:
  agrx kasperjunge/hello --type skill
  agrx kasperjunge/hello --type command
```

## agr init

Create scaffolds for repositories and resources.

### Create a repository

```bash
agr init repo
agr init repo my-resources
agr init repo .
```

Options:

- `--path`, `-p`: Custom output path
- `--github`, `-g`: Create a GitHub repo and push (requires `gh`)

### Create a skill

```bash
agr init skill my-skill
```

Options:

- `--path`, `-p`: Custom output path

### Create a command

```bash
agr init command my-command
```

Options:

- `--path`, `-p`: Custom output path

### Create an agent

```bash
agr init agent my-agent
```

Options:

- `--path`, `-p`: Custom output path

## Deprecated syntax

The old subcommand syntax is deprecated but still works:

```bash
# Deprecated (shows warning)
agr add skill <username>/<name>
agr add command <username>/<name>
agr add agent <username>/<name>
agr add bundle <username>/<name>

agr remove skill <name>
agr remove command <name>
agr remove agent <name>
agr remove bundle <name>

agrx skill <username>/<name>
agrx command <username>/<name>

# Use instead
agr add <username>/<name>
agr remove <name>
agrx <username>/<name>
```
