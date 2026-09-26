# Скрипты запуска платформы (launchers)

Директория содержит скрипты запуска и управления службами и микросервисами платформы **AI Breadboard**.

---

## 📋 Список сценариев запуска

### Основные серверы и оркестраторы:
- `run.py` — Интерактивный основной лаунчер платформы с поддержкой аргументов `--host`, `--port`, `--non-interactive`.
- `run_unicorn.py` — Специализированный лаунчер Uvicorn для production ASGI-сервера.
- `run_light_server.py` — Легковесный режим сервера с минимальной загрузкой компонентов.
- `run_foundry.py` — Запуск Microsoft AI Foundry совместно с FastAPI-сервером.
- `Run-Apps.ps1` — Универсальный мульти-сервисный диспетчер для пакетного запуска/остановки микросервисов из каталога `/apps`.
- `Run-TC.ps1` — Главный комплексный сценарий запуска всей рабочей среды (проверка и автостарт службы телеметрии `ai-telemetry.exe`, запуск LibreHardwareMonitor и веб-интерфейса).
- `Run-Terminals.ps1` — Мультитерминальный режим в Windows Terminal (вкладки или сплит-панели).
- `run_tests.ps1` — Скрипт полного прогона тестового набора (`pytest`).

### Служба системной телеметрии Windows:
- [`Run-Telemetry.ps1`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/launchers/Run-Telemetry.ps1) — Универсальный PowerShell-лончер управления автономной службой телеметрии **`ai-telemetry.exe`** (CPU, RAM, GPU, диски, сеть, процессы).
  - Поддерживаемые команды: `start`, `stop`, `restart`, `status`, `install-task`, `uninstall-task`, `status-task`.
  - Режимы сбора: `minimal` (ультралегкий, 28 мс/замер), `hybrid` (быстрый легкий цикл 5с + периодический тяжелый LHM/SMART 60с), `full`.
  - Запуск через WMI (`Win32_Process.Create`) в приоритете `BelowNormal` — процесс отвязан от родительской консоли и работает непрерывно.
- [`Install-TelemetryTask.ps1`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/launchers/Install-TelemetryTask.ps1) — Автоматическая регистрация службы `ai-telemetry.exe` в **Windows Task Scheduler** с флагом `WakeToRun = $true` (пробуждение при сне, питание от батареи, бесконечный цикл работы, приоритет `BelowNormal`, автоперезапуск при сбоях).

### Провайдеры ИИ и микросервисы:
- `Run-Agy.ps1` — Запуск провайдера AGY (Antigravity).
- `Run-Foundry.ps1` — Запуск Microsoft AI Foundry Local.
- `Run-Ollama.ps1` — Управление локальной службой Ollama.
- `Run-GeminiCli.ps1` — Запуск интерактивного режима Google Gemini CLI.
- `Run-LightServer.ps1` — Запуск легковесного сервера платформы.
- `Run-TelegramBot.ps1` — Запуск автономного сервиса Telegram-бота.
- `Run-WindowsAdmin.ps1` — Автономный микросервис администрирования Windows (порт 8100).
- `Run-NetworkTerminal.ps1` — Автономный микросервис сетевого анализатора Network Analyzer (порт 8101).
- `Run-SystemInspector.ps1` — Автономный микросервис инспектора оборудования System Inspector (порт 8102).
- `Run-TradingTerminal.ps1` — Автономный микросервис торгового терминала (порт 8103).
- `Run-CloudflaredMonitor.ps1` — Автономный микросервис монитора Cloudflare Tunnel (порт 8104).
- `Run-Unicorn.ps1` — PowerShell-обертка для запуска в режиме Uvicorn.

---

## 🚀 Примеры использования

```powershell
# Запуск службы телеметрии в фоне (режим hybrid)
.\launchers\Run-Telemetry.ps1

# Проверка статуса службы телеметрии (PID, имя ai-telemetry, Working Set RAM)
.\launchers\Run-Telemetry.ps1 -Action status

# Регистрация службы телеметрии в планировщике задач Windows (с WakeToRun)
.\launchers\Run-Telemetry.ps1 -Action install-task

# Запуск основного интерфейса AI Breadboard
.\Run-TC.ps1
```

---

## 🪟 Интеграция с окном приложения Windows Edge (App Mode)

При запуске на Windows сценарии `Run-TC.ps1`, `run.ps1` и `Run-Unicorn.ps1` автоматически открывают интерфейс управления в отдельном автономном окне веб-приложения Edge (`msedge.exe --app="..."`):
- **Без лишнего хрома браузера**: отсутствуют адресная строка, панель вкладок и сторонние расширения.
- **Изолированный профиль**: cookies, кэш и хранилище изолированы в `%APPDATA%/AI-Breadboard/browser_profile`.
- **Маршрутизация Admin URL**: при включенном Cloudflare Tunnel (`use_cloudflared: true`) окно открывается по публичному адресу туннеля, при локальном режиме — по `http://localhost:8000/admin`.
