"""Tests for parser module."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from claude_backup.parser import Message, parse_session, session_summary


def test_parse_basic_session(fake_project_path: Path) -> None:
    messages = parse_session(fake_project_path / "abc-123.jsonl")
    assert len(messages) == 4
    assert messages[0].role == "user"
    assert messages[0].content == "fix auth bug"
    assert messages[0].timestamp == "2026-05-07T10:42:46Z"
    assert messages[1].role == "assistant"
    assert messages[1].model == "claude-sonnet-4"


def test_parse_handles_list_content(fake_project_path: Path) -> None:
    messages = parse_session(fake_project_path / "abc-123.jsonl")
    last = messages[-1]
    assert "All done." in last.content
    assert "[tool_use: Bash]" in last.content


def test_parse_unicode_content(fake_project_path: Path) -> None:
    messages = parse_session(fake_project_path / "def-456.jsonl")
    assert messages[0].content == "add unicode support — тест 🚀"
    assert "Unicode" in messages[1].content
    assert "✅" in messages[1].content


def test_parse_skips_malformed_lines(fake_project_path: Path) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        messages = parse_session(fake_project_path / "corrupt-000.jsonl")
    # 3 valid lines, 2 malformed
    assert len(messages) == 3
    # Warnings emitted for the 2 malformed lines
    malformed = [warn for warn in w if "malformed" in str(warn.message)]
    assert len(malformed) == 2


def test_parse_empty_file_returns_empty_list(fake_project_path: Path) -> None:
    messages = parse_session(fake_project_path / "empty-aaa.jsonl")
    assert messages == []


def test_parse_missing_file_returns_empty_with_warning(tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        messages = parse_session(tmp_path / "nope.jsonl")
    assert messages == []
    assert any("not found" in str(warn.message) for warn in w)


def test_parse_skips_lines_without_role(tmp_path: Path) -> None:
    f = tmp_path / "x.jsonl"
    f.write_text(
        '{"role":"user","content":"hi"}\n'
        '{"content":"no role"}\n'
        '"just a string"\n'
        '{"role":"assistant","content":"reply"}\n'
    )
    messages = parse_session(f)
    roles = [m.role for m in messages]
    assert roles == ["user", "assistant"]


def test_parse_handles_dict_content_with_text_block(tmp_path: Path) -> None:
    f = tmp_path / "x.jsonl"
    f.write_text(
        '{"role":"user","content":[{"type":"text","text":"hello"}]}\n'
    )
    messages = parse_session(f)
    assert messages[0].content == "hello"


def test_parse_handles_tool_result_block(tmp_path: Path) -> None:
    f = tmp_path / "x.jsonl"
    f.write_text(
        '{"role":"tool_result","content":[{"type":"tool_result","content":"output"}]}\n'
    )
    messages = parse_session(f)
    assert "output" in messages[0].content


def test_parse_handles_none_content(tmp_path: Path) -> None:
    f = tmp_path / "x.jsonl"
    f.write_text('{"role":"assistant","content":null}\n')
    messages = parse_session(f)
    assert messages[0].content == ""


def test_session_summary(fake_project_path: Path) -> None:
    summary = session_summary(fake_project_path / "abc-123.jsonl")
    assert summary["message_count"] == 4
    assert summary["first_prompt"] == "fix auth bug"
    assert summary["model"] == "claude-sonnet-4"


def test_message_dataclass_default_raw() -> None:
    m = Message(role="user", content="x")
    assert m.raw == {}
