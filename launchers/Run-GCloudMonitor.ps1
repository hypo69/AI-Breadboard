<#
.SYNOPSIS
    Launches the Google Cloud Console & Observability Monitor Microservice.
.DESCRIPTION
    Runs the standalone FastAPI microservice for Google Cloud logging,
    metrics, audit inspection, error reporting, and AI diagnostics.
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = False)]
    [int] = 8106,

    [Parameter(Mandatory = False)]
    [string] = "127.0.0.1",

    [Parameter(Mandatory = False)]
    [switch]
)

Continue = "Stop"
 = Split-Path -Parent System.Management.Automation.InvocationInfo.MyCommand.Path
 = Split-Path -Parent 

Set-Location 

# Activate virtual environment if available
if (Test-Path "\.venv\Scripts\Activate.ps1") {
    . "\.venv\Scripts\Activate.ps1"
}

if () {
    Write-Host "[*] Launching Google Cloud Monitor Interactive TUI Dashboard..." -ForegroundColor Cyan
    python -m apps.gcloud_monitor
} else {
    Write-Host "[*] Launching Google Cloud Monitor FastAPI server on http://:..." -ForegroundColor Green
    python -m apps.gcloud_monitor --mode server --host  --port 
}
