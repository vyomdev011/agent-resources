---
title: Installing resources
---

# Installing resources

Install skills, commands, and agents directly from GitHub.

## Install from the default repo name

If a user has a repo named `agent-resources`, you only need the username:

```bash
agr add username/my-resource
```

The resource type (skill, command, agent, or bundle) is auto-detected.

## Install from a custom repo name

If the repo name is not `agent-resources`, include it:

```bash
agr add username/custom-repo/my-resource
```

## How resources are organized

Resources install to namespaced paths organized by username:

```
./
└── .claude/
    ├── skills/
    │   └── username/
    │       └── my-skill/
    ├── commands/
    │   └── username/
    │       └── my-command.md
    └── agents/
        └── username/
            └── my-agent.md
```

This organization:

- **Prevents naming conflicts** — Two authors can both have a resource named `review`
- **Shows ownership** — You can see who created each resource
- **Keeps things tidy** — Resources from the same author are grouped together

## Install nested resources

You can organize resources into nested folders and reference them with `:`.
For example, this installs from a nested path in the source repo:

```bash
agr add username/backend:hello-world
```

The resource installs with the full nested structure preserved.

## Install globally

Global installs go to `~/.claude/` instead of the current project:

```bash
agr add username/my-resource --global
```

Global resources are available in all your projects.

## Overwrite an existing resource

```bash
agr add username/my-resource --overwrite
```

## Disambiguate resource types

If the same name exists in multiple types (e.g., both a skill and a command named `hello`), use the `--type` flag:

```bash
agr add username/hello --type skill
agr add username/hello --type command
```

Valid types: `skill`, `command`, `agent`, `bundle`

## Automatic dependency tracking

When you install a resource, agr automatically adds it to `agr.toml`:

```toml
[dependencies]
"username/my-resource" = {}
```

This lets you:

- Share your project's dependencies with your team
- Reinstall everything with `agr sync`
- Keep track of what's installed

See [Managing dependencies](managing-dependencies.md) for more details.

## Verify the install

Check that files exist in `.claude/` or `~/.claude/`:

```bash
ls .claude/skills/
ls .claude/commands/
ls .claude/agents/
```

Then run your command or let your agent use the skill automatically.
