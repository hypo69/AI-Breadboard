# Project Skills (адаптировано из .gemini/skills/)

Этот файл агрегирует все навыки проекта. Применяй соответствующий навык при получении задачи, совпадающей с его описанием.

---

## 🔄 Правило автосинхронизации навыков

В начале КАЖДОГО диалога:
1. Прочитать список директорий `.gemini/skills/`
2. Сравнить с навыками, перечисленными в этом файле (секции `## skill: *`)
3. Если найден новый навык (есть папка в `.gemini/skills/`, но нет секции здесь) — прочитать его `SKILL.md` и добавить новую секцию в этот файл
4. Сообщить пользователю: «Обнаружен новый навык `<name>`, добавлен в `.amazonq/rules/skills.md`»

Текущий эталонный список навыков (обновляется автоматически):
`db-inspector`, `file-saver`, `media-card-builder`, `media-data-collector`, `media-manager`, `rag-search-manager`, `skill-factory`, `smart-deletion-duplicates`, `storage-controller`, `storage-tool`, `tdd-doc-gen`, `torrent-controller`, `web-chat-cli`

---

## skill: db-inspector
**Когда использовать:** анализ, проверка или модификация `media.db`.

- Перед ЛЮБЫМ изменением `media.db` — создать резервную копию: `media.db.MMDD-HHMMSSS`
- Проверка структуры: `python get_schema.py`
- Проверка данных: `python check_db.py`
- Поиск неполных записей: `python find_incomplete_records.py`
- Инспекция RAG: `python inspect_user_rags.py`

---

## skill: file-saver
**Когда использовать:** сохранение файлов на диск.

- `python save_file.py --path <путь> --content "<текст>"`

---

## skill: media-card-builder
**Когда использовать:** составление карточек фильмов и сериалов.

Требования к контенту:
- Сюжет: 150–200 слов
- Атмосфера: ~15 слов
- Описания эпизодов: единый абзац 50–60 слов, без сухих маркеров
- Финал сезона: 1–2 предложения

Шаблон:
```markdown
# Название (Оригинальное название) (Год / 1–N сезоны)
**Тип медиа** | **Жанр** | **Категория:** ...
**Страна:** ... | **Режиссеры:** ... | **В ролях:** ...

**Сюжет:** [150–200 слов]
**Атмосфера:** [~15 слов]

## Сезон N (Год)
* **Серия N.1:** [50–60 слов]
**Финал сезона:** [резюме]
```

---

## skill: media-data-collector
**Когда использовать:** сбор структурированных данных о медиа для RAG.

- Персона: эксперт-киновед, создающий базу знаний
- Языки: русский, иврит, английский
- Единый `entity_id` для всех языковых версий
- Финалы сезонов и серий обязательны, не сокращать

---

## skill: media-manager
**Когда использовать:** сканирование, классификация, аудит медиатеки.

- Полное сканирование: `python run_media_organizer.py`
- Аудит диска: `python audit_media.py --disk ДИСК_N`
- Классификация: `python run_media_organizer.py --title "Название"`

---

## skill: rag-search-manager
**Когда использовать:** поиск медиа.

Приоритет:
1. RAG-индекс: `python .gemini/skills/rag-search-manager/scripts/search_media.py --query "запрос"`
2. Интернет — только если RAG не дал результатов

---

## skill: skill-factory
**Когда использовать:** создание и упаковка новых навыков.

- Упаковка: `python .gemini/skills/skill-factory/scripts/pack.py <путь_к_навыку>`
- Скрипт создаёт `dist/` внутри папки навыка

---

## skill: smart-deletion-duplicates
**Когда использовать:** удаление дубликатов медиа-файлов.

⚠️ Удаление необратимо. Перед выполнением — резервная копия `media.db.MMDD-HHMMSSS`.

1. Подготовить CSV со списком путей в колонке `to_delete`
2. `python scripts/delete_media.py --file <csv> --execute`

Скрипт: удаляет файл с диска (`os.remove`), затем запись из БД (`DELETE FROM media WHERE path = ?`).

---

## skill: storage-controller
**Когда использовать:** управление подключёнными дисками.

- Сканирование дисков: `python -m plugins.media_organizer.core.drive_scanner`
- Текущие диски: `python -c "import os; print(os.environ.get('CONNECTED_DRIVES', ''))"`
- API: `POST /api/control/rescan`

---

## skill: storage-tool
**Когда использовать:** аудит и мониторинг хранилища.

- Аудит наличия файлов: `python audit_disk.py`
- Обновление размеров в БД: `python update_media_sizes.py`
- Статистика по дискам: `python view_storage.py`

---

## skill: tdd-doc-gen
**Когда использовать:** генерация тестов и документации после изменения `.py` файлов.

Протокол (обязателен):
1. Создать `README.md` в каждой новой директории
2. Анализ зависимостей: найти все импорты изменённого модуля
3. Smoke test: `python -c "from src.module import Class; print('OK')"`
4. Генерация тестов — покрытие: Happy Path, Edge Cases, Type Variants, Boundary Values, Error Scenarios, Regression
5. Запуск: `pytest tests/test_<module>.py -v`
6. Документирование (только после зелёных тестов) — формат `hypo69 docblock`, без Sphinx/reST

Жёсткие правила:
- ❌ Не документировать до зелёных тестов
- ❌ Не создавать тест без комментария к каждой переменной
- ✅ Всегда: `assert ..., "Что сломано и почему"`

---

## skill: torrent-controller
**Когда использовать:** управление qBittorrent.

- Назначение ID/категорий: `python assign_torrents_ids.py`
- Синхронизация путей: `python update_torrents_path.py`
- Проверка целостности: `python update_torrent_state.py`
- Очистка метаданных: `python clear_torrents_meta.py`

---

## skill: web-chat-cli
**Когда использовать:** консольный чат с RAG-интеграцией.

- `python .gemini/skills/web-chat-cli/src/chat.py`
