<#
.SYNOPSIS
    Регистрация фоновой службы телеметрии AI-Breadboard в Windows Task Scheduler.

.DESCRIPTION
    Создает задание в Планировщике заданий Windows (Task Scheduler) с именем
    'AI-Breadboard-Telemetry'.
    Запускает ai-telemetry.exe в фоновом режиме с флагом WakeToRun (продолжает
    работать и будит систему для выполнения замеров, не прекращает работу при сне
    или питании от батареи, перезапускается при сбоях).

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
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$projectRoot = Split-Path -Parent $scriptDir

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
            Write-Host "   • Автор:       $($task.Author)" -ForegroundColor DarkGray
            Write-Host "   • WakeToRun:   $($task.Settings.WakeToRun)" -ForegroundColor Cyan
            Write-Host "   • Приоритет:   $($task.Settings.Priority)" -ForegroundColor DarkGray
            Write-Host ""
        } else {
            Write-Host "ℹ️ Задание '$taskName' не зарегистрировано в Task Scheduler." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Ошибка проверки задания: $_" -ForegroundColor Red
    }
    exit 0
}

# ---------------------------------------------------------------------------
# УДАЛЕНИЕ ЗАДАНИЯ
# ---------------------------------------------------------------------------
if ($Uninstall) {
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

$telemetryScript = Join-Path $projectRoot "apps\windows\telemetry\main.py"
if (-not (Test-Path $telemetryScript)) {
    Write-Host "❌ Скрипт телеметрии не найден: $telemetryScript" -ForegroundColor Red
    exit 1
}

$taskArgs = "-u `"$telemetryScript`" --mode $Mode --interval $Interval --heavy-interval $HeavyInterval"

# 1. Action (Действие)
$action = New-ScheduledTaskAction `
    -Execute $telemetryExe `
    -Argument $taskArgs `
    -WorkingDirectory $projectRoot

# 2. Trigger (При входе пользователя и при старте)
$trigger = New-ScheduledTaskTrigger -AtLogOn

# 3. Settings (Ключевые свойства: WakeToRun, работа без лимита времени)
$settings = New-ScheduledTaskSettingsSet `
    -WakeToRun `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -Priority 6 `
    -MultipleInstances IgnoreNew

# 4. Регистрация задания
try {
    # Удаляем старое, если существовало
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    $currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    $currentUser = $currentPrincipal.Identity.Name

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Фоновый сервис сбора системной телеметрии AI-Breadboard (ai-telemetry.exe)" `
        -User $currentUser | Out-Null

    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "  ✅ ЗАДАНИЕ ТЕЛЕМЕТРИИ УСПЕШНО ЗАРЕГИСТРИРОВАНО!               " -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  • Имя задания:    $taskName" -ForegroundColor Cyan
    Write-Host "  • Процесс:        $telemetryExe" -ForegroundColor Cyan
    Write-Host "  • Режим:          $Mode" -ForegroundColor Cyan
    Write-Host "  • Интервалы:      быстрый $Interval с | тяжелый $HeavyInterval с" -ForegroundColor Cyan
    Write-Host "  • WakeToRun:      ВКЛЮЧЕНО (работает при сне и питании от батареи)" -ForegroundColor Green
    Write-Host "  • Автозапуск:     При входе в систему ($currentUser)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Для запуска задания прямо сейчас:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor DarkGray
    Write-Host "Для удаления задания:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Install-TelemetryTask.ps1 -Uninstall" -ForegroundColor DarkGray
    Write-Host ""
} catch {
    Write-Host "❌ Ошибка регистрации задания: $_" -ForegroundColor Red
    exit 1
}
