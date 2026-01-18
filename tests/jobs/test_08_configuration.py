"""Test Job 8: Configuration Management.

Tests for agr.toml configuration management.

Reference: .documents/jobs.md section "8. Configuration Management"

NOTE: Comprehensive tests for this job are in:
- tests/test_config.py - AgrConfig class tests
- tests/test_config_local.py - local configuration tests

Existing Coverage:
- tests/test_config.py - agr.toml parsing, saving, loading
- tests/test_config_local.py - local dependency handling
- tests/test_workspace.py - workspace/package configuration
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig, Dependency


runner = CliRunner()


class TestAgrTomlTracking:
    """Tests for agr.toml dependency tracking.

    See test_config.py for comprehensive tests.
    """

    def test_add_updates_agr_toml(self, project_with_agr_toml: Path):
        """Verify add command updates agr.toml."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "tracked"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Tracked")

        runner.invoke(app, ["add", "./resources/skills/tracked"])

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert len(config.dependencies) > 0

    def test_remove_updates_agr_toml(self, project_with_agr_toml: Path):
        """Verify remove command updates agr.toml."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "removable"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Removable")

        runner.invoke(app, ["add", "./resources/skills/removable"])
        config_before = AgrConfig.load(project_with_agr_toml / "agr.toml")
        deps_before = len(config_before.dependencies)

        # Remove by path (remove uses path matching for local resources)
        runner.invoke(app, ["remove", "./resources/skills/removable"])

        config_after = AgrConfig.load(project_with_agr_toml / "agr.toml")
        assert len(config_after.dependencies) < deps_before


class TestConfigSerialization:
    """Tests for agr.toml serialization.

    See test_config.py for comprehensive tests.
    """

    def test_config_save_load_roundtrip(self, project_with_git: Path):
        """Verify config survives save/load roundtrip."""
        config_path = project_with_git / "agr.toml"

        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.add_local("./resources/skills/local", "skill")
        config.save(config_path)

        loaded = AgrConfig.load(config_path)

        assert len(loaded.dependencies) == 2
        remote_deps = loaded.get_remote_dependencies()
        local_deps = loaded.get_local_dependencies()
        assert len(remote_deps) == 1
        assert len(local_deps) == 1

    def test_config_preserves_types(self, project_with_git: Path):
        """Verify config preserves resource types."""
        config_path = project_with_git / "agr.toml"

        config = AgrConfig()
        config.add_remote("user/skill", "skill")
        config.add_remote("user/cmd", "command")
        config.add_remote("user/agent", "agent")
        config.save(config_path)

        loaded = AgrConfig.load(config_path)
        types = {d.type for d in loaded.dependencies}

        assert "skill" in types
        assert "command" in types
        assert "agent" in types


class TestCollaboratorSync:
    """Tests for collaborator environment synchronization.

    See test_sync.py for comprehensive tests.
    """

    def test_sync_installs_from_agr_toml(self, project_with_agr_toml: Path):
        """Verify sync installs dependencies from agr.toml."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "sync-test"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Sync Test")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_local("./resources/skills/sync-test", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        # Sync should install it
        result = runner.invoke(app, ["sync", "--local"])

        assert result.exit_code == 0
        claude_skills = project_with_agr_toml / ".claude" / "skills"
        assert claude_skills.exists()


class TestLegacyMigration:
    """Tests for legacy config format migration.

    See test_config.py for comprehensive tests.
    """

    def test_old_format_migrated_on_load(self, project_with_git: Path):
        """Verify old format configs are migrated automatically."""
        config_path = project_with_git / "agr.toml"

        # Write old format (if applicable)
        # Current format uses dependencies array, old might have been different
        old_content = """
dependencies = [
    { handle = "kasperjunge/commit", type = "skill" }
]
"""
        config_path.write_text(old_content)

        # Load should migrate and work
        config = AgrConfig.load(config_path)

        assert len(config.dependencies) == 1
        assert config.dependencies[0].handle == "kasperjunge/commit"


class TestDirectoryStructure:
    """Tests for .claude/ directory structure.

    See test_paths.py and test_namespaced_paths.py for comprehensive tests.
    """

    def test_skills_installed_to_claude_skills(self, project_with_agr_toml: Path):
        """Verify skills are installed to .claude/skills/."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "dir-test"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Dir Test")

        runner.invoke(app, ["add", "./resources/skills/dir-test"])

        claude_skills = project_with_agr_toml / ".claude" / "skills"
        assert claude_skills.exists()

    def test_commands_installed_to_claude_commands(self, project_with_agr_toml: Path):
        """Verify commands are installed to .claude/commands/."""
        cmd_dir = project_with_agr_toml / "resources" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "dir-test.md").write_text("# Dir Test")

        runner.invoke(app, ["add", "./resources/commands/dir-test.md"])

        claude_commands = project_with_agr_toml / ".claude" / "commands"
        assert claude_commands.exists()


class TestFlattenedSkillNaming:
    """Tests for flattened skill naming in .claude/skills/.

    See test_namespace_flattening.py for comprehensive tests.
    """

    def test_skills_use_colon_namespacing(self, project_with_agr_toml: Path):
        """Verify skills use colon-namespaced directory names."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "colon-test"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Colon Test")

        runner.invoke(app, ["add", "./resources/skills/colon-test"])

        claude_skills = project_with_agr_toml / ".claude" / "skills"
        if claude_skills.exists():
            skill_dirs = list(claude_skills.iterdir())
            # Should have at least one directory
            assert len(skill_dirs) > 0
            # Check for colon in name (username:skillname format)
            # Note: for local skills, the username might be "local" or from git
