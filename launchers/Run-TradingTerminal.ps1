<#
.SYNOPSIS
    Standalone launcher for Exchange Trading Terminal microservice / TUI desk.

.DESCRIPTION
    Launches apps.trading_terminal in background or standalone window with Uvicorn / Rich TUI.
    Listens on port 8103 by default.

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER Mode
    Operation mode: 'server' (FastAPI microservice, default) or 'dashboard' (TUI).

.PARAMETER Port
    Server bind port (default: 8103).

.PARAMETER HostAddress
    Server bind address (default: 127.0.0.1).

.PARAMETER Symbol
    Trading pair symbol (default: BTC/USDT).

.PARAMETER Foreground
    Run directly in current console/terminal without detaching.

.PARAMETER NewWindow
    Launch in a visible standalone console/terminal window with -NoExit.

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\launchers\Run-TradingTerminal.ps1
    .\launchers\Run-TradingTerminal.ps1 -NewWindow
    .\launchers\Run-TradingTerminal.ps1 -Mode dashboard -NewWindow
    .\launchers\Run-TradingTerminal.ps1 -Action status
    .\launchers\Run-TradingTerminal.ps1 -Action stop
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [ValidateSet('server', 'dashboard')]
    [string]$Mode = 'server',

    [int]$Port = 8103,

    [Alias('Host', 'Address', 'IP')]
    [string]$HostAddress = '127.0.0.1',

    [string]$Symbol = 'BTC/USDT',

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
    Write-Host "║       Run-TradingTerminal.ps1 — HELP AND PARAMETERS           ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch Exchange Trading Terminal microservice / TUI desk."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-TradingTerminal.ps1 [-Action start|stop|restart|status] [-Mode server|dashboard] [-NewWindow]"
    Write-Host "  .\launchers\Run-TradingTerminal.ps1 --help"
    Write-Host ""
    exit 0
}

$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
}

function Get-AppProcesses {
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match 'apps\.trading_terminal'
    }
}

$runningProcs = Get-AppProcesses

if ($Action -eq 'status') {
    if ($runningProcs) {
        $pids = ($runningProcs | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ Exchange Trading Terminal is running (PID: $pids, Port: $Port)" -ForegroundColor Green
    } else {
        Write-Host "❌ Exchange Trading Terminal is not running." -ForegroundColor Yellow
    }
    exit 0
}

if ($Action -in @('stop', 'restart')) {
    if ($runningProcs) {
        Write-Host "🛑 Stopping Exchange Trading Terminal..." -ForegroundColor Yellow
        $runningProcs | ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Host "    [OK] Stopped PID $($_.ProcessId)" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Seconds 1
    } else {
        Write-Host "ℹ️ Exchange Trading Terminal was not running." -ForegroundColor DarkGray
    }
    if ($Action -eq 'stop') {
        exit 0
    }
}

if ($Action -in @('start', 'restart')) {
    $existing = Get-AppProcesses
    if ($existing) {
        $pids = ($existing | ForEach-Object { $_.ProcessId }) -join ', '
        Write-Host "✅ Exchange Trading Terminal is already running (PID: $pids)" -ForegroundColor Green
        exit 0
    }

    $appArgs = if ($Mode -eq 'server') {
        "-m apps.trading_terminal --mode server --host $HostAddress --port $Port"
    } else {
        "-m apps.trading_terminal --symbol $Symbol"
    }

    if ($Foreground) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  📈 TRADING TERMINAL RUNNING (FOREGROUND CONSOLE)              " -ForegroundColor Green
        Write-Host "  Mode:      $Mode                                              " -ForegroundColor DarkGray
        Write-Host "  Host/Port: ${HostAddress}:${Port}                             " -ForegroundColor DarkGray
        Write-Host "  Python:    $venvPython                                        " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Push-Location $projectRoot
        if ($Mode -eq 'server') {
            & $venvPython -m apps.trading_terminal --mode server --host $HostAddress --port $Port
        } else {
            & $venvPython -m apps.trading_terminal --symbol $Symbol
        }
        Pop-Location
        exit $LASTEXITCODE
    }

    if ($NewWindow) {
        Write-Host "    Starting Trading Terminal in a separate console window..." -ForegroundColor Cyan
        $hasWt = Get-Command wt.exe -ErrorAction SilentlyContinue
        $hasPwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
        $shellExe = if ($hasPwsh) { "pwsh.exe" } else { "powershell.exe" }
        $thisScript = $MyInvocation.MyCommand.Path
        if (-not $thisScript) {
            $thisScript = Join-Path $projectRoot "launchers\Run-TradingTerminal.ps1"
        }

        if ($hasWt) {
            $proc = Start-Process wt.exe -ArgumentList "-d `"$projectRoot`" --title `"Trading Terminal ($Port)`" $shellExe -NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Mode $Mode -HostAddress $HostAddress -Port $Port -Symbol $Symbol -Foreground" -PassThru
        } else {
            $proc = Start-Process $shellExe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$thisScript`" -Mode $Mode -HostAddress $HostAddress -Port $Port -Symbol $Symbol -Foreground" -WorkingDirectory $projectRoot -PassThru
        }
    } else {
        $logsDir = Join-Path $projectRoot "logs"
        if (-not (Test-Path $logsDir)) {
            New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
        }
        $logOutPath = Join-Path $logsDir "trading_terminal.log"
        $logErrPath = Join-Path $logsDir "trading_terminal_stderr.log"

        Write-Host "    Starting Trading Terminal in background process..." -ForegroundColor Cyan
        $proc = Start-Process $venvPython -ArgumentList "$appArgs" -WorkingDirectory $projectRoot -PassThru -WindowStyle Minimized -RedirectStandardOutput $logOutPath -RedirectStandardError $logErrPath
    }

    if ($proc) {
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ✅ TRADING TERMINAL STARTED!                                   " -ForegroundColor Green
        if ($Mode -eq 'server') {
            Write-Host "  Address:  http://${HostAddress}:${Port}                       " -ForegroundColor Green
        } else {
            Write-Host "  Symbol:   $Symbol                                             " -ForegroundColor Green
        }
        Write-Host "  Mode:     $Mode                                               " -ForegroundColor DarkGray
        Write-Host "  PID:      $($proc.Id)                                         " -ForegroundColor DarkGray
        Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[ERROR] Failed to start Trading Terminal process." -ForegroundColor Red
        exit 1
    }
}
