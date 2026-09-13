<#
.SYNOPSIS
    Launches the Website Intelligence Monitor Desk (GA4, GSC & Technical Observability).
.DESCRIPTION
    Runs the standalone FastAPI microservice or interactive Rich TUI dashboard
    for Google Analytics 4, Search Console, server telemetry, and AI diagnostics.
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [int]$Port = 8107,

    [Parameter(Mandatory = $false)]
    [string]$Host = "127.0.0.1",

    [Parameter(Mandatory = $false)]
    [switch]$TUI
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

# Activate virtual environment if available
if (Test-Path "$ProjectRoot\.venv\Scripts\Activate.ps1") {
    . "$ProjectRoot\.venv\Scripts\Activate.ps1"
}

if ($TUI) {
    Write-Host "[*] Launching Website Intelligence Monitor Interactive TUI Dashboard..." -ForegroundColor Cyan
    python -m apps.website_monitor
} else {
    Write-Host "[*] Launching Website Intelligence Monitor FastAPI server on http://${Host}:${Port}..." -ForegroundColor Green
    python -m apps.website_monitor --mode server --port $Port
}
