<#
.SYNOPSIS
    Ollama local service launcher and management.

.DESCRIPTION
    Script for checking, running and managing local Ollama service.
    Detects executable path, tests active port 11434, runs 'ollama serve' in background
    and updates environment variables if needed.

.PARAMETER Action
    start | stop | restart | status

.EXAMPLE
    .\Run-Ollama.ps1
    .\Run-Ollama.ps1 -Action status
    .\Run-Ollama.ps1 -Action restart
    .\Run-Ollama.ps1 -Action stop
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [string]$OllamaExe = ''
)

$ErrorActionPreference = 'Continue'

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

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                  OLLAMA LOCAL SERVICE                         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Find ollama.exe
$exeCandidates = @(
    $OllamaExe,
    (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
    (Join-Path $env:ProgramFiles "Ollama\ollama.exe"),
    "C:\Program Files\Ollama\ollama.exe",
    (Join-Path $env:LOCALAPPDATA "bin\ollama.exe"),
    (Join-Path $projectRoot "ollama.exe")
)

$resolvedExe = $null
foreach ($cand in $exeCandidates) {
    if ($cand -and (Test-Path $cand)) {
        $resolvedExe = $cand
        break
    }
}

if (-not $resolvedExe) {
    $cmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($cmd) {
        $resolvedExe = $cmd.Source
    }
}

function Test-OllamaPort {
    param ([int]$Port = 11434)
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/version" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            return $true
        }
    } catch {
        try {
            $r2 = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($r2.StatusCode -eq 200 -or $r2.Content -match "Ollama is running") {
                return $true
            }
        } catch {}
    }
    return $false
}

$isRunning = Test-OllamaPort

if ($Action -eq 'status') {
    if ($isRunning) {
        Write-Host "✅ Ollama is running on http://localhost:11434" -ForegroundColor Green
    } else {
        Write-Host "❌ Ollama is not running." -ForegroundColor Red
    }
    exit 0
}

if ($Action -eq 'stop') {
    Write-Host "🛑 Stopping Ollama service..." -ForegroundColor Yellow
    Get-Process -Name "ollama" -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "✅ Service stopped." -ForegroundColor Green
    exit 0
}

if ($Action -eq 'restart') {
    Write-Host "🔄 Restarting Ollama service..." -ForegroundColor Yellow
    Get-Process -Name "ollama" -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    $Action = 'start'
}

if ($Action -eq 'start') {
    if ($isRunning) {
        Write-Host "✅ Ollama already running on http://localhost:11434" -ForegroundColor Green
        exit 0
    }

    if (-not $resolvedExe) {
        Write-Host "⚠️  Ollama executable not found on host." -ForegroundColor Yellow
        Write-Host "   Install Ollama from https://ollama.com/download or ensure 'ollama' is in PATH." -ForegroundColor DarkGray
        exit 0
    }

    Write-Host "🚀 Starting Ollama service in a separate window: $resolvedExe serve" -ForegroundColor Cyan
    try {
        $hasWt = Get-Command wt.exe -ErrorAction SilentlyContinue
        $hasPwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
        $shellExe = if ($hasPwsh) { "pwsh.exe" } else { "powershell.exe" }

        if ($hasWt) {
            Start-Process wt.exe -ArgumentList "-d `"$projectRoot`" --title `"Ollama Service`" $shellExe -NoExit -Command `"`& `'$resolvedExe`' serve`""
        } else {
            Start-Process $shellExe -ArgumentList "-NoExit -Command `"`& `'$resolvedExe`' serve`"" -WorkingDirectory $projectRoot
        }

        for ($i = 1; $i -le 10; $i++) {
            Start-Sleep -Seconds 1
            if (Test-OllamaPort) {
                Write-Host "✅ Ollama started successfully!" -ForegroundColor Green
                Write-Host "Base URL: http://localhost:11434" -ForegroundColor Green
                exit 0
            }
            Write-Host "⏳ Waiting for Ollama startup... ($i/10)" -ForegroundColor Gray
        }

        Write-Host "⚠️  Ollama window opened, but port 11434 is not responding yet." -ForegroundColor Yellow
    } catch {
        Write-Host "⚠️  Failed to launch Ollama: $_" -ForegroundColor Yellow
    }
}
