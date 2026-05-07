# claude-backup

> Экспортируй сессии Claude Code **и Claude Cowork** в локальные Markdown-файлы — чтобы сохранить работу, даже если Anthropic заблокирует аккаунт.

[English](README.md) · Русский

> [!TIP]
> **Не хотите читать доки?** Вставьте [готовый промпт](./PROMPT.md) в Claude (или любой другой AI-ассистент) — он проведёт через установку и первый бэкап за ~5 минут, по шагам. **Рекомендуемый путь для 90% пользователей.**

---

## Зачем

Claude Code и Claude Cowork (десктоп-приложение local-agent) хранят всё на диске: сессии, контекст проекта, кастомные инструкции, transcripts subagent'ов. Всё это лежит в папках, которыми вы не управляете напрямую, и привязано к вашему Anthropic-аккаунту.

**Если аккаунт заблокируют, ограничат по rate limit или потеряете доступ к OAuth — каждый разговор, каждый план, каждое исследование subagent'а исчезает.**

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

> **Хорошая новость:** Anthropic блокирует только API-доступ. Ваши локальные файлы в `~/.claude/projects/` и `~/Library/Application Support/Claude/` остаются нетронутыми на диске — это ваши файлы, не их ([источник](https://blog.laozhang.ai/en/posts/claude-code-max-recharge-account-banned)). Одна команда (`claude-backup rescue`) собирает всё в портативный пакет, который можно отдать ChatGPT, Cursor, OpenClaw, любой другой AI-модели — и продолжить ровно с того места где остановились.

---

## 🆘 Если аккаунт только что забанили — читай это первым делом

Запусти **одну команду**:

```bash
claude-backup rescue
```

Получишь папку `claude-rescue-<сегодня>/` с содержимым:

- `README.md` — что это за пакет
- **`HANDOFF_PROMPT.md`** — копируешь и вставляешь в нового AI-агента (Claude.ai на личном аккаунте, ChatGPT, Cursor, OpenClaw, китайская хостед-модель — что угодно)
- `INDEX.md` — все ваши сессии, по дате
- `sessions/` — чистый Markdown-transcript каждой сессии

Новый агент читает пакет, принимает у Claude роль партнёра и продолжает работу с полным контекстом. Полная инструкция в [QUICKSTART.md § rescue](./QUICKSTART.md#step-8--rescue-bundle-the-banned-user-escape-hatch).

---

## Быстрый старт

```bash
git clone https://github.com/parallelclaw/claude-backup.git
cd claude-backup
pip install -e .
```

```bash
# Посмотреть всё что есть — Code и Cowork в одной таблице
claude-backup list

# Экспортировать одну сессию по короткому префиксу ID (работает для любого источника)
claude-backup export f7a07eec --output ~/claude-backups/

# Экспортировать всё из обоих источников (организовано по source-папкам)
claude-backup export-all --output ~/claude-backups/

# Продолжить сессию в ДРУГОМ агенте — paste-ready промпт прямо в буфер
claude-backup handoff f7a07eec | pbcopy        # macOS
claude-backup handoff f7a07eec | xclip -selection clipboard   # Linux

# Rescue: упаковать ВСЁ для нового агента (escape hatch при бане аккаунта)
claude-backup rescue
```

По умолчанию каждый экспорт создаёт **два файла** рядом:
- `<date>--<id>.md` — чистый диалог (ваши промпты + текстовые ответы Claude)
- `<date>--<id>.full.md` — полная audit-копия с tool-вызовами, tool-результатами, блоками рассуждений **и transcripts subagent'ов**

Если нужен только один из них — `--mode minimal` или `--mode full`.

Новым пользователям: см. [QUICKSTART.md](./QUICKSTART.md) — полная пошаговая инструкция (macOS, Linux, Windows/WSL).

---

## Установка

Требуется **Python 3.9+** (CI тестирует 3.9, 3.10, 3.11, 3.12).

```bash
pip install -e .
```

---

## Использование

### Список сессий

```bash
claude-backup list
```

Выводит компактную таблицу с **обоими** источниками — Claude Code и Claude Cowork. Столбец Source показывает откуда сессия. Столбец «First Prompt / Title» показывает AI-сгенерированный заголовок (если есть), иначе первый промпт:

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

Cowork-сессии берутся из `~/Library/Application Support/Claude/local-agent-mode-sessions/` (директория данных десктоп-приложения local-agent). Их колонка `Project` показывает дружелюбный кодноим вроде `beautiful-charming-curie`, который сам Cowork генерирует.

### Экспорт одной сессии

```bash
claude-backup export f7a07eec --output ./backups/
```

По умолчанию создаёт два файла в `./backups/`:

```
2026-05-07--f7a07eec-<полный-uuid>.md       ← чистый диалог, тот что хочется открыть
2026-05-07--f7a07eec-<полный-uuid>.full.md  ← полная audit-копия со всеми tool-вызовами
```

**Достаточно первых 8 символов session ID** — утилита сама находит сессию по префиксу.

### Выбор файлов (`--mode`)

| Флаг | Что записывает |
|------|----------------|
| _(по умолчанию)_ | оба файла: `<id>.md` и `<id>.full.md` |
| `--mode minimal` | только `<id>.md` (чистый диалог) |
| `--mode full` | только `<id>.full.md` (audit-копия) |

`.md` файл — тот, что обычно хочется открыть: как правило в 2 раза меньше audit-копии и читается как обычный чат-лог. `.full.md` — это страховка: каждый tool-вызов, каждый shell-вывод, каждый блок reasoning. Полезно когда реально нужно отдебажить что делал агент.

### Экспорт всего

```bash
claude-backup export-all --output ./backups/                    # оба файла на каждую сессию
claude-backup export-all --output ./backups/ --mode minimal     # только чистые .md
claude-backup export-all --output ./backups/ --mode full        # только .full.md audit-копии
```

Вывод организован сначала по источнику, затем по структуре где сессия запускалась:

```
backups/
├── code/                                       ← обычные Claude Code сессии
│   └── Documents/Claude/
│       ├── 2026-04-06--<id>.md
│       ├── 2026-04-06--<id>.full.md
│       └── Projects/Administrator/memex-mvp/
│           └── 2026-05-03--<id>.md
└── cowork/                                     ← Claude Cowork сессии
    ├── beautiful-charming-curie/
    │   └── 2026-04-06--<id>.md
    ├── upbeat-epic-feynman/
    │   └── 2026-04-20--<id>.md
    └── session-3c6c44ca/                       ← редкое: cwd был внутренней output-папкой сессии
        └── 2026-04-29--<id>.md
```

Для Code-сессий дефисы в именах директорий (`memex-mvp`) восстанавливаются корректно, если исходная директория существует на диске — утилита обходит файловую систему чтобы разрешить ambiguity. Для Cowork-сессий используется напрямую кодноим, который Cowork сам генерирует (`beautiful-charming-curie`).

### Кастомные пути

У каждого источника свой override-флаг. Передайте любой из них или оба — отсутствующие пути молча пропускаются:

```bash
claude-backup --claude-home /path/to/code list                            # только Code из кастомного root
claude-backup --cowork-home /path/to/cowork list                          # только Cowork из кастомного root
claude-backup --claude-home /a --cowork-home /b list                      # оба, кастомные пути
```

### Продолжить сессию в другом агенте (`handoff`)

Иногда хочется продолжить разговор в *другом* AI-инструменте — перенести Cowork-сессию в claude.ai web, подцепить Code-сессию в ChatGPT или Cursor, отправить разговор агенту коллеги. Команда `handoff` создаёт один paste-ready промпт, который:

- Говорит новому агенту что он продолжает разговор
- Называет источник (Claude Code или Claude Cowork) и исходную задачу
- Подсовывает полный dialogue-only транскрипт (без tool-шума, чтобы paste не разросся)
- Просит нового агента подтвердить контекст и подождать следующего сообщения

```bash
claude-backup handoff f7a07eec                                  # печать в stdout
claude-backup handoff f7a07eec | pbcopy                         # macOS — сразу в буфер
claude-backup handoff f7a07eec | xclip -selection clipboard     # Linux
claude-backup handoff f7a07eec --output ./handoff.md            # сохранить в файл
claude-backup handoff f7a07eec --lang en                        # форсить English-обёртку
claude-backup handoff f7a07eec --lang ru                        # форсить Russian-обёртку
```

Язык обёртки авто-определяется по сессии: если в title или первом промпте есть кириллица → русская обёртка, иначе английская. Сам транскрипт не меняется — новый агент ответит на том же языке что был в разговоре.

Workflow:

1. Запустить `claude-backup handoff <id> | pbcopy`
2. Открыть Claude.ai (или ChatGPT, Cursor чат, Perplexity, что угодно)
3. Вставить в новый разговор
4. Агент читает контекст, подтверждает в 1–2 предложениях
5. Печатаешь следующее сообщение — разговор продолжается там

Сессия из 200 сообщений обычно укладывается в 80–200 КБ текста — нормально для context window любого современного хостед-ассистента.

### Rescue-пакет (`rescue`) — escape hatch для забаненного юзера

`handoff` это для одной сессии. `rescue` — это для **всех сразу**, специально под ситуацию когда Anthropic заблокировал аккаунт и нужно продолжать работать. Локальные файлы переживают бан (Anthropic блокирует только API-доступ, не диск), так что можно упаковать всё и отдать другому AI-провайдеру.

```bash
claude-backup rescue                                    # пишет в ./claude-rescue-<сегодня>/
claude-backup rescue --output ~/my-rescue/              # кастомное место
claude-backup rescue --lang en                          # форсить английскую обёртку
```

Пакет самодостаточный:

```
claude-rescue-2026-05-07/
├── README.md             # что это за пакет, как использовать
├── HANDOFF_PROMPT.md     # ← ЭТОТ промпт вставляешь в нового AI-агента
├── INDEX.md              # одна строка на сессию, хронологически
└── sessions/             # полный чистый-диалог transcript каждой сессии
    ├── 2026-04-06--269ed03b.md
    ├── 2026-04-22--0c631197.md
    └── ...
```

**Два способа использования:**

1. **Ленивый (любой чат-агент — Claude.ai, ChatGPT, Cursor и т.д.):** Открой `HANDOFF_PROMPT.md`, скопируй содержимое, вставь в новый разговор. Агент подтверждает. Когда сошлёшься на прошлую работу — вставь нужный `sessions/<file>.md`.

2. **Тщательный (агенты с file uploads — Cursor, Claude Projects, ChatGPT Files):** Загрузи всю папку как файлы проекта, первым сообщением вставь содержимое `HANDOFF_PROMPT.md`. Теперь у нового агента весь архив, в котором можно искать.

Язык обёртки авто-выбирается по доминирующему языку: если хотя бы половина сессий с кириллицей — промпт на русском, иначе английский. Можно переопределить через `--lang`.

---

## Формат вывода

Каждая сессия сохраняется как Markdown с YAML frontmatter. Если Claude Code или Cowork сгенерировал заголовок сессии, он попадает в frontmatter и используется как H1 заголовок документа. Поле `source` показывает источник — Code или Cowork:

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
...
```

Полный экспорт (`<id>.full.md`) приклеивает после основной timeline секцию `# Subagents` если сессия их порождала. Каждый subagent — отдельный блок `## Subagent N: <id>` со своим transcript'ом, чтобы можно было реконструировать что делали параллельные агенты.

В файле `<id>.md` (по умолчанию и при `--mode minimal`) frontmatter тот же — плюс поле `mode: dialogue-only`, — но в теле остаются только турны `## User` и `## Assistant` с реальным текстом. Без `[tool_use: ...]`, без эхо tool-результатов, без блоков extended thinking, **и без transcripts subagent'ов** (они с точки зрения чтения человеком — чистая tool-плумбинг).

---

## Почему dialogue-only экспорт — это не просто «версия поменьше»

Файл `<id>.md` по умолчанию — это не просто компактный экспорт. Сессии, в которых родилось содержательное интеллектуальное содержимое, превращаются в **полностью самодостаточные knowledge-artifact'ы** — Markdown-документы, которые живут отдельно от Claude Code, контекста разговора и даже вашего аккаунта. Двухчасовая сессия, где вы вместе с Claude разобрали 1600 сообщений Telegram-дампа и сформулировали Top-10 трендов в ИИ, превращается в один читаемый файл, который можно положить в Obsidian, отправить коллеге или закоммитить в notes-репозиторий.

Что переживает экспорт без потерь:

- **AI-сгенерированные заголовки сессии** становятся H1 документа и попадают в frontmatter как `title:`.
- **Смешанный кириллица / латиница, emoji, таблицы** рендерятся корректно — парсер unicode-чистый по всему пайплайну.
- **Метки времени по каждому турну** (`## User (06:40:06)`) дают понятный таймлайн при перечитывании.
- **Block-level Markdown** — заголовки, **bold**, списки, code fences, блок-цитаты — проходит сквозь экспортёр нетронутым.
- **События auto-compaction'а Claude Code'а** (`This session is being continued from a previous conversation...`) сохраняются как видимые границы — видно, где исходная сессия упёрлась в context limit и была сжата.

### Один любопытный артефакт: title заморожен на старте сессии

Claude Code генерирует AI-title **один раз**, в начале сессии, и больше никогда его не обновляет. Поэтому сессия, начавшаяся с «установи superpowers», но ушедшая на 90% в анализ ИИ-трендов, остаётся с заголовком про superpowers. Это поведение Claude Code, а не баг экспортёра — но если это станет реальной болью, в будущем можно добавить флаг `--retitle`, который заново соберёт заголовок из summary реального содержимого сессии.

---

## Чем это отличается от cc2md / ccexport / claude-conversation-extractor?

В Anthropic-нише уже есть несколько утилит для экспорта Claude Code в Markdown. Для базового backup-кейса они нормальные. В чём `claude-backup` отличается:

| Возможность | `claude-backup` | [cc2md](https://github.com/magarcia/cc2md) | [ccexport](https://github.com/marcheiligers/ccexport) | [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor) | [claudit](https://github.com/adam-leigh/claudit) |
|---|:---:|:---:|:---:|:---:|:---:|
| Экспорт Claude Code | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Экспорт Claude Cowork** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Subagent transcripts (`<session>/subagents/`)** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Handoff-промпт для другого AI** (команда `handoff`) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Account-rescue пакет** (все сессии + meta-промпт для нового агента) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **AI-installer onboarding** (paste prompt → AI ставит утилиту) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Dialogue-only режим (без tool-вызовов) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Удаление зашифрованных thinking-сигнатур | ✅ | ❌ | ❌ | ❌ | ❌ |
| Secret redaction (TruffleHog) | ❌ | ❌ | ✅ | ❌ | ❌ |
| Terminal-rendered предпросмотр | ❌ | ✅ | ❌ | ❌ | ❌ |
| Несколько форматов (XML, HTML, JSON) | только Markdown | Markdown | Markdown | MD/JSON/HTML | MD/XML |

Короткая версия: если нужен только экспорт Claude Code → Markdown и вы разработчик который всё настроит руками — альтернативы отличные. Если нужны **поддержка Cowork**, **портативность в другие AI-агенты** (handoff/rescue) и **путь установки для не-разработчиков** — на сегодня это единственная утилита с такой комбинацией.

---

## Поведение

- **Два источника, один CLI.** И Claude Code (`~/.claude/projects/`), и Claude Cowork (`~/Library/Application Support/Claude/local-agent-mode-sessions/`) обнаруживаются автоматически. Если на машине только один источник — другой молча пропускается.
- **Портативный handoff.** Команда `handoff` создаёт paste-ready промпт, чтобы продолжить любую сессию в другом AI-агенте (Claude.ai, ChatGPT, Cursor и т.д.). Обёртка авто-выбирает русский или английский по сессии.
- **Account-rescue пакет.** `rescue` упаковывает все ваши сессии в самодостаточную папку с master meta-промптом — специально под случай когда Anthropic блокирует аккаунт и нужно продолжать работу в другом агенте. Локальные файлы переживают бан (Anthropic блокирует только API-доступ).
- **Subagents восстанавливаются.** И Code, и Cowork порождают transcripts subagent'ов в `<session-id>/subagents/agent-*.jsonl`. Полный экспорт подтягивает их как отдельные секции; minimal-режим их роняет. Поле `subagents:` в frontmatter показывает сколько было приклеено.
- **Читает реальный формат Claude Code.** Метаданные (первый промпт, число сообщений, дата создания, AI-title) считаются прямо из `.jsonl` потоковым чтением. Никакого `sessions-index.json` не требуется — Claude Code его на самом деле не создаёт.
- **AI-titles на видном месте.** Если приложение записало событие `ai-title`, заголовок отображается в `list` и используется как H1 в Markdown-документе.
- **Декодинг имён проектов.** Закодированные пути типа `-Users-macbook-Documents-Claude` превращаются в читаемые (`Documents/Claude`); Cowork-кодноимы вроде `-sessions-noble-clever-shannon` сохраняются с дефисами в исходном виде.
- **Префиксы session ID.** Любой префикс, однозначно идентифицирующий сессию, работает — `claude-backup export f7a07eec` найдёт нужный UUID. Если префикс неоднозначный — выводятся все совпадения и происходит выход.
- **Зашифрованные thinking-сигнатуры удаляются.** Многокилобайтные base64-сигнатуры extended thinking никогда не попадают в вывод. Видимый текст рассуждений (если есть) сохраняется в италике.
- **Graceful degradation.** Пустые или повреждённые `.jsonl` пропускаются с предупреждением. Утилита никогда не падает на битых данных.
- **Если данных нигде нет** — выход с кодом 1 и понятным сообщением, перечисляющим оба root'а где она искала.
- **Unicode** — корректно обрабатывает русский, emoji и спецсимволы.
- **Tool-aware.** В полном режиме блоки `tool_use` / `tool_result` / `image` рендерятся как компактные плейсхолдеры (`[tool_use: Bash]`, `[image]`), а не сырые JSON-дампы.

---

## Разработка

```bash
pip install -e ".[dev]"
pytest -v --cov=claude_backup
```

CI запускается на Python 3.9, 3.10, 3.11 и 3.12 — см. [.github/workflows/test.yml](.github/workflows/test.yml).

**Покрытие тестами: 91%** (106/106 тестов проходят) — реальный формат Claude Code, legacy-формат из спеки, вложенная иерархия Cowork, обнаружение и рендеринг subagent'ов, edge-кейсы (пустой/битый JSONL, unicode, отсутствующие root'ы), выбор `--mode` (both / minimal / full), FS-aware декодинг путей, генератор `handoff` paste-промптов (с авто-детектом кириллицы/ASCII), `rescue` пакет (генерация README/INDEX/HANDOFF_PROMPT, fallback на один источник, поведение default-output), и интеграционные тесты CLI по обоим источникам.

### Структура проекта

```
claude_backup/
├── __init__.py
├── cli.py             # Точка входа Click
├── scanner.py         # Обнаружение Code + Cowork сессий, декодинг путей
├── parser.py          # Чтение .jsonl (оба формата — flat и nested)
└── exporter.py        # Рендеринг Markdown (оба режима; subagents в full)

tests/
├── conftest.py            # Общие фикстуры + автоизоляция от реальных Claude-данных
├── fixtures/              # Фейковые Claude Code project data
├── fixtures-cowork/       # Фейковая Cowork-иерархия (account/workspace/local_*)
├── test_scanner.py
├── test_parser.py
├── test_exporter.py
├── test_cli.py
├── test_minimal.py        # Dialogue-only режим + CLI флаг --mode
├── test_real_format.py    # Вложенный формат message, ai-title, декодинг путей
├── test_cowork.py         # Cowork-иерархия + рендеринг subagent'ов в обоих источниках
├── test_handoff.py        # Paste-ready промпт для продолжения в другом агенте
└── test_rescue.py         # Bundled handoff: спасти все сессии для нового провайдера
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
