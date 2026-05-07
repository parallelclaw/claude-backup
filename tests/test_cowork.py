"""Tests for the Cowork source: nested directory hierarchy + subagents.

The fixture lives in `tests/fixtures-cowork/` and mirrors the real on-disk
structure:

    fixtures-cowork/
    └── account-aaa/
        └── workspace-bbb/
            └── local_session-ccc/
                ├── audit.jsonl
                └── .claude/projects/
                    └── -sessions-noble-clever-shannon/
                        ├── cowork-main-001.jsonl
                        └── cowork-main-001/
                            └── subagents/
                                └── agent-aresearch1.jsonl
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from claude_backup.cli import main
from claude_backup.exporter import export_session, render_markdown
from claude_backup.parser import parse_session
from claude_backup.scanner import (
    SOURCE_COWORK,
    scan_projects,
)


COWORK_FIXTURES = Path(__file__).parent / "fixtures-cowork"


@pytest.fixture
def cowork_fixture(tmp_path: Path) -> Path:
    """Copy the cowork fixture tree into a temp directory."""
    dest = tmp_path / "cowork-data"
    shutil.copytree(COWORK_FIXTURES, dest)
    return dest


def test_cowork_scanner_finds_session(
    claude_home: Path, cowork_fixture: Path
) -> None:
    projects = scan_projects(claude_home, cowork_fixture)
    cowork_projects = [p for p in projects if p.source == SOURCE_COWORK]
    assert len(cowork_projects) == 1
    assert cowork_projects[0].name == "-sessions-noble-clever-shannon"
    assert len(cowork_projects[0].sessions) == 1


def test_cowork_session_has_correct_metadata(
    claude_home: Path, cowork_fixture: Path
) -> None:
    projects = scan_projects(claude_home, cowork_fixture)
    cowork = next(p for p in projects if p.source == SOURCE_COWORK)
    s = cowork.sessions[0]
    assert s.source == SOURCE_COWORK
    assert s.session_id == "cowork-main-001"
    assert s.title == "Q2 results slide deck"
    assert s.first_prompt == "draft a slide deck about Q2 results"
    # 1 user prompt + 2 assistant turns (one with text+tool_use, one text-only)
    assert s.message_count == 3


def test_cowork_session_links_subagent_files(
    claude_home: Path, cowork_fixture: Path
) -> None:
    projects = scan_projects(claude_home, cowork_fixture)
    cowork = next(p for p in projects if p.source == SOURCE_COWORK)
    s = cowork.sessions[0]
    assert len(s.subagent_jsonl_paths) == 1
    assert s.subagent_jsonl_paths[0].name == "agent-aresearch1.jsonl"


def test_render_full_mode_includes_subagents(
    claude_home: Path, cowork_fixture: Path
) -> None:
    projects = scan_projects(claude_home, cowork_fixture)
    s = next(p for p in projects if p.source == SOURCE_COWORK).sessions[0]
    messages = parse_session(s.jsonl_path)
    md = render_markdown(s, messages, minimal=False)

    assert "source: cowork" in md
    assert "subagents: 1" in md
    assert "# Subagents" in md
    assert "Subagent 1: `aresearch1`" in md
    assert "Q2 EMEA grew 18%" in md  # subagent's actual content


def test_render_minimal_mode_drops_subagents(
    claude_home: Path, cowork_fixture: Path
) -> None:
    projects = scan_projects(claude_home, cowork_fixture)
    s = next(p for p in projects if p.source == SOURCE_COWORK).sessions[0]
    messages = parse_session(s.jsonl_path)
    md = render_markdown(s, messages, minimal=True)

    assert "source: cowork" in md
    assert "mode: dialogue-only" in md
    assert "Subagent" not in md
    assert "Q2 EMEA" not in md  # subagent content stripped


def test_export_session_creates_subagent_section(
    claude_home: Path, cowork_fixture: Path, tmp_path: Path
) -> None:
    projects = scan_projects(claude_home, cowork_fixture)
    s = next(p for p in projects if p.source == SOURCE_COWORK).sessions[0]
    out = tmp_path / "out"
    paths = export_session(s, out, mode="full")
    assert len(paths) == 1
    content = paths[0].read_text(encoding="utf-8")
    assert "# Subagents" in content
    assert "Q2 EMEA" in content


def test_cli_list_shows_both_sources(
    claude_home: Path, cowork_fixture: Path
) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "--cowork-home",
            str(cowork_fixture),
            "list",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Code" in result.output
    assert "Cowork" in result.output
    assert "Q2 results slide deck" in result.output


def test_cli_export_all_separates_sources(
    claude_home: Path, cowork_fixture: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    out = tmp_path / "backups"
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(claude_home),
            "--cowork-home",
            str(cowork_fixture),
            "export-all",
            "--output",
            str(out),
            "--mode",
            "minimal",
        ],
    )
    assert result.exit_code == 0, result.output

    code_dir = out / "code"
    cowork_dir = out / "cowork"
    assert code_dir.is_dir()
    assert cowork_dir.is_dir()

    # Cowork session lands under cowork/<friendly-codename>/
    cowork_files = list(cowork_dir.rglob("*.md"))
    assert any("noble-clever-shannon" in str(f) for f in cowork_files)


def test_cli_works_with_only_cowork_data(
    cowork_fixture: Path, tmp_path: Path
) -> None:
    """If the user has Cowork sessions but no Claude Code projects, list still works."""
    runner = CliRunner()
    nonexistent_code = tmp_path / "no-code-here"
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(nonexistent_code),
            "--cowork-home",
            str(cowork_fixture),
            "list",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Cowork" in result.output


def test_cli_errors_when_neither_source_exists(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--claude-home",
            str(tmp_path / "no-code"),
            "--cowork-home",
            str(tmp_path / "no-cowork"),
            "list",
        ],
    )
    assert result.exit_code == 1
    assert "not found" in result.output.lower()
