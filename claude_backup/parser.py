"""Parser: Reads .jsonl session files and validates structure."""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Message:
    """A single conversation entry from a session JSONL line."""

    role: str
    content: str
    timestamp: str = ""
    model: str = ""
    git_branch: str = ""
    raw: dict = field(default_factory=dict)


def parse_session(jsonl_path: Path) -> list[Message]:
    """Read a session JSONL file and return parsed messages.

    Skips malformed lines with a warning. Returns [] for missing/empty files.
    """
    if not jsonl_path.exists():
        warnings.warn(f"Session file not found: {jsonl_path}", stacklevel=2)
        return []

    messages: list[Message] = []
    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    warnings.warn(
                        f"{jsonl_path.name}:{line_no}: malformed JSON ({e.msg}); skipping",
                        stacklevel=2,
                    )
                    continue
                if not isinstance(data, dict):
                    warnings.warn(
                        f"{jsonl_path.name}:{line_no}: line is not an object; skipping",
                        stacklevel=2,
                    )
                    continue
                msg = _build_message(data)
                if msg is not None:
                    messages.append(msg)
    except OSError as e:
        warnings.warn(f"Cannot read {jsonl_path}: {e}", stacklevel=2)
        return []

    return messages


SKIP_TOP_TYPES = {"queue-operation", "ai-title", "summary"}


def _build_message(data: dict) -> Message | None:
    """Convert a JSONL record into a Message. Return None if not a chat message.

    Handles two shapes:
      1. Flat:  {"role": "user", "content": "...", "timestamp": "..."}  (legacy/spec format)
      2. Nested Claude Code format:
         {"type": "user", "message": {"role": "user", "content": ...}, "timestamp": ...}
         {"message": {"role": "assistant", "model": "...", "content": [...]}}
    """
    top_type = data.get("type")
    if isinstance(top_type, str) and top_type in SKIP_TOP_TYPES:
        return None

    if "attachment" in data and "message" not in data:
        return None

    nested = data.get("message")
    if isinstance(nested, dict):
        role = nested.get("role")
        if not isinstance(role, str) or not role:
            return None
        content = _normalize_content(nested.get("content", ""))
        if not content.strip():
            return None
        timestamp = str(data.get("timestamp", "") or nested.get("timestamp", "") or "")
        model = str(nested.get("model", "") or data.get("model", "") or "")
        git_branch = str(data.get("gitBranch", "") or nested.get("gitBranch", "") or "")
        return Message(
            role=role,
            content=content,
            timestamp=timestamp,
            model=model,
            git_branch=git_branch,
            raw=data,
        )

    role = data.get("role")
    if not role or not isinstance(role, str):
        return None
    content = _normalize_content(data.get("content", ""))
    return Message(
        role=role,
        content=content,
        timestamp=str(data.get("timestamp", "") or ""),
        model=str(data.get("model", "") or ""),
        git_branch=str(data.get("gitBranch", "") or ""),
        raw=data,
    )


def extract_session_title(jsonl_path: Path) -> str:
    """Pull `aiTitle` from an `ai-title` record if present. Returns '' if not found."""
    if not jsonl_path.exists():
        return ""
    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict) and data.get("type") == "ai-title":
                    title = data.get("aiTitle", "")
                    if isinstance(title, str) and title:
                        return title
    except OSError:
        return ""
    return ""


def _normalize_content(content) -> str:
    """Flatten Claude content blocks into plain text.

    Handles: plain strings, text blocks, tool_use, tool_result, and image blocks.
    Skips empty extended-thinking blocks (which contain only encrypted signatures —
    huge base64 blobs that aren't useful to humans). Non-empty thinking text is
    preserved in italics.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif "text" in block and isinstance(block["text"], str) and not block_type:
                parts.append(block["text"])
            elif block_type == "tool_use":
                name = block.get("name", "tool")
                parts.append(f"[tool_use: {name}]")
            elif block_type == "tool_result":
                inner = block.get("content", "")
                parts.append(_normalize_content(inner))
            elif block_type == "thinking":
                thought = block.get("thinking", "")
                if isinstance(thought, str) and thought.strip():
                    parts.append(f"_<thinking>_\n{thought}\n_</thinking>_")
            elif block_type == "redacted_thinking":
                continue
            elif block_type == "image":
                parts.append("[image]")
            elif block_type:
                parts.append(f"[{block_type}]")
        return "\n".join(p for p in parts if p)
    if content is None:
        return ""
    return str(content)


def dialogue_text(msg: "Message") -> str:
    """Extract only human-facing text from a message: no tool_use, no tool_result,
    no thinking, no images. Used by the dialogue-only render path (`--mode minimal`
    and the default `<id>.md` half of `--mode both`)."""
    nested = msg.raw.get("message") if isinstance(msg.raw, dict) else None
    raw = nested if isinstance(nested, dict) else msg.raw
    content = raw.get("content") if isinstance(raw, dict) else None

    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
            continue
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text = block.get("text", "")
            if isinstance(text, str) and text:
                parts.append(text)
    return "\n".join(parts)


def is_dialogue_message(msg: "Message") -> bool:
    """True if the message has any visible human-facing dialogue text."""
    return bool(dialogue_text(msg).strip())


def session_summary(jsonl_path: Path) -> dict:
    """Quick stats about a session: message count, first prompt, model."""
    messages = parse_session(jsonl_path)
    first_user = next((m.content for m in messages if m.role == "user"), "")
    model = next((m.model for m in messages if m.model), "")
    return {
        "message_count": len(messages),
        "first_prompt": first_user[:200],
        "model": model,
    }
