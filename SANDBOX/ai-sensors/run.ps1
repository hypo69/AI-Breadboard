<#
.SYNOPSIS
    Standalone launcher for AI-Sensors telemetry aggregation service.

.DESCRIPTION
    Launches SANDBOX/ai-sensors/ in modular structure.
    Collects telemetry from all /apps/ modules and logs to JSON files.

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER Foreground
    Run directly in current console/terminal without detaching.

.PARAMETER NewWindow
    Launch in a visible standalone console/terminal window with -NoExit.

.PARAMETER Interval
    Override interval from config.json (seconds).

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\SANDBOX\ai-sensors\run.ps1
    .\SANDBOX\ai-sensors\run.ps1 -NewWindow
    .\SANDBOX\ai-sensors\run.ps1 -Action status
    .\SANDBOX\ai-sensors\run.ps1 -Action stop
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
if ((Split-Path -Leaf $projectRoot) -eq "ai-sensors" -or -not (Test-Path (Join-Path $projectRoot ".." "main.py"))) {
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
    Write-Host "║        Run-AI-Sensors.ps1 — AI Telemetry Aggregator           ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch AI-Sensors telemetry aggregation service."
    Write-Host "  Collects hardware, file events, and other telemetry from /apps/."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\SANDBOX\ai-sensors\run.ps1 [-Action start|stop|restart|status] [-NewWindow]"
    Write-Host "  .\SANDBOX\ai-sensors\run.ps1 --help"
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\SANDBOX\ai-sensors\run.ps1              # Start with default config"
    Write-Host "  .\SANDBOX\ai-sensors\run.ps1 -NewWindow   # Start in separate window"
    Write-Host "  .\SANDBOX\ai-sensors\run.ps1 -Status      # Check service status"
    Write-Host "  .\SANDBOX\ai-sensors\run.ps1 -Stop        # Stop the service"
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
$pidFile = Join-Path $scriptDir "ai_sensors.pid"
$logDir = Join-Path $scriptDir "logs"
$logFile = Join-Path $logDir "ai_sensors.log"

# Ensure logs directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

function Get-AISensorsProcess {
    param([string]$ScriptPath)

    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match [regex]::Escape($ScriptPath)
    }

    return $processes
}

$runningProcs = Get-AISensorsProcess -ScriptPath $mainScript

if ($Action -eq 'status') {
    if ($runningProcs) {
        $pids = ($runningProcs | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ AI-Sensors is running (PID: $pids)" -ForegroundColor Green
        Write-Host "   Log file: $logFile" -ForegroundColor DarkGray
    } else {
        Write-Host "❌ AI-Sensors is not running." -ForegroundColor Yellow
    }
    exit 0
}

if ($Action -in @('stop', 'restart')) {
    if ($runningProcs) {
        Write-Host "🛑 Stopping AI-Sensors..." -ForegroundColor Yellow
        $runningProcs | ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Host "    [OK] Stopped PID $($_.ProcessId)" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Seconds 1

        # Clean up PID file
        if (Test-Path $pidFile) {
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "ℹ️ AI-Sensors was not running." -ForegroundColor DarkGray
    }
    if ($Action -eq 'stop') {
        exit 0
    }
}

if ($Action -in @('start', 'restart')) {
    $existing = Get-AISensorsProcess -ScriptPath $mainScript
    if ($existing) {
        $pids = ($existing | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ AI-Sensors is already running (PID: $pids)" -ForegroundColor Green
        exit 0
    }

    # Build arguments
    $appArgs = "`"$mainScript`""
    if ($Interval) {
        $appArgs += " --interval $Interval"
    }

    if ($Foreground) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  📊 AI-SENSORS RUNNING (FOREGROUND CONSOLE)                    " -ForegroundColor Green
        Write-Host "  Python:    $venvPython                                        " -ForegroundColor DarkGray
        Write-Host "  Log file:  $logFile                                           " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Push-Location $projectRoot
        & $venvPython $appArgs
        Pop-Location
        exit $LASTEXITCODE
    }

    if ($NewWindow) {
        Write-Host "    Starting AI-Sensors in a separate console window..." -ForegroundColor Cyan
        $hasWt = Get-Command wt.exe -ErrorAction SilentlyContinue
        $hasPwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
        $shellExe = if ($hasPwsh) { "pwsh.exe" } else { "powershell.exe" }
        $thisScript = $MyInvocation.MyCommand.Path
        if (-not $thisScript) {
            $thisScript = Join-Path $scriptDir "run.ps1"
        }

        if ($hasWt) {
            $proc = Start-Process wt.exe -ArgumentList "-d `"$projectRoot`" --title `"AI-Sensors`" $shellExe -NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Foreground" -PassThru
        } else {
            $proc = Start-Process $shellExe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Foreground" -WorkingDirectory $projectRoot -PassThru
        }
    } else {
        Write-Host "    Starting AI-Sensors in background process..." -ForegroundColor Cyan
        $proc = Start-Process $venvPython -ArgumentList $appArgs -WorkingDirectory $projectRoot -PassThru -WindowStyle Minimized -RedirectStandardOutput $logFile -RedirectStandardError $logFile
    }

    if ($proc) {
        # Save PID
        $proc.Id | Out-File -FilePath $pidFile -Encoding utf8

        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ✅ AI-SENSORS STARTED!                                         " -ForegroundColor Green
        Write-Host "  PID:       $($proc.Id)                                        " -ForegroundColor DarkGray
        Write-Host "  Log file:  $logFile                                           " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[ERROR] Failed to start AI-Sensors process." -ForegroundColor Red
        exit 1
    }
}
