# claude-backup

> Экспортируй сессии Claude Code, память и настройки в локальные Markdown-файлы — чтобы сохранить работу, даже если Anthropic заблокирует аккаунт.

[English](README.md) · Русский

---

## Зачем

Claude Code хранит всё в `~/.claude/`. Сессии, контекст проекта, кастомные инструкции, память. Всё это живёт на серверах Anthropic и в локальном кеше, который вы не контролируете.

**Если аккаунт заблокируют, ограничат по rate limit или потеряете доступ к OAuth — память проекта исчезнет.**

> *"Купил подписку Claude Max 5x, прилетела блокировка. Ощущение, как-будто лучшего друга и напарника потерял..."*
> — Реальный пользователь, май 2026

Этот инструмент решает проблему.

---

## Реальные истории

Claude нанял стороннюю компанию для верификации. Они ошиблись и **массово отметили легитимные аккаунты** — включая платящих пользователей, которые ничего не нарушали.

> *"Claude нанял специальную компанию для проверки пользователей. Похоже компания ошиблась и массово отметила как левые множество реально нормальных и чистых аккаунтов. Увы, но разбираться будут долго."*

Пользователи, оплатившие через нестандартные каналы или использовавшие VPN, пострадали больше всего. Апелляции занимают месяцы. При этом **месяцы проектного контекста испаряются**.

> *"Я использую клод для бэкенда, в основном. Бесплатная версия с таким объемом задач не справится. Да, оплатил окольными путями — может быть из-за этого + vpn detect."*

**claude-backup не предотвращает баны. Он предотвращает амнезию.**

---

## Быстрый старт

```bash
git clone https://github.com/parallelclaw/claude-backup.git
cd claude-backup
pip install -e .
```

```bash
# Посмотреть, что есть
claude-backup list

# Экспортировать одну сессию
claude-backup export abc-123 --output ~/claude-backups/

# Экспортировать всё
claude-backup export-all --output ~/claude-backups/
```

Новым пользователям: см. [QUICKSTART.md](./QUICKSTART.md) — полная пошаговая инструкция (macOS, Linux, Windows/WSL).

---

## Установка

Требуется **Python 3.10+** (CI тестирует 3.10, 3.11, 3.12).

```bash
pip install -e .
```

> **Примечание:** Если у вас Python 3.9, установка возможна с `pip install -e . --ignore-requires-python`. Код использует `from __future__ import annotations` и работает на 3.9, но официальная поддержка — 3.10+.

---

## Использование

### Список сессий

```bash
claude-backup list
```

Выводит таблицу:

```
Project    Session ID              First Prompt         Msg Count  Created              Git Branch
─────────  ──────────────────────  ───────────────────  ─────────  ───────────────────  ──────────
my-webapp  abc-123                 fix auth bug         42         2026-05-07T10:42:00Z main
my-webapp  def-456                 add unicode support  18         2026-05-06T14:00:00Z feature/unicode
```

### Экспорт одной сессии

```bash
claude-backup export abc-123 --output ./backups/
```

Создаёт `./backups/2026-05-07--abc-123.md`.

### Экспорт всего

```bash
claude-backup export-all --output ./backups/
```

Каждый проект получает свою поддиректорию в `--output`.

### Кастомный путь к Claude

Переопределить стандартный `~/.claude/projects/`:

```bash
claude-backup --claude-home /path/to/projects list
```

---

## Формат вывода

Каждая сессия сохраняется как Markdown с YAML frontmatter:

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

## Поведение

- **Graceful degradation** — пустые или повреждённые `.jsonl` пропускаются с warning'ом. Утилита никогда не падает на битых данных.
- **Orphan-сессии** — сессии, найденные через `.jsonl`, но отсутствующие в `sessions-index.json`, всё равно экспортируются (с минимальными метаданными).
- **Ghost-записи** — сессии в индексе без файла `.jsonl` на диске отображаются в списке, но не экспортируются.
- **Отсутствующий `~/.claude/`** — выход с кодом 1 и понятным сообщением об ошибке.
- **Unicode** — корректно обрабатывает русский, emoji и спецсимволы.
- **Tool-aware** — сохраняет блоки `tool_use` / `tool_result` в читаемом Markdown.

---

## Разработка

```bash
pip install -e ".[dev]"
pytest -v --cov=claude_backup
```

CI запускается на Python 3.10, 3.11 и 3.12 — см. [.github/workflows/test.yml](.github/workflows/test.yml).

**Покрытие тестами: 93%** (42/42 тестов проходят).

### Структура проекта

```
claude_backup/
├── __init__.py
├── cli.py          # Точка входа Click
├── scanner.py      # Обнаружение проектов и сессий
├── parser.py       # Чтение .jsonl
└── exporter.py     # Рендеринг Markdown

tests/
├── fixtures/       # Фейковые данные — реальные ~/.claude/ не читаются в тестах
├── test_scanner.py
├── test_parser.py
├── test_exporter.py
└── test_cli.py
```

---

## Пользователям OpenClaw

Экспортированные `.md` файлы можно разместить в `~/.openclaw/workspace/memory/` для справки. `memory_search` OpenClaw проиндексирует содержимое, хотя поля frontmatter отличаются от нативного формата OpenClaw.

---

## Предупреждение

Этот инструмент читает директорию данных Claude Code. Он **не отправляет ничего на внешние серверы**. Всё остаётся локально.

---

## Лицензия

MIT
