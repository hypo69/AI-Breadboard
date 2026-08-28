<#
.SYNOPSIS
    Проверка, установка и запуск Google Antigravity CLI (agy).

.DESCRIPTION
    Скрипт для проверки наличия Antigravity CLI (agy) в системе, предложения
    установки/обновления при отсутствии, настройки API-ключей из .env и запуска
    интерактивной сессии или разовых запросов к агенту.

.PARAMETER Action
    Действие для выполнения:
    - 'check': Проверить наличие и статус agy CLI (по умолчанию)
    - 'chat': Запустить интерактивную консольную сессию agy
    - 'models': Показать список доступных моделей (agy models)
    - 'update': Обновить утилиту agy до актуальной версии (agy update)
    - 'version': Показать версию утилиты (agy --version)
    - 'status': Показать текущий статус окружения

.PARAMETER Prompt
    Опциональный разовый текстовый запрос для выполнения через agy --print.

.PARAMETER Model
    Модель для запроса (по умолчанию из config.json или agy-flash).

.PARAMETER Help
    Отображение справки по использованию скрипта (-Help, -h, --help).

.EXAMPLE
    .\Run-Agy.ps1
    .\Run-Agy.ps1 -Action chat
    .\Run-Agy.ps1 -Action models
    .\Run-Agy.ps1 -Prompt "Объясни устройство Antigravity"
    .\Run-Agy.ps1 --help
#>

[CmdletBinding()]
param (
    [ValidateSet('check', 'chat', 'models', 'update', 'version', 'status', 'install')]
    [string]$Action = 'check',

    [Parameter(Position = 0)]
    [string]$Prompt = '',

    [string]$Model = '',

    [Alias('h', '-help')]
    [switch]$Help
)

$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir) -and $env:AIBREADBOARD_DIR -and (Test-Path $env:AIBREADBOARD_DIR)) {
    $scriptDir = $env:AIBREADBOARD_DIR
}
if ([string]::IsNullOrEmpty($scriptDir) -and $MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

# Определение корня проекта (если скрипт находится в директории launchers/)
$projectRoot = $scriptDir
if ((Split-Path -Leaf $projectRoot) -eq "launchers" -or -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if (Test-Path (Join-Path $parent "main.py")) {
        $projectRoot = $parent
    }
}
$env:AIBREADBOARD_DIR = $projectRoot
$env:ASSIST_DIR = $projectRoot

# ============================================
# ВЫВОД СПРАВКИ (--help / -h / -Help)
# ============================================
if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║              Run-Agy.ps1 — СПРАВКА И ПАРАМЕТРЫ                ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Проверка, установка и запуск консольного агента Google Antigravity (agy)."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\Run-Agy.ps1 [-Action <check|chat|models|update|version>]"
    Write-Host "  .\Run-Agy.ps1 -Prompt `"ваш вопрос`""
    Write-Host "  .\Run-Agy.ps1 --help"
    Write-Host ""
    Write-Host "ПАРАМЕТРЫ:" -ForegroundColor Yellow
    Write-Host "  -Action <string>    Действие: check (по умолчанию), chat, models, update, version."
    Write-Host "  -Prompt <string>    Выполнить разовый запрос к модели без входа в интерактив."
    Write-Host "  -Model <string>     Модель (например: agy-flash, agy-pro, gemma)."
    Write-Host "  -Help, -h, --help   Показать эту справку и выйти."
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\Run-Agy.ps1"
    Write-Host "  .\Run-Agy.ps1 -Action chat"
    Write-Host "  .\Run-Agy.ps1 -Action models"
    Write-Host "  .\Run-Agy.ps1 -Prompt `"Оптимизируй алгоритм поиска`""
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          GOOGLE ANTIGRAVITY (AGY) — ДИАГНОСТИКА И ЗАПУСК      ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# [1/4] ЗАГРУЗКА .ENV И КОНФИГУРАЦИИ
# ============================================
$envFile = Join-Path $projectRoot ".env"
$agyApiKey = $null

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -in @("AGY_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")) {
                if (-not $agyApiKey -and $val) {
                    $agyApiKey = $val
                }
            }
        }
    }
}

if ($agyApiKey) {
    $env:AGY_API_KEY = $agyApiKey
    $env:GEMINI_API_KEY = $agyApiKey
}

$configPath = Join-Path $projectRoot "config.json"
$defaultModel = "agy-flash"
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($cfg.ai.agy_model_id) {
            $defaultModel = [string]$cfg.ai.agy_model_id
        } elseif ($cfg.web_search.agy_model) {
            $defaultModel = [string]$cfg.web_search.agy_model
        }
    } catch {}
}

if (-not $Model) {
    $Model = $defaultModel
}

# ============================================
# [2/4] ПОИСК ИСПОЛНЯЕМОГО ФАЙЛА AGY CLI
# ============================================
function Find-AgyCli {
    $candidates = @("agy.exe", "agy.cmd", "agy.ps1", "agy")
    foreach ($c in $candidates) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source) {
            return $cmd.Source
        }
    }

    # Стандартные пути установки Antigravity в Windows
    $localAgy = Join-Path $env:LOCALAPPDATA "agy\bin\agy.exe"
    if (Test-Path $localAgy) {
        return $localAgy
    }

    $geminiAgy = Join-Path $env:USERPROFILE ".gemini\antigravity\bin\agy.exe"
    if (Test-Path $geminiAgy) {
        return $geminiAgy
    }

    $progAgy = Join-Path $env:ProgramFiles "Antigravity\bin\agy.exe"
    if (Test-Path $progAgy) {
        return $progAgy
    }

    return $null
}

function Install-AgyCli {
    Write-Host ""
    Write-Host "📦 Установка Google Antigravity CLI (agy)..." -ForegroundColor Cyan
    $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
    if ($wingetCmd) {
        Write-Host "   Попытка установки через Windows Package Manager (winget)..." -ForegroundColor DarkGray
        try {
            & winget install Google.Antigravity --silent --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Google Antigravity успешно установлен через winget!" -ForegroundColor Green
                return $true
            }
        } catch {}
    }

    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if ($npmCmd) {
        Write-Host "   Попытка установки через npm (antigravity-cli / @google/antigravity)..." -ForegroundColor DarkGray
        try {
            & npm install -g antigravity-cli 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Antigravity CLI успешно установлен через npm!" -ForegroundColor Green
                return $true
            }
        } catch {}
    }

    Write-Host "ℹ️ Автоматическая установка через winget/npm не удалась." -ForegroundColor Yellow
    Write-Host "   Пожалуйста, установите Google Antigravity с официального сайта или через инсталлятор." -ForegroundColor Yellow
    return $false
}

$cliPath = Find-AgyCli

# ============================================
# [3/4] ОБРАБОТКА СИТУАЦИИ, ЕСЛИ AGY НЕ НАЙДЕН
# ============================================
if (-not $cliPath -or $Action -in @('install', 'update')) {
    if (-not $cliPath) {
        Write-Host "[WARN] Google Antigravity CLI (agy) не найден в системе!" -ForegroundColor Yellow
        Write-Host ""
        $answer = Read-Host "Хотите попробовать установить Google Antigravity CLI сейчас? (Y/n) [Enter = Да]"
        $answer = $answer.Trim().ToLower()
        if ($answer -in @("", "y", "yes", "д", "да", "1")) {
            $installed = Install-AgyCli
            if ($installed) {
                $cliPath = Find-AgyCli
            }
        } else {
            Write-Host ""
            Write-Host "Установка пропущена. Для работы agy скачайте дистрибутив Antigravity." -ForegroundColor Yellow
            Write-Host ""
            exit 1
        }
    } elseif ($Action -eq 'update') {
        Write-Host "🔄 Обновление Antigravity CLI..." -ForegroundColor Cyan
        & $cliPath update
        exit $LASTEXITCODE
    }
}

if (-not $cliPath) {
    Write-Host "❌ Исполняемый файл agy не найден. Перезапустите консоль после установки." -ForegroundColor Red
    exit 1
}

# Определение версии
$versionStr = "Неизвестно"
try {
    $verOut = & $cliPath --version 2>$null
    if ($verOut) { $versionStr = $verOut.Trim() }
} catch {}

Write-Host "    [OK] Antigravity CLI найден: $cliPath" -ForegroundColor Green
Write-Host "    Версия:       $versionStr" -ForegroundColor Gray
Write-Host "    Модель:       $Model" -ForegroundColor Gray
if ($env:AGY_API_KEY -or $env:GEMINI_API_KEY) {
    Write-Host "    API-ключ:     Загружен из .env" -ForegroundColor Green
} else {
    Write-Host "    [WARN] API-ключ (AGY_API_KEY / GEMINI_API_KEY) не найден в .env!" -ForegroundColor Yellow
}
Write-Host ""

# ============================================
# [4/4] ВЫПОЛНЕНИЕ ДЕЙСТВИЙ (PROMPT / CHAT / MODELS)
# ============================================
if ($Action -eq 'version') {
    Write-Host "Версия Antigravity CLI: $versionStr" -ForegroundColor Green
    exit 0
}

if ($Action -eq 'models') {
    Write-Host "📋 Список доступных моделей Antigravity:" -ForegroundColor Cyan
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath models
    exit $LASTEXITCODE
}

# Если передан прямой текстовый запрос (-Prompt)
if ($Prompt) {
    Write-Host "💬 Запрос к agy: $Prompt" -ForegroundColor Cyan
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath --print $Prompt
    exit $LASTEXITCODE
}

# Если запрошен интерактивный чат (-Action chat)
if ($Action -eq 'chat') {
    Write-Host "🚀 Запуск интерактивной консоли Google Antigravity (agy)..." -ForegroundColor Green
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath
    exit $LASTEXITCODE
}

# Режим проверки (по умолчанию)
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ANTIGRAVITY CLI (AGY) ГОТОВ К РАБОТЕ                         ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Команды для работы:" -ForegroundColor Yellow
Write-Host "  .\Run-Agy.ps1 -Action chat              # Интерактивная консоль"
Write-Host "  .\Run-Agy.ps1 -Action models            # Список моделей"
Write-Host "  .\Run-Agy.ps1 -Prompt `"Ваш вопрос`"     # Разовый запрос"
Write-Host "  .\Run-Agy.ps1 -Action update            # Обновление CLI"
Write-Host ""
