<div align="center">

# 🧩 agent-resources

**Share and install Claude Code skills, commands, and agents with a single command.**

*Like pip or npm, but for Claude Code resources.*

[![PyPI](https://img.shields.io/pypi/v/agent-resources?color=blue)](https://pypi.org/project/agent-resources/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Get Started](#-get-started-in-30-seconds) • [Install Resources](#-install-any-resource) • [Share](#-share-with-others) • [Community](#-community-resources)

</div>

---

## 🚀 Get Started in 30 Seconds

Create your own shareable toolkit with one command:

```bash
uvx create-agent-resources-repo --github
```

**That's it.** You now have a GitHub repo with example resources that anyone can install.

> Requires [GitHub CLI](https://cli.github.com/). Or run without `--github` to set up manually.

### What You Get

- A ready-to-use `agent-resources` repo on your GitHub
- Example skill, command, and agent to learn from
- Instant shareability — tell others to run:

```bash
uvx add-skill <your-username>/hello-world
```

### Add Your Own Resources

Edit the files in your new repo:

```
your-username/agent-resources/
└── .claude/
    ├── skills/          # Skill folders with SKILL.md
    ├── commands/        # Slash command .md files
    └── agents/          # Sub-agent .md files
```

Push to GitHub. Done. No registry, no publishing step.

---

## ⚡ Try It Now

Want to see it in action first? Install a skill without any setup:

```bash
uvx add-skill kasperjunge/hello-world
```

The skill is now available in your Claude Code.

---

## 📦 Install Any Resource

```bash
uvx add-skill <username>/<skill-name>       # Skills
uvx add-command <username>/<command-name>   # Slash commands
uvx add-agent <username>/<agent-name>       # Sub-agents
```

**Options:**
- `--global` / `-g` — Install to `~/.claude/` (available in all projects)
- `--overwrite` — Replace existing resource

---

## 🌍 Share With Others

The best part: sharing is just a message.

> *"This skill saves me hours — try `uvx add-skill yourname/cool-skill`"*

**One command. Zero friction.** Anyone can install your resources instantly.

The more you share, the more the community grows. Every resource you publish makes Claude Code better for everyone.

---

## 🗂 Community Resources

*Coming soon — be the first!*

**Built something useful?** [Open an issue](https://github.com/kasperjunge/agent-resources-project/issues) with a link to your `agent-resources` repo and we'll add it here.

---

<div align="center">

**MIT License** · Made for the [Claude Code](https://claude.ai/code) community

</div>
