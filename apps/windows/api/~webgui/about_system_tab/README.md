# ℹ️ Вкладка «О Системе» (About System Tab)

Интерактивная панель подробной спецификации оборудования, системной телеметрии и AI-диагностики хоста Windows с поддержкой сквозной наблюдаемости (Observability).

---

## 🏛️ Архитектура и блок-схема потока данных

```mermaid
flowchart TD
    subgraph Host_OS["💻 Хост Windows (Низкоуровневый слой)"]
        REG["Реестр Windows (winreg)<br/>• HKLM/CurrentVersion (InstallDate, Build)<br/>• HKLM/System/BIOS (Материнская плата)"]
        WIN32["Native Win32 API (ctypes)<br/>• Locale & Codepages (Kernel32)<br/>• Keyboard Layouts (User32)<br/>• WinAPI Capability Detector"]
        PSUTIL["Системные вызовы & psutil<br/>• CPU, RAM, Uptime, Диски, Сеть"]
        LHM["Аппаратные зонды & LHM<br/>• LibreHardwareMonitor (Температуры, Вольтаж, Нагрузка)"]
    end

    subgraph Windows_Subsystem["⚙️ Подсистема apps/windows (Единое ядро)"]
        COLLECTOR["apps.windows.telemetry.collector<br/><b>SystemCollector</b>"]
        
        subgraph Collector_Methods["Методы сбора фактов"]
            M_IDENT["get_system_identity()<br/>(Хост, Юзер, Локали, <b>InstallDate</b>)"]
            M_TREE["get_hardware_tree()<br/>(Иерархическое дерево узлов оборудования)"]
            M_METRICS["get_cpu_metrics() / get_disk_metrics()<br/>(Метрики производительности и дисков)"]
            M_SENS["get_hardware_sensors()<br/>(Сенсоры и температуры LHM)"]
        end

        subgraph Core_Managers["Менеджеры apps/windows/core"]
            SPM["system_param_manager<br/>(Безопасное управление + Restore Points)"]
            SWA["software_audit<br/>(Аудит ПО, Prefetch, UserAssist)"]
            DEF["defender_manager<br/>(Защитник Windows и Firewall)"]
        end

        MODELS["apps.windows.telemetry.models<br/><b>SystemSnapshot</b> & <b>HardwareNode</b>"]
    end

    subgraph AI_Observability["🧠 Слой AI-диагностики & Observability"]
        AI_ENGINE["src.ai.observability.engine<br/><b>ObservabilityDiagnosticsEngine</b>"]
        DIAG_ENGINE["src.ai.observability.system_engine<br/><b>SystemDiagnosticEngine</b>"]
        STAGES["Multi-stage Pipeline<br/>(Telemetry Analysis → Heuristic Evaluation → LLM Diagnosis)"]
        OBS_MODELS["src.ai.observability.models<br/><b>SystemDiagnosticReport</b><br/>• health_score, anomalies, recommendations<br/>• system_instruction, generated_prompt, raw_llm_response, error"]
    end

    subgraph API_Layer["🌐 Слой API (FastAPI)"]
        ROUTER["src.api.router_system.py<br/><b>/api/v1/system/*</b>"]
        EP_SUM["GET /api/v1/system/summary<br/>(Единый снимок SystemSnapshot)"]
        EP_HW["GET /api/v1/system/hardware<br/>(Дерево узлов HardwareNode)"]
        EP_SENS["GET /api/v1/system/sensors<br/>(Сенсоры LHM)"]
        EP_DIAG["POST /api/v1/system/diagnose<br/>(AI-диагностика и аудит телеметрии)"]
    end

    subgraph Frontend["🖥️ Веб-интерфейс (about_system_tab)"]
        GUI_MAIN["main.js<br/>(fetchSystemSummary, fetchHardwareSpec, fetchAIDiagnostics)"]
        
        subgraph UI_Components["Компоненты index.html"]
            UI_ID["<b>Карточка идентификации хоста</b><br/>• Имя ПК / Юзер / Локали / Часовой пояс<br/>• 📅 <b>Дата установки ОС</b><br/>• 🛡️ Резервное копирование / Сборка Windows / Обновления"]
            UI_KPI["<b>KPI Телеметрии</b><br/>• CPU, RAM, GPU, Диск (C:) I/O"]
            UI_SPEC["<b>Сводные таблицы</b><br/>• System Specification<br/>• Security & Firewall Profiles<br/>• Storage Volumes & Partitions"]
            UI_TREE["<b>Спецификация оборудования</b><br/>• Адаптивный CSS Grid (ключ-значение рядом)<br/>• Многоколоночный макет на широких экранах"]
            UI_AI["<b>AI Copilot & Observability Panel</b><br/>• Health Score & Индикаторы этапов сканирования<br/>• Аномалии и Рекомендации<br/>• Инспектор системной инструкции и промпта<br/>• Инспектор сырого ответа LLM и блок ошибок"]
        end
    end

    %% Связи Host -> Windows Subsystem
    REG --> M_IDENT
    REG --> M_TREE
    WIN32 --> M_IDENT
    PSUTIL --> M_METRICS
    LHM --> M_SENS

    %% Связи внутри Windows Subsystem
    COLLECTOR --> Collector_Methods
    Collector_Methods --> MODELS
    Core_Managers -.-> COLLECTOR

    %% Связи Windows Subsystem -> API
    MODELS --> ROUTER
    ROUTER --> EP_SUM
    ROUTER --> EP_HW
    ROUTER --> EP_SENS

    %% Связи AI Observability -> API
    MODELS --> DIAG_ENGINE
    DIAG_ENGINE --> AI_ENGINE
    AI_ENGINE --> STAGES
    STAGES --> OBS_MODELS
    OBS_MODELS --> EP_DIAG
    ROUTER --> EP_DIAG

    %% Связи API -> Frontend
    EP_SUM --> GUI_MAIN
    EP_HW --> GUI_MAIN
    EP_SENS --> GUI_MAIN
    EP_DIAG --> GUI_MAIN

    %% Связи Frontend -> UI
    GUI_MAIN --> UI_ID
    GUI_MAIN --> UI_KPI
    GUI_MAIN --> UI_SPEC
    GUI_MAIN --> UI_TREE
    GUI_MAIN --> UI_AI
```

---

## 📋 Возможности и компоненты интерфейса

1. **Карточка идентификации хоста и региональных параметров**:
   - Имя хоста, имя текущего пользователя и уровень привилегий.
   - Язык интерфейса, локали пользователя и системы (`user_locale`, `system_locale`), кодовые страницы (ACP / OEM).
   - Часовой пояс и раскладки ввода клавиатуры.
   - 📅 **Дата установки ОС** — прямое чтение времени установки Windows из системного реестра (`HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\InstallDate`).
   - Номер сборки Windows и статус установленных исправлений (Windows Update).

2. **Сводные KPI-карточки и живая телеметрия**:
   - Мониторинг загрузки CPU (физические ядра, логические потоки, частота).
   - Оперативная память (RAM занято / свободно, процент использования).
   - Графический ускоритель (GPU модель, объем VRAM, нагрузка, поддержка CUDA / DirectML).
   - Активность накопителя C: (скорость чтения и записи в реальном времени).

3. **Спецификация оборудования (Hardware Tree)**:
   - Иерархическое дерево устройств (System, Processor, Motherboard, Memory, Display, Storage, Network).
   - **Верстка CSS Grid**: свойства отображаются в виде компактной адаптивной двухколоночной сетки (`minmax(140px, 200px) 1fr`), где ключ и значение находятся рядом друг с другом.
   - На широких мониторах список свойств автоматически распределяется по нескольким параллельным колонкам (`repeat(auto-fill, minmax(360px, 1fr))`).
   - Быстрый поиск компонентов и фильтрация на лету.

4. **Износ накопителей и состояние батареи (Storage & Battery Health)**:
   - Мониторинг износа и остаточного ресурса SSD / NVMe (SMART-статус, Health %).
   - Детальная таблица разделов с полосами износа и статусами накопителей.
   - Телеметрия источника питания и деградации аккумулятора ноутбука (Battery Degradation / AC Mains).

5. **Интеллектуальная AI-диагностика и Observability**:
   - Многоэтапный конвейер аудита (*Multi-stage Diagnostic Pipeline*) со статусами выполнения в реальном времени.
   - Расчет индекса здоровья системы (*Health Score 0-100*).
   - Кластеризация и отображение аномалий по уровням важности (Warning, Critical, Info).
   - **Сквозная наблюдаемость (Observability)**:
     - 🛡️ Инспектор системной инструкции модели (*System Instruction Inspector*).
     - 📝 Инспектор сгенерированного промпта (*Sent Prompt Inspector*).
     - 🔬 Инспектор сырого ответа нейросети (*Raw LLM Response Inspector*).
     - ⚠️ Информативный блок ошибок с точной локализацией сбоев провайдеров.

---

## 🔌 API эндпоинты

- `GET /api/v1/system/summary` — получение сводного снимка телеметрии хоста (`SystemSnapshot`).
- `GET /api/v1/system/hardware` — получение иерархического дерева компонентов (`List[HardwareNode]`).
- `GET /api/v1/system/sensors` — сбор показателей сенсоров LibreHardwareMonitor (`List[HardwareSensor]`).
- `GET /api/v1/system/diagnostics/storage-battery` — телеметрия износа накопителей SSD/NVMe (SMART) и батареи питания (`StorageBatteryWearReport`).
- `GET /api/v1/system/processes` — получение списка активных процессов хоста с метриками CPU/RAM.
- `POST /api/v1/system/diagnose` — запуск эвристического и AI-анализа телеметрии (`SystemDiagnosticReport`).
