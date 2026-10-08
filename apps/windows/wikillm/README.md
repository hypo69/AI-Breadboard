# WikiLLM: Progressive Windows Knowledge Base

**WikiLLM** — это интеллектуальная система прогрессивного накопления и извлечения знаний (Progressive Knowledge Acquisition + Retrieval) по наблюдаемым артефактам операционной системы Windows и структуре кодовой базы.

В отличие от классического RAG (который каждый раз выполняет ресурсоемкий поиск по эмбеддингам и обращается к LLM), WikiLLM использует парадигму:

$$\text{Observe} \longrightarrow \text{Identify} \longrightarrow \text{Resolve} \longrightarrow \text{Learn} \longrightarrow \text{Store} \longrightarrow \text{Reuse}$$

После первого исследования артефакта через Gemini все последующие запросы обслуживаются **мгновенно за $O(1)$** из локальной базы SQLite без обращения к LLM.

---

## 🏛 Архитектурные слои знаний

Система разделена на два фундаментальных слоя:

```
                    WikiLLM
                       │
          ┌────────────┴────────────┐
          │                         │
    Code Knowledge            Diagnostic Knowledge
          │                         │
   функции / классы           Event ID
   компоненты                 коды ошибок (Win32 / NTSTATUS)
   API / методы               пути Registry
   зависимости / импорты      процессы / службы / драйверы
   docstrings                 симптомы и первопричины
```

---

## 🔍 Четырёхуровневый конвейер поиска (4-Level Lookup)

```
                Входной артефакт
                       │
                       ▼
           [Level 1: Exact Match] ──────────► Найдено в SQLite (O(1))
                       │ (Miss)
                       ▼
        [Level 2: Fingerprint Match] ──────► Найдено по шаблону/хешу
                       │ (Miss)
                       ▼
         [Level 3: Semantic Match] ────────► Найдено по FTS5 / смыслу
                       │ (Miss)
                       ▼
        [Level 4: Gemini LLM Resolver] ────► Синтез строгого JSON
                       │
                       ▼
         Валидация + Запись в SQLite ──────► Следующий запрос мгновенный!
```

1. **Level 1 — Exact Match**: Мгновенный поиск по детерминированному каноническому ключу (`win32:0x80070490`, `windows_event:DistributedCOM:10016`, `process:svchost.exe`, `code:apps.windows.telemetry:SystemCollector`).
2. **Level 2 — Fingerprint Template Match**: Поиск по структурному шаблону сообщения со стертыми динамическими параметрами (GUID, адреса, даты).
3. **Level 3 — Semantic / FTS5 Match**: Полнотекстовый поиск по морфологии, симптомам и тегам в виртуальной таблице SQLite FTS5.
4. **Level 4 — Gemini Structured Resolver**: Вызов Gemini с получением строгого JSON, Pydantic-валидацией и автоматическим занесением факта в базу знаний.

---

## 📊 Самообучение и эмпирические наблюдения

WikiLLM не только сохраняет знания от LLM, но и фиксирует реальную телеметрию с локального компьютера:
- Счётчик повторений каждого артефакта (`total_occurrences`).
- Граф корреляций совместных событий ($X \to Y$ co-occurrences).
- Разделение статусов достоверности: `observed`, `documented`, `inferred`, `llm_generated`.

---

## ⚡ Синхронный и асинхронный режимы

- **Synchronous Mode**: Для критических интерактивных запросов (мгновенный вызов Gemini при промахе кэша).
- **Asynchronous Mode**: Для потока телеметрии из `IncidentDetector` / `SystemCollector`. Неизвестные события ставятся в очередь `KnowledgeQueue`, не блокируя сборщик телеметрии.

---

## 🚀 Использование через CLI и TUI

```powershell
# Разрешить ошибку или событие
py -m apps.windows.wikillm resolve "0x80070490"
py -m apps.windows.wikillm resolve "Event ID 10016 DistributedCOM"

# Полнотекстовый поиск по базе знаний
py -m apps.windows.wikillm search "DCOM permissions"

# Индексация исходного кода
py -m apps.windows.wikillm index-code --path apps/windows

# Просмотр статистики кэш-хитов и сущностей
py -m apps.windows.wikillm stats

# Интерактивный терминал
py -m apps.windows.wikillm tui
```

---

## 🌐 REST API Эндпоинты

- `POST /api/windows/wikillm/resolve` — Разрешение артефакта через 4-уровневый конвейер.
- `GET /api/windows/wikillm/entities/{canonical_key}` — Получение подробностей о сущности.
- `GET /api/windows/wikillm/entities` — Постраничный список сущностей.
- `GET /api/windows/wikillm/search?q=...` — Полнотекстовый поиск FTS5.
- `GET /api/windows/wikillm/observations/{canonical_key}` — Локальная статистика наблюдений.
- `POST /api/windows/wikillm/observe` — Фиксация совместных наблюдений.
- `POST /api/windows/wikillm/code/ingest` — Индексация кодовой базы.
- `GET /api/windows/wikillm/stats` — Метрики эффективности кэша и размер базы.

---

## 💾 Локальное хранилище данных (SQLite Database)

Все накопленные знания, факты, наблюдения телеметрии и полнотекстовый поисковый индекс WikiLLM сохраняются в локальной базе данных SQLite.

### 📍 Расположение базы данных

- **Путь по умолчанию:** `data/windows_wikillm/knowledge.db` (относительно корневой директории проекта).
- При первом запуске или инициализации директория `data/windows_wikillm/` создаётся автоматически.

### ⚙️ Конфигурация пути к базе данных

Путь к файлу базы данных настраивается несколькими способами:

1. **Через файл конфигурации:** `apps/windows/wikillm/config.json`
   ```json
   {
     "database_path": "data/windows_wikillm/knowledge.db",
     "min_confidence_threshold": 0.70,
     "max_queue_size": 1000,
     "async_workers": 2,
     "gemini_model_id": "gemini-3.5-flash-lite",
     "enable_code_indexer": true,
     "enable_semantic_search": true,
     "cache_exact_hits": true
   }
   ```

2. **Программно через Pydantic-модель:**
   ```python
   from apps.windows.wikillm.config import WikiLLMConfig
   from apps.windows.wikillm.engine import WikiEngine

   config = WikiLLMConfig(database_path="data/windows_wikillm/knowledge.db")
   engine = WikiEngine(config=config)
   ```

3. **Напрямую в хранилище `WikiStorage`:**
   ```python
   from apps.windows.wikillm.storage import WikiStorage

   # Использование файла на диске
   storage = WikiStorage(db_path="data/windows_wikillm/knowledge.db")

   # In-memory база данных (для тестов)
   mem_storage = WikiStorage(db_path=":memory:")
   ```

### 🗄️ Структура таблиц SQLite

| Таблица | Описание |
|---|---|
| `entities` | Основной реестр нормализованных сущностей (первичный ключ: `canonical_key`, тип, имя, резюме, категория, важность, статус подтверждения). |
| `claims` | Атомарные проверенные утверждения, факты и выводы о сущностях (`claim_type`, `statement`, `confidence`). |
| `evidence` | Доказательная база, симптомы, контекст и пошаговые инструкции по исправлению проблем (`action_type`, `instruction`). |
| `observations` | Локальная телеметрия и статистика встречаемости артефакта на машине (`total_occurrences`, `first_seen`, `last_seen`). |
| `co_occurrences` | Матрица совместных событий для выявления корреляций между артефактами. |
| `relations` | Направленный граф связей между сущностями базы знаний (`source_key`, `target_key`, `relation_type`). |
| `entities_fts` | Виртуальная таблица полнотекстового поиска SQLite FTS5 (поля `canonical_key`, `name`, `summary`, `tags`). |

