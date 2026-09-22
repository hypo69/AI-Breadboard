# AI Windows 64-bit Collector (ai_w64_collector)

## Обзор

**ai_w64_collector** - это максимальный сборщик событий Windows, который логгирует **ВСЕ** изменения в системе без анализа. Данные собираются для последующего анализа другими агентами.

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│              AI Windows 64-bit Collector                    │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Main Collector │  │   ETW Collector │                  │
│  │  (ai_w64_col)   │  │  (ai_w64_etw)   │                  │
│  └────────┬────────┘  └────────┬────────┘                  │
│           │                    │                            │
│  ┌────────▼────────┐  ┌────────▼────────┐                  │
│  │   Processes     │  │   Processes     │                  │
│  │   Files         │  │   Registry      │                  │
│  │   Registry      │  │   Network       │                  │
│  │   Network       │  │   ETW Events    │                  │
│  │   Events        │  └─────────────────┘                  │
│  └────────┬────────┘                                        │
│           │                                                  │
│  ┌────────▼────────┐                                        │
│  │   Log Files     │                                        │
│  │   (JSONL)       │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

## Файлы

| Файл | Описание |
|------|----------|
| `ai_w64_collector.py` | Основной сборщик событий |
| `ai_w64_etw_collector.py` | ETW трассировка (низкоуровневые события) |
| `ai_w64_collector_launcher.py` | Запуск и управление |
| `ai_w64_collector_config.json` | Конфигурация |

## Установка

```powershell
# Установка зависимостей
pip install psutil

# Проверка установки
python -c "import psutil; print('psutil installed')"
```

## Использование

### 1. Программное использование

```python
from apps.windows.ai_w64_collector import AIW64Collector

# Создаем сборщик
collector = AIW64Collector(
    log_dir="C:\\AI-Breadboard\\logs",
    monitored_paths=[
        r"C:\Users\%USERNAME%\Documents",
        r"C:\Program Files",
    ],
    enable_file_monitoring=True,
    enable_process_monitoring=True,
    enable_registry_monitoring=True,
    enable_network_monitoring=True,
)

# Запускаем
collector.start()

# Работаем...
time.sleep(60)

# Останавливаем
collector.stop()

# Получаем статус
status = collector.get_status()
print(json.dumps(status, indent=2))

# Получаем события
events = collector.get_events(limit=100)
for event in events:
    print(f"{event['event_type']}: {event.get('path', event.get('name', 'N/A'))}")
```

### 2. Через CLI

```powershell
# Запуск
python ai_w64_collector_launcher.py --start

# Статус
python ai_w64_collector_launcher.py --status

# Остановка
python ai_w64_collector_launcher.py --stop

# Показать события
python ai_w64_collector_launcher.py --events

# Показать события определенного типа
python ai_w64_collector_launcher.py --events --event-type process_start

# Показать последние 50 событий
python ai_w64_collector_launcher.py --events --limit 50
```

### 3. Глобальный экземпляр

```python
from apps.windows.ai_w64_collector import start_w64_collector, stop_w64_collector

# Запуск
collector = start_w64_collector()

# Остановка
stop_w64_collector()
```

## События, которые собираются

### Основной сборщик (ai_w64_collector)

| Тип события | Описание | Данные |
|-------------|----------|--------|
| `process_start` | Запуск нового процесса | pid, name, exe, cmdline, username, cpu_percent, memory_mb |
| `process_terminate` | Завершение процесса | pid, name, exe, cpu_percent, memory_mb |
| `process_cpu_change` | Изменение загрузки CPU процесса | pid, name, cpu_before, cpu_after, cpu_delta |
| `process_memory_change` | Изменение RAM процесса | pid, name, memory_before, memory_after, memory_delta_mb |
| `network_connection_new` | Новое сетевое соединение | local_address, remote_address, status, pid, type |
| `network_connection_closed` | Закрытое сетевое соединение | local_address, remote_address, status, pid, type |
| `registry_value_created` | Создано значение в реестре | key, name, value |
| `registry_value_modified` | Изменено значение в реестре | key, name, old_value, new_value |
| `registry_value_deleted` | Удалено значение из реестра | key, name |
| `file_created` | Создан новый файл | path, hash |
| `file_modified` | Изменен файл | path, old_hash, new_hash |
| `file_deleted` | Удален файл | path, hash |

### ETW сборщик (ai_w64_etw_collector)

| Тип события | Описание | Данные |
|-------------|----------|--------|
| `etw_process_create` | Создание процесса (Event 4688) | Данные из Security Event Log |
| `etw_file_access` | Доступ к файлу (Event 4663) | Данные из Security Event Log |
| `etw_network_connection` | Сетевое соединение | LocalAddress, LocalPort, RemoteAddress, RemotePort |
| `etw_registry_access` | Доступ к реестру | Данные из ProcessAuditManager |

## Конфигурация

Файл `ai_w64_collector_config.json`:

```json
{
  "log_dir": null,
  "monitored_paths": [
    "C:\\Users\\%USERNAME%\\Documents",
    "C:\\Users\\%USERNAME%\\Downloads",
    "C:\\Users\\%USERNAME%\\Desktop",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\Windows\\System32",
    "C:\\Windows\\SysWOW64"
  ],
  "enable_file_monitoring": true,
  "enable_process_monitoring": true,
  "enable_registry_monitoring": true,
  "enable_network_monitoring": true,
  "enable_event_log_monitoring": true,
  "enable_process_trace": true,
  "enable_disk_trace": true,
  "enable_network_trace": true,
  "enable_registry_trace": true
}
```

## Логи

Логи сохраняются в формате JSONL (JSON Lines) по одному событию на строку:

```
{"event_id": "evt_1726956789_1", "timestamp": "2026-09-21T22:13:09.123456+00:00", "event_type": "process_start", "pid": 12345, "name": "chrome.exe", "exe": "C:\\Program Files\\Chrome\\chrome.exe", "cmdline": "--new-window", "username": "DOMAIN\\user", "cpu_percent": 5.2, "memory_mb": 125.5}
{"event_id": "evt_1726956790_2", "timestamp": "2026-09-21T22:13:10.234567+00:00", "event_type": "file_created", "path": "C:\\Users\\user\\Documents\\test.txt", "hash": "d41d8cd98f00b204e9800998ecf8427e"}
```

## Структура логов

```
%LOCALAPPDATA%\AI-Breadboard\
├── ai_w64_logs\
│   ├── process_start_2026-09-21.jsonl
│   ├── process_terminate_2026-09-21.jsonl
│   ├── file_created_2026-09-21.jsonl
│   ├── file_modified_2026-09-21.jsonl
│   ├── file_deleted_2026-09-21.jsonl
│   ├── network_connection_new_2026-09-21.jsonl
│   ├── network_connection_closed_2026-09-21.jsonl
│   ├── registry_value_created_2026-09-21.jsonl
│   ├── registry_value_modified_2026-09-21.jsonl
│   └── registry_value_deleted_2026-09-21.jsonl
└── ai_w64_etw_logs\
    ├── etw_process_create_2026-09-21.jsonl
    ├── etw_file_access_2026-09-21.jsonl
    ├── etw_network_connection_2026-09-21.jsonl
    └── etw_registry_access_2026-09-21.jsonl
```

## Примеры использования

### 1. Найти все запуски Python

```python
from apps.windows.ai_w64_collector import AIW64Collector

collector = AIW64Collector()
collector.start()

# ... работа системы ...

events = collector.get_events_by_type("process_start")
python_events = [e for e in events if "python" in e.get("exe", "").lower()]

for event in python_events:
    print(f"Python запущен: {event['exe']} {event['cmdline']}")
```

### 2. Найти файлы, которые были изменены

```python
events = collector.get_events_by_type("file_modified")
for event in events:
    print(f"Файл изменен: {event['path']}")
    print(f"  Старый хэш: {event['old_hash']}")
    print(f"  Новый хэш: {event['new_hash']}")
```

### 3. Найти сетевые соединения

```python
events = collector.get_events_by_type("network_connection_new")
for event in events:
    print(f"Соединение: {event['local_address']} -> {event['remote_address']}")
    print(f"  PID: {event['pid']}")
    print(f"  Тип: {event['type']}")
```

### 4. Мониторинг в реальном времени

```python
import time
from apps.windows.ai_w64_collector import AIW64Collector

collector = AIW64Collector()
collector.start()

print("Мониторинг событий (Ctrl+C для остановки)...")

try:
    while True:
        events = collector.get_events(limit=10)
        for event in events:
            print(f"[{event['timestamp']}] {event['event_type']}: {event.get('name', event.get('path', 'N/A'))}")
        time.sleep(1)
except KeyboardInterrupt:
    collector.stop()
```

## Производительность

- **Основной сборщик**: Проверка каждую секунду
- **ETW сборщик**: Проверка каждые 5 секунд
- **Логирование**: JSONL формат для быстрой записи
- **Память**: Минимальное использование (только baseline)

## Ограничения

1. **Windows только** - не работает на Linux/macOS
2. **Права администратора** - для ETW трассировки требуются права администратора
3. **Производительность** - при большом количестве событий может замедлить систему
4. **Размер логов** - логи быстро растут (GB в день на активной системе)

## Оптимизация

### Уменьшить объем логов

```python
collector = AIW64Collector(
    enable_file_monitoring=False,  # Отключить мониторинг файлов
    enable_registry_monitoring=False,  # Отключить мониторинг реестра
    monitored_paths=["C:\\Users\\%USERNAME%\\Documents"],  # Только одну папку
)
```

### Уменьшить частоту проверки

```python
# В коде основного сборщика измените check_interval
check_interval = 5.0  # Проверка каждые 5 секунд вместо 1
```

## Устранение неполадок

### Сборщик не запускается

```python
# Проверьте, что psutil установлен
pip install psutil

# Проверьте права доступа к логам
# Запустите от имени администратора
```

### Нет событий в логах

```python
# Проверьте конфигурацию
collector = AIW64Collector(
    enable_process_monitoring=True,
    enable_file_monitoring=True,
    # ...
)

# Проверьте логи
print(collector.get_status())
```

### ETW трассировка не работает

```powershell
# Проверьте, что Event Tracing для Windows включен
wevtutil el | Select-String "Microsoft-Windows"

# Запустите от имени администратора
```

## Интеграция с другими компонентами

### С телеметрией

```python
from apps.windows.ai_w64_collector import AIW64Collector
from apps.windows.telemetry.service import TelemetryLoggerService

# Запускаем оба сборщика
w64_collector = AIW64Collector()
w64_collector.start()

telemetry_service = TelemetryLoggerService.get_instance()
telemetry_service.start()

# Данные собираются независимо
```

### С ProcessAuditManager

```python
from apps.windows.ai_w64_collector import AIW64Collector
from apps.windows.core.process_audit_manager import ProcessAuditManager

# AIW64Collector собирает события
w64_collector = AIW64Collector()
w64_collector.start()

# ProcessAuditManager читает из логов
manager = ProcessAuditManager()
history = manager.get_process_execution_history()
```

## Безопасность

- **Логи содержат чувствительные данные** - пути файлов, команды процессов, сетевые соединения
- **Храните логи в безопасном месте**
- **Ограничьте доступ к логам**
- **Регулярно очищайте старые логи**

## Лицензия

MIT © 2026 hypo69
