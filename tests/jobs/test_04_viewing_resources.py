"""Test Job 4: Viewing & Inspecting Resources.

Tests for `agr list` command covering:
- Listing all dependencies from agr.toml
- Output formats (table, simple, json)
- Filtering (--local, --remote)
- Global flag (--global/-g)
- Installation status display

Reference: .documents/jobs.md section "4. Viewing & Inspecting Resources"
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig
from agr.handle import ParsedHandle


runner = CliRunner()


class TestAgrListFormats:
    """Tests for agr list output formats."""

    def test_list_default_shows_table_format(self, project_with_agr_toml: Path):
        """Test that default output is table format with columns."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        # Table format shows headers
        assert "Source" in result.output or "Type" in result.output or "Handle" in result.output
        assert "kasperjunge/commit" in result.output

    def test_list_format_simple_shows_plain_text(self, project_with_agr_toml: Path):
        """Test --format simple produces plain text output."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.add_remote("alice/helper", "command")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "--format", "simple"])

        assert result.exit_code == 0
        assert "kasperjunge/commit" in result.output
        assert "alice/helper" in result.output
        assert "(skill)" in result.output
        assert "(command)" in result.output

    def test_list_format_json_produces_valid_json(self, project_with_agr_toml: Path):
        """Test --format json produces valid, parseable JSON."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "--format", "json"])

        assert result.exit_code == 0
        # Parse JSON from output (skip summary line)
        lines = result.output.strip().split("\n")
        # Find the JSON array (skip lines that aren't part of JSON)
        json_lines = []
        in_json = False
        for line in lines:
            if line.strip().startswith("["):
                in_json = True
            if in_json:
                json_lines.append(line)
            if line.strip() == "]":
                break

        json_str = "\n".join(json_lines)
        data = json.loads(json_str)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["handle"] == "kasperjunge/commit"
        assert data[0]["type"] == "skill"

    def test_list_format_json_structure_validation(self, project_with_agr_toml: Path):
        """Test JSON output structure includes all expected fields."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "local-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Local Skill")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.add_local("./resources/skills/local-skill", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "--format", "json"])

        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            if line.strip().startswith("["):
                in_json = True
            if in_json:
                json_lines.append(line)
            if line.strip() == "]":
                break

        data = json.loads("\n".join(json_lines))
        assert len(data) == 2

        # Check remote entry structure
        remote = next(d for d in data if d.get("source") == "remote")
        assert "type" in remote
        assert "source" in remote
        assert "installed" in remote
        assert "handle" in remote

        # Check local entry structure
        local = next(d for d in data if d.get("source") == "local")
        assert "type" in local
        assert "source" in local
        assert "installed" in local
        assert "path" in local


class TestAgrListFilters:
    """Tests for agr list filtering options."""

    def test_list_local_flag_shows_only_local_dependencies(
        self, project_with_agr_toml: Path
    ):
        """Test --local filter shows only local path dependencies."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.add_local("./resources/skills/my-skill", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "--local"])

        assert result.exit_code == 0
        assert "./resources/skills/my-skill" in result.output
        assert "kasperjunge/commit" not in result.output

    def test_list_remote_flag_shows_only_remote_dependencies(
        self, project_with_agr_toml: Path
    ):
        """Test --remote filter shows only remote GitHub dependencies."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.add_local("./resources/skills/my-skill", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "--remote"])

        assert result.exit_code == 0
        assert "kasperjunge/commit" in result.output
        assert "./resources/skills/my-skill" not in result.output

    def test_list_local_with_no_local_deps_shows_message(
        self, project_with_agr_toml: Path
    ):
        """Test --local with no local dependencies shows appropriate message."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "--local"])

        assert result.exit_code == 0
        assert "no matching dependencies" in result.output.lower()

    def test_list_remote_with_no_remote_deps_shows_message(
        self, project_with_agr_toml: Path
    ):
        """Test --remote with no remote dependencies shows appropriate message."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_local("./resources/skills/my-skill", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "--remote"])

        assert result.exit_code == 0
        assert "no matching dependencies" in result.output.lower()


class TestAgrListGlobal:
    """Tests for agr list --global flag."""

    def test_list_global_short_flag_works(self, project_with_agr_toml: Path):
        """Test -g short flag is accepted."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "-g"])

        # Should run without error (even if nothing installed globally)
        assert result.exit_code == 0

    def test_list_global_long_flag_works(self, project_with_agr_toml: Path):
        """Test --global long flag is accepted."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "--global"])

        assert result.exit_code == 0


class TestAgrListInstallStatus:
    """Tests for agr list installation status display."""

    def test_list_shows_installed_status_when_resource_exists(
        self, project_with_agr_toml: Path
    ):
        """Test that installed resources show 'installed' status."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        # Install the skill
        handle = ParsedHandle.from_components("kasperjunge", "commit")
        skill_path = handle.to_skill_path(project_with_agr_toml / ".claude")
        skill_path.mkdir(parents=True)
        (skill_path / "SKILL.md").write_text("# Commit Skill")

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "installed" in result.output.lower()
        # Should NOT show "not installed" for this one
        output_lines = result.output.lower().split("\n")
        commit_line = next(l for l in output_lines if "kasperjunge/commit" in l)
        assert "not installed" not in commit_line

    def test_list_shows_not_installed_status_when_resource_missing(
        self, project_with_agr_toml: Path
    ):
        """Test that missing resources show 'not installed' status."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        # Do NOT install the skill

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "not installed" in result.output.lower()

    def test_list_shows_summary_count(self, project_with_agr_toml: Path):
        """Test that list shows N/M installed summary."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.add_remote("kasperjunge/missing", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        # Install only one
        handle = ParsedHandle.from_components("kasperjunge", "commit")
        skill_path = handle.to_skill_path(project_with_agr_toml / ".claude")
        skill_path.mkdir(parents=True)
        (skill_path / "SKILL.md").write_text("# Commit Skill")

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        # Should show "1/2 installed" or similar
        assert "1/2" in result.output

    def test_list_json_includes_installed_boolean(self, project_with_agr_toml: Path):
        """Test JSON output includes installed boolean for each entry."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("kasperjunge/commit", "skill")
        config.add_remote("alice/helper", "command")
        config.save(project_with_agr_toml / "agr.toml")

        # Install only the skill
        handle = ParsedHandle.from_components("kasperjunge", "commit")
        skill_path = handle.to_skill_path(project_with_agr_toml / ".claude")
        skill_path.mkdir(parents=True)
        (skill_path / "SKILL.md").write_text("# Commit Skill")

        result = runner.invoke(app, ["list", "--format", "json"])

        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            if line.strip().startswith("["):
                in_json = True
            if in_json:
                json_lines.append(line)
            if line.strip() == "]":
                break

        data = json.loads("\n".join(json_lines))
        commit = next(d for d in data if d.get("handle") == "kasperjunge/commit")
        helper = next(d for d in data if d.get("handle") == "alice/helper")

        assert commit["installed"] is True
        assert helper["installed"] is False


class TestAgrListNoConfig:
    """Tests for agr list with no config or empty dependencies."""

    def test_list_without_agr_toml_shows_message(
        self, project_with_git: Path
    ):
        """Test list without agr.toml shows helpful message."""
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "no agr.toml" in result.output.lower()

    def test_list_with_empty_dependencies_shows_message(
        self, project_with_agr_toml: Path
    ):
        """Test list with empty dependencies shows appropriate message."""
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "no dependencies" in result.output.lower()

    def test_list_suggests_agr_add_when_no_deps(self, project_with_agr_toml: Path):
        """Test that empty dependency list suggests using agr add."""
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "agr add" in result.output.lower()


class TestAgrListMultipleTypes:
    """Tests for agr list with multiple resource types."""

    def test_list_shows_all_resource_types(self, project_with_agr_toml: Path):
        """Test list displays skills, commands, and agents together."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("user/skill-a", "skill")
        config.add_remote("user/cmd-b", "command")
        config.add_remote("user/agent-c", "agent")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "skill-a" in result.output
        assert "cmd-b" in result.output
        assert "agent-c" in result.output
        # Check types are displayed
        assert "skill" in result.output.lower()
        assert "command" in result.output.lower()
        assert "agent" in result.output.lower()

    def test_list_json_preserves_type_field(self, project_with_agr_toml: Path):
        """Test JSON output correctly preserves type for each entry."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_remote("user/skill-a", "skill")
        config.add_remote("user/cmd-b", "command")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["list", "--format", "json"])

        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            if line.strip().startswith("["):
                in_json = True
            if in_json:
                json_lines.append(line)
            if line.strip() == "]":
                break

        data = json.loads("\n".join(json_lines))
        types = {d["type"] for d in data}
        assert "skill" in types
        assert "command" in types
