# Схема базы данных и жизненный цикл сообщений DLQ

## Схема таблицы SQLite `dlq_messages`

| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Уникальный автоинкрементный идентификатор записи |
| `source` | TEXT NOT NULL | Модуль или ИИ-агент, где произошел сбой (например, `gemini-cli`, `search-rag`) |
| `error_message` | TEXT NOT NULL | Описание ошибки или полный Traceback исключения |
| `payload` | TEXT NOT NULL | JSON-строка с контекстом задачи, параметрами запроса и переменными |
| `retry_count` | INTEGER DEFAULT 0 | Количество предпринятых попыток повторного выполнения |
| `created_at` | TIMESTAMP | Дата и время создания записи (CURRENT_TIMESTAMP) |
| `updated_at` | TIMESTAMP | Дата и время последнего изменения статуса |
| `status` | TEXT DEFAULT 'PENDING' | Статус жизненного цикла (`PENDING`, `RETRYING`, `RESOLVED`, `FAILED`) |

## Индексы
- `idx_dlq_status`: Индекс по полю `status` для ускорения выборки нерешенных задач.
- `idx_dlq_source`: Индекс по полю `source` для фильтрации по источнику.
