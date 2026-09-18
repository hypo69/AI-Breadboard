# 🖥️ Windows Hardware Monitor & Diagnostics
# =============================================================================
# Package: apps.windows.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

Пакет низкоуровневой аппаратной диагностики, мониторинга оборудования в реальном времени и контролируемого стресс-тестирования для операционных систем Windows.

---

## 📌 Возможности

1. **Hardware Monitor (Мониторинг реального времени)**:
   - **CPU**: Загрузка ядер/потоков, текущие и предельные частоты, прерывания и переключения контекста.
   - **RAM & Swap**: Объем физической памяти, использование, резерв и файл подкачки.
   - **GPU Telemetry**: Поддержка видеокарт NVIDIA (`nvidia-smi`), AMD (`amd-smi`), Intel Arc (`xpu-smi`) и WMI fallback (температуры, память VRAM, энергопотребление, кулеры).
   - **Storage & SMART**: Скорости чтения/записи (IOPS / MB/s), свободное место томов, детальный статус накопителей через `smartctl` и WMI.
   - **Датчики (Sensors)**: Температуры ACPI / материнской платы, обороты вентиляторов (RPM), напряжения через `LibreHardwareMonitor` / `OpenHardwareMonitor` / WMI.
   - **Сеть и Электропитание**: Пропускная способность сети (KB/s, MB/s), активные сокеты, состояние батареи и зарядного устройства.

2. **Аппаратный аудит (Hardware Audit)**:
   - Сбор спецификаций CPU, сокета, материнской платы и таймингов памяти через `CPU-Z`, `AIDA64` или WMI.

3. **Стресс-тестирование (SafeOps Stress Benchmark)**:
   - Контролируемый тест стабильности CPU и GPU с активным аварийным прерыванием при достижении критической температуры (`max_safe_temp_c`).

---

## 🚀 Быстрый старт в коде

```python
from apps.windows.hardware import HardwareMonitor

monitor = HardwareMonitor()

# Получение полного моментального снимка
snapshot = monitor.get_snapshot()
print(f"Загрузка CPU: {snapshot.cpu.utilization_pct}%")
print(f"Занято RAM: {snapshot.memory.used_gb} GB / {snapshot.memory.total_gb} GB")

# Оценка здоровья оборудования
summary = monitor.get_summary()
print(f"Статус системы: {summary['status']}")
```

---

## 🌐 API Эндпоинты

- `GET /api/windows/hardware/monitor` — Полный моментальный снимок всех компонентов оборудования.
- `GET /api/windows/hardware/monitor/summary` — Краткая сводка здоровья и превышения пороговых значений.
- `GET /api/windows/hardware/sensors` — Показания всех активных датчиков температуры, вентиляторов и напряжений.
- `GET /api/windows/hardware/gpu` — Детальная телеметрия графических процессоров.
- `GET /api/windows/hardware/smart` — S.M.A.R.T. здоровье дисков.
- `POST /api/windows/benchmark/stress` — Запуск контролируемого стресс-теста.
