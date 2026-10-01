# =============================================================================
# Process Name: AI-Breadboard Automation - Show-Tlm Script
# =============================================================================
# Description:
#   PowerShell-сценарий системного обслуживания и запуска (show-tlm).
#
# Usage Examples:
#   PowerShell Execution:
#     .\show-tlm.ps1
#
# File: show-tlm.ps1
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:20:26
# =============================================================================

<#
.SYNOPSIS
    Лончер для запуска Web GUI исследования системной телеметрии (show-tlm.ps1).

.DESCRIPTION
    Запускает автономный FastAPI веб-сервер исследования телеметрии
    (apps\windows\telemetry_research\main.py) и открывает интерактивный
    дашборд с графиками, анализом аномалий, проверкой гипотез и журналом записей
    в браузере по умолчанию.

.PARAMETER Port
    Порт для веб-сервера (по умолчанию 8090).

.PARAMETER HostAddress
    Хост/IP-адрес для привязки сервера (по умолчанию 127.0.0.1).

.PARAMETER NoBrowser
    Не открывать веб-браузер автоматически после запуска.

.PARAMETER Reload
    Включить режим автоперезагрузки FastAPI (Hot Reload для разработки).

.EXAMPLE
    .\show-tlm.ps1
    .\show-tlm.ps1 -Port 8095
    .\show-tlm.ps1 -NoBrowser
    .\show-tlm.ps1 -Reload
#>

[CmdletBinding()]
param (
    [Alias('p')]
    [int]$Port = 8090,

    [Alias('Host', 'IP', 'Address')]
    [string]$HostAddress = '127.0.0.1',

    [Alias('n', 'NoWeb')]
    [switch]$NoBrowser,

    [Alias('r', 'Dev')]
    [switch]$Reload,

    [Alias('h', '-help')]
    [switch]$Help
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

# Поиск интерпретатора Python (venv или системный py/python)
$pythonExe = $null
$venvPython = Join-Path $scriptDir '.venv\Scripts\python.exe'
$altVenvPython = Join-Path $scriptDir 'venv\Scripts\python.exe'

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} elseif (Test-Path $altVenvPython) {
    $pythonExe = $altVenvPython
} elseif (Get-Command 'py' -ErrorAction SilentlyContinue) {
    $pythonExe = 'py'
} elseif (Get-Command 'python' -ErrorAction SilentlyContinue) {
    $pythonExe = 'python'
} else {
    Write-Error "Интерпретатор Python не найден в системе и в .venv!"
    exit 1
}

$targetModule = Join-Path $scriptDir 'apps\windows\telemetry_research\main.py'
if (-not (Test-Path $targetModule)) {
    Write-Error "Модуль telemetry_research не найден по пути: $targetModule"
    exit 1
}

$url = "http://${HostAddress}:${Port}"

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  🔬 AI-Breadboard: Исследование телеметрии Windows (Web GUI)" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  • URL веб-интерфейса: $url" -ForegroundColor Yellow
Write-Host "  • Интерпретатор:      $pythonExe" -ForegroundColor Gray
Write-Host "  • Модуль:             apps/windows/telemetry_research" -ForegroundColor Gray
if ($Reload) {
    Write-Host "  • Режим Hot-Reload:   Включен" -ForegroundColor Magenta
}
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Нажмите [Ctrl+C] для остановки веб-сервера." -ForegroundColor DarkGray
Write-Host ""

# Автоматическое открытие браузера в фоне
if (-not $NoBrowser) {
    Start-Job -ScriptBlock {
        param($targetUrl)
        Start-Sleep -Seconds 2
        try {
            Start-Process $targetUrl
        } catch {}
    } -ArgumentList $url | Out-Null
}

$cmdArgs = @(
    $targetModule,
    '--host', $HostAddress,
    '--port', $Port.ToString()
)

if ($Reload) {
    $cmdArgs += '--reload'
}

& $pythonExe @cmdArgs
