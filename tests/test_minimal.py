"""Tests for --minimal export mode (dialogue-only output)."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from claude_backup.cli import main
from claude_backup.exporter import export_session, render_markdown
from claude_backup.parser import dialogue_text, is_dialogue_message, parse_session
from claude_backup.scanner import scan_projects


def _real_session(claude_home: Path):
    projects = scan_projects(claude_home)
    real = next(p for p in projects if p.name == "real-format-project")
    return real.sessions[0]


def test_dialogue_text_strips_tool_use(claude_home: Path) -> None:
    """In `real-001.jsonl` the assistant says 'Installing now.' then makes a tool_use call.
    `dialogue_text` should keep the text and drop the tool_use marker."""
    f = claude_home / "real-format-project" / "real-001.jsonl"
    messages = parse_session(f)
    assistant_first = next(m for m in messages if m.role == "assistant")
    assert dialogue_text(assistant_first) == "Installing now."
    assert "[tool_use:" not in dialogue_text(assistant_first)


def test_dialogue_text_strips_tool_result(claude_home: Path) -> None:
    """The user 'tool_result' message should produce empty dialogue text."""
    f = claude_home / "real-format-project" / "real-001.jsonl"
    messages = parse_session(f)
    tool_result_user = [
        m for m in messages if m.role == "user" and "installed" in m.content
    ][0]
    assert dialogue_text(tool_result_user) == ""
    assert is_dialogue_message(tool_result_user) is False


def test_dialogue_text_strips_thinking(tmp_path: Path) -> None:
    f = tmp_path / "x.jsonl"
    f.write_text(
        '{"role":"assistant","content":['
        '{"type":"thinking","thinking":"weighing options","signature":"sig"},'
        '{"type":"text","text":"answer"}'
        ']}\n'
    )
    messages = parse_session(f)
    assert dialogue_text(messages[0]) == "answer"


def test_is_dialogue_message_true_for_user_prompt(claude_home: Path) -> None:
    f = claude_home / "real-format-project" / "real-001.jsonl"
    messages = parse_session(f)
    real_user = next(m for m in messages if m.role == "user")
    assert is_dialogue_message(real_user) is True


def test_render_markdown_minimal_drops_tool_messages(claude_home: Path) -> None:
    session = _real_session(claude_home)
    messages = parse_session(session.jsonl_path)
    md = render_markdown(session, messages, minimal=True)

    assert "[tool_use:" not in md
    assert "tool_result" not in md
    assert "installed" not in md  # tool_result content
    assert "Installing now." in md
    assert "Done." in md
    assert "install superpowers skill" in md
    assert "mode: dialogue-only" in md


def test_render_markdown_full_keeps_tool_messages(claude_home: Path) -> None:
    """Sanity: without minimal flag, tool messages are still there."""
    session = _real_session(claude_home)
    messages = parse_session(session.jsonl_path)
    md = render_markdown(session, messages, minimal=False)

    assert "[tool_use: Bash]" in md
    assert "installed" in md
    assert "mode: dialogue-only" not in md


def test_export_session_minimal_writes_separate_file(
    claude_home: Path, tmp_path: Path
) -> None:
    session = _real_session(claude_home)
    full_path = export_session(session, tmp_path, minimal=False)
    minimal_path = export_session(session, tmp_path, minimal=True)

    assert full_path != minimal_path
    assert full_path.name.endswith(".md")
    assert not full_path.name.endswith(".minimal.md")
    assert minimal_path.name.endswith(".minimal.md")

    assert "[tool_use:" in full_path.read_text(encoding="utf-8")
    assert "[tool_use:" not in minimal_path.read_text(encoding="utf-8")


def test_cli_export_with_minimal_flag(claude_home: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "backups"
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "export",
            "real-001",
            "--output",
            str(out),
            "--minimal",
        ],
    )
    assert result.exit_code == 0, result.output
    files = list(out.glob("*.minimal.md"))
    assert len(files) == 1


def test_cli_export_all_with_minimal_flag(claude_home: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "all"
    result = runner.invoke(
        main,
        ["--claude-home", str(claude_home), "export-all", "--output", str(out), "--minimal"],
    )
    assert result.exit_code == 0, result.output
    minimal_files = list(out.rglob("*.minimal.md"))
    assert len(minimal_files) >= 1
