<#
=============================================================================
Process Name: AI-Breadboard Automation - Run LibreHardwareMonitor Proxy
=============================================================================
Description:
  Корневой лончер-прокси для управления процессом LibreHardwareMonitor (LHM).
  Делегирует исполнение в apps/windows/telemetry/launchers/Run-LHM.ps1.

File: Run-LHM.ps1
Project: ai-breadboard
Package: launchers
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-06 01:24:00
=============================================================================

.SYNOPSIS
    Корневой прокси-лончер LibreHardwareMonitor для AI-Breadboard.

.DESCRIPTION
    Перенаправляет вызов во внутренний лончер apps/windows/telemetry/launchers/Run-LHM.ps1.

.EXAMPLE
    .\launchers\Run-LHM.ps1 -Action status
#>

$scriptDir = $PSScriptRoot
$targetLauncher = Join-Path $scriptDir "..\apps\windows\telemetry\launchers\Run-LHM.ps1"

if (-not (Test-Path $targetLauncher)) {
    $targetLauncher = Join-Path $scriptDir "Run-LHM.ps1"
}

if (-not (Test-Path $targetLauncher)) {
    Write-Error "Внутренний лончер LHM не найден по пути: $targetLauncher"
    exit 1
}

& $targetLauncher @args
