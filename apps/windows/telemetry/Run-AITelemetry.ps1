<#
.SYNOPSIS
    Standalone launcher for Windows AI Telemetry Aggregation Service.

.DESCRIPTION
    Launches apps/windows/telemetry aggregation service in background or foreground mode.
    Collects hardware, sensor, network, and file system event telemetry and logs to JSON.

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER Foreground
    Run directly in current console/terminal without detaching.

.PARAMETER NewWindow
    Launch in a visible standalone console/terminal window with -NoExit.

.PARAMETER Interval
    Override baseline polling interval from config.json (seconds).

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\apps\windows\telemetry\Run-AITelemetry.ps1
    .\apps\windows\telemetry\Run-AITelemetry.ps1 -NewWindow
    .\apps\windows\telemetry\Run-AITelemetry.ps1 -Action status
    .\apps\windows\telemetry\Run-AITelemetry.ps1 -Action stop
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [Alias('f', 'Interactive', 'Console')]
    [switch]$Foreground,

    [Alias('Window', 'SeparateWindow')]
    [switch]$NewWindow,

    [float]$Interval = $null,

    [ValidateSet('minimal', 'full')]
    [string]$Mode = 'minimal',

    [switch]$Minimal,

    [Alias('h', '-help')]
    [switch]$Help
)

$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

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

# Resolve project root
$projectRoot = $scriptDir
while ($projectRoot -and -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if ($parent -eq $projectRoot) { break }
    $projectRoot = $parent
}
if (-not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $projectRoot = (Get-Location).Path
}

$env:AIBREADBOARD_DIR = $projectRoot
$env:ASSIST_DIR = $projectRoot

if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║       Run-AITelemetry.ps1 — Windows Telemetry Aggregator      ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch Windows AI Telemetry aggregation and sensor service."
    Write-Host "  Collects hardware, sensors, network, and file events."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\apps\windows\telemetry\Run-AITelemetry.ps1 [-Action start|stop|restart|status] [-NewWindow] [-Foreground]"
    Write-Host "  .\apps\windows\telemetry\Run-AITelemetry.ps1 --help"
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\apps\windows\telemetry\Run-AITelemetry.ps1              # Start in background"
    Write-Host "  .\apps\windows\telemetry\Run-AITelemetry.ps1 -NewWindow   # Start in separate window"
    Write-Host "  .\apps\windows\telemetry\Run-AITelemetry.ps1 -Foreground  # Start interactively in console"
    Write-Host "  .\apps\windows\telemetry\Run-AITelemetry.ps1 -Status      # Check service status"
    Write-Host "  .\apps\windows\telemetry\Run-AITelemetry.ps1 -Stop        # Stop background service"
    Write-Host ""
    exit 0
}

# Determine Python executable
$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
}

# Paths
$mainScript = Join-Path $scriptDir "main.py"
$pidFile = Join-Path $scriptDir "ai_telemetry.pid"

$appDataDir = $env:APPDATA
if (-not $appDataDir) {
    $appDataDir = Join-Path $env:USERPROFILE "AppData\Roaming"
}
$logDir = Join-Path $appDataDir "AI-Breadboard\apps\windows\telemetry\logs"
$logOutFile = Join-Path $logDir "ai_telemetry.log"
$logErrFile = Join-Path $logDir "ai_telemetry_err.log"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

function Get-AITelemetryProcess {
    param([string]$ScriptPath)

    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match [regex]::Escape($ScriptPath)
    }

    return $processes
}

$runningProcs = Get-AITelemetryProcess -ScriptPath $mainScript

if ($Action -eq 'status') {
    if ($runningProcs) {
        $pids = ($runningProcs | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ AI-Telemetry is running (PID: $pids)" -ForegroundColor Green
        Write-Host "   Log file: $logOutFile" -ForegroundColor DarkGray
    } else {
        Write-Host "❌ AI-Telemetry is not running." -ForegroundColor Yellow
    }
    exit 0
}

if ($Action -in @('stop', 'restart')) {
    if ($runningProcs) {
        Write-Host "🛑 Stopping AI-Telemetry..." -ForegroundColor Yellow
        $runningProcs | ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Host "    [OK] Stopped PID $($_.ProcessId)" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Seconds 1

        if (Test-Path $pidFile) {
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "ℹ️ AI-Telemetry was not running." -ForegroundColor DarkGray
    }
    if ($Action -eq 'stop') {
        exit 0
    }
}

if ($Action -in @('start', 'restart')) {
    $existing = Get-AITelemetryProcess -ScriptPath $mainScript
    if ($existing) {
        $pids = ($existing | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ AI-Telemetry is already running (PID: $pids)" -ForegroundColor Green
        exit 0
    }

    $effectiveMode = if ($Minimal) { "minimal" } else { $Mode }
    $appArgs = "`"$mainScript`" --mode $effectiveMode"
    if ($Interval) {
        $appArgs += " --interval $Interval"
    }

    if ($Foreground) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  📊 AI-TELEMETRY RUNNING (FOREGROUND CONSOLE)                  " -ForegroundColor Green
        Write-Host "  Python:    $venvPython                                        " -ForegroundColor DarkGray
        Write-Host "  Log file:  $logOutFile                                        " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Push-Location $projectRoot
        & $venvPython $appArgs
        Pop-Location
        exit $LASTEXITCODE
    }

    if ($NewWindow) {
        Write-Host "    Starting AI-Telemetry in a separate console window..." -ForegroundColor Cyan
        $hasWt = Get-Command wt.exe -ErrorAction SilentlyContinue
        $hasPwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
        $shellExe = if ($hasPwsh) { "pwsh.exe" } else { "powershell.exe" }
        $thisScript = $MyInvocation.MyCommand.Path
        if (-not $thisScript) {
            $thisScript = Join-Path $scriptDir "Run-AITelemetry.ps1"
        }

        if ($hasWt) {
            $proc = Start-Process wt.exe -ArgumentList "-d `"$projectRoot`" --title `"AI-Telemetry`" $shellExe -NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Foreground" -PassThru
        } else {
            $proc = Start-Process $shellExe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Foreground" -WorkingDirectory $projectRoot -PassThru
        }
    } else {
        Write-Host "    Starting AI-Telemetry in background process..." -ForegroundColor Cyan
        $proc = Start-Process $venvPython -ArgumentList $appArgs -WorkingDirectory $projectRoot -PassThru -WindowStyle Minimized -RedirectStandardOutput $logOutFile -RedirectStandardError $logErrFile
    }

    if ($proc) {
        $proc.Id | Out-File -FilePath $pidFile -Encoding utf8

        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ✅ AI-TELEMETRY STARTED IN BACKGROUND!                        " -ForegroundColor Green
        Write-Host "  PID:       $($proc.Id)                                        " -ForegroundColor DarkGray
        Write-Host "  Log file:  $logFile                                           " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[ERROR] Failed to start AI-Telemetry process." -ForegroundColor Red
        exit 1
    }
}
