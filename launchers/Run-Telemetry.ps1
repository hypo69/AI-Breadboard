<#
.SYNOPSIS
    Диспетчер-обертка для запуска службы системной телеметрии AI-Breadboard.

.DESCRIPTION
    Перенаправляет вызов с аргументами в основной лончер apps\windows\Run-Telemetry.ps1.
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status', 'install-task', 'uninstall-task', 'status-task')]
    [string]$Action = 'start',

    [float]$Interval = 5.0,

    [float]$HeavyInterval = 60.0,

    [int]$TopProcesses = 10,

    [ValidateSet('hybrid', 'minimal', 'full')]
    [string]$Mode = 'hybrid',

    [Alias('f', 'Interactive', 'Console')]
    [switch]$Foreground,

    [Alias('Window', 'SeparateWindow')]
    [switch]$NewWindow,

    [Alias('v', 'DebugLog')]
    [switch]$VerboseLog,

    [switch]$Restart,

    [switch]$Force,

    [Alias('h', '-help')]
    [switch]$Help
)

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

$projectRoot = $scriptDir
while ($projectRoot -and -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if ($parent -eq $projectRoot) { break }
    $projectRoot = $parent
}
if (-not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $projectRoot = (Get-Location).Path
}

$targetLauncher = Join-Path $projectRoot "apps\windows\Run-Telemetry.ps1"

if (-not (Test-Path $targetLauncher)) {
    Write-Host "❌ Основной лончер телеметрии не найден по пути: $targetLauncher" -ForegroundColor Red
    exit 1
}

& $targetLauncher @PSBoundParameters @args
exit $LASTEXITCODE
