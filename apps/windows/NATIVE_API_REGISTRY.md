# 🪟 Реестр нативных функций Windows API (Native API Registry)

Данный документ представляет собой **техническую карту программного доступа к Windows** для всех подсистем AI-Breadboard и Windows Diagnostic & Administration Center.

Каждый компонент анализируется через 4 уровня взаимодействия:
1. **Native Windows API (Win32, NT API, специализированные DLL)** — основной высокопроизводительный уровень.
2. **COM-интерфейсы** — компонентная модель Windows.
3. **WMI/CIM-классы** — слой структурированных системных запросов.
4. **PowerShell-командлеты** — интерфейс сценариев и автоматизации.
5. **Python-интеграция** — `ctypes`, `win32com.client`, `pywin32`, `wmi`.

---

## 📑 Содержание

1. [Управление процессами и потоками (Processes & Threads)](#1-управление-процессами-и-потоками)
2. [Управление системными службами (Windows Services / SCM)](#2-управление-системными-службами-windows-services--scm)
3. [Планировщик заданий (Task Scheduler 2.0)](#3-планировщик-заданий-task-scheduler-20)
4. [Журналы событий (Windows Event Log)](#4-журналы-событий-windows-event-log)
5. [Оборудование и устройства (Device Manager / PnP)](#5-оборудование-и-устройства-device-manager--pnp)
6. [Диски, тома и VSS (Storage, Volumes & Shadow Copies)](#6-диски-тома-и-vss)
7. [Сеть и сетевой стек (Network & IP Helper)](#7-сеть-и-сетевой-стек)
8. [Брандмауэр Windows (Windows Firewall & Filtering Platform)](#8-брандмауэр-windows)
9. [Реестр Windows (Windows Registry)](#9-реестр-windows)
10. [Точки восстановления и теневые копии (System Restore & VSS)](#10-точки-восстановления-и-теневые-копии)
11. [Мониторинг производительности (Performance Monitoring & PDH)](#11-мониторинг-производительности)
12. [Пользователи, сессии и безопасность (Users, SAM & Tokens)](#12-пользователи-сессии-и-безопасность)

---

## 1. Управление процессами и потоками

### Схема Native API
```text
Process Management
│
├── Перечисление процессов и снапшоты
│   ├── CreateToolhelp32Snapshot (kernel32.dll)
│   ├── Process32FirstW / Process32NextW (kernel32.dll)
│   ├── EnumProcesses (psapi.dll)
│   └── NtQuerySystemInformation (SystemProcessInformation) (ntdll.dll)
│
├── Доступ и идентификация процесса
│   ├── OpenProcess (PROCESS_QUERY_INFORMATION | PROCESS_VM_READ)
│   ├── QueryFullProcessImageNameW (kernel32.dll)
│   ├── GetProcessTimes (kernel32.dll)
│   └── GetProcessId (kernel32.dll)
│
├── Анализ памяти и дескрипторов
│   ├── GetProcessMemoryInfo (psapi.dll)
│   ├── VirtualQueryEx (kernel32.dll)
│   ├── GetProcessHandleCount (kernel32.dll)
│   └── NtQueryInformationProcess (ProcessHandleInformation) (ntdll.dll)
│
├── Потоки (Threads)
│   ├── Thread32First / Thread32Next (kernel32.dll)
│   ├── OpenThread (kernel32.dll)
│   └── GetThreadTimes (kernel32.dll)
│
└── Токены и безопасность
    ├── OpenProcessToken (advapi32.dll)
    └── GetTokenInformation (advapi32.dll)
```

| Функция API | DLL | Сигнатура / Назначение | Необходимые права | COM / WMI | PowerShell | Python вызов |
|---|---|---|---|---|---|---|
| `CreateToolhelp32Snapshot` | `kernel32.dll` | `HANDLE (DWORD dwFlags, DWORD th32ProcessID)` — снимок процессов/потоков | Обычные | `Win32_Process` | `Get-Process` | `ctypes.windll.kernel32.CreateToolhelp32Snapshot` |
| `Process32FirstW` / `NextW` | `kernel32.dll` | `BOOL (HANDLE hSnapshot, LPPROCESSENTRY32W lppe)` | Обычные | `Win32_Process` | `Get-Process` | `ctypes.windll.kernel32.Process32NextW` |
| `EnumProcesses` | `psapi.dll` | `BOOL (DWORD *pProcessIds, DWORD cb, DWORD *pBytesReturned)` | Обычные | `Win32_Process` | `Get-Process` | `ctypes.windll.psapi.EnumProcesses` |
| `GetProcessMemoryInfo` | `psapi.dll` | `BOOL (HANDLE hProcess, PPROCESS_MEMORY_COUNTERS, DWORD cb)` | `PROCESS_QUERY_INFORMATION` | `Win32_PerfFormattedData_PerfProc_Process` | `Get-Process \| select WS` | `ctypes.windll.psapi.GetProcessMemoryInfo` |
| `NtQuerySystemInformation` | `ntdll.dll` | `NTSTATUS (SYSTEM_INFORMATION_CLASS, PVOID, ULONG, PULONG)` | Обычные / Admin | `Win32_Process` | `Get-CimInstance Win32_Process` | `ctypes.windll.ntdll.NtQuerySystemInformation` |

---

## 2. Управление системными службами (Windows Services / SCM)

### Схема Native API
```text
Service Control Manager (SCM)
│
├── Управление базой SCM
│   ├── OpenSCManagerW (advapi32.dll)
│   ├── EnumServicesStatusExW (advapi32.dll)
│   └── CloseServiceHandle (advapi32.dll)
│
├── Запросы конфигурации и статуса
│   ├── OpenServiceW (advapi32.dll)
│   ├── QueryServiceStatusEx (advapi32.dll)
│   ├── QueryServiceConfigW (advapi32.dll)
│   └── EnumDependentServicesW (advapi32.dll)
│
└── Управление состоянием
    ├── StartServiceW (advapi32.dll)
    ├── ControlService (SERVICE_CONTROL_STOP, etc.) (advapi32.dll)
    └── ChangeServiceConfigW (advapi32.dll)
```

| Функция API | DLL | Назначение | Права | COM / WMI | PowerShell | Python вызов |
|---|---|---|---|---|---|---|
| `OpenSCManagerW` | `advapi32.dll` | Открытие дескриптора Service Control Manager | `SC_MANAGER_ENUMERATE_SERVICE` | `Win32_Service` | `Get-Service` | `ctypes.windll.advapi32.OpenSCManagerW` |
| `EnumServicesStatusExW` | `advapi32.dll` | Пакетное перечисление всех служб и их PID/состояний за 1 вызов | Обычные | `Win32_Service` | `Get-Service` | `apps.windows.api.scm.ServiceControlManager` |
| `QueryServiceConfigW` | `advapi32.dll` | Получение BinaryPathName, StartType, ServiceAccount | Обычные | `Win32_Service` | `Get-CimInstance Win32_Service` | `apps.windows.api.scm.ServiceControlManager` |
| `ControlService` | `advapi32.dll` | Остановка, пауза, отправка управляющего сигнала | `SERVICE_STOP` / Admin | Метод `StopService()` в WMI | `Stop-Service` | `ctypes.windll.advapi32.ControlService` |

---

## 3. Планировщик заданий (Task Scheduler 2.0)

### Схема COM & Native API
```text
Task Scheduler 2.0
│
├── COM Root Object: CLSID_TaskScheduler / "Schedule.Service"
│   ├── ITaskService::Connect()
│   ├── ITaskService::GetFolder(path) -> ITaskFolder
│   └── ITaskService::NewTask()
│
├── Навигация по папкам и задачам
│   ├── ITaskFolder::GetTasks() -> IRegisteredTaskCollection
│   ├── ITaskFolder::GetFolders() -> ITaskFolderCollection
│   └── IRegisteredTask::get_Definition() -> ITaskDefinition
│
└── Анализ действий и триггеров
    ├── ITaskDefinition::get_Actions() -> IActionCollection (ExecAction)
    ├── ITaskDefinition::get_Triggers() -> ITriggerCollection
    └── IRegisteredTask::get_State(), get_LastRunTime(), get_LastTaskResult()
```

| Интерфейс / Метод | Уровень | Назначение | Права | WMI / PowerShell | Python вызов |
|---|---|---|---|---|---|
| `Schedule.Service` | COM API 2.0 | Инициализация сервиса планировщика | Обычные | `Get-ScheduledTask` | `win32com.client.Dispatch("Schedule.Service")` |
| `ITaskFolder::GetTasks` | COM API 2.0 | Рекурсивный сбор всех зарегистрированных заданий | Обычные | `Get-ScheduledTask` | `apps.windows.api.tasksched.TaskSchedulerAPI` |
| `IExecAction::get_Path` | COM API 2.0 | Получение исполняемого пути и скрытых аргументов | Обычные | `Get-ScheduledTask \| % Actions` | `apps.windows.api.tasksched.TaskSchedulerAPI` |

---

## 4. Журналы событий (Windows Event Log)

### Схема Native API
```text
Windows Event Log API (wevtapi.dll)
│
├── Перечисление каналов и провайдеров
│   ├── EvtOpenChannelEnum
│   ├── EvtNextChannelPath
│   └── EvtOpenPublisherEnum
│
├── Выборка и фильтрация событий (XPath / XML Query)
│   ├── EvtQuery (EvtQueryChannelPath, EvtQueryReverseDirection)
│   ├── EvtNext (пакетное чтение буфера дескрипторов событий)
│   └── EvtClose
│
└── Рендеринг и подписка
    ├── EvtRender (EvtRenderEventXml) -> быстрый XML парсинг
    ├── EvtFormatMessage (получение локализованного текста ошибки)
    └── EvtSubscribe (потоковая подписка в реальном времени)
```

| Функция API | DLL | Назначение | Права | WMI / PowerShell | Python вызов |
|---|---|---|---|---|---|
| `EvtQuery` | `wevtapi.dll` | Высокоскоростной запрос событий по XPath | Обычные (System/App), Admin (Security) | `Get-WinEvent` | `apps.windows.api.wevtapi.WevtAPI` |
| `EvtNext` | `wevtapi.dll` | Итерация по дескрипторам событий | Обычные | `Get-WinEvent` | `apps.windows.api.wevtapi.WevtAPI` |
| `EvtRender` | `wevtapi.dll` | Преобразование бинарного события в структурированный XML | Обычные | `Get-WinEvent` | `apps.windows.api.wevtapi.WevtAPI` |

---

## 5. Оборудование и устройства (Device Manager / PnP)

### Схема Native API
```text
Device & PnP Architecture
│
├── SetupAPI (setupapi.dll)
│   ├── SetupDiGetClassDevsW (DIGCF_ALLCLASSES | DIGCF_PRESENT)
│   ├── SetupDiEnumDeviceInfo (SP_DEVINFO_DATA)
│   ├── SetupDiGetDeviceRegistryPropertyW (SPDRP_FRIENDLYNAME, SPDRP_HARDWAREID)
│   └── SetupDiDestroyDeviceInfoList
│
└── Configuration Manager (cfgmgr32.dll)
    ├── CM_Get_DevNode_Status (проверка статуса DN_HAS_PROBLEM, DN_STARTED)
    ├── CM_Get_Device_IDW
    └── CM_Reenumerate_DevNode
```

| Функция API | DLL | Назначение | Права | WMI / PowerShell | Python вызов |
|---|---|---|---|---|---|
| `SetupDiGetClassDevsW` | `setupapi.dll` | Получение дескриптора списка PnP оборудования | Обычные | `Win32_PnPEntity` | `apps.windows.api.setupapi.SetupAPI` |
| `SetupDiEnumDeviceInfo` | `setupapi.dll` | Перечисление элементов устройств | Обычные | `Get-PnpDevice` | `apps.windows.api.setupapi.SetupAPI` |
| `CM_Get_DevNode_Status` | `cfgmgr32.dll` | Чтение флагов статуса и кода ошибки (Code 10, 43, 28) | Обычные | `ProblemCode` в WMI | `apps.windows.api.setupapi.SetupAPI` |

---

## 6. Диски, тома и VSS (Storage, Volumes & Shadow Copies)

### Схема Native API
```text
Storage & Volume Management
│
├── Win32 File/Volume APIs (kernel32.dll)
│   ├── GetDiskFreeSpaceExW (свободное место, квоты)
│   ├── GetVolumeInformationW (метка, файловая система NTFS/ReFS, серийный номер)
│   ├── GetLogicalDriveStringsW / GetDriveTypeW (DRIVE_FIXED, DRIVE_REMOVABLE)
│   └── FindFirstVolumeW / FindNextVolumeW / FindVolumeClose
│
├── Device I/O Control (kernel32.dll)
│   └── DeviceIoControl (IOCTL_STORAGE_QUERY_PROPERTY, IOCTL_DISK_GET_DRIVE_GEOMETRY_EX)
│
└── VSS (Volume Shadow Copy Service COM API & WMI)
    ├── VSS Requester Interfaces (vssapi.dll)
    └── WMI: Win32_ShadowCopy, Win32_ShadowStorage
```

| Функция / Интерфейс | DLL / Подсистема | Назначение | Права | PowerShell | Python вызов |
|---|---|---|---|---|---|
| `GetDiskFreeSpaceExW` | `kernel32.dll` | Быстрый опрос свободного/общего места | Обычные | `Get-PSDrive` | `ctypes.windll.kernel32.GetDiskFreeSpaceExW` |
| `GetVolumeInformationW` | `kernel32.dll` | Проверка типа ФС (NTFS/ReFS/FAT32) и флагов | Обычные | `Get-Volume` | `ctypes.windll.kernel32.GetVolumeInformationW` |
| `Win32_ShadowStorage` | WMI / CIM | Контроль выделенного объема теневых копий | Admin | `Get-CimInstance Win32_ShadowStorage` | `apps.windows.core.system_restore.WindowsSystemRestoreManager` |

---

## 7. Сеть и сетевой стек (Network & IP Helper)

### Схема Native API
```text
Network Intelligence & Sockets
│
├── IP Helper API (iphlpapi.dll)
│   ├── GetExtendedTcpTable (TCP_TABLE_OWNER_PID_ALL, TCP_TABLE_OWNER_MODULE_ALL)
│   ├── GetExtendedUdpTable (UDP_TABLE_OWNER_PID)
│   ├── GetAdaptersAddresses (AF_UNSPEC, GAA_FLAG_INCLUDE_GATEWAYS)
│   └── GetNetworkParams (DNS серверы, домен, хост)
│
├── COM Network List Manager (netprofm.dll)
│   ├── INetworkListManager::GetNetworks(NLM_ENUM_NETWORK_CONNECTED)
│   └── INetwork::IsConnectedToInternet()
│
└── Windows Filtering Platform (WFP / fwpmu.dll)
    ├── FwpmEngineOpen0
    └── FwpmFilterEnum0
```

| Функция API | DLL | Назначение | Права | WMI / PowerShell | Python вызов |
|---|---|---|---|---|---|
| `GetExtendedTcpTable` | `iphlpapi.dll` | Мгновенный сбор всех открытых TCP сокетов со связкой с PID | Обычные | `Get-NetTCPConnection` | `apps.windows.api.nethelper.IPHelperAPI` |
| `GetExtendedUdpTable` | `iphlpapi.dll` | Мгновенный сбор всех UDP сокетов с PID | Обычные | `Get-NetUDPEndpoint` | `apps.windows.api.nethelper.IPHelperAPI` |
| `GetAdaptersAddresses` | `iphlpapi.dll` | Полная инвентаризация сетевых интерфейсов, MAC, IPv4/IPv6, MTU | Обычные | `Get-NetAdapter` | `apps.windows.api.nethelper.IPHelperAPI` |
| `INetworkListManager` | COM | Проверка статуса интернета и профиля сети (Private/Public) | Обычные | `Get-NetConnectionProfile` | `win32com.client.Dispatch("{DCB00C01-570F-4A9B-8D69-199FDBA5723B}")` |

---

## 8. Брандмауэр Windows (Windows Firewall)

### Схема API
```text
Windows Firewall Management
│
├── COM API: "HNetCfg.FwPolicy2"
│   ├── INetFwPolicy2::get_Rules() -> INetFwRules
│   ├── INetFwPolicy2::get_FirewallEnabled(NET_FW_PROFILE2_DOMAIN/PRIVATE/PUBLIC)
│   └── INetFwRules::Item(name) / Add(rule) / Remove(name)
│
└── PowerShell NetSecurity Module
    ├── Get-NetFirewallProfile
    ├── Get-NetFirewallRule
    └── Set-NetFirewallProfile
```

| Интерфейс | Уровень | Назначение | Права | PowerShell | Python вызов |
|---|---|---|---|---|---|
| `HNetCfg.FwPolicy2` | COM API | Чтение и аудит всех правил файрвола, профилей и блокировок | Обычные (чтение) / Admin (изменение) | `Get-NetFirewallRule` | `win32com.client.Dispatch("HNetCfg.FwPolicy2")` |

---

## 9. Реестр Windows (Windows Registry)

### Схема Native API
```text
Registry Subsystem (advapi32.dll / winreg)
│
├── Открытие и навигация
│   ├── RegOpenKeyExW (KEY_READ | KEY_WOW64_64KEY)
│   ├── RegCreateKeyExW
│   └── RegCloseKey
│
├── Чтение и перечисление
│   ├── RegQueryValueExW (REG_SZ, REG_DWORD, REG_MULTI_SZ, REG_EXPAND_SZ)
│   ├── RegEnumKeyExW (перебор подразделов)
│   └── RegEnumValueW (перебор параметров)
│
└── Безопасная запись (SafeOps)
    ├── RegSetValueExW
    └── RegDeleteValueW
```

| Функция API | Модуль | Назначение | Права | PowerShell | Python вызов |
|---|---|---|---|---|---|
| `RegOpenKeyExW` | `advapi32.dll` / `winreg` | Чтение системных параметров HKLM / HKCU | Обычные | `Get-ItemProperty` | `winreg.OpenKey` / `apps.windows.api.advapi32.AdvAPI32` |
| `RegQueryValueExW` | `advapi32.dll` / `winreg` | Считывание значений ключей реестра | Обычные | `Get-ItemPropertyValue` | `winreg.QueryValueEx` |

---

## 10. Точки восстановления и теневые копии (System Restore & VSS)

### Схема API
```text
System Protection & VSS
│
├── System Restore API & PowerShell
│   ├── Checkpoint-Computer (создание точки отката)
│   ├── Get-ComputerRestorePoint (инвентаризация точек)
│   └── Disable-ComputerRestore / Enable-ComputerRestore
│
└── VSS / CIM
    ├── Win32_ShadowStorage (контроль лимита места VSS)
    └── Win32_ShadowCopy (инспекция снимков томов)
```

| Компонент | Уровень | Назначение | Права | Python реализация |
|---|---|---|---|---|
| `WindowsSystemRestoreManager` | WMI + PowerShell + Immutable Snapshots | Проверка защиты, управление точками отката и теневым хранилищем | Admin | `apps.windows.core.system_restore.WindowsSystemRestoreManager` |

---

## 11. Мониторинг производительности (Performance Monitoring & PDH)

### Схема Native API
```text
Performance Subsystem
│
├── Performance Data Helper (pdh.dll)
│   ├── PdhOpenQueryW
│   ├── PdhAddCounterW ("\Processor(_Total)\% Processor Time")
│   ├── PdhCollectQueryData
│   ├── PdhGetFormattedCounterValue (PDH_FMT_DOUBLE / PDH_FMT_LONG)
│   └── PdhCloseQuery
│
└── Query Performance Counters (kernel32.dll)
    ├── QueryPerformanceCounter (высокоточный системный таймер)
    └── QueryPerformanceFrequency
```

| Функция API | DLL | Назначение | Права | WMI / PowerShell | Python вызов |
|---|---|---|---|---|---|
| `PdhOpenQueryW` / `PdhCollectQueryData` | `pdh.dll` | Нативный сбор аппаратных счетчиков загрузки без WMI накладных расходов | Обычные | `Get-Counter` | `ctypes.windll.pdh.PdhOpenQueryW` |
| `QueryPerformanceCounter` | `kernel32.dll` | Микросекундный замер длительности системных операций | Обычные | `[System.Diagnostics.Stopwatch]` | `ctypes.windll.kernel32.QueryPerformanceCounter` |

---

## 12. Пользователи, сессии и безопасность (Users, SAM & Tokens)

### Схема Native API
```text
Security, Users & Tokens
│
├── Access Tokens (advapi32.dll)
│   ├── OpenProcessToken (TOKEN_QUERY | TOKEN_ADJUST_PRIVILEGES)
│   ├── GetTokenInformation (TokenUser, TokenGroups, TokenPrivileges, TokenElevation)
│   └── LookupAccountSidW / LookupPrivilegeValueW
│
├── Local Security Authority (LSA) & NetAPI32 (netapi32.dll)
│   ├── NetUserEnum / NetUserGetInfo
│   ├── NetLocalGroupEnum / NetLocalGroupGetMembers
│   └── WTSQuerySessionInformationW (wtsapi32.dll — активные сессии RDP/консоли)
```

| Функция API | DLL | Назначение | Права | WMI / PowerShell | Python вызов |
|---|---|---|---|---|---|
| `GetTokenInformation` | `advapi32.dll` | Определение прав (Admin, Elevation type, SeDebugPrivilege) | Обычные | `whoami /priv` | `apps.windows.api.advapi32.AdvAPI32` |
| `WTSQuerySessionInformationW` | `wtsapi32.dll` | Перечисление интерактивных и RDP сессий | Обычные / Admin | `quser` / `Get-LocalUser` | `ctypes.windll.wtsapi32.WTSQuerySessionInformationW` |

---

## 🛡️ Политика отказоустойчивости и каскадирования (Cascade Fallback Policy)

Каждый доменный модуль в платформе следует правилу:
1. **Tier 1 (Native WinAPI / Ctypes)**: Попытка прямого вызова DLL (время выполнения < 5мс).
2. **Tier 2 (COM API)**: Использование зарегистрированных COM-серверов (`Schedule.Service`, `HNetCfg.FwPolicy2`).
3. **Tier 3 (WMI / CIM)**: Запрос к репозиторию CIM/WMI через WMI API.
4. **Tier 4 (PowerShell / SafeOps)**: Запуск безопасного подпроцесса с таймаутом при отсутствии низкоуровневых интерфейсов.
