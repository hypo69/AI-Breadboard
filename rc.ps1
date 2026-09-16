<#
.SYNOPSIS
    Forwarding alias launcher for Test Computer / Apps Hub (tc.ps1).

.DESCRIPTION
    Forwards all arguments directly to tc.ps1 in the project root.

.EXAMPLE
    .\rc.ps1
    .\rc.ps1 -Action status
    .\rc.ps1 -ConfigFile config_tc.json
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [Alias('Window', 'SeparateWindow', 'w')]
    [switch]$NewWindow,

    [Alias('bg')]
    [switch]$Background,

    [Alias('Config', 'Cfg')]
    [string]$ConfigFile = 'config_tc.json',

    [Parameter(Position = 1)]
    [string]$Port,

    [Alias('Host', 'Address', 'IP')]
    [string]$HostAddress,

    [Alias('NoOpen', 'Silent')]
    [switch]$NoBrowser,

    [Alias('i')]
    [switch]$Interactive,

    [switch]$NonInteractive,

    [Alias('h', '-help', '?')]
    [switch]$Help
)

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

$tcScript = Join-Path $scriptDir "tc.ps1"

if (Test-Path $tcScript) {
    & $tcScript @PSBoundParameters
} else {
    Write-Error "Сценарий tc.ps1 не найден по пути: $tcScript"
    exit 1
}
