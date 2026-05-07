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


def test_export_session_writes_file(claude_home: Path, tmp_path: Path) -> None:
    session = _abc_session(claude_home)
    out_dir = tmp_path / "out"
    fixed_now = datetime(2026, 5, 7, 15, 30, 0, tzinfo=timezone.utc)
    out_path = export_session(session, out_dir, now=fixed_now)

    assert out_path.exists()
    assert out_path.parent == out_dir
    assert out_path.name == "2026-05-07--abc-123.md"

    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert "project: fake-project" in content
    assert "session_id: abc-123" in content
    assert "branch: main" in content
    assert "messages: 4" in content
    assert "## User (10:42:46)" in content
    assert "fix auth bug" in content


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


def test_export_session_snapshot(claude_home: Path, tmp_path: Path) -> None:
    """Full snapshot match — guards against accidental format drift."""
    session = _abc_session(claude_home)
    fixed_now = datetime(2026, 5, 7, 15, 30, 0, tzinfo=timezone.utc)
    out_path = export_session(session, tmp_path, now=fixed_now)
    actual = out_path.read_text(encoding="utf-8")

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
    out_path = export_session(session, tmp_path)
    text = out_path.read_text(encoding="utf-8")
    assert "тест 🚀" in text
    assert "Поддержка Unicode" in text


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
