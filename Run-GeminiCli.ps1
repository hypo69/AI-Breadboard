<#
.SYNOPSIS
    Проверка, установка и запуск Google Gemini CLI (@google/gemini-cli).

.DESCRIPTION
    Скрипт для проверки наличия Gemini CLI в системе, автоматического предложения
    установки через npm при отсутствии, настройки API-ключей из .env и запуска
    интерактивной сессии или одиночных запросов.

.PARAMETER Action
    Действие для выполнения:
    - 'check': Проверить наличие и статус Gemini CLI
    - 'install': Установить/обновить Gemini CLI через npm
    - 'chat': Запустить интерактивную консольную сессию
    - 'version': Показать версию утилиты
    По умолчанию: 'check'.

.PARAMETER Prompt
    Опциональный разовый текстовый запрос для выполнения через Gemini CLI.

.PARAMETER Model
    Модель Gemini для запроса (по умолчанию из config.json или gemini-2.5-flash).

.PARAMETER Help
    Отображение справки по использованию скрипта (-Help, -h, --help).

.EXAMPLE
    .\Run-GeminiCli.ps1
    .\Run-GeminiCli.ps1 -Action install
    .\Run-GeminiCli.ps1 -Action chat
    .\Run-GeminiCli.ps1 -Prompt "Привет, расскажи о проекте"
    .\Run-GeminiCli.ps1 --help
#>

[CmdletBinding()]
param (
    [ValidateSet('check', 'install', 'chat', 'version', 'status')]
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
$env:AIBREADBOARD_DIR = $scriptDir
$env:ASSIST_DIR = $scriptDir

# ============================================
# ВЫВОД СПРАВКИ (--help / -h / -Help)
# ============================================
if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║           Run-GeminiCli.ps1 — СПРАВКА И ПАРАМЕТРЫ             ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Проверка, установка и запуск консольного агента Google Gemini CLI."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\Run-GeminiCli.ps1 [-Action <check|install|chat|version>]"
    Write-Host "  .\Run-GeminiCli.ps1 -Prompt `"ваш вопрос`""
    Write-Host "  .\Run-GeminiCli.ps1 --help"
    Write-Host ""
    Write-Host "ПАРАМЕТРЫ:" -ForegroundColor Yellow
    Write-Host "  -Action <string>    Действие: check (по умолчанию), install, chat, version."
    Write-Host "  -Prompt <string>    Выполнить разовый запрос к модели."
    Write-Host "  -Model <string>     Модель (например: gemini-2.5-flash, gemini-3.1-flash-lite)."
    Write-Host "  -Help, -h, --help   Показать эту справку и выйти."
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\Run-GeminiCli.ps1"
    Write-Host "  .\Run-GeminiCli.ps1 -Action install"
    Write-Host "  .\Run-GeminiCli.ps1 -Action chat"
    Write-Host "  .\Run-GeminiCli.ps1 -Prompt `"Объясни архитектуру FastAPI`""
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              GOOGLE GEMINI CLI — ДИАГНОСТИКА И ЗАПУСК         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# [1/4] ЗАГРУЗКА .ENV И КОНФИГУРАЦИИ
# ============================================
$envFile = Join-Path $scriptDir ".env"
$geminiApiKey = $null

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -in @("GEMINI_API_KEY", "GOOGLE_API_KEY", "AGY_API_KEY")) {
                if (-not $geminiApiKey -and $val) {
                    $geminiApiKey = $val
                }
            }
        }
    }
}

# Экспорт API-ключа в сессию для gemini-cli
if ($geminiApiKey) {
    $env:GEMINI_API_KEY = $geminiApiKey
}

$configPath = Join-Path $scriptDir "config.json"
$defaultModel = "gemini-2.5-flash"
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($cfg.ai.gemini_cli_model_id) {
            $defaultModel = [string]$cfg.ai.gemini_cli_model_id
        } elseif ($cfg.web_search.gemini_cli_model) {
            $defaultModel = [string]$cfg.web_search.gemini_cli_model
        }
    } catch {}
}

if (-not $Model) {
    $Model = $defaultModel
}

# ============================================
# [2/4] ПОИСК ИСПОЛНЯЕМОГО ФАЙЛА GEMINI CLI
# ============================================
function Find-GeminiCli {
    $candidates = @("gemini.cmd", "gemini.exe", "gemini.ps1", "gemini")
    foreach ($c in $candidates) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source) {
            return $cmd.Source
        }
    }

    # Стандартные пути npm global в Windows
    $npmPath = Join-Path $env:APPDATA "npm\gemini.cmd"
    if (Test-Path $npmPath) {
        return $npmPath
    }

    $progFilesNpm = Join-Path $env:ProgramFiles "nodejs\gemini.cmd"
    if (Test-Path $progFilesNpm) {
        return $progFilesNpm
    }

    return $null
}

function Install-GeminiCli {
    Write-Host ""
    Write-Host "📦 Установка Google Gemini CLI (@google/gemini-cli)..." -ForegroundColor Cyan
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        Write-Host "❌ Ошибка: Менеджер пакетов npm / Node.js не найден в системе!" -ForegroundColor Red
        Write-Host "   Для работы Gemini CLI требуется установленный Node.js (https://nodejs.org/)." -ForegroundColor Yellow
        $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetCmd) {
            $installNode = Read-Host "   Установить Node.js через winget прямо сейчас? (Y/n)"
            if ($installNode.Trim().ToLower() -in @("", "y", "yes", "д", "да", "1")) {
                Write-Host "   Запуск winget install OpenJS.NodeJS.LTS..." -ForegroundColor Cyan
                & winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
                Write-Host "   После установки Node.js перезапустите терминал и повторите запуск." -ForegroundColor Yellow
            }
        }
        return $false
    }

    Write-Host "   Выполняется: npm install -g @google/gemini-cli" -ForegroundColor DarkGray
    try {
        & npm install -g @google/gemini-cli
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Google Gemini CLI успешно установлен!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Ошибка установки Gemini CLI через npm (код $LASTEXITCODE)." -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Ошибка при вызове npm: $_" -ForegroundColor Red
        return $false
    }
}

$cliPath = Find-GeminiCli

# ============================================
# [3/4] ОБРАБОТКА СИТУАЦИИ, ЕСЛИ CLI НЕ НАЙДЕН
# ============================================
if (-not $cliPath -or $Action -eq 'install') {
    if (-not $cliPath) {
        Write-Host "[WARN] Google Gemini CLI (@google/gemini-cli) не найден в системе!" -ForegroundColor Yellow
        Write-Host ""
        $answer = Read-Host "Хотите установить Google Gemini CLI прямо сейчас через npm? (Y/n) [Enter = Да]"
        $answer = $answer.Trim().ToLower()
        if ($answer -in @("", "y", "yes", "д", "да", "1")) {
            $installed = Install-GeminiCli
            if ($installed) {
                $cliPath = Find-GeminiCli
            }
        } else {
            Write-Host ""
            Write-Host "Установка пропущена. Вы можете установить утилиту вручную командой:" -ForegroundColor Yellow
            Write-Host "  npm install -g @google/gemini-cli" -ForegroundColor Cyan
            Write-Host ""
            exit 1
        }
    } else {
        # При явном вызове -Action install
        $installed = Install-GeminiCli
        if ($installed) {
            $cliPath = Find-GeminiCli
        }
    }
}

if (-not $cliPath) {
    Write-Host "❌ Исполняемый файл gemini не найден. Перезапустите консоль после установки." -ForegroundColor Red
    exit 1
}

# Определение версии
$versionStr = "Неизвестно"
try {
    $verOut = & $cliPath --version 2>$null
    if ($verOut) { $versionStr = $verOut.Trim() }
} catch {}

Write-Host "    [OK] Gemini CLI найден: $cliPath" -ForegroundColor Green
Write-Host "    Версия:       $versionStr" -ForegroundColor Gray
Write-Host "    Модель:       $Model" -ForegroundColor Gray
if ($env:GEMINI_API_KEY) {
    Write-Host "    API-ключ:     Загружен из .env" -ForegroundColor Green
} else {
    Write-Host "    [WARN] API-ключ (GEMINI_API_KEY) не найден в .env!" -ForegroundColor Yellow
}
Write-Host ""

# ============================================
# [4/4] ВЫПОЛНЕНИЕ ДЕЙСТВИЙ (PROMPT / CHAT / CHECK)
# ============================================
if ($Action -eq 'version') {
    Write-Host "Версия Gemini CLI: $versionStr" -ForegroundColor Green
    exit 0
}

# Если передан прямой текстовый запрос (-Prompt)
if ($Prompt) {
    Write-Host "💬 Запрос: $Prompt" -ForegroundColor Cyan
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath -m $Model $Prompt
    exit $LASTEXITCODE
}

# Если запрошен интерактивный чат (-Action chat)
if ($Action -eq 'chat') {
    Write-Host "🚀 Запуск интерактивного диалога Gemini CLI (Ctrl+C для выхода)..." -ForegroundColor Green
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    & $cliPath -m $Model
    exit $LASTEXITCODE
}

# Режим проверки (по умолчанию)
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  GEMINI CLI ГОТОВ К РАБОТЕ                                    ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Команды для работы:" -ForegroundColor Yellow
Write-Host "  .\Run-GeminiCli.ps1 -Action chat              # Интерактивный диалог"
Write-Host "  .\Run-GeminiCli.ps1 -Prompt `"Ваш вопрос`"     # Разовый запрос"
Write-Host "  .\Run-GeminiCli.ps1 -Action install           # Обновление пакета"
Write-Host ""
