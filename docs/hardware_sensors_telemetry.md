# Система сенсоров и телеметрии AI-Breadboard

## Обзор

Система собирает аппаратные метрики компьютера через **два независимых источника**:
1. **LibreHardwareMonitor (LHM)** — через HTTP API (порт 8085) и WMI namespace
2. **Пользовательские сборщики** — через `nvidia-smi` CLI и прямой WMI доступ

Это позволяет покрыть все возможные сенсоры и избежать потери данных.

---

## Источники данных

### 1. `_poll_hardware_monitor()` — `hardware_monitor_polls.csv`

**Метод:** `get_hardware_sensors()` → 3 подисточника:
- `_probe_nvidia_gpu_sensors()` — через `nvidia-smi` CLI
- `_probe_libre_hardware_monitor_wmi()` — через WMI namespace `root\LibreHardwareMonitor`
- `_probe_wmi_thermal_zones()` — через WMI `root\wmi\MSAcpi_ThermalZoneTemperature`

**Колонки CSV:**
```
timestamp, sensor_name, sensor_type, value, unit, hardware_type
```

**Что собирает:**
| Категория | Данные | Примеры |
|-----------|--------|---------|
| **GPU (через NVIDIA SMI)** | Температура, Мощность (W), Обороты вентилятора (%) | GPU Core Temp, GPU Power (W), GPU Fan Speed (%) |
| **ACPI Thermal Zones** | Температура термальных зон материнской платы | ACPI Thermal Zone 1 (°C) |
| **LHM через WMI** | Температуры, обороты, напряжения | CPU Package, Fan RPM, Voltage |

---

### 2. `_poll_librehardwaremonitor()` — `librehardwaremonitor_polls.csv`

**Метод:** `LhmService.get_flattened_sensors()` → HTTP API (http://localhost:8085/data.json)

**Колонки CSV:**
```
timestamp, hardware, sensor_name, category, value, unit, raw_value
```

**Категории сенсоров (из LHM):**
```
Temperatures, Load, Clocks, Voltages, Powers, Fans,
Controls, Levels, Data, Throughput, Factors, Times
```

**Что собирает (уникальные данные):**
| Категория | Данные | Примеры |
|-----------|--------|---------|
| **Clocks (Частоты)** | CPU/GPU/Memory Clock | CPU Clock (MHz), GPU Core Clock (MHz), Memory Clock (MHz) |
| **Voltages (Напряжения)** | Напряжения питания | CPU Core Voltage (V), 3.3V (V), 5V (V), 12V (V) |
| **Controls (Контроллеры)** | Управление сенсорами | Fan Control (%), Pump Control |
| **Levels (Уровни)** | Использование ресурсов | GPU Memory Used (GB), RAM Used (GB) |
| **Data (Данные)** | Емкость и объемы | GPU Memory Total (GB), RAM Total (GB) |
| **Throughput (Пропускная способность)** | Скорость чтения/записи | Disk Read Speed (MB/s), Network Throughput (Mbps) |
| **Factors (Факторы)** | Множители и базовые частоты | CPU Multiplier, Bus Speed (MHz) |
| **Times (Время)** | Время работы и нагрузки | GPU Time, Uptime |

---

## Почему два источника?

### Дублирование НЕТ — каждый источник уникален:

| Данные | `_poll_hardware_monitor()` | `_poll_librehardwaremonitor()` |
|--------|----------------------------|-------------------------------|
| GPU Power (W) | ✅ Через `nvidia-smi` | ❌ Нет |
| GPU Fan Speed (%) | ✅ Через `nvidia-smi` | ⚠️ Через WMI (менее надежно) |
| GPU Core Clock (MHz) | ❌ Нет | ✅ Через LHM HTTP API |
| CPU Core Voltage (V) | ❌ Нет | ✅ Через LHM HTTP API |
| 3.3V/5V/12V | ❌ Нет | ✅ Через LHM HTTP API |
| Fan Control (%) | ❌ Нет | ✅ Через LHM HTTP API |
| RAM Used (GB) | ❌ Только общее | ✅ Через LHM HTTP API |
| GPU Memory Used (GB) | ❌ Нет | ✅ Через LHM HTTP API |
| Network Throughput (Mbps) | ❌ Только bytes/sec | ✅ Через LHM HTTP API |
| ACPI Thermal Zones | ✅ Через WMI | ❌ Нет |

---

## Фильтрация изменений

Оба польлера используют метод `_has_value_changed()`:

```python
def _has_value_changed(self, app_name: str, new_value: Any) -> bool:
    prev_value = self._last_values.get(app_name)
    
    # Конвертируем сложные структуры в hashable для сравнения
    def to_hashable(val: Any) -> Any:
        if isinstance(val, dict):
            return tuple(sorted((k, to_hashable(v)) for k, v in val.items()))
        elif isinstance(val, (list, set)):
            return tuple(to_hashable(v) for v in val)
        return val
    
    prev_hashable = to_hashable(prev_value) if prev_value is not None else None
    new_hashable = to_hashable(new_value)
    
    changed = prev_hashable != new_hashable
    self._last_values[app_name] = new_value
    return changed
```

**Результат:** записываются только изменения — если все значения не изменились, строка в CSV НЕ добавляется.

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                   AutoLogEngine                             │
│  Запускает pollers с интервалом из config.json             │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌───────────────────────┐           ┌───────────────────────┐
│ _poll_hardware_monitor│           │ _poll_librehardwaremon│
│ (get_hardware_sensors)│           │ (LhmService.get_flatt │
└───────────────────────┘           │ ened_sensors())       │
        ↓                                       ↓
┌───────────────────────┐           ┌───────────────────────┐
│ hardware_monitor_polls│           │ librehardwaremonitor_po│
│ .csv                  │           │ lls.csv               │
│ timestamp, sensor_nam │           │ timestamp, hardware,   │
│ e, sensor_type, value │           │ sensor_name, category, │
│ , unit, hardware_type │           │ value, unit, raw_value │
└───────────────────────┘           └───────────────────────┘
```

---

## Конфигурация

В `config.json`:

```json
{
  "logging": {
    "enable_autolog": true,
    "default_interval": "1 minute",
    "loggers": {
      "hardware_monitor": {
        "interval": "5 seconds",
        "enabled": true
      },
      "librehardwaremonitor": {
        "interval": "5 seconds",
        "enabled": true
      }
    }
  }
}
```

---

## Файлы CSV

Все CSV файлы сохраняются в `%APPDATA%/AI-Breadboard/apps/logs/`:

- `hardware_monitor_polls.csv` — сенсоры через `get_hardware_sensors()`
- `librehardwaremonitor_polls.csv` — сенсоры через LHM HTTP API
- `lhm_sensor_polls.csv` — дополнительные сенсоры LHM (если есть)
- `system_inspector_polls.csv` — базовая телеметрия (CPU, RAM, Disk, Net)
- `software_audit.csv` — аудит ПО

---

## Запуск через лончер

`launchers/Run-Sensors.ps1`:

```powershell
# Запуск сенсоров по умолчанию
.\launchers\Run-Sensors.ps1

# Проверка статуса
.\launchers\Run-Sensors.ps1 -Action status

# Остановка
.\launchers\Run-Sensors.ps1 -Action stop

# С нестандартными параметрами
.\launchers\Run-Sensors.ps1 -Interval 2.0 -TopProcesses 50
```

---

## Централизованный агрегатор телеметрии (`TelemetryAggregator`)

Потоковый сборщик и логгер телеметрии со всех аппаратных датчиков и сетевых компонентов.

### Структурированный формат сенсоров и значений (values)

Каждый датчик представлен отдельной записью, в массив `values` которой инкрементируются новые замеры:

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

### Автономность и ротация 50 МБ

1. **Автономность модуля**: Подсистема `apps/windows/telemetry` изолирована от веб-сервера и баз данных. Запись выполняется прямо в локальные файлы `%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs`, обеспечивая непрерывную работу при любых сбоях окружения.
2. **Ротация 50 МБ**: При достижении 50 МБ файл `ai_sensors_polls.json` ротируется с меткой времени (`ai_sensors_polls_YYYYMMDD_HHMMSS.json`), и сбор продолжается в новый чистый файл.

### Управление через `Run-AI-Sensors.ps1`

```powershell
# Запуск
.\launchers\Run-AI-Sensors.ps1

# Перезапуск заново (сброс старых процессов)
.\launchers\Run-AI-Sensors.ps1 -Restart

# Статус
.\launchers\Run-AI-Sensors.ps1 -Action status

# Остановка
.\launchers\Run-AI-Sensors.ps1 -Action stop
```

---

## Дополнительные модули

- `apps/windows/telemetry/sensor_collector.py` — адаптер сбора метрик и группировки `samples`
- `apps/windows/telemetry/aggregator.py` — центральный агрегатор телеметрии
- `apps/windows/telemetry/json_logger.py` — JSON-логгер с авторотацией по 50 МБ
- `apps/windows/telemetry/telemetry_config.py` — менеджер конфигурации сенсоров
- `apps/librehardwaremonitor/core/lhm_service.py` — сервис LHM через HTTP API
- `apps/common/autolog_engine.py` — движок автологгирования

---

## История изменений

- **2026-09-24** — Рефакторинг формата телеметрии: группировка по устройствам/метрикам и массив `samples` с таймстемпами. Установлена ротация логов на 50 МБ. Добавлена поддержка флага `-Restart` в лаунчере `Run-AI-Sensors.ps1`.
- **2026-09-21** — Переписан `storage.py`: SQLite → CSV (убрана зависимость от `data/telemetry.db`).
- **2026-09-21** — Документирована архитектура сенсоров и логгирования.

---

## Контакты

- **Author:** hypo69
- **Project:** AI-Breadboard
- **Version:** 1.0 (FastAPI Foundry Edition)