# =============================================================================
# Process Name: AI-Breadboard Automation - Run-Telemetry Script
# =============================================================================
# Description:
#   PowerShell-сценарий системного обслуживания и запуска (Run-Telemetry).
#
# Usage Examples:
#   PowerShell Execution:
#     .\Run-Telemetry.ps1
#
# File: Run-Telemetry.ps1
# Project: ai-breadboard
# Package: apps.windows.telemetry.launchers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

# Description:
#   PowerShell-сценарий администрирования и автоматизации (Run-Telemetry).
#
# Usage Examples:
#   PowerShell Execution:
#     .\Run-Telemetry.ps1
#
# File: Run-Telemetry.ps1
# Project: ai-breadboard
# Package: windows/telemetry/launchers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:04:40
# =============================================================================

# Description:
#   PowerShell-сценарий системных операций и автоматизации (Run-Telemetry).
#
# Usage Examples:
#   PowerShell:
#     .\Run-Telemetry.ps1
#
# File: Run-Telemetry.ps1
# Project: ai-breadboard
# Package: windows/telemetry/launchers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 12:54:56
# =============================================================================

<#
# Updated: 2026-10-01 09:28:00
.SYNOPSIS
    Лончер для управления фоновой службой системной телеметрии AI-Breadboard (ai-telemetry.exe).

.DESCRIPTION
    Запускает автономный процесс сбора телеметрии Windows под собственным системным
    именем 'ai-telemetry.exe' (CPU, RAM, GPU, диски, сеть, топ процессов) в режимах:
      - minimal: ультралегковесный быстрый цикл (28 мс замер, 120 МБ RAM, 0% CPU);
      - hybrid:  быстрый минимал (5с) + периодический опрос тяжелых сенсоров (60с);
      - full:    полный опрос всех сенсоров на каждом тике.
    Поддерживает интеграцию с Windows Task Scheduler (WakeToRun) и автоинициализацию telemetry.db.

.PARAMETER Action
    Действие: 'tui' (по умолчанию), 'start', 'stop', 'restart', 'status', 'init-db',
              'install-task', 'uninstall-task', 'status-task', 'get-errors', 'get-stdout'.

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
    .\tlm.ps1                                            # Интерактивный TUI интерфейс
    .\apps\windows\telemetry\Run-Telemetry.ps1           # Фоновый запуск (hybrid)
    .\apps\windows\telemetry\Run-Telemetry.ps1 -Action status # Проверка статуса, PID и RAM
    .\apps\windows\telemetry\Run-Telemetry.ps1 -Action init-db # Проверка и инициализация telemetry.db
    .\apps\windows\telemetry\Run-Telemetry.ps1 -Action stop   # Остановка сервиса
#>

[CmdletBinding()]
param (
    [ValidateSet('tui', 'start', 'stop', 'restart', 'status', 'init-db', 'start-log', 'show-log', 'install-task', 'uninstall-task', 'status-task', 'get-errors', 'get-stdout')]
    [string]$Action = 'tui',

    [Alias('Gui', 'InteractiveTUI')]
    [switch]$TUI,

    [Alias('LogView', 'StartLog', 'ShowLog')]
    [switch]$ShowStartLog,

    [Alias('BuildDb', 'InitDatabase')]
    [switch]$InitDb,

    [float]$Interval = 5.0,

    [float]$HeavyInterval = 60.0,

    [int]$TopProcesses = 10,

    [ValidateSet('hybrid', 'minimal', 'full')]
    [string]$Mode = 'hybrid',

    [Alias('f', 'Interactive', 'Console')]
    [switch]$Foreground,

    [Alias('Window', 'SeparateWindow')]
    [switch]$NewWindow,

    [Alias('v', 'DebugLog')]
    [switch]$VerboseLog,

    [switch]$Restart,

    [switch]$Force,

    [Alias('GetStderr', 'Errors', 'Err')]
    [switch]$GetErrors,

    [Alias('Stdout', 'Log', 'Out')]
    [switch]$GetStdOut,

    [int]$Tail = 50,

    [Alias('h', '-help')]
    [switch]$Help
)

if ($Restart -or $Force) {
    $Action = 'restart'
}
if ($TUI) {
    $Action = 'tui'
}
if ($ShowStartLog) {
    $Action = 'show-log'
}
if ($InitDb) {
    $Action = 'init-db'
}
if ($GetErrors) {
    $Action = 'get-errors'
}
if ($GetStdOut) {
    $Action = 'get-stdout'
}

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Определение директории проекта
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

$telemetryScript = Join-Path $scriptDir "main.py"
if (-not (Test-Path $telemetryScript)) {
    $telemetryScript = Join-Path $projectRoot "apps\windows\telemetry\main.py"
}
$selfScript = $PSCommandPath
if ([string]::IsNullOrEmpty($selfScript)) {
    $selfScript = Join-Path $scriptDir "Run-Telemetry.ps1"
}
$showLogScript = Join-Path $scriptDir "Show-StartLog.ps1"
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
$taskInstaller = Join-Path $PSScriptRoot "Install-TelemetryTask.ps1"
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
    Write-Host "  .\tlm.ps1"
    Write-Host "  .\apps\windows\telemetry\Run-Telemetry.ps1 [-Action start|stop|restart|status|install-task|uninstall-task]"
    Write-Host "                                             [-Mode hybrid|minimal|full] [-Interval 5.0] [-HeavyInterval 60.0]"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\tlm.ps1                                   # ТУИ Меню по умолчанию"
    Write-Host "  .\apps\windows\telemetry\Run-Telemetry.ps1 # Запуск в фоне (hybrid)"
    Write-Host "  .\tlm.ps1 -Action status                   # Статус процесса ai-telemetry.exe"
    Write-Host "  .\tlm.ps1 -Action stop                     # Остановка сервиса"
    Write-Host "  .\tlm.ps1 -Action install-task              # Регистрация в Task Scheduler (WakeToRun)"
    Write-Host "  .\tlm.ps1 -Foreground                    # Интерактивный запуск в консоли"
    Write-Host ""
    exit 0
}

if ($Action -in @('show-log', 'start-log')) {
    if (Test-Path $showLogScript) {
        & $showLogScript -Tail $Tail -NoPause
    } else {
        Write-Host "❌ Файл не найден: $showLogScript" -ForegroundColor Red
    }
    exit 0
}

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

# Проверка и автоинициализация базы данных telemetry.db
function Ensure-TelemetryDb {
    param(
        [string]$PyExe,
        [switch]$Force
    )

    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    }

    $needsInit = $Force -or (-not (Test-Path $dbFile))

    if ($needsInit) {
        Write-Host "⚙️ [ИНИЦИАЛИЗАЦИЯ БД] Инициализация новой SQLite базы данных telemetry.db..." -ForegroundColor Cyan

        $pyRunner = if ($PyExe -and (Test-Path $PyExe)) { $PyExe } else { Get-PythonPath }
        if ($pyRunner -and (Test-Path $pyRunner)) {
            try {
                $initPy = Join-Path $scriptDir "init_db.py"
                if (-not (Test-Path $initPy)) {
                    $initPy = Join-Path $projectRoot "apps\windows\telemetry\init_db.py"
                }
                if (Test-Path $initPy) {
                    $initArgs = @($initPy, "--db-path", $dbFile)
                    if ($Force) { $initArgs += "--force" }
                    & $pyRunner @initArgs
                } else {
                    $initCmd = "import sys; sys.path.insert(0, r'$projectRoot'); from apps.windows.telemetry.sqlite import TelemetryStorage; TelemetryStorage(db_path=r'$dbFile')"
                    & $pyRunner -c $initCmd
                }
            } catch {
                Write-Host "⚠️ Ошибка при автоматической инициализации БД: $_" -ForegroundColor Yellow
            }
        }

        if (Test-Path $dbFile) {
            $createdSize = [math]::Round((Get-Item $dbFile).Length / 1KB, 1)
            Write-Host "✅ База данных telemetry.db готова (${createdSize} КБ, путь: $dbFile)" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Файл базы данных не создан явно. Он будет сформирован сервисом при первом цикле." -ForegroundColor Yellow
        }
    } else {
        $dbSize = (Get-Item $dbFile).Length
        $dbSizeMb = [math]::Round($dbSize / 1MB, 2)
        Write-Host "🗄️ База данных telemetry.db: $dbFile ($dbSizeMb МБ)" -ForegroundColor DarkGray
    }
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

# -------------------------------------------------------------
# ИНТЕРАКТИВНЫЙ ТЕРМИНАЛЬНЫЙ ИНТЕРФЕЙС (TUI CONTROL CENTER)
# -------------------------------------------------------------
function Invoke-TelemetryTUI {
    $oldCtrlC = $false
    try {
        $oldCtrlC = [Console]::TreatControlCAsInput
        [Console]::TreatControlCAsInput = $true
    } catch {}

    try {
        while ($true) {
            Clear-Host
            $running = Get-TelemetryProcesses
            $statusStr = if ($running) {
                $pids = ($running | ForEach-Object { "$($_.ProcessName) (PID: $($_.Id), RAM: $([math]::Round($_.WorkingSet64/1MB,1)) МБ)" }) -join '; '
                "✅ АКТИВЕН [$pids]"
            } else {
                "❌ НЕ ЗАПУЩЕН"
            }

            $statusColor = if ($running) { "Green" } else { "Yellow" }

            Write-Host ""
            Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
            Write-Host "║       📊 AI BREADBOARD — СЛУЖБА ТЕЛЕМЕТРИИ (TUI CONTROL CENTER)              ║" -ForegroundColor Cyan
            Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
            Write-Host ""
            Write-Host " Статус службы:  $statusStr" -ForegroundColor $statusColor
            Write-Host " Режим работы:   $Mode | Быстрый интервал: ${Interval}с | Тяжелый: ${HeavyInterval}с" -ForegroundColor White
            Write-Host " База данных:    $dbFile" -ForegroundColor DarkGray
            Write-Host " Файл логов:     $serviceLogFile" -ForegroundColor DarkGray
            Write-Host "────────────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
            Write-Host ""
            Write-Host " МЕНЮ ДЕЙСТВИЙ:" -ForegroundColor Yellow
            Write-Host "   [0] 📋 Стартовый лог, база данных и аудит ошибок (Show-StartLog)" -ForegroundColor Green
            Write-Host "   [1] 🚀 Запустить службу телеметрии (start)" -ForegroundColor Green
            Write-Host "   [2] 🛑 Остановить службу (stop)" -ForegroundColor Red
            Write-Host "   [3] 🔄 Перезапустить службу (restart)" -ForegroundColor Yellow
            Write-Host "   [4] ⚙️  Сменить режим (hybrid / minimal / full)" -ForegroundColor Cyan
            Write-Host "   [5] 📜 Просмотреть консольный лог (stdout)" -ForegroundColor White
            Write-Host "   [6] ⚠️ Просмотреть ошибки и предупреждения (errors)" -ForegroundColor Red
            Write-Host "   [7] 📊 Запросить текущий статус (status)" -ForegroundColor Cyan
            Write-Host "   [8] 🖥️  Запуск в консоли (foreground) [Ctrl+C возвращает в TUI]" -ForegroundColor Magenta
            Write-Host "   [9] 🗄️  Инициализировать / проверить базу данных (init-db)" -ForegroundColor Green
            Write-Host "   [10] 📅 Статус планировщика задач (Task Scheduler)" -ForegroundColor DarkCyan
            Write-Host "   [q] ❌ Выход из TUI (служба продолжит работать в фоне)" -ForegroundColor DarkGray
            Write-Host ""
            Write-Host " Подсказка: Ctrl+C в любой момент НЕ останавливает фоновую службу, а возвращает в TUI!" -ForegroundColor DarkGray
            Write-Host ""
            Write-Host "Выберите опцию [0-10, q]: " -NoNewline -ForegroundColor Yellow

            $key = $null
            try {
                $rawKey = [Console]::ReadKey($true)
                if ($rawKey.Modifiers -band [ConsoleModifiers]::Control -and $rawKey.Key -eq [ConsoleKey]::C) {
                    Write-Host "`n⚠️ Ctrl+C перехвачен: Фоновый сервис телеметрии продолжает работать." -ForegroundColor Yellow
                    Start-Sleep -Milliseconds 800
                    continue
                }
                $key = $rawKey.KeyChar.ToString()
            } catch {
                $key = Read-Host
            }

            switch ($key.ToLower()) {
                '0' {
                    Write-Host "`n📋 Запуск стартового лога и аудита..." -ForegroundColor Green
                    if (Test-Path $showLogScript) {
                        & $showLogScript -Tail 15
                    } else {
                        Write-Host "❌ Файл не найден: $showLogScript" -ForegroundColor Red
                    }
                }
                '1' {
                    Write-Host "`n🚀 Запуск службы телеметрии..." -ForegroundColor Green
                    & $selfScript -Action start -Mode $Mode -Interval $Interval -HeavyInterval $HeavyInterval -TopProcesses $TopProcesses
                    Write-Host "`nНажмите любую клавишу для возврата в TUI..." -ForegroundColor DarkGray
                    try { [Console]::ReadKey($true) | Out-Null } catch {}
                }
                '2' {
                    Write-Host "`n🛑 Остановка службы..." -ForegroundColor Red
                    & $selfScript -Action stop
                    Write-Host "`nНажмите любую клавишу для возврата в TUI..." -ForegroundColor DarkGray
                    try { [Console]::ReadKey($true) | Out-Null } catch {}
                }
                '3' {
                    Write-Host "`n🔄 Перезапуск службы..." -ForegroundColor Yellow
                    & $selfScript -Action restart -Mode $Mode -Interval $Interval -HeavyInterval $HeavyInterval -TopProcesses $TopProcesses
                    Write-Host "`nНажмите любую клавишу для возврата в TUI..." -ForegroundColor DarkGray
                    try { [Console]::ReadKey($true) | Out-Null } catch {}
                }
                '4' {
                    Write-Host "`n⚙️ Смена режима работы телеметрии:" -ForegroundColor Cyan
                    Write-Host "  [1] hybrid  (быстрый 5с + тяжелый 60с) [По умолчанию]" -ForegroundColor White
                    Write-Host "  [2] minimal (ультралегкий 5с)" -ForegroundColor White
                    Write-Host "  [3] full    (полный опрос всех сенсоров)" -ForegroundColor White
                    Write-Host "Выберите [1-3]: " -NoNewline -ForegroundColor Yellow
                    $mKey = Read-Host
                    switch ($mKey) {
                        '1' { $script:Mode = 'hybrid' }
                        '2' { $script:Mode = 'minimal' }
                        '3' { $script:Mode = 'full' }
                    }
                    Write-Host "Режим изменен на: $script:Mode. Перезапуск службы..." -ForegroundColor Green
                    & $selfScript -Action restart -Mode $script:Mode -Interval $Interval -HeavyInterval $HeavyInterval -TopProcesses $TopProcesses
                    Write-Host "`nНажмите любую клавишу для возврата в TUI..." -ForegroundColor DarkGray
                    try { [Console]::ReadKey($true) | Out-Null } catch {}
                }
                '5' {
                    Write-Host "`n📜 Просмотр stdout лога..." -ForegroundColor Cyan
                    try {
                        & $selfScript -Action get-stdout -Tail 40
                    } catch {}
                    Write-Host "`nНажмите любую клавишу для возврата в TUI..." -ForegroundColor DarkGray
                    try { [Console]::ReadKey($true) | Out-Null } catch {}
                }
                '6' {
                    Write-Host "`n⚠️ Просмотр ошибок лога..." -ForegroundColor Red
                    try {
                        & $selfScript -Action get-errors -Tail 40
                    } catch {}
                    Write-Host "`nНажмите любую клавишу для возврата в TUI..." -ForegroundColor DarkGray
                    try { [Console]::ReadKey($true) | Out-Null } catch {}
                }
                '7' {
                    Write-Host "`n📊 Статус службы..." -ForegroundColor Cyan
                    try {
                        & $selfScript -Action status
                    } catch {}
                    Write-Host "`nНажмите любую клавишу для возврата в TUI..." -ForegroundColor DarkGray
                    try { [Console]::ReadKey($true) | Out-Null } catch {}
                }
                '8' {
                    Write-Host "`n🖥️ Запуск в интерактивном режиме консоли (Ctrl+C возвращает в TUI)..." -ForegroundColor Magenta
                    try {
                        & $selfScript -Foreground -Mode $Mode -Interval $Interval -HeavyInterval $HeavyInterval -TopProcesses $TopProcesses
                    } catch {}
                    Write-Host "`n⚠️ Выход из интерактивного режима. Возврат в TUI..." -ForegroundColor Yellow
                    Start-Sleep -Milliseconds 1000
                }
                '9' {
                    Write-Host "`n🗄️ Проверка и инициализация SQLite базы данных telemetry.db..." -ForegroundColor Green
                    try {
                        & $selfScript -Action init-db
                    } catch {}
                    Write-Host "`nНажмите любую клавишу для возврата в TUI..." -ForegroundColor DarkGray
                    try { [Console]::ReadKey($true) | Out-Null } catch {}
                }
                '10' {
                    Write-Host "`n📅 Статус планировщика задач..." -ForegroundColor DarkCyan
                    try {
                        & $selfScript -Action status-task
                    } catch {}
                    Write-Host "`nНажмите любую клавишу для возврата в TUI..." -ForegroundColor DarkGray
                    try { [Console]::ReadKey($true) | Out-Null } catch {}
                }
                'q' {
                    Write-Host "`n👋 Выход из TUI. Процесс телеметрии продолжает работать в фоне." -ForegroundColor Green
                    break
                }
            }
        }
    } finally {
        try {
            [Console]::TreatControlCAsInput = $oldCtrlC
        } catch {}
    }
}

if ($Action -eq 'tui') {
    Invoke-TelemetryTUI
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: INIT-DB (-InitDb)
# -------------------------------------------------------------
if ($Action -eq 'init-db') {
    $pythonExe = Get-PythonPath
    Ensure-TelemetryDb -PyExe $pythonExe -Force:$Force
    exit 0
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
            $role = if ($proc.ProcessName -eq 'ai-telemetry') { "Лончер" } else { "Воркер Python" }
            Write-Host "   • PID: $($proc.Id) | Процесс: $($proc.ProcessName) [$role] | RAM (Working Set): $wsMb МБ | CPU: ${cpuSec}с" -ForegroundColor Cyan
        }
        Write-Host ""
        Write-Host "📁 Логи и хранилище:" -ForegroundColor DarkGray
        Write-Host "   • SQLite БД: $dbFile" -ForegroundColor DarkGray
        Write-Host "   • JSON-лог:  $jsonLogFile" -ForegroundColor DarkGray
        Write-Host "   • Лог файл:  $serviceLogFile" -ForegroundColor DarkGray
    } else {
        Write-Host "❌ Процесс телеметрии не запущен." -ForegroundColor Yellow
        Write-Host "   Для запуска: .\tlm.ps1" -ForegroundColor DarkGray
    }

    # Проверка планировщика
    try {
        $schedTask = Get-ScheduledTask -TaskName 'AI-Breadboard-Telemetry' -ErrorAction SilentlyContinue
        if ($schedTask) {
            Write-Host ""
            Write-Host "📅 Task Scheduler: Задание зарегистрировано [Статус: $($schedTask.State), WakeToRun: $($schedTask.Settings.WakeToRun)]" -ForegroundColor DarkCyan
        }
    } catch {}

    Write-Host ""
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: GET-ERRORS (-GetErrors -Tail N)
# -------------------------------------------------------------
if ($Action -eq 'get-errors') {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║   📊 ЛОГ ОШИБОК И ИСКЛЮЧЕНИЙ ТЕЛЕМЕТРИИ (Топ-$Tail строк)       ║" -ForegroundColor Red
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""

    $hasOutput = $false
    if (Test-Path $errLogFile) {
        $lines = Get-Content -Path $errLogFile -Tail $Tail -ErrorAction SilentlyContinue
        if ($lines) {
            Write-Host "📁 Ошибки и исключения из $errLogFile :" -ForegroundColor Yellow
            $lines | ForEach-Object { Write-Host $_ -ForegroundColor Red }
            $hasOutput = $true
        }
    }

    if (Test-Path $serviceLogFile) {
        $errorLines = Get-Content -Path $serviceLogFile -ErrorAction SilentlyContinue | Where-Object { $_ -match 'ERROR|CRITICAL|WARNING|Exception' } | Select-Object -Last $Tail
        if ($errorLines) {
            if ($hasOutput) { Write-Host "" }
            Write-Host "📁 Предупреждения и ошибки из $serviceLogFile :" -ForegroundColor Yellow
            $errorLines | ForEach-Object {
                if ($_ -match 'ERROR|CRITICAL|Exception') {
                    Write-Host $_ -ForegroundColor Red
                } else {
                    Write-Host $_ -ForegroundColor Yellow
                }
            }
            $hasOutput = $true
        }
    }

    if (-not $hasOutput) {
        Write-Host "✅ В логах телеметрии критических ошибок не обнаружено." -ForegroundColor Green
    }

    Write-Host ""
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: GET-STDOUT (-GetStdOut -Tail N)
# -------------------------------------------------------------
if ($Action -eq 'get-stdout') {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   📊 СТАНДАРТНЫЙ ВЫВОД (STDOUT) ТЕЛЕМЕТРИИ (Топ-$Tail строк)    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    $targetFile = if (Test-Path $outLogFile) { $outLogFile } elseif (Test-Path $serviceLogFile) { $serviceLogFile } else { $null }

    if ($targetFile) {
        Write-Host "📁 Вывод из $targetFile :" -ForegroundColor DarkGray
        Write-Host ""
        Get-Content -Path $targetFile -Tail $Tail | ForEach-Object { Write-Host $_ }
    } else {
        Write-Host "⚠️ Лог-файл консольного вывода не найден по пути: $outLogFile" -ForegroundColor Yellow
    }

    Write-Host ""
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STOP / RESTART
# -------------------------------------------------------------
if ($Action -in @('stop', 'restart')) {
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
# ДЕЙСТВИЕ: START / RESTART (Изолированный запуск без FastAPI/HTTP)
# -------------------------------------------------------------
if ($Action -in @('start', 'restart')) {
    $existing = Get-TelemetryProcesses
    if ($existing -and $Action -ne 'restart') {
        $pids = ($existing | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', '
        Write-Host "✅ Телеметрия уже запущена ($pids)" -ForegroundColor Green
        Write-Host "   Для перезапуска используйте: .\tlm.ps1 -Restart" -ForegroundColor DarkGray
        Write-Host "   Или с логированием:          .\tlm.ps1 -Foreground -v -Force" -ForegroundColor DarkGray
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

    # Проверка и создание БД перед запуском процесса
    Ensure-TelemetryDb -PyExe $pythonExe

    $isVerbose = $PSBoundParameters.ContainsKey('Verbose') -or $VerboseLog
    $appArgs = "-u `"$telemetryScript`" --mode $Mode --interval $Interval --heavy-interval $HeavyInterval --top-processes $TopProcesses"
    if ($isVerbose) {
        $appArgs += " --verbose"
    }

    if ($Foreground) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  📊 ТЕЛЕМЕТРИЯ (ИНТЕРАКТИВНЫЙ РЕЖИМ ЛОГИРОВАНИЯ)                " -ForegroundColor Green
        Write-Host "  Режим:      $Mode                                             " -ForegroundColor Cyan
        Write-Host "  Интервал:   быстрый ${Interval}с | тяжелый ${HeavyInterval}с " -ForegroundColor Cyan
        Write-Host "  БД:         $dbFile                                           " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Push-Location $projectRoot
        $pyCmdArgs = @("-u", $telemetryScript, "--mode", $Mode, "--interval", $Interval.ToString(), "--heavy-interval", $HeavyInterval.ToString(), "--top-processes", $TopProcesses.ToString())
        if ($isVerbose) { $pyCmdArgs += "--verbose" }
        & $pythonExe @pyCmdArgs
        Pop-Location
        exit $LASTEXITCODE
    }

    $launchPid = $null
    if ($NewWindow) {
        Write-Host "🚀 Запуск телеметрии в отдельном окне консоли..." -ForegroundColor Cyan
        $thisScript = $selfScript
        if (-not $thisScript) {
            $thisScript = Join-Path $PSScriptRoot "Run-Telemetry.ps1"
        }
        $shellExe = if (Get-Command pwsh.exe -ErrorAction SilentlyContinue) { "pwsh.exe" } else { "powershell.exe" }
        $vFlag = if ($isVerbose) { " -VerboseLog" } else { "" }
        $proc = Start-Process $shellExe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Foreground -Interval $Interval -HeavyInterval $HeavyInterval -TopProcesses $TopProcesses -Mode $Mode$vFlag" -WorkingDirectory $projectRoot -PassThru
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
