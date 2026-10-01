# =============================================================================
# Process Name: AI-Breadboard Automation - Tc Script
# =============================================================================
# Description:
#   PowerShell-сценарий системного обслуживания и запуска (tc).
#
# Usage Examples:
#   PowerShell Execution:
#     .\tc.ps1
#
# File: tc.ps1
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:20:26
# =============================================================================

<#
.SYNOPSIS
    Запускает сервер Windows API (AI Breadboard /tc).

.DESCRIPTION
    Запускает FastAPI сервер для модуля apps/windows/api на порту 8001.
    Доступен по адресу http://localhost:8001/tc

.EXAMPLE
    .\tc.ps1
    .\tc.ps1 -Port 8080
#>

[CmdletBinding()]
param (
    [Alias('Host', 'Address', 'IP')]
    [string]$HostAddress,

    [string]$Port
)

$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) { $scriptDir = (Get-Location).Path }

$pythonExe = if ($env:PYTHON_HOME) { Join-Path $env:PYTHON_HOME 'python.exe' } else { 'python' }

$host_ = if ($HostAddress) { $HostAddress } else { '127.0.0.1' }
$port_ = if ($Port)        { $Port }        else { '8001' }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AI Breadboard Windows Internal API Server" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "  Запуск сервера..." -ForegroundColor Cyan
Write-Host "  URL:    http://${host_}:${port_}/tc" -ForegroundColor Green
Write-Host "  Health: http://${host_}:${port_}/health" -ForegroundColor DarkGray
Write-Host "  Docs:   http://${host_}:${port_}/docs" -ForegroundColor DarkGray
Write-Host ""

# Освобождаем порт если он занят
$occupied = netstat -aon 2>$null |
    Select-String ":${port_}\s" |
    ForEach-Object { ($_ -split '\s+')[-1] } |
    Where-Object { $_ -match '^\d+$' -and $_ -ne '0' } |
    Select-Object -Unique

foreach ($pid_ in $occupied) {
    try {
        Stop-Process -Id $pid_ -Force -ErrorAction Stop
        Write-Host "[OK] Освобождён порт $port_ (PID $pid_)" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Не удалось завершить PID ${pid_}: $_" -ForegroundColor Yellow
    }
}

& $pythonExe -m apps.windows.api --host $host_ --port $port_