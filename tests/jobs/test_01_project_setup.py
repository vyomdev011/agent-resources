"""Test Job 1: Project & Package Setup.

Tests for project initialization and resource scaffolding.

Reference: .documents/jobs.md section "1. Project & Package Setup"

NOTE: Comprehensive tests for this job are in test_init_authoring.py.
This stub references existing coverage and adds any additional integration tests.

Existing Coverage:
- tests/test_init_authoring.py::TestInitSimplified - agr init basic functionality
- tests/test_init_authoring.py::TestInitSkillAuthoring - skill scaffolding
- tests/test_init_authoring.py::TestInitCommandAuthoring - command scaffolding
- tests/test_init_authoring.py::TestInitAgentAuthoring - agent scaffolding
- tests/test_init_authoring.py::TestInitPackage - package scaffolding
- tests/test_init_authoring.py::TestInitPathInName - path detection in name
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app


runner = CliRunner()


class TestProjectInitialization:
    """Tests for agr init project setup.

    See test_init_authoring.py::TestInitSimplified for comprehensive tests.
    """

    def test_init_creates_agr_toml(self, project_with_git: Path):
        """Verify agr init creates agr.toml file."""
        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert (project_with_git / "agr.toml").exists()

    def test_init_creates_resources_directory_structure(self, project_with_git: Path):
        """Verify agr init creates conventional directory structure."""
        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        resources = project_with_git / "resources"
        assert resources.exists()
        assert (resources / "skills").exists()
        assert (resources / "commands").exists()
        assert (resources / "agents").exists()
        assert (resources / "packages").exists()


class TestResourceScaffolding:
    """Tests for resource scaffolding commands.

    See test_init_authoring.py for comprehensive scaffolding tests.
    """

    def test_init_skill_creates_skill_md(self, project_with_git: Path):
        """Verify agr init skill creates SKILL.md template."""
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init", "skill", "my-skill"])

        assert result.exit_code == 0
        skill_md = project_with_git / "resources" / "skills" / "my-skill" / "SKILL.md"
        assert skill_md.exists()

    def test_init_command_creates_md_file(self, project_with_git: Path):
        """Verify agr init command creates .md template."""
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init", "command", "my-command"])

        assert result.exit_code == 0
        cmd_md = project_with_git / "resources" / "commands" / "my-command.md"
        assert cmd_md.exists()

    def test_init_agent_creates_md_file(self, project_with_git: Path):
        """Verify agr init agent creates .md template."""
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init", "agent", "my-agent"])

        assert result.exit_code == 0
        agent_md = project_with_git / "resources" / "agents" / "my-agent.md"
        assert agent_md.exists()

    def test_init_package_creates_structure(self, project_with_git: Path):
        """Verify agr init package creates package structure."""
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init", "package", "my-toolkit"])

        assert result.exit_code == 0
        pkg_path = project_with_git / "resources" / "packages" / "my-toolkit"
        assert pkg_path.exists()
        assert (pkg_path / "skills").exists()
        assert (pkg_path / "commands").exists()
        assert (pkg_path / "agents").exists()


class TestCustomPathOption:
    """Tests for --path option in scaffolding.

    See test_init_authoring.py for comprehensive path option tests.
    """

    def test_init_skill_with_custom_path(self, project_with_git: Path):
        """Verify --path option overrides default skill location."""
        custom_path = project_with_git / "custom" / "location"

        result = runner.invoke(
            app,
            ["init", "skill", "my-skill", "--path", str(custom_path)]
        )

        assert result.exit_code == 0
        assert (custom_path / "SKILL.md").exists()


class TestLegacyOption:
    """Tests for --legacy option in scaffolding.

    See test_init_authoring.py for comprehensive legacy option tests.
    """

    def test_init_skill_legacy_uses_claude_directory(self, project_with_git: Path):
        """Verify --legacy creates in .claude/ instead of resources/."""
        result = runner.invoke(app, ["init", "skill", "legacy-skill", "--legacy"])

        assert result.exit_code == 0
        assert (project_with_git / ".claude" / "skills" / "legacy-skill" / "SKILL.md").exists()
