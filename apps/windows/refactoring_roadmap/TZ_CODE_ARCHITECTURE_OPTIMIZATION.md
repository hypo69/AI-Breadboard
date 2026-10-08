# Техническое задание: Архитектурная реорганизация и оптимизация кодовой базы AI-Breadboard

## 1. Общие положения и цели проекта

Настоящее техническое задание (ТЗ) определяет порядок проведения комплексного архитектурного рефакторинга и реорганизации кодовой базы платформы **AI-Breadboard Windows Diagnostic & Administration Center** (`apps.windows`).

### 1.1. Цели оптимизации
* **Устранение циклических зависимостей**: Ликвидация взаимных блокировок при импортах модулей и полный отказ от использования динамических ленивых хаков через `__getattr__` в инициализаторах пакетов.
* **Переход к слоистой архитектуре (Clean Layered Architecture)**: Четкое разделение ответственности между нативным Win32 C-FFI слоем, DTO-контрактами, ядрами телеметрии, исполнительными аудиторами, ИИ-сервисами и REST API.
* **Стандартизация DTO и контрактов**: Объединение разрозненных файлов моделей (`data_model.py`, `models.py`, `atomic_models.py`, `system32_models.py`) в единый пакет нулевой зависимости `apps.windows.contracts`.
* **Автоматизация API-слоя**: Замена 500-строчной цепочки ручной регистрации роутеров в `FastAPI` на динамический изолированный механизм Auto-Discovery.
* **Слияние подсистем телеметрии**: Объединение коллекторов `telemetry` и аналитического подпакета `telemetry_research` в единую модульную структуру без прокси-оберток обратной совместимости.

---

## 2. Анализ текущего состояния и архитектурные дефекты

На основе аудита кодовой базы зафиксированы следующие технические проблемы:

1. **Фрагментация домена телеметрии**:
   * Наличие двух параллельных пакетов первого уровня: `apps/windows/telemetry` и `apps/windows/telemetry_research`.
   * Содержимое файла `telemetry/grouped_telemetry.py` представляет собой прокси-обертку над `telemetry_research/grouped_telemetry.py`.
   * В `telemetry/__init__.py` используется метод `__getattr__` для ленивого импорта `DiagnosticEngine` с целью обойти циклическую загрузку.

2. **Дублирование моделей данных**:
   * Сущности системного состояния, датчиков, рисков и аудитов одновременно объявлены в `core/models.py`, `core/data_model.py`, `core/atomic_models.py`, `telemetry/models.py`, `telemetry_research/models.py` и `modules/*/models.py`.
   * Из-за отсутствия единого реестра DTO разработчикам приходится вызывать `import` внутри методов и функций (lazy imports), что усложняет статический анализ типа `mypy` / `pyright`.

3. **Сложность обслуживания FastAPI сервера**:
   * Главный файл сервера `fast_api.pdf` / `server.py` содержит гигантскую монолитную функцию `_register()`, в которой через последовательные блоки `try-except` вручную импортируются и подсоединяются десятки роутеров.
   * Добавление каждого нового модуля требует ручной правки основного файла инициализации сервера.

4. **Разобщенность C-FFI системных вызовов**:
   * Вызовы C-FFI / ctypes к нативным библиотекам Windows (`wevtapi.dll`, `setupapi.dll`, `iphlpapi.dll`, `pdh.dll`, `scm.py`, `ntdll.py`) разнесены между `telemetry/win32_ffi/`, `core/winapi.py` и отдельными коллекторами в `core/audits/`.

5. **Рассредоточение ИИ-контура**:
   * Компоненты ИИ и знаний распределены по разным директориям: `apps/windows/wikillm` (база знаний), `apps/windows/log_intelligence` (RAG логов), `apps/windows/telemetry_research/assistant.py` (Gemini ассистент) и `prompts/` (системные инструкции).

---

## 3. Целевая архитектура и структура каталогов

Все компоненты платформы `apps/windows` переформировываются в 7 строго изолированных слоев:

```text
apps/
└── windows/
    ├── contracts/                     # Слой 1: Единые контракты и DTO (Zero-dependency)
    │   ├── enums.py                   # RiskLevel, TelemetryTier, AccessType, SamplingMode
    │   ├── audit.py                   # AuditFinding, DomainAuditResult, RemediationAction
    │   ├── hardware.py                # HardwareSensor, CpuMetrics, GpuMetrics, MemoryMetrics
    │   ├── telemetry.py               # SystemSnapshot, ProcessMetrics, TelemetryIncident
    │   └── ai.py                      # ArtifactInput, KnowledgeEntity, ResolutionResult
    │
    ├── native/                        # Слой 2: Единый слой C-FFI вызовов Win32 DLL
    │   ├── wevtapi.py                 # Windows Event Log API (wevtapi.dll)
    │   ├── setupapi.py                # PnP Device & Driver Management (setupapi.dll)
    │   ├── iphlpapi.py                # Network Sockets & Adapters (iphlpapi.dll)
    │   ├── pdh.py                     # Performance Counters Engine (pdh.dll)
    │   ├── scm.py                     # Service Control Manager (advapi32.dll)
    │   └── ntdll.py                   # Native NT Kernel API (ntdll.py)
    │
    ├── telemetry/                     # Слой 3: Подсистема сбора, хранения и сжатия телеметрии
    │   ├── ingestion/                 # Коллекторы (SystemCollector, SensorCollector, ETW, W64)
    │   ├── storage/                   # SQLite Facade, WAL Connection, Buffer, Maintenance
    │   ├── catalog/                   # 7 Доменов телеметрии, Sysmon Layer, Event Registry
    │   └── analytics/                 # Aggregator, Compactor, Anomaly Detector, Rollups
    │
    ├── core/                          # Слой 4: Исполнительное ядро, SafeOps и аудит
    │   ├── agent_loop.py              # Автономный агентский цикл (WindowsAgentLoop)
    │   ├── safe_ops.py                # Исполнитель SafeExecutor и Dry-Run симуляция
    │   ├── system32_catalog.py        # Реестр ~180 утилит System32 и Command Registry
    │   ├── atomic_registry.py         # 17 Категорий Atomic Operations
    │   └── audits/                    # 15 Доменных коллекторов аудита (Clean, Driver, Services...)
    │
    ├── modules/                       # Слой 5: Высокоуровневые бизнес-модули
    │   ├── accounts_identity/         # LSA, профили, SID, токены
    │   ├── backup_manager/            # File History, VSS, Библиотеки, VSS-версионирование
    │   ├── defender/                  # Microsoft Defender, ASR, CFA, Угрозы
    │   ├── event_logs/                # Менеджер журналов событий
    │   ├── firewall_manager/          # Windows Firewall / WFP
    │   ├── focus_policy/              # Focus Policy Engine, UserNotificationListener
    │   ├── hardware/                  # LHM Service, GPU Prober, Sensor Registry
    │   ├── personalization/           # PersonalizationManager (курсоры, темы, обои)
    │   └── software_manager/          # Инвентаризация ПО, UserAssist, Transparency
    │
    ├── ai/                            # Слой 6: Контур ИИ, RAG и Интеллектуальной Диагностики
    │   ├── wikillm/                   # 4-уровневый конвейер знаний, AST Code Indexer
    │   ├── log_intelligence/          # Пайплайн анализа логов и поиск аномалий
    │   ├── diagnostician.py           # ИИ-диагност (Health Score, гипотезы)
    │   └── tool_engine.py             # DynamicWindowsToolEngine & Фабрика навыков
    │
    └── api/                           # Слой 7: Единый API слой (FastAPI)
        ├── server.py                  # Фабрика приложения и динамический роутер
        └── routers/                   # Автоматически регистрируемые REST-роутеры
```

---

## 4. Спецификация изменений по подсистемам

### 4.1. Единый пакет контрактов (`apps.windows.contracts`)
* Создается чистый Python-пакет, который зависит **только** от стандартной библиотеки Python, `dataclasses` и `pydantic`.
* Запрещены любые импорты из других подсистем `apps.windows.*` внутрь `contracts`.
* Все бизнес-модули, аудиторы и коллекторы обязаны использовать типы из `apps.windows.contracts`.

### 4.2. Нативный слой Win32 C-FFI (`apps.windows.native`)
* Объединяет все низкоуровневые обертки `ctypes.windll` и `wintypes`.
* Все функции слоя возвращают строго типизированные структуры из `apps.windows.contracts`.
* Предусматривается обработка ошибок Win32 Error Codes через системный декоратор `win32_error_check`.

### 4.3. Подсистема телеметрии и аналитики (`apps.windows.telemetry`)
* Удаляется модуль `apps/windows/telemetry_research`.
* Аналитические компоненты (`analyzer.py`, `compactor.py`, `incident_detector.py`, `reboot_analyzer.py`) переносятся в `apps/windows/telemetry/analytics/`.
* Устраняется прокси-файл `grouped_telemetry.py`. Потребители импортируют `GroupedTelemetryBuilder` напрямую из `apps.windows.telemetry.analytics`.

### 4.4. Динамический роутинг FastAPI (Auto-Discovery)
В `apps/windows/api/server.py` внедряется функция изобличенного автообнаружения роутеров с обработкой ошибок загрузки:

```python
import importlib
import pkgutil
from fastapi import FastAPI, APIRouter
from logger import logger

def discover_and_register_routers(app: FastAPI, package_path: str) -> None:
    """Динамическое сканирование и подсоединение REST API роутеров."""
    try:
        package = importlib.import_module(package_path)
    except Exception as err:
        logger.error(f"[AutoDiscovery] Не удалось импортировать базовый пакет {package_path}: {err}")
        return

    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if module_name.endswith(".router") or "routers.router_" in module_name:
            try:
                mod = importlib.import_module(module_name)
                router = getattr(mod, "router", None) or (mod.init_router() if hasattr(mod, "init_router") else None)
                if isinstance(router, APIRouter):
                    app.include_router(router)
                    logger.debug(f"[AutoDiscovery] Успешно зарегистрирован роутер: {module_name}")
            except Exception as router_err:
                logger.warning(f"[AutoDiscovery] Пропуск роутера {module_name} из-за ошибки: {router_err}")
```

### 4.5. Стандартизация доменных модулей (`apps.windows.modules.*`)
Каждый модуль подсистемы приводит структуру к унифицированному стандарту:
* `core/` — доменная бизнес-логика.
* `models.py` — спецификации DTO (расширяющие контракты).
* `router.py` — FastAPI роутер с обязательным экспортом `router = APIRouter(...)`.
* `tui.py` — терминальный UI на базе Rich.
* `__main__.py` — точка автономного CLI-запуска.

---

## 5. План миграции и этапность работ

| Этап | Содержание работ | Трудоемкость | Зависимости |
| :--- | :--- | :--- | :--- |
| **Этап 1** | Создание пакета `contracts`, консолидация всех Enum и Pydantic-схем. | 2 дня | Отсутствуют |
| **Этап 2** | Создание пакета `native`, объединение всех C-FFI / Win32 DLL вызовов. | 2 дня | Этап 1 |
| **Этап 3** | Рефакторинг `telemetry`: объединение с `telemetry_research`, ликвидация прокси. | 3 дня | Этап 1, 2 |
| **Этап 4** | Рефакторинг `core` и 15 коллекторов аудитов с переходом на `contracts` и `native`. | 3 дня | Этап 1, 2 |
| **Этап 5** | Реорганизация `ai` контура (`wikillm`, `log_intelligence`, `diagnostician`). | 2 дня | Этап 1, 3 |
| **Этап 6** | Перевод `modules/*` на новую структуру и внедрение Auto-Discovery в FastAPI. | 2 дня | Этап 1–5 |
| **Этап 7** | Комплексное интеграционное тестирование и актуализация unit-тестов. | 2 дня | Этап 1–6 |

---

## 6. Критерии приемки и метрики качества

1. **Производительность**:
   * Время отклика REST API выборок из SQLite телеметрии — **< 5 мс**.
   * Время полной инициализации FastAPI приложения со всеми роутерами — **< 500 мс**.
2. **Надежность кода**:
   * Полное отсутствие цикличных импортов (`ImportError`, `CircularImport`).
   * Полный отказ от вызовов `import` внутри методов и функций для решения проблем загрузки.
   * Полное отсутствие `__getattr__` оберток в файлах `__init__.py`.
3. **Покрытие и совместимость**:
   * 100% успешное прохождение интеграционных и unit-тестов.
   * Полное сохранение обратной совместимости по REST API эндпоинтам для фронтенд-панелей.
