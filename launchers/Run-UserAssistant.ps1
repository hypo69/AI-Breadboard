<#
.SYNOPSIS
    User Assistant launcher for AI-Breadboard.

.DESCRIPTION
    Launches the User Assistant microservice on port 8105.

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER NewWindow
    Launch assistant in visible standalone console window.

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\launchers\Run-UserAssistant.ps1
    .\launchers\Run-UserAssistant.ps1 -NewWindow
    .\launchers\Run-UserAssistant.ps1 -Action status
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
    Write-Host "║           Run-UserAssistant.ps1 — USER ASSISTANT              ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch User Assistant microservice."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-UserAssistant.ps1 [-Action start|stop|restart|status] [-NewWindow]"
    Write-Host "  .\launchers\Run-UserAssistant.ps1 --help"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              AI BREADBOARD — USER ASSISTANT                   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Assistant port
$assistantPort = 8105

# Check if assistant is already running
$assistantRunning = $false
try {
    $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*" }
    foreach ($proc in $processes) {
        try {
            $cmdLine = (Get-WmiObject -Query "SELECT CommandLine FROM Win32_Process WHERE ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -and $cmdLine -match "user_assistant" -and $cmdLine -match "$assistantPort") {
                $assistantRunning = $true
                break
            }
        } catch {
            # Ignore errors
        }
    }
} catch {
    # Ignore errors
}

if ($assistantRunning) {
    if ($Action -eq "start" -or $Action -eq "restart") {
        Write-Host "  [INFO] User Assistant is already running on port $assistantPort" -ForegroundColor Green
        Write-Host "  Opening assistant in browser..." -ForegroundColor Cyan
        Start-Process "http://localhost:$assistantPort"
        exit 0
    } elseif ($Action -eq "stop") {
        Write-Host "  Stopping User Assistant..." -ForegroundColor Yellow
        # Find and stop assistant process
        $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*" }
        foreach ($proc in $processes) {
            try {
                $cmdLine = (Get-WmiObject -Query "SELECT CommandLine FROM Win32_Process WHERE ProcessId = $($proc.Id)").CommandLine
                if ($cmdLine -and $cmdLine -match "user_assistant" -and $cmdLine -match "$assistantPort") {
                    Stop-Process -Id $proc.Id -Force
                    Write-Host "  User Assistant stopped" -ForegroundColor Green
                    exit 0
                }
            } catch {
                # Ignore errors
            }
        }
    }
}

if ($Action -eq "status") {
    if ($assistantRunning) {
        Write-Host "  User Assistant: RUNNING on port $assistantPort" -ForegroundColor Green
    } else {
        Write-Host "  User Assistant: STOPPED" -ForegroundColor Red
    }
    exit 0
}

# Start assistant
Write-Host "  Starting User Assistant on port $assistantPort..." -ForegroundColor Cyan

$assistantScript = Join-Path $projectRoot "apps\user_assistant\__main__.py"
if (Test-Path $assistantScript) {
    $pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = "python"
    }

    $startArgs = @()
    if ($NewWindow) {
        $startArgs += "-NoExit"
    }
    $startArgs += "-Command"
    $startArgs += "& '$pythonExe' '$assistantScript' --port $assistantPort"

    if ($NewWindow) {
        Start-Process powershell -ArgumentList $startArgs -WindowStyle Normal
    } else {
        & $pythonExe $assistantScript --port $assistantPort
    }
} else {
    Write-Host "  [ERROR] User Assistant script not found: $assistantScript" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  User Assistant started successfully!" -ForegroundColor Green
Write-Host "  Opening assistant in browser..." -ForegroundColor Cyan
Start-Process "http://localhost:$assistantPort"