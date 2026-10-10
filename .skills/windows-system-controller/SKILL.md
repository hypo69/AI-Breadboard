---
name: windows-system-controller
description: Autonomous Windows OS diagnostics, full telemetry, powershell/ssh execution and management controller
description_i18n:
  en: Autonomous Windows OS diagnostics, full telemetry, powershell/ssh execution and management controller
  ru: Автономный полноправный контроллер Windows OS: диагностика, телеметрия, PowerShell/SSH и прямое управление через SDK
---

# 🖥️ Навык: Windows System Controller (Full Control & SDK Plane)

## 🎯 Назначение
Навык `windows-system-controller` наделяет модель и автономных агентов расширенными полномочиями прямого управления операционной системой Windows через единый стек `apps/windows/sdk` (`WindowsSDK`), а также предоставляет права на исполнение произвольных команд PowerShell, удаленное администрирование через SSH / WinRM, вызовы низкоуровневого C-FFI слоя и управление всеми системными доменами.

---

## 🏗️ Архитектура единого SDK (`apps/windows/sdk`)

Система организована в 5 полнофункциональных архитектурных слоев:

```
apps/windows/sdk/
├── native/                   # Слой 1: Нативный C-FFI доступ к системным Win32 DLL
│   ├── advapi32.py           # Токены безопасности, права, службы, реестр
│   ├── kernel32.py           # Память, процессы, потоки, дескрипторы
│   ├── psapi.py              # Память процессов, модули, системные драйверы
│   ├── pdh.py                # Счётчики производительности Performance Data Helper
│   ├── scm.py                # Service Control Manager (управление службами)
│   ├── setupapi.py           # PnP устройства, аппаратные ID (Device Classes)
│   ├── ntdll.py              # Нативные системные вызовы ядра NT (NtQuery*)
│   ├── wevtapi.py            # Windows Event Log API (журналы событий)
│   ├── tasksched.py          # COM/FFI интерфейс Task Scheduler
│   ├── nethelper.py          # Сетевые адаптеры, маршрутизация, TCP/UDP
│   ├── iphlpapi.py           # IP Helper API
│   └── etw.py                # Event Tracing for Windows
├── drivers/                  # Слой 2: Детекция оборудования, каталоги и загрузка драйверов
│   ├── gpu.py / vendor.py    # Определение GPU (NVIDIA / AMD / Intel)
│   └── downloader.py         # Загрузка и автоматическая установка драйверов
├── features/                 # Слой 3: Управление компонентами Windows (Optional Features)
│   └── manager.py            # Включение/отключение (OpenSSH, WSL2, Hyper-V, Sandbox)
├── core/                     # Слой 4: Ядро аналитики, SafeOps и системный каталог
│   ├── winapi.py             # Снимок системы (SystemState)
│   ├── safe_executor.py      # Безопасное исполнение с Preview / Dry-Run
│   ├── diagnostics.py        # Мультидоменная диагностика здоровья хоста
│   ├── correlation_engine.py # Корреляция сбоев и Root Cause Analysis (RCA)
│   ├── system_restore.py     # Точки восстановления Windows System Restore
│   ├── system_param_manager.py # Менеджер системных параметров ОС
│   ├── system32_catalog.py   # Каталог встроенных утилит System32
│   ├── atomic_capabilities.py # Реестр атомарных CLI команд Windows
│   ├── dynamic_tool_engine.py # Динамическая генерация и синтез инструментов
│   ├── tools/                # Встроенные умные инструменты (Collector, PowerShell Probe)
│   └── audits/               # 15 доменных коллекторов телеметрии
└── modules/                  # Слой 5: 29 доменных модулей администрирования
    ├── accounts_identity/    # Пользователи, группы, UAC, SID
    ├── backup_manager/       # Теневые копии тома VSS, бэкапы
    ├── boot_recovery/        # BCD конфигурация, Safe Mode, WinRE
    ├── defender/             # Windows Defender, защита в реальном времени, исключения
    ├── event_logs/           # Анализ журналов System, Security, Application, PowerShell
    ├── explorer_manager/     # Shell расширения, настройки Проводника
    ├── firewall_manager/     # Правила сетевого экрана, профили, порты
    ├── focus_policy/         # Уведомления, режим «Не беспокоить»
    ├── hardware/             # Сенсоры (CPU, GPU, RAM, материнская плата, LibreHardwareMonitor)
    ├── network/              # Адаптеры, IP, DNS, сокеты, таблица маршрутов
    ├── performance_tracing/  # Мониторинг узких мест и нагрузки
    ├── personalization/      # Темы, параметры рабочего стола
    ├── process_manager/      # Дерево процессов, приоритеты, affinity, завершение
    ├── programms_history_deep_researh/ # UserAssist, Prefetch, ShimCache, Amcache
    ├── registry/             # Чтение, поиск и безопасная запись в реестр
    ├── security_acl/         # Права доступа NTFS, дескрипторы безопасности SDDL, icacls
    ├── services_manager/     # Полный цикл управления системными службами
    ├── servicing_integrity/  # Целостность файлов SFC /scannow, восстановление DISM
    ├── shell_namespace/      # Системные папки CLSID, ярлыки
    ├── software_manager/     # Установленные Win32/UWP программы, Winget/Chocolatey
    ├── startup/              # Автозагрузка (Реестр, Папка Автозагрузка, Задачи)
    ├── storage_manager/      # Физические диски, тома, BitLocker, SMART
    ├── sysadmin/             # Мониторинг сессий, директорий, SSH / WinRM оркестрация
    ├── system_checkpoints/   # Контрольные точки конфигурации системы
    ├── system_control_center/# Централизованная панель управления и CLI
    ├── task_scheduler/       # Управление планировщиком заданий Windows
    ├── taskbar/              # Закрепление и настройка панели задач
    └── window_control_plane/ # Управление окнами, позиционирование, захват GUI
```

---

## ⚡ Расширенные полномочия агента (Full Administrative Authority)

Агенту предоставлены полномочия на выполнение следующих операций:

### 1. 💻 Прямое выполнение PowerShell и CMD
- Выполнение любых команд через `pwsh` или `powershell` (включая конвейеры, фильтры, конвертацию в JSON).
- Выполнение скриптов автоматизации, управление модулями PowerShell.
- Запуск диагностических и административных утилит Windows (`diskpart`, `bcdedit`, `dism`, `sfc`, `netsh`, `icacls`, `powercfg`, `wevtutil`, `schtasks`, `reg`).

### 2. 🔑 SSH, WinRM и удалённое управление
- Настройка и запуск службы `OpenSSH Server` (`sshd`) и клиента через `apps.windows.sdk.features`.
- Генерация и управление SSH-ключами (`ssh-keygen`, `authorized_keys`).
- Запуск удалённых команд и сессий через SSH (`ssh user@host "command"`) и WinRM (`Invoke-Command -ComputerName ...`).
- Управление сессиями пользователей и мониторинг подключений.

### 3. ⚙️ Низкоуровневый C-FFI и прямое управление ресурсами
- Прямой вызов Win32 API через `apps.windows.sdk.native` без накладных расходов командной оболочки.
- Управление службами через SCM (`Advapi32` / `scm.py`): запуск, остановка, смена типа запуска (`Automatic`, `Manual`, `Disabled`).
- Управление процессами: инспекция дескрипторов, потоков, изменение приоритетов (`HIGH_PRIORITY_CLASS`, `IDLE_PRIORITY_CLASS`), безопасное или принудительное завершение.
- Управление сетевым экраном (Брандмауэр): создание правил для портов, программ, протоколов.
- Управление безопасностью: аудит и настройка Windows Defender, антивирусных исключений и сканирования.

### 4. 🛡️ SafeOps и защита стабильности системы
- **Точки восстановления (System Restore)**: Автоматическое или ручное создание точек восстановления перед внесением системных правок (`windows_sdk.core.restore_manager.create_restore_point(...)`).
- **Dry-Run / Preview**: Предварительный расчет параметров и изменений до физического применения.
- **Rollback**: Мгновенный откат конфигурационных изменений из журнала истории.

---

## 🐍 Примеры работы через Python SDK Facade

```python
from apps.windows.sdk import windows_sdk

# 1. Сводка здоровья хоста
health = windows_sdk.get_health_summary()

# 2. Моментальный снимок процессов, памяти и служб
snapshot = windows_sdk.get_system_snapshot()

# 3. Управление службами через SDK
status = windows_sdk.modules.services.get_service_status("wuauserv")
windows_sdk.modules.services.restart_service("wuauserv")

# 4. Проверка и включение компонентов Windows (например, OpenSSH)
features = windows_sdk.features.get_features()
windows_sdk.features.enable_feature("OpenSSH.Server~~~~0.0.1.0")

# 5. Низкоуровневый аудит оборудования и накопителей
hardware = windows_sdk.modules.hardware.get_summary()
storage = windows_sdk.modules.storage.get_disks_summary()
```

---

## 🛠️ Нативные инструменты агента (LangChain / SDK Tools)

Агент оснащен полным набором инструментов:
- `windows_collector_audit` — сбор глубокой телеметрии и аудит 15 системных доменов
- `windows_execute_atomic_op` — выполнение проверенных атомарных утилит Windows
- `windows_manage_service` — управление системными службами (статус, запуск, остановка, автозапуск)
- `windows_manage_process` — инспекция и завершение процессов по протоколу SafeOps
- `windows_manage_restore_point` — создание и управление точками восстановления системы
- `windows_manage_sys_param` — безопасное управление параметрами реестра и SafeOps
- `windows_safe_probe` — безопасные PowerShell / WMI / CIM зонды с автоконвертацией в JSON
- `windows_execute_powershell` — прямое выполнение командлетов и скриптов PowerShell
- `windows_manage_optional_feature` — управление компонентами Windows DISM / Optional Features

---

## 🛠️ Нативные инструменты агента (LangChain / SDK Tools)

Агент оснащен полным набором инструментов:
- `windows_collector_audit` — сбор глубокой телеметрии и аудит 15 системных доменов
- `windows_execute_atomic_op` — выполнение проверенных атомарных утилит Windows
- `windows_manage_service` — управление системными службами (статус, запуск, остановка, автозапуск)
- `windows_manage_process` — инспекция и завершение процессов по протоколу SafeOps
- `windows_manage_restore_point` — создание и управление точками восстановления системы
- `windows_manage_sys_param` — безопасное управление параметрами реестра и SafeOps
- `windows_safe_probe` — безопасные PowerShell / WMI / CIM зонды с автоконвертацией в JSON
- `windows_execute_powershell` — прямое выполнение командлетов и скриптов PowerShell
- `windows_manage_optional_feature` — управление компонентами Windows DISM / Optional Features

---

## 🚀 Протокол выполнения задач
1. **Анализ задачи**: Определить целевой слой (`native`, `core`, `features`, `drivers`, `modules` или прямой `PowerShell`/`SSH`).
2. **Безопасность**: Для рискованных изменений создать точку восстановления Windows.
3. **Исполнение**: Выполнить операцию через соответствующий модуль SDK или инструмент командной строки.
4. **Верификация**: Проверить код возврата, статус служб/компонентов и вернуть пользователю структурированный отчет на русском языке.
