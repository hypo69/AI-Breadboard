# apps/windows/api/webgui

Каталог веб-интерфейса (WebGUI) сценария Test Computer (TC).

## Назначение

Содержит статические файлы (HTML, JS, CSS) всех вкладок интерфейса AI Breadboard,
а также Python-роутер дашборд-панелей, читающий данные из `telemetry.db`.

## Структура

```
apps/windows/api/webgui/
├── router_dashboard.py          # FastAPI-роутер дашбордов (источник: telemetry.db)
├── hardware_monitor_tab/        # Вкладка мониторинга оборудования
│   ├── index.html
│   └── main.js                  # fetch → /api/windows/dashboard/snapshot & sensors
├── telemetry_history_tab/       # Вкладка истории телеметрии
│   ├── index.html               # Селектор источника: telemetry.db / CSV-файлы
│   └── main.js                  # fetch → /api/windows/dashboard/history (режим DB)
├── telemetry_research_tab/      # Вкладка исследования телеметрии
├── process_leaks_tab/           # Вкладка утечек процессов
├── admin/                       # Панель администратора
├── ...                          # Остальные вкладки UI
└── README.md                    # Этот файл
```

## API дашбордов (router_dashboard.py)

Все эндпоинты работают **исключительно с `telemetry.db`** через синглтон `TelemetryStorage`.

| Метод | Путь | Таблица DB | Описание |
|---|---|---|---|
| GET | `/api/windows/dashboard/snapshot` | `system_snapshots` (latest) | Последний снепшот CPU/RAM/GPU |
| GET | `/api/windows/dashboard/sensors` | `sensor_polls` (latest per sensor) | Актуальные значения датчиков |
| GET | `/api/windows/dashboard/processes` | `process_snapshots` (latest) | Топ процессов из последнего снепшота |
| GET | `/api/windows/dashboard/history` | `system_snapshots` (N records) | История снепшотов |
| GET | `/api/windows/dashboard/sensor-history` | `sensor_polls` | История показаний датчика |
| GET | `/api/windows/dashboard/events` | `telemetry_events` | События телеметрии |
| GET | `/api/windows/dashboard/process-stats` | `process_rollups_2min` + outliers | Агрегированная статистика |

### Параметры запросов

```
GET /api/windows/dashboard/history?limit=60&since=<unix_epoch>
GET /api/windows/dashboard/sensor-history?sensor_id=<id>&category=Temperatures&limit=100
GET /api/windows/dashboard/processes?limit=50&sort_by=cpu
GET /api/windows/dashboard/events?event_type=<type>&limit=100
GET /api/windows/dashboard/process-stats?name=<substring>&limit=50
```

## Схема базы данных telemetry.db

БД расположена в: `%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs\telemetry.db`

Ключевые таблицы:
- **`system_snapshots`** — снепшоты системы (CPU, RAM, GPU, дисковый I/O, сеть)
- **`sensor_polls`** — показания аппаратных датчиков (LHM, OpenHardwareMonitor)
- **`process_snapshots`** — топ процессов в каждом снепшоте
- **`telemetry_events`** — аномалии и события
- **`process_rollups_2min`** — 2-минутные агрегаты процессов
- **`process_outliers`** — аномальные пики процессов

## Запуск

```powershell
.\\Run-TC.ps1
# Открыть: https://localhost:8000/tc
```

## Зависимости

- `apps.windows.telemetry.sqlite.TelemetryStorage` — синглтон хранилища
- `apps.windows.telemetry.collector` — служба сбора данных (Run-Telemetry.ps1)
- FastAPI, uvicorn — HTTP-сервер

## Стандарты

- Все docstrings и комментарии на **русском языке** (PEP 8, hypo69 docblock)
- Нет live-запросов к железу из дашборд-роутера — только чтение из DB
- Логирование через `logger` (без `print`)
