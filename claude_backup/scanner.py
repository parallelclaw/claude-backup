"""Scanner: Discovers Claude project directories and loads sessions-index.json."""

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
    jsonl_path: Path | None = None


@dataclass
class ProjectInfo:
    """A Claude project directory and its sessions."""

    name: str
    path: Path
    sessions: list[SessionInfo] = field(default_factory=list)


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
    """Load a single project: read sessions-index.json + match .jsonl files."""
    project = ProjectInfo(name=project_dir.name, path=project_dir)
    index = _load_index(project_dir / "sessions-index.json")

    jsonl_files = {p.stem: p for p in project_dir.glob("*.jsonl")}

    seen: set[str] = set()
    for session_id, meta in index.items():
        seen.add(session_id)
        project.sessions.append(
            SessionInfo(
                project=project_dir.name,
                session_id=session_id,
                first_prompt=str(meta.get("firstPrompt", "")),
                message_count=int(meta.get("messageCount", 0) or 0),
                created=str(meta.get("created", "")),
                git_branch=str(meta.get("gitBranch", "")),
                jsonl_path=jsonl_files.get(session_id),
            )
        )

    # Include orphan jsonl files not present in the index
    for session_id, jsonl_path in jsonl_files.items():
        if session_id in seen:
            continue
        project.sessions.append(
            SessionInfo(
                project=project_dir.name,
                session_id=session_id,
                jsonl_path=jsonl_path,
            )
        )

    project.sessions.sort(key=lambda s: (s.created or "", s.session_id))
    return project


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
