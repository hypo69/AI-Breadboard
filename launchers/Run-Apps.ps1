<#
.SYNOPSIS
    Universal multi-app orchestrator launcher for all /apps microservices.

.DESCRIPTION
    Starts, stops, restarts, or queries the status of all standalone microservices in /apps:
    - Windows System Administrator (Port 8100)
    - Network Analyzer Terminal (Port 8101)
    - System Inspector (Port 8102)
    - Exchange Trading Desk (Port 8103)
    - Cloudflare Tunnel Monitor (Port 8104)

.PARAMETER Action
    Action to perform across all apps: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER NewWindow
    Launch all apps in visible standalone console windows.

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\launchers\Run-Apps.ps1
    .\launchers\Run-Apps.ps1 -NewWindow
    .\launchers\Run-Apps.ps1 -Action status
    .\launchers\Run-Apps.ps1 -Action stop
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

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
    Write-Host "║           Run-Apps.ps1 — ALL APPS ORCHESTRATOR                ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Manage and launch all standalone microservices in /apps."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-Apps.ps1 [-Action start|stop|restart|status] [-NewWindow]"
    Write-Host "  .\launchers\Run-Apps.ps1 --help"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              AI BREADBOARD — /apps MICROSERVICES              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$appScripts = @(
    @{ Name = "Windows System Administrator"; File = "Run-WindowsAdmin.ps1"; Port = 8100 },
    @{ Name = "Network Analyzer Terminal";    File = "Run-NetworkTerminal.ps1"; Port = 8101 },
    @{ Name = "System Inspector";             File = "Run-SystemInspector.ps1"; Port = 8102 },
    @{ Name = "Exchange Trading Terminal";    File = "Run-TradingTerminal.ps1"; Port = 8103 },
    @{ Name = "Cloudflared Monitor";          File = "Run-CloudflaredMonitor.ps1"; Port = 8104 }
)

foreach ($app in $appScripts) {
    $launcherPath = Join-Path $projectRoot "launchers\$($app.File)"
    if (-not (Test-Path $launcherPath)) {
        $launcherPath = Join-Path $projectRoot $app.File
    }

    if (Test-Path $launcherPath) {
        Write-Host "▶ $($app.Name) (Port: $($app.Port))..." -ForegroundColor Cyan
        $callArgs = @{ Action = $Action }
        if ($NewWindow -and $Action -in @('start', 'restart')) {
            $callArgs['NewWindow'] = $true
        }
        & $launcherPath @callArgs
    } else {
        Write-Host "  [WARN] Launcher script not found: $launcherPath" -ForegroundColor Yellow
    }
}
Write-Host ""
