# 🚀 LAUNCHER GUIDE — Руководство по лончерам проекта

**Проект:** `AI Breadboard`  
**Статус:** ✅ Актуально  
**Дата:** 2026-08-26  
**Для:** разработчиков, агентов ИИ, оркестраторов

---

## 📍 Где находятся лончеры

**Все лончеры (`Run-*.ps1`) расположены в КОРНЕ проекта (`$env:AIBREADBOARD_DIR` или рабочая директория):**

```
<project_root>\
├── run.ps1                   ← ГЛАВНЫЙ лончер (запускает всё)
├── Run-Unicorn.ps1           ← FastAPI сервер (uvicorn)
├── Run-Foundry.ps1           ← Azure AI Foundry (локальная LLM)
├── Run-LightServer.ps1       ← Лёгкий HTTP-сервер
├── Run-GeminiCli.ps1         ← Google Gemini CLI агент
└── Run-Agy.ps1               ← Google Antigravity (AGY) агент
```

---

## 📋 Реестр лончеров

| Лончер | Сервис | Что запускает | Параметры |
|--------|--------|--------------|-----------|
| `run.ps1` | Всё (Интерактивный) | Foundry + uvicorn | `-Host 0.0.0.0\|127.0.0.1`, `-Port 8000`, `-NonInteractive` |
| `Run-Unicorn.ps1` | FastAPI | `uvicorn main:app` на порту из `config.json` | `-Host 0.0.0.0\|127.0.0.1`, `-Port 8000` |
| `Run-Foundry.ps1` | AI Foundry | Локальная LLM-служба | `-Action start\|stop\|status` |
| `Run-LightServer.ps1` | FastAPI / Uvicorn | Лёгкий сервер (1 воркер, без туннелей) | `-mode 0.0.0.0\|localhost` (по умолчанию `0.0.0.0`), `-port 8000` |
| `Run-GeminiCli.ps1` | Gemini CLI | Google Gemini CLI агент | `-Action check\|install\|chat\|version`, `-Prompt "..."` |
| `Run-Agy.ps1` | Antigravity AGY | Google Antigravity CLI агент | `-Action check\|chat\|models\|update\|version`, `-Prompt "..."` |

---

## 🤖 Запуск лончеров агентами ИИ

### Базовый синтаксис

```powershell
# Из корня проекта
.\Run-<ServiceName>.ps1

# Через переменную окружения AIBREADBOARD_DIR
& "$env:AIBREADBOARD_DIR\Run-<ServiceName>.ps1"
```

### Примеры

```powershell
# Запуск главного сервера (FastAPI + Foundry)
.\run.ps1

# Только FastAPI сервер
.\Run-Unicorn.ps1

# Foundry с параметром действия
.\Run-Foundry.ps1 -Action start
.\Run-Foundry.ps1 -Action stop
.\Run-Foundry.ps1 -Action status
```

### Проверка состояния

```powershell
# FastAPI health-check
Invoke-WebRequest -Uri "https://localhost:3000/health" -SkipCertificateCheck

# Проверить занятость порта
netstat -aon | Select-String ":3000"
```

### Остановка сервисов

# Остановить сервисы
$pid_ = (netstat -aon | Select-String ":3000\s" | ForEach-Object { ($_ -split "\s+")[-1] } | Select-Object -First 1)
if ($pid_) { Stop-Process -Id $pid_ -Force }
```

---

## ➕ Как создать новый лончер

### Правила именования

- **Файл:** `Run-<ServiceName>.ps1` (PascalCase)
- **Расположение:** корень проекта (`$env:AIBREADBOARD_DIR`)
- **Примеры:** `Run-Redis.ps1`, `Run-Worker.ps1`, `Run-Scheduler.ps1`

### Шаблон нового лончера

```powershell
<#
.SYNOPSIS
    Запускает <ServiceName>.

.DESCRIPTION
    Описание сервиса. Читает конфигурацию из .env и config.json.

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

# === Загрузка .env ===
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
    'status' { <# TODO: проверка состояния #> }
}
```

### Чек-лист нового лончера

- [ ] Файл назван `Run-<ServiceName>.ps1`
- [ ] Помещён в **корень** репозитория
- [ ] Содержит `.SYNOPSIS` и `.DESCRIPTION`
- [ ] Читает `.env` при старте
- [ ] Выводит чёткий статус
- [ ] Добавлена запись в таблицу "Реестр лончеров" выше

---

## 🔧 Вспомогательные скрипты (не лончеры)

| Скрипт | Назначение |
|--------|------------ |
| `install.ps1` | Установка проекта и venv |
| `install.cmd` | Установка (CMD вариант) |
| `install_ssl_cert.ps1` | Генерация SSL-сертификата |
| `run_tests.ps1` | Запуск тестов pytest |

---

## 📁 Структура проекта

```
AI Breadboard/
├── 📄 run.ps1 + Run-*.ps1    # Лончеры сервисов
├── 📄 main.py                # FastAPI приложение
├── 📄 manage_tools.py        # Универсальный CLI агентов
├── 📄 header.py              # Определение __root__ проекта
├── 📁 core/                   # Основной код (AI, FastAPI, TTS, rag, utils...)
│   └── 📁 rag/                # Подсистема RAG (RAG-First пайплайн, RulesRAG)
├── 📁 tools/                 # Служебные инструменты
│   ├── 📁 ai/                # Инструменты агентов ИИ (RAG, поиск)
│   └── 📁 setup/             # Настройка кодовой базы
├── 📁 tmp/                   # Временные файлы и отчёты (tmp/reports/, tmp/logs/, tmp/rag/)
├── 📁 __skills/              # Навыки агентов (Antigravity)
├── 📁 tests/                 # Тесты (pytest)
├── 📁 .gemini/               # Конфигурация Gemini AI
└── 📁 .ai_instructions/      # Инструкции для ИИ
```

---

## 🔗 Связанные документы

- [`manage_tools.py`](../manage_tools.py) — CLI для управления инструментами проекта
- [`.ai_instructions/knowledge/scripts_tools.md`](scripts_tools.md) — справочник скриптов
- [`.ai_instructions/knowledge/MODEL_SCRIPT_EXECUTION_GUIDE.md`](MODEL_SCRIPT_EXECUTION_GUIDE.md) — руководство для моделей ИИ
- [`tools/README.md`](../../tools/README.md) — инструменты проекта
