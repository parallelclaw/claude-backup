# 🪄 The lazy install — paste this into your AI assistant

Most people don't read 200 lines of docs. So here's the shortest path to a working `claude-backup`:

1. **Open** any AI assistant — Claude Code, claude.ai, ChatGPT, Cursor's chat, anything.
2. **Copy** one of the prompts below.
3. **Paste** into a fresh conversation.
4. **Follow** the assistant's step-by-step instructions.

About 5 minutes from "paste" to "your Claude Code conversations are now in clean Markdown on disk". Skip-ready, error-friendly. No need to come back to this README.

---

## English prompt

Copy everything between the lines:

---

```
I want to install and try `claude-backup` — a CLI tool that exports my Claude Code AND Claude Cowork session history (both apps) to local Markdown files. The repo is https://github.com/parallelclaw/claude-backup.

Walk me through it step by step. After each step, wait for me to paste the output before moving on. Be terse — no walls of text, one short paragraph per step is fine. Don't run commands yourself; print the command and let me run it.

The full path:

1. Verify Python 3.9+ (`python3 --version`). If older, point me at python.org or `brew install python` (macOS) and stop here.
2. Have me `git clone https://github.com/parallelclaw/claude-backup.git` somewhere convenient (default: `~/Desktop`) and `cd` into the repo.
3. Have me run `pip3 install --user -e .`. If pip warns that the install dir isn't on PATH, give me the right `export PATH=...` line for my OS AND tell me how to make it permanent (in `~/.zshrc` on macOS / `~/.bashrc` on Linux).
4. Have me run `claude-backup --version` to confirm the CLI is reachable.
5. Have me run `claude-backup list` and help me read the table. Columns: Source (Code or Cowork) / Project / Session (8-char prefix) / First Prompt or Title / Msgs / Created. Note that the tool auto-finds both Claude Code (`~/.claude/projects/`) and Claude Cowork (`~/Library/Application Support/Claude/local-agent-mode-sessions/`); if I have only one, the other is silently skipped.
6. Pick an interesting session with me and have me run `claude-backup export <8-char-prefix> --output ./backups/`. By default this writes two files: `<id>.md` (clean dialogue, only my prompts and Claude's text replies) and `<id>.full.md` (everything — tool calls, tool results, AND any subagent transcripts the session spawned). Explain when to use each.
7. Have me `open ./backups/<filename>.md` (macOS) or `xdg-open` (Linux) to view the result. Ask what I think.
8. If I want a full backup of everything, have me run `claude-backup export-all --output ~/claude-backups`. Explain that the output is split first by source — `code/` and `cowork/` subfolders — and inside each, organised by project (Code mirrors my real working dirs, Cowork uses the friendly codename like `beautiful-charming-curie` that Cowork itself generates).
9. Mention one more useful command for later: `claude-backup handoff <prefix> | pbcopy` (macOS) or `| xclip -selection clipboard` (Linux). It produces a paste-ready prompt I can drop into Claude.ai, ChatGPT, Cursor, or any other AI assistant to continue the same conversation there. Don't make me try it now unless I ask — just plant the seed so I know it exists.

If a command errors: help me debug, don't just dump a fix. Common issues —
- "Claude data not found" → I haven't used either Claude Code or Cowork on this machine yet
- `pip: command not found` → try `python3 -m pip` instead
- `command not found: claude-backup` after install → PATH issue, see step 3
- "externally-managed-environment" pip error → use `pip3 install --user --break-system-packages -e .` or a venv

Start with step 1.
```

---

## Russian prompt / Промпт на русском

Скопируйте всё между линиями:

---

```
Я хочу установить и попробовать `claude-backup` — CLI-утилиту, которая экспортирует историю моих сессий Claude Code И Claude Cowork (обе утилиты) в локальные Markdown-файлы. Репозиторий — https://github.com/parallelclaw/claude-backup.

Проведи меня по шагам. После каждого шага жди когда я вставлю вывод. Будь лаконичен — никаких стен текста, один короткий абзац на шаг достаточно. Сам команды не выполняй — печатай команду и жди пока я выполню.

Полный путь:

1. Проверить Python 3.9+ (`python3 --version`). Если старее — отправь меня на python.org или скажи `brew install python` (macOS) и останови процесс.
2. `git clone https://github.com/parallelclaw/claude-backup.git` куда-нибудь удобно (по умолчанию `~/Desktop`) и `cd` в репозиторий.
3. `pip3 install --user -e .`. Если pip ругается что папка не в PATH — дай правильную строку `export PATH=...` для моей системы И объясни как сделать перманентным (в `~/.zshrc` на macOS / `~/.bashrc` на Linux).
4. `claude-backup --version` — проверить что CLI работает.
5. `claude-backup list` — помоги прочитать таблицу. Колонки: Source (Code или Cowork) / Project / Session (8-символьный префикс) / First Prompt или Title / Msgs / Created. Заметь что утилита авто-находит и Claude Code (`~/.claude/projects/`), и Claude Cowork (`~/Library/Application Support/Claude/local-agent-mode-sessions/`); если есть только один — другой молча пропускается.
6. Выбери со мной одну сессию и вели мне `claude-backup export <8-символьный-префикс> --output ./backups/`. По умолчанию создаются два файла: `<id>.md` (чистый диалог — только мои промпты и текстовые ответы Claude) и `<id>.full.md` (всё: tool-вызовы, tool-результаты И transcripts subagent'ов которые сессия порождала). Объясни когда использовать каждый.
7. `open ./backups/<filename>.md` (macOS) или `xdg-open` (Linux) — посмотреть результат. Спроси что я думаю.
8. Если хочу выгрузить всё — `claude-backup export-all --output ~/claude-backups`. Объясни что вывод сначала разделён по источнику — подпапки `code/` и `cowork/`, — а внутри каждой организован по проекту (Code зеркалит реальные рабочие директории, Cowork использует дружелюбный кодноим типа `beautiful-charming-curie` который Cowork сам генерирует).
9. Упомяни ещё одну полезную команду на будущее: `claude-backup handoff <prefix> | pbcopy` (macOS) или `| xclip -selection clipboard` (Linux). Она создаёт paste-ready промпт, который можно вставить в Claude.ai, ChatGPT, Cursor или любого другого AI-ассистента, чтобы продолжить тот же разговор там. Не заставляй пробовать сейчас если я не попрошу — просто посади семечко чтобы я знал что это есть.

Если команда выдаёт ошибку — помоги отладить, не вываливай готовый фикс. Частые проблемы:
- "Claude data not found" → я ещё не пользовался ни Claude Code, ни Cowork на этой машине
- `pip: command not found` → попробовать `python3 -m pip`
- `command not found: claude-backup` после установки → PATH, см. шаг 3
- ошибка "externally-managed-environment" от pip → `pip3 install --user --break-system-packages -e .` или venv

Начни с шага 1.
```

---

## Why this works

You're doing what a 1-on-1 onboarding looks like, except your assistant is the one running it. The agent adapts to your OS, your shell, your Python version, your error messages — and is patient with you. No README skim, no copy-paste confusion, no "I got an error and don't know what to do". Just one prompt and 5 minutes of guided conversation.

If you'd rather read: continue with [QUICKSTART.md](./QUICKSTART.md) for the manual walkthrough, or [README.md](./README.md) for the full reference.
