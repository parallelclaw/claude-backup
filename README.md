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

# Export one session — short ID prefix is enough
claude-backup export f7a07eec --output ~/claude-backups/

# Export everything (each project gets its own subfolder)
claude-backup export-all --output ~/claude-backups/
```

By default each export produces **two files** side-by-side:
- `<date>--<id>.md` — clean dialogue (your prompts + Claude's text replies)
- `<date>--<id>.full.md` — full audit copy with tool calls, tool results, and reasoning

If you only want one of them, pass `--mode minimal` or `--mode full`.

New users: see [QUICKSTART.md](./QUICKSTART.md) for the full step-by-step guide (macOS, Linux, Windows/WSL).

---

## Install

Requires **Python 3.9+** (CI tests 3.9, 3.10, 3.11, 3.12).

```bash
pip install -e .
```

---

## Usage

### List sessions

```bash
claude-backup list
```

Prints a compact table — project paths are decoded from the encoded form Claude Code stores them as, and the "First Prompt / Title" column shows the AI-generated session title when present, falling back to the literal first prompt:

```
Project           Session   First Prompt / Title                          Msgs  Created
────────────────  ────────  ────────────────────────────────────────────  ────  ───────────────────
Documents/Claude  269ed03b  ты сможешь сам подключиться к апи coingecko?  236   2026-04-06T18:34:16
Documents/Claude  0c631197  Install superpowers skill from GitHub         318   2026-04-22T06:40:06
Documents/Claude  ad73386a  Build task extraction agent from audio files  612   2026-04-23T17:51:28
Documents/Claude  f7a07eec  Build claude-backup CLI tool with export      296   2026-05-07T07:35:01
```

### Export a single session

```bash
claude-backup export f7a07eec --output ./backups/
```

By default writes two files into `./backups/`:

```
2026-05-07--f7a07eec-<full-uuid>.md       ← clean dialogue, the one you'd open to re-read
2026-05-07--f7a07eec-<full-uuid>.full.md  ← audit copy with every tool call and result
```

**You only need the first 8 characters of the session ID** — the tool resolves the prefix.

### Choosing one or both files (`--mode`)

| Flag | Output |
|------|--------|
| _(default)_ | both `<id>.md` and `<id>.full.md` |
| `--mode minimal` | only `<id>.md` (clean dialogue) |
| `--mode full` | only `<id>.full.md` (audit copy) |

The `.md` file is the version you'll usually open — typically half the size of the audit copy and reads like a normal chat log. The `.full.md` is the safety net: every tool call, every shell output, every internal reasoning step — useful when you actually need to debug what the agent did.

### Export everything

```bash
claude-backup export-all --output ./backups/                    # both files per session
claude-backup export-all --output ./backups/ --mode minimal     # only the clean .md files
claude-backup export-all --output ./backups/ --mode full        # only the .full.md audit copies
```

Each project gets its own subdirectory under `--output`.

### Custom Claude root

Override the default `~/.claude/projects/` location:

```bash
claude-backup --claude-home /path/to/projects list
```

---

## Output format

Each session is written as Markdown with YAML frontmatter. When Claude Code has auto-generated a session title, it's used as the document heading and added to the frontmatter:

```markdown
---
project: "-Users-macbook-Documents-Claude"
session_id: f7a07eec-e18c-4ba5-96da-b798266c7486
branch: HEAD
model: claude-opus-4-7
messages: 296
exported_at: 2026-05-07T15:30:00Z
title: Build claude-backup CLI tool with export
---

# Build claude-backup CLI tool with export

_-Users-macbook-Documents-Claude / HEAD / f7a07eec-e18c-4ba5-96da-b798266c7486_

## User (07:35:01)
Build a backup tool for my Claude Code sessions...

## Assistant (07:35:08)
I'll create the utility according to the spec...

## Assistant (07:35:08)
[tool_use: Bash]

## User (07:35:09)
(Bash output here)

## Assistant (07:35:14)
[tool_use: Write]
...
```

The `<id>.md` file (default and `--mode minimal`) shares the same frontmatter — plus `mode: dialogue-only` — but the body contains only `## User` and `## Assistant` text turns. No `[tool_use: ...]` markers, no tool-result echoes, no extended-thinking blocks.

---

## Why the dialogue-only export is more than "the smaller one"

The default `<id>.md` isn't just a slimmer file. Sessions where you produced real intellectual content turn into **self-contained knowledge artifacts** — Markdown documents that live independently of Claude Code, the conversation context, and even your account. A two-hour session where you and Claude analyzed a 1600-message Telegram dump and distilled a Top-10 AI trends list becomes one readable file you can drop into Obsidian, share with a colleague, or commit to a notes repo.

What survives the export cleanly:

- **AI-generated session titles** become the document `H1` heading and land in frontmatter as `title:`.
- **Mixed Cyrillic / Latin text, emoji, and tables** render correctly — the parser is unicode-clean throughout.
- **Per-turn timestamps** (e.g. `## User (06:40:06)`) make the timeline easy to follow when re-reading.
- **Block-level Markdown** — headings, bold, lists, code fences, blockquotes — passes through untouched.
- **Claude Code's auto-compaction events** (`This session is being continued from a previous conversation...`) are preserved as visible boundaries, so you can see exactly where the original session ran out of context and was summarized.

### Known quirk: the title is frozen at session start

Claude Code generates the AI-title **once**, near the start of a session, and never updates it. So a session that begins "install the superpowers skill" but pivots into a deep AI-trends analysis still ends up with a heading that reflects only the original intent. This is a Claude Code behaviour, not a bug in the exporter — but if it becomes a real pain point, a future `--retitle` flag could regenerate the heading from a summary of the actual content.

---

## Behaviour

- **Reads the real Claude Code format.** Metadata (first prompt, message count, created timestamp, AI title) is computed by streaming the `.jsonl` directly. No `sessions-index.json` is required — Claude Code doesn't actually create one.
- **AI-titles surfaced.** When Claude Code records an `ai-title` event, the title is shown in `list` output and used as the Markdown heading on export.
- **Decoded project names.** The encoded folder names Claude Code uses (e.g. `-Users-macbook-Documents-Claude`) are decoded to readable paths (`Documents/Claude`) in the `list` table.
- **Session ID prefixes.** Any prefix that uniquely identifies a session works — `claude-backup export f7a07eec` resolves to the full UUID. Ambiguous prefixes print all matches and exit.
- **Encrypted thinking signatures stripped.** Extended-thinking `signature` blobs (multi-kilobyte base64) never reach the output. Visible thinking text, when present, is preserved in italics.
- **Graceful degradation.** Empty or corrupted `.jsonl` files are skipped with a warning. The tool never crashes on bad data.
- **Missing `~/.claude/`** exits with code 1 and a clear error message.
- **Unicode-ready.** Correctly handles Russian, emoji, and special characters.
- **Tool-aware.** In full mode, `tool_use` / `tool_result` / `image` blocks render as compact placeholders (`[tool_use: Bash]`, `[image]`) — never as raw JSON dumps.

---

## Development

```bash
pip install -e ".[dev]"
pytest -v --cov=claude_backup
```

CI runs on Python 3.9, 3.10, 3.11, and 3.12 — see [.github/workflows/test.yml](.github/workflows/test.yml).

**Test coverage: 91%** (68/68 tests passing) — covers the real Claude Code format, the legacy spec format, edge cases (empty/corrupt JSONL, unicode, missing index), `--mode` selection (both / minimal / full), and CLI integration.

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
