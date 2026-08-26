---
languages:
  - id: ru
    name: Русский
    native: Русский
  - id: en
    name: English
    native: English
  - id: he
    name: עברית
    native: Hebrew
---

[Switch language | Переключить язык | החלף שפה 🌐](#language-switch)

<div lang="ru" style="display:none;">

# Prompts — модульная система промптов

Директория содержит атомарные файлы инструкций для AI-агентов медиатеки.
Вместо одного монолитного промпта используется набор специализированных модулей,
которые собираются в нужную комбинацию через `prompt_loader.py`.

## Структура

```
prompts/
│
├── core/                        — базовые модули (нужны всегда)
│   ├── identity.md              — кто агент и что он делает
│   ├── categories.md            — 11 разрешённых категорий медиа
│   └── output_schema.json       — JSON Schema структуры ответа
│
├── narrator/                    — модули для режима диктора
│   ├── tts_rules.md             — правила TTS: числа словами, только русский
│   └── narrator_style.md        — стиль текста: запрет «это», размеры полей
│
├── chat/                        — модули для режима чата
│   └── chat_rules.md            — правила чат-агента
│
├── examples/                    — примеры заполненных JSON
│   └── series_example.json      — эталонный пример для сериала
│
└── media_organizer/             — точка сборки основного агента
    ├── system_instruction.md    — индекс: ссылки на все модули
    ├── prompt_research.md       — правила для режима исследования
    └── prompt_tts.md            — дополнительные TTS-правила
```

## Какой агент получает какие модули

| Модуль | Chat Agent | Narrator Agent |
|---|:---:|:---:|
| `core/identity.md` | ✓ | ✓ |
| `core/categories.md` | ✓ | ✓ |
| `core/output_schema.json` | ✓ | ✓ |
| `narrator/tts_rules.md` | — | ✓ |
| `narrator/narrator_style.md` | ✓ | ✓ |
| `chat/chat_rules.md` | ✓ | — |
| `examples/series_example.json` | ✓ | ✓ |

## Сборка промптов

Промпты собираются через `src/prompt_loader.py`:

```python
from src.prompt_loader import load_chat_prompt, load_narrator_prompt

chat_prompt = load_chat_prompt()
narrator_prompt = load_narrator_prompt()
```

## Принципы модификации

- Каждый файл отвечает за одну задачу.
- При изменении правил редактируется только соответствующий модуль.
- Новые правила добавляются как новый файл, а не расширяют существующий.
- При добавлении нового файла — обновить эту таблицу и `prompt_loader.py`.

</div>

<div lang="en">

# Prompts — Modular Prompt System

Directory contains atomic instruction files for AI agents of the media library.
Instead of a monolithic prompt, a set of specialized modules is used,
assembled into the required combination via `prompt_loader.py`.

## Structure

```
prompts/
│
├── core/                        — base modules (always required)
│   ├── identity.md              — who the agent is and what it does
│   ├── categories.md            — 11 allowed media categories
│   └── output_schema.json       — JSON Schema of response structure
│
├── narrator/                    — modules for narrator mode
│   ├── tts_rules.md             — TTS rules: numbers in words, Russian only
│   └── narrator_style.md        — text style: forbid "это", field sizes
│
├── chat/                        — modules for chat mode
│   └── chat_rules.md            — chat agent rules
│
├── examples/                    — filled JSON examples
│   └── series_example.json      — reference example for a series
│
└── media_organizer/             — main agent assembly point
    ├── system_instruction.md    — index: links to all modules
    ├── prompt_research.md       — rules for research mode
    └── prompt_tts.md            — additional TTS rules
```

## Which Agent Receives Which Modules

| Module | Chat Agent | Narrator Agent |
|---|:---:|:---:|
| `core/identity.md` | ✓ | ✓ |
| `core/categories.md` | ✓ | ✓ |
| `core/output_schema.json` | ✓ | ✓ |
| `narrator/tts_rules.md` | — | ✓ |
| `narrator/narrator_style.md` | ✓ | ✓ |
| `chat/chat_rules.md` | ✓ | — |
| `examples/series_example.json` | ✓ | ✓ |

## Prompt Assembly

Prompts are assembled via `src/prompt_loader.py`:

```python
from src.prompt_loader import load_chat_prompt, load_narrator_prompt

chat_prompt = load_chat_prompt()
narrator_prompt = load_narrator_prompt()
```

## Modification Principles

- Each file is responsible for one task.
- When changing rules, only the corresponding module is edited.
- New rules are added as a new file, not extending the existing one.
- When adding a new file — update this table and `prompt_loader.py`.

</div>

<div lang="he" style="display:none;">

# Prompts — מערכת פרומפטים מודולרית

התיקייה מכילה קבצי הוראות אטומיים לסוכני AI של ספריית המדיה.
במקום פרומפט מונוליטי אחד, נעשה שימוש במערכת מודולים מיוחדים,
המורכבים לשילוב הנדרש באמצעות `prompt_loader.py`.

## מבנה

```
prompts/
│
├── core/                        — מודולים בסיסיים (תמיד נדרשים)
│   ├── identity.md              — מיהו הסוכן ומה הוא עושה
│   ├── categories.md            — 11 קטגוריות מדיה מותרות
│   └── output_schema.json       — JSON Schema של מבנה התשובה
│
├── narrator/                    — מודולים למצב קריין
│   ├── tts_rules.md             — כללי TTS: מספרים במילים, רוסית בלבד
│   └── narrator_style.md        — סגנון טקסט: איסור "это", גודל שדות
│
├── chat/                        — מודולים למצב צ'אט
│   └── chat_rules.md            — כללי סוכן צ'אט
│
├── examples/                    — דוגמאות JSON ממולאות
│   └── series_example.json      — דוגמת ייחוס לסדרה
│
└── media_organizer/             — נקודת הרכבת הסוכן הראשי
    ├── system_instruction.md    — אינדקס: קישורים לכל המודולים
    ├── prompt_research.md       — כללים למצב מחקר
    └── prompt_tts.md            — כללי TTS נוספים
```

## איזה סוכן מקבל אילו מודולים

| מודול | סוכן צ'אט | סוכן קריין |
|---|:---:|:---:|
| `core/identity.md` | ✓ | ✓ |
| `core/categories.md` | ✓ | ✓ |
| `core/output_schema.json` | ✓ | ✓ |
| `narrator/tts_rules.md` | — | ✓ |
| `narrator/narrator_style.md` | ✓ | ✓ |
| `chat/chat_rules.md` | ✓ | — |
| `examples/series_example.json` | ✓ | ✓ |

## הרכבת פרומפטים

הפרומפטים מורכבים באמצעות `src/prompt_loader.py`:

```python
from src.prompt_loader import load_chat_prompt, load_narrator_prompt

chat_prompt = load_chat_prompt()
narrator_prompt = load_narrator_prompt()
```

## עקרונות שינוי

- כל קובץ אחראי למשימה אחת.
- בעת שינוי כללים, רק המודול המתאים נערך.
- כללים חדשים מתווספים כקובץ חדש, לא כהרחבה של קיים.
- בהוספת קובץ חדש — לעדכן טבלה זו ואת `prompt_loader.py`.

</div>

---

## Language Switch / Переключатель языков / החלפת שפה 🌐

<div align="center">

**[Русский 🇷🇺](#language-switch)** | **[English 🇺🇸](#language-switch)** | **[עברית 🇮🇱](#language-switch)**

</div>

**Instructions:** Search for `<div lang="...">` blocks above and toggle `style="display:none;"` to switch language.

**Инструкции:** Найдите блоки `<div lang="...">` выше и переключите `style="display:none;"` для смены языка.

**הוראות:** חפשו בלוקים `<div lang="...">` למעלה והחליפו את `style="display:none;"` להחלפת שפה.

---

## Translation Status / Статус перевода / סטטוס תרגום

| Language | Status |
|----------|--------|
| 🇷🇺 Russian | ✓ Translated |
| 🇺🇸 English | ✓ Default |
| 🇮🇱 Hebrew | ✓ Translated |