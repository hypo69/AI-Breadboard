# Win32 FFI & Native Bindings

Директория содержит низкоуровневые интерфейсы взаимодействия с нативными библиотеками Windows C API (`ctypes` / FFI).

## 📌 Назначение
Модули данного пакета используются подсистемой телеметрии и аудита (`apps.windows.telemetry`, `apps.windows.core.audits`) для прямого сбора метрик ОС, минуя тяжеловесные вызовы WMI или внешних скриптов PowerShell:

- **`kernel32.py`** — снапшоты процессов, потоков и модулей (`CreateToolhelp32Snapshot`), замер процессорного времени и дескрипторы.
- **`advapi32.py`** — чтение системного реестра, токенов безопасности и дескрипторов прав.
- **`wevtapi.py`** — Windows Event Log API (высокоскоростной XPath-запрос и рендеринг журналов событий Windows).
- **`setupapi.py`** — инвентаризация PnP-устройств, детекция сбоев оборудования и флаппинга.
- **`nethelper.py`** — IP Helper API (`iphlpapi.dll`): опрос сетевых адаптеров, сетевой статистики и сокетов TCP/UDP.
- **`psapi.py`** — Process Status API: замер памяти процессов (Working Set, Pagefile).
- **`scm.py`** — Service Control Manager: опрос и аудит системных служб.
- **`tasksched.py`** — Task Scheduler COM API: сбор информации о запланированных задачах.
- **`ntdll.py`** — доступ к недокументированным NT Native API вызовам.
- **`etw.py`** — трассировка событий Windows (Event Tracing for Windows).
- **`error_decoder.py`** — декодирование системных ошибок Win32/NTSTATUS и BSOD Bugcheck кодов.
