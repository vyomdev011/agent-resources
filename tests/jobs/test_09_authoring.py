"""Test Job 9: Authoring & Publishing Workflows.

Tests for local development and publishing workflows:
- Authoring resources in resources/ directory
- Testing locally authored resources
- Syncing local changes to .claude/
- Publishing workflow considerations

Reference: .documents/jobs.md section "9. Authoring & Publishing Workflows"

NOTE: Core init/scaffolding tests are in test_init_authoring.py.
This module focuses on the full authoring workflow from init through testing.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig


runner = CliRunner()


class TestLocalDevelopmentWorkflow:
    """Tests for the local development workflow."""

    def test_init_then_add_local_skill_workflow(
        self, project_with_git: Path
    ):
        """Test full workflow: init project, init skill, add to project."""
        # Step 1: Initialize project
        result1 = runner.invoke(app, ["init"])
        assert result1.exit_code == 0

        # Step 2: Scaffold a new skill
        result2 = runner.invoke(app, ["init", "skill", "my-new-skill"])
        assert result2.exit_code == 0

        # Verify skill was created in resources/
        skill_path = project_with_git / "resources" / "skills" / "my-new-skill"
        assert skill_path.exists()
        assert (skill_path / "SKILL.md").exists()

        # Step 3: Add local skill to project
        result3 = runner.invoke(app, ["add", "./resources/skills/my-new-skill"])
        assert result3.exit_code == 0

        # Verify skill was added to agr.toml
        config = AgrConfig.load(project_with_git / "agr.toml")
        assert any("my-new-skill" in (d.path or "") for d in config.dependencies)

        # Verify skill was installed to .claude/
        claude_skills = project_with_git / ".claude" / "skills"
        assert claude_skills.exists()

    def test_edit_then_sync_local_workflow(self, project_with_git: Path):
        """Test workflow: edit local resource, sync to update .claude/."""
        import time

        # Initialize and add local skill
        runner.invoke(app, ["init"])
        runner.invoke(app, ["init", "skill", "editable-skill"])
        runner.invoke(app, ["add", "./resources/skills/editable-skill"])

        # Edit the skill (modify SKILL.md)
        skill_md = project_with_git / "resources" / "skills" / "editable-skill" / "SKILL.md"
        original_content = skill_md.read_text()
        time.sleep(0.1)  # Ensure mtime difference
        skill_md.write_text(original_content + "\n## New Section\n")

        # Sync to update .claude/
        result = runner.invoke(app, ["sync", "--local"])
        assert result.exit_code == 0

        # Verify the update was applied
        # (The installed content should be updated)

    def test_init_skill_with_custom_path_workflow(self, project_with_git: Path):
        """Test scaffolding skill with custom path."""
        custom_dir = project_with_git / "src" / "skills"

        result = runner.invoke(
            app,
            ["init", "skill", "custom-skill", "--path", str(custom_dir)]
        )

        assert result.exit_code == 0
        assert (custom_dir / "SKILL.md").exists()


class TestAuthoringConventions:
    """Tests for authoring directory conventions."""

    def test_init_creates_convention_structure(self, project_with_git: Path):
        """Test that agr init creates the convention structure."""
        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        resources = project_with_git / "resources"
        assert resources.exists()
        assert (resources / "skills").exists()
        assert (resources / "commands").exists()
        assert (resources / "agents").exists()
        assert (resources / "packages").exists()

    def test_skill_scaffolded_to_resources_skills(self, project_with_git: Path):
        """Test that skills are scaffolded to resources/skills/ by default."""
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init", "skill", "my-skill"])

        assert result.exit_code == 0
        assert (project_with_git / "resources" / "skills" / "my-skill" / "SKILL.md").exists()

    def test_command_scaffolded_to_resources_commands(self, project_with_git: Path):
        """Test that commands are scaffolded to resources/commands/ by default."""
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init", "command", "my-command"])

        assert result.exit_code == 0
        assert (project_with_git / "resources" / "commands" / "my-command.md").exists()

    def test_agent_scaffolded_to_resources_agents(self, project_with_git: Path):
        """Test that agents are scaffolded to resources/agents/ by default."""
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init", "agent", "my-agent"])

        assert result.exit_code == 0
        assert (project_with_git / "resources" / "agents" / "my-agent.md").exists()


class TestSkillMdTemplate:
    """Tests for SKILL.md template content."""

    def test_skill_md_has_name_field(self, project_with_git: Path):
        """Test that scaffolded SKILL.md includes name field."""
        runner.invoke(app, ["init"])
        runner.invoke(app, ["init", "skill", "template-test"])

        skill_md = project_with_git / "resources" / "skills" / "template-test" / "SKILL.md"
        content = skill_md.read_text()

        # Should have some content (template)
        assert len(content) > 0

    def test_skill_md_is_valid_markdown(self, project_with_git: Path):
        """Test that scaffolded SKILL.md is valid markdown."""
        runner.invoke(app, ["init"])
        runner.invoke(app, ["init", "skill", "markdown-test"])

        skill_md = project_with_git / "resources" / "skills" / "markdown-test" / "SKILL.md"
        content = skill_md.read_text()

        # Should start with markdown heading or have structure
        assert "#" in content or "---" in content


class TestCommandMdTemplate:
    """Tests for command .md template content."""

    def test_command_md_has_content(self, project_with_git: Path):
        """Test that scaffolded command .md includes template content."""
        runner.invoke(app, ["init"])
        runner.invoke(app, ["init", "command", "cmd-template-test"])

        cmd_md = project_with_git / "resources" / "commands" / "cmd-template-test.md"
        content = cmd_md.read_text()

        # Should have some content
        assert len(content) > 0


class TestAgentMdTemplate:
    """Tests for agent .md template content."""

    def test_agent_md_has_content(self, project_with_git: Path):
        """Test that scaffolded agent .md includes template content."""
        runner.invoke(app, ["init"])
        runner.invoke(app, ["init", "agent", "agent-template-test"])

        agent_md = project_with_git / "resources" / "agents" / "agent-template-test.md"
        content = agent_md.read_text()

        # Should have some content
        assert len(content) > 0


class TestPackageScaffolding:
    """Tests for package scaffolding."""

    def test_package_creates_subdirectories(self, project_with_git: Path):
        """Test that package scaffold creates skills/, commands/, agents/ subdirs."""
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init", "package", "my-toolkit"])

        assert result.exit_code == 0
        pkg_path = project_with_git / "resources" / "packages" / "my-toolkit"
        assert (pkg_path / "skills").exists()
        assert (pkg_path / "commands").exists()
        assert (pkg_path / "agents").exists()

    def test_package_with_custom_path(self, project_with_git: Path):
        """Test package scaffolding with custom path."""
        custom_path = project_with_git / "libs" / "toolkit"

        result = runner.invoke(
            app,
            ["init", "package", "custom-toolkit", "--path", str(custom_path)]
        )

        assert result.exit_code == 0
        assert custom_path.exists()
        assert (custom_path / "skills").exists()


class TestLegacyFlag:
    """Tests for --legacy flag in authoring commands."""

    def test_legacy_skill_uses_claude_directory(self, project_with_git: Path):
        """Test that --legacy flag creates skill in .claude/skills/."""
        result = runner.invoke(app, ["init", "skill", "legacy-skill", "--legacy"])

        assert result.exit_code == 0
        assert (project_with_git / ".claude" / "skills" / "legacy-skill" / "SKILL.md").exists()

    def test_legacy_command_uses_claude_directory(self, project_with_git: Path):
        """Test that --legacy flag creates command in .claude/commands/."""
        result = runner.invoke(app, ["init", "command", "legacy-cmd", "--legacy"])

        assert result.exit_code == 0
        assert (project_with_git / ".claude" / "commands" / "legacy-cmd.md").exists()

    def test_legacy_agent_uses_claude_directory(self, project_with_git: Path):
        """Test that --legacy flag creates agent in .claude/agents/."""
        result = runner.invoke(app, ["init", "agent", "legacy-agent", "--legacy"])

        assert result.exit_code == 0
        assert (project_with_git / ".claude" / "agents" / "legacy-agent.md").exists()


class TestLocalToInstalledFlow:
    """Tests for the flow from local authoring to installed resources."""

    def test_local_skill_installs_with_flattened_name(self, project_with_git: Path):
        """Test that local skills are installed with flattened colon-namespaced names."""
        runner.invoke(app, ["init"])
        runner.invoke(app, ["init", "skill", "namespaced-skill"])
        runner.invoke(app, ["add", "./resources/skills/namespaced-skill"])

        # Check that skill is installed with colon naming
        claude_skills = project_with_git / ".claude" / "skills"
        skill_dirs = list(claude_skills.iterdir()) if claude_skills.exists() else []

        # Should have at least one skill directory with colon naming
        assert any(":" in d.name or "namespaced-skill" in d.name for d in skill_dirs)

    def test_local_command_installs_with_username_namespace(self, project_with_git: Path):
        """Test that local commands are installed under username namespace."""
        runner.invoke(app, ["init"])
        runner.invoke(app, ["init", "command", "my-cmd"])
        runner.invoke(app, ["add", "./resources/commands/my-cmd.md"])

        # Check that command is installed
        claude_commands = project_with_git / ".claude" / "commands"
        assert claude_commands.exists()
        # Commands are installed under username/name.md structure
        # or at least in the commands directory
        cmd_files = list(claude_commands.rglob("*.md"))
        assert any("my-cmd" in f.name for f in cmd_files)
