"""Exporter: Convert parsed sessions to Markdown files."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .parser import Message, dialogue_text, is_dialogue_message, parse_session
from .scanner import SessionInfo


ROLE_LABELS = {
    "user": "User",
    "assistant": "Assistant",
    "tool_result": "Tool Result",
    "system": "System",
}


def export_session(
    session: SessionInfo,
    output_dir: Path,
    now: datetime | None = None,
    minimal: bool = False,
) -> Path:
    """Export a single session to Markdown. Returns path to the written file.

    When `minimal=True`, drops tool calls, tool results, and reasoning blocks —
    keeps only the user/assistant dialogue. Filename gets a `.minimal.md` suffix.
    """
    if session.jsonl_path is None or not session.jsonl_path.exists():
        raise FileNotFoundError(
            f"Session JSONL not found for {session.session_id}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    messages = parse_session(session.jsonl_path)

    date_prefix = _date_prefix(session, messages)
    suffix = ".minimal.md" if minimal else ".md"
    filename = f"{date_prefix}--{session.session_id}{suffix}"
    out_path = output_dir / filename

    md = render_markdown(session, messages, now=now, minimal=minimal)
    out_path.write_text(md, encoding="utf-8")
    return out_path


def render_markdown(
    session: SessionInfo,
    messages: list[Message],
    now: datetime | None = None,
    minimal: bool = False,
) -> str:
    """Build the full Markdown document for a session."""
    now = now or datetime.now(timezone.utc)

    visible = [m for m in messages if is_dialogue_message(m)] if minimal else messages

    branch = session.git_branch or _first_non_empty(m.git_branch for m in messages)
    model = _first_non_empty(m.model for m in messages)
    msg_count = len(visible) if minimal else (session.message_count or len(messages))

    fm_fields = {
        "project": session.project,
        "session_id": session.session_id,
        "branch": branch,
        "model": model,
        "messages": msg_count,
        "exported_at": _format_iso(now),
    }
    if minimal:
        fm_fields["mode"] = "dialogue-only"
    if session.title:
        fm_fields["title"] = session.title
    frontmatter = _render_frontmatter(**fm_fields)

    title_branch = branch or "no-branch"
    if session.title:
        header = f"# {session.title}\n\n_{session.project} / {title_branch} / {session.session_id}_\n"
    else:
        header = f"# {session.project} / {title_branch} / {session.session_id}\n"

    body = _render_body(visible, minimal=minimal)

    parts = [frontmatter, "", header, body]
    return "\n".join(parts).rstrip() + "\n"


def _render_frontmatter(**fields) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


_YAML_INDICATOR_PREFIXES = ("'", '"', "[", "{", "&", "*", "!", "|", ">", "%", "@", "`", "?", "-")


def _yaml_scalar(value) -> str:
    if isinstance(value, int):
        return str(value)
    s = str(value) if value is not None else ""
    if s == "":
        return '""'
    needs_quoting = (
        "\n" in s
        or '"' in s
        or ": " in s
        or " #" in s
        or s.startswith(_YAML_INDICATOR_PREFIXES)
        or s.endswith(":")
        or s.strip() != s
    )
    if needs_quoting:
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s


def _render_body(messages: list[Message], minimal: bool = False) -> str:
    if not messages:
        return "_No messages._\n"

    sections: list[str] = []
    for msg in messages:
        label = ROLE_LABELS.get(msg.role, msg.role.capitalize())
        time_str = _format_short_time(msg.timestamp)
        heading = f"## {label} ({time_str})" if time_str else f"## {label}"
        if minimal:
            text = dialogue_text(msg).rstrip()
        else:
            text = msg.content.rstrip() if msg.content else ""
        body = text or "_(empty)_"
        sections.append(f"{heading}\n{body}\n")
    return "\n".join(sections)


def _format_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_short_time(timestamp: str) -> str:
    if not timestamp:
        return ""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return timestamp
    return dt.strftime("%H:%M:%S")


def _date_prefix(session: SessionInfo, messages: list[Message]) -> str:
    candidate = session.created or _first_non_empty(m.timestamp for m in messages)
    if candidate:
        try:
            dt = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _first_non_empty(values) -> str:
    for v in values:
        if v:
            return v
    return ""
