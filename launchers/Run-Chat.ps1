<#
.SYNOPSIS
    AI Chat Application Launcher for AI-Breadboard.

.DESCRIPTION
    Launches the standalone AI Chat application microservice on port 8128.

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER NewWindow
    Launch microservice in visible standalone console window.

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\launchers\Run-Chat.ps1
    .\launchers\Run-Chat.ps1 -NewWindow
    .\launchers\Run-Chat.ps1 -Action status
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
    Write-Host "║              Run-Chat.ps1 — AI CHAT LAUNCHER                  ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch AI Chat microservice."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-Chat.ps1 [-Action start|stop|restart|status] [-NewWindow]"
    Write-Host "  .\launchers\Run-Chat.ps1 --help"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                 AI BREADBOARD — AI CHAT                       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$chatPort = 8128

$chatRunning = $false
try {
    $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*" }
    foreach ($proc in $processes) {
        try {
            $cmdLine = (Get-WmiObject -Query "SELECT CommandLine FROM Win32_Process WHERE ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -and $cmdLine -match "chat" -and $cmdLine -match "$chatPort") {
                $chatRunning = $true
                break
            }
        } catch {
            # Ignore errors
        }
    }
} catch {
    # Ignore errors
}

if ($chatRunning) {
    if ($Action -eq "start" -or $Action -eq "restart") {
        Write-Host "  [INFO] AI Chat is already running on port $chatPort" -ForegroundColor Green
        Write-Host "  Opening chat in browser..." -ForegroundColor Cyan
        Start-Process "http://localhost:$chatPort"
        exit 0
    } elseif ($Action -eq "stop") {
        Write-Host "  Stopping AI Chat..." -ForegroundColor Yellow
        $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*" }
        foreach ($proc in $processes) {
            try {
                $cmdLine = (Get-WmiObject -Query "SELECT CommandLine FROM Win32_Process WHERE ProcessId = $($proc.Id)").CommandLine
                if ($cmdLine -and $cmdLine -match "chat" -and $cmdLine -match "$chatPort") {
                    Stop-Process -Id $proc.Id -Force
                    Write-Host "  AI Chat stopped" -ForegroundColor Green
                    exit 0
                }
            } catch {
                # Ignore errors
            }
        }
    }
}

if ($Action -eq "status") {
    if ($chatRunning) {
        Write-Host "  AI Chat: RUNNING on port $chatPort" -ForegroundColor Green
    } else {
        Write-Host "  AI Chat: STOPPED" -ForegroundColor Red
    }
    exit 0
}

Write-Host "  Starting AI Chat on port $chatPort..." -ForegroundColor Cyan

$pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$startArgs = @()
if ($NewWindow) {
    $startArgs += "-NoExit"
}
$startArgs += "-Command"
$startArgs += "& '$pythonExe' -m uvicorn apps.chat.router:router --port $chatPort --host 127.0.0.1"

if ($NewWindow) {
    Start-Process powershell -ArgumentList $startArgs -WindowStyle Normal
} else {
    & $pythonExe -m uvicorn apps.chat.router:router --port $chatPort --host 127.0.0.1
}

Write-Host ""
Write-Host "  AI Chat started successfully!" -ForegroundColor Green
Write-Host "  Opening chat in browser..." -ForegroundColor Cyan
Start-Process "http://localhost:$chatPort"
