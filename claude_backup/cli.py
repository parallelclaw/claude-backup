"""CLI entry point for claude-backup."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .exporter import export_session, render_handoff
from .parser import parse_session
from .scanner import (
    ProjectInfo,
    SOURCE_CODE,
    SOURCE_COWORK,
    decode_project_name,
    decode_project_path,
    get_claude_home,
    get_cowork_home,
    scan_projects,
)


@click.group(
    help=(
        "Export Claude Code AND Claude Cowork session history to Markdown. "
        "Both sources are auto-discovered; you don't need to choose."
    )
)
@click.version_option(__version__, prog_name="claude-backup")
@click.option(
    "--claude-home",
    type=click.Path(path_type=Path),
    default=None,
    help="Override Claude Code projects root (default: ~/.claude/projects).",
)
@click.option(
    "--cowork-home",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "Override Claude Cowork sessions root "
        "(default: ~/Library/Application Support/Claude/local-agent-mode-sessions)."
    ),
)
@click.pass_context
def main(
    ctx: click.Context, claude_home: Path | None, cowork_home: Path | None
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["claude_home"] = claude_home
    ctx.obj["cowork_home"] = cowork_home


@main.command("list", help="List all discovered sessions.")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    projects = _safe_scan(ctx.obj.get("claude_home"), ctx.obj.get("cowork_home"))
    rows = _flatten_sessions(projects)

    if not rows:
        click.echo("No sessions found.")
        return

    headers = ["Source", "Project", "Session", "First Prompt / Title", "Msgs", "Created"]
    table_rows = [
        [
            "Cowork" if r.source == SOURCE_COWORK else "Code",
            _truncate(_project_display(r), 26),
            r.session_id[:8],
            _truncate(r.title or r.first_prompt, 46),
            str(r.message_count),
            (r.created or "-")[:19],
        ]
        for r in rows
    ]
    click.echo(_format_table(headers, table_rows))


@main.command("export", help="Export a single session by ID.")
@click.argument("session_id")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("./backups"),
    help="Output directory (default: ./backups/).",
)
@click.option(
    "--mode",
    type=click.Choice(["both", "minimal", "full"], case_sensitive=False),
    default="both",
    show_default=True,
    help=(
        "Which file(s) to write. "
        "'both' writes the clean dialogue (<id>.md) AND the audit copy with tool "
        "calls (<id>.full.md). 'minimal' writes only the clean dialogue. "
        "'full' writes only the audit copy."
    ),
)
@click.pass_context
def export_cmd(
    ctx: click.Context, session_id: str, output: Path, mode: str
) -> None:
    target = _resolve_session_or_exit(
        session_id, ctx.obj.get("claude_home"), ctx.obj.get("cowork_home")
    )
    paths = export_session(target, output, mode=mode)
    for p in paths:
        click.echo(f"Exported: {p}")


@main.command(
    "handoff",
    help=(
        "Print a paste-ready prompt to continue this session in another AI agent. "
        "Pipe to your clipboard (e.g. `| pbcopy` on macOS) and paste into "
        "Claude.ai, ChatGPT, Cursor — any chat agent."
    ),
)
@click.argument("session_id")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Write to a file instead of stdout.",
)
@click.option(
    "--lang",
    type=click.Choice(["auto", "en", "ru"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Wrapper language. 'auto' picks Russian if the session has Cyrillic text.",
)
@click.pass_context
def handoff_cmd(
    ctx: click.Context, session_id: str, output: Path | None, lang: str
) -> None:
    target = _resolve_session_or_exit(
        session_id, ctx.obj.get("claude_home"), ctx.obj.get("cowork_home")
    )
    messages = parse_session(target.jsonl_path)
    prompt = render_handoff(target, messages, lang=lang)

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(prompt, encoding="utf-8")
        click.echo(f"Wrote handoff prompt to: {output}", err=True)
    else:
        click.echo(prompt)
        # Tip line goes to stderr so `| pbcopy` only captures the prompt
        size_kb = len(prompt.encode("utf-8")) // 1024
        click.echo(
            f"\n💡 {size_kb} KB. Pipe to clipboard: "
            "`| pbcopy` (macOS) / `| xclip -selection clipboard` (Linux). "
            "Paste into Claude.ai / ChatGPT / Cursor / any chat agent.",
            err=True,
        )


def _resolve_session_or_exit(
    session_id: str, claude_home: Path | None, cowork_home: Path | None
) -> "ProjectInfo":
    """Find a session by exact ID or unique prefix. Exit with a useful error otherwise."""
    projects = _safe_scan(claude_home, cowork_home)
    matches = []
    for project in projects:
        for session in project.sessions:
            if session.session_id == session_id or session.session_id.startswith(
                session_id
            ):
                matches.append(session)

    if not matches:
        click.echo(f"Session not found: {session_id}", err=True)
        sys.exit(2)
    if len(matches) > 1:
        click.echo(
            f"Ambiguous session prefix '{session_id}' matched {len(matches)} sessions:",
            err=True,
        )
        for m in matches:
            click.echo(
                f"  {m.session_id}  ({decode_project_name(m.project)})", err=True
            )
        sys.exit(2)
    target = matches[0]
    if target.jsonl_path is None or not target.jsonl_path.exists():
        click.echo(f"Session {session_id} has no JSONL file on disk.", err=True)
        sys.exit(2)
    return target


@main.command("export-all", help="Export every discovered session.")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("./backups"),
    help="Output directory (default: ./backups/).",
)
@click.option(
    "--mode",
    type=click.Choice(["both", "minimal", "full"], case_sensitive=False),
    default="both",
    show_default=True,
    help="Which file(s) to write per session — see `claude-backup export --help`.",
)
@click.pass_context
def export_all_cmd(ctx: click.Context, output: Path, mode: str) -> None:
    projects = _safe_scan(ctx.obj.get("claude_home"), ctx.obj.get("cowork_home"))
    exported = 0
    skipped = 0

    for project in projects:
        project_out = output / project.source / _project_subdir(project)
        for session in project.sessions:
            if session.jsonl_path is None or not session.jsonl_path.exists():
                click.echo(
                    f"Skip {project.name}/{session.session_id}: no JSONL file",
                    err=True,
                )
                skipped += 1
                continue
            try:
                paths = export_session(session, project_out, mode=mode)
                for p in paths:
                    click.echo(f"Exported: {p}")
                exported += 1
            except Exception as e:  # pragma: no cover - defensive
                click.echo(
                    f"Failed {project.name}/{session.session_id}: {e}", err=True
                )
                skipped += 1

    click.echo(f"\nDone. Exported: {exported}, skipped: {skipped}")


def _project_subdir(project: ProjectInfo) -> Path:
    """Pick the directory name for a project under <output>/<source>/.

    For Code: filesystem-aware decode of the encoded cwd, e.g. 'Documents/Claude'.
    For Cowork: strip the '-sessions-' prefix to get the friendly codename
        (e.g. '-sessions-beautiful-charming-curie' -> 'beautiful-charming-curie').
        Falls back to a short id if the project name is something else.
    """
    if project.source == SOURCE_COWORK:
        name = project.name
        if name.startswith("-sessions-"):
            return Path(name[len("-sessions-"):])
        # Cowork sessions whose cwd is the session's own outputs dir get an
        # ugly long encoded name. Use a short stable id from the parent
        # session folder ('local_<uuid>') if we can derive one.
        try:
            parent = project.path.parents[2].name  # local_<uuid>
            if parent.startswith("local_"):
                return Path("session-" + parent[len("local_"):][:8])
        except IndexError:
            pass
        return Path(name[:32])
    return Path(decode_project_path(project.name))


def _safe_scan(
    claude_home: Path | None, cowork_home: Path | None = None
) -> list[ProjectInfo]:
    try:
        return scan_projects(claude_home, cowork_home)
    except FileNotFoundError:
        code_root = get_claude_home(claude_home)
        cw_root = get_cowork_home(cowork_home)
        click.echo(
            "Error: Claude data not found. Tried:\n"
            f"  - {code_root}\n"
            f"  - {cw_root}\n"
            "Have you used Claude Code or Cowork on this machine?",
            err=True,
        )
        sys.exit(1)


def _flatten_sessions(projects):
    rows = []
    for project in projects:
        for session in project.sessions:
            rows.append(session)
    return rows


def _project_display(session) -> str:
    return decode_project_name(session.project)


def _truncate(text: str, length: int) -> str:
    if not text:
        return "-"
    text = text.replace("\n", " ").strip()
    if len(text) <= length:
        return text
    return text[: length - 1] + "…"


def _format_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def line(cells: list[str]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    sep = "  ".join("-" * w for w in widths)
    return "\n".join([line(headers), sep, *[line(r) for r in rows]])


if __name__ == "__main__":
    main()
