<#
=============================================================================
Process Name: AI-Breadboard Automation - Show Startlog
=============================================================================
Description:
  Отображение подробного стартового лога, конфигурации, статуса базы данных и ошибок телеметрии AI-Breadboard

Usage Examples:
  PowerShell Execution:
    .\Show-StartLog.ps1

File: Show-StartLog.ps1
Project: ai-breadboard
Package: apps/windows/telemetry/launchers
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-02 21:57:05
=============================================================================
.SYNOPSIS
    Отображение подробного стартового лога, конфигурации, статуса базы данных и ошибок телеметрии AI-Breadboard
.DESCRIPTION
    Открывает консольное окно / информационную панель системной телеметрии Windows:
      1
#>

[CmdletBinding()]
param (
    [Alias('Window', 'SeparateWindow', 'w')]
    [switch]$NewWindow,

    [int]$Tail = 15,

    [Alias('Follow', 'Live', 'f')]
    [switch]$Watch,

    [int]$RefreshInterval = 5,

    [switch]$NoPause,

    [Alias('PurgeLogs', 'ResetLogs')]
    [switch]$ClearLogs,

    [Alias('h', '-help')]
    [switch]$Help
)

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Определение директорий проекта
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
while ($projectRoot -and -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if ($parent -eq $projectRoot) { break }
    $projectRoot = $parent
}
if (-not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $projectRoot = (Get-Location).Path
}

# Если запрошено открытие в новом окне
if ($NewWindow) {
    $thisScript = $MyInvocation.MyCommand.Path
    if (-not $thisScript) {
        $thisScript = Join-Path $scriptDir "Show-StartLog.ps1"
    }
    $shellExe = if (Get-Command pwsh.exe -ErrorAction SilentlyContinue) { "pwsh.exe" } else { "powershell.exe" }
    $watchArg = if ($Watch) { " -Watch" } else { "" }
    Start-Process $shellExe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Tail $Tail$watchArg" -WorkingDirectory $projectRoot
    exit 0
}

# Пути к логам и базе данных
$appDataDir = $env:APPDATA
if (-not $appDataDir) {
    $appDataDir = Join-Path $env:USERPROFILE "AppData\Roaming"
}
$telemetryLogDir = Join-Path $appDataDir "AI-Breadboard\apps\windows\telemetry\logs"
$dbFile = Join-Path $telemetryLogDir "telemetry.db"
$dbShmFile = Join-Path $telemetryLogDir "telemetry.db-shm"
$dbWalFile = Join-Path $telemetryLogDir "telemetry.db-wal"
$jsonLogFile = Join-Path $telemetryLogDir "ai_sensors_polls.json"
$serviceLogFile = Join-Path $telemetryLogDir "telemetry_service.log"
$outLogFile = Join-Path $telemetryLogDir "telemetry_stdout.log"
$errLogFile = Join-Path $telemetryLogDir "telemetry_stderr.log"
$configFile = Join-Path $scriptDir "config.json"
if (-not (Test-Path $configFile)) {
    $configFile = Join-Path (Split-Path -Parent $scriptDir) "config.json"
}

if ($ClearLogs) {
    $logFilesToClear = @($serviceLogFile, $errLogFile, $outLogFile, $aiErrLogFile)
    foreach ($f in $logFilesToClear) {
        if (Test-Path $f) {
            Clear-Content -Path $f -ErrorAction SilentlyContinue
        }
    }
    Write-Host "✅ Логи ошибок телеметрии успешно очищены!" -ForegroundColor Green
    if (-not $Watch) { exit 0 }
}
$pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $cmdPy = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($cmdPy) { $pythonExe = $cmdPy }
}

if ($Help) {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   Show-StartLog.ps1 — Информационная панель и аудит телеметрии           ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Отображает исчерпывающий отчет о работе службы системной телеметрии:"
    Write-Host "    • Когда запущена (время старта, аптайм, процесс ai-telemetry.exe, PID, RAM, CPU)"
    Write-Host "    • Что собирает (режим работы, сенсоры CPU/GPU/RAM/Диск/Сеть/SMART, интервалы)"
    Write-Host "    • В какую базу данных (путь к telemetry.db, размер на диске, число записей)"
    Write-Host "    • Ошибки в логах (количество ошибок/варнингов, последние инциденты)"
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\apps\windows\telemetry\Show-StartLog.ps1 [-NewWindow] [-Tail 15] [-Watch] [-NoPause]"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\apps\windows\telemetry\Show-StartLog.ps1            # Быстрый аудит состояния"
    Write-Host "  .\apps\windows\telemetry\Show-StartLog.ps1 -NewWindow # Запуск в новом окне терминала"
    Write-Host "  .\apps\windows\telemetry\Show-StartLog.ps1 -Watch     # Живой мониторинг каждые 5 сек"
    Write-Host ""
    exit 0
}

# Функция форматирования размера файла
function Format-FileSize {
    param([long]$Bytes)
    if ($Bytes -ge 1GB) {
        return "$([math]::Round($Bytes / 1GB, 2)) ГБ"
    } elseif ($Bytes -ge 1MB) {
        return "$([math]::Round($Bytes / 1MB, 2)) МБ"
    } elseif ($Bytes -ge 1KB) {
        return "$([math]::Round($Bytes / 1KB, 1)) КБ"
    } else {
        return "$Bytes Байт"
    }
}

# Функция форматирования интервала времени (Uptime)
function Format-Uptime {
    param([timespan]$TimeSpan)
    $days = $TimeSpan.Days
    $hours = $TimeSpan.Hours
    $minutes = $TimeSpan.Minutes
    $seconds = $TimeSpan.Seconds
    $parts = @()
    if ($days -gt 0) { $parts += "$days дн." }
    if ($hours -gt 0 -or $days -gt 0) { $parts += "$hours ч." }
    if ($minutes -gt 0 -or $hours -gt 0 -or $days -gt 0) { $parts += "$minutes мин." }
    $parts += "$seconds сек."
    return $parts -join " "
}

# Функция получения активных процессов телеметрии
function Get-ActiveTelemetryProcs {
    $procs = @()
    $named = Get-Process -Name "ai-telemetry" -ErrorAction SilentlyContinue
    if ($named) { $procs += $named }
    try {
        $cim = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
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

# Функция чтения статистики SQLite базы данных через Python
function Get-DatabaseStats {
    param([string]$DbPath, [string]$PyExe)
    $stats = [ordered]@{
        TotalSnapshots = 0
        FirstTimestamp = $null
        LastTimestamp  = $null
        TableCounts    = @{}
        DbReadable     = $false
    }

    if (-not (Test-Path $DbPath) -or -not (Test-Path $PyExe)) {
        return $stats
    }

    try {
        $pyCode = @"
import sqlite3, json, sys, os
try:
    db = r"$DbPath"
    conn = sqlite3.connect(db, timeout=4.0)
    cur = conn.cursor()
    counts = {}
    try:
        cur.execute("SELECT name, seq FROM sqlite_sequence")
        for row in cur.fetchall():
            counts[row[0]] = row[1]
    except Exception:
        pass
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall() if r[0] != 'sqlite_sequence']
    for t in tables:
        if t not in counts:
            try:
                cur.execute(f"SELECT COUNT(1) FROM {t}")
                counts[t] = cur.fetchone()[0]
            except Exception:
                pass
    first_ts, last_ts = None, None
    total_snaps = counts.get('system_snapshots', 0)
    if total_snaps > 0:
        try:
            cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM system_snapshots")
            row = cur.fetchone()
            if row:
                first_ts, last_ts = row[0], row[1]
        except Exception:
            pass
    res = {'readable': True, 'total_snapshots': total_snaps, 'first_ts': first_ts, 'last_ts': last_ts, 'tables': counts}
    print(json.dumps(res, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'readable': False, 'error': str(e)}))
"@
        $b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($pyCode))
        $b64Cmd = "import base64; exec(base64.b64decode('$b64').decode('utf-8'))"
        $rawOut = & $PyExe -c $b64Cmd 2>$null
        if ($rawOut) {
            $parsed = $rawOut | ConvertFrom-Json
            if ($parsed.readable) {
                $stats.DbReadable = $true
                $stats.TotalSnapshots = [long]$parsed.total_snapshots
                $stats.FirstTimestamp = $parsed.first_ts
                $stats.LastTimestamp = $parsed.last_ts
                if ($parsed.tables) {
                    $parsed.tables.PSObject.Properties | ForEach-Object {
                        $stats.TableCounts[$_.Name] = [long]$_.Value
                    }
                }
            }
        }
    } catch {}

    return $stats
}

# Функция сканирования ошибок в логах
function Get-TelemetryErrorsSummary {
    param([string[]]$LogFiles, [int]$TailCount)
    $summary = [ordered]@{
        TotalErrors     = 0
        TotalWarnings   = 0
        TotalExceptions = 0
        FileStats       = @()
        RecentErrors    = @()
    }

    $errorPattern = 'ERROR|CRITICAL|Traceback|Exception'
    $warnPattern  = 'WARNING'

    foreach ($file in $LogFiles) {
        if (Test-Path $file) {
            $item = Get-Item $file
            $fileErrCount = 0
            $fileWarnCount = 0
            $fileExcCount = 0

            try {
                $lines = Get-Content -Path $file -Encoding UTF8 -ErrorAction SilentlyContinue
                if ($lines) {
                    foreach ($line in $lines) {
                        if ($line -match 'ERROR|CRITICAL') {
                            $fileErrCount++
                            $summary.TotalErrors++
                        } elseif ($line -match 'WARNING') {
                            $fileWarnCount++
                            $summary.TotalWarnings++
                        } elseif ($line -match 'Exception|Traceback') {
                            $fileExcCount++
                            $summary.TotalExceptions++
                        }
                    }

                    # Сбор последних подозрительных строк
                    $matchingLines = $lines | Where-Object { $_ -match "$errorPattern|$warnPattern" }
                    if ($matchingLines) {
                        $selected = $matchingLines | Select-Object -Last $TailCount
                        foreach ($m in $selected) {
                            $summary.RecentErrors += [PSCustomObject]@{
                                File = $item.Name
                                Line = $m.Trim()
                            }
                        }
                    }
                }
            } catch {}

            $summary.FileStats += [PSCustomObject]@{
                FileName   = $item.Name
                Size       = Format-FileSize $item.Length
                Errors     = $fileErrCount
                Warnings   = $fileWarnCount
                Exceptions = $fileExcCount
                LastModified = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            }
        }
    }

    return $summary
}

# Функция отрисовки полного отчета
function Render-Report {
    $now = Get-Date
    try { Clear-Host } catch {}

    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║              📊 AI-BREADBOARD TELEMETRY — СТАРТОВЫЙ ЛОГ И СТАТУС                   ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host " Отчет сформирован: $($now.ToString('yyyy-MM-dd HH:mm:ss')) | Хост: $env:COMPUTERNAME | Пользователь: $env:USERNAME" -ForegroundColor DarkGray
    Write-Host "────────────────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray

    # -------------------------------------------------------------
    # 1. КОГДА ТЕЛЕМЕТРИЯ ЗАПУСТИЛАСЬ И СТАТУС ПРОЦЕССА
    # -------------------------------------------------------------
    Write-Host "`n[ 1. СТАТУС И ВРЕМЯ ЗАПУСКА ТЕЛЕМЕТРИИ ]" -ForegroundColor Yellow
    $activeProcs = Get-ActiveTelemetryProcs

    if ($activeProcs) {
        $mainProc = $activeProcs[0]
        $startTime = $mainProc.StartTime
        $uptime = $now - $startTime
        $uptimeStr = Format-Uptime $uptime

        Write-Host "  ✅ Состояние службы:       " -NoNewline
        Write-Host "АКТИВНА (Запущена и собирает данные)" -ForegroundColor Green

        Write-Host "  ⏰ Время запуска службы:    " -NoNewline
        Write-Host "$($startTime.ToString('yyyy-MM-dd HH:mm:ss')) " -ForegroundColor White -NoNewline
        Write-Host "($uptimeStr назад)" -ForegroundColor Cyan

        Write-Host "  ⏱️  Время непрерывной работы: " -NoNewline
        Write-Host "$uptimeStr" -ForegroundColor Cyan

        Write-Host "  ⚙️  Активные процессы:      " -ForegroundColor White
        foreach ($proc in $activeProcs) {
            $ramMb = [math]::Round($proc.WorkingSet64 / 1MB, 1)
            $cpuSec = [math]::Round($proc.CPU, 2)
            $role = if ($proc.ProcessName -eq 'ai-telemetry') { "Лончер сервиса" } else { "Python-воркер сбора" }
            Write-Host "     • PID: $($proc.Id) | Имя: $($proc.ProcessName) | Назначение: $role | RAM: $ramMb МБ | CPU: ${cpuSec}с" -ForegroundColor DarkCyan
        }
    } else {
        Write-Host "  ❌ Состояние службы:       " -NoNewline
        Write-Host "ОСТАНОВЛЕНА (Процесс не запущен)" -ForegroundColor Red
        Write-Host "  ℹ️  Подсказка для запуска:  .\apps\windows\telemetry\Run-Telemetry.ps1 или .\tlm.ps1" -ForegroundColor DarkGray
    }

    # Проверка планировщика задач Windows
    try {
        $task = Get-ScheduledTask -TaskName 'AI-Breadboard-Telemetry' -ErrorAction SilentlyContinue
        if ($task) {
            $taskState = switch ($task.State) {
                'Ready'    { "Готово к запуску (Ready)" }
                'Running'  { "Выполняется (Running)" }
                'Disabled' { "Отключено (Disabled)" }
                default    { $task.State.ToString() }
            }
            $taskColor = if ($task.State -eq 'Running') { "Green" } elseif ($task.State -eq 'Ready') { "Cyan" } else { "Yellow" }
            Write-Host "  📅 Планировщик Windows:    " -NoNewline
            Write-Host "Задание 'AI-Breadboard-Telemetry' зарегистрировано [$taskState, WakeToRun: $($task.Settings.WakeToRun)]" -ForegroundColor $taskColor
        }
    } catch {}

    # -------------------------------------------------------------
    # 2. ЧТО ОНА СОБИРАЕТ (КОНФИГУРАЦИЯ И СЕНСОРЫ)
    # -------------------------------------------------------------
    Write-Host "`n[ 2. ЧТО СОБИРАЕТ ТЕЛЕМЕТРИЯ ]" -ForegroundColor Yellow

    $configMode = "hybrid"
    $fastInterval = 5.0
    $heavyInterval = 60.0
    $topProcs = 10
    $procMode = "top_n"
    $enabledSensors = @()
    $allSensors = [ordered]@{}

    if (Test-Path $configFile) {
        try {
            $cfg = Get-Content $configFile -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($cfg.mode) { $configMode = $cfg.mode }
            if ($cfg.interval_seconds) { $fastInterval = $cfg.interval_seconds }
            if ($cfg.heavy_interval_seconds) { $heavyInterval = $cfg.heavy_interval_seconds }
            if ($cfg.top_processes) { $topProcs = $cfg.top_processes }
            if ($cfg.process_mode) { $procMode = $cfg.process_mode }

            if ($cfg.sensors) {
                $cfg.sensors.PSObject.Properties | ForEach-Object {
                    $sName = $_.Name
                    $sVal = $_.Value
                    $sEnabled = if ($sVal.enabled -eq $true) { $true } else { $false }
                    $sMetrics = if ($sVal.metrics) { ($sVal.metrics -join ", ") } else { "все метрики" }
                    $sInt = if ($sVal.interval_seconds) { "${($sVal.interval_seconds)}с" } else { "-" }
                    $allSensors[$sName] = [PSCustomObject]@{ Enabled = $sEnabled; Metrics = $sMetrics; Interval = $sInt }
                    if ($sEnabled) { $enabledSensors += $sName }
                }
            }
        } catch {}
    }

    Write-Host "  🎯 Режим работы:           " -NoNewline
    Write-Host "$configMode " -ForegroundColor Green -NoNewline
    Write-Host "(Интервал быстрой телеметрии: ${fastInterval}с, тяжелых сенсоров: ${heavyInterval}с)" -ForegroundColor White

    Write-Host "  📊 Отслеживание процессов: " -NoNewline
    $procDesc = if ($procMode -eq 'top_n') { "Топ-$topProcs процессов с наибольшей нагрузкой CPU/RAM/IO" } else { "Все системные процессы" }
    Write-Host "$procDesc" -ForegroundColor Cyan

    Write-Host "  🎛️  Активные сенсоры и метрики:" -ForegroundColor White
    $sensorIcons = @{
        'cpu'             = "🖥️  CPU             : температура, нагрузка ядер, тактовые частоты"
        'gpu'             = "🎮 GPU             : температура, загрузка ядра/памяти, TDP, VRAM"
        'ram'             = "🧠 RAM             : использование памяти, swap, доступный объем"
        'disk'            = "💾 Диски           : нагрузка IO, активность разделов, чтение/запись"
        'network'         = "🌐 Сеть            : пропускная способность, соединения, адаптеры"
        'sensors'         = "🌡️  Hardware Sensors: вентиляторы, напряжения матплаты (LHM)"
        'internet'        = "🚀 Интернет        : Ping, задержка DNS, скорость"
        'storage'         = "🛡️  S.M.A.R.T.      : здоровье SSD/HDD, температура, износ"
        'device_flapping' = "⚡ Device Flapping : события переподключения USB/PCIe устройств"
    }

    foreach ($sKey in $sensorIcons.Keys) {
        $sInfo = $allSensors[$sKey]
        $statusMark = if ($sInfo -and $sInfo.Enabled) { "✅ Вкл" } else { "⚠️  Выкл" }
        $markColor = if ($sInfo -and $sInfo.Enabled) { "Green" } else { "DarkGray" }
        Write-Host "     • [$statusMark] $($sensorIcons[$sKey])" -ForegroundColor $markColor
    }

    # -------------------------------------------------------------
    # 3. В КАКУЮ БАЗУ ДАННЫХ СОХРАНЯЮТСЯ ДАННЫЕ
    # -------------------------------------------------------------
    Write-Host "`n[ 3. БАЗА ДАННЫХ И ХРАНИЛИЩЕ ДАННЫХ ]" -ForegroundColor Yellow

    if (Test-Path $dbFile) {
        $dbItem = Get-Item $dbFile
        $dbSizeStr = Format-FileSize $dbItem.Length

        Write-Host "  📁 Основная SQLite БД:     " -NoNewline
        Write-Host "$dbFile" -ForegroundColor Cyan

        Write-Host "  💾 Размер файла БД:        " -NoNewline
        Write-Host "$dbSizeStr " -ForegroundColor White -NoNewline
        Write-Host "(Последнее изменение: $($dbItem.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')))" -ForegroundColor DarkGray

        # Проверка WAL и SHM
        if (Test-Path $dbWalFile) {
            $walSize = Format-FileSize (Get-Item $dbWalFile).Length
            Write-Host "     • Журнал WAL:           $walSize (активен режим Write-Ahead-Logging)" -ForegroundColor DarkCyan
        }

        # Статистика записей в БД
        $dbStats = Get-DatabaseStats -DbPath $dbFile -PyExe $pythonExe
        if ($dbStats.DbReadable) {
            Write-Host "  📈 Всего снапшотов:        " -NoNewline
            Write-Host "$($dbStats.TotalSnapshots.ToString('N0')) записей" -ForegroundColor Green

            if ($dbStats.FirstTimestamp -and $dbStats.LastTimestamp) {
                $firstStr = if ($dbStats.FirstTimestamp -is [datetime]) { $dbStats.FirstTimestamp.ToString('yyyy-MM-dd HH:mm:ss') } else { [string]$dbStats.FirstTimestamp }
                $lastStr = if ($dbStats.LastTimestamp -is [datetime]) { $dbStats.LastTimestamp.ToString('yyyy-MM-dd HH:mm:ss') } else { [string]$dbStats.LastTimestamp }
                if ($firstStr.Length -gt 19) { $firstStr = $firstStr.Substring(0, 19) }
                if ($lastStr.Length -gt 19) { $lastStr = $lastStr.Substring(0, 19) }
                Write-Host "  ⏳ Временной охват БД:     " -NoNewline
                Write-Host "с $firstStr по $lastStr" -ForegroundColor Cyan
            }

            if ($dbStats.TableCounts.Count -gt 0) {
                Write-Host "  📋 Таблицы данных в SQLite:" -ForegroundColor White
                $dbStats.TableCounts.Keys | ForEach-Object {
                    $cnt = $dbStats.TableCounts[$_]
                    Write-Host "     • $_ : $($cnt.ToString('N0')) записей" -ForegroundColor DarkGray
                }
            }
        }
    } else {
        Write-Host "  ⚠️  Файл SQLite БД пока не создан по пути: $dbFile" -ForegroundColor Yellow
    }

    if (Test-Path $jsonLogFile) {
        $jsonItem = Get-Item $jsonLogFile
        Write-Host "  📄 JSON-лог измерений:     $jsonLogFile ($(Format-FileSize $jsonItem.Length))" -ForegroundColor DarkGray
    }

    # -------------------------------------------------------------
    # 4. СКОЛЬКО ОШИБОК В ЛОГАХ
    # -------------------------------------------------------------
    Write-Host "`n[ 4. АНАЛИЗ ОШИБОК В ЛОГАХ ]" -ForegroundColor Yellow

    $logFilesToScan = @($serviceLogFile, $errLogFile, $outLogFile, $aiErrLogFile)
    $errSummary = Get-TelemetryErrorsSummary -LogFiles $logFilesToScan -TailCount $Tail

    Write-Host "  📁 Просканированные файлы логов ($telemetryLogDir):" -ForegroundColor White
    foreach ($fStat in $errSummary.FileStats) {
        $statColor = if ($fStat.Errors -gt 0) { "Red" } elseif ($fStat.Warnings -gt 0) { "Yellow" } else { "Green" }
        Write-Host "     • $($fStat.FileName) [$($fStat.Size)]: " -NoNewline -ForegroundColor DarkGray
        Write-Host "Ошибок: $($fStat.Errors) | Предупреждений: $($fStat.Warnings) | Исключений: $($fStat.Exceptions) " -ForegroundColor $statColor -NoNewline
        Write-Host "(Изм: $($fStat.LastModified))" -ForegroundColor DarkGray
    }

    Write-Host ""
    $totalIssues = $errSummary.TotalErrors + $errSummary.TotalExceptions
    if ($totalIssues -eq 0 -and $errSummary.TotalWarnings -eq 0) {
        Write-Host "  ✅ В логах телеметрии не обнаружено ошибок или сбоев!" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Сводка по инцидентам:  " -NoNewline
        Write-Host "Критических ошибок/исключений: $totalIssues | Предупреждений: $($errSummary.TotalWarnings)" -ForegroundColor $(if ($totalIssues -gt 0) { "Red" } else { "Yellow" })

        if ($errSummary.RecentErrors.Count -gt 0) {
            Write-Host "`n  🚨 Последние зафиксированные записи (Топ-$Tail):" -ForegroundColor Yellow
            $recent = $errSummary.RecentErrors | Select-Object -Last $Tail
            foreach ($item in $recent) {
                $lineColor = if ($item.Line -match 'ERROR|CRITICAL|Traceback|Exception') { "Red" } else { "Yellow" }
                Write-Host "     [$($item.File)] $($item.Line)" -ForegroundColor $lineColor
            }
        }
    }

    Write-Host "`n────────────────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
}

# Главный цикл выполнения
if ($Watch) {
    try {
        while ($true) {
            Render-Report
            Write-Host "Режим живого обновления (каждые ${RefreshInterval}с). Для выхода нажмите Ctrl+C..." -ForegroundColor DarkGray
            Start-Sleep -Seconds $RefreshInterval
        }
    } catch {
        Write-Host "`nМониторинг завершен." -ForegroundColor Yellow
    }
} else {
    Render-Report
    if (-not $NoPause) {
        Write-Host "`nНажмите любую клавишу для закрытия окна..." -ForegroundColor DarkGray
        try {
            [Console]::ReadKey($true) | Out-Null
        } catch {}
    }
}
