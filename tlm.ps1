# =============================================================================
# Process Name: AI-Breadboard Automation - Tlm Script
# =============================================================================
# Description:
#   PowerShell-сценарий системного обслуживания и запуска (tlm).
#
# Usage Examples:
#   PowerShell Execution:
#     .\tlm.ps1
#
# File: tlm.ps1
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:20:26
# =============================================================================

<#
.SYNOPSIS
    Главный корневой лончер системной телеметрии AI-Breadboard (tlm.ps1).

.DESCRIPTION
    Перенаправляет вызовы и параметры во внутренний лончер
    apps\windows\telemetry\Run-Telemetry.ps1.

.EXAMPLE
    .\tlm.ps1                                # Интерактивный TUI интерфейс по умолчанию
    .\tlm.ps1 -Action status                 # Статус службы телеметрии
    .\tlm.ps1 -Action stop                   # Остановка службы
    .\tlm.ps1 -GetErrors                     # Просмотр лога ошибок
    .\tlm.ps1 -GetStdOut                     # Просмотр консольного вывода
#>

$scriptDir = $PSScriptRoot
$targetLauncher = Join-Path $scriptDir "apps\windows\telemetry\launchers\Run-Telemetry.ps1"

if (-not (Test-Path $targetLauncher)) {
    Write-Error "Внутренний лончер телеметрии не найден по пути: $targetLauncher"
    exit 1
}

& $targetLauncher @args
