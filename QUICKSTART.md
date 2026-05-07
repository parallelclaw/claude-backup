# Quick Start — 5 Minutes to Your First Backup

> Works on **macOS**, **Linux**, and **Windows (WSL2)**. No prior experience required.

---

## What this tool does

Claude Code stores every conversation on your computer in a folder called `~/.claude/projects/`. Those files are in a format (`.jsonl`) that's hard to read. **`claude-backup`** turns them into nice, readable Markdown files you can open in any text editor, search, or archive.

---

## Step 1 — Check that you have Python

Open a terminal and type:

```bash
python3 --version   # macOS / Linux
python --version    # Windows (WSL)
```

You should see **Python 3.10 or higher**.

> **Note:** If you see Python 3.9, you can still install with `pip install -e . --ignore-requires-python`. The code works on 3.9, but official support and CI target 3.10+.

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

You'll see a table of every Claude Code session on your machine. The "First Prompt / Title" column shows the AI-generated session title when Claude Code recorded one, and falls back to your literal first prompt otherwise:

```
Project           Session   First Prompt / Title                          Msgs  Created
────────────────  ────────  ────────────────────────────────────────────  ────  ───────────────────
my-webapp         abc12345  Fix the login bug                             42    2026-05-07T10:42:00
my-webapp         def45678  Add dark mode toggle                          18    2026-05-06T14:00:00
notes-app         ghi78901  Refactor parser for nested blocks             7     2026-05-04T09:15:00
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
| `2026-05-07--abc12345-….full.md` | Everything: every tool call, every shell command, every internal reasoning step | Debugging or auditing what the agent actually did |

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

## Step 6 — Export everything at once

```bash
claude-backup export-all --output ./backups/                    # both files per session
claude-backup export-all --output ./backups/ --mode minimal     # only the clean .md files
```

Each project gets its own subfolder under `./backups/`. You now have a complete Markdown archive of your Claude Code history.

---

## Common questions

**Where does it look for my conversations?**

Default: `~/.claude/projects/` on macOS/Linux, `C:\Users\YourName\.claude\projects\` on Windows (WSL path: `/mnt/c/Users/YourName/.claude/projects/`).

**Can I point it at a different folder?**

Yes — use `--claude-home`:

```bash
claude-backup --claude-home /some/other/path list
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
| Python version error | Running Python 3.9 | `pip install -e . --ignore-requires-python` or upgrade to 3.10+ |

---

## (Optional) Daily auto-backup

Add to your shell profile (`~/.zshrc`, `~/.bashrc`, or `~/.bash_profile`):

```bash
cb_backup() {
    local dest="$HOME/claude-backups"
    mkdir -p "$dest"
    claude-backup export-all --output "$dest" --quiet
    cd "$dest" && git add . && git commit -m "backup $(date +%F)" 2>/dev/null
}
cb_backup
```

Or use cron (macOS / Linux):
```bash
crontab -e
# Add: daily at 9 PM
0 21 * * * /usr/local/bin/claude-backup export-all --output $HOME/claude-backups/ --quiet
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
