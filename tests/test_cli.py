"""Tests for the CLI."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from claude_backup.cli import main


def test_list_command_shows_sessions(claude_home: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--claude-home", str(claude_home), "list"])
    assert result.exit_code == 0
    assert "abc-123" in result.output
    assert "def-456" in result.output
    assert "fake-project" in result.output
    assert "Project" in result.output  # header


def test_list_handles_missing_claude_home(tmp_path: Path) -> None:
    runner = CliRunner()
    missing = tmp_path / "does-not-exist"
    result = runner.invoke(main, ["--claude-home", str(missing), "list"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


def test_export_command_writes_both_files_by_default(
    claude_home: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    out = tmp_path / "backups"
    result = runner.invoke(
        main,
        ["--claude-home", str(claude_home), "export", "abc-123", "--output", str(out)],
    )
    assert result.exit_code == 0, result.output
    written = sorted(p.name for p in out.glob("*.md"))
    assert written == [
        "2026-05-07--abc-123.full.md",
        "2026-05-07--abc-123.md",
    ]


def test_export_unknown_session_returns_error(claude_home: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--claude-home", str(claude_home), "export", "no-such-id", "--output", str(tmp_path)],
    )
    assert result.exit_code == 2
    assert "not found" in result.output.lower()


def test_export_session_without_jsonl_returns_error(
    claude_home: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--claude-home", str(claude_home), "export", "ghost-789", "--output", str(tmp_path)],
    )
    assert result.exit_code == 2
    assert "no jsonl" in result.output.lower()


def test_export_all_writes_per_project_dirs(claude_home: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "all"
    result = runner.invoke(
        main, ["--claude-home", str(claude_home), "export-all", "--output", str(out)]
    )
    assert result.exit_code == 0, result.output

    # New layout: <output>/<source>/<project>/<files>
    fake_dir = out / "code" / "fake-project"
    assert fake_dir.is_dir()
    md_files = list(fake_dir.glob("*.md"))
    # abc-123, def-456, orphan-999, corrupt-000, empty-aaa — ghost-789 has no jsonl
    assert len(md_files) >= 4
    assert "Done." in result.output


def test_help_shows_subcommands() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "export" in result.output
    assert "export-all" in result.output


def test_version_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "claude-backup" in result.output
