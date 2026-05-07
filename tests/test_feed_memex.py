"""Tests for the `feed-memex` command — writes clean JSONL to memex's inbox.

Memex is a separate local MCP server (github.com/parallelclaw/memex-mvp).
This command produces dialogue-only JSONL files in memex's inbox folder
in the flat format memex's existing claude-code parser expects:

    {"role":"user","content":"...","timestamp":"...","id":"..."}
    {"role":"assistant","content":"...","timestamp":"...","id":"..."}

Each session becomes one .jsonl file named `code-<short>.jsonl` or
`cowork-<short>.jsonl`. The prefix lets memex distinguish sources.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from claude_backup.cli import main


def test_feed_memex_creates_jsonl_per_session(
    claude_home: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    inbox = tmp_path / "memex" / "inbox"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "feed-memex",
            "--inbox",
            str(inbox),
        ],
    )
    assert result.exit_code == 0, result.output
    assert inbox.is_dir()
    files = list(inbox.glob("*.jsonl"))
    assert len(files) >= 1


def test_feed_memex_uses_code_prefix_for_code_sessions(
    claude_home: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    inbox = tmp_path / "memex" / "inbox"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "feed-memex",
            "--inbox",
            str(inbox),
        ],
    )
    assert result.exit_code == 0, result.output
    code_files = list(inbox.glob("code-*.jsonl"))
    assert len(code_files) >= 1, "expected at least one code-*.jsonl file"


def test_feed_memex_uses_cowork_prefix_for_cowork_sessions(
    claude_home: Path, tmp_path: Path
) -> None:
    """Test fixture has Cowork sessions in fixtures-cowork/. Once it's in the
    cowork-home, the feed-memex command should produce cowork-* files."""
    cowork_root = Path(__file__).parent / "fixtures-cowork"
    runner = CliRunner()
    inbox = tmp_path / "memex" / "inbox"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "--cowork-home",
            str(cowork_root),
            "feed-memex",
            "--inbox",
            str(inbox),
        ],
    )
    assert result.exit_code == 0, result.output
    cowork_files = list(inbox.glob("cowork-*.jsonl"))
    assert len(cowork_files) >= 1, "expected at least one cowork-*.jsonl file"


def test_feed_memex_record_shape_matches_memex_parser(
    claude_home: Path, tmp_path: Path
) -> None:
    """Each line must have top-level `role` + `content` (string) + `timestamp`
    + `id`. That's what memex's claude-code parser reads (server.js:215-263)."""
    runner = CliRunner()
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "feed-memex",
            "--inbox",
            str(inbox),
        ],
    )
    files = list(inbox.glob("code-*.jsonl"))
    assert files, "no code-* files written"

    with files[0].open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            assert "role" in rec and isinstance(rec["role"], str)
            assert "content" in rec and isinstance(rec["content"], str)
            assert rec["content"].strip(), "empty content should not be written"
            assert "id" in rec
            # timestamp may be empty string if missing in source
            assert "timestamp" in rec


def test_feed_memex_strips_tool_use_and_thinking(
    claude_home: Path, tmp_path: Path
) -> None:
    """Ensures the output is dialogue-only — no tool_use, tool_result, or
    thinking signature noise pollutes the memex index."""
    runner = CliRunner()
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "feed-memex",
            "--inbox",
            str(inbox),
        ],
    )
    for f in inbox.glob("*.jsonl"):
        content = f.read_text(encoding="utf-8")
        assert "[tool_use:" not in content
        assert "tool_result" not in content
        assert '"signature"' not in content


def test_feed_memex_msg_ids_stable_across_runs(
    claude_home: Path, tmp_path: Path
) -> None:
    """Re-running feed-memex must produce identical msg ids so memex's
    UNIQUE(source, conversation_id, msg_id) dedupe works on re-import."""
    runner = CliRunner()
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    runner.invoke(
        main,
        ["--claude-home", str(claude_home), "feed-memex", "--inbox", str(inbox)],
    )
    sample_file = next(inbox.glob("code-*.jsonl"))
    first_run = sample_file.read_text(encoding="utf-8")

    # Re-run
    runner.invoke(
        main,
        ["--claude-home", str(claude_home), "feed-memex", "--inbox", str(inbox)],
    )
    second_run = sample_file.read_text(encoding="utf-8")
    assert first_run == second_run, "msg ids must be deterministic"


def test_feed_memex_dry_run_does_not_write(
    claude_home: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    inbox = tmp_path / "inbox"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "feed-memex",
            "--inbox",
            str(inbox),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Dry run" in result.output or "would write" in result.output.lower()
    # No files written
    assert not inbox.exists() or list(inbox.glob("*.jsonl")) == []


def test_feed_memex_errors_when_memex_dir_missing(tmp_path: Path) -> None:
    """If the memex parent doesn't exist (memex not installed), error clearly."""
    runner = CliRunner()
    fake_inbox = tmp_path / "no-memex-here" / "inbox"
    # Create empty Claude Code home so scan succeeds
    claude_home = tmp_path / "code"
    (claude_home / "fake-project").mkdir(parents=True)
    (claude_home / "fake-project" / "x.jsonl").write_text(
        '{"role":"user","content":"hi","timestamp":"2026-01-01T00:00:00Z"}\n'
    )
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "feed-memex",
            "--inbox",
            str(fake_inbox),
        ],
    )
    assert result.exit_code == 1
    assert "memex" in result.output.lower()
