"""Tests for init authoring commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app


runner = CliRunner()


class TestInitCallback:
    """Tests for agr init (no subcommand) - shows usage info."""

    def test_init_shows_usage_info(self, tmp_path: Path, monkeypatch):
        """Test that agr init shows usage information without creating dirs."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        # Should show usage info, not create directories
        assert "agr init skill" in result.output
        assert "agr init command" in result.output
        assert "agr init agent" in result.output
        assert "agr init package" in result.output

        # Should NOT create convention directories automatically
        assert not (tmp_path / "skills").exists()
        assert not (tmp_path / "commands").exists()
        assert not (tmp_path / "agents").exists()
        assert not (tmp_path / "packages").exists()

    def test_init_mentions_automatic_dir_creation(self, tmp_path: Path, monkeypatch):
        """Test that agr init mentions dirs are created automatically."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "automatically" in result.output.lower()


class TestInitSkillAuthoring:
    """Tests for agr init skill with authoring paths."""

    def test_init_skill_uses_authoring_path_by_default(self, tmp_path: Path, monkeypatch):
        """Test that skill is created in ./skills/ by default."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init", "skill", "my-skill"])

        assert result.exit_code == 0
        assert (tmp_path / "skills" / "my-skill" / "SKILL.md").exists()

    def test_init_skill_creates_skills_dir(self, tmp_path: Path, monkeypatch):
        """Test that init skill creates skills/ directory if it doesn't exist."""
        monkeypatch.chdir(tmp_path)

        # skills/ doesn't exist yet
        assert not (tmp_path / "skills").exists()

        result = runner.invoke(app, ["init", "skill", "my-skill"])

        assert result.exit_code == 0
        assert (tmp_path / "skills").is_dir()
        assert (tmp_path / "skills" / "my-skill" / "SKILL.md").exists()

    def test_init_skill_legacy_uses_claude_path(self, tmp_path: Path, monkeypatch):
        """Test that --legacy creates in .claude/skills/."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init", "skill", "my-skill", "--legacy"])

        assert result.exit_code == 0
        assert (tmp_path / ".claude" / "skills" / "my-skill" / "SKILL.md").exists()

    def test_init_skill_custom_path(self, tmp_path: Path, monkeypatch):
        """Test that --path overrides default."""
        monkeypatch.chdir(tmp_path)
        custom_path = tmp_path / "custom"

        result = runner.invoke(app, ["init", "skill", "my-skill", "--path", str(custom_path)])

        assert result.exit_code == 0
        assert (custom_path / "SKILL.md").exists()


class TestInitCommandAuthoring:
    """Tests for agr init command with authoring paths."""

    def test_init_command_uses_authoring_path_by_default(self, tmp_path: Path, monkeypatch):
        """Test that command is created in ./commands/ by default."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init", "command", "my-cmd"])

        assert result.exit_code == 0
        assert (tmp_path / "commands" / "my-cmd.md").exists()

    def test_init_command_creates_commands_dir(self, tmp_path: Path, monkeypatch):
        """Test that init command creates commands/ directory if it doesn't exist."""
        monkeypatch.chdir(tmp_path)

        # commands/ doesn't exist yet
        assert not (tmp_path / "commands").exists()

        result = runner.invoke(app, ["init", "command", "my-cmd"])

        assert result.exit_code == 0
        assert (tmp_path / "commands").is_dir()
        assert (tmp_path / "commands" / "my-cmd.md").exists()

    def test_init_command_legacy_uses_claude_path(self, tmp_path: Path, monkeypatch):
        """Test that --legacy creates in .claude/commands/."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init", "command", "my-cmd", "--legacy"])

        assert result.exit_code == 0
        assert (tmp_path / ".claude" / "commands" / "my-cmd.md").exists()


class TestInitAgentAuthoring:
    """Tests for agr init agent with authoring paths."""

    def test_init_agent_uses_authoring_path_by_default(self, tmp_path: Path, monkeypatch):
        """Test that agent is created in ./agents/ by default."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init", "agent", "my-agent"])

        assert result.exit_code == 0
        assert (tmp_path / "agents" / "my-agent.md").exists()

    def test_init_agent_creates_agents_dir(self, tmp_path: Path, monkeypatch):
        """Test that init agent creates agents/ directory if it doesn't exist."""
        monkeypatch.chdir(tmp_path)

        # agents/ doesn't exist yet
        assert not (tmp_path / "agents").exists()

        result = runner.invoke(app, ["init", "agent", "my-agent"])

        assert result.exit_code == 0
        assert (tmp_path / "agents").is_dir()
        assert (tmp_path / "agents" / "my-agent.md").exists()

    def test_init_agent_legacy_uses_claude_path(self, tmp_path: Path, monkeypatch):
        """Test that --legacy creates in .claude/agents/."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init", "agent", "my-agent", "--legacy"])

        assert result.exit_code == 0
        assert (tmp_path / ".claude" / "agents" / "my-agent.md").exists()


class TestInitPackage:
    """Tests for agr init package command."""

    def test_init_package_creates_structure(self, tmp_path: Path, monkeypatch):
        """Test that package creates skills/, commands/, agents/ subdirs."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init", "package", "my-toolkit"])

        assert result.exit_code == 0
        pkg_path = tmp_path / "packages" / "my-toolkit"
        assert pkg_path.is_dir()
        assert (pkg_path / "skills").is_dir()
        assert (pkg_path / "commands").is_dir()
        assert (pkg_path / "agents").is_dir()

    def test_init_package_creates_packages_dir(self, tmp_path: Path, monkeypatch):
        """Test that init package creates packages/ directory if it doesn't exist."""
        monkeypatch.chdir(tmp_path)

        # packages/ doesn't exist yet
        assert not (tmp_path / "packages").exists()

        result = runner.invoke(app, ["init", "package", "my-toolkit"])

        assert result.exit_code == 0
        assert (tmp_path / "packages").is_dir()

    def test_init_package_custom_path(self, tmp_path: Path, monkeypatch):
        """Test that --path overrides default package location."""
        monkeypatch.chdir(tmp_path)
        custom_path = tmp_path / "libs" / "utils"

        result = runner.invoke(app, ["init", "package", "my-toolkit", "--path", str(custom_path)])

        assert result.exit_code == 0
        assert custom_path.is_dir()
        assert (custom_path / "skills").is_dir()
        assert (custom_path / "commands").is_dir()
        assert (custom_path / "agents").is_dir()

    def test_init_package_errors_if_exists(self, tmp_path: Path, monkeypatch):
        """Test that init package errors if directory exists."""
        monkeypatch.chdir(tmp_path)

        # Create existing package
        (tmp_path / "packages" / "my-toolkit").mkdir(parents=True)

        result = runner.invoke(app, ["init", "package", "my-toolkit"])

        assert result.exit_code == 1
        assert "already exists" in result.output
