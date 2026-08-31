<#
.SYNOPSIS
    Microsoft Foundry local server launcher and management.

.DESCRIPTION
    Script for checking, running and managing local Microsoft AI Foundry service.
    Uses CLI command 'foundry server start' and detects active port.
    Supports cross-platform execution with automatic environment configuration.

.PARAMETER Action
    start | stop | restart | status

.EXAMPLE
    .\Run-Foundry.ps1
    .\Run-Foundry.ps1 -Action restart
    .\Run-Foundry.ps1 -Action stop

.NOTES
    Ported from legacy batch scripts for Windows PowerShell execution.
    Automatically updates FOUNDRY_BASE_URL in .env file on startup.
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start'
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

# Project root detection (if script is in launchers/ directory)
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
Write-Host "║              MICROSOFT AI FOUNDRY LOCAL SERVICE               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Checking for CLI presence
function Test-FoundryCli {
    try {
        Get-Command foundry -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Port detection
function Get-FoundryPort {
    try {
        $output = foundry server status 2>&1 | Out-String
        $match  = [regex]::Match($output, 'http://127\.0\.0\.1:(\d+)')
        if ($match.Success) {
            $port = $match.Groups[1].Value
            try {
                $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" `
                    -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                if ($r.StatusCode -eq 200) {
                    return $port
                }
            } catch { }
        }
    } catch {}
    return $null
}

if (-not (Test-FoundryCli)) {
    Write-Error "Foundry CLI ('foundry') not found in your PATH variable."
    Write-Host "Please install Microsoft AI Foundry Local CLI." -ForegroundColor Yellow
    exit 1
}

if ($Action -eq 'stop') {
    Write-Host "🛑 Stopping Microsoft AI Foundry service..." -ForegroundColor Yellow
    try {
        foundry server stop 2>&1 | Out-Host
        Write-Host "✅ Service stopped successfully." -ForegroundColor Green
    } catch {
        Write-Error "Failed to stop Foundry: $_"
    }
    exit 0
}

if ($Action -eq 'restart') {
    Write-Host "🔄 Restarting Microsoft AI Foundry service..." -ForegroundColor Yellow
    try {
        foundry server stop 2>&1 | Out-Host
        Start-Sleep -Seconds 2
    } catch {}
    $Action = 'start'
}

$port = Get-FoundryPort

if ($Action -eq 'status') {
    if ($port) {
        Write-Host "✅ Foundry running on port $port" -ForegroundColor Green
        Write-Host "Base URL: http://localhost:$port/v1/" -ForegroundColor Gray
    } else {
        Write-Host "❌ Foundry is not running." -ForegroundColor Red
    }
    exit 0
}

if ($Action -eq 'start') {
    if ($port) {
        Write-Host "✅ Foundry already running on port $port" -ForegroundColor Green
        Write-Host "Base URL: http://localhost:$port/v1/" -ForegroundColor Gray
    } else {
        Write-Host "🚀 Starting Microsoft AI Foundry local service..." -ForegroundColor Cyan
        try {
            $logsDir = Join-Path $projectRoot "logs"
            if (-not (Test-Path $logsDir)) {
                New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
            }
            $logOutPath = Join-Path $logsDir "foundry_stdout.log"
            $logErrPath = Join-Path $logsDir "foundry_stderr.log"
            Start-Process -FilePath "foundry" -ArgumentList "server", "start" -RedirectStandardOutput $logOutPath -RedirectStandardError $logErrPath -WindowStyle Minimized
            
            for ($i = 1; $i -le 15; $i++) {
                Start-Sleep -Seconds 2
                $port = Get-FoundryPort
                if ($port) {
                    Write-Host ""
                    Write-Host "✅ Foundry started successfully!" -ForegroundColor Green
                    Write-Host "Port:     $port" -ForegroundColor Gray
                    Write-Host "Base URL: http://localhost:$port/v1/" -ForegroundColor Green
                    Write-Host ""
                    
                    # Writing FOUNDRY_BASE_URL to .env for automatic configuration
                    $envFile = Join-Path $projectRoot ".env"
                    if (Test-Path $envFile) {
                        $content = Get-Content $envFile
                        $updated = $false
                        $newContent = @()
                        foreach ($line in $content) {
                            if ($line -match "^FOUNDRY_BASE_URL=") {
                                $newContent += "FOUNDRY_BASE_URL=http://localhost:$port"
                                $updated = $true
                            } else {
                                $newContent += $line
                            }
                        }
                        if (-not $updated) {
                            $newContent += "FOUNDRY_BASE_URL=http://localhost:$port"
                        }
                        $newContent | Set-Content $envFile
                        Write-Host "📝 Updated FOUNDRY_BASE_URL in .env file" -ForegroundColor Gray
                    }
                    break
                }
                Write-Host "⏳ Waiting for Foundry startup... ($i/15)" -ForegroundColor Gray
            }
            if (-not $port) {
                Write-Error "Foundry service startup timeout. Check logs using 'foundry server status'"
            }
        } catch {
            Write-Error "Critical error during Foundry startup: $_"
        }
    }
}
