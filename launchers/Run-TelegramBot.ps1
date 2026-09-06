<#
.SYNOPSIS
    Standalone Telegram bot launcher for ai-breadboard.

.DESCRIPTION
    Launches scripts/dev/bot_runner.py in background.
    Reads TELEGRAM_BOT_TOKEN from .env, validates environment and
    manages the bot process lifecycle.

.PARAMETER Action
    Action to perform: start | stop | restart | status (default: start).

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\launchers\Run-TelegramBot.ps1 -Action start
    .\launchers\Run-TelegramBot.ps1 -Action stop
    .\launchers\Run-TelegramBot.ps1 -Action status
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

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

$projectRoot = $scriptDir
if ((Split-Path -Leaf $projectRoot) -eq "launchers" -or -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if (Test-Path (Join-Path $parent "main.py")) {
        $projectRoot = $parent
    }
}
$env:AIBREADBOARD_DIR = $projectRoot
$env:ASSIST_DIR = $projectRoot

if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║           Run-TelegramBot.ps1 — HELP AND PARAMETERS           ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch Telegram bot in separate background process."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-TelegramBot.ps1 [-Action <start|stop|restart|status>]"
    Write-Host "  .\launchers\Run-TelegramBot.ps1 --help"
    Write-Host ""
    exit 0
}

$botScript = Join-Path $projectRoot "scripts\dev\bot_runner.py"
if (-not (Test-Path $botScript)) {
    Write-Host "[ERROR] bot_runner.py not found: $botScript" -ForegroundColor Red
    exit 1
}

$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
}

function Get-BotProcesses {
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match 'bot_runner\.py'
    }
}

$runningProcs = Get-BotProcesses

if ($Action -eq 'status') {
    if ($runningProcs) {
        $pids = ($runningProcs | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ Telegram bot is running (PID: $pids)" -ForegroundColor Green
    } else {
        Write-Host "❌ Telegram bot is not running." -ForegroundColor Yellow
    }
    exit 0
}

if ($Action -in @('stop', 'restart')) {
    if ($runningProcs) {
        Write-Host "🛑 Stopping Telegram bot..." -ForegroundColor Yellow
        $runningProcs | ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Host "    [OK] Stopped PID $($_.ProcessId)" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Seconds 1
    } else {
        Write-Host "ℹ️ Telegram bot was not running." -ForegroundColor DarkGray
    }
    if ($Action -eq 'stop') {
        exit 0
    }
}

if ($Action -in @('start', 'restart')) {
    $existing = Get-BotProcesses
    if ($existing) {
        $pids = ($existing | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ Telegram bot is already running (PID: $pids)" -ForegroundColor Green
        exit 0
    }

    # Verify token
    $envFile = Join-Path $projectRoot ".env"
    $tgToken = $env:TELEGRAM_BOT_TOKEN
    if (-not $tgToken -and (Test-Path $envFile)) {
        Get-Content $envFile | ForEach-Object {
            $line = $_.Trim()
            if ($line -and -not $line.StartsWith('#') -and $line -match "^TELEGRAM_BOT_TOKEN=(.*)$") {
                $tgToken = $Matches[1].Trim().Trim('"').Trim("'")
            }
        }
    }

    if (-not $tgToken) {
        Write-Host "[WARN] TELEGRAM_BOT_TOKEN is not configured in .env." -ForegroundColor Yellow
    }

    $logsDir = Join-Path $projectRoot "logs"
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
    }
    $logFilePath = Join-Path $logsDir "telegram_bot.log"

    Write-Host "    Starting Telegram bot in background process..." -ForegroundColor Cyan
    $botProc = Start-Process $venvPython -ArgumentList "`"$botScript`"" -PassThru -WindowStyle Minimized -RedirectStandardOutput $logFilePath -RedirectStandardError $logFilePath

    if ($botProc) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ✅ TELEGRAM BOT STARTED!                                       " -ForegroundColor Green
        Write-Host "  Script:   $botScript" -ForegroundColor DarkGray
        Write-Host "  PID:      $($botProc.Id)" -ForegroundColor DarkGray
        Write-Host "  Log:      $logFilePath" -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[ERROR] Failed to start Telegram bot process." -ForegroundColor Red
        exit 1
    }
}
