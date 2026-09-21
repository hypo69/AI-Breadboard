# 📊 AIDA64 Diagnostic App

Модуль интеграции с диагностическим комплексом **AIDA64** (Extreme / Engineer / Business) для проекта **AI-Breadboard**.

Предоставляет сбор телеметрии в реальном времени через **Windows Shared Memory (WinAPI)**, WMI, а также формирование аппаратных отчетов через **AIDA64 CLI**.

---

## 🚀 Возможности

1. **Мгновенный опрос датчиков (Shared Memory):**
   * Считывание температур (CPU, GPU, чипсет, накопители NVMe/SSD/HDD).
   * Считывание энергопотребления (Package W, IA Cores W, DIMM W).
   * Считывание напряжений (Core V, VID, GPU V) и скорости вентиляторов (RPM).
   * Нулевая нагрузка на процессор (прямой доступ к блоку `AIDA64_SensorValues` в WinAPI).
2. **Аппаратные отчёты (CLI):**
   * Генерация XML/HTML/CSV отчетов конфигурации системы в фоновом режиме (`/R /XML /HW /SILENT`).
3. **REST API & CLI:**
   * Автономный микросервер FastAPI на порту `8120` (`/api/v1/aida64`).
   * Консольный интерфейс для быстрой проверки и интеграции со скриптами.

---

## ⚙️ Настройка AIDA64 (Portable)

1. Распакуйте AIDA64 в папку: `bin/aida64/` (чтобы исполняемый файл был `bin/aida64/aida64.exe` или `bin/AIDA64/aida64.exe`).
2. В окне AIDA64 откройте:
   `File` ➔ `Preferences` ➔ `Hardware Monitoring` ➔ `External Applications`
3. Включите опции:
   * ✅ **Enable shared memory** *(обязательно для live-сенсоров)*
   * ✅ **Enable writing sensor values to Registry**
   * ✅ **Enable writing sensor values to WMI**
   * ✅ **Enable writing sensor values to Rivatuner OSD Server**

---

## 💻 Использование

### CLI
```powershell
# Проверить статус бинарника и Shared Memory
python -m apps.aida64

# Вывести показания всех датчиков
python -m apps.aida64 --sensors

# Вывести показания датчиков в формате JSON
python -m apps.aida64 --sensors --json

# Сгенерировать аппаратный отчёт через CLI
python -m apps.aida64 --report HW

# Запустить автономный HTTP API сервер
python -m apps.aida64 --server --port 8120
```

### REST API
* `GET /api/v1/aida64/status` — статус доступности Shared Memory, путь к бинарнику и руководство по настройке.
* `GET /api/v1/aida64/sensors` — список всех активных датчиков в реальном времени.
* `POST /api/v1/aida64/report` — запуск генерации отчёта через CLI.

---

## 🧪 Тестирование
```powershell
pytest apps/aida64/tests/test_aida64.py -v
```
