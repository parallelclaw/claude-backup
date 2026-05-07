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
    """Flatten content into a string. Handles list-of-blocks shape too."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if "text" in block and isinstance(block["text"], str):
                    parts.append(block["text"])
                elif block.get("type") == "tool_use":
                    name = block.get("name", "tool")
                    parts.append(f"[tool_use: {name}]")
                elif block.get("type") == "tool_result":
                    inner = block.get("content", "")
                    parts.append(_normalize_content(inner))
                else:
                    parts.append(json.dumps(block, ensure_ascii=False))
        return "\n".join(p for p in parts if p)
    if content is None:
        return ""
    return str(content)


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
