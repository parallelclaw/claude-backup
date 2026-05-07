"""Tests for the real Claude Code JSONL format (nested message + queue-operation noise)."""

from __future__ import annotations

from pathlib import Path

from claude_backup.parser import extract_session_title, parse_session
from claude_backup.scanner import (
    decode_project_name,
    decode_project_path,
    scan_projects,
)


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


def _encoded(home: Path, *trailing: str) -> str:
    """Build a Claude-Code-style encoded path: leading '-' + every dir joined by '-'."""
    home_parts = [p for p in home.parts if p not in ("", "/")]
    return "-" + "-".join([*home_parts, *trailing])


def test_decode_project_path_strips_user_home(tmp_path: Path) -> None:
    """Used for export-all subdirectory naming. Strip the home-prefix so
    backups don't bury everything under a useless Users/<name> tree."""
    encoded = _encoded(tmp_path, "Documents", "Claude")
    assert decode_project_path(encoded, home=tmp_path) == "Documents/Claude"


def test_decode_project_path_recovers_hyphenated_directory_via_fs(
    tmp_path: Path,
) -> None:
    """When a real directory like `memex-mvp` exists on disk, we walk the FS
    to figure out that those two segments belong together rather than being
    `memex/mvp`."""
    (tmp_path / "Projects" / "memex-mvp").mkdir(parents=True)
    encoded = _encoded(tmp_path, "Projects", "memex", "mvp")
    assert decode_project_path(encoded, home=tmp_path) == "Projects/memex-mvp"


def test_decode_project_path_falls_back_to_split_when_dir_missing(
    tmp_path: Path,
) -> None:
    """If the project directory was deleted, we can't disambiguate hyphens
    from path separators — split everything and produce a best-effort path."""
    encoded = _encoded(tmp_path, "Projects", "memex", "mvp")
    # No `Projects/memex-mvp` on disk — fallback splits everything
    assert decode_project_path(encoded, home=tmp_path) == "Projects/memex/mvp"


def test_decode_project_path_handles_unencoded_names() -> None:
    """Names that aren't path-encoded (no leading dash) pass through."""
    assert decode_project_path("regular-project-name") == "regular-project-name"
    assert decode_project_path("") == ""


def test_decode_project_path_drops_parent_traversal_segments(tmp_path: Path) -> None:
    """Defensive: never let a `..` segment survive into a filesystem path."""
    decoded = decode_project_path("-..-..-etc-passwd", home=tmp_path)
    assert ".." not in decoded.split("/")
