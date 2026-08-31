# =============================================================================
# AI Breadboard Installer - Windows PowerShell Bootstrap
# =============================================================================
# Description: Launches the web-based installer server on Windows
#              This is the recommended entry point for Windows users.
#
# File: installer/install.ps1
# Project: AI Breadboard
# =============================================================================

<#
.SYNOPSIS
    Launches the AI Breadboard web-based installer.
.DESCRIPTION
    Starts the FastAPI installer server and opens the web interface
    in the default browser.
.EXAMPLE
    .\install.ps1
    .\install.ps1 -Port 8080
    .\install.ps1 -NoBrowser
#>

param(
    [int]$Port = 8000,
    [string]$Host = "127.0.0.1",
    [switch]$NoBrowser,
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Cyan
try {
    $pythonCmd = Get-Command python -ErrorAction Stop
    $pythonVersion = & python --version 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Python not found or not working" -ForegroundColor Red
        Write-Host "Please install Python 3.10 or later from https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    Write-Host "Please install Python 3.10 or later from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Cyan
$requiredPackages = @("fastapi", "uvicorn", "pydantic", "aiofiles")
$missingPackages = @()

foreach ($pkg in $requiredPackages) {
    try {
        & python -c "import $pkg" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  $pkg - OK" -ForegroundColor Green
        } else {
            $missingPackages += $pkg
            Write-Host "  $pkg - Missing" -ForegroundColor Red
        }
    } catch {
        $missingPackages += $pkg
        Write-Host "  $pkg - Missing" -ForegroundColor Red
    }
}

# Install missing packages
if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "Installing missing packages..." -ForegroundColor Cyan
    & python -m pip install --upgrade pip --quiet
    
    $packageList = $missingPackages -join " "
    & python -m pip install $packageList --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Packages installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to install packages. Please run manually:" -ForegroundColor Red
        Write-Host "  python -m pip install $packageList" -ForegroundColor Yellow
        exit 1
    }
}

# Start server
Write-Host ""
Write-Host "Starting AI Breadboard Installer..." -ForegroundColor Cyan
Write-Host ""

$serverArgs = @("python", "install.py")
$serverArgs += @("--host", $Host)
$serverArgs += @("--port", $Port.ToString())

if ($Verbose) {
    $serverArgs += "--verbose"
}

# Start server in background
$job = Start-Job -ScriptBlock {
    param($dir, $args)
    Set-Location $dir
    python @args
} -ArgumentList $ScriptDir, $serverArgs

# Wait a moment for server to start
Start-Sleep -Seconds 2

# Check if server is running
$serverUrl = "http://$Host`:$Port"
try {
    $response = Invoke-WebRequest -Uri $serverUrl -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "Server started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  AI Breadboard Installer" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "  URL:  $serverUrl" -ForegroundColor Cyan
        Write-Host ""
        
        # Open browser
        if (-not $NoBrowser) {
            Write-Host "Opening browser..." -ForegroundColor Cyan
            Start-Sleep -Seconds 1
            Start-Process $serverUrl
        }
        
        Write-Host ""
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        
        # Keep script running
        while ($true) {
            Start-Sleep -Seconds 1
        }
    } else {
        Write-Host "ERROR: Server failed to start" -ForegroundColor Red
        Stop-Job $job
        Remove-Job $job
        exit 1
    }
} catch {
    Write-Host "ERROR: Server failed to start" -ForegroundColor Red
    Write-Host "Check the server output above for errors" -ForegroundColor Yellow
    Stop-Job $job
    Remove-Job $job
    exit 1
}