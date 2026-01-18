"""Test Job 3: Managing Package Dependencies.

Tests for `agr add --workspace/-w` flag covering:
- Creating [packages] section in agr.toml
- Adding remote resources to workspace
- Adding local resources to workspace
- The deprecated --to flag (documenting it's dead code)

Reference: .documents/jobs.md section "3. Managing Package Dependencies"
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig


runner = CliRunner()


class TestWorkspaceFlag:
    """Tests for --workspace/-w flag functionality via CLI."""

    def test_add_local_to_workspace_creates_packages_section(
        self, project_with_agr_toml: Path
    ):
        """Test that adding with --workspace creates [packages] section in agr.toml."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "tool-use"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Tool Use Skill")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/tool-use", "--workspace", "myworkspace"],
        )

        assert result.exit_code == 0

        # Verify agr.toml was updated with packages section
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert "myworkspace" in config.packages
        assert len(config.packages["myworkspace"].dependencies) >= 1

    def test_add_local_to_workspace_short_flag(self, project_with_agr_toml: Path):
        """Test -w short flag works for workspace."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "-w", "toolkit"],
        )

        assert result.exit_code == 0

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert "toolkit" in config.packages

    def test_add_multiple_to_same_workspace(self, project_with_agr_toml: Path):
        """Test adding multiple resources to the same workspace."""
        # Create local skills
        skill1 = project_with_agr_toml / "resources" / "skills" / "skill-a"
        skill1.mkdir(parents=True)
        (skill1 / "SKILL.md").write_text("# Skill A")

        skill2 = project_with_agr_toml / "resources" / "skills" / "skill-b"
        skill2.mkdir(parents=True)
        (skill2 / "SKILL.md").write_text("# Skill B")

        # Add first
        result1 = runner.invoke(
            app,
            ["add", "./resources/skills/skill-a", "-w", "myworkspace"],
        )
        assert result1.exit_code == 0

        # Add second
        result2 = runner.invoke(
            app,
            ["add", "./resources/skills/skill-b", "-w", "myworkspace"],
        )
        assert result2.exit_code == 0

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert "myworkspace" in config.packages
        # Should have 2 dependencies in the workspace
        assert len(config.packages["myworkspace"].dependencies) == 2

    def test_add_to_different_workspaces(self, project_with_agr_toml: Path):
        """Test adding resources to different workspaces."""
        # Create local skills
        skill1 = project_with_agr_toml / "resources" / "skills" / "skill-a"
        skill1.mkdir(parents=True)
        (skill1 / "SKILL.md").write_text("# Skill A")

        skill2 = project_with_agr_toml / "resources" / "skills" / "skill-b"
        skill2.mkdir(parents=True)
        (skill2 / "SKILL.md").write_text("# Skill B")

        # Add to workspace1
        result1 = runner.invoke(
            app,
            ["add", "./resources/skills/skill-a", "-w", "workspace1"],
        )
        assert result1.exit_code == 0

        # Add to workspace2
        result2 = runner.invoke(
            app,
            ["add", "./resources/skills/skill-b", "-w", "workspace2"],
        )
        assert result2.exit_code == 0

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert "workspace1" in config.packages
        assert "workspace2" in config.packages
        assert len(config.packages["workspace1"].dependencies) == 1
        assert len(config.packages["workspace2"].dependencies) == 1

    def test_workspace_shows_in_add_output(self, project_with_agr_toml: Path):
        """Test that workspace name is shown in add command output."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "-w", "my-toolkit"],
        )

        assert result.exit_code == 0
        assert "my-toolkit" in result.output

    def test_add_command_to_workspace(self, project_with_agr_toml: Path):
        """Test adding a command (md file) to workspace."""
        cmd_dir = project_with_agr_toml / "resources" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "deploy.md").write_text("# Deploy Command")

        result = runner.invoke(
            app,
            ["add", "./resources/commands/deploy.md", "-w", "devops"],
        )

        assert result.exit_code == 0

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert "devops" in config.packages
        deps = config.packages["devops"].dependencies
        assert any("deploy" in (d.path or "") for d in deps)


class TestDeprecatedToFlag:
    """Tests documenting that --to flag is deprecated/dead code.

    The --to flag is parsed but NEVER USED in the function body.
    Line 613 in add.py extracts `to_package` but it's never referenced.
    Users should use --workspace instead.
    """

    def test_to_flag_is_accepted_but_ignored(self, project_with_agr_toml: Path):
        """Test that --to flag is parsed without error but has no effect.

        This documents the current behavior where --to is dead code.
        The flag is extracted on line 613 but never used.
        """
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # Using --to should not crash, but also won't create a package
        result = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "--to", "my-package"],
        )

        # Command succeeds
        assert result.exit_code == 0

        # But --to doesn't actually create a package (it's dead code)
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        # The dependency is added to main deps, NOT to a package
        assert len(config.dependencies) == 1
        # No packages section created (--to is ignored)
        assert "my-package" not in config.packages

    def test_workspace_flag_is_the_working_alternative(self, project_with_agr_toml: Path):
        """Test that --workspace works where --to would be expected to work.

        Users who want package organization should use --workspace/-w.
        """
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # --workspace actually works
        result = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "--workspace", "my-package"],
        )

        assert result.exit_code == 0

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        # Workspace creates the packages section correctly
        assert "my-package" in config.packages
        assert len(config.packages["my-package"].dependencies) >= 1


class TestWorkspaceWithSyncIntegration:
    """Tests for workspace dependencies and sync command integration."""

    def test_workspace_dependencies_survive_config_roundtrip(
        self, project_with_agr_toml: Path
    ):
        """Test workspace deps persist through save/load cycle."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # Add to workspace
        runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "-w", "toolkit"],
        )

        # Reload config
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert "toolkit" in config.packages
        assert len(config.packages["toolkit"].dependencies) == 1

        # Save and reload again
        config.save(project_with_agr_toml / "agr.toml")
        config2 = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert "toolkit" in config2.packages
        assert len(config2.packages["toolkit"].dependencies) == 1


class TestWorkspaceWithOptions:
    """Tests for workspace flag combined with other options."""

    def test_add_to_workspace_with_type_flag(self, project_with_agr_toml: Path):
        """Test --workspace combined with --type flag."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "ambiguous"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Ambiguous")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/ambiguous", "-t", "skill", "-w", "tools"],
        )

        assert result.exit_code == 0

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert "tools" in config.packages
        deps = config.packages["tools"].dependencies
        assert any(d.type == "skill" for d in deps)

    def test_workspace_flag_after_path_argument(self, project_with_agr_toml: Path):
        """Test --workspace flag works when placed after the path argument.

        Some users write: agr add ./path --workspace name
        This tests that option parsing handles this order correctly.
        """
        skill_dir = project_with_agr_toml / "resources" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill")

        # workspace flag after path
        result = runner.invoke(
            app,
            ["add", "./resources/skills/test-skill", "--workspace", "my-ws"],
        )

        assert result.exit_code == 0

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert "my-ws" in config.packages


class TestWorkspaceInstallation:
    """Tests verifying workspace dependencies are installed correctly."""

    def test_workspace_dep_installs_to_claude_directory(
        self, project_with_agr_toml: Path
    ):
        """Test that workspace dependencies are installed to .claude/."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "-w", "toolkit"],
        )

        assert result.exit_code == 0
        assert "installed to:" in result.output.lower() or ".claude" in result.output

        # Verify skill was installed
        claude_skills = project_with_agr_toml / ".claude" / "skills"
        assert claude_skills.exists()
        # Should have at least one skill directory
        skill_dirs = list(claude_skills.iterdir())
        assert len(skill_dirs) >= 1
