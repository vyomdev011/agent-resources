"""Tests for centralized handle parsing and conversion module."""

import pytest

from agr.handle import (
    ParsedHandle,
    parse_handle,
    skill_dirname_to_toml_handle,
    toml_handle_to_skill_dirname,
)


class TestParseHandle:
    """Test handle parsing for all formats."""

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_handle("")
        assert result.username is None
        assert result.name == ""
        assert result.path_segments == []

    def test_simple_name(self):
        """Test parsing simple resource name."""
        result = parse_handle("seo")
        assert result.username is None
        assert result.name == "seo"
        assert result.simple_name == "seo"
        assert result.path_segments == ["seo"]

    def test_two_part_slash(self):
        """Test parsing user/name format."""
        result = parse_handle("kasperjunge/seo")
        assert result.username == "kasperjunge"
        assert result.name == "seo"
        assert result.repo is None
        assert result.path_segments == ["seo"]

    def test_three_part_slash(self):
        """Test parsing user/nested/name format.

        Note: 3-part handles are treated as user/nested_path/name for skill
        dirname purposes. The middle segment is part of path_segments,
        not treated as a repo name.
        """
        result = parse_handle("user/repo/command")
        assert result.username == "user"
        assert result.name == "command"
        # All segments after username are in path_segments for skill dirname conversion
        assert result.path_segments == ["repo", "command"]

    def test_four_part_slash(self):
        """Test parsing user/nested/more/name format."""
        result = parse_handle("user/nested/more/name")
        assert result.username == "user"
        assert result.name == "name"
        assert result.path_segments == ["nested", "more", "name"]

    def test_colon_format_simple(self):
        """Test parsing user:name colon format."""
        result = parse_handle("kasperjunge:seo")
        assert result.username == "kasperjunge"
        assert result.name == "seo"
        assert result.path_segments == ["seo"]

    def test_colon_format_nested(self):
        """Test parsing user:nested:name colon format."""
        result = parse_handle("kasperjunge:product-strategy:growth-hacker")
        assert result.username == "kasperjunge"
        assert result.name == "growth-hacker"
        assert result.path_segments == ["product-strategy", "growth-hacker"]


class TestParsedHandleSimpleName:
    """Test the simple_name property."""

    def test_simple_name_from_simple_input(self):
        """simple_name returns the name when there are no segments."""
        parsed = ParsedHandle(name="test")
        assert parsed.simple_name == "test"

    def test_simple_name_from_segments(self):
        """simple_name returns last segment."""
        parsed = ParsedHandle(name="ignored", path_segments=["nested", "actual"])
        assert parsed.simple_name == "actual"


class TestParsedHandleToTomlHandle:
    """Test conversion to toml handle format."""

    def test_to_toml_handle_simple(self):
        """Test conversion with username and simple name."""
        parsed = ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"])
        assert parsed.to_toml_handle() == "kasperjunge/seo"

    def test_to_toml_handle_with_repo(self):
        """Test conversion with explicit repo."""
        parsed = ParsedHandle(
            username="user", repo="repo", name="cmd", path_segments=["cmd"]
        )
        assert parsed.to_toml_handle() == "user/repo/cmd"

    def test_to_toml_handle_nested(self):
        """Test conversion with nested path segments."""
        parsed = ParsedHandle(
            username="kasperjunge",
            name="growth-hacker",
            path_segments=["product-strategy", "growth-hacker"],
        )
        assert parsed.to_toml_handle() == "kasperjunge/product-strategy/growth-hacker"

    def test_to_toml_handle_no_username(self):
        """Test conversion without username returns just name."""
        parsed = ParsedHandle(name="seo", path_segments=["seo"])
        assert parsed.to_toml_handle() == "seo"


class TestParsedHandleToSkillDirname:
    """Test conversion to skill directory name format."""

    def test_to_skill_dirname_simple(self):
        """Test conversion with username and simple name."""
        parsed = ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"])
        assert parsed.to_skill_dirname() == "kasperjunge:seo"

    def test_to_skill_dirname_nested(self):
        """Test conversion with nested path segments."""
        parsed = ParsedHandle(
            username="kasperjunge",
            name="growth-hacker",
            path_segments=["product-strategy", "growth-hacker"],
        )
        assert parsed.to_skill_dirname() == "kasperjunge:product-strategy:growth-hacker"

    def test_to_skill_dirname_no_username(self):
        """Test conversion without username returns just name."""
        parsed = ParsedHandle(name="seo", path_segments=["seo"])
        assert parsed.to_skill_dirname() == "seo"


class TestMatchesTomlHandle:
    """Test handle matching logic."""

    def test_exact_match(self):
        """Test exact match between parsed and toml handle."""
        parsed = parse_handle("kasperjunge/seo")
        assert parsed.matches_toml_handle("kasperjunge/seo")

    def test_simple_name_matches_full(self):
        """Test simple name matches full handle."""
        parsed = parse_handle("seo")
        assert parsed.matches_toml_handle("kasperjunge/seo")

    def test_different_username_no_match(self):
        """Test different usernames don't match."""
        parsed = parse_handle("other/seo")
        assert not parsed.matches_toml_handle("kasperjunge/seo")

    def test_different_name_no_match(self):
        """Test different names don't match."""
        parsed = parse_handle("kasperjunge/other")
        assert not parsed.matches_toml_handle("kasperjunge/seo")

    def test_three_part_matches(self):
        """Test 3-part ref matching."""
        parsed = parse_handle("user/repo/cmd")
        assert parsed.matches_toml_handle("user/repo/cmd")

    def test_colon_format_matches_slash(self):
        """Test colon format matches slash format."""
        parsed = parse_handle("kasperjunge:seo")
        assert parsed.matches_toml_handle("kasperjunge/seo")

    def test_nested_colon_matches_nested_slash(self):
        """Test nested colon format matches nested slash format."""
        parsed = parse_handle("k:product-strategy:growth-hacker")
        assert parsed.matches_toml_handle("k/product-strategy/growth-hacker")


class TestSkillDirnameToTomlHandle:
    """Test reverse conversion from dirname to toml handle."""

    def test_simple(self):
        """Test simple conversion."""
        assert skill_dirname_to_toml_handle("kasperjunge:seo") == "kasperjunge/seo"

    def test_nested(self):
        """Test nested conversion."""
        result = skill_dirname_to_toml_handle("kasperjunge:product-strategy:growth-hacker")
        assert result == "kasperjunge/product-strategy/growth-hacker"


class TestTomlHandleToSkillDirname:
    """Test conversion from toml handle to dirname."""

    def test_simple(self):
        """Test simple conversion."""
        assert toml_handle_to_skill_dirname("kasperjunge/seo") == "kasperjunge:seo"

    def test_nested(self):
        """Test nested conversion."""
        result = toml_handle_to_skill_dirname("kasperjunge/product-strategy/growth-hacker")
        assert result == "kasperjunge:product-strategy:growth-hacker"

    def test_with_nested_path(self):
        """Test conversion with nested path (3-part)."""
        # 3-part handles are treated as user/nested/name, so all segments
        # after username become part of the skill dirname
        result = toml_handle_to_skill_dirname("user/nested/skill")
        assert result == "user:nested:skill"


class TestRoundTrip:
    """Test round-trip conversions."""

    def test_toml_to_dirname_to_toml(self):
        """Test toml -> dirname -> toml round trip."""
        original = "kasperjunge/seo"
        dirname = toml_handle_to_skill_dirname(original)
        back = skill_dirname_to_toml_handle(dirname)
        assert back == original

    def test_nested_toml_to_dirname_to_toml(self):
        """Test nested toml -> dirname -> toml round trip."""
        original = "kasperjunge/product-strategy/growth-hacker"
        dirname = toml_handle_to_skill_dirname(original)
        assert dirname == "kasperjunge:product-strategy:growth-hacker"
        back = skill_dirname_to_toml_handle(dirname)
        assert back == original

    def test_dirname_to_toml_to_dirname(self):
        """Test dirname -> toml -> dirname round trip."""
        original = "kasperjunge:seo"
        toml = skill_dirname_to_toml_handle(original)
        back = toml_handle_to_skill_dirname(toml)
        assert back == original

    def test_nested_dirname_to_toml_to_dirname(self):
        """Test nested dirname -> toml -> dirname round trip."""
        original = "kasperjunge:product-strategy:growth-hacker"
        toml = skill_dirname_to_toml_handle(original)
        back = toml_handle_to_skill_dirname(toml)
        assert back == original
