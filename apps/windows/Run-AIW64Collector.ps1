# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Windows 64-bit Collector PowerShell Launcher
# =============================================================================
# Description:
#   PowerShell скрипт для запуска и управления ai_w64_collector.
#
# File: Run-AIW64Collector.ps1
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

<#
.SYNOPSIS
    Запуск и управление AI Windows 64-bit Collector

.DESCRIPTION
    Скрипт для запуска, остановки и управления всеми сборщиками событий Windows.

.PARAMETER Action
    Действие: start, stop, status, events

.PARAMETER EventType
    Фильтр по типу события (для команды events)

.PARAMETER Limit
    Лимит событий (по умолчанию 100)

.PARAMETER Config
    Путь к конфигурационному файлу

.EXAMPLE
    .\Run-AIW64Collector.ps1 -Action start
    Запустить сборщики

.EXAMPLE
    .\Run-AIW64Collector.ps1 -Action status
    Показать статус

.EXAMPLE
    .\Run-AIW64Collector.ps1 -Action events -EventType process_start -Limit 50
    Показать последние 50 событий запуска процессов

.EXAMPLE
    .\Run-AIW64Collector.ps1 -Action stop
    Остановить сборщики
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("start", "stop", "status", "events")]
    [string]$Action,
    
    [Parameter(Mandatory = $false)]
    [string]$EventType = "",
    
    [Parameter(Mandatory = $false)]
    [int]$Limit = 100,
    
    [Parameter(Mandatory = $false)]
    [string]$Config = ""
)

# Путь к скрипту
$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
$RootDir = Split-Path -Parent $ScriptDir

# Путь к Python
$PythonPath = Join-Path $RootDir "venv\Scripts\python.exe"

# Проверка Python
if (-not (Test-Path $PythonPath)) {
    Write-Host "ERROR: Python не найден: $PythonPath" -ForegroundColor Red
    Write-Host "Пожалуйста, запустите установку: .\install.ps1" -ForegroundColor Yellow
    exit 1
}

# Путь к лаунчеру
$LauncherPath = Join-Path $ScriptDir "ai_w64_collector_launcher.py"

# Проверка лаунчера
if (-not (Test-Path $LauncherPath)) {
    Write-Host "ERROR: Лаунчер не найден: $LauncherPath" -ForegroundColor Red
    exit 1
}

# Формируем команду
$Command = "& '$PythonPath' '$LauncherPath' --$Action"

if ($EventType) {
    $Command += " --event-type '$EventType'"
}

$Command += " --limit $Limit"

if ($Config) {
    $Command += " --config '$Config'"
}

Write-Host "AI Windows 64-bit Collector" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

switch ($Action) {
    "start" {
        Write-Host "Запуск сборщиков..." -ForegroundColor Green
        Invoke-Expression $Command
    }
    "stop" {
        Write-Host "Остановка сборщиков..." -ForegroundColor Yellow
        Invoke-Expression $Command
    }
    "status" {
        Write-Host "Статус сборщиков:" -ForegroundColor White
        Invoke-Expression $Command
    }
    "events" {
        Write-Host "Последние события:" -ForegroundColor White
        Invoke-Expression $Command
    }
}

Write-Host ""
Write-Host "Готово" -ForegroundColor Cyan
