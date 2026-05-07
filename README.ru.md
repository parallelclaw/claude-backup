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

# Экспортировать одну сессию — короткого префикса ID хватит
claude-backup export f7a07eec --output ~/claude-backups/

# Экспортировать всё (каждый проект — в отдельную папку)
claude-backup export-all --output ~/claude-backups/

# Mini-лог: только ваши сообщения и текстовые ответы Claude, без tool-вызовов
claude-backup export f7a07eec --output ~/claude-backups/ --minimal
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

Выводит компактную таблицу — пути проектов декодируются из закодированного формата Claude Code, а столбец «First Prompt / Title» показывает AI-сгенерированный заголовок сессии (если есть), либо первый промпт пользователя:

```
Project           Session   First Prompt / Title                          Msgs  Created
────────────────  ────────  ────────────────────────────────────────────  ────  ───────────────────
Documents/Claude  269ed03b  ты сможешь сам подключиться к апи coingecko?  236   2026-04-06T18:34:16
Documents/Claude  0c631197  Install superpowers skill from GitHub         318   2026-04-22T06:40:06
Documents/Claude  ad73386a  Build task extraction agent from audio files  612   2026-04-23T17:51:28
Documents/Claude  f7a07eec  Build claude-backup CLI tool with export      296   2026-05-07T07:35:01
```

### Экспорт одной сессии

```bash
claude-backup export f7a07eec --output ./backups/
```

Создаёт `./backups/2026-05-07--f7a07eec-<полный-uuid>.md`. **Достаточно первых 8 символов session ID** — утилита сама находит сессию по префиксу.

### Mini-лог (`--minimal`)

Когда нужен чистый транскрипт диалога — только ваши промпты и текстовые ответы Claude, без tool-вызовов, tool-результатов и блоков extended thinking:

```bash
claude-backup export f7a07eec --output ./backups/ --minimal
```

Создаётся отдельный файл с суффиксом `.minimal.md`, чтобы полный и mini-экспорты могли существовать одновременно для одной сессии. В frontmatter — `mode: dialogue-only` и пересчитанный `messages`. Обычно mini-лог занимает 30–50% от объёма полного экспорта.

### Экспорт всего

```bash
claude-backup export-all --output ./backups/
claude-backup export-all --output ./backups/ --minimal   # mini-версия всех сессий
```

Каждый проект получает свою поддиректорию в `--output`.

### Кастомный путь к Claude

Переопределить стандартный `~/.claude/projects/`:

```bash
claude-backup --claude-home /path/to/projects list
```

---

## Формат вывода

Каждая сессия сохраняется как Markdown с YAML frontmatter. Если Claude Code сгенерировал заголовок сессии, он попадает в frontmatter и используется как H1 заголовок документа:

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
...
```

В режиме `--minimal` frontmatter тот же (плюс поле `mode: dialogue-only`), но в теле остаются только турны `## User` и `## Assistant` с реальным текстом — без `[tool_use: ...]`, без эхо tool-результатов, без блоков thinking.

---

## Поведение

- **Читает реальный формат Claude Code.** Метаданные (первый промпт, число сообщений, дата создания, AI-title) считаются прямо из `.jsonl` потоковым чтением. Никакого `sessions-index.json` не требуется — Claude Code его на самом деле не создаёт.
- **AI-titles на видном месте.** Если Claude Code зафиксировал событие `ai-title`, заголовок отображается в `list` и используется как H1 в экспортированном Markdown.
- **Декодинг имён проектов.** Закодированные пути (`-Users-macbook-Documents-Claude`) превращаются в читаемые (`Documents/Claude`) в таблице `list`.
- **Префиксы session ID.** Любой префикс, однозначно идентифицирующий сессию, работает — `claude-backup export f7a07eec` найдёт нужный UUID. Если префикс неоднозначный, утилита выводит все совпадения и выходит.
- **Зашифрованные thinking-сигнатуры удаляются.** Многокилобайтные base64-сигнатуры extended thinking никогда не попадают в вывод. Видимый текст рассуждений (если есть) сохраняется в италике.
- **Graceful degradation.** Пустые или повреждённые `.jsonl` пропускаются с предупреждением. Утилита никогда не падает на битых данных.
- **Отсутствующий `~/.claude/`** — выход с кодом 1 и понятным сообщением об ошибке.
- **Unicode** — корректно обрабатывает русский, emoji и спецсимволы.
- **Tool-aware.** В полном режиме блоки `tool_use` / `tool_result` / `image` рендерятся как компактные плейсхолдеры (`[tool_use: Bash]`, `[image]`), а не сырые JSON-дампы.

---

## Разработка

```bash
pip install -e ".[dev]"
pytest -v --cov=claude_backup
```

CI запускается на Python 3.10, 3.11 и 3.12 — см. [.github/workflows/test.yml](.github/workflows/test.yml).

**Покрытие тестами: 91%** (64/64 тестов проходят) — реальный формат Claude Code, legacy-формат из спеки, edge-кейсы (пустой/битый JSONL, unicode, отсутствующий индекс), режим `--minimal` и интеграционные тесты CLI.

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
