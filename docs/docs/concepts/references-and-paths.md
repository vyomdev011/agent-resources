---
title: References and paths
---

# References and paths

Resources are referenced by GitHub owner and name.

## Reference formats

Short form (default repo name `agent-resources`):

```
<username>/<resource-name>
```

Full form (custom repo name):

```
<username>/<repo>/<resource-name>
```

Examples:

```bash
agr add kasperjunge/hello-world
agr add acme/tools/review
```

## Nested resources with colons

A resource name may include `:` to represent nested folders:

```bash
agr add username/backend:hello-world
```

This maps to a resource at `.claude/skills/backend/hello-world/` in the source repository.

## How references become paths

When you install a resource, the reference determines where it goes:

| Reference | Installed path |
|-----------|----------------|
| `kasperjunge/hello-world` | `.claude/skills/kasperjunge/hello-world/` |
| `acme/tools/review` | `.claude/commands/acme/review.md` |

The username becomes a namespace directory, keeping resources organized by author.

## Using references with commands

All agr commands accept references in the same format:

```bash
# Add
agr add kasperjunge/hello-world

# Remove (can use just the name or full reference)
agr remove hello-world
agr remove kasperjunge/hello-world

# Run temporarily
agrx kasperjunge/hello-world
```
