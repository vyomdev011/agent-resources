"""Test configuration and fixtures."""

import pytest
from pathlib import Path

from agr.config import AgrConfig


@pytest.fixture(autouse=True)
def cleanup_test_entries():
    """Clean up any testuser entries from agr.toml after each test.

    This is a safety net in case tests accidentally write to the real agr.toml
    instead of using a temp directory or mocking _add_to_agr_toml.
    """
    yield

    # Find project root agr.toml
    agr_toml = Path(__file__).parent.parent / "agr.toml"
    if not agr_toml.exists():
        return

    config = AgrConfig.load(agr_toml)
    original_count = len(config.dependencies)

    # Filter out testuser entries (both handle and path based)
    config.dependencies = [
        dep for dep in config.dependencies
        if not (
            (dep.handle and dep.handle.startswith("testuser/"))
            or (dep.path and "testuser" in dep.path)
        )
    ]

    # Only save if we removed something
    if len(config.dependencies) != original_count:
        config.save(agr_toml)
