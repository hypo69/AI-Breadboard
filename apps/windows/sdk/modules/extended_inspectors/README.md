# Extended Inspectors (Расширенные Инспекторы Windows)

Данная директория содержит модули для глубокой аналитики ресурсов и динамического тестирования безопасности в ОС Windows:

1. **`srum_power_analytics.py` (SRUM & Power Analytics)**:
   - Анализирует исторические данные из реестра и базы данных `SRUDB.dat` (System Resource Usage Monitor).
   - Выявляет процессы и драйверы, блокирующие переход в спящий режим через `powercfg /requests`.

2. **`wsl2_hyperv_inspector.py` (WSL2 & Hyper-V Inspector)**:
   - Сканирует и отслеживает размеры динамических виртуальных дисков `.vhdx` подсистем WSL2 и Hyper-V.
   - Осуществляет автоматическое сжатие файлов дисков через интерфейс `compact vdisk` служебной утилиты `diskpart`.

3. **`windows_sandbox_inspector.py` (Windows Sandbox Inspector)**:
   - Автоматизирует подготовку конфигураций `.wsb` для безопасного динамического запуска подозрительных исполнимых файлов.
   - Обеспечивает изолированное исполнение в среде Windows Sandbox.

## Использование в Python API

```python
from apps.windows.sdk.modules.extended_inspectors import (
    SRUMPowerAnalytics,
    WSL2HyperVInspector,
    WindowsSandboxInspector
)

# 1. Анализ блокировок электропитания
power_analytics = SRUMPowerAnalytics()
summary = power_analytics.analyze_power_and_resource_usage()

# 2. Инспекция дисков WSL2
wsl_inspector = WSL2HyperVInspector()
wsl_report = wsl_inspector.inspect_vhdx_disks()

# 3. Запуск в песочнице
sandbox = WindowsSandboxInspector()
result = sandbox.launch_in_sandbox("C:/Downloads/suspicious_sample.exe")
```
