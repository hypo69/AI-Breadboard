# Корреляционная телеметрия

## Обзор

Система корреляционной телеметрии отслеживает **изменения метрик системы** при событиях (запуск программ, файловые операции), фиксирует **дельты** по ключевым параметрам и персистентно сохраняет всю историю в **базу данных SQLite** (`telemetry.db`).

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    События                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Запуск программы │  │ Запись файла │  │ Удаление файла │      │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘      │
│          │                   │                   │              │
│          └───────────────────┴───────────────────┘              │
│                              │                                  │
│                    ┌─────────▼─────────┐                       │
│                    │ TelemetryDelta    │                       │
│                    │   Calculator      │                       │
│                    └─────────┬─────────┘                       │
│                              │                                  │
│                    ┌─────────▼─────────┐                       │
│                    │  EventCorrelation │                       │
│                    │   (с дельтами)    │                       │
│                    └─────────┬─────────┘                       │
│                              │                                  │
│                    ┌─────────▼─────────┐                       │
│                    │  TelemetryStorage │                       │
│                    │  (SQLite база)    │                       │
│                    └───────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Метрики, которые отслеживаются

| Метрика | Описание | Ед. изм | Порог значимости |
|---------|----------|---------|------------------|
| `cpu_delta_percent` | Изменение загрузки CPU | % | 5% |
| `ram_delta_percent` | Изменение использования RAM | % | 2% |
| `disk_io_delta_read` | Дельта чтения диска | B/s | 1 MB/s |
| `disk_io_delta_write` | Дельта записи диска | B/s | 1 MB/s |
| `network_delta_recv` | Дельта сетевого трафика (получено) | B/s | 1 MB/s |
| `network_delta_sent` | Дельта сетевого трафика (отправлено) | B/s | 1 MB/s |
| `process_count_delta` | Изменение количества процессов | count | 5 |
| `top_process_cpu` | Изменение загрузки топ-процесса | % | 10% |
| `top_process_memory_mb` | Изменение RAM топ-процесса | MB | 50 MB |

## База данных SQLite (`telemetry.db`)

Данные сохраняются в `%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs\telemetry.db`:

- `system_snapshots` — системные срезы CPU, RAM, GPU, дисков, сети и аптайма.
- `process_snapshots` — снимки активных процессов (Top-N) с привязкой к snapshot_id.
- `sensor_polls` — замеры сенсоров (температуры, вольтажи, кулеры, частоты, пинг).
- `telemetry_events` — события системы, изменения оборудования и аномалии.
- `hardware_audits` — архивные снимки аудита железа и драйверов.

## Использование

### Запись события в базу данных

```python
from apps.windows.telemetry.service import TelemetryLoggerService

# Получаем сервис
service = TelemetryLoggerService.get_instance()

# Записываем событие запуска программы (сохраняется в SQLite)
event_id = service.record_event(
    event_type="process_start",
    event_details={
        "process_name": "chrome.exe",
        "executable_path": "C:\\Program Files\\Chrome\\chrome.exe",
        "command_line": "--new-window",
        "user": "DOMAIN\\username",
        "pid": 12345,
    },
    severity="info",
)

print(f"Событие сохранено в SQLite с ID: {event_id}")
```

### Запрос данных через `TelemetryStorage`

```python
from apps.windows.telemetry.storage import TelemetryStorage

storage = TelemetryStorage.get_instance()

# 1. Получение последних 50 срезов системы
snapshots = storage.get_snapshots(limit=50)

# 2. Получение процессов конкретного снимка
if snapshots:
    processes = storage.get_snapshot_processes(snapshots[0]["id"])
    print(f"Процессов в снимке: {len(processes)}")

# 3. История поведения конкретного процесса
proc_history = storage.get_process_history(name="chrome", limit=100)

# 4. События телеметрии
events = storage.get_events(limit=50)

# 5. Статистика хранилища
stats = storage.get_storage_stats()
print(f"Статистика БД: {stats}")
```

### Миграция данных из CSV/JSON в SQLite

Если на диске присутствуют исторические CSV или JSON логи:

```python
from apps.windows.telemetry.storage import TelemetryStorage

storage = TelemetryStorage.get_instance()
migration_results = storage.migrate_csv_to_db()
print(f"Результат миграции: {migration_results}")
```

## Производительность

- **Хранилище**: SQLite с режимом WAL (`Write-Ahead Logging`) и индексами.
- **Оптимизация**: Пакетные транзакции `executemany` и каскадные внешние ключи.
- **Очистка**: Метод `cleanup_old_records(retention_days=7)` для автоматической ротации.
