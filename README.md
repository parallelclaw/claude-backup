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

# Mini-log: only your messages and Claude's text replies, no tool calls
claude-backup export f7a07eec --output ~/claude-backups/ --minimal
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

Writes `./backups/2026-05-07--f7a07eec-<full-uuid>.md`. **You only need the first 8 characters of the session ID** — the tool resolves the prefix.

### Mini-log mode (`--minimal`)

When you just want a clean transcript of the conversation — your prompts and Claude's text replies — without tool calls, tool results, or extended-thinking blocks:

```bash
claude-backup export f7a07eec --output ./backups/ --minimal
```

Writes a separate file with a `.minimal.md` suffix, so the full and minimal exports can coexist for the same session. Frontmatter records `mode: dialogue-only` and an adjusted `messages` count. Typically the minimal file is 30–50% the size of the full one.

### Export everything

```bash
claude-backup export-all --output ./backups/
claude-backup export-all --output ./backups/ --minimal   # mini-log version of all sessions
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

`--minimal` mode produces the same frontmatter (with `mode: dialogue-only` added) but the body contains only `## User` and `## Assistant` text turns — no `[tool_use: ...]` markers, no tool-result echoes, no thinking blocks.

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

CI runs on Python 3.10, 3.11, and 3.12 — see [.github/workflows/test.yml](.github/workflows/test.yml).

**Test coverage: 91%** (64/64 tests passing) — covers the real Claude Code format, the legacy spec format, edge cases (empty/corrupt JSONL, unicode, missing index), the `--minimal` mode, and CLI integration.

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
