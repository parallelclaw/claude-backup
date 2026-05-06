# claude-backup

> Export your Claude Code sessions, memory, and credentials to local Markdown files — so you keep your work even if Anthropic suspends your account.

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

## What it does

- Scans `~/.claude/sessions/` and exports every conversation to a dated `.md` file
- Extracts project-specific memory and instructions into `memory/` format
- Backs up credentials metadata (not secrets — pointers and config)
- Optionally encrypts exports with `gpg` before writing to disk
- Runs on cron: daily automated backups you forget about

---

## Install

```bash
pip install claude-backup
```

Or clone and run directly:

```bash
git clone https://github.com/parallelclaw/claude-backup.git
cd claude-backup
python -m claude_backup --help
```

---

## Quick Start

```bash
# One-time export
claude-backup export ~/claude-backups/

# With encryption
claude-backup export ~/claude-backups/ --encrypt --gpg-key your@email.com

# Set up daily cron
claude-backup cron --daily ~/claude-backups/
```

---

## What's exported

| Source | Destination | Content |
|--------|-------------|---------|
| `~/.claude/sessions/` | `YYYY-MM-DD/session-{id}.md` | Full conversation history |
| `~/.claude/.credentials.json` | `credentials-meta.json` | Account pointers (not keys) |
| `~/.claude/settings.json` | `settings-backup.json` | Custom instructions & preferences |
| `~/.claude/memory/` | `memory/` | Long-term project context |

---

## OpenClaw users

Exports are compatible with OpenClaw's `memory/` format. Drop `claude-backup/memory/` into your `~/.openclaw/workspace/memory/` directory and your new agent retains project context.

---

## Warning

This tool reads your Claude Code data directory. It does **not** send anything to external servers. Everything stays local. If you use `--encrypt`, even your disk backups are protected.

---

## License

MIT
