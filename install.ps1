<#
.SYNOPSIS
    AI Breadboard - New Web-Based Installer (v2.0)
    Launches FastAPI server with web interface for installation.
.DESCRIPTION
    1. Installs FastAPI and required packages
    2. Starts web installer server
    3. Opens browser to web GUI for continued installation
.EXAMPLE
    irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
    .\install.ps1
#>

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Определение каталога текущего скрипта
$runningScriptDir = ""
try {
    if ($PSScriptRoot) {
        $runningScriptDir = $PSScriptRoot
    } elseif ($MyInvocation.MyCommand.Path) {
        $runningScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    }
} catch {}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Breadboard Web Installer v2.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Проверка и установка FastAPI
Write-Host "[1/3] Checking FastAPI installation..." -ForegroundColor Cyan

$requiredPackages = @("fastapi", "uvicorn", "pydantic", "aiofiles")
$missingPackages = @()

foreach ($pkg in $requiredPackages) {
    try {
        $result = & python -c "import $pkg" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  $pkg - OK" -ForegroundColor Green
        } else {
            $missingPackages += $pkg
            Write-Host "  $pkg - Not installed" -ForegroundColor Yellow
        }
    } catch {
        $missingPackages += $pkg
        Write-Host "  $pkg - Not installed" -ForegroundColor Yellow
    }
}

# Install missing packages
if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "Installing missing packages..." -ForegroundColor Cyan
    
    try {
        # Upgrade pip first
        Write-Host "  Upgrading pip..." -ForegroundColor Gray
        & python -m pip install --upgrade pip --quiet
        
        # Install missing packages
        $packageList = $missingPackages -join " "
        Write-Host "  Installing: $packageList" -ForegroundColor Gray
        & python -m pip install $packageList --quiet
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] All packages installed successfully" -ForegroundColor Green
        } else {
            Write-Host "  [WARN] Some packages may have failed to install" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [ERROR] Failed to install packages: $_" -ForegroundColor Red
        Write-Host "  Please run manually: python -m pip install $packageList" -ForegroundColor Yellow
        exit 1
    }
}

# 2. Определение путей
$scriptDir = if ($runningScriptDir) { $runningScriptDir } else { $PWD.Path }
$installerDir = Join-Path $scriptDir "installer"
$mainScript = Join-Path $installerDir "install.py"

# Check if installer directory exists
if (-not (Test-Path $mainScript)) {
    Write-Host ""
    Write-Host "  [ERROR] Installer not found at: $mainScript" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please clone the repository first:" -ForegroundColor Yellow
    Write-Host "    git clone https://github.com/hypo69/AI-Breadboard.git" -ForegroundColor Yellow
    exit 1
}

# 3. Запуск веб-сервера
Write-Host ""
Write-Host "[2/3] Starting web installer server..." -ForegroundColor Cyan

# Start server in background
$serverArgs = @("--host", "127.0.0.1", "--port", "8000", "--no-open")
& python $mainScript @serverArgs

Write-Host ""
Write-Host "  Server started on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Browser should open automatically..." -ForegroundColor Cyan
Write-Host "  If not, open: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""