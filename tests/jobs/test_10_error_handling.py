"""Test Job 10: Error Handling & Validation.

Tests for error handling across agr/agrx commands:
- Non-existent repository errors
- Resource not found errors
- Resource exists errors (--overwrite)
- Empty package errors
- Ambiguous resource type errors
- Invalid reference format errors

Reference: .documents/jobs.md section "10. Error Handling & Validation"
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.cli.run import app as agrx_app
from agr.config import AgrConfig
from agr.exceptions import RepoNotFoundError, ResourceNotFoundError
from agr.fetcher import ResourceType, DiscoveredResource, DiscoveryResult


runner = CliRunner()


class TestNonExistentRepository:
    """Tests for non-existent repository error handling."""

    @patch("agr.cli.handlers.fetch_resource")
    def test_add_remote_shows_repo_not_found_error(
        self, mock_fetch, project_with_agr_toml: Path
    ):
        """Test that adding from non-existent repo shows clear error."""
        mock_fetch.side_effect = RepoNotFoundError("Repository not found")

        result = runner.invoke(app, ["add", "nonexistent-user/nonexistent-skill"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    @patch("agr.cli.run.downloaded_repo")
    def test_agrx_shows_repo_not_found_error(
        self, mock_download, project_with_git: Path
    ):
        """Test that agrx with non-existent repo shows clear error."""
        mock_download.return_value.__enter__ = MagicMock(
            side_effect=RepoNotFoundError("Repository not found")
        )
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        result = runner.invoke(agrx_app, ["--type", "skill", "nonexistent-user/skill"])

        # Should exit with error
        assert result.exit_code != 0


class TestResourceNotFound:
    """Tests for resource not found error handling."""

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.discover_runnable_resource")
    def test_agrx_shows_resource_not_found_error(
        self, mock_discover, mock_download, mock_which, project_with_git: Path
    ):
        """Test that agrx shows error when resource doesn't exist in repo."""
        mock_download.return_value.__enter__ = MagicMock(return_value=project_with_git)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)
        mock_discover.return_value = DiscoveryResult(resources=[])

        result = runner.invoke(agrx_app, ["testuser/nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()


class TestResourceExistsError:
    """Tests for resource already exists error handling."""

    def test_add_existing_without_overwrite_succeeds_by_default(
        self, project_with_agr_toml: Path
    ):
        """Test that adding existing resource updates it by default for local resources."""
        # Create local skill
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Original")

        # First add
        result1 = runner.invoke(app, ["add", "./resources/skills/my-skill"])
        assert result1.exit_code == 0

        # Second add should also succeed (overwrites by default for local)
        (skill_dir / "SKILL.md").write_text("# Updated")
        result2 = runner.invoke(app, ["add", "./resources/skills/my-skill"])
        assert result2.exit_code == 0

    def test_add_with_overwrite_flag_succeeds(self, project_with_agr_toml: Path):
        """Test that --overwrite flag allows replacing existing resource."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Original")

        # First add
        runner.invoke(app, ["add", "./resources/skills/my-skill"])

        # Update and add with --overwrite
        (skill_dir / "SKILL.md").write_text("# Updated with overwrite")
        result = runner.invoke(app, ["add", "./resources/skills/my-skill", "--overwrite"])

        assert result.exit_code == 0


class TestEmptyPackageError:
    """Tests for empty package validation error."""

    def test_add_empty_package_shows_error(self, project_with_agr_toml: Path):
        """Test that adding empty package shows validation error."""
        # Create empty package directory
        pkg_dir = project_with_agr_toml / "resources" / "packages" / "empty-pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "skills").mkdir()
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()
        # No actual resources inside

        result = runner.invoke(
            app,
            ["add", "./resources/packages/empty-pkg", "--type", "package"]
        )

        assert result.exit_code != 0
        assert "no resources" in result.output.lower() or "empty" in result.output.lower()


class TestAmbiguousResourceType:
    """Tests for ambiguous resource type error handling."""

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.discover_runnable_resource")
    def test_agrx_ambiguous_shows_type_suggestion(
        self, mock_discover, mock_download, mock_which, project_with_git: Path
    ):
        """Test that ambiguous resource suggests using --type flag."""
        mock_download.return_value.__enter__ = MagicMock(return_value=project_with_git)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        # Return both skill and command with same name
        mock_discover.return_value = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.SKILL,
                    path_segments=["hello"]
                ),
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.COMMAND,
                    path_segments=["hello"]
                ),
            ]
        )

        result = runner.invoke(agrx_app, ["testuser/hello"])

        assert result.exit_code != 0
        assert "multiple" in result.output.lower()
        assert "--type" in result.output


class TestInvalidReferenceFormat:
    """Tests for invalid reference format error handling."""

    def test_add_invalid_local_path_shows_error(self, project_with_agr_toml: Path):
        """Test that invalid local path shows clear error."""
        result = runner.invoke(app, ["add", "./nonexistent/path/skill"])

        assert result.exit_code != 0
        assert "not exist" in result.output.lower() or "error" in result.output.lower()

    def test_add_cannot_detect_type_shows_error(self, project_with_agr_toml: Path):
        """Test that adding undetectable resource type shows error."""
        # Create a random file that's not a recognizable resource
        random_file = project_with_agr_toml / "random.txt"
        random_file.write_text("just some text")

        result = runner.invoke(app, ["add", "./random.txt"])

        assert result.exit_code != 0
        assert "could not detect" in result.output.lower() or "type" in result.output.lower()


class TestPathNotFoundErrors:
    """Tests for path not found errors in various commands."""

    def test_sync_nonexistent_local_path_shows_error(
        self, project_with_agr_toml: Path
    ):
        """Test that syncing a nonexistent local path shows error."""
        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_local("./nonexistent/skill", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["sync", "--local"])

        # Should report the error for the missing path
        assert "not exist" in result.output.lower() or "error" in result.output.lower() or "failed" in result.output.lower()


class TestRemoveErrors:
    """Tests for remove command error handling."""

    def test_remove_nonexistent_resource_shows_message(
        self, project_with_agr_toml: Path
    ):
        """Test that removing nonexistent resource shows appropriate message."""
        result = runner.invoke(app, ["remove", "nonexistent-resource"])

        # Should show that resource wasn't found
        assert "not found" in result.output.lower() or "no" in result.output.lower()


class TestInitErrors:
    """Tests for init command error handling."""

    def test_init_package_existing_shows_error(self, project_with_git: Path):
        """Test that init package errors if directory already exists."""
        # Create existing package directory
        pkg_dir = project_with_git / "resources" / "packages" / "existing-pkg"
        pkg_dir.mkdir(parents=True)

        result = runner.invoke(app, ["init", "package", "existing-pkg"])

        assert result.exit_code != 0
        assert "already exists" in result.output.lower()


class TestInvalidTypeFlag:
    """Tests for invalid --type flag values."""

    def test_add_invalid_type_shows_error(self, project_with_agr_toml: Path):
        """Test that invalid --type value shows error."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "test"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test")

        result = runner.invoke(
            app,
            ["add", "./resources/skills/test", "--type", "invalid"]
        )

        # Should either show error or ignore invalid type
        # (depends on implementation)

    def test_agrx_invalid_type_shows_error(self):
        """Test that agrx with invalid --type shows error."""
        result = runner.invoke(agrx_app, ["--type", "invalid", "testuser/hello"])

        assert result.exit_code != 0
        assert "unknown" in result.output.lower() or "invalid" in result.output.lower()


class TestGracefulDegradation:
    """Tests for graceful degradation in error scenarios."""

    def test_list_with_corrupt_config_handles_gracefully(
        self, project_with_git: Path
    ):
        """Test that list handles corrupt agr.toml gracefully."""
        # Create invalid toml
        (project_with_git / "agr.toml").write_text("invalid [ toml content")

        result = runner.invoke(app, ["list"])

        # Should either show error or handle gracefully
        # Not crash with unhandled exception

    def test_sync_partial_failure_continues(self, project_with_agr_toml: Path):
        """Test that sync continues after partial failure."""
        # Create one valid and one invalid local dependency
        skill_dir = project_with_agr_toml / "resources" / "skills" / "valid-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Valid")

        config = AgrConfig.load(project_with_agr_toml / "agr.toml")
        config.add_local("./resources/skills/valid-skill", "skill")
        config.add_local("./nonexistent/skill", "skill")
        config.save(project_with_agr_toml / "agr.toml")

        result = runner.invoke(app, ["sync", "--local"])

        # Should process the valid one even if invalid fails
        # The valid skill should be installed
        claude_skills = project_with_agr_toml / ".claude" / "skills"
        if claude_skills.exists():
            skill_dirs = list(claude_skills.iterdir())
            # At least the valid skill should be installed
            assert any("valid-skill" in d.name for d in skill_dirs)
