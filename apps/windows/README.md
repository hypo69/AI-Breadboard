# 🪟 AI Windows Diagnostic & Administration Center

Интеллектуальный центр диагностики, аудита, оптимизации и безопасного администрирования Windows на базе низкоуровневых интерфейсов WinAPI/WMI/PowerShell и аналитического слоя AI (Gemini / Foundry / Ollama / Local).

---

## 💡 Концепция и Архитектурный принцип

> **Низкоуровневые системные интерфейсы (WinAPI, WMI/CIM, Event Log, Registry, Services, Task Scheduler, PnP/DriverStore, Defender, PowerShell) собирают факты, а модель занимается корреляцией, диагностикой, расчётом рисков и формированием безопасных рекомендаций, не получая права на неконтролируемые деструктивные изменения.**

---

## 🏛️ Архитектура системы

```
AI WINDOWS DIAGNOSTIC & ADMINISTRATION CENTER
├── 1. Слой интерфейсов (Presentation & API)
│   ├── router.py             # FastAPI REST API endpoints
│   ├── cli.py                # Универсальный CLI (python -m apps.windows)
│   ├── tui.py                # Интерактивный Rich TUI Dashboard
│   └── __main__.py           # Точка входа в модуль
│
├── 2. Слой AI и корреляции (AI Intelligence Layer)
│   ├── ai/diagnostician.py        # AI-диагност и расчёт Health Score
│   ├── ai/root_cause_analyzer.py  # Анализатор первопричин по симптомам
│   └── ai/prompt_templates.py     # Структурированные промпты для LLM
│
├── 3. Безопасность и исполнение (SafeOps Layer)
│   ├── core/safe_executor.py      # Dry-run симуляция, изоляция рисков, бэкапы
│   ├── core/root_cause_engine.py  # Построение графа расследования (Timeline Graph)
│   └── core/models.py             # Нормализованные модели данных и уровни рисков
│
└── 4. 15 Доменных модулей сбора фактов (Fact Collectors)
    ├── clean_collector.py         # 1. Очистка кэшей, %TEMP%, WinUpdate, Minidump
    ├── performance_collector.py   # 2. Производительность, автозагрузка, CPU/RAM
    ├── driver_collector.py        # 3. Драйверы, ошибки PnP, DriverStore audit
    ├── software_collector.py      # 4. Инвентарь ПО (App -> Service -> Task -> Driver)
    ├── integrity_collector.py     # 5. Целостность (SFC / DISM / Servicing / Reboot)
    ├── storage_collector.py       # 6. Диски, тома, свободное место, SMART
    ├── security_collector.py      # 7. Defender, UAC, брандмауэр, персистентность
    ├── eventlog_collector.py      # 8. Корреляция системных журналов (Event Log)
    ├── process_collector.py       # 9. Интеллект процессов (Process Explorer)
    ├── services_collector.py      # 10. Матрица служб и поиск осиротевших сервисов
    ├── tasks_collector.py         # 11. Задачи планировщика (Task Scheduler)
    ├── network_collector.py       # 12. Сетевая телеметрия, сокеты и порты
    ├── update_collector.py        # 13. Обновления Windows (KB, версии, SSU)
    ├── baseline_collector.py      # 14. Снимок конфигурации и Drift Detector
    └── postinstall_collector.py   # 15. Чек-лист готовности после установки Windows
```

---

## 🚀 Режимы работы (Diagnostic Modes)

1. **`Quick Health Check` (`--mode quick`)**: Быстрая проверка ключевых параметров за 3 секунды (CPU/RAM/Диск, критические ошибки логов, UAC, Defender).
2. **`Full Deep Audit` (`--mode full`)**: Глубокий аудит по всем 15 доменам системы с расчётом **Health Score (0-100)** и сводным отчетом.
3. **`Security & Persistence Audit` (`--mode security`)**: Проверка защитных механизмов, UAC, открытых портов, подозрительных задач планировщика и персистентности.
4. **`Performance Bottleneck Analysis` (`--mode performance`)**: Выявление ресурсоемких процессов, оптимизация автозагрузки и параметров электропитания.
5. **`Driver Store & Hardware Audit` (`--mode drivers`)**: Поиск PnP ошибок (Code 10/43), инвентаризация и очистка устаревших версий пакетов в `DriverStore`.
6. **`Post-Install System Audit` (`--mode postinstall`)**: Комплексный аудит готовности рабочей станции после чистой установки Windows.
7. **`Root-Cause Investigator` (`--investigate "<симптом>"`):**
   - Пользовательский ввод (напр. *"Компьютер начал тормозить после установки программы X"*).
   - Построение цепочки расследования: Программа → Службы → Автозагрузка → Задачи → Драйверы → Нагрузка → Журналы.
   - Вывод: **Гипотеза + Доказательства + Уровень уверенности + Безопасный план устранения**.

---

## 🔒 Протокол безопасности SafeOps

- **Read-Only по умолчанию:** Любой аудит и диагностика абсолютно пассивны и не изменяют систему.
- **Dry-Run симуляция:** Любое действие (очистка, отключение задачи/службы) сначала рассчитывает освобождаемое место и потенциальные эффекты.
- **Классификация рисков:**
  - 🟢 `Safe`: Очистка `%TEMP%`, кэша браузера, корзины (выполняется свободно).
  - 🟡 `Caution`: Отключение автозагрузки, удаление старых пакетов DriverStore (требует подтверждения пользователя).
  - 🔴 `Critical`: Изменение системных служб, параметров реестра ядра, восстановление компонентов — требует прав администратора и создания точки отката.

---

## 💻 Использование CLI

```powershell
# Быстрая проверка здоровья системы
python -m apps.windows --mode quick

# Полный глубокий аудит системы
python -m apps.windows --mode full

# Расследование первопричины сбоя по симптому
python -m apps.windows --investigate "Компьютер начал тормозить после установки программы"

# Вывод в формате JSON (для интеграций и RAG)
python -m apps.windows --mode full --json

# Запуск интерактивного TUI Dashboard
python -m apps.windows --tui

# Запуск интерактивного TUI монитора оборудования (Hardware Monitor)
python -m apps.windows --hardware

# Получение аппаратного снимка в формате JSON
python -m apps.windows --hw-json

# Запуск интерактивного монитора системных логов
python -m apps.windows --logs --channel System

# Запуск автономного REST API сервера
python -m apps.windows --server --port 8105
```

---

## 🌐 FastAPI REST API

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/windows/health?mode=quick` | Сводная оценка Health Score (0-100) |
| `GET` | `/api/windows/hardware/monitor` | Полный слепок аппаратного мониторинга (CPU, RAM, GPU, Диски, Сеть, Датчики) |
| `GET` | `/api/windows/hardware/monitor/summary` | Сводка здоровья и пороговых предупреждений оборудования |
| `GET` | `/api/windows/hardware/sensors` | Показания всех активных датчиков температуры, вентиляторов и вольтажа |
| `GET` | `/api/windows/hardware/gpu` | Телеметрия видеокарт NVIDIA / AMD / Intel / WMI |
| `GET` | `/api/windows/hardware/smart` | Диагностика накопителей и S.M.A.R.T. |
| `GET` | `/api/windows/hardware/audit` | Аппаратный аудит через CPU-Z / AIDA64 / WMI |
| `POST` | `/api/windows/benchmark/stress` | Стресс-тест CPU / GPU с защитой от перегрева |
| `GET` | `/api/windows/audit/full` | Полный глубокий отчет по 15 доменам |
| `GET` | `/api/windows/audit/clean` | Аудит кэшей, %TEMP% и корзины |
| `GET` | `/api/windows/audit/performance` | Аудит нагрузки CPU/RAM и автозагрузки |
| `GET` | `/api/windows/audit/drivers` | Аудит PnP устройств и DriverStore |
| `GET` | `/api/windows/audit/software` | Инвентарь установленного ПО и компонентов |
| `GET` | `/api/windows/audit/integrity` | Проверка целостности SFC / DISM / Servicing |
| `GET` | `/api/windows/audit/storage` | Аудит дисков, томов и свободного места |
| `GET` | `/api/windows/audit/security` | Аудит Defender, UAC и персистентности |
| `GET` | `/api/windows/audit/events` | Корреляция системных журналов ошибок |
| `GET` | `/api/windows/audit/processes` | Анализ запущенных процессов |
| `GET` | `/api/windows/audit/services` | Инвентарь служб и поиск осиротевших сервисов |
| `GET` | `/api/windows/audit/tasks` | Аудит планировщика заданий |
| `GET` | `/api/windows/audit/network` | Телеметрия сокетов и открытых портов |
| `GET` | `/api/windows/audit/updates` | Версии ОС и установленные KB |
| `GET` | `/api/windows/audit/baseline` | Аудит эталонного снимка и дрифта |
| `GET` | `/api/windows/audit/postinstall` | Чек-лист готовности после установки ОС |
| `POST` | `/api/windows/investigate` | Расследование симптома (Root-Cause) |
| `POST` | `/api/windows/actions/simulate` | SafeOps Dry-Run симуляция действия |
| `POST` | `/api/windows/actions/execute` | Безопасное выполнение действия (Admin) |

---

## 🛠️ Нативный Function Calling и Саморасширяемые инструменты (Self-Extending Tools)

Модуль `apps/windows/core/tools` реализует передовую архитектуру вызова и синтеза инструментов на лету:

1. **`ToolRegistry` (`registry.py`)**:
   - Централизованный реестр инструментов с формированием схем вызова OpenAPI / Function Calling (`to_function_definition()`).
   - Динамическая регистрация и удаление инструментов без перезапуска сервиса.
2. **`BaseTool` (`base.py`)**:
   - Абстрактный базовый класс для безопасных инструментов с валидацией входных аргументов, структурированным результатом (`ToolExecutionResult`) и оценкой уровней риска (`RiskLevel`).
3. **`WindowsCollectorTool` & `SafePowerShellProbeTool` (`system_tools.py`)**:
   - Встроенные системные инструменты, оборачивающие 15 доменных коллекторов и безопасный PowerShell-зондировщик с жестким SafeOps-фильтром деструктивных инструкций.
4. **`DynamicToolFactory` & `CreateCustomToolMetaTool` (`dynamic_factory.py`)**:
   - **Мета-инструмент `create_custom_tool`**: позволяет языковой модели самостоятельно конструировать новый инструмент под уникальный запрос пользователя, безопасно регистрировать его в runtime, выполнять зондирование хоста и автоматически сохранять переиспользуемый навык в каталог `.skills/`.
5. **`WindowsAgentLoop` (`agent_loop.py`)**:
   - Автономный ReAct / Function Calling цикл принятия решений с потоковой генерацией промежуточных этапов в веб-интерфейс Test Computer (`/tc`).

---

## 🧪 Тестирование

```powershell
pytest apps/windows/tests/test_hardware_monitor.py apps/windows/tests/test_ai_diagnostic_center.py -v
```

---

## 📜 Лицензия

© 2026 hypo69. Все права защищены.

