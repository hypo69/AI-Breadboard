<#
.SYNOPSIS
    Лончер для управления фоновой службой системной телеметрии AI-Breadboard (ai-telemetry.exe).

.DESCRIPTION
    Запускает автономный процесс сбора телеметрии Windows под собственным системным
    именем 'ai-telemetry.exe' (CPU, RAM, GPU, диски, сеть, топ процессов) в режимах:
      - minimal: ультралегковесный быстрый цикл (28 мс замер, 120 МБ RAM, 0% CPU);
      - hybrid:  быстрый минимал (5с) + периодический опрос тяжелых сенсоров (60с);
      - full:    полный опрос всех сенсоров на каждом тике.
    Поддерживает интеграцию с Windows Task Scheduler (WakeToRun).

.PARAMETER Action
    Действие: 'start' (по умолчанию), 'stop', 'restart', 'status',
              'install-task', 'uninstall-task', 'status-task'.

.PARAMETER Interval
    Интервал сбора быстрой телеметрии в секундах (по умолчанию 5.0).

.PARAMETER HeavyInterval
    Интервал сбора тяжелых сенсоров в секундах для hybrid режима (по умолчанию 60.0).

.PARAMETER TopProcesses
    Количество сохраняемых процессов с наибольшей нагрузкой (по умолчанию 10).

.PARAMETER Mode
    Режим работы: 'hybrid' (по умолчанию), 'minimal', 'full'.

.PARAMETER Foreground
    Запуск интерактивно в текущей консоли без фонового режима.

.PARAMETER NewWindow
    Запуск в отдельном окне терминала.

.PARAMETER Help
    Показать справочную информацию.

.EXAMPLE
    .\launchers\Run-Telemetry.ps1                     # Фоновый запуск (hybrid)
    .\launchers\Run-Telemetry.ps1 -Action status     # Проверка статуса, PID и RAM
    .\launchers\Run-Telemetry.ps1 -Action stop       # Остановка сервиса
    .\launchers\Run-Telemetry.ps1 -Action install-task # Установка в Task Scheduler
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status', 'install-task', 'uninstall-task', 'status-task')]
    [string]$Action = 'start',

    [float]$Interval = 5.0,

    [float]$HeavyInterval = 60.0,

    [int]$TopProcesses = 10,

    [ValidateSet('hybrid', 'minimal', 'full')]
    [string]$Mode = 'hybrid',

    [Alias('f', 'Interactive', 'Console')]
    [switch]$Foreground,

    [Alias('Window', 'SeparateWindow')]
    [switch]$NewWindow,

    [switch]$Restart,

    [switch]$Force,

    [Alias('h', '-help')]
    [switch]$Help
)

if ($Restart -or $Force) {
    $Action = 'restart'
}

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
while ($projectRoot -and -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if ($parent -eq $projectRoot) { break }
    $projectRoot = $parent
}
if (-not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $projectRoot = (Get-Location).Path
}

$telemetryScript = Join-Path $projectRoot "apps\windows\telemetry\main.py"
$appDataDir = $env:APPDATA
if (-not $appDataDir) {
    $appDataDir = Join-Path $env:USERPROFILE "AppData\Roaming"
}
$logDir = Join-Path $appDataDir "AI-Breadboard\apps\windows\telemetry\logs"
$dbFile = Join-Path $logDir "telemetry.db"
$jsonLogFile = Join-Path $logDir "ai_sensors_polls.json"
$serviceLogFile = Join-Path $logDir "telemetry_service.log"
$outLogFile = Join-Path $logDir "telemetry_stdout.log"
$errLogFile = Join-Path $logDir "telemetry_stderr.log"
$pidFile = Join-Path $logDir "telemetry.pid"
$taskInstaller = Join-Path $projectRoot "launchers\Install-TelemetryTask.ps1"
$lhmLauncher = Join-Path $projectRoot "launchers\Run-LHM.ps1"

if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   Run-Telemetry.ps1 — Служба системной телеметрии Windows     ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Управление автономным процессом 'ai-telemetry.exe' (CPU, RAM, GPU, диски, сеть)."
    Write-Host "  Режимы: minimal (ультралегкий), hybrid (базовый 5с + тяжелый 60с), full (полный)."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-Telemetry.ps1 [-Action start|stop|restart|status|install-task|uninstall-task]"
    Write-Host "                               [-Mode hybrid|minimal|full] [-Interval 5.0] [-HeavyInterval 60.0]"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-Telemetry.ps1                      # Запуск в фоне (hybrid)"
    Write-Host "  .\launchers\Run-Telemetry.ps1 -Action status      # Статус процесса ai-telemetry.exe"
    Write-Host "  .\launchers\Run-Telemetry.ps1 -Action stop        # Остановка сервиса"
    Write-Host "  .\launchers\Run-Telemetry.ps1 -Action install-task# Регистрация в Task Scheduler (WakeToRun)"
    Write-Host "  .\launchers\Run-Telemetry.ps1 -Foreground         # Интерактивный запуск в консоли"
    Write-Host ""
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЯ С ПЛАНИРОВЩИКОМ ЗАДАЧ (TASK SCHEDULER)
# -------------------------------------------------------------
if ($Action -eq 'install-task') {
    if (Test-Path $taskInstaller) {
        & $taskInstaller -Mode $Mode -Interval $Interval -HeavyInterval $HeavyInterval
    } else {
        Write-Host "❌ Файл не найден: $taskInstaller" -ForegroundColor Red
    }
    exit $LASTEXITCODE
}

if ($Action -eq 'uninstall-task') {
    if (Test-Path $taskInstaller) {
        & $taskInstaller -Uninstall
    } else {
        Write-Host "❌ Файл не найден: $taskInstaller" -ForegroundColor Red
    }
    exit $LASTEXITCODE
}

if ($Action -eq 'status-task') {
    if (Test-Path $taskInstaller) {
        & $taskInstaller -Status
    } else {
        Write-Host "❌ Файл не найден: $taskInstaller" -ForegroundColor Red
    }
    exit $LASTEXITCODE
}

# -------------------------------------------------------------
# ФУНКЦИИ ПОИСКА И ПОДГОТОВКИ ИСПОЛНЯЕМЫХ ФАЙЛОВ
# -------------------------------------------------------------
function Get-PythonPath {
    $venvPy = Join-Path $projectRoot "venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        return $venvPy
    }
    $cmdPy = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($cmdPy) {
        return $cmdPy
    }
    return $null
}

function Get-PythonwPath {
    param([string]$PyExe)
    if ($PyExe) {
        $candidate = $PyExe.Replace("python.exe", "pythonw.exe")
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    $cmdPyw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
    if ($cmdPyw) {
        return $cmdPyw
    }
    return $PyExe
}

# Подготовка уникального исполняемого файла ai-telemetry.exe в venv
function Ensure-TelemetryExe {
    $venvScripts = Join-Path $projectRoot "venv\Scripts"
    $customExe = Join-Path $venvScripts "ai-telemetry.exe"
    $pythonw = Join-Path $venvScripts "pythonw.exe"

    if (Test-Path $pythonw) {
        if (-not (Test-Path $customExe) -or ((Get-Item $customExe).Length -ne (Get-Item $pythonw).Length)) {
            try {
                Copy-Item -Path $pythonw -Destination $customExe -Force -ErrorAction SilentlyContinue
            } catch {}
        }
    }

    if (Test-Path $customExe) {
        return $customExe
    }
    return (Get-PythonwPath -PyExe (Get-PythonPath))
}

# Функция поиска запущенных процессов телеметрии (по имени ai-telemetry и скрипту)
function Get-TelemetryProcesses {
    $procs = @()
    # 1. Поиск по имени ai-telemetry
    $named = Get-Process -Name "ai-telemetry" -ErrorAction SilentlyContinue
    if ($named) {
        $procs += $named
    }

    # 2. Поиск по аргументам Win32_Process (на случай запуска через pythonw)
    try {
        $cim = Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -and ($_.CommandLine -match 'telemetry[\\\/]main\.py')
        }
        if ($cim) {
            foreach ($c in $cim) {
                $p = Get-Process -Id $c.ProcessId -ErrorAction SilentlyContinue
                if ($p -and ($procs.Id -notcontains $p.Id)) {
                    $procs += $p
                }
            }
        }
    } catch {}

    return $procs
}

$runningProcs = Get-TelemetryProcesses

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STATUS
# -------------------------------------------------------------
if ($Action -eq 'status') {
    Write-Host ""
    if ($runningProcs) {
        Write-Host "✅ Процесс телеметрии активен:" -ForegroundColor Green
        foreach ($proc in $runningProcs) {
            $wsMb = [math]::Round($proc.WorkingSet64 / 1MB, 1)
            $cpuSec = [math]::Round($proc.CPU, 2)
            Write-Host "   • PID: $($proc.Id) | Процесс: $($proc.ProcessName) | RAM (Working Set): $wsMb МБ | CPU: ${cpuSec}с" -ForegroundColor Cyan
        }
        Write-Host ""
        Write-Host "📁 Логи и хранилище:" -ForegroundColor DarkGray
        Write-Host "   • SQLite БД: $dbFile" -ForegroundColor DarkGray
        Write-Host "   • JSON-лог:  $jsonLogFile" -ForegroundColor DarkGray
        Write-Host "   • Лог файл:  $serviceLogFile" -ForegroundColor DarkGray
    } else {
        Write-Host "❌ Процесс телеметрии не запущен." -ForegroundColor Yellow
        Write-Host "   Для запуска: .\launchers\Run-Telemetry.ps1" -ForegroundColor DarkGray
    }

    # Проверка планировщика
    try {
        $schedTask = Get-ScheduledTask -TaskName 'AI-Breadboard-Telemetry' -ErrorAction SilentlyContinue
        if ($schedTask) {
            Write-Host ""
            Write-Host "📅 Task Scheduler: Задание зарегистрировано [Статус: $($schedTask.State), WakeToRun: $($schedTask.Settings.WakeToRun)]" -ForegroundColor DarkCyan
        }
    } catch {}

    # Статус LibreHardwareMonitor (LHM)
    if (Test-Path $lhmLauncher) {
        Write-Host ""
        & $lhmLauncher -Action status
    }

    Write-Host ""
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STOP / RESTART
# -------------------------------------------------------------
if ($Action -in @('stop', 'restart')) {
    if (Test-Path $lhmLauncher) {
        & $lhmLauncher -Action stop
    }

    if ($runningProcs) {
        Write-Host "🛑 Остановка процессов телеметрии..." -ForegroundColor Yellow
        foreach ($p in $runningProcs) {
            try {
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
                Write-Host "   [OK] Остановлен PID $($p.Id) ($($p.ProcessName))" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Milliseconds 800
        if (Test-Path $pidFile) {
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "ℹ️ Процесс телеметрии не был запущен." -ForegroundColor DarkGray
    }

    if ($Action -eq 'stop') {
        Write-Host "✅ Телеметрия остановлена" -ForegroundColor Green
        exit 0
    }
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: START / RESTART
# -------------------------------------------------------------
if ($Action -in @('start', 'restart')) {
    # Сначала запускаем LibreHardwareMonitor
    if (Test-Path $lhmLauncher) {
        & $lhmLauncher -Action start
    } else {
        Write-Host "⚠️ Предупреждение: Скрипт LHM не найден по пути: $lhmLauncher" -ForegroundColor Yellow
    }

    $existing = Get-TelemetryProcesses
    if ($existing) {
        $pids = ($existing | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', '
        Write-Host "✅ Телеметрия уже запущена ($pids)" -ForegroundColor Green
        exit 0
    }

    $telemetryExe = Ensure-TelemetryExe
    $pythonExe = Get-PythonPath

    if (-not $telemetryExe -and -not $pythonExe) {
        Write-Host "❌ Python не найден (ни в venv, ни в PATH)" -ForegroundColor Red
        exit 1
    }

    if (-not (Test-Path $telemetryScript)) {
        Write-Host "❌ Скрипт телеметрии не найден: $telemetryScript" -ForegroundColor Red
        exit 1
    }

    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    }

    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONPATH = $projectRoot

    $appArgs = "-u `"$telemetryScript`" --mode $Mode --interval $Interval --heavy-interval $HeavyInterval --top-processes $TopProcesses"

    if ($Foreground) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  📊 ТЕЛЕМЕТРИЯ (ИНТЕРАКТИВНЫЙ РЕЖИМ)                           " -ForegroundColor Green
        Write-Host "  Режим:      $Mode                                             " -ForegroundColor Cyan
        Write-Host "  Интервал:   быстрый ${Interval}с | тяжелый ${HeavyInterval}с " -ForegroundColor Cyan
        Write-Host "  БД:         $dbFile                                           " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Push-Location $projectRoot
        & $pythonExe -u $telemetryScript --mode $Mode --interval $Interval --heavy-interval $HeavyInterval --top-processes $TopProcesses
        Pop-Location
        exit $LASTEXITCODE
    }

    $launchPid = $null
    if ($NewWindow) {
        Write-Host "🚀 Запуск телеметрии в отдельном окне консоли..." -ForegroundColor Cyan
        $thisScript = $MyInvocation.MyCommand.Path
        if (-not $thisScript) {
            $thisScript = Join-Path $scriptDir "Run-Telemetry.ps1"
        }
        $shellExe = if (Get-Command pwsh.exe -ErrorAction SilentlyContinue) { "pwsh.exe" } else { "powershell.exe" }
        $proc = Start-Process $shellExe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Foreground -Interval $Interval -HeavyInterval $HeavyInterval -TopProcesses $TopProcesses -Mode $Mode" -WorkingDirectory $projectRoot -PassThru
        if ($proc) { $launchPid = $proc.Id }
    } else {
        Write-Host "🚀 Фоновый запуск процесса 'ai-telemetry.exe'..." -ForegroundColor Cyan
        $fullCmd = "`"$telemetryExe`" $appArgs"
        $cimRes = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
            CommandLine = $fullCmd
            CurrentDirectory = $projectRoot
        }
        if ($cimRes -and ($cimRes.ReturnValue -eq 0)) {
            $launchPid = $cimRes.ProcessId
        }
    }

    if ($launchPid) {
        Start-Sleep -Milliseconds 1200
        $launchPid | Out-File -FilePath $pidFile -Encoding utf8 -Force

        # Поиск реальных воркеров телеметрии
        $activeProcs = Get-TelemetryProcesses
        $displayInfo = if ($activeProcs) {
            ($activeProcs | ForEach-Object { "$($_.ProcessName) (PID: $($_.Id), RAM: $([math]::Round($_.WorkingSet64/1MB,1)) МБ)" }) -join '; '
        } else {
            "PID: $launchPid"
        }

        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ✅ ПРОЦЕСС ТЕЛЕМЕТРИИ УСПЕШНО ЗАПУЩЕН!                        " -ForegroundColor Green
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "  • Процессы:   $displayInfo" -ForegroundColor Cyan
        Write-Host "  • Приоритет:  BelowNormal (минимальное влияние на CPU)" -ForegroundColor Cyan
        Write-Host "  • Режим:      $Mode (быстрый $Interval с | тяжелый $HeavyInterval с)" -ForegroundColor Cyan
        Write-Host "  • SQLite БД:  $dbFile" -ForegroundColor DarkGray
        Write-Host "  • JSON-лог:   $jsonLogFile" -ForegroundColor DarkGray
        Write-Host "  • Лог файл:   $serviceLogFile" -ForegroundColor DarkGray
        Write-Host ""
    } else {
        Write-Host "❌ Ошибка запуска процесса телеметрии" -ForegroundColor Red
        exit 1
    }
}
