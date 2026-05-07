"""Tests for the real Claude Code JSONL format (nested message + queue-operation noise)."""

from __future__ import annotations

from pathlib import Path

from claude_backup.parser import extract_session_title, parse_session
from claude_backup.scanner import decode_project_name, scan_projects


def test_real_format_skips_queue_ops_and_attachments(claude_home: Path) -> None:
    f = claude_home / "real-format-project" / "real-001.jsonl"
    messages = parse_session(f)
    # 1 user prompt + 1 assistant + 1 tool_result + 1 assistant = 4
    assert len(messages) == 4
    roles = [m.role for m in messages]
    assert roles == ["user", "assistant", "user", "assistant"]


def test_real_format_extracts_assistant_text(claude_home: Path) -> None:
    f = claude_home / "real-format-project" / "real-001.jsonl"
    messages = parse_session(f)
    assistant_texts = [m.content for m in messages if m.role == "assistant"]
    assert "Installing now." in assistant_texts[0]
    assert "[tool_use: Bash]" in assistant_texts[0]
    assert assistant_texts[1] == "Done."


def test_real_format_extracts_assistant_model(claude_home: Path) -> None:
    f = claude_home / "real-format-project" / "real-001.jsonl"
    messages = parse_session(f)
    models = [m.model for m in messages if m.role == "assistant"]
    assert models == ["claude-sonnet-4-6", "claude-sonnet-4-6"]


def test_real_format_extracts_user_tool_result(claude_home: Path) -> None:
    f = claude_home / "real-format-project" / "real-001.jsonl"
    messages = parse_session(f)
    user_msgs = [m.content for m in messages if m.role == "user"]
    assert user_msgs[0] == "install superpowers skill"
    assert "installed" in user_msgs[1]


def test_extract_session_title(claude_home: Path) -> None:
    f = claude_home / "real-format-project" / "real-001.jsonl"
    title = extract_session_title(f)
    assert title == "Install superpowers skill from GitHub"


def test_extract_session_title_returns_empty_when_absent(fake_project_path: Path) -> None:
    title = extract_session_title(fake_project_path / "abc-123.jsonl")
    assert title == ""


def test_scanner_computes_metadata_from_real_jsonl(claude_home: Path) -> None:
    projects = scan_projects(claude_home)
    real = next(p for p in projects if p.name == "real-format-project")
    assert len(real.sessions) == 1
    s = real.sessions[0]
    assert s.first_prompt == "install superpowers skill"
    assert s.message_count == 4
    assert s.title == "Install superpowers skill from GitHub"
    assert s.created.startswith("2026-04-22")


def test_decode_project_name() -> None:
    assert decode_project_name("-Users-macbook-Documents-Claude") == "Documents/Claude"
    assert decode_project_name("normal-name") == "normal-name"
    assert decode_project_name("-foo-bar") == "foo/bar"
    assert decode_project_name("-just-one") == "just/one"
    assert decode_project_name("") == ""
