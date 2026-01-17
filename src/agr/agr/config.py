"""Configuration management for agr.toml."""

from dataclasses import dataclass, field
from pathlib import Path

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.exceptions import TOMLKitError

from agr.exceptions import ConfigParseError


@dataclass
class DependencySpec:
    """Specification for a dependency in agr.toml."""

    type: str | None = None  # "skill", "command", "agent"


@dataclass
class AgrConfig:
    """
    Configuration loaded from agr.toml.

    The config file tracks dependencies with fully qualified references:

    [dependencies]
    "kasperjunge/commit" = {}
    "alice/review" = { type = "skill" }
    """

    dependencies: dict[str, DependencySpec] = field(default_factory=dict)
    _document: TOMLDocument | None = field(default=None, repr=False)
    _path: Path | None = field(default=None, repr=False)

    @classmethod
    def load(cls, path: Path) -> "AgrConfig":
        """
        Load configuration from an agr.toml file.

        Args:
            path: Path to the agr.toml file

        Returns:
            AgrConfig instance with loaded dependencies

        Raises:
            ConfigParseError: If the file contains invalid TOML
        """
        if not path.exists():
            config = cls()
            config._path = path
            return config

        try:
            content = path.read_text()
            doc = tomlkit.parse(content)
        except TOMLKitError as e:
            raise ConfigParseError(f"Invalid TOML in {path}: {e}")

        config = cls()
        config._document = doc
        config._path = path

        # Parse dependencies section
        deps_section = doc.get("dependencies", {})
        for ref, spec in deps_section.items():
            if isinstance(spec, dict):
                config.dependencies[ref] = DependencySpec(
                    type=spec.get("type")
                )
            else:
                config.dependencies[ref] = DependencySpec()

        return config

    def save(self, path: Path | None = None) -> None:
        """
        Save configuration to an agr.toml file.

        Args:
            path: Path to save to (uses original path if not specified)
        """
        save_path = path or self._path
        if save_path is None:
            raise ValueError("No path specified for saving config")

        # Use existing document to preserve comments, or create new one
        if self._document is not None:
            doc = self._document
        else:
            doc = tomlkit.document()

        # Update dependencies section
        if "dependencies" not in doc:
            doc["dependencies"] = tomlkit.table()

        deps_table = doc["dependencies"]

        # Clear existing dependencies and rebuild
        # First, collect keys to remove
        existing_keys = list(deps_table.keys())
        for key in existing_keys:
            del deps_table[key]

        # Add current dependencies
        for ref, spec in self.dependencies.items():
            if spec.type:
                deps_table[ref] = {"type": spec.type}
            else:
                deps_table[ref] = {}

        save_path.write_text(tomlkit.dumps(doc))
        self._document = doc
        self._path = save_path

    def add_dependency(self, ref: str, spec: DependencySpec) -> None:
        """
        Add or update a dependency.

        Args:
            ref: Dependency reference (e.g., "kasperjunge/commit")
            spec: Dependency specification
        """
        self.dependencies[ref] = spec

    def remove_dependency(self, ref: str) -> None:
        """
        Remove a dependency.

        Args:
            ref: Dependency reference to remove
        """
        self.dependencies.pop(ref, None)


def find_config(start_path: Path | None = None) -> Path | None:
    """
    Find agr.toml by walking up from the start path to the git root.

    Args:
        start_path: Directory to start searching from (defaults to cwd)

    Returns:
        Path to agr.toml if found, None otherwise
    """
    current = start_path or Path.cwd()

    while True:
        config_path = current / "agr.toml"
        if config_path.exists():
            return config_path

        # Check if we've reached git root
        if (current / ".git").exists():
            return None

        # Move to parent
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None
        current = parent


def get_or_create_config(start_path: Path | None = None) -> tuple[Path, AgrConfig]:
    """
    Get existing config or create a new one in cwd.

    Args:
        start_path: Directory to start searching from (defaults to cwd)

    Returns:
        Tuple of (path to config, AgrConfig instance)
    """
    existing = find_config(start_path)
    if existing:
        return existing, AgrConfig.load(existing)

    # Create new config in cwd
    cwd = start_path or Path.cwd()
    config_path = cwd / "agr.toml"

    config = AgrConfig()
    config.save(config_path)

    return config_path, config
