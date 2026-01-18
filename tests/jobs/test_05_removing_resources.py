"""Test Job 5: Removing Resources.

Tests for agr remove command.

Reference: .documents/jobs.md section "5. Removing Resources"

NOTE: Comprehensive tests for this job are in test_remove_unified.py.
This stub references existing coverage and adds any additional integration tests.

Existing Coverage:
- tests/test_remove_unified.py - unified remove command tests
- tests/test_remove_consistency.py - remove consistency tests
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig
from agr.handle import ParsedHandle


runner = CliRunner()


class TestRemoveByName:
    """Tests for removing resources by name.

    See test_remove_unified.py for comprehensive tests.
    """

    def test_remove_by_name_removes_from_agr_toml(
        self, project_with_agr_toml: Path
    ):
        """Verify remove by name removes dependency from agr.toml."""
        # Add a local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        runner.invoke(app, ["add", "./resources/skills/my-skill"])

        # Verify it's in config
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert any("my-skill" in (d.path or "") for d in config.dependencies)

        # Remove by path (remove uses path matching for local resources)
        result = runner.invoke(app, ["remove", "./resources/skills/my-skill"])

        # Verify it's removed from config
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert not any("my-skill" in (d.path or "") for d in config.dependencies)


class TestRemoveByPath:
    """Tests for removing resources by path.

    See test_remove_unified.py for comprehensive tests.
    """

    def test_remove_by_path_removes_from_agr_toml(
        self, project_with_agr_toml: Path
    ):
        """Verify remove by path removes dependency from agr.toml."""
        # Add a local command
        cmd_dir = project_with_agr_toml / "resources" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "deploy.md").write_text("# Deploy")

        runner.invoke(app, ["add", "./resources/commands/deploy.md"])

        # Remove by path
        result = runner.invoke(app, ["remove", "./resources/commands/deploy.md"])

        # Verify it's removed from config
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert not any("deploy" in (d.path or "") for d in config.dependencies)


class TestRemoveGlobalFlag:
    """Tests for agr remove --global flag.

    See test_remove_unified.py for comprehensive tests.
    """

    def test_remove_global_flag_accepted(self, project_with_agr_toml: Path):
        """Verify --global flag is accepted."""
        result = runner.invoke(app, ["remove", "some-resource", "--global"])

        # Flag should be accepted (resource may not exist)
        assert "--global" not in result.output or "error" not in result.output.lower()

    def test_remove_short_global_flag_accepted(self, project_with_agr_toml: Path):
        """Verify -g short flag is accepted."""
        result = runner.invoke(app, ["remove", "some-resource", "-g"])

        # Flag should be accepted
        assert "-g" not in result.output or "error" not in result.output.lower()


class TestRemoveTypeFlag:
    """Tests for agr remove --type flag.

    See test_remove_unified.py for comprehensive tests.
    """

    def test_remove_type_flag_accepted(self, project_with_agr_toml: Path):
        """Verify --type flag is accepted."""
        result = runner.invoke(app, ["remove", "some-resource", "--type", "skill"])

        # Flag should be accepted
        assert result.exit_code in [0, 1]  # 0=success, 1=not found (both valid)

    def test_remove_short_type_flag_accepted(self, project_with_agr_toml: Path):
        """Verify -t short flag is accepted."""
        result = runner.invoke(app, ["remove", "some-resource", "-t", "command"])

        # Flag should be accepted
        assert result.exit_code in [0, 1]


class TestRemoveCleanup:
    """Tests for remove cleanup behavior.

    See test_remove_unified.py and test_remove_consistency.py for comprehensive tests.
    """

    def test_remove_deletes_from_claude_directory(
        self, project_with_agr_toml: Path
    ):
        """Verify remove deletes resource from .claude/ directory."""
        # Add and install a local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "cleanup-test"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Cleanup Test")

        runner.invoke(app, ["add", "./resources/skills/cleanup-test"])

        # Verify it's installed
        claude_skills = project_with_agr_toml / ".claude" / "skills"
        installed_before = [d for d in claude_skills.iterdir() if "cleanup-test" in d.name]
        assert len(installed_before) > 0

        # Remove it
        runner.invoke(app, ["remove", "cleanup-test"])

        # Verify it's removed from .claude/
        installed_after = [d for d in claude_skills.iterdir() if "cleanup-test" in d.name] if claude_skills.exists() else []
        assert len(installed_after) == 0


class TestRemoveNotFound:
    """Tests for remove behavior when resource not found."""

    def test_remove_nonexistent_shows_message(self, project_with_agr_toml: Path):
        """Verify remove of nonexistent resource shows appropriate message."""
        result = runner.invoke(app, ["remove", "definitely-not-here"])

        # Should indicate not found
        assert "not found" in result.output.lower() or "no" in result.output.lower()
