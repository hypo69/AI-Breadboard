<#
.SYNOPSIS
    AI Breadboard — Графический лончер сценариев и сервисов (алиас).
.DESCRIPTION
    Запускает основной графический интерфейс launcher.ps1.
#>

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

$mainLauncher = Join-Path $scriptDir 'launcher.ps1'
if (Test-Path $mainLauncher) {
    & $mainLauncher @args
} else {
    Write-Error "Главный лончер launcher.ps1 не найден по пути: $mainLauncher"
}
