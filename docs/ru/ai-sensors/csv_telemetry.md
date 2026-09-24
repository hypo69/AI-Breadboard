# Централизованное CSV-логгирование сенсоров и приложений (CSV Telemetry)

## 📋 Обзор

В AI-Breadboard все сенсоры, аппаратные проберы и модули приложений записывают структурированную телеметрию в формате **CSV** через единый централизованный логгер [`AppCsvLogger`](../../apps/common/csv_logger.py).

Логирование в CSV обеспечивает:
1. **Табличную совместимость:** Удобный импорт в Excel, Pandas, Grafana, PowerBI и BI-аналитику без промежуточного парсинга.
2. **Потокобезопасность:** Многопоточная запись через единый мьютекс (`threading.Lock`).
3. **Стандартизацию схемы:** Строгое разделение на 3 категории логов (Опросы, События, Изменения параметров).
4. **Автоматическую инициализацию:** Автоматическое создание заголовков колонок (`headers`) при первом обращении к файлу с кодировкой `utf-8-sig` (для корректного отображения в Microsoft Excel).

---

## 📁 Расположение файлов CSV-логов

Все CSV-файлы сохраняются в системный каталог пользователя:

* **Windows:** `%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs\` (например, `C:\Users\<User>\AppData\Roaming\AI-Breadboard\apps\windows\telemetry\logs\`)
* **Фолбэк:** `%LOCALAPPDATA%\AI-Breadboard\apps\windows\telemetry\logs\` или `~/.config/AI-Breadboard/apps/windows/telemetry/logs/`

---

## 📊 Три стандартных формата CSV-файлов

### 1. Файлы опроса телеметрии и сенсоров (`*_polls.csv`)
Используются для регулярных замеров метрик (температуры, частоты, напряжения, сетевой трафик, пинг, состояние дисков).

**Структура колонок:**
```csv
timestamp,app,poll_type,metric_name,value,unit,status,details
```

| Колонка | Тип | Описание | Пример |
| :--- | :--- | :--- | :--- |
| `timestamp` | ISO-8601 UTC | Точное время фиксации замера | `2026-09-24T11:45:00.123456+00:00` |
| `app` | String | Идентификатор приложения / провайдера | `librehardwaremonitor`, `hwinfo`, `windows` |
| `poll_type` | String | Тип опроса (`sensor_read`, `status_check`, `metrics_fetch`) | `sensor_read` |
| `metric_name` | String | Наименование конкретной метрики | `cpu_package_temp`, `gpu_core_clock`, `disk_tbw` |
| `value` | Number / String / JSON | Численное значение или структурированный результат | `62.5`, `1830`, `14.2` |
| `unit` | String | Единица измерения | `°C`, `MHz`, `V`, `W`, `RPM`, `GB`, `ms` |
| `status` | String | Статус получения данных (`OK`, `WARNING`, `FAILED`) | `OK` |
| `details` | String / JSON | Дополнительный контекст или метаданные | `{"sensor_id": "/amdcpu/0/temperature/2"}` |

---

### 2. Файлы событий жизненного цикла и инвентаризации (`*_events.csv`)
Используются для регистрации дискретных событий (запуск/остановка служб, подключение устройств, обнаружение оборудования, сканирования).

**Структура колонок:**
```csv
timestamp,app,event_type,status,details
```

| Колонка | Тип | Описание | Пример |
| :--- | :--- | :--- | :--- |
| `timestamp` | ISO-8601 UTC | Время возникновения события | `2026-09-24T11:45:05.654321+00:00` |
| `app` | String | Имя приложения / модуля | `windows_defender`, `lhm_service`, `cloudflared` |
| `event_type` | String | Тип события (`service_start`, `scan_completed`, `device_connected`) | `service_start` |
| `status` | String | Результат события (`OK`, `SUCCESS`, `FAILED`, `EXECUTED`) | `SUCCESS` |
| `details` | String / JSON | Детальное описание или полезная нагрузка события | `{"binary_path": "C:\\LHM\\LibreHardwareMonitor.exe"}` |

---

### 3. Файлы изменений параметров и конфигураций (`*_param_changes.csv`)
Используются для аудита изменения настроек сенсоров, интервалов опроса, параметров безопасности и конфигурации системы.

**Структура колонок:**
```csv
timestamp,app,param_name,old_value,new_value,status,user,details
```

| Колонка | Тип | Описание | Пример |
| :--- | :--- | :--- | :--- |
| `timestamp` | ISO-8601 UTC | Время изменения параметра | `2026-09-24T11:45:10.000000+00:00` |
| `app` | String | Имя подсистемы | `admin`, `system_control_center`, `windows` |
| `param_name` | String | Название параметра | `sensors.disk.interval_seconds`, `sec.uac_level` |
| `old_value` | Any | Старое значение | `60.0`, `1` |
| `new_value` | Any | Новое значение | `30.0`, `2` |
| `status` | String | Статус применения (`SUCCESS`, `FAILED`, `ROLLBACK`) | `SUCCESS` |
| `user` | String | Инициатор изменения | `admin`, `system`, `user` |
| `details` | String / JSON | Причина изменения или снимок точки отката | `{"reason": "Performance tuning"}` |

---

## 📑 Сводный реестр CSV-файлов сенсоров и провайдеров

В таблице ниже приведен полный перечень файлов, формируемых сенсорами и аппаратными провайдерами:

| Категория | Имя CSV-файла | Источник / Модуль | Что именно записывается в файл (`%APPDATA%/AI-Breadboard/apps/windows/telemetry/logs/`) |
| :--- | :--- | :--- | :--- |
| 🌡️ **LHM** | `lhm_sensor_polls.csv` | [`apps/librehardwaremonitor`](../../apps/librehardwaremonitor) | Температуры CPU/GPU, частоты, мощности, напряжения шин (3.3V/5V/12V), обороты кулеров RPM |
| 🌡️ **LHM** | `lhm_status_polls.csv` | [`apps/librehardwaremonitor`](../../apps/librehardwaremonitor) | Доступность Web API (порт 8085) и WMI-пространства `root\LibreHardwareMonitor` |
| ⚙️ **LHM** | `lhm_service_events.csv` | [`apps/librehardwaremonitor`](../../apps/librehardwaremonitor) | События старта, остановки и рестарта фонового процесса `LibreHardwareMonitor.exe` |
| 🔍 **HWiNFO** | `hwinfo_sensor_polls.csv` | [`apps/~hwinfo`](../../apps/~hwinfo) | Показания датчиков HWiNFO (CPU Core/Package, GPU Hotspot, Memory Junction, VRM) |
| 🔍 **HWiNFO** | `hwinfo_status_polls.csv` | [`apps/~hwinfo`](../../apps/~hwinfo) | Статус подключения и доступности Shared Memory / CLI HWiNFO |
| 📋 **HWiNFO** | `hwinfo_inventory_events.csv` | [`apps/~hwinfo`](../../apps/~hwinfo) | Снимки инвентаризации чипсета, модулей памяти SPD и видеоадаптера |
| 🎮 **GPU-Z** | `gpuz_sensor_polls.csv` | [`apps/~gpuz`](../../apps/~gpuz) | Метрики видеокарты: частота GPU/памяти, загрузка видеоядра, энергопотребление W, обороты вентиляторов |
| ⚡ **CPU-Z** | `cpuz_hardware_polls.csv` | [`apps/~cpuz`](../../apps/~cpuz) | Спецификации процессора: множители ядер, BCLK, ревизия микрокода, вольтаж VCORE |
| 🔬 **AIDA64** | `aida64_sensor_polls.csv` | [`apps/~aida64`](../../apps/~aida64) | Опрос датчиков материнской платы через AIDA64 Shared Memory XML |
| 🔬 **AIDA64** | `aida64_status_polls.csv` | [`apps/~aida64`](../../apps/~aida64) | Доступность движка аудита AIDA64 |
| 📄 **AIDA64** | `aida64_report_events.csv` | [`apps/~aida64`](../../apps/~aida64) | События генерации CSV-отчетов аудита аппаратного обеспечения |
| 💾 **SMART / Disks** | `smartmontools_drives_polls.csv` | [`apps/smartmontools`](../../apps/smartmontools) | S.M.A.R.T. накопителей: наработка часов (Power-On Hours), Power Cycles, % износа (Wear), TBW, Reallocated Sectors |
| 💾 **SMART / Disks** | `smartmontools_status_polls.csv` | [`apps/smartmontools`](../../apps/smartmontools) | Доступность утилиты `smartctl.exe` и драйверов дисковой подсистемы |
| 🪟 **Windows System** | `windows_audit_polls.csv` | [`apps/windows`](../../apps/windows) | Загрузка CPU/RAM, активность логических дисков, сетевые интерфейсы psutil |
| 🪟 **Windows System** | `windows_audit_events.csv` | [`apps/windows`](../../apps/windows) | Аппаратные аномалии, события ядра и падения компонентов |
| 🛡️ **Defender** | `windows_defender_polls.csv` | [`apps/windows/defender`](../../apps/windows/defender) | Статус антивируса, версии сигнатур, активность Real-time protection |
| 🛡️ **Defender** | `windows_defender_events.csv` | [`apps/windows/defender`](../../apps/windows/defender) | События сканирования на угрозы, изоляция файлов |
| 🌐 **Network** | `windows_network_polls.csv` | [`apps/windows/network`](../../apps/windows/network) | Метрики сетевых адаптеров, пинг, DNS-задержки |
| 🌐 **Cloudflare** | `cloudflared_status_polls.csv` | [`apps/cloudflared_monitor`](../../apps/cloudflared_monitor) | Доступность Cloudflare туннелей, статус коннекторов |
| 🌐 **Cloudflare** | `cloudflared_endpoint_probes.csv` | [`apps/cloudflared_monitor`](../../apps/cloudflared_monitor) | Периодические пробы эндпоинтов туннеля (RTT, HTTP status code) |
| 🛠️ **Inspector** | `system_inspector_polls.csv` | [`apps/system_inspector`](../../apps/system_inspector) | Регулярные снимки процессов, открытых портов и дескрипторов |
| ⚙️ **Control Center** | `system_control_status_polls.csv` | [`apps/system_control_center`](../../apps/system_control_center) | Состояние системных служб Windows и профилей производительности |
| ⚙️ **Control Center** | `system_control_restore_points.csv`| [`apps/system_control_center`](../../apps/system_control_center) | Создание и статус системных точек восстановления |
| 👤 **Admin Panel** | `admin_status_polls.csv` | [`apps/ai_breadboard_admin`](../../apps/ai_breadboard_admin) | Состояние фоновых демонов, воркеров и API-роутеров |
| 👤 **Admin Panel** | `admin_config_param_changes.csv` | [`apps/ai_breadboard_admin`](../../apps/ai_breadboard_admin) | Журнал изменения системных параметров администратором |

---

## 💻 Программное использование в Python

Для записи метрик в свой собственный сенсор или модуль используется класс `AppCsvLogger`:

```python
from apps.common.csv_logger import AppCsvLogger

# 1. Инициализация логгера для своего модуля
csv_logger = AppCsvLogger("my_custom_sensor")

# 2. Логирование периодического замера метрики
csv_logger.log_poll(
    poll_type="sensor_read",
    metric_name="storage_temperature",
    value=41.5,
    unit="°C",
    status="OK",
    details={"disk_id": "NVMe_0", "model": "Samsung SSD 990 EVO Plus"},
    filename="my_custom_sensor_polls.csv"
)

# 3. Логирование события
csv_logger.log_event(
    event_type="threshold_exceeded",
    status="WARNING",
    details="Температура накопителя превысила 40°C",
    filename="my_custom_sensor_events.csv"
)

# 4. Логирование изменения параметров
csv_logger.log_param_change(
    param_name="poll_interval_sec",
    old_value=60,
    new_value=15,
    status="SUCCESS",
    user="administrator",
    filename="my_custom_sensor_param_changes.csv"
)
```
