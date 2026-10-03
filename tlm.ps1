<#
=============================================================================
Process Name: AI-Breadboard Automation - Tlm
=============================================================================
Description:
  Главный корневой лончер системной телеметрии AI-Breadboard (tlm

Usage Examples:
  PowerShell Execution:
    .\tlm.ps1

File: tlm.ps1
Project: ai-breadboard
Package: root
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-02 21:57:05
=============================================================================
.SYNOPSIS
    Главный корневой лончер системной телеметрии AI-Breadboard (tlm
.DESCRIPTION
    Перенаправляет вызовы и параметры во внутренний лончер
    apps\windows\telemetry\Run-Telemetry
#>

$scriptDir = $PSScriptRoot
$targetLauncher = Join-Path $scriptDir "apps\windows\telemetry\launchers\Run-Telemetry.ps1"

if (-not (Test-Path $targetLauncher)) {
    Write-Error "Внутренний лончер телеметрии не найден по пути: $targetLauncher"
    exit 1
}

& $targetLauncher @args
