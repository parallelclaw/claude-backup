"""CLI entry point for claude-backup."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .exporter import export_session
from .scanner import ProjectInfo, decode_project_name, get_claude_home, scan_projects


@click.group(help="Export Claude Code session history to Markdown.")
@click.version_option(__version__, prog_name="claude-backup")
@click.option(
    "--claude-home",
    type=click.Path(path_type=Path),
    default=None,
    help="Override the Claude projects root (default: ~/.claude/projects).",
)
@click.pass_context
def main(ctx: click.Context, claude_home: Path | None) -> None:
    ctx.ensure_object(dict)
    ctx.obj["claude_home"] = claude_home


@main.command("list", help="List all discovered sessions.")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    projects = _safe_scan(ctx.obj.get("claude_home"))
    rows = _flatten_sessions(projects)

    if not rows:
        click.echo("No sessions found.")
        return

    headers = ["Project", "Session", "First Prompt / Title", "Msgs", "Created"]
    table_rows = [
        [
            _truncate(_project_display(r), 28),
            r.session_id[:8],
            _truncate(r.title or r.first_prompt, 50),
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
@click.pass_context
def export_cmd(ctx: click.Context, session_id: str, output: Path) -> None:
    projects = _safe_scan(ctx.obj.get("claude_home"))
    matches = []
    for project in projects:
        for session in project.sessions:
            if session.session_id == session_id or session.session_id.startswith(session_id):
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
            click.echo(f"  {m.session_id}  ({decode_project_name(m.project)})", err=True)
        sys.exit(2)
    target = matches[0]

    if target.jsonl_path is None or not target.jsonl_path.exists():
        click.echo(
            f"Session {session_id} has no JSONL file on disk.", err=True
        )
        sys.exit(2)

    out = export_session(target, output)
    click.echo(f"Exported: {out}")


@main.command("export-all", help="Export every discovered session.")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("./backups"),
    help="Output directory (default: ./backups/).",
)
@click.pass_context
def export_all_cmd(ctx: click.Context, output: Path) -> None:
    projects = _safe_scan(ctx.obj.get("claude_home"))
    exported = 0
    skipped = 0

    for project in projects:
        project_out = output / project.name
        for session in project.sessions:
            if session.jsonl_path is None or not session.jsonl_path.exists():
                click.echo(
                    f"Skip {project.name}/{session.session_id}: no JSONL file",
                    err=True,
                )
                skipped += 1
                continue
            try:
                path = export_session(session, project_out)
                click.echo(f"Exported: {path}")
                exported += 1
            except Exception as e:  # pragma: no cover - defensive
                click.echo(
                    f"Failed {project.name}/{session.session_id}: {e}", err=True
                )
                skipped += 1

    click.echo(f"\nDone. Exported: {exported}, skipped: {skipped}")


def _safe_scan(claude_home: Path | None) -> list[ProjectInfo]:
    try:
        return scan_projects(claude_home)
    except FileNotFoundError:
        root = get_claude_home(claude_home)
        click.echo(
            f"Error: Claude projects directory not found at {root}.\n"
            f"Have you used Claude Code on this machine?",
            err=True,
        )
        sys.exit(1)
    except NotADirectoryError as e:
        click.echo(f"Error: {e}", err=True)
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
