# 🚀 LAUNCHER GUIDE — Руководство по лончерам проекта

**Проект:** `AI Breadboard`  
**Status:** ✅ Актуально  
**Дата:** 2026-08-26  
**Для:** разработчиков, агентов ИИ, оркестраторов

---

## 📍 Где находятся лончеры
 
- Главный лончер `run.ps1` расположен в КОРНЕ проекта (`$env:AIBREADBOARD_DIR` или рабочая директория).
- Все специализированные лончеры (`Run-*.ps1` и `run_tests.ps1`) расположены в поддиректории `launchers/`.

```
<project_root>\
├── run.ps1                       ← ГЛАВНЫЙ лончер (запускает всё)
├── tc.ps1                        ← Лончер блока приложений и веб-интерфейса /apps (по config_tc.json)
├── run_terminals.ps1             ← Лончер мульти-терминального окна
├── config.json                   ← Основная конфигурация проекта
├── config_tc.json                ← Конфигурация для Test Computer / лончера tc.ps1
└── launchers/
    ├── Run-Apps.ps1              ← Оркестратор запуска всех микросервисов из /apps
    ├── Run-Unicorn.ps1           ← FastAPI сервер (uvicorn)
    ├── Run-Foundry.ps1           ← Azure AI Foundry (локальная LLM)
    ├── Run-LightServer.ps1       ← Лёгкий HTTP-сервер
    ├── Run-GeminiCli.ps1         ← Google Gemini CLI агент
    ├── Run-Agy.ps1               ← Google Antigravity (AGY) агент
    ├── Run-Terminals.ps1         ← Мульти-терминальное окно / сплит-панели
    ├── Run-WindowsAdmin.ps1      ← Windows System Administrator (порт 8100)
    ├── Run-NetworkTerminal.ps1   ← Network Analyzer Terminal (порт 8101)
    ├── Run-SystemInspector.ps1   ← System Inspector (порт 8102)
    ├── Run-TradingTerminal.ps1   ← Exchange Trading Terminal (порт 8103)
    ├── Run-CloudflaredMonitor.ps1← Cloudflare Tunnel Monitor (порт 8104)
    ├── Run-GCloudMonitor.ps1     ← Google Cloud Monitor (порт 8106)
    ├── Run-WebsiteMonitor.ps1    ← Website Intelligence Monitor (порт 8107)
 │   ├── Run-SystemLogViewer.ps1   ← Windows Event & System Log Center (порт 8108)
│   ├── Run-SystemControlCenter.ps1← Windows System Control Center (порт 8109)
│   └── run_tests.ps1             ← Запуск тестов
```

---

## 📋 Реестр лончеров

| Лончер | Сервис | Что запускает | Parameters |
|--------|--------|--------------|-----------|
| `run.ps1` | Всё (Интерактивный) | FastAPI + Foundry + Ollama + Бот + Сервисы | `-Host 0.0.0.0\|127.0.0.1`, `-Port 8000`, `-NonInteractive`, `-Cloudflared` |
| `tc.ps1` | Блок приложений (`/apps`) | Только микросервисы и веб-интерфейс `/apps` (по `config_tc.json`) | `-Action start\|stop\|restart\|status`, `-ConfigFile <file.json>`, `-NewWindow`, `-Background`, `-NoBrowser` |
| `run_terminals.ps1` | Мульти-терминалы | Единое окно терминалов (wt.exe split/tabs) | `-Preset breadboard\|trading\|network\|custom`, `-Layout grid\|tabs\|windows`, `-Interactive` |
| `launchers/Run-Apps.ps1` | Оркестратор `/apps` | Запуск приложений по `config_tc.json` или `config.json` | `-Action start\|stop\|restart\|status`, `-ConfigFile <file.json>`, `-NewWindow` |
| `launchers/Run-Unicorn.ps1` | FastAPI | `uvicorn main:app` на порту из `config.json` | `-Host 0.0.0.0\|127.0.0.1`, `-Port 8000`, `-OpenUrl <url>` |
| `launchers/Run-Foundry.ps1` | AI Foundry | Локальная LLM-служба | `-Action start\|stop\|status` |
| `launchers/Run-LightServer.ps1` | FastAPI / Uvicorn | Лёгкий сервер (1 воркер, без туннелей) | `-mode 0.0.0.0\|localhost` (по умолчанию `0.0.0.0`), `-port 8000` |
| `launchers/Run-GeminiCli.ps1` | Gemini CLI | Google Gemini CLI агент | `-Action check\|install\|chat\|version`, `-Prompt "..."` |
| `launchers/Run-Agy.ps1` | Antigravity AGY | Google Antigravity CLI агент | `-Action check\|chat\|models\|update\|version`, `-Prompt "..."` |
| `launchers/Run-Terminals.ps1` | Мульти-терминалы | Сплит-панели Windows Terminal | `-Preset breadboard\|trading\|network\|custom`, `-Layout grid\|tabs\|windows` |
| `launchers/Run-WindowsAdmin.ps1` | Windows Sysadmin | Standalone FastAPI & TUI (порт 8100) | `-Action start\|stop\|restart\|status`, `-Mode server\|dashboard`, `-NewWindow` |
| `launchers/Run-NetworkTerminal.ps1` | Network Analyzer | Standalone FastAPI & TUI (порт 8101) | `-Action start\|stop\|restart\|status`, `-Mode server\|dashboard`, `-NewWindow` |
| `launchers/Run-SystemInspector.ps1` | System Inspector | Standalone FastAPI & TUI (порт 8102) | `-Action start\|stop\|restart\|status`, `-Mode server\|dashboard`, `-NewWindow` |
| `launchers/Run-TradingTerminal.ps1` | Trading Desk | Standalone FastAPI & TUI (порт 8103) | `-Action start\|stop\|restart\|status`, `-Mode server\|dashboard`, `-NewWindow` |
| `launchers/Run-CloudflaredMonitor.ps1` | Cloudflare Monitor | Standalone FastAPI & TUI (порт 8104) | `-Action start\|stop\|restart\|status`, `-Mode server\|dashboard`, `-NewWindow` |
| `launchers/Run-GCloudMonitor.ps1` | Google Cloud Monitor | Standalone FastAPI & TUI (порт 8106) | `-Action start\|stop\|restart\|status`, `-Mode server\|dashboard`, `-NewWindow` |
| `launchers/Run-WebsiteMonitor.ps1` | Website Intelligence | Standalone FastAPI & TUI (порт 8107) | `-Action start\|stop\|restart\|status`, `-Mode server\|dashboard`, `-NewWindow` |
| `launchers/Run-SystemLogViewer.ps1` | System Log Viewer | Standalone FastAPI & TUI (порт 8108) | `-Action start\|stop\|restart\|status`, `-Mode server\|dashboard`, `-NewWindow` |
| `launchers/Run-SystemControlCenter.ps1` | System Control Center | Standalone FastAPI & TUI (порт 8109) | `-Action start\|stop\|restart\|status`, `-Mode server\|dashboard`, `-NewWindow` |
| `launchers/run_tests.ps1` | Pytest Runner | Запуск модульных и интеграционных тестов | `-Coverage`, `-Verbose`, `-Markers` |

---

## 🤖 Запуск лончеров агентами ИИ

### Базовый синтаксис

```powershell
# Главный лончер из корня проекта
.\run.ps1

# Специализированные лончеры
.\launchers\Run-<ServiceName>.ps1

# Через переменную окружения AIBREADBOARD_DIR
& "$env:AIBREADBOARD_DIR\launchers\Run-<ServiceName>.ps1"
```

### Examples

```powershell
# Запуск главного сервера (FastAPI + Foundry)
.\run.ps1

# Только FastAPI сервер
.\launchers\Run-Unicorn.ps1

# Foundry с параметром действия
.\launchers\Run-Foundry.ps1 -Action start
.\launchers\Run-Foundry.ps1 -Action stop
.\launchers\Run-Foundry.ps1 -Action status
```

### Check состояния

```powershell
# FastAPI health-check
Invoke-WebRequest -Uri "https://localhost:8000/health" -SkipCertificateCheck

# Проверить занятость порта
netstat -aon | Select-String ":8000"
```

### Остановка сервисов

# Остановить сервисы
$pid_ = (netstat -aon | Select-String ":8000\s" | ForEach-Object { ($_ -split "\s+")[-1] } | Select-Object -First 1)
if ($pid_) { Stop-Process -Id $pid_ -Force }
```

---

## ➕ Как создать новый лончер

### Правила именования

- **Файл:** `Run-<ServiceName>.ps1` (PascalCase)
- **Расположение:** корень проекта (`$env:AIBREADBOARD_DIR`)
- **Examples:** `Run-Redis.ps1`, `Run-Worker.ps1`, `Run-Scheduler.ps1`

### Шаблон нового лончера

```powershell
<#
.SYNOPSIS
    Запускает <ServiceName>.

.DESCRIPTION
    Описание сервиса. Reads конфигурацию из .env и config.json.

.PARAMETER Action
    start | stop | restart | status

.EXAMPLE
    .\Run-<ServiceName>.ps1
    .\Run-<ServiceName>.ps1 -Action stop
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start'
)

$ErrorActionPreference = 'Stop'
$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) { $scriptDir = Get-Location }

# === Loading .env ===
$envFile = Join-Path $scriptDir ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$" -and -not $_.StartsWith('#')) {
            [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim())
        }
    }
}

Write-Host "=== <ServiceName> ===" -ForegroundColor Cyan

switch ($Action) {
    'start'  { <# TODO: логика запуска #>  ; Write-Host "[OK] Запущен" -ForegroundColor Green }
    'stop'   { <# TODO: логика остановки #>; Write-Host "[OK] Остановлен" -ForegroundColor Yellow }
    'status' { <# TODO: check состояния #> }
}
```

### Чек-лист нового лончера

- [ ] Файл назван `Run-<ServiceName>.ps1`
- [ ] Помещён в каталог `launchers/`
- [ ] Содержит `.SYNOPSIS` и `.DESCRIPTION`
- [ ] Reads `.env` при старте
- [ ] Выводит чёткий status
- [ ] Добавлена запись в таблицу "Реестр лончеров" выше

---

## 🔧 Вспомогательные скрипты (не лончеры)

| Скрипт | Назначение |
|---|---|
| `install.ps1` | Установка проекта и venv |
| `install.cmd` | Установка (CMD вариант) |
| `install_ssl_cert.ps1` | Генерация SSL-сертификата |
| `launchers/run_tests.ps1` | Запуск тестов pytest |

---

## 🌐 Маршрутизация URL: Cloudflare Tunnel vs Localhost

В скриптах `run.ps1` и `launchers/Run-Unicorn.ps1` целевой URL для встроенного окна приложения (`msedge.exe --app=...`) определяется на основе настроек туннелирования:

- **Туннель включён (`"use_cloudflared": true`):**
  Если задан `client_url` или `user_domain` (например, `https://kino.davidka.net`), окно приложения направляется на внешний URL через туннель Cloudflare.
- **Туннель выключен (`"use_cloudflared": false`):**
  Сервер поднимается на интерфейсе `0.0.0.0:8000`, окно приложения открывает локальный адрес `localhost:8000/admin` (или `${proto}://localhost:${port}/admin`), а процессы `cloudflared` и сопутствующий микросервис `Cloudflared Monitor` (8104) не запускаются.

---

## 📁 Структура проекта

```
AI-Breadboard/
├── 📄 run.ps1                # Главный лончер сервисов
├── 📁 launchers/             # Специализированные лончеры (Run-*.ps1, run_tests.ps1)
├── 📄 main.py                # FastAPI приложение
├── 📄 manage_tools.py        # Универсальный CLI агентов
├── 📄 header.py              # Определение __root__ проекта
├── 📁 src/                   # Основной код (ai/, fastapi/, .skills/, rag/, logger/, tts/...)
│   ├── 📁 ai/providers/      # Провайдеры ИИ (gemini, foundry, onnx, windows_ai, ollama...)
│   ├── 📁 fastapi/           # Роутеры FastAPI и webinterface
│   └── 📁 rag/               # RAG-подсистема
├── 📁 plugins/               # Плагины
├── 📁 scripts/dev/           # Инструменты разработчика
├── 📁 tmp/                   # Временные файлы и логи
├── 📁 .skills/        # Навыки агентов
├── 📁 tests/                 # Тесты (pytest)
└── 📁 .ai/instructions/      # Инструкции для ИИ
```

---

## 🔗 Связанные документы

- [`manage_tools.py`](../../../manage_tools.py) — CLI для управления инструментами проекта
- [`scripts_tools.md`](scripts_tools.md) — справочник скриптов
- [`MODEL_SCRIPT_EXECUTION_GUIDE.md`](MODEL_SCRIPT_EXECUTION_GUIDE.md) — руководство для моделей ИИ

