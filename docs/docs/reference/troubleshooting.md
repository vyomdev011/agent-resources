---
title: Troubleshooting
---

# Troubleshooting

## Repository not found

If you see an error about a missing repository, check:

- The GitHub username and repo name are correct
- The repository is public
- The default branch is `main`

## Resource not found

If agr reports that a resource does not exist, confirm the path in the repo:

- Skills: `.claude/skills/<name>/SKILL.md`
- Commands: `.claude/commands/<name>.md`
- Agents: `.claude/agents/<name>.md`

If you use nested paths, verify the folder structure matches the `:` segments.

## Resource already exists

If the destination exists, rerun with `--overwrite`:

```bash
agr add username/my-skill --overwrite
```

## Ambiguous resource type

If you see an error about multiple resource types:

```
Error: Resource 'hello' found in multiple types: skill, command.
```

Use `--type` to specify which one you want:

```bash
agr add username/hello --type skill
```

## agr.toml not found

`agr sync` requires an `agr.toml` file. If you don't have one:

- Run `agr add` to create one automatically
- Or create `agr.toml` manually:

```toml
[dependencies]
"username/my-resource" = {}
```

## Sync not installing resources

If `agr sync` skips resources that should be installed:

- Check that the resources are listed in `agr.toml`
- Verify the reference format is correct (`username/name` or `username/repo/name`)
- Resources already installed are skipped (this is expected behavior)

## Prune not removing resources

`agr sync --prune` only removes resources in namespaced paths:

- Resources at `.claude/skills/username/resource/` will be pruned
- Resources at `.claude/skills/resource/` (flat paths from older versions) are preserved

This preserves backward compatibility with older installations.

## Network errors

agr downloads from GitHub. Ensure you have network access and try again.
