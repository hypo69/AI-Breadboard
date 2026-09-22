# Платформа корпоративных знаний

`apps/enterprise_knowledge` — локальное ядро накопительной корпоративной базы знаний. Оно сохраняет исходные события, разрешает идентичность сотрудников по email и алиасам, хранит факты с источниками и временными границами и выполняет гибридный поиск по фактам и FTS5.

## Архитектура

```
ai-breadboard/apps/enterprise_knowledge/
│
├── connectors/          # Коннекторы источников данных
│   ├── base.py         # Базовый интерфейс коннекторов
│   ├── outlook/        # Outlook (email, календарь, контакты)
│   ├── teams/          # Microsoft Teams (сообщения, звонки)
│   ├── gmail/          # Gmail
│   ├── filesystem/     # Файловая система
│   ├── crm/            # CRM системы
│   └── audio/          # Аудиозаписи (транскрипция, диаризация)
│
├── ingestion/          # Обработка входящих данных
│   ├── events/         # Обработка событий
│   ├── normalization/  # Нормализация данных
│   ├── deduplication/  # Дедупликация
│   └── processing/     # Обработка
│
├── identity/           # Управление идентичностью
│   ├── registry.py     # Регистр идентичности
│   ├── resolution.py   # Разрешение идентификаторов
│   ├── aliases.py      # Управление алиасами
│   └── verification.py # Верификация идентичности
│
├── knowledge/          # Обработка знаний
│   ├── extraction.py   # Извлечение фактов
│   ├── facts.py        # Управление фактами
│   ├── relationships.py # Связи между сущностями
│   ├── consolidation.py # Консолидация знаний
│   └── temporal.py     # Временная история
│
├── retrieval/          # Поиск и извлечение
│   ├── structured.py   # Структурированный поиск
│   ├── fulltext.py     # Полнотекстовый поиск
│   ├── vector.py       # Векторный поиск
│   ├── graph.py        # Графовый поиск
│   └── hybrid.py       # Гибридный поиск
│
├── workers/            # Рабочие процессы
│   ├── ingestion_worker.py    # Ингестия данных
│   ├── extraction_worker.py   # Извлечение фактов
│   ├── resolution_worker.py   # Разрешение идентичности
│   └── consolidation_worker.py # Консолидация знаний
│
├── engine.py           # Основной движок
├── storage.py          # SQLite хранилище
├── router.py           # FastAPI API
├── config.json         # Конфигурация
└── README.md           # Документация
```

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

## Возможности

### Identity Resolution
* Регистрация сотрудников с алиасами (email, имена, employee_id)
* Автоматическое разрешение идентификаторов
* Управление алиасами с уровнем доверия
* Верификация идентичности

### Knowledge Ingestion
* Поддержка множества источников (Outlook, Teams, Gmail, CRM, файлы, аудио)
* Нормализация данных в унифицированный формат
* Дедупликация событий
* Извлечение фактов из текстов

### Knowledge Storage
* Хранение исходных событий
* Факты с временной историей (valid_from, valid_to)
* Связи между сущностями
* Доказательства и источники

### Hybrid Retrieval
* Структурированный поиск (employee_id, даты, должности)
* Полнотекстовый поиск (FTS5)
* Векторный поиск (embeddings)
* Графовый поиск (связи между сотрудниками)
* Гибридный поиск (объединение стратегий)

### Workers
* IngestionWorker — ингестия данных из коннекторов
* ExtractionWorker — извлечение фактов из текстов
* ResolutionWorker — разрешение идентичности
* ConsolidationWorker — консолидация знаний и проверка противоречий

## Безопасность

* Контроль доступа на уровне сотрудников
* Аудит всех запросов
* Поддержка OAuth2 и JWT
* Шифрование чувствительных данных

## Интеграция с другими компонентами

* RAG — использование фактов для генерации ответов
* AI Models — извлечение фактов с помощью LLM
* Plugins — интеграция с другими модулями AI-Breadboard
