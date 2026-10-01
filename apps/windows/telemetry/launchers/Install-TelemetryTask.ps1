# =============================================================================
# Process Name: AI-Breadboard Automation - Install-Telemetrytask Script
# =============================================================================
# Description:
#   PowerShell-сценарий системного обслуживания и запуска (Install-TelemetryTask).
#
# Usage Examples:
#   PowerShell Execution:
#     .\Install-TelemetryTask.ps1
#
# File: Install-TelemetryTask.ps1
# Project: ai-breadboard
# Package: apps.windows.telemetry.launchers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

# Description:
#   PowerShell-сценарий администрирования и автоматизации (Install-TelemetryTask).
#
# Usage Examples:
#   PowerShell Execution:
#     .\Install-TelemetryTask.ps1
#
# File: Install-TelemetryTask.ps1
# Project: ai-breadboard
# Package: windows/telemetry/launchers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:04:40
# =============================================================================

# Description:
#   PowerShell-сценарий системных операций и автоматизации (Install-TelemetryTask).
#
# Usage Examples:
#   PowerShell:
#     .\Install-TelemetryTask.ps1
#
# File: Install-TelemetryTask.ps1
# Project: ai-breadboard
# Package: windows/telemetry/launchers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 12:54:56
# =============================================================================

<#
# Updated: 2026-10-01 09:28:00
.SYNOPSIS
    Регистрация фоновой службы телеметрии AI-Breadboard в Windows Task Scheduler.

.DESCRIPTION
    Создает задание в Планировщике заданий Windows (Task Scheduler) с именем
    'AI-Breadboard-Telemetry'.
    Запускает ai-telemetry.exe в фоновом режиме с флагом WakeToRun (продолжает
    работать и будит систему для выполнения замеров, не прекращает работу при сне
    или питании от батареи, перезапускается при сбоях).
    Автоматически проверяет и инициализирует базу данных telemetry.db.

.PARAMETER Mode
    Режим сбора: 'hybrid' (по умолчанию), 'minimal', 'full'.

.PARAMETER Interval
    Интервал быстрого сбора в секундах (по умолчанию 5.0).

.PARAMETER HeavyInterval
    Интервал сбора тяжелых сенсоров в секундах (по умолчанию 60.0).

.PARAMETER Uninstall
    Удалить задание из Планировщика заданий.

.PARAMETER Status
    Проверить статус задания в Планировщике заданий.
#>

[CmdletBinding()]
param (
    [ValidateSet('hybrid', 'minimal', 'full')]
    [string]$Mode = 'hybrid',

    [float]$Interval = 5.0,

    [float]$HeavyInterval = 60.0,

    [switch]$Uninstall,

    [switch]$Status
)

$ErrorActionPreference = 'Stop'
$taskName = 'AI-Breadboard-Telemetry'

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir) -and $env:AIBREADBOARD_DIR -and (Test-Path $env:AIBREADBOARD_DIR)) {
    $scriptDir = Join-Path $env:AIBREADBOARD_DIR "apps\windows\telemetry"
}
if ([string]::IsNullOrEmpty($scriptDir) -and $MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

$projectRoot = $scriptDir
while ($projectRoot -and -not (Test-Path (Join-Path $projectRoot "pyproject.toml")) -and -not (Test-Path (Join-Path $projectRoot "venv"))) {
    $parent = Split-Path -Parent $projectRoot
    if ($parent -eq $projectRoot) { break }
    $projectRoot = $parent
}
if (-not (Test-Path (Join-Path $projectRoot "pyproject.toml"))) {
    $projectRoot = (Get-Location).Path
}

$appDataDir = $env:APPDATA
if (-not $appDataDir) {
    $appDataDir = Join-Path $env:USERPROFILE "AppData\Roaming"
}
$logDir = Join-Path $appDataDir "AI-Breadboard\apps\windows\telemetry\logs"
$dbFile = Join-Path $logDir "telemetry.db"

# ---------------------------------------------------------------------------
# ПРОВЕРКА СТАТУСА
# ---------------------------------------------------------------------------
if ($Status) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host ""
            Write-Host "✅ Задание '$taskName' зарегистрировано в Task Scheduler:" -ForegroundColor Green
            Write-Host "   • Статус:      $($task.State)" -ForegroundColor Cyan
            Write-Host "   • Имя задания: $($task.TaskName)" -ForegroundColor Cyan
            Write-Host "   • Разбудить ПК: $($task.Settings.WakeToRun)" -ForegroundColor Cyan
            Write-Host "   • Команда:     $($task.Actions.Execute) $($task.Actions.Arguments)" -ForegroundColor DarkGray
        } else {
            Write-Host "ℹ️ Задание '$taskName' не найдено в Task Scheduler." -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "❌ Ошибка получения статуса задания: $_" -ForegroundColor Red
    }
    exit 0
}

# ---------------------------------------------------------------------------
# УДАЛЕНИЕ ЗАДАНИЯ
# ---------------------------------------------------------------------------
if ($Uninstall) {
    Write-Host "🗑️ Удаление задания '$taskName' из Task Scheduler..." -ForegroundColor Yellow
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
            Write-Host "✅ Задание '$taskName' успешно удалено из Task Scheduler." -ForegroundColor Green
        } else {
            Write-Host "ℹ️ Задание '$taskName' не найдено." -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "❌ Ошибка удаления задания: $_" -ForegroundColor Red
        exit 1
    }
    exit 0
}

# ---------------------------------------------------------------------------
# УСТАНОВКА / ОБНОВЛЕНИЕ ЗАДАНИЯ
# ---------------------------------------------------------------------------
Write-Host "⚙️ Подготовка к регистрации задания '$taskName' в Task Scheduler..." -ForegroundColor Cyan

# Проверяем исполняемый файл
$venvScripts = Join-Path $projectRoot "venv\Scripts"
$telemetryExe = Join-Path $venvScripts "ai-telemetry.exe"
$pythonwExe = Join-Path $venvScripts "pythonw.exe"

if (-not (Test-Path $telemetryExe)) {
    if (Test-Path $pythonwExe) {
        Copy-Item -Path $pythonwExe -Destination $telemetryExe -Force
        Write-Host "  [OK] Создан исполняемый файл: $telemetryExe" -ForegroundColor Green
    } else {
        Write-Host "❌ Не найден pythonw.exe в venv: $pythonwExe" -ForegroundColor Red
        exit 1
    }
}

$telemetryScript = Join-Path $scriptDir "main.py"
if (-not (Test-Path $telemetryScript)) {
    Write-Host "❌ Скрипт телеметрии не найден: $telemetryScript" -ForegroundColor Red
    exit 1
}

# Проверяем и создаем каталог логов и базу данных телеметрии telemetry.db
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

$pythonExe = Join-Path $venvScripts "python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not (Test-Path $dbFile)) {
    Write-Host "⚠️ База данных телеметрии не обнаружена: $dbFile" -ForegroundColor Yellow
    Write-Host "⚙️ Выполняется предварительная инициализация структуры telemetry.db..." -ForegroundColor Cyan

    if ($pythonExe -and (Test-Path $pythonExe)) {
        try {
            $initPy = Join-Path $scriptDir "init_db.py"
            if (Test-Path $initPy) {
                & $pythonExe $initPy --db-path "$dbFile"
            } else {
                $initCmd = "import sys; sys.path.insert(0, r'$projectRoot'); from apps.windows.telemetry.sqlite import TelemetryStorage; TelemetryStorage(db_path=r'$dbFile')"
                & $pythonExe -c $initCmd
            }
        } catch {
            Write-Host "⚠️ Ошибка при инициализации базы через Python: $_" -ForegroundColor Yellow
        }
    }

    if (Test-Path $dbFile) {
        $createdSize = [math]::Round((Get-Item $dbFile).Length / 1KB, 1)
        Write-Host "  [OK] База данных telemetry.db готова (${createdSize} КБ)" -ForegroundColor Green
    }
} else {
    $dbSize = (Get-Item $dbFile).Length
    $dbSizeMb = [math]::Round($dbSize / 1MB, 2)
    Write-Host "  [OK] База данных telemetry.db подтверждена: $dbFile ($dbSizeMb МБ)" -ForegroundColor Green
}

$taskArgs = "-u `"$telemetryScript`" --mode $Mode --interval $Interval --heavy-interval $HeavyInterval"

# Создаем Действие (Action)
$action = New-ScheduledTaskAction -Execute $telemetryExe -Argument $taskArgs -WorkingDirectory $projectRoot

# Триггер: при старте системы (Startup) и повтор раз в 1 минуту
$trigger = New-ScheduledTaskTrigger -AtStartup

# Настройки задания
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([System.TimeSpan]::Zero) `
    -Priority 6

# Флаг WakeToRun = True
$settings.WakeToRun = $true

# Регистрация задания
try {
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Служба системной телеметрии AI-Breadboard (автономный сбор данных, WakeToRun)" `
        -User "SYSTEM" `
        -RunLevel Highest | Out-Null

    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "  ✅ ЗАДАНИЕ '$taskName' УСПЕШНО ЗАРЕГИСТРИРОВАНО!              " -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  • Имя задания:  $taskName" -ForegroundColor Cyan
    Write-Host "  • Файл:         $telemetryExe" -ForegroundColor Cyan
    Write-Host "  • Аргументы:    $taskArgs" -ForegroundColor DarkGray
    Write-Host "  • WakeToRun:    True (будит систему при сне)" -ForegroundColor Cyan
    Write-Host "  • Питание:      Автономно от сети и батареи" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "⚠️ Не удалось зарегистрировать от имени SYSTEM, пробуем под текущим пользователем..." -ForegroundColor Yellow
    try {
        Register-ScheduledTask `
            -TaskName $taskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Description "Служба системной телеметрии AI-Breadboard (автономный сбор данных, WakeToRun)" | Out-Null

        Write-Host "✅ Задание зарегистрировано под текущим пользователем." -ForegroundColor Green
    } catch {
        Write-Host "❌ Ошибка регистрации задания: $_" -ForegroundColor Red
        Write-Host "   Попробуйте запустить консоль от имени Администратора." -ForegroundColor DarkGray
        exit 1
    }
}
