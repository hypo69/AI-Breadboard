# 🪟 Архитектура AI Windows Diagnostic & Administration Center

## 📌 Обзор системы

Центр диагностики и администрирования Windows построен на основе **4-уровневой иерархии доступа к системным интерфейсам**, протокола безопасности **SafeOps** и слоя аналитического интеллекта (AI).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        AI WINDOWS DIAGNOSTIC & ADMINISTRATION CENTER                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│ Presentation/API │             │   AI & SafeOps   │             │   15 Коллекторов │
│ • CLI / TUI      │             │ • Diagnostician  │             │ • Clean/Drivers  │
│ • FastAPI REST   │             │ • Root-Cause     │             │ • Network/Sec    │
│ • Hardware Mon   │             │ • System Restore │             │ • SCM/Tasks/Disk │
└────────┬─────────┘             └────────┬─────────┘             └────────┬─────────┘
         │                                │                                │
         └────────────────────────────────┼────────────────────────────────┘
                                          │
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   НАТИВНЫЙ СЛОЙ WINDOWS API (apps/windows/api/)                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ • Tier 1 (Native Win32/NT): kernel32.dll, psapi.dll, advapi32.dll, iphlpapi.dll,      │
│                            setupapi.dll, cfgmgr32.dll, ntdll.dll, wevtapi.dll, pdh.dll │
│ • Tier 2 (COM API):        Schedule.Service, HNetCfg.FwPolicy2, INetworkListManager   │
│ • Tier 3 (WMI / CIM):      Win32_ShadowStorage, Win32_PnPEntity, Win32_Process        │
│ • Tier 4 (PowerShell/Safe): SafeOps fallback подпроцессы с ограничением прав            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Структура директории `apps/windows/`

```
apps/windows/
├── __init__.py                      # Регистрация приложения
├── README.md                        # Руководство пользователя и эндпоинты
├── ARCHITECTURE.md                  # Данная архитектурная спецификация
├── NATIVE_API_REGISTRY.md           # Полный реестр нативных функций Windows API
├── AUDIT_REPORT.md                  # Отчет аудита платформы
├── router.py                        # FastAPI REST API (20+ эндпоинтов)
├── cli.py                           # CLI интерфейс (python -m apps.windows)
├── tui.py                           # Rich TUI дашборд реального времени
│
├── api/                             # Низкоуровневые API wrappers
│   ├── scm.py                       # Service Control Manager (advapi32.dll)
│   ├── tasksched.py                 # Task Scheduler 2.0 COM API
│   ├── nethelper.py                 # IP Helper API (iphlpapi.dll)
│   ├── setupapi.py                  # SetupAPI & CfgMgr32 (PnP устройства)
│   ├── kernel32.py                  # Toolhelp32, снимки процессов, память
│   ├── psapi.py                     # Анализ рабочих наборов памяти и модулей
│   ├── advapi32.py                  # Реестр, токены и безопасность
│   ├── ntdll.py                     # Native NT API функции
│   ├── etw.py                       # Event Tracing for Windows
│   └── wevtapi.py                   # Windows Event Log API (wevtapi.dll)
│
├── core/                            # Ядро и безопасное управление
│   ├── system_param_manager.py      # Управление настройками системы с точками отката
│   ├── system_restore.py            # Создание точек восстановления и VSS-снимков
│   ├── safe_executor.py             # SafeOps Dry-Run симуляция и изоляция рисков
│   ├── root_cause_engine.py         # Движок расследования первопричин
│   ├── correlation_engine.py        # Междоменная корреляция фактов
│   ├── models.py                    # Нормализованные модели данных
│   └── modules/                     # 15 Доменных коллекторов фактов
│       ├── clean_collector.py       # (1) Очистка дисков и кэшей
│       ├── performance_collector.py # (2) Анализ CPU/RAM и автозагрузки
│       ├── driver_collector.py      # (3) Драйверы и PnP устройства (SetupAPI)
│       ├── software_collector.py    # (4) Инвентарь ПО
│       ├── integrity_collector.py   # (5) Целостность (SFC/DISM)
│       ├── storage_collector.py     # (6) Диски, тома, VSS хранилище
│       ├── security_collector.py    # (7) Defender, UAC, персистентность
│       ├── eventlog_collector.py    # (8) Корреляция журналов Event Log
│       ├── process_collector.py     # (9) Процессы и дескрипторы
│       ├── services_collector.py    # (10) Службы Windows (SCM)
│       ├── tasks_collector.py       # (11) Задачи планировщика (COM)
│       ├── network_collector.py     # (12) Сеть, сокеты, Firewall (IP Helper)
│       ├── update_collector.py      # (13) Центр обновления Windows
│       ├── baseline_collector.py    # (14) Конфигурационный эталон и Drift
│       └── postinstall_collector.py # (15) Post-install готовность ОС
│
├── ai/                              # Слой искусственного интеллекта
│   ├── diagnostician.py             # AI-диагност и расчет Health Score
│   ├── root_cause_analyzer.py       # Анализатор первопричин сбоев
│   └── prompt_templates.py          # Шаблоны промптов для моделей
│
└── hardware/                        # Аппаратный мониторинг в реальном времени
    ├── monitor.py                   # Сбор телеметрии датчиков, CPU, GPU, дисков
    └── sensors.py                   # Чтение показаний температуры, вольтажа, вентиляторов
```

---

## 🛡️ Безопасность и SafeOps

1. **Read-Only аудит**: все 15 коллекторов работают исключительно на чтение и не модифицируют систему.
2. **Точки восстановления (System Restore & VSS)**: перед применением любого чувствительного параметра создается точка отката в Windows.
3. **Локальные снимки (Immutable State Snapshots)**: при достижении системного лимита частоты точек восстановления параметры фиксируются в неизменяемом JSON.
4. **Dry-Run симуляция**: предварительный расчет эффектов перед внесением изменений.
