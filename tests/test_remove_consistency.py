"""Integration tests for remove command consistency with handle formats.

Tests that remove works correctly when:
1. Using the same slash format as add (kasperjunge/seo)
2. Skills are stored in colon format on disk (kasperjunge:seo)
3. agr.toml entries use slash format
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig


runner = CliRunner()


class TestRemoveWithSlashFormat:
    """Test that remove works with same format as add."""

    def test_remove_skill_slash_format(self, tmp_path: Path, monkeypatch):
        """agr remove kasperjunge/seo works when skill installed as kasperjunge:seo."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create flattened skill directory (as agr add would create it)
        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge:seo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# SEO Skill")

        # Create agr.toml with slash format (as agr add would create it)
        (tmp_path / "agr.toml").write_text(
            'dependencies = [{handle = "kasperjunge/seo", type = "skill"}]'
        )

        result = runner.invoke(app, ["remove", "kasperjunge/seo"])

        assert result.exit_code == 0
        assert not skill_dir.exists(), "Skill directory should be removed"

        config = AgrConfig.load(tmp_path / "agr.toml")
        assert len(config.dependencies) == 0, "Dependency should be removed from agr.toml"

    def test_remove_skill_simple_name(self, tmp_path: Path, monkeypatch):
        """agr remove seo finds and removes skill installed as kasperjunge:seo."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create flattened skill directory
        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge:seo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# SEO Skill")

        # Create agr.toml with slash format
        (tmp_path / "agr.toml").write_text(
            'dependencies = [{handle = "kasperjunge/seo", type = "skill"}]'
        )

        result = runner.invoke(app, ["remove", "seo"])

        assert result.exit_code == 0
        assert not skill_dir.exists(), "Skill directory should be removed"

        config = AgrConfig.load(tmp_path / "agr.toml")
        assert len(config.dependencies) == 0, "Dependency should be removed from agr.toml"

    def test_remove_updates_agr_toml(self, tmp_path: Path, monkeypatch):
        """Removing a skill also removes it from agr.toml."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        skill_dir = tmp_path / ".claude" / "skills" / "testuser:testskill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test")

        (tmp_path / "agr.toml").write_text(
            'dependencies = [{handle = "testuser/testskill", type = "skill"}]'
        )

        result = runner.invoke(app, ["remove", "testuser/testskill"])

        assert result.exit_code == 0
        assert not skill_dir.exists()

        config = AgrConfig.load(tmp_path / "agr.toml")
        assert len(config.dependencies) == 0

    def test_remove_nested_skill(self, tmp_path: Path, monkeypatch):
        """agr remove kasperjunge/product-strategy/growth-hacker works."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create nested skill with flattened name
        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge:product-strategy:growth-hacker"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Growth Hacker Skill")

        # Create agr.toml with slash format
        (tmp_path / "agr.toml").write_text(
            'dependencies = [{handle = "kasperjunge/product-strategy/growth-hacker", type = "skill"}]'
        )

        result = runner.invoke(app, ["remove", "kasperjunge/product-strategy/growth-hacker"])

        assert result.exit_code == 0
        assert not skill_dir.exists(), "Skill directory should be removed"


class TestRemoveThreePartRef:
    """Test removing resources with 3-part refs."""

    def test_remove_command_three_part(self, tmp_path: Path, monkeypatch):
        """agr remove user/repo/cmd works."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create command (commands use nested format)
        cmd_path = tmp_path / ".claude" / "commands" / "testuser" / "testcmd.md"
        cmd_path.parent.mkdir(parents=True)
        cmd_path.write_text("# Test Command")

        (tmp_path / "agr.toml").write_text(
            'dependencies = [{handle = "testuser/testrepo/testcmd", type = "command"}]'
        )

        result = runner.invoke(app, ["remove", "testuser/testrepo/testcmd"])

        # Should succeed and remove the command
        assert result.exit_code == 0

        config = AgrConfig.load(tmp_path / "agr.toml")
        assert len(config.dependencies) == 0


class TestDiscoveryFindsFlattened:
    """Test that discovery finds colon-namespaced skills."""

    def test_discovers_flattened_skill_with_slash_input(self, tmp_path: Path, monkeypatch):
        """Discovery finds kasperjunge:seo when searching for kasperjunge/seo."""
        from agr.cli.common import discover_local_resource_type

        monkeypatch.chdir(tmp_path)

        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge:seo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# SEO")

        result = discover_local_resource_type("kasperjunge/seo", global_install=False)

        assert not result.is_empty
        assert result.resources[0].username == "kasperjunge"
        assert result.resources[0].name == "seo"

    def test_discovers_flattened_skill_with_simple_name(self, tmp_path: Path, monkeypatch):
        """Discovery finds kasperjunge:seo when searching for just seo."""
        from agr.cli.common import discover_local_resource_type

        monkeypatch.chdir(tmp_path)

        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge:seo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# SEO")

        result = discover_local_resource_type("seo", global_install=False)

        assert not result.is_empty
        assert result.resources[0].username == "kasperjunge"
        assert result.resources[0].name == "seo"

    def test_discovers_nested_flattened_skill(self, tmp_path: Path, monkeypatch):
        """Discovery finds kasperjunge:product-strategy:growth-hacker."""
        from agr.cli.common import discover_local_resource_type

        monkeypatch.chdir(tmp_path)

        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge:product-strategy:growth-hacker"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Growth Hacker")

        result = discover_local_resource_type("growth-hacker", global_install=False)

        assert not result.is_empty
        assert result.resources[0].username == "kasperjunge"
        assert result.resources[0].name == "growth-hacker"


class TestAgrTomlConsistency:
    """Test that agr.toml operations are consistent with filesystem."""

    def test_remove_from_toml_with_slash_matches_colon_on_disk(self, tmp_path: Path, monkeypatch):
        """agr.toml with slash format matches filesystem with colon format."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Skill on disk with colon format
        skill_dir = tmp_path / ".claude" / "skills" / "alice:my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # agr.toml with slash format
        config = AgrConfig()
        config.add_remote("alice/my-skill", "skill")
        config.save(tmp_path / "agr.toml")

        # Remove using slash format should work
        result = runner.invoke(app, ["remove", "alice/my-skill"])

        assert result.exit_code == 0
        assert not skill_dir.exists()

        reloaded = AgrConfig.load(tmp_path / "agr.toml")
        assert len(reloaded.dependencies) == 0

    def test_remove_only_removes_matching_dependency(self, tmp_path: Path, monkeypatch):
        """Removing one dependency doesn't affect others."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create two skills
        skill1 = tmp_path / ".claude" / "skills" / "user1:skill1"
        skill1.mkdir(parents=True)
        (skill1 / "SKILL.md").write_text("# Skill 1")

        skill2 = tmp_path / ".claude" / "skills" / "user2:skill2"
        skill2.mkdir(parents=True)
        (skill2 / "SKILL.md").write_text("# Skill 2")

        # Create agr.toml with both
        config = AgrConfig()
        config.add_remote("user1/skill1", "skill")
        config.add_remote("user2/skill2", "skill")
        config.save(tmp_path / "agr.toml")

        # Remove first skill
        result = runner.invoke(app, ["remove", "user1/skill1"])

        assert result.exit_code == 0
        assert not skill1.exists()
        assert skill2.exists()

        # Check agr.toml still has second dependency
        reloaded = AgrConfig.load(tmp_path / "agr.toml")
        assert len(reloaded.dependencies) == 1
        assert reloaded.dependencies[0].handle == "user2/skill2"


class TestListStatusConsistency:
    """Test that list shows correct status for flattened skills."""

    def test_list_shows_installed_for_flattened_skill(self, tmp_path: Path, monkeypatch):
        """agr list shows 'installed' for skills in colon format."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create flattened skill
        skill_dir = tmp_path / ".claude" / "skills" / "testuser:testskill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill")

        # Create agr.toml with slash format
        config = AgrConfig()
        config.add_remote("testuser/testskill", "skill")
        config.save(tmp_path / "agr.toml")

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "installed" in result.output.lower()
        assert "1/1 installed" in result.output


class TestSyncConsistency:
    """Test that sync operations work with flattened format."""

    def test_sync_detects_installed_flattened_skill(self, tmp_path: Path, monkeypatch):
        """agr sync --remote recognizes flattened skills as already installed."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create flattened skill (simulating already installed)
        skill_dir = tmp_path / ".claude" / "skills" / "testuser:testskill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill")

        # Create agr.toml with slash format
        config = AgrConfig()
        config.add_remote("testuser/testskill", "skill")
        config.save(tmp_path / "agr.toml")

        # Sync should detect skill is already installed and not try to fetch
        result = runner.invoke(app, ["sync", "--remote"])

        # Should complete without errors and not install anything new
        assert result.exit_code == 0
        # The skill should still exist
        assert skill_dir.exists()
