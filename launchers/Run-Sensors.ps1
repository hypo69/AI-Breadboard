<#
.SYNOPSIS
    Запуск только сенсоров и автологгирования системных метрик.

.DESCRIPTION
    Запускает LibreHardwareMonitor для сбора аппаратных метрик.
    Python сервис логгирования отключен - сбор только в памяти.

.PARAMETER Action
    Действие: 'start' (по умолчанию), 'stop', 'restart', 'status'.

.PARAMETER Interval
    Интервал сбора метрик в секундах (по умолчанию: 1.0).

.PARAMETER TopProcesses
    Количество сохраняемых активных процессов (по умолчанию: 20).

.PARAMETER Help
    Показать справочную информацию.

.EXAMPLE
    .\launchers\Run-Sensors.ps1
    .\launchers\Run-Sensors.ps1 -Action status
    .\launchers\Run-Sensors.ps1 -Action stop
    .\launchers\Run-Sensors.ps1 -Interval 2.0 -TopProcesses 50
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [float]$Interval = 1.0,

    [int]$TopProcesses = 20,

    [Alias('h', '-help')]
    [switch]$Help
)

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Определение директории проекта
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
    if ((Test-Path (Join-Path $parent "main.py")) -or (Test-Path (Join-Path $parent "bin\LibreHardwareMonitor"))) {
        $projectRoot = $parent
    }
}

$lhmExe = Join-Path $projectRoot "bin\LibreHardwareMonitor\LibreHardwareMonitor.exe"

if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║         Run-Sensors.ps1 — Сенсоры и Автологгирование          ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Запуск только сенсоров и автологгирования системных метрик."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-Sensors.ps1 [-Action start|stop|restart|status] [-Interval 1.0] [-TopProcesses 20]"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-Sensors.ps1                        # Запуск сенсоров по умолчанию"
    Write-Host "  .\launchers\Run-Sensors.ps1 -Action status        # Проверка статуса сенсоров"
    Write-Host "  .\launchers\Run-Sensors.ps1 -Action stop          # Остановка сенсоров"
    Write-Host "  .\launchers\Run-Sensors.ps1 -Interval 2.0         # Интервал 2 секунды"
    Write-Host ""
    exit 0
}

# Функция проверки наличия Python
function Test-PythonAvailable {
    try {
        $python = Get-Command python -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Функция проверки наличия venv
function Test-VenvExists {
    return (Test-Path (Join-Path $projectRoot "venv"))
}

# Функция получения запущенных процессов LHM
function Get-LHMProcesses {
    Get-Process -Name "LibreHardwareMonitor" -ErrorAction SilentlyContinue
}

# Функция проверки веб-сервера LHM
function Test-LHMWebServer {
    param([int]$TimeoutSeconds = 3)
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8085/data.json" -TimeoutSec $TimeoutSeconds -ErrorAction Stop
        return @{ Success = $true; Data = $response }
    } catch {
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

# Функция запуска Python сервиса
function Start-PythonService {
    param([float]$Interval, [int]$TopProcesses)

    # Python сервис отключен - только сбор в памяти
    Write-Host "⚠️  Python сервис логгирования отключен (сбор только в памяти)" -ForegroundColor Yellow
    return $true
}

# Функция запуска LHM
function Start-LHM {
    if (-not (Test-Path $lhmExe)) {
        Write-Host "❌ Исполняемый файл LHM не найден по пути: $lhmExe" -ForegroundColor Red
        return $false
    }

    Write-Host "🚀 Запуск LibreHardwareMonitor..." -ForegroundColor Cyan

    $proc = Start-Process -FilePath $lhmExe `
                          -ArgumentList "/sensors", "/minimized" `
                          -WorkingDirectory (Split-Path -Parent $lhmExe) `
                          -WindowStyle Hidden `
                          -PassThru

    if ($proc) {
        Write-Host "✅ LibreHardwareMonitor запущен (PID: $($proc.Id))" -ForegroundColor Green
        
        # Ждем запуска веб-сервера
        Write-Host "⏳ Ожидание инициализации веб-сервера..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 3

        $testResult = Test-LHMWebServer -TimeoutSeconds 3
        if ($testResult.Success) {
            Write-Host "   [OK] Веб-сервер LHM активен и отвечает!" -ForegroundColor Green
        } else {
            Write-Host "   [WARN] Веб-сервер LHM не отвечает: $($testResult.Error)" -ForegroundColor Yellow
        }
        return $true
    } else {
        Write-Host "❌ Не удалось запустить LibreHardwareMonitor" -ForegroundColor Red
        return $false
    }
}

$runningLHM = Get-LHMProcesses

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STATUS
# -------------------------------------------------------------
if ($Action -eq 'status') {
    Write-Host ""
    
    # Статус LHM
    if ($runningLHM) {
        $pids = ($runningLHM | ForEach-Object { $_.Id }) -join ', '
        Write-Host "✅ LibreHardwareMonitor запущен (PID: $pids)" -ForegroundColor Green
    } else {
        Write-Host "❌ LibreHardwareMonitor не запущен" -ForegroundColor Yellow
    }

    Write-Host ""
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STOP / RESTART
# -------------------------------------------------------------
if ($Action -in @('stop', 'restart')) {
    if ($runningLHM) {
        Write-Host "🛑 Остановка LibreHardwareMonitor..." -ForegroundColor Yellow
        $runningLHM | ForEach-Object {
            try {
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                Write-Host "   [OK] Остановлен PID $($_.Id)" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Milliseconds 800
    }
    
    if ($Action -eq 'stop') {
        Write-Host "✅ Сенсоры остановлены" -ForegroundColor Green
        exit 0
    }
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: START / RESTART
# -------------------------------------------------------------
if ($Action -in @('start', 'restart')) {
    $started = $false

    # Запуск LHM
    if (Test-Path $lhmExe) {
        $lhmStarted = Start-LHM
        $started = $started -or $lhmStarted
    } else {
        Write-Host "⚠️ LibreHardwareMonitor не найден, пропускаем" -ForegroundColor Yellow
    }

    # Запуск Python сервиса
    $pythonStarted = Start-PythonService -Interval $Interval -TopProcesses $TopProcesses
    $started = $started -or $pythonStarted

    if ($started) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ✅ СЕНСОРЫ ЗАПУЩЕНЫ!                                         " -ForegroundColor Green
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 LibreHardwareMonitor запущен для сбора аппаратных метрик" -ForegroundColor Cyan
        Write-Host "📈 Интервал сбора: ${Interval}с" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host "❌ Не удалось запустить ни один компонент сенсоров" -ForegroundColor Red
        exit 1
    }
}
