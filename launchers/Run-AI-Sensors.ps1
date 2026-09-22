<#
.SYNOPSIS
    Запуск AI-Sensors telemetry aggregator с modular structure.

.DESCRIPTION
    Запускает AI-Sensors telemetry aggregator:
    - HardwareMonitor (CPU, RAM, GPU, Disk, Network, Battery)
    - LibreHardwareMonitor Web API (дополнительные сенсоры)
    - DirectoryWatcher (файловые события)
    - InternetSpeedSensor (ping, download, upload, DNS)
    - JSON logging с ротацией файлов

.PARAMETER Action
    Действие: 'start' (по умолчанию), 'stop', 'restart', 'status'.

.PARAMETER Interval
    Интервал сбора метрик в секундах (по умолчанию: 60.0).

.PARAMETER ConfigFile
    Путь к файлу конфигурации config.json (по умолчанию: SANDBOX/ai-sensors/config.json).

.PARAMETER Help
    Показать справочную информацию.

.EXAMPLE
    .\launchers\Run-AI-Sensors.ps1
    .\launchers\Run-AI-Sensors.ps1 -Action status
    .\launchers\Run-AI-Sensors.ps1 -Action stop
    .\launchers\Run-AI-Sensors.ps1 -Interval 30.0
    .\launchers\Run-AI-Sensors.ps1 -ConfigFile SANDBOX/ai-sensors/config.json
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [float]$Interval = 60.0,

    [string]$ConfigFile = $null,

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
    if ((Test-Path (Join-Path $parent "main.py"))) {
        $projectRoot = $parent
    }
}

$aiSensorsDir = Join-Path $projectRoot "SANDBOX" "ai-sensors"
$aiSensorsMain = Join-Path $aiSensorsDir "main.py"
$aiSensorsConfig = if ($ConfigFile) { $ConfigFile } else { Join-Path $aiSensorsDir "config.json" }

if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║      Run-AI-Sensors.ps1 — Telemetry Aggregator                ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Запуск AI-Sensors telemetry aggregator с модульной структурой."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-AI-Sensors.ps1 [-Action start|stop|restart|status] [-Interval 60.0]"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-AI-Sensors.ps1                        # Запуск по умолчанию"
    Write-Host "  .\launchers\Run-AI-Sensors.ps1 -Action status        # Проверка статуса"
    Write-Host "  .\launchers\Run-AI-Sensors.ps1 -Action stop          # Остановка"
    Write-Host "  .\launchers\Run-AI-Sensors.ps1 -Interval 30.0        # Интервал 30 сек"
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

# Функция получения запущенных процессов AI-Sensors
function Get-AISensorsProcesses {
    param([string]$ScriptPath)
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match [regex]::Escape($ScriptPath)
    }
}

# Функция запуска AI-Sensors
function Start-AISensors {
    param([float]$Interval)

    if (-not (Test-PythonAvailable)) {
        Write-Host "❌ Python не найден" -ForegroundColor Red
        return $false
    }

    if (-not (Test-Path $aiSensorsMain)) {
        Write-Host "❌ main.py не найден: $aiSensorsMain" -ForegroundColor Red
        return $false
    }

    if (-not (Test-Path $aiSensorsConfig)) {
        Write-Host "❌ config.json не найден: $aiSensorsConfig" -ForegroundColor Red
        return $false
    }

    Write-Host "🚀 Запуск AI-Sensors telemetry aggregator..." -ForegroundColor Cyan
    Write-Host "   Конфигурация: $aiSensorsConfig" -ForegroundColor DarkGray
    Write-Host "   Интервал: ${Interval}с" -ForegroundColor DarkGray

    # Определяем Python executable
    $venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    }

    if (-not $venvPython) {
        Write-Host "❌ Python не найден в venv и в PATH" -ForegroundColor Red
        return $false
    }

    $appArgs = "`"$aiSensorsMain`""
    if ($Interval) {
        $appArgs += " --interval $Interval"
    }

    $logDir = Join-Path $aiSensorsDir "logs"
    $logFile = Join-Path $logDir "ai_sensors.log"

    # Создаем директорию для логов
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    }

    Write-Host "   Python: $venvPython" -ForegroundColor DarkGray
    Write-Host "   Лог-файл: $logFile" -ForegroundColor DarkGray
    Write-Host ""

    # Запускаем в фоновом режиме
    $proc = Start-Process $venvPython -ArgumentList $appArgs `
        -WorkingDirectory $aiSensorsDir `
        -PassThru `
        -WindowStyle Minimized `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError $logFile

    if ($proc) {
        Write-Host "✅ AI-Sensors запущен (PID: $($proc.Id))" -ForegroundColor Green
        Write-Host "   Лог-директория: $logDir" -ForegroundColor Cyan
        Write-Host ""
        return $true
    } else {
        Write-Host "❌ Не удалось запустить AI-Sensors" -ForegroundColor Red
        return $false
    }
}

$runningProcs = Get-AISensorsProcesses -ScriptPath $aiSensorsMain

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STATUS
# -------------------------------------------------------------
if ($Action -eq 'status') {
    Write-Host ""

    if ($runningProcs) {
        $pids = ($runningProcs | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ AI-Sensors запущен (PID: $pids)" -ForegroundColor Green
        Write-Host "   Лог-файл: $logFile" -ForegroundColor DarkGray
    } else {
        Write-Host "❌ AI-Sensors не запущен" -ForegroundColor Yellow
        Write-Host "   Для запуска: .\launchers\Run-AI-Sensors.ps1" -ForegroundColor DarkGray
    }

    Write-Host ""
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STOP / RESTART
# -------------------------------------------------------------
if ($Action -in @('stop', 'restart')) {
    if ($runningProcs) {
        Write-Host "🛑 Остановка AI-Sensors..." -ForegroundColor Yellow
        $runningProcs | ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Host "   [OK] Остановлен PID $($_.ProcessId)" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Seconds 1
    } else {
        Write-Host "ℹ️ AI-Sensors не был запущен" -ForegroundColor DarkGray
    }

    if ($Action -eq 'stop') {
        Write-Host "✅ AI-Sensors остановлен" -ForegroundColor Green
        exit 0
    }
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: START / RESTART
# -------------------------------------------------------------
if ($Action -in @('start', 'restart')) {
    $existing = Get-AISensorsProcesses -ScriptPath $aiSensorsMain
    if ($existing) {
        $pids = ($existing | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ AI-Sensors уже запущен (PID: $pids)" -ForegroundColor Green
        exit 0
    }

    $started = Start-AISensors -Interval $Interval

    if ($started) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ✅ AI-SENSORS ЗАПУЩЕН!                                       " -ForegroundColor Green
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Сенсоры:" -ForegroundColor Cyan
        Write-Host "   - HardwareMonitor (CPU, RAM, GPU, Disk, Network, Battery)" -ForegroundColor White
        Write-Host "   - LibreHardwareMonitor Web API" -ForegroundColor White
        Write-Host "   - DirectoryWatcher (файловые события)" -ForegroundColor White
        Write-Host "   - InternetSpeedSensor (ping, download, upload, DNS)" -ForegroundColor White
        Write-Host ""
        Write-Host "📈 Интервал сбора: ${Interval}с" -ForegroundColor Cyan
        Write-Host "📁 Лог-файл: $logFile" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host "❌ Не удалось запустить AI-Sensors" -ForegroundColor Red
        exit 1
    }
}
