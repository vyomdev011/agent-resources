---
title: Introduction
---

# Introduction

Agent Resources (agr) is a CLI for installing, managing, and sharing Claude Code resources from GitHub.
It lets you pull skills, slash commands, and subagents into your local `.claude/` folder with a
single command—and track them as project dependencies.

## Highlights

- **Install resources instantly** — Add skills, commands, and agents from GitHub with one command
- **Track dependencies** — Declare resources in `agr.toml` and sync across machines
- **Organized by default** — Resources install to namespaced paths that prevent conflicts
- **Auto-detection** — No need to specify resource types; agr figures it out
- **Share easily** — Create and publish your own resources with `agr init`

## Quick start

No install required:

```bash
uvx agr add kasperjunge/hello-world
```

Install permanently:

```bash
pip install agr
agr add kasperjunge/hello-world
```

The resource type (skill, command, agent, or bundle) is auto-detected.

## Where resources go

Resources install to organized, namespaced paths:

```
./
└── .claude/
    ├── skills/
    │   └── kasperjunge/
    │       └── hello-world/
    ├── commands/
    │   └── kasperjunge/
    │       └── review.md
    └── agents/
        └── kasperjunge/
            └── expert.md
```

Or globally with `--global`:

```
~/
└── .claude/
    └── ...
```

## Track your dependencies

**New in v0.4.0:** agr automatically tracks resources in `agr.toml`:

```toml
[dependencies]
"kasperjunge/hello-world" = {}
"madsnorgaard/drupal-expert" = { type = "skill" }
```

Sync your resources on any machine:

```bash
agr sync
```

## How it works

Resources are fetched from GitHub repositories that follow a simple layout:

```
agent-resources/
└── .claude/
    ├── skills/
    ├── commands/
    └── agents/
```

By default, `agr add` looks in a repository named `agent-resources` on the user's GitHub account.
If a repo has a different name, include it in the reference:

```bash
agr add username/custom-repo/resource-name
```

## Next steps

- Start with [Installation](getting-started/installation.md)
- Follow [First steps](getting-started/first-steps.md) for a complete walkthrough
- Learn about [Managing dependencies](guides/managing-dependencies.md) with `agr.toml`
- Browse full CLI details in [CLI reference](reference/cli.md)
