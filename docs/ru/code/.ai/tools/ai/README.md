# tools/ai/ — Инструменты для агентов ИИ

Скрипты для **внутреннего использования агентами и моделями ИИ**.  
Обеспечивают RAG-индексацию, поиск по коду и управление навыками.

---

## Файлы

| Файл | Назначение | Команда |
|------|------------ |---------|
| `rebuild_dev_rag.py` | Пересборка RAG-индекса кодовой базы | `py tools/ai/rebuild_dev_rag.py` |
| `rebuild_rag.py` | Пересборка RAG-индекса медиатеки | `py tools/ai/rebuild_rag.py` |
| `search_code.py` | Семантический поиск по кодовой базе | `py tools/ai/search_code.py --query "..."` |
| `validate_rag_files.py` | Валидация файлов RAG-индексов | `py tools/ai/validate_rag_files.py` |
| `inspect_user_rags.py` | Инспекция пользовательских RAG-индексов | `py tools/ai/inspect_user_rags.py` |
| `update_docs.py` | Обновление документации кода | `py tools/ai/update_docs.py` |
| `package_skill.py` | Упаковка навыков (skills) | `py tools/ai/package_skill.py <name>` |

---

## Когда запускать (для агентов)

| Сценарий | Команда |
|----------|---------|
| После изменения `.py` файлов в `src/` | `py tools/ai/rebuild_dev_rag.py` |
| Поиск по коду в процессе разработки | `py tools/ai/search_code.py --query "..."` |
| После создания нового навыка | `py tools/ai/package_skill.py <name>` |

---

## Правила

- Все скрипты запускаются из **корня проекта** (`C:\ai-assistant`) с активированным `.venv`
- Никогда не импортируй эти скрипты как модули — только прямой запуск
- При добавлении нового инструмента — обновить таблицу выше
