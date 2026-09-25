# Общие модули приложений (`apps/common`)

Пакет `apps/common` предоставляет базовые службы для всех приложений и подсистем AI-Breadboard:
1. **Унифицированная телеметрия и логирование (`csv_logger.py`)**: высокопроизводительная запись событий, замеров и параметров в единую базу данных SQLite с возможностью выгрузки CSV по требованию (On-Demand).
2. **Движок фонового автологирования (`autolog_engine.py`)**: периодический опрос метрик приложений с адаптивными интервалами и поддержкой REST API.
3. **Автообнаружение приложений и сервисов (`discovery.py`)**: сканирование структуры проекта и манифестов `manifest.json`.

---

## 🗄️ Архитектура логирования (`csv_logger.py`)

### 1. SQLite как Single Source of Truth
Все телеметрические данные приложений сохраняются напрямую в единую базу данных SQLite:
`%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs\telemetry.db`

Таблицы приложений:
- **`app_polls`** — регулярные замеры датчиков и метрик приложений (`app`, `poll_type`, `metric_name`, `value`, `unit`, `tags`, `timestamp`).
- **`app_events`** — события жизненного цикла и статусы (`app`, `event_type`, `status`, `details`, `duration_ms`, `metadata`, `timestamp`).
- **`app_param_changes`** — аудит изменений конфигурации (`app`, `param_name`, `old_value`, `new_value`, `changed_by`, `timestamp`).
- **`custom_records`** — произвольные табличные записи (`app`, `log_name`, `row_data_json`, `timestamp`).

### 2. Зеркалирование в CSV (`enable_mirroring_logs_to_csv`)
По умолчанию постоянная запись на диск в файлы `.csv` **отключена** для устранения дискового оверхеда при высокой частоте опросов:
- Управление: `set_mirroring_logs_to_csv(True / False)`
- Проверка: `is_mirroring_logs_to_csv_enabled() -> bool`
- Переменная окружения: `AI_BREADBOARD_ENABLE_MIRRORING_LOGS_TO_CSV=true`

### 3. Выгрузка CSV по требованию (On-Demand)
CSV-файлы генерируются на лету из SQLite только тогда, когда это явно запрошено:

```python
from apps.common.csv_logger import (
    AppCsvLogger,
    export_app_events_to_csv,
    export_app_polls_to_csv,
    export_to_csv,
)

# Выгрузка через функции модуля
exported_files = export_to_csv(app="system_inspector")

# Выгрузка через объект логгера
logger = AppCsvLogger("cloudflared_monitor")
files = logger.export_csv(target_type="all")
```

### 4. Опциональная пакетная буферизация в памяти
Для высоконагруженных сценариев предусмотрена пакетная буферизация замеров:
- Управление: `set_memory_batching(True / False)`
- Сброс буфера: `flush_batch_buffer()`
- Переменная окружения: `AI_BREADBOARD_ENABLE_MEMORY_BATCHING=true`

---

## ⚙️ Движок автологирования (`autolog_engine.py`)

Управляет периодическим опросом зарегистрированных логгеров приложений:
- `AutoLogEngine`: синглтон-движок с поддержкой асинхронного фонового цикла опроса.
- Поддерживаемые модули: `system_inspector`, `network_analyzer`, `cloudflared_monitor`, `nginx_monitor`, `storage_tool`, `trading_terminal` и др.
- REST API маршруты доступны через `src/api/router_autolog.py` (`/api/autolog/*`).

---

## 🔍 Обнаружение приложений (`discovery.py`)

Осуществляет поиск и регистрацию приложений из каталога `/apps`:
- Чтение `manifest.json` и метаданных.
- Формирование динамического реестра доступных модулей.
