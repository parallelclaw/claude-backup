"""Shared pytest fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def claude_home(tmp_path: Path) -> Path:
    """Copy fixtures into a temp Claude projects root."""
    dest = tmp_path / "projects"
    shutil.copytree(FIXTURES_DIR, dest)
    return dest


@pytest.fixture
def fake_project_path(claude_home: Path) -> Path:
    return claude_home / "fake-project"
