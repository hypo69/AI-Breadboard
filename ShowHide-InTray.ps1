<#
.SYNOPSIS
    Forwarder for launchers/ShowHide-InTray.ps1.

.DESCRIPTION
    Launches ShowHide-InTray.ps1 from launchers directory.

.EXAMPLE
    .\ShowHide-InTray.ps1
    .\ShowHide-InTray.ps1 -Action hide
    .\ShowHide-InTray.ps1 -Action show
#>

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

$launcher = Join-Path $scriptDir "launchers\ShowHide-InTray.ps1"
if (Test-Path $launcher) {
    & $launcher @args
} else {
    Write-Error "Launcher not found: $launcher"
}
