# Корреляционная телеметрия

## Обзор

Система корреляционной телеметрии отслеживает **изменения метрик системы** при событиях (запуск программ, файловые операции) и сохраняет **дельты** (разницы) по всем параметрам.

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
│                    │   TelemetryLogger │                       │
│                    │  (CSV файлы)      │                       │
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

## Файлы CSV

Данные сохраняются в `%LOCALAPPDATA%\AI-Breadboard\telemetry_csv\`:

- `telemetry_YYYYMMDD.csv` — ежедневные снапшоты с колонками:
  - `timestamp`, `hostname`, `cpu_percent`, `memory_percent`, `gpu_load`, `disk_io_read`, `disk_io_write`, `network_recv`, `network_sent`

## Использование

### Запись события

```python
from apps.windows.telemetry.service import TelemetryLoggerService

# Получаем сервис
service = TelemetryLoggerService.get_instance()

# Записываем событие запуска программы
correlation = service.record_event(
    event_type="process_start",
    event_details={
        "process_name": "chrome.exe",
        "executable_path": "C:\\Program Files\\Chrome\\chrome.exe",
        "command_line": "--new-window",
        "user": "DOMAIN\\username",
        "pid": 12345,
    },
)

# Проверяем результат (событие логируется, но не сохраняется в базу)
print(f"Событие: {correlation.event_id}")
print(f"Серьезность: {correlation.severity}")
print(f"Измененных метрик: {correlation.affected_metrics_count}")

for delta in correlation.deltas:
    if delta.is_significant:
        print(f"{delta.metric_name}: {delta.before_value} → {delta.after_value} ({delta.delta:+.2f}%)")
```

### Запись файловой активности

```python
from apps.windows.core.modules.file_activity_collector import FileActivityCollector

collector = FileActivityCollector(monitored_paths=["C:\\Users\\%USERNAME%\\Documents"])
result = collector.collect()

# Автоматически создаются корреляции для каждого события
```

### Запрос данных

Данные теперь хранятся в CSV-файлах. Для чтения используйте:

```python
import pandas as pd
from pathlib import Path

# Читаем последний CSV файл
telemetry_dir = Path("%LOCALAPPDATA%") / "AI-Breadboard" / "telemetry_csv"
latest_csv = sorted(telemetry_dir.glob("telemetry_*.csv"))[-1]
df = pd.read_csv(latest_csv)

print(df.head())
print(f"Всего записей: {len(df)}")
```

## Примеры использования

### 1. Найти программ, которая вызвала высокую нагрузку на CPU

```python
import pandas as pd
from pathlib import Path

# Читаем все CSV файлы
telemetry_dir = Path("%LOCALAPPDATA%") / "AI-Breadboard" / "telemetry_csv"
all_data = pd.concat([pd.read_csv(f) for f in telemetry_dir.glob("telemetry_*.csv")])

# Фильтруем высокую нагрузку на CPU (> 80%)
high_cpu = all_data[all_data["cpu_percent"] > 80]

print(f"Высокая нагрузка CPU: {len(high_cpu)} записей")
print(high_cpu[["timestamp", "hostname", "cpu_percent"]])
```

### 2. Найти файловые операции с высоким I/O

```python
import pandas as pd
from pathlib import Path

telemetry_dir = Path("%LOCALAPPDATA%") / "AI-Breadboard" / "telemetry_csv"
all_data = pd.concat([pd.read_csv(f) for f in telemetry_dir.glob("telemetry_*.csv")])

# Фильтруем высокую запись диска (> 10 MB/s)
high_write = all_data[all_data["disk_io_write"] > 10 * 1024 * 1024]

print(f"Высокая запись диска: {len(high_write)} записей")
print(high_write[["timestamp", "disk_io_write"]])
```

### 3. Построить график изменения метрик

```python
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

telemetry_dir = Path("%LOCALAPPDATA%") / "AI-Breadboard" / "telemetry_csv"
latest_csv = sorted(telemetry_dir.glob("telemetry_*.csv"))[-1]
df = pd.read_csv(latest_csv)

# Строим график загрузки CPU и RAM
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp")[["cpu_percent", "memory_percent"]].plot(figsize=(12, 6))
plt.title("Изменение загрузки CPU и RAM")
plt.ylabel("%")
plt.show()
```

## Интеграция с существующими компонентами

### ProcessCollector
Автоматически записывает корреляции при сборе информации о процессах.

### FileActivityCollector
Автоматически записывает корреляции при обнаружении файловых операций.

### RootCauseEngine
Может использовать корреляции для анализа причин системных проблем.

## Настройка

### Пороги значимости

Можно изменить в `telemetry_delta.py`:

```python
SIGNIFICANCE_THRESHOLDS = {
    "cpu_percent": 5.0,      # Изменение CPU > 5% считается значимым
    "memory_percent": 2.0,   # Изменение RAM > 2% считается значимым
    "disk_io_read_bps": 1024 * 1024,  # 1 MB/s
    "disk_io_write_bps": 1024 * 1024,  # 1 MB/s
    # ...
}
```

### Интервал сбора

В `service.py`:

```python
service = TelemetryLoggerService(interval_sec=1.0)  # Сбор каждую секунду
```

## Производительность

- **Хранилище**: CSV-файлы (простой текстовый формат)
- **Оптимизация**: Дельты сохраняются только при значимых изменениях
- **Чтение**: Pandas для быстрого анализа больших объёмов данных
