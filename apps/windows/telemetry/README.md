# Модуль сбора системной телеметрии и сенсоров (`apps/windows/telemetry`)

Автономная подсистема сбора системных метрик, аппаратных сенсоров, мониторинга файловых событий, непрерывного сохранения в **базу данных SQLite (`telemetry.db`)** и потокового логирования телеметрии для **AI-Breadboard**.

---

## 📋 Содержание

1. [Обзор возможностей](#-обзор-возможностей)
2. [Что мониторит система](#-что-мониторит-система)
3. [Хранилище данных SQLite (`telemetry.db`)](#-хранилище-данных-sqlite-telemetrydb)
4. [Как запускается (Управление)](#-как-запускается-управление)
5. [Как настроить конфигурацию](#-как-настроить-конфигурацию)
6. [Формат данных и ротация файлов](#-формат-данных-и-ротация-файлов)
7. [Миграция из CSV в SQLite](#-миграция-из-csv-в-sqlite)

---

## 🌟 Обзор возможностей

- **Постоянное хранение в SQLite (`telemetry.db`)**: надежное сохранение системных срезов, процессов, аппаратных замеров и событий с поддержкой WAL-режима и каскадных внешних ключей.
- **Полная автономность**: служба может функционировать независимо от основного API-сервера AI-Breadboard, внешней СУБД или UI.
- **Структурированный формат замеров**: группировка метрик по устройствам и типам с массивом замеров `samples` (включая ядра `core` и потоки `thread` процессора).
- **Zero-Dependency & Fail-Safe**: потоковая запись с автоматической ротацией логов по достижении лимита **50 МБ** и автоматическая очистка устаревших записей в БД.
- **Каждый замер с ISO Timestamp**: точная привязка каждого измерения во времени.

---

## 🔍 Что мониторит система

| Подсистема / Датчик | Собираемые метрики | Описание параметров |
| :--- | :--- | :--- |
| **Процессор (CPU)** | `load`, `clock` | Общая загрузка (`total`), загрузка каждого ядра (`core`) и потока (`thread`), тактовая частота в `MHz`. |
| **Оперативная память (RAM)** | `load`, `data` | Использование физической памяти (`ram`) и файла подкачки (`swap`) в `%`, объемы `used` и `available` в `GB`. |
| **Видеокарта (GPU)** | `load`, `temperature`, `power` | Загрузка графического ядра и памяти (%), температура кристалла (°C), потребляемая мощность (W), скорость кулера (%). |
| **Хранилище (Disks)** | `load`, `throughput`, `smart` | Занятое пространство по разделам (C:, D:, ... в %), скорость чтения/записи (B/s), SMART-здоровье физических дисков. |
| **Сеть (Network)** | `throughput` | Скорость отправки (`sent`) и приема (`recv`) трафика в байтах/сек. |
| **Интернет (Internet)** | `latency`, `bandwidth` | Сетевая задержка (Ping ms, DNS ms), скорость загрузки (Download Mbps) и отдачи (Upload Mbps). |
| **Сенсоры LHM (Hardware)** | `voltages`, `temperatures`, `fans`, `powers` | Напряжения линий питания (V), температуры материнской платы, обороты вентиляторов (RPM), энергопотребление. |
| **Файловая система (DirectoryWatcher)** | `file_events` | Создание, изменение, перемещение и удаление файлов в отслеживаемых каталогах в реальном времени. |

---

## 🗄️ Хранилище данных SQLite (`telemetry.db`)

Все телеметрические данные сохраняются в базу данных SQLite по пути:  
`%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs\telemetry.db`

### Схема таблиц:

1. **`system_snapshots`** — ежесекундные/периодические системные срезы:
   - `id`, `timestamp`, `created_at`, `hostname`, `uptime_seconds`
   - `cpu_total_percent`, `cpu_frequency_mhz`
   - `memory_total_gb`, `memory_used_gb`, `memory_percent`, `swap_percent`
   - `gpu_load_percent`, `gpu_temp_c`
   - `disk_read_bytes_sec`, `disk_write_bytes_sec`, `disk_read_count_sec`, `disk_write_count_sec`
   - `network_sent_bytes_sec`, `network_recv_bytes_sec`, `raw_json`

2. **`process_snapshots`** — Top-N активных процессов в момент снимка:
   - `id`, `snapshot_id`, `timestamp`, `pid`, `name`, `status`, `cpu_percent`, `memory_mb`, `memory_percent`, `num_threads`, `username`, `read_bytes_sec`, `write_bytes_sec`

3. **`sensor_polls`** — замеры отдельных сенсоров:
   - `id`, `sensor_id`, `timestamp`, `created_at`, `hardware_name`, `hardware_type`, `sensor_category`, `sensor_name`, `unit`, `value`, `raw_json`

4. **`telemetry_events`** — события системы и аномалии:
   - `id`, `timestamp`, `created_at`, `event_type`, `severity`, `event_details`, `raw_json`

5. **`hardware_audits`** — архивы аудита конфигурации оборудования:
   - `id`, `archive_id`, `timestamp`, `created_at`, `devices_count`, `problem_devices_count`, `outdated_drivers_count`, `changes_count`, `raw_json`

---

## 🚀 Как запускается (Управление)

### 1. Запуск через PowerShell-лаунчер (Основной способ)

Скрипт расположен в папке `launchers/Run-AI-Sensors.ps1`:

```powershell
# Запуск сервиса телеметрии в фоновом режиме
.\launchers\Run-AI-Sensors.ps1

# Перезапуск с нуля (завершает старые процессы и запускает заново)
.\launchers\Run-AI-Sensors.ps1 -Restart

# Проверка текущего статуса и PID работающих процессов
.\launchers\Run-AI-Sensors.ps1 -Action status

# Остановка сервиса
.\launchers\Run-AI-Sensors.ps1 -Action stop

# Запуск с переопределением интервала опроса (например, 30 секунд)
.\launchers\Run-AI-Sensors.ps1 -Interval 30.0
```

### 2. Прямой запуск через Python CLI

```powershell
# Запуск с базовым интервалом из конфигурации
python apps/windows/telemetry/main.py

# Запуск с кастомным интервалом и подробным выводом (DEBUG)
python apps/windows/telemetry/main.py --interval 10 --verbose

# Указание кастомного файла конфигурации и директории логов
python apps/windows/telemetry/main.py --config path/to/config.json --log-dir path/to/logs
```

---

## ⚙️ Как настроить конфигурацию

Конфигурационный файл расположен по пути:  
`apps/windows/telemetry/config.json` (или `apps/windows/config.json`).

### Пример настроек `config.json`:

```json
{
  "interval_seconds": 5.0,
  "max_file_size_mb": 50,
  "watch_directories": [
    "C:\\Users\\"
  ],
  "log_filename": "ai_sensors_polls.json",
  "collect_serial_numbers": true,
  "collect_hardware_inventory": true,
  "collect_file_events": true,
  "sensors": {
    "cpu": {
      "enabled": true,
      "interval_seconds": 5.0,
      "metrics": ["temperature", "load", "clocks"]
    },
    "gpu": {
      "enabled": true,
      "interval_seconds": 10.0,
      "metrics": ["temperature", "load", "memory", "power"]
    },
    "ram": {
      "enabled": true,
      "interval_seconds": 10.0,
      "metrics": ["usage", "swap"]
    },
    "disk": {
      "enabled": true,
      "interval_seconds": 30.0,
      "metrics": ["usage", "io"]
    },
    "network": {
      "enabled": true,
      "interval_seconds": 10.0,
      "metrics": ["throughput"]
    },
    "sensors": {
      "enabled": true,
      "interval_seconds": 10.0,
      "metrics": ["voltage", "fans", "power"]
    },
    "internet": {
      "enabled": true,
      "interval_seconds": 120.0,
      "metrics": ["ping", "speed"]
    }
  }
}
```

---

## 📦 Формат данных и ротация файлов

### Структура записи в `ai_sensors_polls.json`:

```json
[
  {
    "id": 38,
    "hardware_name": "Intel Core i5-10400",
    "hardware_type": "cpu",
    "sensor_category": "Temperatures",
    "sensor_name": "CPU Core #4 Distance to TjMax",
    "unit": "°C",
    "values": [
      {"num": 56.0, "time": "2026-09-24T15:21:21+03:00"},
      {"num": 56.0, "time": "2026-09-24T15:21:26+03:00"}
    ]
  }
]
```

### Правило ротации файлов (50 МБ):
- Когда текущий файл `ai_sensors_polls.json` достигает размера **50 МБ**, он автоматически переименовывается с суффиксом текущей временной метки (`ai_sensors_polls_YYYYMMDD_HHMMSS.json`).
- Для текущих записей немедленно открывается новый чистый файл `ai_sensors_polls.json`.

---

## 🔄 Миграция из CSV в SQLite

Для переноса старых файлов `.csv` в новую базу данных SQLite используется метод `migrate_csv_to_db()`:

```python
from apps.windows.telemetry.storage import TelemetryStorage

storage = TelemetryStorage.get_instance()
results = storage.migrate_csv_to_db()
print(f"Импортировано: {results}")
```
