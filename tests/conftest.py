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
def cowork_home(tmp_path: Path) -> Path:
    """A fake (empty) Cowork root. Tests that exercise Cowork seed it directly."""
    dest = tmp_path / "cowork-empty"
    dest.mkdir()
    return dest


@pytest.fixture(autouse=True)
def _isolate_real_cowork(monkeypatch, tmp_path: Path) -> None:
    """Prevent every test from accidentally scanning the developer's real
    ~/Library/Application Support/Claude/ directory. Each test gets a guaranteed-
    empty default Cowork home unless it explicitly opts in."""
    safe_default = tmp_path / "no-real-cowork"
    monkeypatch.setattr(
        "claude_backup.scanner.DEFAULT_COWORK_HOME", safe_default
    )
    monkeypatch.setattr(
        "claude_backup.scanner.DEFAULT_CLAUDE_HOME",
        tmp_path / "no-real-code",
    )


@pytest.fixture
def fake_project_path(claude_home: Path) -> Path:
    return claude_home / "fake-project"
