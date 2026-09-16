---
name: doc-generator
description: Automated documentation generation, validation, and synchronization toolkit for AI-Breadboard.
description_i18n:
  en: Automated documentation generation, validation, and synchronization toolkit for AI-Breadboard.
  ru: Набор инструментов для автоматической пакетной генерации, валидации и синхронизации документации API и скриптов.
  es: Herramientas para generación por lotes, validación y sincronización de documentación de API y scripts.
  he: ערכת כלים ליצירה באצווה, אימות וסנכרון תיעוד API ותסריטים.
---

# 📚 Document Generator & Synchronization Skill

Автоматизированный навык генерации, проверки и синхронизации документации проекта **AI-Breadboard**.

---

## 🎯 Назначение и триггеры активации

Используйте этот навык в следующих сценариях:
1. **Создание / обновление Python модулей:** необходимо сгенерировать актуальную API-документацию на основе docstrings (hypo69 docblock).
2. **Добавление / модификация скриптов (scripts/, manage_tools.py):** требуется обновить сводку и каталог скриптов SCRIPTS_DOCUMENTATION.md и SCRIPTS_SUMMARY.md.
3. **Пакетная синхронизация документации:** пользователь запрашивает команду python manage_tools.py docs generate или python manage_tools.py docs update.
4. **Валидация перед коммитом:** проверка наличия docstrings во всех измененных файлах git.
5. **Проверка структуры и ссылок:** запуск верификации alidate_structure.py и check_links.py.

---

## 🚀 Протокол выполнения (Workflow)

`mermaid
flowchart TD
    A["Trigger: Code Changes or Docs Command"] --> B["Validate Docstrings: manage_tools.py docs update"]
    B --> C["Generate API Markdown: scripts/docs/generate_api.py"]
    C --> D["Update Scripts Summary: scripts/dev/update_scripts_documentation.py"]
    D --> E["Validate Structure & Links: scripts/docs/check_links.py"]
    E --> F["Documentation Synchronized & Verified ✅"]
`

### Шаг 1 — Проверка покрытия docstrings
Перед генерацией убедитесь, что модифицированные файлы содержат docstrings:
`powershell
python manage_tools.py docs update
`

### Шаг 2 — Пакетная генерация документации
Выполните пакетную генерацию всей проектной документации:
`powershell
python manage_tools.py docs generate
`
Что происходит под капотом:
1. scripts/docs/generate_api.py парсит через AST docstrings модулей src.skills, src.ai, src.ai.agents, src.utils и генерирует Markdown-файлы в docs/ru/api/ и docs/en/api/.
2. scripts/dev/update_scripts_documentation.py сканирует каталог scripts/ и корневые скрипты, категоризирует их и формирует SCRIPTS_SUMMARY.md.

### Шаг 3 — Проверка ссылок и целостности
При необходимости валидации ссылок и структуры:
`powershell
python scripts/docs/check_links.py
python scripts/docs/validate_structure.py
`

---

## 🛠️ Команды CLI

| Команда | Описание |
|---|---|
| python manage_tools.py docs generate | Полная пакетная генерация API и каталога скриптов |
| python manage_tools.py docs update | Экспресс-валидация docstrings для измененных в git файлов |
| python scripts/docs/generate_api.py | Прямой вызов генератора API docs |
| python scripts/dev/update_scripts_documentation.py | Прямой вызов генератора каталога скриптов |

---

## 📐 Стандарты оформления Docstrings

Все docstrings в исходном коде Python должны строго следовать стандарту hypo69 docblock на **английском языке**:

`python
def process_data(input_path: Path, max_records: int = 100) -> list[dict]:
    """Processes input files and extracts structured records.

    Reads incoming data files, parses lines, and returns records
    conforming to schema constraints.

    Args:
        input_path (Path): Absolute or relative path to the source file.
        max_records (int, optional): Maximum number of records to parse. Defaults to 100.

    Returns:
        list[dict]: List of parsed record dictionaries.

    Raises:
        FileNotFoundError: If input_path does not exist on disk.
        ValueError: If file content is invalid or corrupted.

    Examples:
        >>> process_data(Path('data.csv'), max_records=10)
        [{'id': 1, 'name': 'Item'}]
    """
`
