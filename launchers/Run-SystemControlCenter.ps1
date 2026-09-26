<#
.SYNOPSIS
    Standalone launcher for Windows System Control Center microservice.

.DESCRIPTION
    Launches apps.system_control_center in background or standalone window with Uvicorn.
    Listens on port 8109 by default.

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER Mode
    Operation mode: 'server' (FastAPI microservice, default) or 'dashboard' (TUI).

.PARAMETER Port
    Server bind port (default: 8109).

.PARAMETER HostAddress
    Server bind address (default: 127.0.0.1).

.PARAMETER Foreground
    Run directly in current console/terminal without detaching.

.PARAMETER NewWindow
    Launch in a visible standalone console/terminal window with -NoExit.

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\launchers\Run-SystemControlCenter.ps1
    .\launchers\Run-SystemControlCenter.ps1 -NewWindow
    .\launchers\Run-SystemControlCenter.ps1 -Action status
    .\launchers\Run-SystemControlCenter.ps1 -Action stop
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [ValidateSet('server', 'dashboard')]
    [string]$Mode = 'server',

    [int]$Port = 8109,

    [Alias('Host', 'Address', 'IP')]
    [string]$HostAddress = '127.0.0.1',

    [Alias('f', 'Interactive', 'Console')]
    [switch]$Foreground,

    [Alias('Window', 'SeparateWindow')]
    [switch]$NewWindow,

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
if ((Split-Path -Leaf $projectRoot) -eq "launchers" -or -not (Test-Path (Join-Path $projectRoot "main.py"))) {
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
    Write-Host "║    Run-SystemControlCenter.ps1 — HELP AND PARAMETERS          ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch Windows System Control Center microservice / dashboard."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-SystemControlCenter.ps1 [-Action start|stop|restart|status] [-Mode server|dashboard] [-NewWindow]"
    Write-Host "  .\launchers\Run-SystemControlCenter.ps1 --help"
    Write-Host ""
    exit 0
}

$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
}

function Get-AppProcesses {
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match 'apps\.windows\.system_control_center'
    }
}

$runningProcs = Get-AppProcesses

if ($Action -eq 'status') {
    if ($runningProcs) {
        $pids = ($runningProcs | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ System Control Center is running (PID: $pids, Port: $Port)" -ForegroundColor Green
    } else {
        Write-Host "❌ System Control Center is not running." -ForegroundColor Yellow
    }
    exit 0
}

if ($Action -in @('stop', 'restart')) {
    if ($runningProcs) {
        Write-Host "🛑 Stopping System Control Center..." -ForegroundColor Yellow
        $runningProcs | ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Host "    [OK] Stopped PID $($_.ProcessId)" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Seconds 1
    } else {
        Write-Host "ℹ️ System Control Center was not running." -ForegroundColor DarkGray
    }
    if ($Action -eq 'stop') {
        exit 0
    }
}

if ($Action -in @('start', 'restart')) {
    $existing = Get-AppProcesses
    if ($existing) {
        $pids = ($existing | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ System Control Center is already running (PID: $pids)" -ForegroundColor Green
        exit 0
    }

    $appArgs = "-m apps.windows.system_control_center --mode $Mode --host $HostAddress --port $Port"

    if ($Foreground) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  🛠️ SYSTEM CONTROL CENTER RUNNING (FOREGROUND CONSOLE)          " -ForegroundColor Green
        Write-Host "  Host/Port: ${HostAddress}:${Port}                             " -ForegroundColor DarkGray
        Write-Host "  Python:    $venvPython                                        " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Push-Location $projectRoot
        & $venvPython -m apps.windows.system_control_center --mode $Mode --host $HostAddress --port $Port
        Pop-Location
        exit $LASTEXITCODE
    }

    if ($NewWindow) {
        Write-Host "    Starting System Control Center in a separate console window..." -ForegroundColor Cyan
        $hasWt = Get-Command wt.exe -ErrorAction SilentlyContinue
        $hasPwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
        $shellExe = if ($hasPwsh) { "pwsh.exe" } else { "powershell.exe" }
        $thisScript = $MyInvocation.MyCommand.Path
        if (-not $thisScript) {
            $thisScript = Join-Path $projectRoot "launchers\Run-SystemControlCenter.ps1"
        }

        if ($hasWt) {
            $proc = Start-Process wt.exe -ArgumentList "-d `"$projectRoot`" --title `"System Control Center ($Port)`" $shellExe -NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Mode $Mode -HostAddress $HostAddress -Port $Port -Foreground" -PassThru
        } else {
            $proc = Start-Process $shellExe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Mode $Mode -HostAddress $HostAddress -Port $Port -Foreground" -WorkingDirectory $projectRoot -PassThru
        }
    } else {
        $logsDir = Join-Path $projectRoot "logs"
        if (-not (Test-Path $logsDir)) {
            New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
        }
        $logOutPath = Join-Path $logsDir "system_control_center.log"
        $logErrPath = Join-Path $logsDir "system_control_center_stderr.log"

        Write-Host "    Starting System Control Center in background process..." -ForegroundColor Cyan
        $proc = Start-Process $venvPython -ArgumentList "$appArgs" -WorkingDirectory $projectRoot -PassThru -WindowStyle Minimized -RedirectStandardOutput $logOutPath -RedirectStandardError $logErrPath
    }

    if ($proc) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ✅ SYSTEM CONTROL CENTER STARTED!                             " -ForegroundColor Green
        Write-Host "  Address:  http://${HostAddress}:${Port}                       " -ForegroundColor Green
        Write-Host "  Mode:     $Mode                                               " -ForegroundColor DarkGray
        Write-Host "  PID:      $($proc.Id)                                         " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[ERROR] Failed to start System Control Center process." -ForegroundColor Red
        exit 1
    }
}
