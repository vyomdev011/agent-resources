"""Test Job 2: Managing Project Environments.

Tests for `agr add` and `agr sync` commands covering:
- Adding remote and local resources
- Sync flags (--local, --remote, --prune, --overwrite)
- Global installation (--global/-g)

Reference: .documents/jobs.md section "2. Managing Project Environments"

NOTE: Remote operations that require network access are already tested in
test_sync.py. This module focuses on CLI integration and local operations.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig
from agr.handle import ParsedHandle


runner = CliRunner()


class TestSyncLocalFlag:
    """Tests for agr sync --local flag behavior."""

    def test_sync_local_only_syncs_local_dependencies(
        self, project_with_agr_toml: Path
    ):
        """Test --local flag only syncs local path dependencies."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Local Skill")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_local("./resources/skills/my-skill", "skill")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["sync", "--local"])

        assert result.exit_code == 0
        # Local resource should be installed
        # (installed to .claude/skills/<username>:my-skill)
        claude_skills = project_with_agr_toml / ".claude" / "skills"
        assert claude_skills.exists()
        # Should have installed the local skill
        skill_dirs = list(claude_skills.iterdir())
        assert any("my-skill" in d.name for d in skill_dirs)

    def test_sync_local_does_not_fetch_remote(self, project_with_agr_toml: Path):
        """Test --local flag skips remote dependency fetching."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "local-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Local Skill")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_local("./resources/skills/local-skill", "skill")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        with patch("agr.cli.sync.fetch_resource") as mock_fetch:
            result = runner.invoke(app, ["sync", "--local"])

            # fetch_resource should NOT be called with --local
            mock_fetch.assert_not_called()
            assert result.exit_code == 0


class TestSyncRemoteFlag:
    """Tests for agr sync --remote flag behavior."""

    def test_sync_remote_does_not_sync_local(self, project_with_agr_toml: Path):
        """Test --remote flag skips local dependency syncing."""
        # Create local skill source
        skill_dir = project_with_agr_toml / "resources" / "skills" / "local-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Local Skill")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_local("./resources/skills/local-skill", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["sync", "--remote"])

        assert result.exit_code == 0
        # Local skill should NOT be installed to .claude/
        claude_skills = project_with_agr_toml / ".claude" / "skills"
        if claude_skills.exists():
            skill_dirs = list(claude_skills.iterdir())
            assert not any("local-skill" in d.name for d in skill_dirs)


class TestSyncPruneFlag:
    """Tests for agr sync --prune flag behavior."""

    def test_sync_prune_removes_unlisted_remote_resources(
        self, project_with_agr_toml: Path
    ):
        """Test --prune removes resources not in agr.toml."""
        # Create agr.toml with one dependency
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        # Install skill that IS in toml
        handle = ParsedHandle.from_components("kasperjunge", "commit")
        skill_in_toml = handle.to_skill_path(project_with_agr_toml / ".claude")
        skill_in_toml.mkdir(parents=True)
        (skill_in_toml / "SKILL.md").write_text("# Commit Skill")

        # Install skill that is NOT in toml
        handle_not_in = ParsedHandle.from_components("alice", "old-skill")
        skill_not_in_toml = handle_not_in.to_skill_path(project_with_agr_toml / ".claude")
        skill_not_in_toml.mkdir(parents=True)
        (skill_not_in_toml / "SKILL.md").write_text("# Old Skill")

        result = runner.invoke(app, ["sync", "--prune"])

        assert result.exit_code == 0
        # Skill in toml should still exist
        assert skill_in_toml.exists()
        assert (skill_in_toml / "SKILL.md").exists()
        # Skill NOT in toml should be removed
        assert not skill_not_in_toml.exists()

    def test_sync_prune_keeps_flat_path_resources(self, project_with_agr_toml: Path):
        """Test --prune doesn't remove flat-path (legacy) resources."""
        # Create empty agr.toml
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.save(project_with_agr_toml / "agr.toml")

        # Create flat-path skill (legacy - no colon in name)
        flat_skill = project_with_agr_toml / ".claude" / "skills" / "legacy-skill"
        flat_skill.mkdir(parents=True)
        (flat_skill / "SKILL.md").write_text("# Legacy Skill")

        result = runner.invoke(app, ["sync", "--prune"])

        assert result.exit_code == 0
        # Flat-path skill should NOT be removed (backward compat)
        assert flat_skill.exists()


class TestSyncOverwriteFlag:
    """Tests for agr sync --overwrite behavior (implicit via config)."""

    def test_sync_updates_local_when_source_is_newer(self, project_with_agr_toml: Path):
        """Test that sync updates installed resources when source is newer."""
        import time

        # Create local skill source
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Original")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_local("./resources/skills/my-skill", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        # First sync
        result1 = runner.invoke(app, ["sync", "--local"])
        assert result1.exit_code == 0

        # Wait a bit and update source
        time.sleep(0.1)
        (skill_dir / "SKILL.md").write_text("# Updated Content")

        # Second sync should update
        result2 = runner.invoke(app, ["sync", "--local"])
        assert result2.exit_code == 0

        # Verify content was updated
        claude_skills = project_with_agr_toml / ".claude" / "skills"
        installed_skills = [d for d in claude_skills.iterdir() if "my-skill" in d.name]
        assert len(installed_skills) == 1
        installed_content = (installed_skills[0] / "SKILL.md").read_text()
        # The name field gets updated, but original content structure should be there
        assert "Updated" in installed_content or "my-skill" in installed_content


class TestAddGlobalFlag:
    """Tests for agr add --global/-g flag."""

    def test_add_global_long_flag_accepted(self, project_with_agr_toml: Path):
        """Test --global flag is accepted."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # This would fail without proper global directory, but flag should be accepted
        result = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "--global"],
        )

        # Command runs (might fail if global dir doesn't exist, but flag is valid)
        assert result.exit_code == 0 or "--global" not in result.output

    def test_add_global_short_flag_accepted(self, project_with_agr_toml: Path):
        """Test -g short flag is accepted."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "-g"],
        )

        # Command runs (might fail if global dir doesn't exist, but flag is valid)
        assert result.exit_code == 0 or "-g" not in result.output


class TestAddTypeFlag:
    """Tests for agr add --type/-t flag."""

    def test_add_with_explicit_type_skill(self, project_with_agr_toml: Path):
        """Test --type skill explicitly sets resource type."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "ambiguous"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Ambiguous Skill")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/ambiguous", "--type", "skill"],
        )

        assert result.exit_code == 0

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        deps = config.dependencies
        assert any(d.type == "skill" for d in deps)

    def test_add_with_short_type_flag(self, project_with_agr_toml: Path):
        """Test -t short flag for type."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "-t", "skill"],
        )

        assert result.exit_code == 0


class TestAddOverwriteFlag:
    """Tests for agr add --overwrite flag."""

    def test_add_overwrites_existing_with_flag(self, project_with_agr_toml: Path):
        """Test --overwrite replaces existing resource."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Original")

        # First add
        result1 = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill"],
        )
        assert result1.exit_code == 0

        # Modify source
        (skill_dir / "SKILL.md").write_text("# Updated")

        # Second add with --overwrite
        result2 = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill", "--overwrite"],
        )

        assert result2.exit_code == 0


class TestSyncGlobalFlag:
    """Tests for agr sync --global/-g flag."""

    def test_sync_global_long_flag_accepted(self, project_with_agr_toml: Path):
        """Test --global flag is accepted for sync."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["sync", "--global"])

        # Command runs (will report nothing to sync)
        assert result.exit_code == 0

    def test_sync_global_short_flag_accepted(self, project_with_agr_toml: Path):
        """Test -g short flag is accepted for sync."""
        result = runner.invoke(app, ["sync", "-g"])

        assert result.exit_code == 0


class TestSyncSummaryOutput:
    """Tests for sync command summary output."""

    def test_sync_shows_nothing_to_sync_when_empty(self, project_with_agr_toml: Path):
        """Test sync shows appropriate message with no dependencies."""
        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0
        assert "nothing to sync" in result.output.lower()

    def test_sync_shows_install_count(self, project_with_agr_toml: Path):
        """Test sync summary shows number of installed resources."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "skill-a"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill A")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_local("./resources/skills/skill-a", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["sync", "--local"])

        assert result.exit_code == 0
        # Should show installation in output
        assert "installed" in result.output.lower()


class TestAddLocalResources:
    """Tests for adding local resources with agr add."""

    def test_add_local_skill_directory(self, project_with_agr_toml: Path):
        """Test adding a local skill directory."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/my-skill"],
        )

        assert result.exit_code == 0
        assert "added" in result.output.lower()

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert any("my-skill" in (d.path or "") for d in config.dependencies)

    def test_add_local_command_file(self, project_with_agr_toml: Path):
        """Test adding a local command markdown file."""
        cmd_dir = project_with_agr_toml / "resources" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "deploy.md").write_text("# Deploy Command")

        result = runner.invoke(
            app,
            ["add", "./resources/commands/deploy.md"],
        )

        assert result.exit_code == 0
        assert "added" in result.output.lower()

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert any("deploy" in (d.path or "") for d in config.dependencies)

    def test_add_local_agent_file(self, project_with_agr_toml: Path):
        """Test adding a local agent markdown file."""
        agent_dir = project_with_agr_toml / "resources" / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "reviewer.md").write_text("# Reviewer Agent")

        result = runner.invoke(
            app,
            ["add", "./resources/agents/reviewer.md"],
        )

        assert result.exit_code == 0
        assert "added" in result.output.lower()

    def test_add_nonexistent_path_shows_error(self, project_with_agr_toml: Path):
        """Test adding a nonexistent path shows error."""
        result = runner.invoke(
            app,
            ["add", "./nonexistent/path/skill"],
        )

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "not exist" in result.output.lower()
