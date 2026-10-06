<#
=============================================================================
Process Name: AI-Breadboard Automation - Run LibreHardwareMonitor (LHM)
=============================================================================
Description:
  Специализированный лончер для управления процессом LibreHardwareMonitor (LHM).

  Зачем нужен этот скрипт:
    1. Управление жизненным циклом LHM: старт, остановка, перезапуск и мониторинг статуса.
    2. Проверка доступности встроенного веб-сервера (http://localhost:8085/data.json).
    3. Поддержка фонового запуска, минимизации в трей и повышения привилегий (RunAs Administrator).

File: Run-LHM.ps1
Project: ai-breadboard
Package: apps/windows/telemetry/launchers
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-06 01:26:00
=============================================================================

.SYNOPSIS
    Лончер для запуска и управления LibreHardwareMonitor в AI-Breadboard.

.DESCRIPTION
    Запускает LibreHardwareMonitor.exe из директории bin/LibreHardwareMonitor,
    проверяет его активность, статус веб-сервера JSON API и управляет процессом.

.PARAMETER Action
    Действие: start (по умолчанию), stop, restart, status, open-web.

.PARAMETER Background
    Запустить процесс в фоновом/минимизированном режиме.

.PARAMETER AsAdmin
    Запустить от имени Администратора для доступа к низкоуровневым датчикам оборудования.

.PARAMETER Port
    TCP-порт веб-сервера LibreHardwareMonitor (по умолчанию 8085).

.PARAMETER OpenWeb
    Открыть веб-интерфейс LHM в браузере после старта.

.EXAMPLE
    .\Run-LHM.ps1 -Action start
    Запуск LibreHardwareMonitor в стандартном режиме.

.EXAMPLE
    .\Run-LHM.ps1 -Background -AsAdmin
    Фоновый запуск от имени администратора.

.EXAMPLE
    .\Run-LHM.ps1 -Action status
    Проверка статуса процесса и доступности веб-сервера.
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status', 'open-web', 'gui')]
    [string]$Action = 'start',

    [Alias('bg', 'Minimized', 'Hide')]
    [switch]$Background,

    [Alias('Silent', 'NoOutput')]
    [switch]$Quiet,

    [Alias('Admin', 'Elevated')]
    [switch]$AsAdmin,

    [int]$Port = 8085,

    [Alias('Web', 'Browser')]
    [switch]$OpenWeb,

    [switch]$Restart,

    [switch]$Force,

    [Alias('h', '-help')]
    [switch]$Help
)

if ($Quiet) {
    $Background = $true
}

if ($Restart -or $Force) {
    $Action = 'restart'
}
if ($OpenWeb) {
    $Action = 'open-web'
}

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Определение корневой директории проекта
$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir) -and $env:AIBREADBOARD_DIR -and (Test-Path $env:AIBREADBOARD_DIR)) {
    $scriptDir = Join-Path $env:AIBREADBOARD_DIR "apps\windows\telemetry\launchers"
}
if ([string]::IsNullOrEmpty($scriptDir) -and $MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

$projectRoot = $scriptDir
while ($projectRoot -and -not (Test-Path (Join-Path $projectRoot "pyproject.toml")) -and -not (Test-Path (Join-Path $projectRoot "bin"))) {
    $parent = Split-Path -Parent $projectRoot
    if ($parent -eq $projectRoot) { break }
    $projectRoot = $parent
}
if (-not (Test-Path (Join-Path $projectRoot "bin"))) {
    $projectRoot = (Get-Location).Path
}

# Поиск исполняемого файла LibreHardwareMonitor.exe
$lhmCandidates = @(
    (Join-Path $projectRoot "bin\LibreHardwareMonitor\LibreHardwareMonitor.exe"),
    (Join-Path $scriptDir "..\..\..\bin\LibreHardwareMonitor\LibreHardwareMonitor.exe"),
    (Join-Path $env:ProgramFiles "LibreHardwareMonitor\LibreHardwareMonitor.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "LibreHardwareMonitor\LibreHardwareMonitor.exe")
)

$lhmExe = $null
foreach ($cand in $lhmCandidates) {
    if (Test-Path $cand) {
        $lhmExe = (Resolve-Path $cand).Path
        break
    }
}

$webUrl = "http://localhost:$Port/data.json"
$webGuiUrl = "http://localhost:$Port/"

if ($Help) {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║       🌡️  AI BREADBOARD — УПРАВЛЕНИЕ LIBREHARDWAREMONITOR (LHM)             ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Управление запуском и состоянием службы датчиков LibreHardwareMonitor."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\Run-LHM.ps1 [-Action start|stop|restart|status|open-web]"
    Write-Host "  .\Run-LHM.ps1 -Background                  # Запуск в свернутом/фоновом режиме"
    Write-Host "  .\Run-LHM.ps1 -AsAdmin                     # Запуск с правами Администратора"
    Write-Host "  .\Run-LHM.ps1 -OpenWeb                     # Открыть веб-интерфейс в браузере"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\Run-LHM.ps1                              # Запуск LHM"
    Write-Host "  .\Run-LHM.ps1 -Action status               # Проверить статус процесса и веб-сервера"
    Write-Host "  .\Run-LHM.ps1 -Action stop                 # Остановить процесс LHM"
    Write-Host "  .\Run-LHM.ps1 -Restart -AsAdmin            # Перезапуск с правами администратора"
    Write-Host ""
    exit 0
}

function Get-LhmProcess {
    return Get-Process -Name "LibreHardwareMonitor" -ErrorAction SilentlyContinue
}

function Test-LhmWebServer {
    param([int]$TimeoutSec = 2)
    try {
        $req = [System.Net.WebRequest]::Create($webUrl)
        $req.Timeout = $TimeoutSec * 1000
        $resp = $req.GetResponse()
        $resp.Close()
        return $true
    } catch {
        return $false
    }
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STATUS
# -------------------------------------------------------------
if ($Action -eq 'status') {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║       📊 СТАТУС LIBREHARDWAREMONITOR                         ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    $procs = Get-LhmProcess
    if ($procs) {
        Write-Host "✅ Процесс LibreHardwareMonitor активен:" -ForegroundColor Green
        foreach ($p in $procs) {
            $wsMb = [math]::Round($p.WorkingSet64 / 1MB, 1)
            $cpuSec = [math]::Round($p.CPU, 2)
            Write-Host "   • PID: $($p.Id) | Имя: $($p.ProcessName) | RAM: $wsMb МБ | CPU: ${cpuSec}с" -ForegroundColor Cyan
        }
    } else {
        Write-Host "❌ Процесс LibreHardwareMonitor не запущен." -ForegroundColor Yellow
    }

    $isWebRunning = Test-LhmWebServer
    if ($isWebRunning) {
        Write-Host "🌐 Веб-сервер LHM (порт $Port): ДОСТУПЕН ($webUrl)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Веб-сервер LHM (порт $Port): НЕ ОТВЕЧАЕТ" -ForegroundColor Yellow
        Write-Host "   (Убедитесь, что в интерфейсе LHM включена опция: Options -> Remote Web Server -> Run)" -ForegroundColor DarkGray
    }

    if ($lhmExe) {
        Write-Host "📁 Исполняемый файл: $lhmExe" -ForegroundColor DarkGray
    } else {
        Write-Host "⚠️ Исполняемый файл LibreHardwareMonitor.exe не найден в bin!" -ForegroundColor Red
    }

    Write-Host ""
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STOP / RESTART
# -------------------------------------------------------------
if ($Action -in @('stop', 'restart')) {
    $procs = Get-LhmProcess
    if ($procs) {
        Write-Host "🛑 Остановка процессов LibreHardwareMonitor..." -ForegroundColor Yellow
        foreach ($p in $procs) {
            try {
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
                Write-Host "   [OK] Остановлен PID $($p.Id)" -ForegroundColor DarkGray
            } catch {
                Write-Host "   [ERR] Не удалось остановить PID $($p.Id): $_" -ForegroundColor Red
            }
        }
        Start-Sleep -Milliseconds 800
    } else {
        Write-Host "ℹ️ Процесс LibreHardwareMonitor не был запущен." -ForegroundColor DarkGray
    }

    if ($Action -eq 'stop') {
        Write-Host "✅ LibreHardwareMonitor остановлен." -ForegroundColor Green
        exit 0
    }
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: OPEN-WEB
# -------------------------------------------------------------
if ($Action -eq 'open-web') {
    $isWeb = Test-LhmWebServer
    if (-not $isWeb) {
        $procs = Get-LhmProcess
        if (-not $procs) {
            Write-Host "ℹ️ LibreHardwareMonitor не запущен. Запускаем..." -ForegroundColor Cyan
            & $PSCommandPath -Action start -Background
            Start-Sleep -Seconds 2
        }
    }
    Write-Host "🌐 Открытие веб-интерфейса LHM в браузере: $webGuiUrl" -ForegroundColor Green
    Start-Process $webGuiUrl
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: START / RESTART / GUI
# -------------------------------------------------------------
if ($Action -in @('start', 'restart', 'gui')) {
    if (-not $lhmExe -or -not (Test-Path $lhmExe)) {
        Write-Host "❌ Исполняемый файл LibreHardwareMonitor.exe не найден!" -ForegroundColor Red
        Write-Host "   Проверьте путь: $projectRoot\bin\LibreHardwareMonitor\LibreHardwareMonitor.exe" -ForegroundColor Yellow
        exit 1
    }

    $existing = Get-LhmProcess
    if ($existing -and $Action -ne 'restart') {
        if (-not $Quiet) {
            $pids = ($existing | ForEach-Object { $_.Id }) -join ', '
            Write-Host "✅ LibreHardwareMonitor уже запущен (PID: $pids)." -ForegroundColor Green
            
            $isWeb = Test-LhmWebServer
            if ($isWeb) {
                Write-Host "🌐 Веб-сервер LHM активен на порту $Port ($webUrl)" -ForegroundColor Green
            } else {
                Write-Host "⚠️ Веб-сервер LHM не отвечает на порту $Port" -ForegroundColor Yellow
            }
        }
        exit 0
    }

    if (-not $Quiet) {
        Write-Host "🚀 Запуск LibreHardwareMonitor..." -ForegroundColor Cyan
        Write-Host "   Файл: $lhmExe" -ForegroundColor DarkGray
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $lhmExe
    $psi.WorkingDirectory = Split-Path -Parent $lhmExe

    if ($Background -or $Quiet) {
        $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $psi.CreateNoWindow = $true
    }

    if ($AsAdmin) {
        $psi.Verb = 'RunAs'
    }

    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
        if (-not $Quiet) {
            if ($proc) {
                Write-Host "✅ LibreHardwareMonitor успешно запущен (PID: $($proc.Id))" -ForegroundColor Green
            } else {
                Start-Sleep -Milliseconds 1000
                $started = Get-LhmProcess
                if ($started) {
                    Write-Host "✅ LibreHardwareMonitor запущен (PID: $(($started | Select-Object -First 1).Id))" -ForegroundColor Green
                } else {
                    Write-Host "⚠️ Процесс инициирован, ожидание регистрации в системе..." -ForegroundColor Yellow
                }
            }
        }
    } catch {
        Write-Host "❌ Ошибка при запуске LibreHardwareMonitor: $_" -ForegroundColor Red
        exit 1
    }

    # Небольшая пауза для проверки старта веб-сервера
    Start-Sleep -Milliseconds 1200
    if (-not $Quiet) {
        if (Test-LhmWebServer) {
            Write-Host "🌐 Веб-сервер LHM активен ($webUrl)" -ForegroundColor Green
        } else {
            Write-Host "ℹ️ LHM запущен. Если требуется доступ по REST/JSON, включите Web Server в меню LHM." -ForegroundColor DarkGray
        }
    }
}
