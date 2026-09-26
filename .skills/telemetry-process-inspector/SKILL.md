---
name: telemetry-process-inspector
description: Retrieve and display system process states and temperature sensors from SQLite telemetry database.
description_i18n:
  en: Retrieve and display system process states and temperature sensors from SQLite telemetry database.
  ru: Инспектор состояния системных процессов и температурных датчиков из SQLite базы данных телеметрии.
---

# Telemetry Process & Hardware Inspector

## 🎯 Назначение
Навык предназначен для быстрого извлечения и отображения текущего состояния запущенных процессов ОС, а также показаний температурных датчиков оборудования из постоянного SQLite-хранилища телеметрии (`telemetry.db`).

## 🚀 Протокол выполнения
1. Подключение к SQLite-базе данных телеметрии Windows (`telemetry.db`).
2. Для процессов: выборка последнего снимка системы (`system_snapshots`) и связанных с ним процессов (`process_snapshots`).
3. Для температуры: выборка последних актуальных показаний датчиков категории `'Temperatures'` из таблицы `sensor_polls` с использованием оконной агрегации по `sensor_id` и `MAX(id)`.

## 🛠️ Использование скриптов
```bash
# Процессы
python .skills/telemetry-process-inspector/scripts/get_process_state.py [--limit 20] [--sort cpu|memory]

# Температурные датчики
python .skills/telemetry-process-inspector/scripts/get_temperatures.py
```
