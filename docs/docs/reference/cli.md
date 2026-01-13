---
title: CLI reference
---

# CLI reference

## Global help

```bash
agr --help
```

## agr add

Add resources from GitHub.

### Commands

```bash
agr add skill <username>/<name>
agr add command <username>/<name>
agr add agent <username>/<name>
```

### Options

- `--global`, `-g`: install to `~/.claude/` instead of the current directory
- `--overwrite`: replace an existing resource

### Examples

```bash
agr add skill kasperjunge/hello-world
agr add command acme/tools/review --global
agr add agent acme/agents/test-writer --overwrite
```

### Custom repo name

```bash
agr add skill username/custom-repo/my-skill
```

### Nested paths

```bash
agr add skill username/backend:hello-world
```

### Bundles

Install all resources from a bundle (a named collection of skills, commands, and agents):

```bash
agr add bundle <username>/<bundle-name>
agr add bundle <username>/<repo>/<bundle-name>
```

Options:

- `--global`, `-g`: install to `~/.claude/` instead of the current directory
- `--overwrite`: replace existing resources

Examples:

```bash
agr add bundle kasperjunge/anthropic
agr add bundle kasperjunge/my-repo/productivity --global
```

## agr update

Re-fetch resources from GitHub to get the latest version.

### Commands

```bash
agr update skill <reference>
agr update command <reference>
agr update agent <reference>
```

### Options

- `--global`, `-g`: update in `~/.claude/` instead of the current directory

### Examples

```bash
agr update skill kasperjunge/hello-world
agr update command kasperjunge/my-repo/hello --global
agr update agent kasperjunge/hello-agent
```

### Bundles

```bash
agr update bundle <username>/<bundle-name>
agr update bundle <username>/<repo>/<bundle-name>
```

Options:

- `--global`, `-g`: update in `~/.claude/` instead of the current directory

Examples:

```bash
agr update bundle kasperjunge/anthropic
agr update bundle kasperjunge/my-repo/productivity --global
```

## agr remove

Remove resources from the local installation.

### Commands

```bash
agr remove skill <name>
agr remove command <name>
agr remove agent <name>
```

### Options

- `--global`, `-g`: remove from `~/.claude/` instead of the current directory

### Examples

```bash
agr remove skill hello-world
agr remove command hello --global
agr remove agent hello-agent
```

### Bundles

```bash
agr remove bundle <bundle-name>
```

Options:

- `--global`, `-g`: remove from `~/.claude/` instead of the current directory

Examples:

```bash
agr remove bundle anthropic
agr remove bundle productivity --global
```

!!! warning
    Resources are removed immediately without confirmation.

## agr init

Create scaffolds for repositories and resources.

### Create a repository

```bash
agr init repo
agr init repo my-resources
agr init repo .
```

Options:

- `--path`, `-p`: custom output path
- `--github`, `-g`: create a GitHub repo and push (requires `gh`)

### Create a skill

```bash
agr init skill my-skill
```

Options:

- `--path`, `-p`: custom output path

### Create a command

```bash
agr init command my-command
```

Options:

- `--path`, `-p`: custom output path

### Create an agent

```bash
agr init agent my-agent
```

Options:

- `--path`, `-p`: custom output path
