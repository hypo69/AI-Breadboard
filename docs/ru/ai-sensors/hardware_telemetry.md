# Аппаратная телеметрия и датчики (Hardware & System Telemetry)

## 📋 Обзор

Аппаратная телеметрия в AI-Breadboard реализует сбор ключевых параметров физического состояния компьютера: температуры компонентов, тактовые частоты ядер, потребляемая мощность, уровни напряжения, скорость вращения вентиляторов, состояние накопителей (S.M.A.R.T., наработка в часах, износ, TBW) и системные ресурсы операционной системы.

---

## 🔌 Источники данных и провайдеры

Сбор метрик осуществляется через многоуровневую систему аппаратных провайдеров:
1. **LibreHardwareMonitor (LHM)** — опрос веб-сервиса (порт 8085) и WMI-пространства `root\LibreHardwareMonitor`.
2. **HWiNFO / CPU-Z / GPU-Z / AIDA64** — аппаратные сенсоры, Shared Memory XML и CLI-отчеты.
3. **Дисковая подсистема и надежность** — нативный сенсор Windows [`WindowsStorageSensor`](../../apps/windows/storage_sensors/windows_storage_sensor.py) (`MSFT_PhysicalDisk` + `StorageReliabilityCounter`).
4. **Прямые системные провайдеры** — утилита `nvidia-smi`, WMI-зоны `root\wmi\MSAcpi_ThermalZoneTemperature` и библиотека `psutil`.

---

## 📈 Собираемые метрики и CSV-файлы опроса

| Группа метрик | Источники | Примеры параметров | Целевой CSV-файл (`%APPDATA%/AI-Breadboard/apps/windows/telemetry/logs/`) |
| :--- | :--- | :--- | :--- |
| **Температуры (°C)** | LHM / HWiNFO / AIDA64 / NVIDIA-SMI | `CPU Package`, `GPU Core Temp`, `GPU Hotspot`, `Motherboard`, `Thermal Zone 1` | `lhm_sensor_polls.csv`, `hwinfo_sensor_polls.csv`, `aida64_sensor_polls.csv` |
| **Напряжения (V)** | LHM / HWiNFO / CPU-Z | `CPU Core Voltage (VCORE)`, `+3.3V`, `+5V`, `+12V`, `DRAM Voltage` | `lhm_sensor_polls.csv`, `cpuz_hardware_polls.csv` |
| **Мощность (W)** | NVIDIA-SMI / LHM / HWiNFO | `GPU Power Draw`, `CPU Package Power`, `Total System Power` | `lhm_sensor_polls.csv`, `gpuz_sensor_polls.csv` |
| **Частоты (MHz)** | LHM / CPU-Z / GPU-Z | `CPU Core #1 Clock`, `GPU Memory Clock`, `BCLK`, `Multiplier` | `lhm_sensor_polls.csv`, `cpuz_hardware_polls.csv`, `gpuz_sensor_polls.csv` |
| **Кулеры и помпы** | LHM / NVIDIA-SMI / HWiNFO | `CPU Fan RPM`, `GPU Fan Speed (%)`, `Water Pump Control (RPM)` | `lhm_sensor_polls.csv`, `hwinfo_sensor_polls.csv` |
| **Накопители и надежность** | WindowsStorageSensor | `Power-On Hours (наработка часов)`, `Power Cycles`, `Wear % (износ)`, `TBW`, `Reallocated Sectors` | `windows_audit_polls.csv` |
| **Память и ОС** | psutil / SystemCollector | `RAM Used (GB)`, `RAM Available`, `Swap %`, `Disk Read/Write MB/s`, `Network Rx/Tx` | `windows_audit_polls.csv`, `system_inspector_polls.csv` |

---

## 💾 Конфигурация интервалов опроса

Интервалы опроса сенсоров задаются в файле **[`apps/windows/config.json`](../../apps/windows/config.json)**:

```json
{
  "sensors": {
    "cpu": { "enabled": true, "interval_seconds": 5.0, "metrics": ["temperature", "load", "clocks"] },
    "gpu": { "enabled": true, "interval_seconds": 10.0, "metrics": ["temperature", "load", "memory", "power"] },
    "ram": { "enabled": true, "interval_seconds": 10.0, "metrics": ["usage", "swap"] },
    "disk": { "enabled": true, "interval_seconds": 30.0, "metrics": ["usage", "io"] },
    "network": { "enabled": true, "interval_seconds": 10.0, "metrics": ["throughput", "connections"] },
    "sensors": { "enabled": true, "interval_seconds": 10.0, "metrics": ["temperature", "fan", "voltage"] },
    "internet": { "enabled": true, "interval_seconds": 120.0, "metrics": ["ping", "download", "upload", "dns"] }
  }
}
```

---

## 💾 Форматы хранения телеметрии

1. **Табличные CSV-файлы:**
   * Расположение: `%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs\`
   * Формат строк: `timestamp,app,poll_type,metric_name,value,unit,status,details`
2. **Потоковые JSONL-файлы:**
   * Расположение: `logs/telemetry/ai_sensors_polls.jsonl`
   * Формат: структурированный JSON с авторотацией при достижении 50–100 МБ.
3. **Историческая база SQLite:**
   * Расположение: `data/telemetry/hardware_history.db` для построения графиков и трендов за длительный период.

---

## 🧪 Запуск и тестирование

```powershell
# Тестирование аппаратных провайдеров и сенсоров
pytest tests/apps/windows/test_telemetry_aggregator.py apps/windows/tests/test_storage_sensor.py -v
```
