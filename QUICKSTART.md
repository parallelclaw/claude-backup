# Quick Start — 5 Minutes to Your First Backup

> Works on **macOS**, **Linux**, and **Windows (WSL2)**. No prior experience required.

> [!TIP]
> **Even faster path:** paste [the install prompt](./PROMPT.md) into Claude (or any AI assistant) and it'll walk you through this whole guide as a conversation, adapting to your OS and any errors. Most people prefer this over reading.

---

## What this tool does

Claude Code and Claude Cowork (the local-agent desktop app) both store every conversation on your computer — in `~/.claude/projects/` and `~/Library/Application Support/Claude/local-agent-mode-sessions/` respectively. Those files are in a format (`.jsonl`) that's hard to read. **`claude-backup`** finds both, walks any subagents they spawned, and turns the lot into nice, readable Markdown files you can open in any text editor, search, or archive.

---

## Step 1 — Check that you have Python

Open a terminal and type:

```bash
python3 --version   # macOS / Linux
python --version    # Windows (WSL)
```

You should see **Python 3.9 or higher**. (CI tests 3.9, 3.10, 3.11, 3.12.)

If Python is not installed:
- **macOS:** install from [python.org/downloads](https://www.python.org/downloads/) or run `brew install python`
- **Linux:** `sudo apt install python3 python3-pip` (Debian/Ubuntu)
- **Windows:** use **WSL2** (Ubuntu) — native Windows CMD/PowerShell is not tested

---

## Step 2 — Install claude-backup

```bash
git clone https://github.com/parallelclaw/claude-backup.git
cd claude-backup
pip install -e .
```

> If `pip install` complains about permissions, try `pip install --user -e .` instead.

That's it. You can now run `claude-backup` from any folder.

---

## Step 3 — See what conversations you have

```bash
claude-backup list
```

You'll see a table of every conversation on your machine — across **both** Claude Code and Claude Cowork. The Source column tells you which app it came from. The "First Prompt / Title" column shows the AI-generated session title when Claude recorded one, and falls back to your literal first prompt otherwise:

```
Source  Project                   Session   First Prompt / Title                          Msgs  Created
──────  ────────────────────────  ────────  ────────────────────────────────────────────  ────  ───────────────────
Code    my-webapp                 abc12345  Fix the login bug                             42    2026-05-07T10:42:00
Code    my-webapp                 def45678  Add dark mode toggle                          18    2026-05-06T14:00:00
Cowork  beautiful-charming-curie  ghi78901  Q2 results slide deck                         88    2026-05-04T09:15:00
```

Each row is one conversation. The **Session** column shows just the first 8 characters of the ID — that's all you need to copy for the next step.

---

## Step 4 — Export a single conversation

Copy the 8-character **Session** prefix from the table (e.g. `abc12345`) and run:

```bash
claude-backup export abc12345 --output ./backups/
```

You'll see:

```
Exported: backups/2026-05-07--abc12345-...md
Exported: backups/2026-05-07--abc12345-...full.md
```

**Two files** are written by default:

| File | What's inside | When to use |
|------|---------------|-------------|
| `2026-05-07--abc12345-….md` | The conversation: your prompts + Claude's text replies, nothing else | Re-reading later, archiving, sharing |
| `2026-05-07--abc12345-….full.md` | Everything: every tool call, every shell command, every internal reasoning step, **plus full transcripts of any subagents the session spawned** | Debugging or auditing what the agent actually did |

Open the `.md` file in any text editor — that's the readable one. It looks like this:

```markdown
---
project: "-Users-yourname-projects-my-webapp"
session_id: abc12345-aaaa-bbbb-cccc-dddddddddddd
branch: main
model: claude-sonnet-4-6
messages: 42
exported_at: 2026-05-07T15:30:00Z
mode: dialogue-only
title: Fix the login bug
---

# Fix the login bug

_-Users-yourname-projects-my-webapp / main / abc12345-..._

## User (10:42:46)
fix the login bug

## Assistant (10:42:50)
Here's the fix...
```

The `.full.md` file looks similar but includes lines like `## Assistant (10:42:51)\n[tool_use: Edit]` followed by `## User (10:42:52)\nFile updated.` — the agent's tool plumbing.

---

## Step 5 — Want only one of the two files?

```bash
# Only the clean conversation
claude-backup export abc12345 --output ./backups/ --mode minimal

# Only the audit copy
claude-backup export abc12345 --output ./backups/ --mode full

# Both (default — same as no flag)
claude-backup export abc12345 --output ./backups/ --mode both
```

The clean version is typically **half the size** of the audit copy and is what you'll usually want.

---

## Step 6 — Continue this conversation in another agent

Want to keep going on this session in **claude.ai web**, **ChatGPT**, **Cursor**, or another AI tool? One command makes a paste-ready prompt:

```bash
# macOS — straight to your clipboard
claude-backup handoff abc12345 | pbcopy

# Linux
claude-backup handoff abc12345 | xclip -selection clipboard
```

Now open the other agent, paste, and hit send. The pasted message tells the new agent it's continuing your conversation, includes the full clean transcript, and asks it to acknowledge context. After it confirms, you keep typing as if you'd never switched.

The wrapper text auto-detects Russian/English from the session, so you don't have to think about it. Pass `--lang en` or `--lang ru` to override, or `--output handoff.md` to save the prompt to a file instead of stdout.

---

## Step 7 — Export everything at once

```bash
claude-backup export-all --output ./backups/                    # both files per session
claude-backup export-all --output ./backups/ --mode minimal     # only the clean .md files
```

The backup tree is split by source first, then mirrors how each app organises sessions. For example:

```
backups/
├── code/                              ← Claude Code sessions, mirroring your real working dirs
│   └── Documents/Claude/
│       ├── 2026-04-22--<id>.md
│       └── 2026-05-07--<id>.md
└── cowork/                            ← Claude Cowork sessions, by friendly codename
    ├── beautiful-charming-curie/
    │   └── 2026-04-06--<id>.md
    └── upbeat-epic-feynman/
        └── 2026-04-20--<id>.md
```

You now have a complete Markdown archive of every Claude conversation across both apps.

---

## Step 8 — Rescue bundle: the banned-user escape hatch

If your Anthropic account ever gets suspended, **your local files survive** — Anthropic only revokes API access. The `rescue` command packages every session you've ever had into a self-contained folder you can hand to any other AI agent (your personal Claude.ai account, ChatGPT, Cursor, OpenClaw, even a Chinese hosted model) to keep working with full context.

```bash
claude-backup rescue
# → writes ./claude-rescue-2026-05-07/ with everything you need
```

What's inside:

```
claude-rescue-2026-05-07/
├── README.md             # what this bundle is, how to use it
├── HANDOFF_PROMPT.md     # ← THE prompt you paste into the new agent
├── INDEX.md              # one line per session, chronological
└── sessions/             # full clean transcripts, one .md per session
    └── ...
```

**The lazy way (works in any chat agent):**

1. Open `claude-rescue-2026-05-07/HANDOFF_PROMPT.md`
2. Copy its full contents
3. Open a new conversation in your other AI agent (Claude.ai, ChatGPT, Cursor, etc.)
4. Paste, send. The agent reads the index, acknowledges, asks for specifics when needed.
5. Continue typing. When you reference past work, paste the relevant `sessions/<file>.md`.

**The thorough way (for agents that take file uploads):**

1. Drop the entire `claude-rescue-<date>/` folder as project files (Cursor, Claude Projects, ChatGPT with Files all support this).
2. First message: paste contents of `HANDOFF_PROMPT.md`.
3. The agent now has the full archive, indexed and searchable.

The bundle's wrapper text auto-detects whether your sessions are mostly Russian or English. Force one with `--lang en` or `--lang ru`.

---

## Common questions

**Where does it look for my conversations?**

Two places, both auto-detected:
- **Claude Code:** `~/.claude/projects/` (Windows/WSL: `/mnt/c/Users/YourName/.claude/projects/`)
- **Claude Cowork:** `~/Library/Application Support/Claude/local-agent-mode-sessions/` (macOS only)

If only one exists, the tool just uses that one. No flag needed.

**Can I point it at a different folder?**

Yes — each source has its own override:

```bash
claude-backup --claude-home /some/other/code-path list
claude-backup --cowork-home /some/other/cowork-path list
```

**Does it modify or delete anything?**

No. The tool only reads from `~/.claude/`. It writes new Markdown files to the output folder you specify. Your original Claude Code data is never touched.

**I see "Claude projects directory not found".**

That means you haven't used Claude Code on this machine yet, or it's installed for a different user account. Open Claude Code and have at least one conversation, then try again.

**A conversation file is corrupted — will the tool crash?**

No. It will print a warning, skip the bad lines, and continue with the rest.

**Why are some Session IDs so short in the table?**

The table shows only the first 8 characters of each session ID for readability. The full UUID is in the exported filename. You can pass the short prefix to `export` — the tool resolves it automatically.

**My exports used to contain huge walls of base64 — is that still a thing?**

No. Earlier versions accidentally rendered Claude's encrypted "thinking signatures" as JSON dumps, which produced kilobytes of base64 noise per assistant turn. The current parser strips those entirely while preserving any visible reasoning text.

**How do I update to a newer version?**

```bash
cd claude-backup
git pull
pip install -e .
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `~/.claude/ not found` | Claude Code never ran | Open Claude Code at least once |
| `Session not found` | Wrong session ID | Run `claude-backup list` and copy full ID |
| `Permission denied` | Installed with `sudo` | Use `pip install --user -e .` |
| Empty `.md` files | No messages in session | Check `messageCount` in `list` output |
| Corrupt JSONL warning | Malformed `.jsonl` lines | Normal — tool skips bad lines, continues |
| Windows: command not found | Native CMD/PowerShell | Use **WSL2** — native Windows not tested |
| Python version error | Running Python &lt;3.9 | Upgrade to Python 3.9 or newer |

---

## (Optional) Daily auto-backup

Add to your shell profile (`~/.zshrc`, `~/.bashrc`, or `~/.bash_profile`):

```bash
cb_backup() {
    local dest="$HOME/claude-backups"
    mkdir -p "$dest"
    claude-backup export-all --output "$dest" >/dev/null
    cd "$dest" && git add . && git commit -m "backup $(date +%F)" 2>/dev/null
}
cb_backup
```

Or use cron (macOS / Linux):
```bash
crontab -e
# Add: daily at 9 PM
0 21 * * * /usr/local/bin/claude-backup export-all --output $HOME/claude-backups/ >/dev/null 2>&1
```

---

## Next steps

- Add a calendar reminder to run `claude-backup export-all` once a month — instant rolling backup.
- Open the generated Markdown files in Obsidian, VS Code, or Logseq for full-text search across all your past sessions.
- Read the full [README.md](./README.md) for behaviour details, development setup, and output format.
- Open an [Issue](https://github.com/parallelclaw/claude-backup/issues) if something breaks.

---

**One-command summary:**
```bash
git clone https://github.com/parallelclaw/claude-backup.git && cd claude-backup && pip install -e . && claude-backup list
```
