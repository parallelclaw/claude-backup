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


EXPORT_MODES = ("both", "minimal", "full")


def export_session(
    session: SessionInfo,
    output_dir: Path,
    now: datetime | None = None,
    mode: str = "both",
) -> list[Path]:
    """Export a session to Markdown. Returns the list of written file paths.

    Two output flavours, controlled by `mode`:
      - `<date>--<session_id>.md`       — clean dialogue: only user prompts and
                                          Claude's text replies.
      - `<date>--<session_id>.full.md`  — everything: tool calls, tool results,
                                          and any visible thinking text.

    `mode` values:
      - `"both"`    (default) — write both files
      - `"minimal"`           — write only the clean `.md` file
      - `"full"`              — write only the `.full.md` file
    """
    if mode not in EXPORT_MODES:
        raise ValueError(
            f"mode must be one of {EXPORT_MODES}; got {mode!r}"
        )
    if session.jsonl_path is None or not session.jsonl_path.exists():
        raise FileNotFoundError(
            f"Session JSONL not found for {session.session_id}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    messages = parse_session(session.jsonl_path)
    date_prefix = _date_prefix(session, messages)
    base = f"{date_prefix}--{session.session_id}"

    written: list[Path] = []
    if mode in ("both", "minimal"):
        path = output_dir / f"{base}.md"
        path.write_text(
            render_markdown(session, messages, now=now, minimal=True),
            encoding="utf-8",
        )
        written.append(path)
    if mode in ("both", "full"):
        path = output_dir / f"{base}.full.md"
        path.write_text(
            render_markdown(session, messages, now=now, minimal=False),
            encoding="utf-8",
        )
        written.append(path)
    return written


def render_markdown(
    session: SessionInfo,
    messages: list[Message],
    now: datetime | None = None,
    minimal: bool = False,
) -> str:
    """Build the full Markdown document for a session.

    In `minimal` mode subagent transcripts are dropped entirely — they're
    almost always tool plumbing, not human-facing dialogue. In full mode
    subagents are appended after the main timeline as separate sections.
    """
    now = now or datetime.now(timezone.utc)

    visible = [m for m in messages if is_dialogue_message(m)] if minimal else messages

    branch = session.git_branch or _first_non_empty(m.git_branch for m in messages)
    model = _first_non_empty(m.model for m in messages)
    msg_count = len(visible) if minimal else (session.message_count or len(messages))

    fm_fields: dict = {
        "project": session.project,
        "session_id": session.session_id,
        "source": session.source,
        "branch": branch,
        "model": model,
        "messages": msg_count,
        "exported_at": _format_iso(now),
    }
    if minimal:
        fm_fields["mode"] = "dialogue-only"
    if session.subagent_jsonl_paths and not minimal:
        fm_fields["subagents"] = len(session.subagent_jsonl_paths)
    if session.title:
        fm_fields["title"] = session.title
    frontmatter = _render_frontmatter(**fm_fields)

    title_branch = branch or "no-branch"
    if session.title:
        header = f"# {session.title}\n\n_{session.project} / {title_branch} / {session.session_id}_\n"
    else:
        header = f"# {session.project} / {title_branch} / {session.session_id}\n"

    body = _render_body(visible, minimal=minimal)

    sections = [frontmatter, "", header, body]
    if not minimal and session.subagent_jsonl_paths:
        sections.append(_render_subagents(session.subagent_jsonl_paths))
    return "\n".join(sections).rstrip() + "\n"


_HANDOFF_TEMPLATE_EN = """\
You are continuing a conversation I started in **{source_label}**.

**Original task:** {title}
**Started:** {created}{messages_clause}

Read the transcript below, briefly acknowledge you've understood the context, then wait for my next message. Match the language and tone of the conversation.

---

{transcript}

---

(Source: `{session_id}` from {source_label}. Continue from here.)
"""


_HANDOFF_TEMPLATE_RU = """\
Ты продолжаешь разговор, который я начал в **{source_label}**.

**Исходная задача:** {title}
**Начат:** {created}{messages_clause}

Прочитай транскрипт ниже, кратко подтверди что понял контекст, и жди следующего сообщения. Сохраняй язык и тон оригинального разговора.

---

{transcript}

---

(Исходная сессия: `{session_id}` из {source_label}. Продолжай отсюда.)
"""


_SOURCE_LABEL_EN = {"code": "Claude Code", "cowork": "Claude Cowork"}
_SOURCE_LABEL_RU = {"code": "Claude Code", "cowork": "Claude Cowork"}


def _has_cyrillic(text: str) -> bool:
    return any("Ѐ" <= ch <= "ӿ" for ch in text)


def detect_handoff_language(session: SessionInfo, messages: list[Message]) -> str:
    """Pick 'ru' if the title or first user prompt is in Russian, else 'en'."""
    sample = (session.title or "") + " " + (session.first_prompt or "")
    if not sample.strip():
        sample = next(
            (m.content for m in messages if m.role == "user" and m.content),
            "",
        )
    return "ru" if _has_cyrillic(sample) else "en"


def render_handoff(
    session: SessionInfo,
    messages: list[Message],
    lang: str = "auto",
) -> str:
    """Build a paste-ready prompt that hands the conversation to another agent.

    `lang`: 'auto' (default — Cyrillic-detected), 'en', or 'ru'.
    Always uses dialogue-only content (no tool noise) so paste size stays small.
    """
    if lang == "auto":
        lang = detect_handoff_language(session, messages)

    visible = [m for m in messages if is_dialogue_message(m)]
    transcript_body = _render_body(visible, minimal=True)

    template = _HANDOFF_TEMPLATE_RU if lang == "ru" else _HANDOFF_TEMPLATE_EN
    label_map = _SOURCE_LABEL_RU if lang == "ru" else _SOURCE_LABEL_EN
    source_label = label_map.get(session.source, session.source.title())

    title = session.title or session.first_prompt or "(no title)"
    created = (session.created or "").split("T")[0] or "—"
    if len(visible) > 0:
        msg_word = "сообщений" if lang == "ru" else "messages"
        messages_clause = f" ({len(visible)} {msg_word})"
    else:
        messages_clause = ""

    return template.format(
        source_label=source_label,
        title=title,
        created=created,
        messages_clause=messages_clause,
        session_id=session.session_id,
        transcript=transcript_body.rstrip(),
    )


def _render_subagents(subagent_paths: list[Path]) -> str:
    """Render each subagent transcript as a numbered section under a divider."""
    parts: list[str] = ["", "---", "", "# Subagents", ""]
    for i, path in enumerate(sorted(subagent_paths), start=1):
        agent_id = path.stem.replace("agent-", "", 1) if path.stem.startswith(
            "agent-"
        ) else path.stem
        sub_messages = parse_session(path)
        parts.append(f"## Subagent {i}: `{agent_id}`")
        if not sub_messages:
            parts.append("_(empty)_\n")
            continue
        parts.append("")
        parts.append(_render_body(sub_messages, minimal=False))
    return "\n".join(parts)


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
