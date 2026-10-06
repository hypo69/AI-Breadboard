<#
=============================================================================
Process Name: AI-Breadboard Automation - Tc
=============================================================================
Description:
  Точка входа и лончер внутреннего сервера Windows System API (Terminal Controller / TC)
  с поддержкой переключения телеметрии реального времени (TC mode) на лету.

  Зачем нужен этот скрипт:
    1. Запуск низкоуровневого API: поднимает FastAPI сервер модуля apps/windows/api (порт 8001).
    2. Управление конфликтами портов: автоматически выявляет и освобождает занятый порт
       перед запуском сервера.
    3. Управление режимом телеметрии: активирует режим реального времени (TC mode, flush 5s)
       с авто-возвратом в стандартный режим через 5 минут.

File: tc.ps1
Project: ai-breadboard
Package: root
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-06 03:30:00
=============================================================================

.SYNOPSIS
    Запуск автономного FastAPI сервера Windows System API (модуль /tc).

.DESCRIPTION
    Проверяет доступность порта 8001 (или переопределенного), завершает старые процессы
    при необходимости, активирует режим реального времени телеметрии и запускает сервер.

.PARAMETER HostAddress
    Сетевой адрес для прослушивания запросов (по умолчанию: 127.0.0.1).

.PARAMETER Port
    Сетевой порт сервиса (по умолчанию: 8001).

.PARAMETER RealtimeTelemetry
    Включить телеметрию в реальном времени (TC mode, сброс каждые 5с, автоотключение через 5 мин).
    По умолчанию: $true.

.PARAMETER DisableRealtimeTelemetry
    Принудительно оставить стандартный режим телеметрии (сброс каждые 30с, лимит 100МБ).

.EXAMPLE
    .\tc.ps1
    Запуск Windows API сервера с телеметрией реального времени.

.EXAMPLE
    .\tc.ps1 -DisableRealtimeTelemetry
    Запуск в стандартном режиме сбора телеметрии.
#>

[CmdletBinding()]
param (
    [Alias('Host', 'Address', 'IP')]
    [string]$HostAddress,

    [string]$Port,

    [switch]$RealtimeTelemetry = $true,

    [switch]$DisableRealtimeTelemetry
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

# Конфигурация телеметрии полностью удалена – больше не используется

# =============================================================================
# ВЕРХНЯЯ ПАНЕЛЬ УПРАВЛЕНИЯ TC
# =============================================================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              AI BREADBOARD — WINDOWS SYSTEM CONTROLLER (TC)                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

if ($isRealtime) {
    Write-Host "  [⚙️  ТЕЛЕМЕТРИЯ: РЕАЛЬНОЕ ВРЕМЯ (TC MODE, flush 5s, автоотключение 5м) | Включено]" -ForegroundColor Green
} else {
    Write-Host "  [⚙️  ТЕЛЕМЕТРИЯ: СТАНДАРТНЫЙ РЕЖИМ (flush 30s, max_db 100MB) | Активен]" -ForegroundColor DarkYellow
}
Write-Host "  [📁  Конфиг: $telemetryConfigPath]" -ForegroundColor DarkGray
Write-Host "──────────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan

Write-Host "  URL Сервера: http://${host_}:${port_}/tc" -ForegroundColor Green
Write-Host "  Health:      http://${host_}:${port_}/health" -ForegroundColor Gray
Write-Host "  OpenAPI Doc: http://${host_}:${port_}/docs" -ForegroundColor DarkGray
Write-Host "──────────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
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
        Write-Host "[OK] Освобождён занятый порт $port_ (PID $pid_)" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Не удалось завершить PID ${pid_}: $_" -ForegroundColor Yellow
    }
}

& $pythonExe -m apps.windows.api --host $host_ --port $port_