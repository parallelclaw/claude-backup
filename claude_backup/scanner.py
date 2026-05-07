"""Scanner: Discovers Claude project directories and computes session metadata.

Two sources are supported:
  - "code"   — regular Claude Code at ~/.claude/projects/
  - "cowork" — Claude Cowork (desktop-agent app) at
               ~/Library/Application Support/Claude/local-agent-mode-sessions/

Both store sessions as JSONL files in the same on-disk format. The differences:
  - Cowork has a deeper hierarchy (account/workspace/local_<session>/.claude/projects/cwd/)
  - Cowork sessions often spawn subagents whose transcripts live in a sibling
    subagents/ folder. Code uses the same convention but spawns them more rarely.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_CLAUDE_HOME = Path.home() / ".claude" / "projects"
DEFAULT_COWORK_HOME = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Claude"
    / "local-agent-mode-sessions"
)


SOURCE_CODE = "code"
SOURCE_COWORK = "cowork"


@dataclass
class SessionInfo:
    """Metadata for a single Claude session."""

    project: str
    session_id: str
    source: str = SOURCE_CODE  # "code" or "cowork"
    first_prompt: str = ""
    message_count: int = 0
    created: str = ""
    git_branch: str = ""
    title: str = ""
    jsonl_path: Path | None = None
    subagent_jsonl_paths: list[Path] = field(default_factory=list)


@dataclass
class ProjectInfo:
    """A Claude project directory and its sessions."""

    name: str
    path: Path
    source: str = SOURCE_CODE
    sessions: list[SessionInfo] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return decode_project_name(self.name)


def decode_project_name(folder_name: str) -> str:
    """Short, table-friendly label for a project.

    Cowork session codenames keep their full hyphenated form:
        `-sessions-noble-clever-shannon` → `noble-clever-shannon`
    Other encoded paths get the last two segments joined with a slash:
        `-Users-macbook-Documents-Claude` → `Documents/Claude`
        `-Users-macbook-Documents-Claude-Projects-foo-bar` → `foo/bar`
    """
    if folder_name.startswith("-sessions-"):
        return folder_name[len("-sessions-"):]
    if not folder_name.startswith("-"):
        return folder_name
    parts = [p for p in folder_name.split("-") if p]
    if not parts:
        return folder_name
    if len(parts) > 2:
        return "/".join(parts[-2:])
    return "/".join(parts)


def decode_project_path(
    folder_name: str, home: Path | None = None
) -> str:
    """Reconstruct the original working-directory path as a relative string.

    Claude Code's encoding replaces every `/` and `-` with `-`, so the inverse
    is ambiguous (was `memex-mvp` one directory or `memex/mvp` two?). We walk
    the filesystem from root, greedy-matching the longest chunk that resolves
    to a real directory at each step. Then we drop the user's home prefix.
    When the path can't be fully resolved on disk, we fall back gracefully.

    `-Users-macbook-Documents-Claude` → `Documents/Claude`
    `-Users-macbook-Documents-Claude-Projects-memex-mvp` →
        `Documents/Claude/Projects/memex-mvp` if that directory exists,
        otherwise `Documents/Claude/Projects/memex/mvp`.
    `regular-name` → `regular-name` (unencoded names pass through)
    """
    if not folder_name.startswith("-"):
        return folder_name
    parts = [p for p in folder_name.split("-") if p and p != ".."]
    if not parts:
        return folder_name

    home_resolved = (home if home is not None else Path.home()).resolve()

    decoded: list[str] = []
    cwd = Path("/")
    remaining = list(parts)
    while remaining:
        matched_n = 0
        if cwd.is_dir():
            for i in range(len(remaining), 0, -1):
                candidate = "-".join(remaining[:i])
                if (cwd / candidate).exists():
                    matched_n = i
                    break
        if matched_n == 0:
            matched_n = 1
        chunk = "-".join(remaining[:matched_n])
        decoded.append(chunk)
        cwd = cwd / chunk
        remaining = remaining[matched_n:]

    abs_path = Path("/" + "/".join(decoded)) if decoded else Path("/")
    try:
        rel = abs_path.resolve(strict=False).relative_to(home_resolved)
        rel_str = str(rel)
        return rel_str if rel_str and rel_str != "." else "home"
    except ValueError:
        home_parts = [p for p in home_resolved.parts if p not in ("", "/")]
        if home_parts and decoded[: len(home_parts)] == home_parts:
            tail = decoded[len(home_parts):]
            return "/".join(tail) if tail else "home"
        return "/".join(decoded)


def get_claude_home(custom: Path | None = None) -> Path:
    """Return the Claude Code projects root directory."""
    return custom if custom is not None else DEFAULT_CLAUDE_HOME


def get_cowork_home(custom: Path | None = None) -> Path:
    """Return the Claude Cowork sessions root directory."""
    return custom if custom is not None else DEFAULT_COWORK_HOME


def scan_projects(
    claude_home: Path | None = None,
    cowork_home: Path | None = None,
) -> list[ProjectInfo]:
    """Discover all sessions across Claude Code and Claude Cowork.

    Both roots are best-effort: if either is missing we just skip it. The
    classic 'no Claude projects directory' error is only raised when BOTH
    roots are missing — i.e. neither product has been used on this machine.

    Returns a single list of ProjectInfo. Each project carries `source`
    ('code' or 'cowork') and its sessions inherit that.
    """
    code_root = get_claude_home(claude_home)
    cowork_root = get_cowork_home(cowork_home)
    code_exists = code_root.exists() and code_root.is_dir()
    cowork_exists = cowork_root.exists() and cowork_root.is_dir()

    if not code_exists and not cowork_exists:
        raise FileNotFoundError(
            f"No Claude data found. Tried:\n  - {code_root}\n  - {cowork_root}"
        )

    projects: list[ProjectInfo] = []
    if code_exists:
        projects.extend(_scan_code_root(code_root))
    if cowork_exists:
        projects.extend(_scan_cowork_root(cowork_root))
    return projects


def _scan_code_root(root: Path) -> list[ProjectInfo]:
    """Scan ~/.claude/projects/ — flat list of project directories."""
    projects: list[ProjectInfo] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        projects.append(_load_project(entry, source=SOURCE_CODE))
    return projects


def _scan_cowork_root(root: Path) -> list[ProjectInfo]:
    """Scan Cowork's nested account/workspace/local_session/.claude/projects/ tree.

    Each session folder may contain multiple project directories (one per cwd
    Cowork actually used). We surface each as its own ProjectInfo so the user
    can distinguish them in `list` output.
    """
    projects: list[ProjectInfo] = []
    for account in sorted(root.iterdir()):
        if not account.is_dir() or account.name == "skills-plugin":
            continue
        for workspace in sorted(account.iterdir()):
            if not workspace.is_dir():
                continue
            for session_folder in sorted(workspace.iterdir()):
                if not session_folder.is_dir() or not session_folder.name.startswith(
                    "local_"
                ):
                    continue
                inner_projects = session_folder / ".claude" / "projects"
                if not inner_projects.exists():
                    continue
                for cwd_dir in sorted(inner_projects.iterdir()):
                    if not cwd_dir.is_dir():
                        continue
                    projects.append(_load_project(cwd_dir, source=SOURCE_COWORK))
    return projects


def _load_project(project_dir: Path, source: str = SOURCE_CODE) -> ProjectInfo:
    """Load a project: read sessions-index.json (if present) + scan .jsonl files.

    Discovers subagent transcripts that live in `<project>/<session-id>/subagents/`
    and links them to their parent session.
    """
    project = ProjectInfo(name=project_dir.name, path=project_dir, source=source)
    index = _load_index(project_dir / "sessions-index.json")
    jsonl_files = {p.stem: p for p in project_dir.glob("*.jsonl")}

    seen: set[str] = set()
    for session_id, meta in index.items():
        seen.add(session_id)
        jsonl_path = jsonl_files.get(session_id)
        info = SessionInfo(
            project=project_dir.name,
            session_id=session_id,
            source=source,
            first_prompt=str(meta.get("firstPrompt", "")),
            message_count=int(meta.get("messageCount", 0) or 0),
            created=str(meta.get("created", "")),
            git_branch=str(meta.get("gitBranch", "")),
            jsonl_path=jsonl_path,
            subagent_jsonl_paths=_discover_subagents(project_dir, session_id),
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
            source=source,
            jsonl_path=jsonl_path,
            subagent_jsonl_paths=_discover_subagents(project_dir, session_id),
        )
        _enrich_from_jsonl(info, jsonl_path)
        project.sessions.append(info)

    project.sessions.sort(key=lambda s: (s.created or "", s.session_id))
    return project


def _discover_subagents(project_dir: Path, session_id: str) -> list[Path]:
    """Find subagent transcripts spawned during a session.

    Convention (used by both Claude Code and Cowork):
      <project_dir>/<session_id>/subagents/agent-<id>.jsonl
    """
    subagents_dir = project_dir / session_id / "subagents"
    if not subagents_dir.is_dir():
        return []
    return sorted(p for p in subagents_dir.glob("agent-*.jsonl") if p.is_file())


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
