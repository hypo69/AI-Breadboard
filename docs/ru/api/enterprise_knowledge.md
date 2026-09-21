# API Enterprise Knowledge Platform

Базовый префикс: `/api/v1/enterprise-knowledge`.

## Проверка состояния

### `GET /health`

```json
{"status": "ok"}
```

## Сотрудники

### `POST /employees`

Регистрирует сотрудника и его идентификаторы.

```json
{
  "employee_id": "EMP-0042",
  "name": "Александр Петров",
  "department": "Engineering",
  "email": "a.petrov@company.com",
  "aliases": ["Alex"],
  "verified": true,
  "confidence": 1.0
}
```

### `GET /employees/{employee_id}`

Возвращает профиль сотрудника и связанные факты. Если сотрудник не найден, возвращается `404`.

## Ingestion

### `POST /ingest`

Принимает унифицированное событие:

```json
{
  "event_id": "EVT-10001",
  "source": {"type": "email", "external_id": "EMAIL-1001"},
  "event_type": "message_received",
  "occurred_at": "2026-09-21T10:30:00Z",
  "content": {"text": "Проверь API до пятницы."},
  "facts": [
    {
      "subject": "a.petrov@company.com",
      "predicate": "assigned_task",
      "object": "Проверка API",
      "status": "proposed",
      "valid_from": "2026-09-21"
    }
  ]
}
```

Повторная обработка того же `event_id` возвращает `status: "duplicate"` и не создаёт новые записи.

## Hybrid query

### `POST /query`

```json
{
  "query": "API",
  "employee_id": "EMP-0042",
  "status": "proposed",
  "limit": 20
}
```

Результат содержит два массива: `facts` со структурированными фактами и `sources` с исходными текстами, найденными через SQLite FTS5. Пустые `employee_id` и `status` отключают соответствующие фильтры.