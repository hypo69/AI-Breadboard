# Roadmap рефакторинга кодовой базы AI Windows Diagnostic & Administration Center

## 🎯 Обзор и архитектурные цели

Настоящий дорожный план (Roadmap) определяет пошаговую стратегию трансформации монолитной структуры подсистемы диагностики Windows 64-bit в масштабируемую, чистую и высокопроизводительную трехслойную архитектуру (`telemetry`, `core`, `services`).

### Ключевые метрики успеха рефакторинга:
1. **Устранение накладных расходов**: Замена синхронного запуска процесса `powershell.exe` на прямое исполнение WinAPI/Ctypes оберток в критических точках сбора телеметрии (снижение задержки вызова с 500–1500 мс до <5 мс).
2. **Четкое разделение ответственности (SoC)**: Разграничение слоя сбора сырых фактов (`telemetry`), слоя вычислительной эвристики и анализа (`core`), а также внешних адаптеров и AI-агентов (`services`).
3. **Оптимизация RAM и CPU**: Внедрение TTL-кэширования и устранение дублирующих проходов по реестру (`Uninstall`, `UserAssist`, `Prefetch`) и дисковым артефактам.

---

## 🏗️ Целевая трехслойная архитектура

```text
apps/windows/
├── telemetry/                      # 1. СЛОЙ СБОРА ДАННЫХ И LOW-LEVEL FFI
│   ├── api_bindings/               # Ctypes обертки Win32 (kernel32, advapi32, wevtapi, setupapi, iphlpapi, scm, tasksched)
│   ├── collectors/                 # Сгруппированные доменные коллекторы (execution, health, resources)
│   ├── models.py                   # Канонические DTO метрик и событий (TelemetrySnapshot, SensorReading)
│   └── service.py                  # TelemetryBus с поддержкой многоуровневого TTL-кэширования
│
├── core/                           # 2. ЧИСТОЕ ЯДРО (Бизнес-логика, эвристика, расследование)
│   ├── engine/                     # Аналитические движки
│   │   ├── root_cause_engine.py    # Корреляция инцидентов и цепочки улик (evidence_chain)
│   │   ├── diagnostics_engine.py   # Вычисление Health Score и 80+ эвристических проверок
│   │   └── correlation_engine.py   # Построение графов связей (Process <-> Socket <-> Service <-> Handle)
│   ├── software/                   # SoftwareIntelligenceEngine (Uninstall, UserAssist, Prefetch, Transparency)
│   ├── startup/                    # Анализ персистентности (Run, IFEO, WMI Subscriptions, Task Scheduler)
│   ├── security/                   # Логика безопасности (UAC, Defender Rules, ASR, CFA, Exclusions)
│   └── safeops/                    # Безопасные изменения (SafeExecutor, SystemParamManager, VSS Snapshots)
│
└── services/                       # 3. ВНЕШНИЕ СЕРВИСЫ И ИНТЕРФЕЙСЫ
    ├── ai/                         # LLM Orch/Reasoning (AIDiagnostician, Prompts, Dynamic Tool Planner)
    ├── rag/                        # RAG подсистема (AdaptiveLogRAG, FileHistoryRAG)
    ├── backup/                     # Менеджер резервного копирования и истории файлов
    ├── hardware/                   # HardwareTelemetryService (Единый фасад для всех внешних утилит и SMI)
    └── interfaces/                 # Точки входа (FastAPI Routers, Rich TUI, CLI)
```

---

## 📅 Пофазовый план реализации

### Фаза 1: Выделение слоя Telemetry & FFI (`apps/windows/telemetry`)
**Приоритет:** Высокий | **Срок:** Неделя 1

#### Задачи:
- [ ] **1.1 Миграция Ctypes-оберток**:
  - Перенести все системные FFI-бииндинги из `apps/windows/api/*` (`wevtapi.py`, `advapi32.py`, `kernel32.py`, `psapi.py`, `setupapi.py`, `nethelper.py`, `scm.py`, `tasksched.py`, `etw.py`) в `apps/windows/telemetry/api_bindings/`.
  - Очистить FFI-модули от строковых констант с описаниями на русском языке и высокоуровневой бизнес-логики.
- [ ] **1.2 Консолидация 15 мелких доменных коллекторов**:
  - Сгруппировать 15 индивидуальных файлов из `apps/windows/core/modules/*` в 3 сбалансированных модуля:
    - `execution_collectors.py`: `ProcessCollector`, `ServicesCollector`, `TasksCollector`.
    - `system_health_collectors.py`: `IntegrityCollector`, `UpdateCollector`, `CleanCollector`, `PostInstallCollector`, `EventLogCollector`, `SecurityCollector`.
    - `resource_collectors.py`: `PerformanceCollector`, `StorageCollector`, `NetworkCollector`, `DriverCollector`, `FileActivityCollector`, `LogDiscoveryEngine`.
- [ ] **1.3 Реализация `TelemetryBus` и TTL-кэширования**:
  - Создать единый сервисный шин-класс `TelemetryBus` в `telemetry/service.py`.
  - Настроить политику инвалидации кэша:
    - *Динамические метрики (CPU/RAM/Net)*: TTL **1 секунда**.
    - *Полустатические метрики (Process Tree, Services, Open Sockets)*: TTL **10 секунд**.
    - *Статические метрики (Installed Software, Drivers, OS Version)*: TTL **300+ секунд**.

---

### Фаза 2: Рефакторинг и декомпозиция ядра (`apps/windows/core`)
**Приоритет:** Высокий | **Срок:** Неделя 2

#### Задачи:
- [ ] **2.1 Декомпозиция `RootCauseEngine`**:
  - Извлечь логику создания и вызова коллекторов из `RootCauseEngine.__init__`.
  - Создать класс `CollectorRegistry` для управления подписками и порядком запуска коллекторов.
  - Оставить в `RootCauseEngine` только логику построения цепочек доказательств (`evidence_chain`), корреляции симптомов и вычисления показателей `HealthScore`.
- [ ] **2.2 Разделение `DynamicWindowsToolEngine`**:
  - Разбить монолитный `dynamic_tool_engine.py` на три класса:
    - `ToolPlanner`: семантический анализ запроса пользователя и построение плана зондирования (`DynamicToolPlan`).
    - `ToolExecutor`: безопасный запуск сформированных PowerShell-скриптов или коллекторов через `ToolRegistry`.
    - `ToolReportSynthesizer`: построение финального отчета и интеграция с LLM.
- [ ] **2.3 Создание `SoftwareIntelligenceEngine`**:
  - Объединить функционал `SoftwareAuditEngine` (`software_audit.py`) и `StartupScanner` (`apps/windows/startup`).
  - Реализовать однократный проход по реестру (`HKLM/HKCU Uninstall`, `Run`, `RunOnce`, `IFEO`) с параллельным декодированием артефактов `UserAssist` (ROT13) и `Prefetch`.

---

### Фаза 3: Консолидация сопутствующих сервисов (`apps/windows/services`)
**Приоритет:** Средний | **Срок:** Неделя 3

#### Задачи:
- [ ] **3.1 Объединение дублирующих RAG-подсистем**:
  - Слить модули `apps.windows.backup_manager.core.file_history_rag` и `apps.windows.file_history_ai_search` в единый сервис `services/rag/file_history_rag.py`.
  - Унифицировать модели чанков и векторов.
- [ ] **3.2 Единый фасад оборудования `HardwareTelemetryService`**:
  - Объединить разрозненные провайдеры (`NativeWinProvider`, `HwinfoProvider`, `Aida64Provider`, `LhmProvider`), `GpuProber`, `LhmService` и `storage_sensors` под единым фасадом `services/hardware/hardware_service.py`.
  - Обеспечить фоновый опрос датчиков через единственный поток с сохранением результатов в `TelemetryBus`.
- [ ] **3.3 Выделение AI Layer**:
  - Перенести `WindowsAIDiagnostician`, `WindowsAIRootCauseAnalyzer` и подсистему генерации промптов в `services/ai/`.

---

### Фаза 4: Обновление точек входа, API и тестирование (`apps/windows/interfaces`)
**Приоритет:** Средний | **Срок:** Неделя 4

#### Задачи:
- [ ] **4.1 Рефакторинг FastAPI Routers**:
  - Перевести все эндпоинты (`router.py`, `defender`, `sysadmin`, `registry`, `startup`) на получение данных исключительно через `TelemetryBus` и методы ядра `CoreEngine`.
  - Исключить прямые импорты низкоуровневых коллекторов из HTTP-роутеров.
- [ ] **4.2 Обновление интерфейсов Rich TUI & CLI**:
  - Переписать консольные дашборды для работы с обновленным `HardwareTelemetryService` и `TelemetryBus`.
- [ ] **4.3 Интеграционное тестирование**:
  - Написать сквозные тесты на проверку скорости работы сбора телеметрии без PowerShell.
  - Проверить корректность генерации итогового `FullAuditReport` при отсоединении отдельных подсистем.

---

## 📊 Матрица миграции компонентов

| Старый путь / модуль | Новый целевой модуль | Ответственность |
| :--- | :--- | :--- |
| `apps/windows/api/*.py` | `apps/windows/telemetry/api_bindings/` | Чистые FFI Win32 API обертки |
| `apps/windows/core/modules/*_collector.py` | `apps/windows/telemetry/collectors/` | Агрегированные коллекторы фактов |
| `apps/windows/core/root_cause_engine.py` | `apps/windows/core/engine/root_cause_engine.py` | Чистый движок расследований |
| `apps/windows/core/tools/dynamic_tool_engine.py` | `apps/windows/core/engine/dynamic_tool_engine.py` | Декомпозированный планер и исполнитель зондов |
| `apps/windows/core/software_audit.py` + `startup` | `apps/windows/core/software/` | Единый аудит ПО и автозапуска |
| `file_history_rag` + `file_history_ai_search` | `apps/windows/services/rag/file_history_rag.py` | Единый векторный поиск по файлам |
| `hardware/providers` + `gpu_prober` + `lhm` | `apps/windows/services/hardware/` | Аппаратный фасад и интеграции |
