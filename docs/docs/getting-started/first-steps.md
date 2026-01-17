---
title: First steps
---

# First steps

This page gets you from zero to a working resource in your project.

## Install a resource

```bash
agr add kasperjunge/hello-world
```

The resource type (skill, command, agent, or bundle) is auto-detected. Resources install to namespaced paths organized by username:

```
./
└── .claude/
    └── skills/
        └── kasperjunge/
            └── hello-world/
```

This organization prevents naming conflicts when you install resources from different authors.

## Track your dependencies

When you add a resource, agr automatically records it in `agr.toml`:

```toml
[dependencies]
"kasperjunge/hello-world" = {}
```

Commit this file to version control to share your project's resource dependencies with your team.

## Use your resource

Once installed, your agent can use the new skill automatically and you can run slash commands
inside Claude Code. No additional configuration is required.

## Common options

```bash
# Install globally instead of in the current repo
agr add kasperjunge/hello-world --global

# Overwrite an existing resource
agr add kasperjunge/hello-world --overwrite

# Specify type explicitly (if a name exists in multiple types)
agr add kasperjunge/hello-world --type skill
```

## Run without installing (agrx)

Try a resource without permanent installation:

```bash
agrx kasperjunge/hello-world              # Auto-detects and runs
agrx kasperjunge/hello-world "my prompt"  # Run with a prompt
```

The resource is downloaded, executed, and cleaned up automatically.

## Sync resources from agr.toml

If you clone a project with an `agr.toml` file, install all declared resources:

```bash
agr sync
```

This installs any resources listed in `agr.toml` that aren't already present.

## Remove a resource

```bash
agr remove hello-world
```

Auto-detects the resource type and removes the dependency from `agr.toml`. Use `--type` to disambiguate if needed.

## Next steps

- Learn more in [Installing resources](../guides/installing-resources.md)
- Understand dependency management in [Managing dependencies](../guides/managing-dependencies.md)
- See repository layouts in [Repository structure](../concepts/repository-structure.md)
