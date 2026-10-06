<#
=============================================================================
Process Name: AI-Breadboard Automation - Tlm
=============================================================================
Description:
  Корневая точка входа (CLI-алиас) для управления службой системной телеметрии.

  Зачем нужен этот скрипт:
    1. Удобный короткий алиас: быстрый запуск подсистемы телеметрии из корня репозитория.
    2. Фоновый тихий запуск LibreHardwareMonitor (LHM): автоматически стартует LHM
       в самом тихом фоновом режиме перед запуском телеметрии, если он еще не запущен.
    3. Прозрачное проксирование: передает любые флаги и параметры (TUI, Background, SQLite и др.)
       напрямую во внутренний диспетчер apps/windows/telemetry/launchers/Run-Telemetry.ps1.

File: tlm.ps1
Project: ai-breadboard
Package: root
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-06 01:26:00
=============================================================================

.SYNOPSIS
    Корневой интерфейс запуска службы системной телеметрии AI-Breadboard.

.DESCRIPTION
    Автоматически запускает LibreHardwareMonitor в тихом фоновом режиме (если он не активен)
    и выполняет запуск сборщика телеметрии в интерактивном, TUI или фоновом режиме.

.EXAMPLE
    .\tlm.ps1
    Запуск службы телеметрии в стандартном консольном режиме (с тихим стартом LHM при необходимости).

.EXAMPLE
    .\tlm.ps1 -TUI
    Запуск интерактивного терминального дашборда мониторинга ресурсов.

.EXAMPLE
    .\tlm.ps1 -Background
    Запуск фоновой службы сбора метрик Windows.
#>

$scriptDir = $PSScriptRoot
$targetLauncher = Join-Path $scriptDir "apps\windows\telemetry\launchers\Run-Telemetry.ps1"
$lhmLauncher = Join-Path $scriptDir "apps\windows\telemetry\launchers\Run-LHM.ps1"

# Проверка параметров: не запускать LHM при вызове справки или остановки
$isStopOrHelp = $false
foreach ($arg in $args) {
    if ($arg -in @('-Help', '-h', '--help', 'stop', 'uninstall-task')) {
        $isStopOrHelp = $true
        break
    }
}

if (-not $isStopOrHelp) {
    # Тихий запуск LibreHardwareMonitor (если процесс еще не запущен)
    $lhmProc = Get-Process -Name "LibreHardwareMonitor" -ErrorAction SilentlyContinue
    if (-not $lhmProc) {
        if (Test-Path $lhmLauncher) {
            & $lhmLauncher -Action start -Background -Quiet
        } else {
            $lhmBin = Join-Path $scriptDir "bin\LibreHardwareMonitor\LibreHardwareMonitor.exe"
            if (Test-Path $lhmBin) {
                $psi = New-Object System.Diagnostics.ProcessStartInfo
                $psi.FileName = $lhmBin
                $psi.WorkingDirectory = Split-Path -Parent $lhmBin
                $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
                $psi.CreateNoWindow = $true
                try {
                    [System.Diagnostics.Process]::Start($psi) | Out-Null
                } catch {}
            }
        }
    }
}

if (-not (Test-Path $targetLauncher)) {
    Write-Error "Внутренний лончер телеметрии не найден по пути: $targetLauncher"
    exit 1
}

& $targetLauncher @args
