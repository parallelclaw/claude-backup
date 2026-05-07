"""Tests for scanner module."""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_backup.scanner import (
    ProjectInfo,
    SessionInfo,
    find_session,
    scan_projects,
)


def test_scan_returns_projects(claude_home: Path) -> None:
    projects = scan_projects(claude_home)
    names = {p.name for p in projects}
    assert names == {"fake-project", "empty-project", "real-format-project"}


def test_scan_loads_sessions_from_index(claude_home: Path) -> None:
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    ids = {s.session_id for s in fake.sessions}
    # All from index + orphans (corrupt, empty, orphan)
    assert {"abc-123", "def-456", "ghost-789", "orphan-999", "corrupt-000", "empty-aaa"} <= ids


def test_session_info_populated_from_index(claude_home: Path) -> None:
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    abc = next(s for s in fake.sessions if s.session_id == "abc-123")
    assert abc.first_prompt == "fix auth bug"
    assert abc.message_count == 4
    assert abc.created == "2026-05-07T10:42:00Z"
    assert abc.git_branch == "main"
    assert abc.jsonl_path is not None
    assert abc.jsonl_path.exists()


def test_orphan_jsonl_metadata_computed_from_file(claude_home: Path) -> None:
    """Orphan sessions (no entry in index) get metadata streamed from the JSONL itself."""
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    orphan = next(s for s in fake.sessions if s.session_id == "orphan-999")
    assert orphan.first_prompt == "session not in the index"
    assert orphan.message_count == 2
    assert orphan.jsonl_path is not None


def test_indexed_session_with_no_jsonl_has_none_path(claude_home: Path) -> None:
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    ghost = next(s for s in fake.sessions if s.session_id == "ghost-789")
    assert ghost.jsonl_path is None


def test_project_without_index_still_loaded(claude_home: Path) -> None:
    projects = scan_projects(claude_home)
    empty = next(p for p in projects if p.name == "empty-project")
    assert len(empty.sessions) == 1
    assert empty.sessions[0].session_id == "lonely-001"


def test_missing_claude_home_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        scan_projects(tmp_path / "does-not-exist")


def test_claude_home_must_be_dir(tmp_path: Path) -> None:
    """Passing a file instead of a directory is treated the same as 'no data found'."""
    f = tmp_path / "afile"
    f.write_text("x")
    with pytest.raises(FileNotFoundError):
        scan_projects(f, cowork_home=tmp_path / "no-cowork")


def test_find_session_locates_by_id(claude_home: Path) -> None:
    s = find_session("abc-123", claude_home)
    assert s is not None
    assert s.session_id == "abc-123"


def test_find_session_returns_none_when_missing(claude_home: Path) -> None:
    assert find_session("nope-xxx", claude_home) is None


def test_dataclasses_are_constructible() -> None:
    s = SessionInfo(project="p", session_id="s")
    p = ProjectInfo(name="p", path=Path("."), sessions=[s])
    assert p.sessions[0].session_id == "s"


def test_code_session_links_subagent_files(claude_home: Path) -> None:
    """Claude Code sessions also use subagents (not just Cowork). The scanner
    should pick up `<session-id>/subagents/agent-*.jsonl` files."""
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    abc = next(s for s in fake.sessions if s.session_id == "abc-123")
    assert len(abc.subagent_jsonl_paths) == 1
    assert abc.subagent_jsonl_paths[0].name == "agent-acode1.jsonl"


def test_sessions_without_subagents_have_empty_list(claude_home: Path) -> None:
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    def_session = next(s for s in fake.sessions if s.session_id == "def-456")
    assert def_session.subagent_jsonl_paths == []


def test_corrupt_index_does_not_crash(tmp_path: Path) -> None:
    proj = tmp_path / "projects" / "broken"
    proj.mkdir(parents=True)
    (proj / "sessions-index.json").write_text("{not json")
    (proj / "x.jsonl").write_text('{"role":"user","content":"hi"}\n')
    projects = scan_projects(tmp_path / "projects")
    assert len(projects) == 1
    assert projects[0].sessions[0].session_id == "x"
