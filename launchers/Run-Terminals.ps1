<#
.SYNOPSIS
    Multi-terminal workspace launcher for AI Breadboard and trading desks.

.DESCRIPTION
    Launches orchestrated terminal sessions in a single Windows Terminal (wt.exe) window
    with split panes (Grid / Horizontal / Vertical) or multi-tab layout.
    Falls back gracefully to standalone console windows if Windows Terminal is not installed.

.PARAMETER Preset
    Layout preset to launch:
    - 'breadboard': Server, Assist CLI, Telegram Bot, and Logs
    - 'trading': Market Orderbook & Ticker desk, Positions, Execution logs
    - 'custom': Interactive selection menu
    Default: 'breadboard'.

.PARAMETER Layout
    Pane layout style: 'grid', 'split', 'tabs', 'windows'.
    Default: 'grid'.

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\launchers\Run-Terminals.ps1
    .\launchers\Run-Terminals.ps1 -Preset trading
    .\launchers\Run-Terminals.ps1 -Preset breadboard -Layout tabs
    .\launchers\Run-Terminals.ps1 --help
#>

[CmdletBinding()]
param (
    [ValidateSet('breadboard', 'trading', 'network', 'custom')]
    [string]$Preset = 'breadboard',

    [ValidateSet('grid', 'split', 'tabs', 'windows')]
    [string]$Layout = 'grid',

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

# Project root detection
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
    Write-Host "║           Run-Terminals.ps1 — HELP AND PARAMETERS             ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch multi-terminal workspace (Windows Terminal split-panes or tabs)."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-Terminals.ps1 [-Preset <breadboard|trading|network|custom>] [-Layout <grid|split|tabs|windows>]"
    Write-Host "  .\launchers\Run-Terminals.ps1 --help"
    Write-Host ""
    Write-Host "PRESETS:" -ForegroundColor Yellow
    Write-Host "  breadboard  FastAPI Server + Assist CLI + Telegram Bot + Logs"
    Write-Host "  trading     Exchange Control Desk + Dual Symbol Ticker + Logs"
    Write-Host "  network     Network Analyzer Terminal + Live Packet Stream + AI Alerts"
    Write-Host "  custom      Interactive menu selection"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              AI BREADBOARD — MULTI-TERMINAL WORKSPACE         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Load .env and config.json if present
$envFile = Join-Path $projectRoot ".env"
$configPath = Join-Path $projectRoot "config.json"

$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
}

$hasWt = Get-Command wt.exe -ErrorAction SilentlyContinue
$hasPwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
$shellExe = if ($hasPwsh) { "pwsh.exe" } else { "powershell.exe" }

Write-Host "    Project Root:     $projectRoot" -ForegroundColor DarkGray
Write-Host "    Windows Terminal: $(if ($hasWt) {'Available (wt.exe)'} else {'Not found (Fallback to separate windows)'})" -ForegroundColor DarkGray
Write-Host "    Shell:            $shellExe" -ForegroundColor DarkGray
Write-Host "    Selected Preset:  $Preset ($Layout)" -ForegroundColor Green
Write-Host ""

# Define panes depending on preset
$panes = @()

if ($Preset -eq 'trading') {
    $panes += @{
        Title = "Trading Desk - BTC/USDT"
        Command = "`"$venvPython`" -m apps.trading_terminal --symbol BTC/USDT"
    }
    $panes += @{
        Title = "Trading Desk - ETH/USDT"
        Command = "`"$venvPython`" -m apps.trading_terminal --symbol ETH/USDT"
    }
    $panes += @{
        Title = "Trading Logs & Feed"
        Command = "$shellExe -NoExit -Command `"Write-Host '=== LIVE TRADING EVENT FEED ===' -ForegroundColor Yellow; $shellExe`""
    }
} elseif ($Preset -eq 'network') {
    $panes += @{
        Title = "Network DPI Terminal"
        Command = "`"$venvPython`" -m apps.network_terminal"
    }
    $panes += @{
        Title = "Network Packet Stream"
        Command = "`"$venvPython`" -m apps.network_terminal --simulate"
    }
    $panes += @{
        Title = "Security Feed"
        Command = "$shellExe -NoExit -Command `"Write-Host '=== NETWORK SECURITY & AI FEED ===' -ForegroundColor Cyan; $shellExe`""
    }
} elseif ($Preset -eq 'breadboard') {
    $unicornScript = Join-Path $projectRoot "launchers\Run-Unicorn.ps1"
    $assistScript = Join-Path $projectRoot "assist.ps1"
    $tgScript = Join-Path $projectRoot "launchers\Run-TelegramBot.ps1"

    $panes += @{
        Title = "FastAPI Server"
        Command = "$shellExe -NoExit -ExecutionPolicy Bypass -File `"$unicornScript`""
    }
    $panes += @{
        Title = "Assist CLI"
        Command = "$shellExe -NoExit -ExecutionPolicy Bypass -File `"$assistScript`""
    }
    $panes += @{
        Title = "Telegram Bot"
        Command = "$shellExe -NoExit -ExecutionPolicy Bypass -File `"$tgScript`" -Foreground"
    }
    $logFile = Join-Path $projectRoot "logs\app.log"
    $panes += @{
        Title = "Live Log Monitor"
        Command = "$shellExe -NoExit -Command `"if (Test-Path '$logFile') { Get-Content -Path '$logFile' -Wait -Tail 30 } else { Write-Host 'Waiting for log file...' -ForegroundColor Gray; while (-not (Test-Path '$logFile')) { Start-Sleep 1 }; Get-Content -Path '$logFile' -Wait -Tail 30 }`""
    }
}

if ($hasWt -and $Layout -ne 'windows') {
    Write-Host "🚀 Launching Windows Terminal multi-pane layout..." -ForegroundColor Cyan

    $wtArgs = @("-d", "`"$projectRoot`"")

    for ($i = 0; $i -lt $panes.Count; $i++) {
        $p = $panes[$i]
        if ($i -eq 0) {
            $wtArgs += @("--title", "`"$($p.Title)`"")
            $wtArgs += @($shellExe, "-NoExit", "-Command", $p.Command)
        } else {
            if ($Layout -eq 'tabs') {
                $wtArgs += @(";", "new-tab", "-d", "`"$projectRoot`"", "--title", "`"$($p.Title)`"")
            } else {
                # Alternating horizontal and vertical splits for a 2x2 grid
                $splitFlag = if ($i % 2 -eq 1) { "-H" } else { "-V" }
                $wtArgs += @(";", "split-pane", $splitFlag, "-d", "`"$projectRoot`"", "--title", "`"$($p.Title)`"")
            }
            $wtArgs += @($shellExe, "-NoExit", "-Command", $p.Command)
        }
    }

    $argString = $wtArgs -join " "
    Start-Process wt.exe -ArgumentList $argString
    Write-Host "✅ Terminal workspace started in Windows Terminal." -ForegroundColor Green
} else {
    Write-Host "🚀 Launching separate terminal windows..." -ForegroundColor Cyan
    foreach ($p in $panes) {
        Write-Host "  • Starting $($p.Title)..." -ForegroundColor DarkGray
        Start-Process $shellExe -ArgumentList "-NoExit -Command `"Write-Host '$($p.Title)' -ForegroundColor Cyan; $($p.Command)`"" -WorkingDirectory $projectRoot
    }
    Write-Host "✅ All terminal windows launched." -ForegroundColor Green
}
