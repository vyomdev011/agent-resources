"""Centralized handle parsing and conversion for agr.

This module provides a single source of truth for parsing and converting
resource handles between different formats used in the codebase:

| System          | Format    | Example                                | Used In                  |
|-----------------|-----------|----------------------------------------|--------------------------|
| External/Config | Slash `/` | `kasperjunge/seo`                      | agr.toml, CLI input      |
| Internal/Storage| Colon `:` | `kasperjunge:seo`                      | Skill directories on disk|

All code paths that need to parse or convert handles should use this module.
"""

from dataclasses import dataclass, field


@dataclass
class ParsedHandle:
    """Parsed resource handle with all components.

    Attributes:
        username: GitHub username (e.g., "kasperjunge"), None for simple names
        repo: Repository name (e.g., "agent-resources"), None if using default
        name: Resource name (the final/leaf segment)
        path_segments: Full list of path segments after username
                       e.g., ["seo"] or ["product-strategy", "growth-hacker"]
    """

    username: str | None = None
    repo: str | None = None
    name: str = ""
    path_segments: list[str] = field(default_factory=list)

    @property
    def simple_name(self) -> str:
        """Just the resource name (last segment)."""
        return self.path_segments[-1] if self.path_segments else self.name

    def to_toml_handle(self) -> str:
        """Convert to agr.toml format: user/name or user/repo/name.

        Examples:
            >>> ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"]).to_toml_handle()
            'kasperjunge/seo'
            >>> ParsedHandle(username="user", repo="repo", name="cmd", path_segments=["cmd"]).to_toml_handle()
            'user/repo/cmd'
            >>> ParsedHandle(username="k", name="g", path_segments=["product-strategy", "growth-hacker"]).to_toml_handle()
            'k/product-strategy/growth-hacker'
        """
        if not self.username:
            return self.name

        if self.repo:
            # With explicit repo: user/repo/path_segments
            parts = [self.username, self.repo] + self.path_segments
            return "/".join(parts)

        # Without repo: user/path_segments
        return f"{self.username}/{'/'.join(self.path_segments)}"

    def to_skill_dirname(self) -> str:
        """Convert to skill directory name: user:name or user:nested:name.

        Skills use a flattened colon-separated format for directory names
        because Claude Code only discovers top-level directories in .claude/skills/.

        Examples:
            >>> ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"]).to_skill_dirname()
            'kasperjunge:seo'
            >>> ParsedHandle(username="k", name="g", path_segments=["product-strategy", "growth-hacker"]).to_skill_dirname()
            'k:product-strategy:growth-hacker'
        """
        if not self.username:
            return self.name

        parts = [self.username] + self.path_segments
        return ":".join(parts)

    def matches_toml_handle(self, toml_handle: str) -> bool:
        """Check if this parsed handle matches a handle from agr.toml.

        Matching is done by comparing:
        1. Simple names must be equal
        2. If both have usernames, they must match
        3. If one has no username, match by simple name only

        Examples:
            >>> parse_handle("kasperjunge/seo").matches_toml_handle("kasperjunge/seo")
            True
            >>> parse_handle("seo").matches_toml_handle("kasperjunge/seo")
            True
            >>> parse_handle("other/seo").matches_toml_handle("kasperjunge/seo")
            False
        """
        other = parse_handle(toml_handle)

        # Match if simple names are equal and usernames match (if both present)
        if self.simple_name != other.simple_name:
            return False

        if self.username and other.username:
            return self.username == other.username

        return True


def parse_handle(handle: str) -> ParsedHandle:
    """Parse any handle format into normalized components.

    Supports:
    - "name" -> simple name
    - "user/name" -> 2-part slash format (config/CLI)
    - "user/repo/name" -> 3-part slash format
    - "user/nested/name" -> multi-part slash format
    - "user:name" -> colon format (from filesystem)
    - "user:nested:name" -> nested colon format

    Args:
        handle: The handle string to parse

    Returns:
        ParsedHandle with all components extracted

    Examples:
        >>> parse_handle("seo").name
        'seo'
        >>> h = parse_handle("kasperjunge/seo")
        >>> (h.username, h.name)
        ('kasperjunge', 'seo')
        >>> h = parse_handle("kasperjunge:seo")
        >>> (h.username, h.name, h.to_toml_handle())
        ('kasperjunge', 'seo', 'kasperjunge/seo')
    """
    if not handle:
        return ParsedHandle(name="")

    # Colon format (filesystem): user:name or user:nested:name
    if ":" in handle and "/" not in handle:
        parts = handle.split(":")
        return ParsedHandle(
            username=parts[0],
            name=parts[-1],
            path_segments=parts[1:],
        )

    # Slash format (config/CLI): user/name or user/repo/name or user/nested/name
    if "/" in handle:
        parts = handle.split("/")

        if len(parts) == 2:
            # user/name
            return ParsedHandle(
                username=parts[0],
                name=parts[1],
                path_segments=[parts[1]],
            )

        # For 3+ parts, we store all segments after username in path_segments
        # This allows proper round-trip conversion for skill dirnames.
        # The repo field is only set when explicitly needed for GitHub URLs,
        # but for skill dirname purposes, path_segments is what matters.
        if len(parts) >= 3:
            return ParsedHandle(
                username=parts[0],
                name=parts[-1],
                path_segments=parts[1:],
            )

    # Simple name
    return ParsedHandle(name=handle, path_segments=[handle])


def skill_dirname_to_toml_handle(dirname: str) -> str:
    """Convert skill directory name back to agr.toml handle format.

    Args:
        dirname: The skill directory name (e.g., "kasperjunge:seo")

    Returns:
        The toml handle format (e.g., "kasperjunge/seo")

    Examples:
        >>> skill_dirname_to_toml_handle("kasperjunge:seo")
        'kasperjunge/seo'
        >>> skill_dirname_to_toml_handle("k:product-strategy:growth-hacker")
        'k/product-strategy/growth-hacker'
    """
    parsed = parse_handle(dirname)
    return parsed.to_toml_handle()


def toml_handle_to_skill_dirname(toml_handle: str) -> str:
    """Convert agr.toml handle to skill directory name format.

    Args:
        toml_handle: The toml handle (e.g., "kasperjunge/seo")

    Returns:
        The skill directory name (e.g., "kasperjunge:seo")

    Examples:
        >>> toml_handle_to_skill_dirname("kasperjunge/seo")
        'kasperjunge:seo'
        >>> toml_handle_to_skill_dirname("k/product-strategy/growth-hacker")
        'k:product-strategy:growth-hacker'
    """
    parsed = parse_handle(toml_handle)
    return parsed.to_skill_dirname()
