---
title: Bundles
---

# Bundles

A bundle is a named collection of skills, commands, and agents that can be installed together with a single command.

## Installing a bundle

```bash
agr add bundle <username>/<bundle-name>
```

For example:

```bash
agr add bundle kasperjunge/anthropic
```

This installs all skills, commands, and agents from the `anthropic` bundle.

### From a custom repository

```bash
agr add bundle <username>/<repo>/<bundle-name>
```

### Options

- `--global`, `-g`: install to `~/.claude/` instead of the current directory
- `--overwrite`: replace existing resources if they exist

## Updating a bundle

Re-fetch all resources in a bundle to get the latest versions:

```bash
agr update bundle kasperjunge/anthropic
```

## Removing a bundle

Remove all resources from a bundle:

```bash
agr remove bundle anthropic
```

## Creating a bundle

To create a bundle, organize your resources into directories with the same name under each resource type.

### Bundle structure

```
your-repo/
└── .claude/
    ├── skills/
    │   └── my-bundle/           # Bundle name
    │       ├── skill-one/       # First skill
    │       │   └── SKILL.md
    │       └── skill-two/       # Second skill
    │           └── SKILL.md
    ├── commands/
    │   └── my-bundle/           # Same bundle name
    │       ├── cmd-one.md
    │       └── cmd-two.md
    └── agents/
        └── my-bundle/           # Same bundle name
            └── my-agent.md
```

The bundle name (`my-bundle` in this example) must be the same across all three resource types.

### Example

Here's a real bundle structure for a "productivity" bundle:

```
.claude/
├── skills/
│   └── productivity/
│       ├── task-manager/
│       │   └── SKILL.md
│       └── note-taker/
│           └── SKILL.md
├── commands/
│   └── productivity/
│       ├── daily-standup.md
│       └── weekly-review.md
└── agents/
    └── productivity/
        └── planner.md
```

Users can then install everything with:

```bash
agr add bundle yourname/productivity
```

### Partial bundles

You don't need all three resource types. A bundle can contain any combination:

- Skills only
- Commands only
- Agents only
- Any combination of the above

If a resource type directory doesn't exist for your bundle name, it's simply skipped during installation.

## How resources are installed

When a bundle is installed, resources keep the bundle name as a prefix:

| Source | Installed to |
|--------|--------------|
| `.claude/skills/my-bundle/skill-one/` | `.claude/skills/my-bundle/skill-one/` |
| `.claude/commands/my-bundle/cmd.md` | `.claude/commands/my-bundle/cmd.md` |
| `.claude/agents/my-bundle/agent.md` | `.claude/agents/my-bundle/agent.md` |

This keeps bundle resources organized and prevents naming conflicts with other resources.
