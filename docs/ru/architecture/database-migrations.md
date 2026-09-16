# Миграции баз данных и версионирование схемы

В данном документе описывается архитектура системы управления схемами баз данных SQLite, механизм версионирования, создание автоматических резервных копий и интеграция процесса миграций в общий цикл обновления системы AI-Breadboard.

---

## 1. Концепция и назначение

В проекте AI-Breadboard для хранения структурированных данных (пользователи, настройки, токены, логи аудита, роли и права) используется встраиваемая СУБД SQLite (например, `src/user_manager/users.db`). 

При развитии проекта, добавлении новых полей или изменении структуры таблиц требуется надежный механизм, который:
1. **Автоматически отслеживает примененные миграции** в каждой базе данных.
2. **Выполняет миграции в транзакциях**, предотвращая частичные обновления при сбоях.
3. **Создает резервную копию** базы перед началом наката изменений и автоматически восстанавливает исходное состояние при ошибке.
4. **Поддерживает как SQL, так и Python-скрипты** для сложных трансформаций данных.
5. **Автоматически запускается при каждом обновлении приложения** (через `run.ps1`, `Run-Unicorn.ps1` или `version_manager.py`).

---

## 2. Архитектура компонентов

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Точки входа и триггеры                         │
├───────────────────┬─────────────────────────┬───────────────────────────┤
│ run.ps1 (git pull)│ Run-Unicorn.ps1 (start) │ version_manager.py (auto) │
│                   │                         │ manage_tools.py db        │
└─────────┬─────────┴────────────┬────────────┴─────────────┬─────────────┘
          │                      │                          │
          ▼                      ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Менеджер миграций: src.db.MigrationManager                 │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Сканирование migrations/<db_name>/ (*.sql, *.py)                     │
│ 2. Проверка _schema_migrations в целевой БД                             │
│ 3. Создание pre-migration бэкапа (.db.backup_<timestamp>)                │
│ 4. Выполнение транзакции (SQL executescript или module.upgrade(conn))   │
│ 5. Фиксация версии и контрольной суммы (SHA256) в _schema_migrations    │
│ 6. При ошибке: откат транзакции + восстановление из бэкапа              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │ Целевая база данных (SQLite)    │
                    │ src/user_manager/users.db       │
                    └─────────────────────────────────┘
```

### 2.1 Таблица учета версий (`_schema_migrations`)
В каждой управляемой базе данных создается служебная таблица:

```sql
CREATE TABLE IF NOT EXISTS _schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TEXT DEFAULT (datetime('now'))
);
```

### 2.2 Структура каталога миграций
Файлы миграций располагаются в корневом каталоге `migrations/` с разделением по базам данных:

```text
migrations/
  └── users/
      ├── 0001_initial_users_schema.sql
      └── 0002_add_user_preferences.sql
```

---

## 3. Формат файлов миграций

### 3.1 SQL-миграции (`.sql`)
Используются для DDL (создание таблиц, изменение колонок, создание индексов) и базового наполнения DML. Выполняются через `conn.executescript()` в рамках транзакции.

Пример `migrations/users/0001_initial_users_schema.sql`:
```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'user'
);
```

### 3.2 Python-миграции (`.py`)
Используются в случаях, когда требуется сложная программная обработка, миграция форматов данных или вызов вспомогательных функций. Скрипт обязан экспортировать функцию `upgrade(conn: sqlite3.Connection) -> bool`.

Пример `migrations/users/0002_transform_data.py`:
```python
# -*- coding: utf-8 -*-
import sqlite3

def upgrade(conn: sqlite3.Connection) -> bool:
    """Трансформация данных пользователей."""
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET name = UPPER(name) WHERE name IS NOT NULL")
    return True
```

---

## 4. Механизм отказоустойчивости и резервного копирования

Перед применением пакета ожидающих миграций `MigrationManager`:
1. Создает точную копию файла базы данных:
   `users.db.backup_YYYYMMDD_HHMMSS_ffffff` в том же каталоге.
2. Последовательно применяет новые миграции внутри единого блока `BEGIN TRANSACTION ... COMMIT`.
3. В случае любого исключения (синтаксическая ошибка SQL, ошибка валидации, сбой скрипта Python):
   - Выполняется `conn.rollback()`.
   - Файл базы данных перезаписывается из созданного бэкапа (`restore_backup`).
   - Ошибка логируется через `src.logger.logger`.

---

## 5. Интеграция в процесс обновления и запуска системы

| Компонент / Скрипт | Место вызова | Поведение |
|---|---|---|
| **`run.ps1`** | Этап 1.5 (после `git pull`) | При обнаружении новой версии в Git и успешном pull автоматически вызывается `python -m src.db.migrations --apply`. |
| **`launchers/Run-Unicorn.ps1`** | Перед стартом сервера FastAPI | Выполняется быстрая проверка и накат ожидающих миграций для гарантии актуальности схемы. |
| **`src/version_manager.py`** | Метод `update_application()` | В программном конвейере обновления после слияния веток запускается `apply_all_pending()`. |
| **`manage_tools.py db`** | Консольный интерфейс | Предоставляет операторам команды управления и инспекции. |

---

## 6. Консольные команды (`manage_tools.py db`)

### Проверка статуса миграций:
```bash
py manage_tools.py db status
```
Вывод:
```text
--- DATABASE MIGRATION STATUS ---
[users] Up-to-date: True | Applied: 1 | Pending: 0
---------------------------------
```

### Применение ожидающих миграций:
```bash
py manage_tools.py db migrate
```

### Генерация шаблона новой миграции:
```bash
# SQL миграция
py manage_tools.py db create users add_avatar_column

# Python миграция
py manage_tools.py db create users recalculate_stats --py
```
Команда автоматически определяет следующий порядковый номер (например, `0002_add_avatar_column.sql`) и создает заготовку файла.

---

## 7. Программный API (`src.db`)

```python
from src.db import get_migration_manager

# Получение синглтона менеджера
manager = get_migration_manager()

# Применение всех ожидающих миграций для всех БД
results = manager.apply_all_pending()
print(results)
# {'success': True, 'applied_total': 1, 'databases': {'users': {'success': True, 'applied_count': 1, 'message': '...'}}}

# Проверка статуса
status = manager.get_status()
```
