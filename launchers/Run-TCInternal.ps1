<#
=============================================================================
Process Name: AI-Breadboard Automation - Run Tcinternal
=============================================================================
Description:
  Запускает/останавливает внутренний FastAPI-сервис Windows TC (apps/windows/api)

Usage Examples:
  PowerShell Execution:
    .\Run-TCInternal.ps1

File: Run-TCInternal.ps1
Project: ai-breadboard
Package: launchers
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-08 13:39:00
=============================================================================
.SYNOPSIS
    Запускает/останавливает внутренний FastAPI-сервис Windows TC (apps/windows/api)
.DESCRIPTION
    Управляет жизненным циклом AI-Breadboard Windows Internal API:
    - Слушает исключительно на 127
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [int]$Port = 8001,

    [string]$ListenHost = '127.0.0.1',

    [ValidateSet('critical','error','warning','info','debug')]
    [string]$LogLevel = 'info'
)

$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) { $scriptDir = (Get-Location).Path }
# Лончер находится в launchers/, корень проекта — на уровень выше
$projectRoot = Split-Path $scriptDir -Parent

$pidFile = Join-Path $env:TEMP "ai-breadboard-tc-internal-$Port.pid"

# ============================================================================
# Функции управления
# ============================================================================

function Get-ServicePid {
    if (Test-Path $pidFile) {
        $storedPid = Get-Content $pidFile -Raw -ErrorAction SilentlyContinue
        if ($storedPid -match '^\d+$') { return [int]$storedPid }
    }
    # Fallback: поиск по командной строке
    $proc = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -match "apps\.windows\.api.*--port\s+$Port" } |
        Select-Object -First 1
    if ($proc) { return $proc.ProcessId }
    return $null
}

function Start-InternalService {
    # Проверяем, не запущен ли уже
    $existingPid = Get-ServicePid
    if ($existingPid) {
        $proc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  [OK] Windows Internal API уже запущен (PID $existingPid, порт $Port)" -ForegroundColor Green
            return
        }
    }

    # Освобождаем порт если занят
    $occupied = netstat -aon 2>$null |
        Select-String ":$Port\s" |
        ForEach-Object { ($_ -split '\s+')[-1] } |
        Where-Object { $_ -match '^\d+$' -and $_ -ne '0' } |
        Select-Object -Unique
    foreach ($pid_ in $occupied) {
        try {
            Stop-Process -Id $pid_ -Force -ErrorAction Stop
            Write-Host "  [OK] Освобождён порт $Port (PID $pid_)" -ForegroundColor Yellow
        } catch {
            Write-Host "  [WARN] Не удалось завершить PID ${pid_}: $_" -ForegroundColor Yellow
        }
    }

    Write-Host "  Запуск Windows Internal API на ${ListenHost}:$Port..." -ForegroundColor Cyan

    $pyArgs = @(
        '-m', 'apps.windows.api',
        '--host', $ListenHost,
        '--port', $Port,
        '--log-level', $LogLevel
    )

    $startParams = @{
        FilePath         = 'py'
        ArgumentList     = $pyArgs
        WorkingDirectory = $projectRoot
        PassThru         = $true
        WindowStyle      = 'Hidden'
    }
    $proc = Start-Process @startParams

    if ($proc) {
        $proc.Id | Set-Content $pidFile -Encoding UTF8
        Write-Host "  [OK] Windows Internal API запущен (PID $($proc.Id))" -ForegroundColor Green
        Write-Host "  [URL] http://${ListenHost}:$Port/tc" -ForegroundColor White
        Write-Host "  [URL] http://${ListenHost}:$Port/health" -ForegroundColor White
        Write-Host "  [URL] http://${ListenHost}:$Port/docs" -ForegroundColor White
    } else {
        Write-Host "  [ERROR] Не удалось запустить Windows Internal API" -ForegroundColor Red
    }
}

function Stop-InternalService {
    $servicePid = Get-ServicePid
    if (-not $servicePid) {
        Write-Host "  [INFO] Windows Internal API не запущен (порт $Port)" -ForegroundColor Yellow
        return
    }
    try {
        Stop-Process -Id $servicePid -Force -ErrorAction Stop
        Write-Host "  [OK] Windows Internal API остановлен (PID $servicePid)" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Не удалось завершить PID ${servicePid}: $_" -ForegroundColor Yellow
    }
    if (Test-Path $pidFile) { Remove-Item $pidFile -Force }
}

function Get-ServiceStatus {
    $servicePid = Get-ServicePid
    if (-not $servicePid) {
        Write-Host "  [STOPPED] Windows Internal API не запущен (порт $Port)" -ForegroundColor Red
        return
    }
    $proc = Get-Process -Id $servicePid -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "  [RUNNING] Windows Internal API активен (PID $servicePid, порт $Port)" -ForegroundColor Green
        # Пробуем health-check
        try {
            $resp = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 2 -ErrorAction Stop
            Write-Host "  [HEALTH] status=$($resp.status), webgui=$($resp.webgui_exists)" -ForegroundColor Green
        } catch {
            Write-Host "  [HEALTH] Сервис запущен, но health-endpoint недоступен (ещё стартует?)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [DEAD] PID $servicePid не активен, очищаю PID-файл" -ForegroundColor Yellow
        if (Test-Path $pidFile) { Remove-Item $pidFile -Force }
    }
}

# ============================================================================
# Диспетчер действий
# ============================================================================
switch ($Action.ToLower()) {
    'start'   { Start-InternalService }
    'stop'    { Stop-InternalService }
    'restart' { Stop-InternalService; Start-Sleep 1; Start-InternalService }
    'status'  { Get-ServiceStatus }
    default   { Write-Host "[ERROR] Неизвестное действие: $Action" -ForegroundColor Red }
}
