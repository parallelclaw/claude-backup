"""Tests for the `rescue` command — portable bundle for handing every session
to a different AI agent (escape hatch when the Anthropic account is banned).
"""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from claude_backup.cli import main
from claude_backup.exporter import (
    render_rescue_handoff_prompt,
    render_rescue_index,
    render_rescue_readme,
)
from claude_backup.scanner import scan_projects


def _all_sessions(claude_home: Path):
    return [
        s
        for p in scan_projects(claude_home)
        for s in p.sessions
        if s.jsonl_path is not None and s.jsonl_path.exists()
    ]


def test_rescue_index_lists_every_session(claude_home: Path) -> None:
    sessions = _all_sessions(claude_home)
    index = render_rescue_index(sessions, lang="en")
    for s in sessions:
        assert s.session_id[:8] in index


def test_rescue_index_contains_source_label(claude_home: Path) -> None:
    sessions = _all_sessions(claude_home)
    index = render_rescue_index(sessions, lang="en")
    assert "Code" in index  # at least one session is from Code source


def test_rescue_handoff_prompt_includes_session_count(claude_home: Path) -> None:
    sessions = _all_sessions(claude_home)
    prompt = render_rescue_handoff_prompt(sessions, lang="en")
    assert f"{len(sessions)} sessions" in prompt
    assert "taking over from Claude" in prompt


def test_rescue_handoff_prompt_russian_template(claude_home: Path) -> None:
    sessions = _all_sessions(claude_home)
    prompt = render_rescue_handoff_prompt(sessions, lang="ru")
    assert "принимаешь" in prompt.lower()
    assert "Claude" in prompt


def test_rescue_readme_summary_counts(claude_home: Path) -> None:
    sessions = _all_sessions(claude_home)
    readme = render_rescue_readme(sessions, lang="en")
    code_count = sum(1 for s in sessions if s.source == "code")
    cowork_count = sum(1 for s in sessions if s.source == "cowork")
    assert f"{code_count} Code" in readme
    assert f"{cowork_count} Cowork" in readme


def test_rescue_auto_lang_picks_russian_when_majority_cyrillic(
    claude_home: Path,
) -> None:
    """If most sessions have Cyrillic titles, auto language is 'ru'.
    The fake-project fixture has def-456 with Cyrillic — but most are English,
    so default is English. Force a Russian-heavy set explicitly.
    """
    sessions = [s for s in _all_sessions(claude_home) if "тест" in (s.first_prompt or "")]
    if not sessions:
        return  # Skip when fixture doesn't have Cyrillic sessions
    prompt = render_rescue_handoff_prompt(sessions, lang="auto")
    assert "принимаешь" in prompt.lower()


def test_cli_rescue_creates_full_bundle(claude_home: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "rescue-out"
    result = runner.invoke(
        main, ["--claude-home", str(claude_home), "rescue", "--output", str(out)]
    )
    assert result.exit_code == 0, result.output

    assert (out / "README.md").exists()
    assert (out / "HANDOFF_PROMPT.md").exists()
    assert (out / "INDEX.md").exists()
    assert (out / "sessions").is_dir()

    session_files = list((out / "sessions").glob("*.md"))
    expected = len(_all_sessions(claude_home))
    assert len(session_files) == expected

    # Every session file should be dialogue-only
    for f in session_files:
        content = f.read_text(encoding="utf-8")
        assert "mode: dialogue-only" in content
        assert "[tool_use:" not in content


def test_cli_rescue_session_filenames_use_date_and_short_id(
    claude_home: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    out = tmp_path / "rescue-out"
    runner.invoke(
        main, ["--claude-home", str(claude_home), "rescue", "--output", str(out)]
    )
    files = sorted(f.name for f in (out / "sessions").glob("*.md"))
    # Convention: <YYYY-MM-DD>--<8-char-id>.md
    for name in files:
        assert "--" in name
        parts = name.split("--")
        assert len(parts) == 2
        date_part, rest = parts
        assert len(date_part) == 10  # YYYY-MM-DD
        assert rest.endswith(".md")


def test_cli_rescue_default_output_when_no_flag(
    claude_home: Path, tmp_path: Path, monkeypatch
) -> None:
    """Without --output we drop a `claude-rescue-<today>/` folder in cwd."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["--claude-home", str(claude_home), "rescue"])
    assert result.exit_code == 0, result.output
    bundle_dirs = list(tmp_path.glob("claude-rescue-*"))
    assert len(bundle_dirs) == 1
    assert (bundle_dirs[0] / "HANDOFF_PROMPT.md").exists()


def test_cli_rescue_works_when_only_one_source_exists(
    claude_home: Path, tmp_path: Path
) -> None:
    """If user has Code only (no Cowork), rescue still bundles successfully."""
    runner = CliRunner()
    out = tmp_path / "rescue-out"
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "--cowork-home",
            str(tmp_path / "no-cowork"),
            "rescue",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out / "README.md").exists()


def test_cli_rescue_errors_when_no_sessions_found(tmp_path: Path) -> None:
    """Empty Code root + missing Cowork → 'No exportable sessions found' error."""
    runner = CliRunner()
    empty_code = tmp_path / "empty-code"
    empty_code.mkdir()  # Exists but empty
    out = tmp_path / "rescue-out"
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(empty_code),
            "--cowork-home",
            str(tmp_path / "no-cowork"),
            "rescue",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 1
    assert "no exportable sessions" in result.output.lower()
