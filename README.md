# claude-backup

> Export your Claude Code sessions, memory, and credentials to local Markdown files — so you keep your work even if Anthropic suspends your account.

[Русский](README.ru.md) · English

---

## Why

Claude Code stores everything in `~/.claude/`. Sessions, project context, custom instructions, memory. All of it lives on Anthropic's servers and in a local cache you don't control.

**If your account gets suspended, rate-limited, or you lose OAuth access — your project memory disappears.**

> *"Купил подписку Claude Max 5x, прилетела блокировка. Ощущение, как-будто лучшего друга и напарника потерял..."*
> — Real user, May 2026

This tool fixes that.

---

## Real Stories

Claude hired a third-party verification company. They made a mistake and **mass-flagged legitimate accounts** — including paying users who did nothing wrong.

> *"Claude нанял специальную компанию для проверки пользователей. Похоже компания ошиблась и массово отметила как левые множество реально нормальных и чистых аккаунтов. Увы, но разбираться будут долго."*

Users who paid through non-standard channels or used VPNs were hit hardest. Appeals take months. Meanwhile, **months of project context vanish**.

> *"Я использую клод для бэкенда, в основном. Бесплатная версия с таким объемом задач не справится. Да, оплатил окольными путями — может быть из-за этого + vpn detect."*

**claude-backup doesn't prevent bans. It prevents amnesia.**

---

## Quick Start

```bash
git clone https://github.com/parallelclaw/claude-backup.git
cd claude-backup
pip install -e .
```

```bash
# See what you have
claude-backup list

# Export one session
claude-backup export abc-123 --output ~/claude-backups/

# Export everything
claude-backup export-all --output ~/claude-backups/
```

New users: see [QUICKSTART.md](./QUICKSTART.md) for the full step-by-step guide (macOS, Linux, Windows/WSL).

---

## Install

Requires **Python 3.10+** (CI tests 3.10, 3.11, 3.12).

```bash
pip install -e .
```

> **Note:** If you only have Python 3.9, you can install with `pip install -e . --ignore-requires-python`. The code uses `from __future__ import annotations` and works on 3.9, but official support is 3.10+.

---

## Usage

### List sessions

```bash
claude-backup list
```

Prints a table:

```
Project    Session ID              First Prompt         Msg Count  Created              Git Branch
─────────  ──────────────────────  ───────────────────  ─────────  ───────────────────  ──────────
my-webapp  abc-123                 fix auth bug         42         2026-05-07T10:42:00Z main
my-webapp  def-456                 add unicode support  18         2026-05-06T14:00:00Z feature/unicode
```

### Export a single session

```bash
claude-backup export abc-123 --output ./backups/
```

Writes `./backups/2026-05-07--abc-123.md`.

### Export everything

```bash
claude-backup export-all --output ./backups/
```

Each project gets its own subdirectory under `--output`.

### Custom Claude root

Override the default `~/.claude/projects/` location:

```bash
claude-backup --claude-home /path/to/projects list
```

---

## Output format

Each session is written as Markdown with YAML frontmatter:

```markdown
---
project: my-webapp
session_id: abc-123
branch: main
model: claude-sonnet-4
messages: 42
exported_at: 2026-05-07T15:30:00Z
---

# my-webapp / main / abc-123

## User (10:42:46)
fix auth bug

## Assistant (10:42:50)
Here's the fix...
```

---

## Behaviour

- **Graceful degradation** — empty or corrupted `.jsonl` files are skipped with a warning. The tool never crashes on bad data.
- **Orphan sessions** — sessions discovered via `.jsonl` files but missing from `sessions-index.json` are still exported (with minimal metadata).
- **Ghost index entries** — sessions in the index without an on-disk `.jsonl` file are listed but cannot be exported.
- **Missing `~/.claude/`** exits with code 1 and a clear error message.
- **Unicode-ready** — correctly handles Russian, emoji, and special characters.
- **Tool-aware** — preserves `tool_use` / `tool_result` blocks in readable Markdown.

---

## Development

```bash
pip install -e ".[dev]"
pytest -v --cov=claude_backup
```

CI runs on Python 3.10, 3.11, and 3.12 — see [.github/workflows/test.yml](.github/workflows/test.yml).

**Test coverage: 93%** (42/42 tests passing).

### Project layout

```
claude_backup/
├── __init__.py
├── cli.py          # Click entry point
├── scanner.py      # Discovers projects + sessions
├── parser.py       # Reads .jsonl files
└── exporter.py     # Renders Markdown

tests/
├── fixtures/       # Fake project data — no real ~/.claude/ data is read in tests
├── test_scanner.py
├── test_parser.py
├── test_exporter.py
└── test_cli.py
```

---

## OpenClaw users

Exported `.md` files can be placed in `~/.openclaw/workspace/memory/` for reference. OpenClaw's `memory_search` will index the content, though the frontmatter fields differ from native OpenClaw memory format.

---

## Warning

This tool reads your Claude Code data directory. It does **not** send anything to external servers. Everything stays local.

---

## License

MIT
