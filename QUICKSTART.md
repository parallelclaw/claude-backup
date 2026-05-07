# Quick Start — 3 Minutes to Your First Backup

> Works on **macOS**, **Linux**, and **Windows (WSL2)**.

---

## 1. Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) installed and used at least once (so `~/.claude/` exists)
- Python **3.10+**
- `pip` or `uv`

Check Python version:
```bash
python3 --version   # macOS / Linux
python --version    # Windows
```

---

## 2. Install `claude-backup`

### Option A — From source (recommended for latest)

```bash
git clone https://github.com/parallelclaw/claude-backup.git
cd claude-backup
pip install -e .
```

### Option B — From PyPI (when published)

```bash
pip install claude-backup
```

---

## 3. Verify installation

```bash
claude-backup --version
```

Expected output:
```
claude-backup 0.1.0
```

---

## 4. See what you have

```bash
claude-backup list
```

Example output:
```
Project              Session ID              Messages  Branch     Created
─────────────────────────────────────────────────────────────────────────────
my-webapp           a1b2c3d4-e5f6-...       156       main       2026-05-01
my-webapp           e5f6g7h8-i9j0-...       42        fix-auth   2026-05-03
landing-page        i9j0k1l2-m3n4-...       89        dev        2026-05-02
```

---

## 5. Export one session

```bash
# Create a directory for backups
mkdir -p ~/claude-backups

# Export a single session by ID
claude-backup export a1b2c3d4 --output ~/claude-backups/
```

Check the result:
```bash
ls ~/claude-backups/
# → 2026-05-01--a1b2c3d4.md
```

Open it:
```bash
# macOS
open ~/claude-backups/2026-05-01--a1b2c3d4.md

# Linux
cat ~/claude-backups/2026-05-01--a1b2c3d4.md

# Windows (WSL)
explorer.exe ~/claude-backups/2026-05-01--a1b2c3d4.md
```

---

## 6. Export everything

```bash
claude-backup export-all --output ~/claude-backups/
```

Result:
```
~/claude-backups/
├── 2026-05-01--a1b2c3d4.md
├── 2026-05-03--e5f6g7h8.md
├── 2026-05-02--i9j0k1l2.md
└── manifest.json          # index of all exported sessions
```

---

## 7. (Optional) Daily auto-backup

Add to your shell profile (`~/.zshrc`, `~/.bashrc`, or `~/.bash_profile`):

```bash
# Daily Claude Code backup
cb_backup() {
    local dest="$HOME/claude-backups"
    mkdir -p "$dest"
    claude-backup export-all --output "$dest" --quiet
    cd "$dest" && git add . && git commit -m "backup $(date +%F)" 2>/dev/null
}

# Run when opening a new terminal
cb_backup
```

Or use cron (macOS / Linux):
```bash
# Edit crontab
crontab -e

# Add line — runs daily at 9 PM
0 21 * * * /usr/local/bin/claude-backup export-all --output $HOME/claude-backups/ --quiet
```

---

## 8. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `~/.claude/ not found` | Claude Code never ran on this machine | Open Claude Code at least once |
| `Session not found` | Wrong session ID | Run `claude-backup list` and copy full ID |
| `Permission denied` | Installed with `sudo` | Use `pip install --user` or virtualenv |
| Empty `.md` files | Session was cleared / never had messages | Check `claude-backup list` for `messageCount` |
| Windows: command not found | Native CMD/PowerShell | Use **WSL2** (Ubuntu) — `claude-backup` is not tested on native Windows |

---

## Next Steps

- Read the full [README.md](./README.md) for advanced features (`--format`, `--encrypt`, `--since`)
- See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) if you want to hack on the code
- Open an [Issue](https://github.com/parallelclaw/claude-backup/issues) if something breaks

---

**One-command summary:**
```bash
git clone https://github.com/parallelclaw/claude-backup.git && cd claude-backup && pip install -e . && claude-backup list
```
