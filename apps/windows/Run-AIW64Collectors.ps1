# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Run All AI Windows 64-bit Collectors
# =============================================================================
# Description:
#   Запуск всех сборщиков событий Windows в фоновом режиме.
#
# File: Run-AIW64Collectors.ps1
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

<#
.SYNOPSIS
    Запуск всех сборщиков событий Windows в фоновом режиме

.DESCRIPTION
    Запускает ai_w64_collector и ai_w64_etw_collector в фоновом режиме
    и сохраняет PID для последующей остановки.

.PARAMETER NoWait
    Не ждать завершения (запустить в фоне)

.EXAMPLE
    .\Run-AIW64Collectors.ps1
    Запустить сборщики и ждать (Ctrl+C для остановки)

.EXAMPLE
    .\Run-AIW64Collectors.ps1 -NoWait
    Запустить сборщики в фоновом режиме
#>

param(
    [switch]$NoWait
)

$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
$RootDir = Split-Path -Parent $ScriptDir

# Путь к Python
$PythonPath = Join-Path $RootDir "venv\Scripts\python.exe"

# Проверка Python
if (-not (Test-Path $PythonPath)) {
    Write-Host "ERROR: Python не найден: $PythonPath" -ForegroundColor Red
    exit 1
}

# Путь к лаунчеру
$LauncherPath = Join-Path $ScriptDir "ai_w64_collector_launcher.py"

# Проверка лаунчера
if (-not (Test-Path $LauncherPath)) {
    Write-Host "ERROR: Лаунчер не найден: $LauncherPath" -ForegroundColor Red
    exit 1
}

Write-Host "AI Windows 64-bit Collector - Запуск всех сборщиков" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Запуск в фоновом режиме
if ($NoWait) {
    Write-Host "Запуск в фоновом режиме..." -ForegroundColor Green
    
    $Process = Start-Process -FilePath $PythonPath `
        -ArgumentList @($LauncherPath, "--start") `
        -WindowStyle Normal `
        -PassThru `
        -WorkingDirectory $RootDir
    
    Write-Host "PID процесса: $($Process.Id)" -ForegroundColor Yellow
    Write-Host "Логи: $env:LOCALAPPDATA\AI-Breadboard\ai_w64_logs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Для остановки используйте: python ai_w64_collector_launcher.py --stop" -ForegroundColor Cyan
}
else {
    Write-Host "Запуск (Ctrl+C для остановки)..." -ForegroundColor Green
    
    & $PythonPath $LauncherPath --start
    
    Write-Host ""
    Write-Host "Остановка..." -ForegroundColor Yellow
    & $PythonPath $LauncherPath --stop
}

Write-Host ""
Write-Host "Готово" -ForegroundColor Cyan
