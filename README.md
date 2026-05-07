# claude-backup

> Export your Claude Code **and Claude Cowork** sessions to local Markdown — so you keep your work even if Anthropic suspends your account.

[Русский](README.ru.md) · English

> [!TIP]
> **Don't want to read docs?** Paste [the install prompt](./PROMPT.md) into Claude (or any AI assistant) — it'll handle install + your first backup in about 5 minutes, step by step. **This is the recommended path for 90% of users.**

---

## Why

Claude Code and Claude Cowork (the local-agent desktop app) store everything on disk: sessions, project context, custom instructions, subagent transcripts. All of it lives in folders you don't directly manage, and is tied to your Anthropic account.

**If your account gets suspended, rate-limited, or you lose OAuth access — every conversation, every plan, every subagent's research disappears.**

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

> **The good news:** Anthropic only revokes API access. Your local files in `~/.claude/projects/` and `~/Library/Application Support/Claude/` survive untouched on your disk — they're yours, not theirs ([source](https://blog.laozhang.ai/en/posts/claude-code-max-recharge-account-banned)). One command (`claude-backup rescue`) packages everything into a portable bundle you can hand to ChatGPT, Cursor, OpenClaw, or any other AI agent — and pick up exactly where you left off.

---

## 🆘 If your account just got banned — read this first

Run **one command**:

```bash
claude-backup rescue
```

You'll get a `claude-rescue-<today>/` folder containing:

- `README.md` — what this bundle is
- **`HANDOFF_PROMPT.md`** — copy this into your new AI agent (Claude.ai personal account, ChatGPT, Cursor, OpenClaw, a Chinese hosted model — anything)
- `INDEX.md` — every session you ever had, listed by date
- `sessions/` — clean Markdown transcript of each session

The new agent reads the bundle, takes over from Claude, and continues your work with full context. Lazy walkthrough is in [QUICKSTART.md § rescue](./QUICKSTART.md#step-8--rescue-bundle-the-banned-user-escape-hatch).

---

## Quick Start

```bash
git clone https://github.com/parallelclaw/claude-backup.git
cd claude-backup
pip install -e .
```

```bash
# See everything you have — Code AND Cowork sessions in one table
claude-backup list

# Export one session by short ID prefix (works for either source)
claude-backup export f7a07eec --output ~/claude-backups/

# Export everything from both sources (organised by source folder)
claude-backup export-all --output ~/claude-backups/

# Continue a session in a DIFFERENT agent — paste-ready prompt to your clipboard
claude-backup handoff f7a07eec | pbcopy        # macOS
claude-backup handoff f7a07eec | xclip -selection clipboard   # Linux

# Rescue: package EVERYTHING for a new agent (account-banned escape hatch)
claude-backup rescue
```

By default each export produces **two files** side-by-side:
- `<date>--<id>.md` — clean dialogue (your prompts + Claude's text replies)
- `<date>--<id>.full.md` — full audit copy with tool calls, tool results, reasoning, **and any subagent transcripts**

If you only want one of them, pass `--mode minimal` or `--mode full`.

> [!NOTE]
> **Something broke during install or use?** [Open a GitHub issue](https://github.com/parallelclaw/claude-backup/issues/new?template=bug.md) — even a one-line *"install failed at step 3"* is genuinely useful. Most early bugs come from setups I haven't tested, and your report goes straight to a fix.

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

Prints a compact table covering **both** Claude Code and Claude Cowork sessions. The Source column tells you which one. Project paths are decoded from the encoded form they're stored as, and the "First Prompt / Title" column shows Claude's auto-generated session title when present, falling back to the literal first prompt:

```
Source  Project                   Session   First Prompt / Title                          Msgs  Created
──────  ────────────────────────  ────────  ────────────────────────────────────────────  ────  ───────────────────
Code    Documents/Claude          269ed03b  ты сможешь сам подключиться к апи coingecko?  236   2026-04-06T18:34:16
Code    Documents/Claude          0c631197  Install superpowers skill from GitHub         318   2026-04-22T06:40:06
Code    Documents/Claude          f7a07eec  Build claude-backup CLI tool with export      296   2026-05-07T07:35:01
Cowork  beautiful-charming-curie  f3e13345  что ты знаешь про бизнесы связанные с арбит…  188   2026-04-06T17:27:14
Cowork  trusting-friendly-dirac   cfa06cf5  Create slide in PDF or PowerPoint             242   2026-04-22T18:46:35
Cowork  upbeat-epic-feynman       4724eae3  Analyze AI admin business potential           128   2026-04-20T20:01:48
```

Cowork sessions are picked up from `~/Library/Application Support/Claude/local-agent-mode-sessions/` (the local-agent desktop app's data dir). Their `Project` column shows the friendly Cowork-generated codename like `beautiful-charming-curie`.

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

The output is organised by source first, then by the directory layout where each session ran:

```
backups/
├── code/                                       ← regular Claude Code sessions
│   └── Documents/Claude/
│       ├── 2026-04-06--<id>.md
│       ├── 2026-04-06--<id>.full.md
│       └── Projects/Administrator/memex-mvp/
│           └── 2026-05-03--<id>.md
└── cowork/                                     ← Claude Cowork (desktop-agent) sessions
    ├── beautiful-charming-curie/
    │   └── 2026-04-06--<id>.md
    ├── upbeat-epic-feynman/
    │   └── 2026-04-20--<id>.md
    └── session-3c6c44ca/                       ← rare: cwd was the session's own outputs dir
        └── 2026-04-29--<id>.md
```

For Code sessions, hyphens in directory names (`memex-mvp`) are recovered correctly when the original directory still exists on disk — the tool walks the filesystem to disambiguate. For Cowork sessions, the friendly codename Cowork itself generates (`beautiful-charming-curie`) is used directly.

### Custom roots

Each source has its own override flag. Pass either or both — missing roots are silently skipped:

```bash
claude-backup --claude-home /path/to/code list                            # only Code from a custom root
claude-backup --cowork-home /path/to/cowork list                          # only Cowork from a custom root
claude-backup --claude-home /a --cowork-home /b list                      # both, custom roots
```

### Continue a session in another agent (`handoff`)

Sometimes you want to keep going in a *different* AI tool — moving a Cowork conversation to claude.ai web, picking up a Code session in ChatGPT or Cursor, sending the discussion to a colleague's agent. The `handoff` command produces a single paste-ready prompt that:

- Tells the new agent it's continuing your conversation
- Names the source (Claude Code or Claude Cowork) and the original task
- Drops the full dialogue-only transcript inline (no tool noise, so it stays paste-friendly)
- Asks the new agent to acknowledge context and wait for your next message

```bash
claude-backup handoff f7a07eec                                  # print to stdout
claude-backup handoff f7a07eec | pbcopy                         # macOS — straight to clipboard
claude-backup handoff f7a07eec | xclip -selection clipboard     # Linux
claude-backup handoff f7a07eec --output ./handoff.md            # save to a file
claude-backup handoff f7a07eec --lang en                        # force English wrapper
claude-backup handoff f7a07eec --lang ru                        # force Russian wrapper
```

The wrapper language auto-detects from the session: Cyrillic in the title or first prompt → Russian wrapper, otherwise English. The transcript itself is unchanged — the new agent will respond in whatever language the conversation was in.

Workflow:

1. Run `claude-backup handoff <id> | pbcopy`
2. Open Claude.ai (or ChatGPT, Cursor chat, Perplexity, anywhere)
3. Paste into a fresh conversation
4. The agent reads the context, acknowledges in 1–2 sentences
5. You type your next message — the conversation continues there

A 200-message session typically packs into 80–200 KB of text — fine for context windows of any modern hosted assistant.

### Live MCP memory — `feed-memex`

If you run [memex-mvp](https://github.com/parallelclaw/memex-mvp) (a separate local MCP server), `claude-backup feed-memex` writes a clean dialogue-only JSONL of every session into memex's inbox folder (`~/.memex/inbox/`). Memex picks them up via `chokidar`, indexes via SQLite + FTS5, and exposes them through MCP to **any compatible AI agent** — Cursor, Cline, Claude Code, Continue, Zed.

```bash
claude-backup feed-memex            # write all sessions to ~/.memex/inbox/
claude-backup feed-memex --dry-run  # show what would be written
```

Output is idempotent — re-run anytime, memex dedupes by stable msg_id. Once set up, your Cursor agent can just `memex_search("the migration we discussed in April")` and surface real results from your past Code/Cowork conversations. **Zero paste.** Zero context-switching.

Filename convention: `code-<8char>.jsonl` for Claude Code sessions, `cowork-<8char>.jsonl` for Cowork. Memex distinguishes the two via the prefix and tags them with separate `source` values, so you can filter `memex_search` by source.

### Rescue bundle (`rescue`) — the banned-user escape hatch

`handoff` is for one session. `rescue` is for **all of them at once** — built specifically for the situation where Anthropic suspends your account and you need to keep working. Your local files survive (Anthropic only revokes API access, not your disk), so you can package the lot and hand it to a different AI provider.

```bash
claude-backup rescue                                    # writes ./claude-rescue-<today>/
claude-backup rescue --output ~/my-rescue/              # custom location
claude-backup rescue --lang en                          # force English wrapper
```

The bundle is self-contained:

```
claude-rescue-2026-05-07/
├── README.md             # what this bundle is, how to use it
├── HANDOFF_PROMPT.md     # ← THE prompt to paste into your new AI agent
├── INDEX.md              # one line per session, chronological
└── sessions/             # full clean-dialogue transcript of every session
    ├── 2026-04-06--269ed03b.md
    ├── 2026-04-22--0c631197.md
    └── ...
```

**Two ways to use it:**

1. **Lazy (any chat agent — Claude.ai, ChatGPT, Cursor, etc.):** Open `HANDOFF_PROMPT.md`, copy contents, paste into a fresh conversation. The agent acknowledges. When you reference past work, paste the relevant `sessions/<file>.md`.

2. **Thorough (agents with file uploads — Cursor, Claude Projects, ChatGPT Files):** Drop the entire folder as project files, paste `HANDOFF_PROMPT.md` content as the first message. Now the new agent has the full searchable archive.

The wrapper auto-detects the dominant language: if at least half your sessions have Cyrillic titles, the prompt comes out in Russian; otherwise English. Override with `--lang`.

---

## Output format

Each session is written as Markdown with YAML frontmatter. When Claude Code or Cowork has auto-generated a session title, it's used as the document heading and added to the frontmatter. The `source` field tells you whether the session came from Code or Cowork:

```markdown
---
project: "-Users-macbook-Documents-Claude"
session_id: f7a07eec-e18c-4ba5-96da-b798266c7486
source: code
branch: HEAD
model: claude-opus-4-7
messages: 296
exported_at: 2026-05-07T15:30:00Z
subagents: 5
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

The full export (`<id>.full.md`) appends a `# Subagents` section after the main timeline when the session spawned any. Each subagent is its own `## Subagent N: <id>` block with its full transcript, so you can reconstruct what the parallel agents did.

The `<id>.md` file (default and `--mode minimal`) shares the same frontmatter — plus `mode: dialogue-only` — but the body contains only `## User` and `## Assistant` text turns. No `[tool_use: ...]` markers, no tool-result echoes, no extended-thinking blocks, **and no subagent transcripts** (those are pure tool plumbing from a human-reading perspective).

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

## How is this different from cc2md / ccexport / claude-conversation-extractor?

A few similar tools exist for exporting Claude Code sessions to Markdown. They're solid for the basic backup case. Where `claude-backup` differs:

| Capability | `claude-backup` | [cc2md](https://github.com/magarcia/cc2md) | [ccexport](https://github.com/marcheiligers/ccexport) | [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor) | [claudit](https://github.com/adam-leigh/claudit) |
|---|:---:|:---:|:---:|:---:|:---:|
| Claude Code export | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Claude Cowork export** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Subagent transcripts (`<session>/subagents/`)** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Handoff prompt for another AI** (`handoff` command) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Account-rescue bundle** (every session + meta-prompt for new agent) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **AI-installer onboarding** (paste a prompt → AI installs the tool) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Dialogue-only mode (drops tool calls) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Encrypted-thinking-signature stripping | ✅ | ❌ | ❌ | ❌ | ❌ |
| Secret redaction (TruffleHog) | ❌ | ❌ | ✅ | ❌ | ❌ |
| Terminal-rendered preview | ❌ | ✅ | ❌ | ❌ | ❌ |
| Multi-format output (XML, HTML, JSON) | Markdown only | Markdown | Markdown | MD/JSON/HTML | MD/XML |

Short version: if you only want a Claude Code → Markdown export and you're a developer who'll set things up by hand, the alternatives are great choices. If you want **Cowork support**, **portability to other AI agents** (handoff/rescue), and an **install path that works for non-developers** — that's where this tool is the only option today.

---

## Behaviour

- **Two sources, one CLI.** Both Claude Code (`~/.claude/projects/`) and Claude Cowork (`~/Library/Application Support/Claude/local-agent-mode-sessions/`) are auto-discovered. If only one source exists on a machine, the other is silently skipped.
- **Portable handoff.** The `handoff` command produces a paste-ready prompt that lets you continue any session in a different AI agent (Claude.ai, ChatGPT, Cursor, etc.). The wrapper auto-detects Russian/English from the session.
- **Account-rescue bundle.** `rescue` packages every session you've ever had into a self-contained folder with a master meta-prompt — designed for the case where Anthropic suspends your account and you need to keep working in a different agent. Your local files survive bans (Anthropic only revokes API access).
- **Subagents recovered.** Both Code and Cowork spawn subagent transcripts under `<session-id>/subagents/agent-*.jsonl`. The full export pulls them in as separate sections; minimal mode drops them. The frontmatter's `subagents:` count tells you how many were attached.
- **Reads the real Claude Code format.** Metadata (first prompt, message count, created timestamp, AI title) is computed by streaming the `.jsonl` directly. No `sessions-index.json` is required — Claude Code doesn't actually create one.
- **AI-titles surfaced.** When the recording app emits an `ai-title` event, the title shows in `list` output and becomes the document heading.
- **Decoded project names.** Encoded folder names like `-Users-macbook-Documents-Claude` are decoded to readable paths (`Documents/Claude`); Cowork codenames like `-sessions-noble-clever-shannon` keep their hyphenated form.
- **Session ID prefixes.** Any prefix that uniquely identifies a session works — `claude-backup export f7a07eec` resolves to the full UUID. Ambiguous prefixes print all matches and exit.
- **Encrypted thinking signatures stripped.** Extended-thinking `signature` blobs (multi-kilobyte base64) never reach the output. Visible thinking text, when present, is preserved in italics.
- **Graceful degradation.** Empty or corrupted `.jsonl` files are skipped with a warning. The tool never crashes on bad data.
- **No data found** exits with code 1 and a clear error listing both roots that were tried.
- **Unicode-ready.** Correctly handles Russian, emoji, and special characters.
- **Tool-aware.** In full mode, `tool_use` / `tool_result` / `image` blocks render as compact placeholders (`[tool_use: Bash]`, `[image]`) — never as raw JSON dumps.

---

## Development

```bash
pip install -e ".[dev]"
pytest -v --cov=claude_backup
```

CI runs on Python 3.9, 3.10, 3.11, and 3.12 — see [.github/workflows/test.yml](.github/workflows/test.yml).

**Test coverage: 91%** (106/106 tests passing) — covers the real Claude Code format, the legacy spec format, the Cowork nested hierarchy, subagent discovery and rendering, edge cases (empty/corrupt JSONL, unicode, missing roots), `--mode` selection (both / minimal / full), the FS-aware project-path decoder, the `handoff` paste-prompt generator (with Cyrillic/ASCII language detection), the `rescue` bundle (README/INDEX/HANDOFF_PROMPT generation, single-source fallback, default-output behaviour), and CLI integration across both sources.

### Project layout

```
claude_backup/
├── __init__.py
├── cli.py             # Click entry point
├── scanner.py         # Discovers Code + Cowork sessions, decodes project paths
├── parser.py          # Reads .jsonl files (both formats — flat and nested)
└── exporter.py        # Renders Markdown (both modes; weaves subagents in full)

tests/
├── conftest.py            # Shared fixtures + auto-isolation from real Claude data
├── fixtures/              # Fake Claude Code project data
├── fixtures-cowork/       # Fake Cowork hierarchy (account/workspace/local_*)
├── test_scanner.py
├── test_parser.py
├── test_exporter.py
├── test_cli.py
├── test_minimal.py        # Dialogue-only mode + --mode CLI flag
├── test_real_format.py    # Nested message shape, ai-title, project-path decoding
├── test_cowork.py         # Cowork hierarchy + subagent rendering across sources
├── test_handoff.py        # Paste-ready prompt for continuing in another agent
└── test_rescue.py         # Bundled handoff: rescue all sessions for a new provider
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
