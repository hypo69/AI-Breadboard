# Платформа корпоративных знаний

`Enterprise Knowledge Platform` — отдельное приложение для накопления знаний о сотрудниках, проектах и рабочих событиях. Приложение сохраняет исходные события, связывает упоминания с сотрудниками, формирует структурированные факты и выполняет поиск по фактам и исходному тексту.

## Возможности текущей версии

- локальное SQLite-хранилище без внешней базы данных;
- реестр сотрудников, email и алиасов;
- разрешение идентичности по точному email или алиасу;
- идемпотентный приём унифицированных ingestion-событий;
- хранение исходного текста отдельно от производных фактов;
- факты со статусом, источником и временными границами;
- полнотекстовый поиск SQLite FTS5;
- фильтрация результатов по сотруднику и статусу факта.

Внешние коннекторы Outlook, Teams, Gmail, CRM и аудиотранскрипции пока не подключены. Такие данные можно передавать через унифицированный API ingestion.

## Запуск

Приложение подключается к общему FastAPI-серверу:

```powershell
python main.py
```

Проверка доступности:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/enterprise-knowledge/health
```

Для консольного поиска по локальной базе:

```powershell
python -m apps.enterprise_knowledge "API"
```

По умолчанию база создаётся в `data/enterprise_knowledge/knowledge.db`. Другой путь задаётся переменной окружения `ENTERPRISE_KNOWLEDGE_DB`.

## Рабочий сценарий

### 1. Зарегистрировать сотрудника

```powershell
$employee = @{
  employee_id = "EMP-0042"
  name = "Александр Петров"
  department = "Engineering"
  email = "a.petrov@company.com"
  aliases = @("Alex", "Саша")
  verified = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/enterprise-knowledge/employees `
  -ContentType "application/json" -Body $employee
```

### 2. Передать событие

Событие содержит внешний источник, исходный текст и извлечённые факты. Поле `subject` может быть email или алиасом сотрудника.

```powershell
$event = @{
  event_id = "EVT-10001"
  source = @{ type = "email"; external_id = "EMAIL-1001" }
  occurred_at = "2026-09-21T10:30:00Z"
  content = @{ text = "Проверь API до пятницы." }
  facts = @(@{
    subject = "a.petrov@company.com"
    predicate = "assigned_task"
    object = "Проверка API"
    status = "proposed"
  })
} | ConvertTo-Json -Depth 8

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/enterprise-knowledge/ingest `
  -ContentType "application/json" -Body $event
```

Повторная отправка того же `event_id` не создаёт дубликаты и возвращает статус `duplicate`.

### 3. Получить профиль и выполнить поиск

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/enterprise-knowledge/employees/EMP-0042

$query = @{ query = "API"; employee_id = "EMP-0042"; limit = 20 } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/enterprise-knowledge/query `
  -ContentType "application/json" -Body $query
```

Результат поиска разделён на `facts` и `sources`, чтобы вместе с утверждением показывать исходный материал.

## Статусы фактов

| Статус | Назначение |
|---|---|
| `proposed` | Факт предложен автоматической обработкой или ingestion-событием. |
| `confirmed` | Факт подтверждён человеком или доверенным источником. |
| `rejected` | Факт признан ошибочным. |
| `superseded` | Факт заменён более актуальной записью. |

Старые факты не удаляются при добавлении новых сведений.

## Хранение данных

- `ingestion_events` — принятые унифицированные события;
- `sources` — исходные тексты и метаданные;
- `employees` и `employee_aliases` — реестр идентичности;
- `facts` — структурированные утверждения;
- `source_fts` — полнотекстовый индекс исходных материалов.

Для резервного копирования достаточно остановить приложение и скопировать файл SQLite.