"""Tests for agr.toml configuration management."""

from pathlib import Path

import pytest

from agr.config import AgrConfig, DependencySpec, find_config, get_or_create_config
from agr.exceptions import ConfigParseError


class TestAgrConfig:
    """Tests for AgrConfig class."""

    def test_load_valid_config(self, tmp_path: Path):
        """Test loading a valid agr.toml file."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text('''[dependencies]
"kasperjunge/commit" = {}
"alice/code-review" = { type = "skill" }
''')

        config = AgrConfig.load(config_path)

        assert "kasperjunge/commit" in config.dependencies
        assert "alice/code-review" in config.dependencies
        assert config.dependencies["kasperjunge/commit"].type is None
        assert config.dependencies["alice/code-review"].type == "skill"

    def test_load_empty_config(self, tmp_path: Path):
        """Test loading an empty agr.toml file."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("")

        config = AgrConfig.load(config_path)

        assert config.dependencies == {}

    def test_load_config_without_dependencies(self, tmp_path: Path):
        """Test loading a config file without dependencies section."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("[metadata]\nname = 'test'\n")

        config = AgrConfig.load(config_path)

        assert config.dependencies == {}

    def test_load_invalid_toml_raises_error(self, tmp_path: Path):
        """Test that invalid TOML raises ConfigParseError."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("invalid toml [[[")

        with pytest.raises(ConfigParseError):
            AgrConfig.load(config_path)

    def test_load_nonexistent_file(self, tmp_path: Path):
        """Test loading a nonexistent file returns empty config."""
        config_path = tmp_path / "nonexistent.toml"

        config = AgrConfig.load(config_path)

        assert config.dependencies == {}

    def test_save_roundtrip(self, tmp_path: Path):
        """Test that saving and loading preserves data."""
        config_path = tmp_path / "agr.toml"

        # Create and save config
        config = AgrConfig()
        config.add_dependency("kasperjunge/commit", DependencySpec())
        config.add_dependency("alice/review", DependencySpec(type="skill"))
        config.save(config_path)

        # Load and verify
        loaded = AgrConfig.load(config_path)
        assert "kasperjunge/commit" in loaded.dependencies
        assert "alice/review" in loaded.dependencies
        assert loaded.dependencies["alice/review"].type == "skill"

    def test_save_preserves_comments(self, tmp_path: Path):
        """Test that saving preserves existing comments in the file."""
        config_path = tmp_path / "agr.toml"
        original_content = '''# My project dependencies
[dependencies]
"kasperjunge/commit" = {}
'''
        config_path.write_text(original_content)

        # Load, modify, and save
        config = AgrConfig.load(config_path)
        config.add_dependency("alice/review", DependencySpec())
        config.save(config_path)

        # Verify comment is preserved
        saved_content = config_path.read_text()
        assert "# My project dependencies" in saved_content


class TestDependencyManagement:
    """Tests for add/remove dependency operations."""

    def test_add_dependency_basic(self):
        """Test adding a basic dependency without type."""
        config = AgrConfig()

        config.add_dependency("kasperjunge/commit", DependencySpec())

        assert "kasperjunge/commit" in config.dependencies
        assert config.dependencies["kasperjunge/commit"].type is None

    def test_add_dependency_with_type(self):
        """Test adding a dependency with explicit type."""
        config = AgrConfig()

        config.add_dependency("alice/ambiguous", DependencySpec(type="skill"))

        assert "alice/ambiguous" in config.dependencies
        assert config.dependencies["alice/ambiguous"].type == "skill"

    def test_add_dependency_overwrites_existing(self):
        """Test that adding an existing dependency overwrites it."""
        config = AgrConfig()
        config.add_dependency("kasperjunge/commit", DependencySpec())

        config.add_dependency("kasperjunge/commit", DependencySpec(type="command"))

        assert config.dependencies["kasperjunge/commit"].type == "command"

    def test_remove_dependency(self):
        """Test removing a dependency."""
        config = AgrConfig()
        config.add_dependency("kasperjunge/commit", DependencySpec())
        config.add_dependency("alice/review", DependencySpec())

        config.remove_dependency("kasperjunge/commit")

        assert "kasperjunge/commit" not in config.dependencies
        assert "alice/review" in config.dependencies

    def test_remove_nonexistent_dependency(self):
        """Test that removing a nonexistent dependency is a no-op."""
        config = AgrConfig()

        # Should not raise
        config.remove_dependency("nonexistent/dep")

        assert config.dependencies == {}


class TestFindConfig:
    """Tests for find_config function."""

    def test_find_config_in_current_dir(self, tmp_path: Path, monkeypatch):
        """Test finding config in current directory."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("[dependencies]\n")
        monkeypatch.chdir(tmp_path)

        # Also create a git directory to mark as git root
        (tmp_path / ".git").mkdir()

        result = find_config()

        assert result == config_path

    def test_find_config_in_parent_dir(self, tmp_path: Path, monkeypatch):
        """Test finding config in parent directory."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("[dependencies]\n")
        (tmp_path / ".git").mkdir()

        subdir = tmp_path / "src" / "app"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        result = find_config()

        assert result == config_path

    def test_find_config_stops_at_git_root(self, tmp_path: Path, monkeypatch):
        """Test that search stops at git root."""
        # Create config outside git root
        outer_config = tmp_path / "agr.toml"
        outer_config.write_text("[dependencies]\n")

        # Create git root without config
        git_root = tmp_path / "project"
        git_root.mkdir()
        (git_root / ".git").mkdir()

        subdir = git_root / "src"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        result = find_config()

        assert result is None

    def test_find_config_not_found(self, tmp_path: Path, monkeypatch):
        """Test when no config file exists."""
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        result = find_config()

        assert result is None


class TestGetOrCreateConfig:
    """Tests for get_or_create_config function."""

    def test_get_existing_config(self, tmp_path: Path, monkeypatch):
        """Test getting an existing config file."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text('''[dependencies]
"kasperjunge/commit" = {}
''')
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        path, config = get_or_create_config()

        assert path == config_path
        assert "kasperjunge/commit" in config.dependencies

    def test_create_config_when_missing(self, tmp_path: Path, monkeypatch):
        """Test creating a config file when none exists."""
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        path, config = get_or_create_config()

        assert path == tmp_path / "agr.toml"
        assert path.exists()
        assert config.dependencies == {}

    def test_get_config_from_parent_dir(self, tmp_path: Path, monkeypatch):
        """Test getting config from parent directory."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("[dependencies]\n")
        (tmp_path / ".git").mkdir()

        subdir = tmp_path / "src"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        path, config = get_or_create_config()

        assert path == config_path
