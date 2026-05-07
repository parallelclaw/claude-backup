"""Scanner: Discovers Claude project directories and computes session metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_CLAUDE_HOME = Path.home() / ".claude" / "projects"


@dataclass
class SessionInfo:
    """Metadata for a single Claude session."""

    project: str
    session_id: str
    first_prompt: str = ""
    message_count: int = 0
    created: str = ""
    git_branch: str = ""
    title: str = ""
    jsonl_path: Path | None = None


@dataclass
class ProjectInfo:
    """A Claude project directory and its sessions."""

    name: str
    path: Path
    sessions: list[SessionInfo] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return decode_project_name(self.name)


def decode_project_name(folder_name: str) -> str:
    """Turn `-Users-macbook-Documents-Claude` into `Documents/Claude`.

    Claude Code encodes the working directory by replacing `/` with `-`.
    We restore the path and trim down to last 2 segments for readable display.
    """
    if not folder_name.startswith("-"):
        return folder_name
    parts = [p for p in folder_name.split("-") if p]
    if not parts:
        return folder_name
    if len(parts) > 2:
        return "/".join(parts[-2:])
    return "/".join(parts)


def get_claude_home(custom: Path | None = None) -> Path:
    """Return the Claude projects root directory."""
    return custom if custom is not None else DEFAULT_CLAUDE_HOME


def scan_projects(claude_home: Path | None = None) -> list[ProjectInfo]:
    """Scan ~/.claude/projects/ and return all projects with their sessions.

    Raises:
        FileNotFoundError: if claude_home does not exist.
    """
    root = get_claude_home(claude_home)
    if not root.exists():
        raise FileNotFoundError(f"Claude projects directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    projects: list[ProjectInfo] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        project = _load_project(entry)
        projects.append(project)
    return projects


def _load_project(project_dir: Path) -> ProjectInfo:
    """Load a project: read sessions-index.json (if present) + scan .jsonl files.

    Real Claude Code installs do NOT have sessions-index.json — for those, metadata
    is computed directly from each .jsonl file. The index, when present, is treated
    as a hint that's overridden by JSONL-derived values.
    """
    project = ProjectInfo(name=project_dir.name, path=project_dir)
    index = _load_index(project_dir / "sessions-index.json")
    jsonl_files = {p.stem: p for p in project_dir.glob("*.jsonl")}

    seen: set[str] = set()
    for session_id, meta in index.items():
        seen.add(session_id)
        jsonl_path = jsonl_files.get(session_id)
        info = SessionInfo(
            project=project_dir.name,
            session_id=session_id,
            first_prompt=str(meta.get("firstPrompt", "")),
            message_count=int(meta.get("messageCount", 0) or 0),
            created=str(meta.get("created", "")),
            git_branch=str(meta.get("gitBranch", "")),
            jsonl_path=jsonl_path,
        )
        if jsonl_path is not None:
            _enrich_from_jsonl(info, jsonl_path)
        project.sessions.append(info)

    for session_id, jsonl_path in jsonl_files.items():
        if session_id in seen:
            continue
        info = SessionInfo(
            project=project_dir.name,
            session_id=session_id,
            jsonl_path=jsonl_path,
        )
        _enrich_from_jsonl(info, jsonl_path)
        project.sessions.append(info)

    project.sessions.sort(key=lambda s: (s.created or "", s.session_id))
    return project


def _enrich_from_jsonl(info: SessionInfo, jsonl_path: Path) -> None:
    """Compute first_prompt / message_count / created / title by streaming the JSONL."""
    from .parser import _build_message  # local import to avoid cycle

    count = 0
    first_prompt = info.first_prompt
    earliest_ts = info.created
    title = info.title
    git_branch = info.git_branch

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
                if not isinstance(data, dict):
                    continue

                if data.get("type") == "ai-title":
                    t = data.get("aiTitle")
                    if isinstance(t, str) and t and not title:
                        title = t
                    continue

                msg = _build_message(data)
                if msg is None:
                    continue
                count += 1
                if msg.timestamp:
                    if not earliest_ts or msg.timestamp < earliest_ts:
                        earliest_ts = msg.timestamp
                if msg.role == "user" and not first_prompt and msg.content:
                    first_prompt = msg.content[:200]
                if msg.git_branch and not git_branch:
                    git_branch = msg.git_branch
    except OSError:
        return

    if count and not info.message_count:
        info.message_count = count
    if first_prompt:
        info.first_prompt = first_prompt
    if earliest_ts:
        info.created = earliest_ts
    if title:
        info.title = title
    if git_branch:
        info.git_branch = git_branch


def _load_index(path: Path) -> dict:
    """Load sessions-index.json. Return empty dict if missing/invalid."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def find_session(
    session_id: str, claude_home: Path | None = None
) -> SessionInfo | None:
    """Locate a session by ID across all projects."""
    for project in scan_projects(claude_home):
        for session in project.sessions:
            if session.session_id == session_id:
                return session
    return None
