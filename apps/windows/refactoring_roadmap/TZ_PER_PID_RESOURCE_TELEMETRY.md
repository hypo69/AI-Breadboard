# Техническое задание: Подсистема попроцессного сбора телеметрии и мониторинга ресурсов по PID

## 1. Назначение и архитектурные принципы

Настоящее техническое задание определяет архитектуру и порядок реализации подсистемы сквозного попроцессного мониторинга ресурсов и активности (**Per-PID Resource & Activity Telemetry Engine**) в рамках платформы «Интеллектуальный центр тонких настроек операционной системы и телеметрии параметров ОС».

### Ключевые архитектурные принципы

* **PID-Centric Lifecycle Tracking**: Каждому запущенному в системе исполняемому процессу после присвоения идентификатора PID назначается изолированный контекст наблюдения. Отслеживание начинается с момента получения события `ProcessStart` и продолжается до `ProcessStop`.
* **Zero-Impact ETW & Native FFI Layer**: Для минимизации накладных расходов сбор файловых, сетевых и процессорно-памятных метрик переводится с поллинга Win32/psutil на события ядра Windows (**ETW Kernel Providers**) и нативные C-FFI вызовы к системным DLL (`iphlpapi.dll`, `pdh.dll`, `kernel32.dll`).
* **Data-First from SQLite**: Все накопленные показатели по PID агрегируются во временном кольцевом буфере в RAM и сбрасываются пакетными WAL-транзакциями в базу данных `telemetry.db`. Чтение информации веб-интерфейсом происходит исключительно из базы данных со временем отклика менее 5 мс.

---

## 2. Спецификация отслеживаемых метрик по PID

Подсистема фиксирует полный спектр ресурсов и операций, инициируемых конкретным процессом.

### 2.1 Процессор и системные потоки (CPU)
* **Процент загрузки ЦП (`cpu_percent`)**: Доля процессорного времени, утилизируемая всеми потоками процесса относительно всех ядер CPU.
* **Kernel & User Time**: Раздельный учет времени, проведенного процессом в режиме ядра (`KernelModeTime`) и в режиме пользователя (`UserModeTime`).
* **Количество активных потоков (`thread_count`)**: Динамический счетчик потоков исполняемого процесса.

### 2.2 Оперативная память (RAM)
* **Working Set (Private & Shared)**: Объем физической оперативной памяти, выделенный процессу (с разделением на монопольные и разделяемые страницы).
* **Commit Charge (Private Bytes)**: Объем выделенной виртуальной памяти, гарантированный подкачкой.
* **Page Faults Count**: Количество ошибок адресации страниц памяти (Hard/Soft Page Faults).

### 2.3 Графический процессор и видеопамять (GPU)
* **Выделенная и общая VRAM (`dedicated_vram_bytes`, `shared_vram_bytes`)**: Объем используемой видеопамяти графического адаптера, определяемый через D3DKMT (Direct3D Kernel Mode Thunks) или счетчик PDH `GPU Engine(pid_<PID>)`.
* **Загрузка GPU-движков (`gpu_engine_utilization`)**: % загрузки блоков 3D, Video Decode/Encode и Compute.

### 2.4 Файловый I/O и отслеживание контролируемых директорий
* **Сквозная активность дискового ввода-вывода**: Общее количество байтов и операций чтения (`read_bytes`, `read_ops`), записи (`write_bytes`, `write_ops`) и управления.
* **Мониторинг файловых событий в целевых каталогах**:
  * Фиксация событий через `ReadDirectoryChangesW` и провайдер ETW `Microsoft-Windows-Kernel-File`.
  * Регистрация фактов создания (`CREATE`), изменения (`MODIFY`), удаления (`DELETE`) и переименования (`RENAME`) файлов в отслеживаемых папках с явной привязкой к инициировавшему событие PID.
* **Счетчик открытых файловых дескрипторов (`file_handles_count`)**.

### 2.5 Сетевая активность и сокеты (Network I/O)
* **Объем сетевого трафика**: Суммарное количество отправленных/принятых байтов (`bytes_sent`, `bytes_recv`) и пакетов (`packets_sent`, `packets_recv`), сгенерированных процессом.
* **Активные сетевые соединения**: Маппинг PID на открытые сокеты TCP/UDP через `GetExtendedTcpTable` / `GetExtendedUdpTable` (`iphlpapi.dll`) с фиксацией адресов назначений, портов и состояний (`ESTABLISHED`, `LISTEN` и др.).

### 2.6 Системные ресурсы и GUI-дескрипторы
* **GDI & USER Objects**: Количество графических объектов (`GetGuiResources(GR_GDIOBJECTS)`) и объектов интерфейса (`GR_USEROBJECTS`) для предотвращения утечек окон.
* **Process Handle Count**: Общее количество открытых хэндлов системных объектов (файлы, секции, мутексы, события).

---

## 3. Схема таблиц SQLite (`telemetry.db`)

Для высокоскоростного сбора и хранения временных рядов в БД вводятся три оптимизированные таблицы:

```sql
-- Таблица снимков метрик ресурсов процессов
CREATE TABLE IF NOT EXISTS process_pid_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    executable_path TEXT,
    cpu_percent REAL NOT NULL DEFAULT 0.0,
    user_time_ms INTEGER NOT NULL DEFAULT 0,
    kernel_time_ms INTEGER NOT NULL DEFAULT 0,
    working_set_bytes INTEGER NOT NULL DEFAULT 0,
    private_bytes INTEGER NOT NULL DEFAULT 0,
    gpu_vram_bytes INTEGER DEFAULT 0,
    gpu_utilization REAL DEFAULT 0.0,
    read_bytes_total INTEGER DEFAULT 0,
    write_bytes_total INTEGER DEFAULT 0,
    net_bytes_sent_total INTEGER DEFAULT 0,
    net_bytes_recv_total INTEGER DEFAULT 0,
    handle_count INTEGER DEFAULT 0,
    gdi_objects INTEGER DEFAULT 0,
    user_objects INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_proc_pid_time ON process_pid_snapshots(pid, timestamp);
CREATE INDEX IF NOT EXISTS idx_proc_name_time ON process_pid_snapshots(process_name, timestamp);

-- Таблица событий файловых операций в отслеживаемых директориях
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

-- Таблица сетевых сокетов и интенсивности трафика по PID
CREATE TABLE IF NOT EXISTS process_network_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid INTEGER NOT NULL,
    protocol TEXT NOT NULL, -- 'TCP', 'UDP'
    local_address TEXT NOT NULL,
    local_port INTEGER NOT NULL,
    remote_address TEXT,
    remote_port INTEGER,
    state TEXT,
    bytes_sent_delta INTEGER DEFAULT 0,
    bytes_recv_delta INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_net_pid_time ON process_network_snapshots(pid, timestamp);
```

---

## 4. REST API Контракт (FastAPI)

Все роутеры читают готовые метрики из `telemetry.db` со временем отклика < 5 мс.

### 4.1 `GET /api/v1/telemetry/processes/{pid}`
Получение текущих свежих метрик ресурсоемкости конкретного процесса по PID.

**Ответ**:
```json
{
  "pid": 4812,
  "process_name": "code.exe",
  "executable_path": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
  "cpu": {
    "percent": 4.2,
    "user_time_ms": 14200,
    "kernel_time_ms": 3100,
    "thread_count": 38
  },
  "memory": {
    "working_set_mb": 312.4,
    "private_bytes_mb": 410.1,
    "page_faults": 128400
  },
  "gpu": {
    "vram_dedicated_mb": 145.0,
    "utilization_percent": 1.5
  },
  "io": {
    "read_bytes_sec": 10240,
    "write_bytes_sec": 4096,
    "handles_count": 850
  },
  "network": {
    "bytes_sent_sec": 512,
    "bytes_recv_sec": 2048,
    "active_sockets": 6
  },
  "timestamp": "2026-10-06T14:55:00Z"
}
```

### 4.2 `GET /api/v1/telemetry/processes/{pid}/file-activity`
Получение истории операций чтения/записи/изменения файлов процессом в отслеживаемых директориях.

**Параметры**: `directory` (опционально), `limit` (default: 50).

### 4.3 `POST /api/v1/telemetry/tracked-directories`
Настройка списка отслеживаемых директорий для мониторинга активности процессов.

---

## 5. Оптимизация производительности

1. **In-Memory Ring Buffer**: Сбор метрик процессом-коллектором происходит раз в 1 секунду с сохранением во внутреннем кольцевом буфере памяти на 60 отсчетов.
2. **Пакетный сброс (Batch WAL Writer)**: Запись снимков процессов в `telemetry.db` выполняется раз в 5 секунд одной транзакцией (`BEGIN TRANSACTION ... COMMIT`).
3. **Автоматическая очистка (Retention & Compaction)**: Детализированные посекундные записи процессов старше 24 часов усекаются, а часовые агрегаты сохраняются в таблицах роллапов.
