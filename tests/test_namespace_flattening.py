"""Tests for namespace flattening functionality.

Claude Code's .claude/skills/ directory only discovers top-level directories.
To support nested skill organization, skills are installed with flattened
colon-namespaced directory names (e.g., "kasperjunge:product-strategy:growth-hacker").
"""

import pytest
from pathlib import Path

from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig
from agr.utils import (
    compute_flattened_skill_name,
    compute_path_segments_from_skill_path,
    update_skill_md_name,
)


runner = CliRunner()


class TestComputeFlattenedSkillName:
    """Tests for compute_flattened_skill_name helper."""

    def test_flat_skill(self):
        """Test flat skill name computation."""
        result = compute_flattened_skill_name("kasperjunge", ["commit"])
        assert result == "kasperjunge:commit"

    def test_nested_skill(self):
        """Test nested skill name computation."""
        result = compute_flattened_skill_name(
            "kasperjunge", ["product-strategy", "growth-hacker"]
        )
        assert result == "kasperjunge:product-strategy:growth-hacker"

    def test_deeply_nested_skill(self):
        """Test deeply nested skill name computation."""
        result = compute_flattened_skill_name(
            "kasperjunge", ["level1", "level2", "level3", "skill"]
        )
        assert result == "kasperjunge:level1:level2:level3:skill"

    def test_remote_skill(self):
        """Test remote skill name computation."""
        result = compute_flattened_skill_name("dsjacobsen", ["golang-pro"])
        assert result == "dsjacobsen:golang-pro"

    def test_empty_segments_raises(self):
        """Test that empty path segments raises an error."""
        with pytest.raises(ValueError):
            compute_flattened_skill_name("kasperjunge", [])


class TestComputePathSegments:
    """Tests for compute_path_segments_from_skill_path helper."""

    def test_flat_skill_path(self):
        """Test flat skill path segment extraction."""
        path = Path("./resources/skills/commit")
        result = compute_path_segments_from_skill_path(path)
        assert result == ["commit"]

    def test_nested_skill_path(self):
        """Test nested skill path segment extraction."""
        path = Path("./resources/skills/product-strategy/growth-hacker")
        result = compute_path_segments_from_skill_path(path)
        assert result == ["product-strategy", "growth-hacker"]

    def test_skill_path_without_skills_dir(self):
        """Test skill path without 'skills' in the path."""
        path = Path("./my-custom-dir/my-skill")
        result = compute_path_segments_from_skill_path(path)
        # Falls back to just the name
        assert result == ["my-skill"]

    def test_skill_path_with_explicit_root(self):
        """Test skill path with explicit skills root."""
        skills_root = Path("./resources/skills")
        skill_path = Path("./resources/skills/product-strategy/growth-hacker")
        result = compute_path_segments_from_skill_path(skill_path, skills_root)
        assert result == ["product-strategy", "growth-hacker"]


class TestUpdateSkillMdName:
    """Tests for update_skill_md_name helper."""

    def test_updates_existing_name(self, tmp_path: Path):
        """Test updating existing name field in SKILL.md."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
name: my-skill
description: A test skill
---

# My Skill
"""
        )

        update_skill_md_name(skill_dir, "kasperjunge:my-skill")

        content = skill_md.read_text()
        assert "name: kasperjunge:my-skill" in content
        assert "description: A test skill" in content
        assert "# My Skill" in content

    def test_adds_name_to_existing_frontmatter(self, tmp_path: Path):
        """Test adding name to frontmatter without name field."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
description: A test skill
---

# My Skill
"""
        )

        update_skill_md_name(skill_dir, "kasperjunge:my-skill")

        content = skill_md.read_text()
        assert "name: kasperjunge:my-skill" in content
        assert "description: A test skill" in content

    def test_adds_frontmatter_when_missing(self, tmp_path: Path):
        """Test adding frontmatter when completely missing."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# My Skill\n\nSome content.")

        update_skill_md_name(skill_dir, "kasperjunge:my-skill")

        content = skill_md.read_text()
        assert content.startswith("---\n")
        assert "name: kasperjunge:my-skill" in content
        assert "# My Skill" in content

    def test_raises_when_skill_md_missing(self, tmp_path: Path):
        """Test that FileNotFoundError is raised when SKILL.md doesn't exist."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            update_skill_md_name(skill_dir, "kasperjunge:my-skill")


class TestInstallFlatSkill:
    """Tests for installing flat skills with flattened names."""

    def test_add_flat_skill_installs_with_flattened_name(
        self, tmp_path: Path, monkeypatch
    ):
        """Test adding a flat skill installs to user:skill/ directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create local skill
        skill_dir = tmp_path / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            """---
name: commit
description: Generate commit messages
---

# Commit
"""
        )

        result = runner.invoke(app, ["add", "./skills/commit"])

        assert result.exit_code == 0

        # Verify installed to flattened path
        installed = tmp_path / ".claude" / "skills" / "local:commit" / "SKILL.md"
        assert installed.exists()

        # Verify name was updated
        content = installed.read_text()
        assert "name: local:commit" in content


class TestInstallNestedSkill:
    """Tests for installing nested skills with flattened names."""

    def test_add_nested_skill_installs_with_flattened_name(
        self, tmp_path: Path, monkeypatch
    ):
        """Test adding a nested skill installs to user:namespace:skill/ directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create nested skill
        skill_dir = tmp_path / "skills" / "product-strategy" / "growth-hacker"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            """---
name: growth-hacker
description: Growth hacking strategies
---

# Growth Hacker
"""
        )

        result = runner.invoke(
            app, ["add", "./skills/product-strategy/growth-hacker"]
        )

        assert result.exit_code == 0

        # Verify installed to flattened path
        installed = (
            tmp_path
            / ".claude"
            / "skills"
            / "local:product-strategy:growth-hacker"
            / "SKILL.md"
        )
        assert installed.exists()

        # Verify name was updated
        content = installed.read_text()
        assert "name: local:product-strategy:growth-hacker" in content


class TestNamespaceAddFlattening:
    """Tests for handle_add_namespace() flattening."""

    def test_add_namespace_flattens_all_skills(self, tmp_path: Path, monkeypatch):
        """Test that adding a namespace directory flattens all contained skills."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create namespace with multiple skills
        namespace_dir = tmp_path / "product-strategy"
        (namespace_dir / "growth-hacker").mkdir(parents=True)
        (namespace_dir / "growth-hacker" / "SKILL.md").write_text("# Growth Hacker")
        (namespace_dir / "flywheel").mkdir(parents=True)
        (namespace_dir / "flywheel" / "SKILL.md").write_text("# Flywheel")

        result = runner.invoke(app, ["add", "./product-strategy"])

        assert result.exit_code == 0
        assert "local:product-strategy:growth-hacker" in result.output
        assert "local:product-strategy:flywheel" in result.output

        # Verify both skills installed with flattened names
        assert (
            tmp_path
            / ".claude"
            / "skills"
            / "local:product-strategy:growth-hacker"
            / "SKILL.md"
        ).exists()
        assert (
            tmp_path
            / ".claude"
            / "skills"
            / "local:product-strategy:flywheel"
            / "SKILL.md"
        ).exists()


class TestPackageExplodeFlattening:
    """Tests for _explode_package() flattening."""

    def test_package_explode_flattens_skills(self, tmp_path: Path, monkeypatch):
        """Test that package explosion uses flattened names for skills."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with skills
        pkg_dir = tmp_path / "packages" / "my-toolkit"
        skills_dir = pkg_dir / "skills" / "helper"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Helper Skill")
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/my-toolkit", "--type", "package"])

        assert result.exit_code == 0

        # Verify skill installed with flattened name
        installed = (
            tmp_path / ".claude" / "skills" / "local:my-toolkit:helper" / "SKILL.md"
        )
        assert installed.exists()

        # Verify SKILL.md name was updated
        content = installed.read_text()
        assert "name: local:my-toolkit:helper" in content

    def test_package_explode_nested_skills(self, tmp_path: Path, monkeypatch):
        """Test that nested skills in packages are discovered and flattened correctly."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with nested skill
        pkg_dir = tmp_path / "packages" / "my-toolkit"
        nested_skill = pkg_dir / "skills" / "category" / "helper"
        nested_skill.mkdir(parents=True)
        (nested_skill / "SKILL.md").write_text("# Nested Helper Skill")
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/my-toolkit", "--type", "package"])

        assert result.exit_code == 0

        # Verify nested skill installed with flattened name
        installed = (
            tmp_path / ".claude" / "skills" / "local:my-toolkit:category:helper" / "SKILL.md"
        )
        assert installed.exists()

        # Verify SKILL.md name was updated
        content = installed.read_text()
        assert "name: local:my-toolkit:category:helper" in content

    def test_package_explode_deeply_nested_skills(self, tmp_path: Path, monkeypatch):
        """Test that skills nested 2+ levels deep in packages are discovered."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with deeply nested skill
        pkg_dir = tmp_path / "packages" / "deep-toolkit"
        deep_skill = pkg_dir / "skills" / "level1" / "level2" / "deep-skill"
        deep_skill.mkdir(parents=True)
        (deep_skill / "SKILL.md").write_text("# Deep Skill")
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/deep-toolkit", "--type", "package"])

        assert result.exit_code == 0

        # Verify deeply nested skill installed with flattened name
        installed = (
            tmp_path / ".claude" / "skills" / "local:deep-toolkit:level1:level2:deep-skill" / "SKILL.md"
        )
        assert installed.exists()

        # Verify SKILL.md name was updated
        content = installed.read_text()
        assert "name: local:deep-toolkit:level1:level2:deep-skill" in content

    def test_package_mixed_skill_depths(self, tmp_path: Path, monkeypatch):
        """Test that both flat and nested skills in same package are handled."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with both flat and nested skills
        pkg_dir = tmp_path / "packages" / "mixed-toolkit"

        # Flat skill
        flat_skill = pkg_dir / "skills" / "flat-skill"
        flat_skill.mkdir(parents=True)
        (flat_skill / "SKILL.md").write_text("# Flat Skill")

        # Nested skill
        nested_skill = pkg_dir / "skills" / "category" / "nested-skill"
        nested_skill.mkdir(parents=True)
        (nested_skill / "SKILL.md").write_text("# Nested Skill")

        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/mixed-toolkit", "--type", "package"])

        assert result.exit_code == 0

        # Verify flat skill installed
        flat_installed = (
            tmp_path / ".claude" / "skills" / "local:mixed-toolkit:flat-skill" / "SKILL.md"
        )
        assert flat_installed.exists()
        flat_content = flat_installed.read_text()
        assert "name: local:mixed-toolkit:flat-skill" in flat_content

        # Verify nested skill installed
        nested_installed = (
            tmp_path / ".claude" / "skills" / "local:mixed-toolkit:category:nested-skill" / "SKILL.md"
        )
        assert nested_installed.exists()
        nested_content = nested_installed.read_text()
        assert "name: local:mixed-toolkit:category:nested-skill" in nested_content


class TestSyncLocalDependencyFlattening:
    """Tests for sync applying flattening to local skills."""

    def test_sync_flattens_local_skill(self, tmp_path: Path, monkeypatch):
        """Test that sync uses flattened names for local skills."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create local skill
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # Create agr.toml with local dependency
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text(
            """
[[dependencies]]
path = "./skills/my-skill"
type = "skill"
"""
        )

        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0

        # Verify installed with flattened name
        installed = tmp_path / ".claude" / "skills" / "local:my-skill" / "SKILL.md"
        assert installed.exists()

    def test_sync_flattens_nested_local_skill(self, tmp_path: Path, monkeypatch):
        """Test that sync uses flattened names for nested local skills."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create nested skill
        skill_dir = tmp_path / "skills" / "product" / "flywheel"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Flywheel")

        # Create agr.toml with local dependency
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text(
            """
[[dependencies]]
path = "./skills/product/flywheel"
type = "skill"
"""
        )

        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0

        # Verify installed with flattened name
        installed = (
            tmp_path / ".claude" / "skills" / "local:product:flywheel" / "SKILL.md"
        )
        assert installed.exists()


class TestSkillMdNameUpdated:
    """Tests that SKILL.md name field is updated after installation."""

    def test_skill_md_name_updated_on_add(self, tmp_path: Path, monkeypatch):
        """Test that SKILL.md name is updated when skill is added."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create skill with original name
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            """---
name: my-skill
description: Test skill
---

# My Skill
"""
        )

        runner.invoke(app, ["add", "./skills/my-skill"])

        # Verify name was updated
        installed = tmp_path / ".claude" / "skills" / "local:my-skill" / "SKILL.md"
        content = installed.read_text()
        assert "name: local:my-skill" in content
        assert "description: Test skill" in content

    def test_skill_md_name_updated_on_sync(self, tmp_path: Path, monkeypatch):
        """Test that SKILL.md name is updated when skill is synced."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create skill with original name
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            """---
name: my-skill
description: Test skill
---

# My Skill
"""
        )

        # Create agr.toml
        (tmp_path / "agr.toml").write_text(
            """
[[dependencies]]
path = "./skills/my-skill"
type = "skill"
"""
        )

        runner.invoke(app, ["sync"])

        # Verify name was updated
        installed = tmp_path / ".claude" / "skills" / "local:my-skill" / "SKILL.md"
        content = installed.read_text()
        assert "name: local:my-skill" in content
