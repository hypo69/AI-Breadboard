# Media Organizer

## Компоненты и поток данных

Исходный workflow задан в `.ai_instructions/knowledge/media_organizer_workflow.md`:

1. `media_scanner.py` обходит медиафайлы и запрашивает TMDB.
2. `genre_classifier.py` обогащает и категоризирует записи через TMDB/Gemini.
3. `database.py` сохраняет записи в SQLite.
4. `report_generator.py` формирует JSON/Markdown-отчёты.
5. `media_rag.py` строит RAG-индекс, а `media_rag_functions.py` предоставляет инструменты Function Calling.
6. `media_auditor.py`, `media_tracker.py` и `media_rebuild.py` обслуживают аудит, торрент-связи и восстановление.

Пути определены в `plugins/media_organizer/core/__init__.py`:

- основная БД: `plugins/media_organizer/data/media.db`;
- RAG БД: `plugins/media_organizer/data/media_rag.db`;
- конфигурация: `plugins/media_organizer/config/`;
- отчёты: `plugins/media_organizer/reports/`.

## SQLite

`MediaDatabase` в `plugins/media_organizer/core/database.py` создаёт таблицы `media` и `duplicates`, а также триггер `trg_check_duplicates`. Уникальность `media` обеспечивается по `path`.

Ключевые группы полей `media`:

- идентификация и файл: `id`, `disk_name`, `path`, `title`, `title_orig`, `title_ru`, `year`, `media_type`, `media_size`;
- классификация: `main_category`, `country`, `genres`, `directors`, `cast`, `rating`, `awards`, `review`;
- сериал: `num_of_seasons`, `num_episodes_per_season`, `status`, `parent_id`, `episode_scan_skipped`;
- описание и рекомендации: `plot`, `atmosphere`, `why_watch`, `mood`, `final_verdict`, `can_stop_at`, `quote`, `facts`, `similar`, `plot_granularity`.

Несколько значений хранятся сериализованными JSON-строками: например `genres`, `directors`, `cast`, `facts`, `similar`, `rating`.

Основные методы: поиск по пути/торренту, `save_media`, получение записи, экспорт всей БД или диска, поиск/консолидация дубликатов, сводка по сериалам и назначение номеров. `normalize_disk_name()` удаляет числовой префикс до первой точки для сопоставления имён дисков.

## RAG и Gemini tools

`media_rag.py` преобразует записи БД в текст и использует `GeminiRAG`. `media_rag_functions.py` предоставляет `search_media`, `get_media_card`, `find_by_exact_title`, `get_random_media`, `rebuild_rag_index`, `get_rag_status`, описание инструментов и диспетчер вызовов. `ask_with_media_rag()` объединяет модель с этими инструментами.

Внутренние промпты классификатора сейчас частично заданы строковыми константами `_PROMPT_*` в `plugins/media_organizer/core/__init__.py`; файл `plugins/media_organizer/config/instruction.md` используется при построении `SYSTEM_INSTRUCTION`. Требование из плана Kiro — вынести **все** промпты во внешние файлы и перечитывать их на каждом запросе — ещё не реализовано.

## Интеграция с плеером

Для будущей разметки ответа `<film>Название</film>` уже есть серверная точка `POST /api/media/by-title`, которая находит путь по русскому, оригинальному или основному названию. Не хватает: инструкции модели о тегах, безопасного разбора нескольких тегов в UI и запуска найденного файла в существующем `playFile()`.

## Правила длинных сериалов

Документация указывает: если сериал имеет более 15 сезонов или более 100 эпизодов, детальная генерация эпизодов Gemini пропускается, а `episode_scan_skipped` должен фиксировать это решение. Перед изменением порогов и формата данных нужно сверить реализацию `genre_classifier.py` с документацией.
