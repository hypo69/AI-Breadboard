# Модуль сбора системной телеметрии и сенсоров (`apps/windows/telemetry`)

Автономная легковесная служба сбора системных метрик, аппаратных сенсоров, мониторинга процессов и файловых событий, непрерывного сохранения в **базу данных SQLite (`telemetry.db`)** и потокового JSON-логирования для **AI-Breadboard**.

Служба выполняется в системе как выделенный процесс **`ai-telemetry.exe`**, оптимизирована под минимальное потребление ресурсов (Zero-cost ML, < 0.5% CPU в фоновом режиме, приоритет `BelowNormal`) и поддерживает автоматический запуск через **Windows Task Scheduler** с пробуждением ПК при спящем режиме (`WakeToRun`).

---

## 📋 Содержание

1. [Архитектура и ключевые особенности](#-архитектура-и-ключевые-особенности)
2. [Режимы работы: Minimal, Hybrid, Full](#-режимы-работы-minimal-hybrid-full)
3. [Что мониторит служба](#-что-мониторит-служба)
4. [Хранилище данных SQLite (`telemetry.db`)](#-хранилище-данных-sqlite-telemetrydb)
5. [Управление процессом через `Run-Telemetry.ps1`](#-управление-процессом-через-run-telemetryps1)
6. [Автозапуск в Windows Task Scheduler (`WakeToRun`)](#-автозапуск-в-windows-task-scheduler-waketorun)
7. [Интеграция в Run-TC.ps1](#-интеграция-в-run-tcps1)
8. [Веб-интерфейс и REST API](#-веб-интерфейс-и-rest-api)
9. [Конфигурация (`config.json`)](#-конфигурация-configjson)
10. [Миграция из CSV в SQLite](#-миграция-из-csv-в-sqlite)

---

## 🌟 Архитектура и ключевые особенности

- **Собственное имя процесса в системе (`ai-telemetry.exe`)**:
  В окружении `venv/Scripts/ai-telemetry.exe` создается выделенный бинарник. Процесс отображается в Диспетчере задач Windows и командлетах PowerShell именно как `ai-telemetry`, что позволяет легко отслеживать его PID, CPU и Working Set RAM.
- **Zero-Cost ML Stack**:
  Исключены нетерпеливые импорты PyTorch, Transformers, HuggingFace и FastAPI. Базовое потребление оперативной памяти снижено более чем в 2 раза (до ~105–120 МБ).
- **Сверхбыстрый сбор без блокировки ядра**:
  Опрос активных процессов оптимизирован (выборка быстрых атрибутов `['pid', 'name', 'memory_info', 'username']` без сканирования системных потоков ядра `Toolhelp32Snapshot`). Время замера составляет **28–76 мс** (в 170 раз быстрее исходного), нагрузка на процессор < 0.5%.
- **Приоритет `BelowNormal`**:
  Служба автоматически переводит себя в класс приоритета `BELOW_NORMAL_PRIORITY_CLASS`, гарантируя максимальную отзывчивость пользовательских приложений.
- **WMI-запуск без привязки к терминалу**:
  Фоновый старт осуществляется через `Win32_Process.Create`, отвязывая процесс от Job Object и пайпов родительской консоли PowerShell. Закрытие терминала не прерывает работу службы.

---

## ⚙️ Режимы работы: Minimal, Hybrid, Full

Служба поддерживает три режима сбора метрик:

| Режим | Описание | Опрос базовых метрик | Опрос тяжелых сенсоров |
| :--- | :--- | :--- | :--- |
| **`minimal`** | Ультралегковесный фоновый мониторинг | Каждые 5 сек (CPU, RAM, GPU, диски, сеть, топ процессов) | Отключен (минимальное потребление памяти и CPU) |
| **`hybrid`** *(рекомендуемый по умолчанию)* | Адаптивный комбинированный сбор | Каждые 5 сек (быстрый цикл ~28 мс) | Каждые 60 сек (LHM, SMART дисков, Ping сети) |
| **`full`** | Максимальный глубокий аудит | Каждые 5 сек (все метрики) | Каждую итерацию (все сенсоры и инвентарь оборудования) |

Режим можно задать в `config.json` (`"mode": "hybrid"`) или через флаг командной строки `--mode hybrid`.

---

## 🔍 Что мониторит служба

| Подсистема / Датчик | Собираемые метрики | Описание параметров |
| :--- | :--- | :--- |
| **Процессор (CPU)** | `load`, `clock`, `cores` | Общая загрузка (%), тактовая частота (MHz), число потоков и логических ядер. |
| **Оперативная память (RAM)** | `load`, `data`, `swap` | Физическая память (used/available в GB, load %), файл подкачки (swap %). |
| **Видеокарта (GPU)** | `load`, `temperature`, `memory` | Загрузка GPU (%), температура ядра (°C), использование видеопамяти (VRAM). |
| **Хранилище (Disks)** | `load`, `io`, `smart` | Занятое пространство разделов (%), скорость чтения/записи (B/s), SMART-здоровье дисков. |
| **Сеть (Network)** | `throughput`, `ping` | Скорость отправки и приема (байт/с), сетевая задержка (Ping ms). |
| **Процессы (Processes)** | `top_processes` | Top-N наиболее прожорливых процессов (PID, имя, RAM MB, % CPU, статус, пользователь). |
| **Аппаратные сенсоры LHM** | `voltages`, `temperatures`, `fans` | Напряжения линий питания, температуры датчиков платы, обороты кулеров (RPM). |

---

## 🗄️ Хранилище данных SQLite (`telemetry.db`)

Все телеметрические данные сохраняются в базу данных SQLite по пути:  
`%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs\telemetry.db`

Таблицы:
1. **`system_snapshots`** — системные срезы (CPU, RAM, GPU, диск, сеть, uptime).
2. **`process_snapshots`** — Top-N процессов в момент каждого среза.
3. **`sensor_polls`** — периодические замеры отдельных сенсоров LHM и SMART.
4. **`telemetry_events`** — системные события и обнаруженные аномалии.
5. **`hardware_audits`** — архивы аудита конфигурации оборудования.
6. **`app_polls`, `app_events`, `app_param_changes`** — аудит модулей и приложений.

Также поддерживается потоковый JSON-лог `%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs\ai_sensors_polls.json` с автоматической ротацией по достижении **50 МБ**.

---

## 🚀 Управление процессом через `Run-Telemetry.ps1`

Основной скрипт управления: [`launchers/Run-Telemetry.ps1`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/launchers/Run-Telemetry.ps1)

```powershell
# Запуск службы в фоновом режиме (по умолчанию режим hybrid)
.\launchers\Run-Telemetry.ps1

# Проверка текущего статуса службы (PID, имя ai-telemetry, RAM, Task Scheduler)
.\launchers\Run-Telemetry.ps1 -Action status

# Остановка службы телеметрии
.\launchers\Run-Telemetry.ps1 -Action stop

# Перезапуск службы
.\launchers\Run-Telemetry.ps1 -Action restart

# Запуск в ультралегковесном режиме minimal с быстрым интервалом 3 секунды
.\launchers\Run-Telemetry.ps1 -Mode minimal -Interval 3.0

# Запуск в интерактивном режиме в текущем окне консоли (для отладки)
.\launchers\Run-Telemetry.ps1 -Foreground
```

---

## ⏰ Автозапуск в Windows Task Scheduler (`WakeToRun`)

Для автономной круглосуточной работы службы даже при перезагрузке системы и спящем режиме используется скрипт [`launchers/Install-TelemetryTask.ps1`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/launchers/Install-TelemetryTask.ps1).

```powershell
# Регистрация задания в планировщике с поддержкой пробуждения (WakeToRun)
.\launchers\Run-Telemetry.ps1 -Action install-task

# Проверка статуса задания в планировщике
.\launchers\Run-Telemetry.ps1 -Action status-task

# Удаление задания из планировщика
.\launchers\Run-Telemetry.ps1 -Action uninstall-task
```

**Особенности задания в Планировщике Windows:**
- **`WakeToRun = $true`**: Система пробуждается для выполнения фонового мониторинга.
- **`AllowStartIfOnBatteries = $true`**: Работа продолжается при питании ноутбука от батареи.
- **`ExecutionTimeLimit = 0`**: Задание работает непрерывно без таймаутов завершения.
- **`Priority = 6` (`BelowNormal`)**: Минимальное влияние на производительность.
- **`RestartCount = 3`**: Автоматический перезапуск в случае непредвиденного сбоя.

---

## 🔗 Интеграция в Run-TC.ps1

Главный сценарий запуска платформы [`Run-TC.ps1`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/Run-TC.ps1) автоматически проверяет активность службы `ai-telemetry`. Если служба не обнаружена среди запущенных процессов, сценарий вызывает тихий фоновый запуск `Run-Telemetry.ps1` до инициализации LibreHardwareMonitor и веб-сервера.

---

## 🌐 Веб-интерфейс и REST API

Управление службой доступно прямо из браузера в панели администратора:
- **Раздел**: `Телеметрия и логи` -> подвкладка **«Служба телеметрии (ai-telemetry)»** ([`autolog_tab`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/api/webgui/autolog_tab/index.html)).
- **Функционал UI**:
  - Карточка статуса (PID, потребление памяти в МБ, число накопленных снимков, статус в Task Scheduler).
  - Кнопки быстрого управления: «Запустить», «Остановить», «Перезапустить», «Установить в Task Scheduler», «Удалить из Task Scheduler».
  - Форма конфигурации: выбор режима (Minimal / Hybrid / Full), задание интервалов быстрого и тяжелого опроса, включение/выключение тяжелых сенсоров с сохранением в `config.json`.
- **REST API эндпоинты** ([`src/api/router_autolog.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/src/api/router_autolog.py)):
  - `GET /api/autolog/telemetry/status` — текущий статус процесса, RAM, PID, Task Scheduler.
  - `POST /api/autolog/telemetry/control` — отправка команд (`start`, `stop`, `restart`, `install-task`, `uninstall-task`).
  - `GET /api/autolog/telemetry/config` — получение конфигурации телеметрии.
  - `POST /api/autolog/telemetry/config` — сохранение обновленных настроек.

---

## ⚙️ Конфигурация (`config.json`)

Файл расположен по пути: [`apps/windows/telemetry/config.json`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows/telemetry/config.json).

```json
{
  "mode": "hybrid",
  "interval_seconds": 5.0,
  "heavy_interval_seconds": 60.0,
  "top_processes": 10,
  "low_priority": true,
  "max_file_size_mb": 50,
  "watch_directories": [
    "C:\\Users\\"
  ],
  "log_filename": "ai_sensors_polls.json",
  "collect_serial_numbers": true,
  "collect_hardware_inventory": false,
  "collect_file_events": false,
  "heavy_collectors": {
    "hardware_sensors": true,
    "storage_smart": true,
    "network_ping": true,
    "inventory_wmi": false
  },
  "sensors": {
    "cpu": { "enabled": true, "interval_seconds": 5.0 },
    "gpu": { "enabled": true, "interval_seconds": 10.0 },
    "ram": { "enabled": true, "interval_seconds": 10.0 },
    "disk": { "enabled": true, "interval_seconds": 30.0 },
    "network": { "enabled": true, "interval_seconds": 10.0 },
    "sensors": { "enabled": true, "interval_seconds": 10.0 },
    "internet": { "enabled": true, "interval_seconds": 120.0 }
  }
}
```

---

## 🔄 Миграция из CSV в SQLite

Для переноса исторических данных из CSV-логов в базу данных SQLite:

```python
from apps.windows.telemetry.storage import TelemetryStorage

storage = TelemetryStorage.get_instance()
results = storage.migrate_csv_to_db()
print(f"Импортировано записей: {results}")
```
