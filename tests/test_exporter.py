"""Tests for exporter module."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from claude_backup.exporter import export_session, render_markdown
from claude_backup.parser import Message
from claude_backup.scanner import SessionInfo, scan_projects


def _abc_session(claude_home: Path) -> SessionInfo:
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    return next(s for s in fake.sessions if s.session_id == "abc-123")


def test_render_markdown_frontmatter_and_header() -> None:
    session = SessionInfo(
        project="my-webapp",
        session_id="abc-123",
        message_count=42,
        git_branch="main",
    )
    messages = [
        Message(role="user", content="fix auth bug", timestamp="2026-05-07T10:42:46Z"),
        Message(
            role="assistant",
            content="Here's the fix...",
            timestamp="2026-05-07T10:42:50Z",
            model="claude-sonnet-4",
        ),
    ]
    fixed_now = datetime(2026, 5, 7, 15, 30, 0, tzinfo=timezone.utc)
    md = render_markdown(session, messages, now=fixed_now)

    assert md.startswith("---\n")
    assert "project: my-webapp" in md
    assert "session_id: abc-123" in md
    assert "branch: main" in md
    assert "model: claude-sonnet-4" in md
    assert "messages: 42" in md
    assert "exported_at: 2026-05-07T15:30:00Z" in md
    assert "# my-webapp / main / abc-123" in md
    assert "## User (10:42:46)" in md
    assert "fix auth bug" in md
    assert "## Assistant (10:42:50)" in md
    assert "Here's the fix..." in md


def test_render_markdown_handles_empty_session() -> None:
    session = SessionInfo(project="p", session_id="s")
    md = render_markdown(session, [], now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert "_No messages._" in md
    assert "# p / no-branch / s" in md


def test_render_markdown_unicode() -> None:
    session = SessionInfo(project="p", session_id="s", git_branch="main")
    messages = [Message(role="user", content="тест 🚀", timestamp="2026-05-06T14:00:00Z")]
    md = render_markdown(session, messages, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert "тест 🚀" in md


def test_export_session_default_writes_both_files(
    claude_home: Path, tmp_path: Path
) -> None:
    session = _abc_session(claude_home)
    out_dir = tmp_path / "out"
    fixed_now = datetime(2026, 5, 7, 15, 30, 0, tzinfo=timezone.utc)
    paths = export_session(session, out_dir, now=fixed_now)

    assert len(paths) == 2
    names = sorted(p.name for p in paths)
    assert names == [
        "2026-05-07--abc-123.full.md",
        "2026-05-07--abc-123.md",
    ]

    minimal_path = next(p for p in paths if p.name.endswith(".md") and ".full" not in p.name)
    full_path = next(p for p in paths if p.name.endswith(".full.md"))

    minimal = minimal_path.read_text(encoding="utf-8")
    full = full_path.read_text(encoding="utf-8")

    # Default `<id>.md` is the clean dialogue version
    assert "mode: dialogue-only" in minimal
    assert "[tool_use:" not in minimal
    assert "fix auth bug" in minimal

    # `.full.md` is the audit copy
    assert "mode: dialogue-only" not in full
    assert "[tool_use: Bash]" in full
    assert "fix auth bug" in full


def test_export_session_creates_output_dir(claude_home: Path, tmp_path: Path) -> None:
    session = _abc_session(claude_home)
    out_dir = tmp_path / "deep" / "nested" / "out"
    export_session(session, out_dir)
    assert out_dir.is_dir()


def test_export_missing_jsonl_raises(claude_home: Path, tmp_path: Path) -> None:
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    ghost = next(s for s in fake.sessions if s.session_id == "ghost-789")
    with pytest.raises(FileNotFoundError):
        export_session(ghost, tmp_path / "out")


def test_export_session_snapshot_full(claude_home: Path, tmp_path: Path) -> None:
    """Snapshot match for the .full.md audit copy — guards against format drift."""
    session = _abc_session(claude_home)
    fixed_now = datetime(2026, 5, 7, 15, 30, 0, tzinfo=timezone.utc)
    paths = export_session(session, tmp_path, now=fixed_now, mode="full")
    assert len(paths) == 1
    actual = paths[0].read_text(encoding="utf-8")

    expected = (
        "---\n"
        "project: fake-project\n"
        "session_id: abc-123\n"
        "branch: main\n"
        "model: claude-sonnet-4\n"
        "messages: 4\n"
        "exported_at: 2026-05-07T15:30:00Z\n"
        "---\n"
        "\n"
        "# fake-project / main / abc-123\n"
        "\n"
        "## User (10:42:46)\n"
        "fix auth bug\n"
        "\n"
        "## Assistant (10:42:50)\n"
        "Here's the fix...\n"
        "\n"
        "## Tool Result (10:43:01)\n"
        "patch applied\n"
        "\n"
        "## Assistant (10:43:05)\n"
        "All done.\n"
        "[tool_use: Bash]\n"
    )
    assert actual == expected


def test_export_unicode_session_roundtrip(claude_home: Path, tmp_path: Path) -> None:
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    session = next(s for s in fake.sessions if s.session_id == "def-456")
    paths = export_session(session, tmp_path)
    combined = "\n".join(p.read_text(encoding="utf-8") for p in paths)
    assert "тест 🚀" in combined
    assert "Поддержка Unicode" in combined


def test_render_markdown_falls_back_to_message_branch_and_model() -> None:
    session = SessionInfo(project="p", session_id="s")  # no branch/model
    messages = [
        Message(role="user", content="hi", timestamp="2026-01-01T00:00:00Z", git_branch="dev"),
        Message(role="assistant", content="hi back", model="claude-haiku-4-5"),
    ]
    md = render_markdown(session, messages, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert "branch: dev" in md
    assert "model: claude-haiku-4-5" in md


def test_render_markdown_quotes_special_characters() -> None:
    session = SessionInfo(
        project="p",
        session_id="s",
        first_prompt="contains: a colon",
        git_branch="main",
    )
    md = render_markdown(session, [], now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    # Should not produce a malformed YAML scalar in fields
    assert "---" in md
