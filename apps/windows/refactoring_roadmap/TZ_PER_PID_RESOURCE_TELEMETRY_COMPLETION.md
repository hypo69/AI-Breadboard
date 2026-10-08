# Техническое задание: Доработка и завершение подсистемы попроцессного мониторинга ресурсов и активности по PID (Per-PID Telemetry Engine)

## 1. Назначение и цель доработок

Настоящее техническое задание определяет порядок проведения финальных работ по доведению подсистемы попроцессного сбора телеметрии и мониторинга ресурсов (**Per-PID Resource & Activity Telemetry Engine**) до **100% функциональной готовности** в соответствии с базовой спецификацией `TZ_PER_PID_RESOURCE_TELEMETRY.md`.

### 1.1 Текущий статус и объем недостающего функционала
На текущий момент платформа **AI-Breadboard** обладает реализованной базой на уровне ~80–85%:
* Работает сборщик процессов `ProcessCollector` и дискового I/O `DiskProcessIOCollector`.
* Реализован C-FFI модуль `nethelper.py` над `iphlpapi.dll` (`GetExtendedTcpTable`/`GetExtendedUdpTable`) для привязки сокетов к PID.
* Реализован считыватель Sysmon/Security логов в `wevtapi.py` и базовые таблицы сетевых снимков в `sqlite.py`.

**Необходимый объем доработок (15–20%) включает**:
1. **Единая консолидация базы данных**: Объединение разрозненных метрик процессов в единую таблицу снимков `process_pid_snapshots`.
2. **Мониторинг контролируемых директорий по PID**: Внедрение движка `DirectoryWatchEngine` на базе `ReadDirectoryChangesW` и ETW `Microsoft-Windows-Kernel-File` с записью в `process_file_events`.
3. **Строгие REST API контракты в FastAPI**: Реализация узкоспециализированных эндпоинтов получения текущего профиля PID, истории файловой активности и управления списками отслеживаемых папок.

---

## 2. Этап 1. Консолидация базы данных и схема `process_pid_snapshots`

### 2.1 Объединение разрозненных таблиц
В `apps/windows/telemetry/sqlite.py` создается единая каноническая таблица `process_pid_snapshots`, заменяющая фрагментарные таблицы `process_snapshots` и `process_leak_items`.

```sql
-- Единая таблица снимков ресурсов и активности процессов по PID
CREATE TABLE IF NOT EXISTS process_pid_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    executable_path TEXT,
    
    -- Процессор (CPU)
    cpu_percent REAL NOT NULL DEFAULT 0.0,
    user_time_ms INTEGER NOT NULL DEFAULT 0,
    kernel_time_ms INTEGER NOT NULL DEFAULT 0,
    thread_count INTEGER NOT NULL DEFAULT 1,
    
    -- Память (RAM)
    working_set_bytes INTEGER NOT NULL DEFAULT 0,
    private_bytes INTEGER NOT NULL DEFAULT 0,
    page_faults_count INTEGER DEFAULT 0,
    
    -- Графика (GPU)
    gpu_vram_bytes INTEGER DEFAULT 0,
    gpu_utilization REAL DEFAULT 0.0,
    
    -- Дисковый I/O
    read_bytes_total INTEGER DEFAULT 0,
    write_bytes_total INTEGER DEFAULT 0,
    read_ops_total INTEGER DEFAULT 0,
    write_ops_total INTEGER DEFAULT 0,
    
    -- Сетевой трафик
    net_bytes_sent_total INTEGER DEFAULT 0,
    net_bytes_recv_total INTEGER DEFAULT 0,
    
    -- Системные дескрипторы и GUI-ресурсы
    handle_count INTEGER DEFAULT 0,
    gdi_objects INTEGER DEFAULT 0,
    user_objects INTEGER DEFAULT 0,
    
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Индексы для обеспечения времени отклика REST API < 5 мс
CREATE INDEX IF NOT EXISTS idx_proc_pid_time ON process_pid_snapshots(pid, timestamp);
CREATE INDEX IF NOT EXISTS idx_proc_name_time ON process_pid_snapshots(process_name, timestamp);
```

### 2.2 Доработка `ProcessCollector`
Класс `ProcessCollector` расширяется за счет прямого снятия показателей `user_time_ms` / `kernel_time_ms` через `GetProcessTimes`, `gdi_objects` / `user_objects` через `GetGuiResources` (`user32.dll`) и объема VRAM через счетчик PDH `GPU Engine`.

---

## 3. Этап 2. Движок отслеживания файлов в целевых директориях (`DirectoryWatchEngine`)

### 3.1 Архитектура `DirectoryWatchEngine`
Создается новый модуль `apps/windows/telemetry/directory_watcher.py`, совмещающий:
1. **Службу Win32 `ReadDirectoryChangesW`**: Обеспечивает мгновенный перехват файловых операций в зарегистрированных директориях.
2. **Провайдер ETW `Microsoft-Windows-Kernel-File`**: Обеспечивает извлечение `OriginatingProcessId` (PID) для каждого зафиксированного файла.

### 3.2 Схема таблицы `process_file_events`
```sql
CREATE TABLE IF NOT EXISTS process_file_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    action_type TEXT NOT NULL, -- 'CREATE', 'MODIFY', 'DELETE', 'RENAME'
    target_directory TEXT NOT NULL,
    file_path TEXT NOT NULL,
    bytes_affected INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_file_events_pid ON process_file_events(pid);
CREATE INDEX IF NOT EXISTS idx_file_events_dir ON process_file_events(target_directory, timestamp);
```

---

## 4. Этап 3. Реализация REST API контрактов FastAPI

В `apps/windows/api/routers/router_telemetry.py` добавлена регистрация трех обязательных REST-маршрутов с гарантированным временем ответа `< 5 мс` прямо из SQLite.

### 4.1 Эндпоинт метрик ресурсоемкости по PID
* **Маршрут**: `GET /api/v1/telemetry/processes/{pid}`
* **Pydantic Модель Ответа**:
```python
class CpuDetail(BaseModel):
    percent: float
    user_time_ms: int
    kernel_time_ms: int
    thread_count: int

class MemoryDetail(BaseModel):
    working_set_mb: float
    private_bytes_mb: float
    page_faults: int

class GpuDetail(BaseModel):
    vram_dedicated_mb: float
    utilization_percent: float

class IoDetail(BaseModel):
    read_bytes_sec: int
    write_bytes_sec: int
    handles_count: int

class NetworkDetail(BaseModel):
    bytes_sent_sec: int
    bytes_recv_sec: int
    active_sockets: int

class ProcessTelemetryResponse(BaseModel):
    pid: int
    process_name: str
    executable_path: Optional[str]
    cpu: CpuDetail
    memory: MemoryDetail
    gpu: GpuDetail
    io: IoDetail
    network: NetworkDetail
    timestamp: str
```

### 4.2 Эндпоинт истории файловых операций PID
* **Маршрут**: `GET /api/v1/telemetry/processes/{pid}/file-activity`
* **Параметры**: `directory: Optional[str] = None`, `limit: int = 50`
* **Возвращает**: Массив записей из таблицы `process_file_events` для указанного PID.

### 4.3 Эндпоинт управления отслеживаемыми директориями
* **Маршрут**: `POST /api/v1/telemetry/tracked-directories`
* **Тело запроса**:
```json
{
  "action": "add",
  "directory_path": "C:\\Data\\Projects"
}
```
* **Функционал**: Обновляет конфигурацию `DirectoryWatchEngine` и сохраняет список путей в `config.json`.

---

## 5. Этап 4. Буферизация, WAL-пакетирование и политика усечения (Retention)

1. **In-Memory Ring Buffer**: Сбор метрик процессом-коллектором происходит раз в 1 секунду с сохранением во внутреннем кольцевом буфере памяти на 60 отсчетов.
2. **Пакетный сброс (Batch WAL Writer)**: Накопленные снимки `process_pid_snapshots` сбрасываются в `telemetry.db` раз в 5 секунд единой транзакцией (`BEGIN TRANSACTION ... COMMIT`).
3. **Автоматическая ротация**:
   * Посекундные детализированные записи в `process_pid_snapshots` хранятся **24 часа**.
   * Фоновый сервис `TelemetryCompactor` раз в сутки переносит агрегаты в таблицы роллапов (`process_rollups_daily`) и удаляет устаревшие сырые записи.

---

## 6. Регламент приемки и критерии успешности

1. **Full Metric Verification**: При запуске тестового процесса (например, `code.exe` или `ffmpeg.exe`) таблица `process_pid_snapshots` фиксирует корректные значения CPU %, RAM, GPU VRAM, I/O и GUI-объектов.
2. **Directory Watch Validation**: Создание, изменение или удаление файла в отслеживаемой папке генерирует точную запись в `process_file_events` с корректным PID инициировавшего процесса.
3. **Latency Target**: Время отклика REST API `GET /api/v1/telemetry/processes/{pid}` не превышает **5 мс**.
