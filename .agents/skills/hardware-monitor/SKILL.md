---
name: hardware-monitor
description: Hardware monitoring toolkit using LibreHardwareMonitor. Use for querying CPU/GPU temperatures, voltages, power consumption, clock speeds, fan speeds, RAM and storage metrics.
description_i18n:
  en: Hardware monitoring toolkit using LibreHardwareMonitor. Use for querying CPU/GPU temperatures, voltages, power consumption, clock speeds, fan speeds, RAM and storage metrics.
  ru: Инструментарий аппаратного мониторинга через LibreHardwareMonitor. Позволяет получать температуру процессора (CPU) и видеокарты (GPU), напряжения, энергопотребление, тактовые частоты, скорость вентиляторов, загрузку памяти и накопителей.
---

# Hardware Monitor (LibreHardwareMonitor)

Системный навык для сбора и отображения телеметрии физического оборудования с помощью локального сервера LibreHardwareMonitor.

## 🚀 Возможности
- Мониторинг температур ядер и пакета CPU (`Core Max`, `Core Average`, `CPU Package`).
- Мониторинг температуры и загрузки GPU.
- Сбор данных по напряжениям, мощностям (ватты), частотам ядер (МГц).
- Проверка загрузки оперативной памяти и состояния накопителей.

## 🛠️ Быстрый старт

### Получение температуры процессора:
```powershell
py .agents/skills/hardware-monitor/monitor.py cpu
```

### Полная сводка по системе (CPU, GPU, RAM):
```powershell
py .agents/skills/hardware-monitor/monitor.py
```

### JSON-вывод для интеграций:
```powershell
py .agents/skills/hardware-monitor/monitor.py --json
```

## ⚙️ Требования
1. Запущенное приложение **LibreHardwareMonitor**.
2. Включенный встроенный веб-сервер в LibreHardwareMonitor:
   - Меню: `Options` -> `Remote Web Server` -> `Run` (порт по умолчанию: `8085`).
