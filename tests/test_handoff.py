"""Tests for the `handoff` command — paste-ready transcripts for another agent."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from claude_backup.cli import main
from claude_backup.exporter import detect_handoff_language, render_handoff
from claude_backup.parser import parse_session
from claude_backup.scanner import scan_projects


def _abc_session(claude_home: Path):
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    return next(s for s in fake.sessions if s.session_id == "abc-123")


def _real_format_session(claude_home: Path):
    projects = scan_projects(claude_home)
    real = next(p for p in projects if p.name == "real-format-project")
    return real.sessions[0]


def test_handoff_includes_framing_title_and_transcript(claude_home: Path) -> None:
    """The output contains: framing line, session title, and the dialogue itself."""
    s = _real_format_session(claude_home)
    messages = parse_session(s.jsonl_path)
    out = render_handoff(s, messages, lang="en")

    assert "continuing a conversation" in out.lower()
    assert "Install superpowers skill from GitHub" in out  # ai-title
    assert "install superpowers skill" in out  # first user prompt
    assert "Done." in out  # last visible assistant text
    # No tool plumbing leaked in
    assert "[tool_use:" not in out
    assert "tool_result" not in out


def test_handoff_uses_dialogue_only_count(claude_home: Path) -> None:
    """The 'N messages' annotation should reflect dialogue-only count, not raw."""
    s = _real_format_session(claude_home)
    messages = parse_session(s.jsonl_path)
    out = render_handoff(s, messages, lang="en")
    # real-001.jsonl has 1 user prompt + 2 assistant text turns visible to user
    assert "(3 messages)" in out


def test_detect_handoff_language_picks_russian_for_cyrillic(claude_home: Path) -> None:
    """If the session is Russian, language detection chooses 'ru'."""
    projects = scan_projects(claude_home)
    fake = next(p for p in projects if p.name == "fake-project")
    russian = next(s for s in fake.sessions if s.session_id == "def-456")
    messages = parse_session(russian.jsonl_path)
    assert detect_handoff_language(russian, messages) == "ru"


def test_detect_handoff_language_picks_english_for_ascii(claude_home: Path) -> None:
    s = _abc_session(claude_home)
    messages = parse_session(s.jsonl_path)
    assert detect_handoff_language(s, messages) == "en"


def test_handoff_explicit_lang_overrides_detection(claude_home: Path) -> None:
    s = _real_format_session(claude_home)
    messages = parse_session(s.jsonl_path)
    en = render_handoff(s, messages, lang="en")
    ru = render_handoff(s, messages, lang="ru")
    assert "continuing a conversation" in en.lower()
    assert "продолжаешь" in ru.lower()


def test_handoff_includes_source_label(claude_home: Path) -> None:
    s = _abc_session(claude_home)
    messages = parse_session(s.jsonl_path)
    out = render_handoff(s, messages, lang="en")
    assert "Claude Code" in out


def test_cli_handoff_prints_to_stdout(claude_home: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["--claude-home", str(claude_home), "handoff", "abc-123"]
    )
    assert result.exit_code == 0, result.output
    assert "continuing a conversation" in result.output.lower()
    assert "fix auth bug" in result.output


def test_cli_handoff_writes_to_file_when_output_given(
    claude_home: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    out = tmp_path / "handoff.md"
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "handoff",
            "abc-123",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "fix auth bug" in content


def test_cli_handoff_unknown_session_returns_error(
    claude_home: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["--claude-home", str(claude_home), "handoff", "nonexistent-zzz"]
    )
    assert result.exit_code == 2
    assert "not found" in result.output.lower()


def test_cli_handoff_clipboard_tip_goes_to_stderr(claude_home: Path) -> None:
    """The clipboard tip must NOT pollute stdout — that breaks `| pbcopy`."""
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        main, ["--claude-home", str(claude_home), "handoff", "abc-123"]
    )
    assert result.exit_code == 0
    assert "pbcopy" not in result.output  # stdout
    assert "pbcopy" in result.stderr     # stderr
