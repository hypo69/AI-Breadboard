# Платформа корпоративных знаний

`apps/enterprise_knowledge` — локальное ядро накопительной корпоративной базы знаний. Оно сохраняет исходные события, разрешает идентичность сотрудников по email и алиасам, хранит факты с источниками и временными границами и выполняет гибридный поиск по фактам и FTS5.

## Запуск

Роутер подключается к общему FastAPI-серверу автоматически:

```powershell
python main.py
```

Для отдельной проверки:

```powershell
python -m apps.enterprise_knowledge "API"
```

Путь базы задается переменной `ENTERPRISE_KNOWLEDGE_DB`; по умолчанию используется `data/enterprise_knowledge/knowledge.db`.

## API

* `POST /api/v1/enterprise-knowledge/employees` — зарегистрировать сотрудника и алиасы.
* `GET /api/v1/enterprise-knowledge/employees/{employee_id}` — профиль и история фактов.
* `POST /api/v1/enterprise-knowledge/ingest` — идемпотентно принять унифицированное событие.
* `POST /api/v1/enterprise-knowledge/query` — поиск по фактам и исходным текстам.
* `GET /api/v1/enterprise-knowledge/health` — проверка доступности.

Факты получают статус `proposed`, `confirmed`, `rejected` или `superseded`. Исходный текст не заменяется производным фактом и хранится отдельно.