"""Shared pytest fixtures and configuration for vibe-stack tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


# Override tmp_path base directory to avoid Windows permission issues
# with the default system temp directory.
@pytest.fixture(scope="session")
def tmp_path_factory_basetemp() -> Path:
    """Use a writable temp directory for tmp_path fixtures."""
    base = Path(os.environ.get("TEMP", "/tmp")) / "vibe-stack-tests"
    base.mkdir(parents=True, exist_ok=True)
    return base
