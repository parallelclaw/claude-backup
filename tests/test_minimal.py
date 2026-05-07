"""Tests for the dialogue-only export path and the new mode-based file layout.

Filename convention:
  <date>--<id>.md       — clean dialogue (default 'minimal' mode of render)
  <date>--<id>.full.md  — audit copy with tool calls (default 'full' mode of render)

Both are written by default via `claude-backup export <id>`; users opt out of
either by passing `--mode minimal` or `--mode full`.
"""

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


def test_export_session_default_writes_both_files(
    claude_home: Path, tmp_path: Path
) -> None:
    session = _real_session(claude_home)
    paths = export_session(session, tmp_path)  # mode='both' is default

    assert len(paths) == 2
    minimal = next(p for p in paths if p.name.endswith(".md") and ".full" not in p.name)
    full = next(p for p in paths if p.name.endswith(".full.md"))

    assert "[tool_use:" not in minimal.read_text(encoding="utf-8")
    assert "[tool_use:" in full.read_text(encoding="utf-8")


def test_export_session_mode_minimal_writes_only_dialogue(
    claude_home: Path, tmp_path: Path
) -> None:
    session = _real_session(claude_home)
    paths = export_session(session, tmp_path, mode="minimal")
    assert len(paths) == 1
    assert paths[0].name.endswith(".md")
    assert not paths[0].name.endswith(".full.md")
    assert "[tool_use:" not in paths[0].read_text(encoding="utf-8")


def test_export_session_mode_full_writes_only_audit(
    claude_home: Path, tmp_path: Path
) -> None:
    session = _real_session(claude_home)
    paths = export_session(session, tmp_path, mode="full")
    assert len(paths) == 1
    assert paths[0].name.endswith(".full.md")
    assert "[tool_use:" in paths[0].read_text(encoding="utf-8")


def test_export_session_invalid_mode_raises(claude_home: Path, tmp_path: Path) -> None:
    import pytest

    session = _real_session(claude_home)
    with pytest.raises(ValueError):
        export_session(session, tmp_path, mode="bogus")


def test_cli_export_default_writes_both(claude_home: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "backups"
    result = runner.invoke(
        main,
        ["--claude-home", str(claude_home), "export", "real-001", "--output", str(out)],
    )
    assert result.exit_code == 0, result.output
    md_files = sorted(p.name for p in out.glob("*.md"))
    assert any(name.endswith(".full.md") for name in md_files)
    assert any(name.endswith(".md") and not name.endswith(".full.md") for name in md_files)


def test_cli_export_with_mode_minimal(claude_home: Path, tmp_path: Path) -> None:
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
            "--mode",
            "minimal",
        ],
    )
    assert result.exit_code == 0, result.output
    files = list(out.glob("*.md"))
    assert len(files) == 1
    assert not files[0].name.endswith(".full.md")


def test_cli_export_all_with_mode_full(claude_home: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "all"
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "export-all",
            "--output",
            str(out),
            "--mode",
            "full",
        ],
    )
    assert result.exit_code == 0, result.output
    full_files = list(out.rglob("*.full.md"))
    minimal_files = [
        p for p in out.rglob("*.md") if not p.name.endswith(".full.md")
    ]
    assert len(full_files) >= 1
    assert len(minimal_files) == 0
