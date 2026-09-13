<#
.SYNOPSIS
    Starts Ngrok Tunnel for AI-Breadboard server and telemetry forwarding.

.DESCRIPTION
    Launches ngrok HTTP tunnel forwarding port 8000 using NGROK_AUTHTOKEN / NGROCK_AUTOTOKEN
    from .env file. Logs status and provides active public HTTPS URL.

.EXAMPLE
    .\launchers\Run-Ngrok.ps1
#>

[CmdletBinding()]
param (
    [int]$Port = 8000,
    [string]$NgrokExe = ''
)

$ErrorActionPreference = 'Stop'

Write-Host ''
Write-Host '╔═══════════════════════════════════════════════════════════════╗' -ForegroundColor Cyan
Write-Host '║                 NGROK TUNNEL FOR TELEMETRY                    ║' -ForegroundColor Cyan
Write-Host '╚═══════════════════════════════════════════════════════════════╝' -ForegroundColor Cyan

# Determine project root
$scriptDir = $PSScriptRoot
if ((Split-Path -Leaf $scriptDir) -eq "launchers" -or -not (Test-Path (Join-Path $scriptDir "main.py"))) {
    $parent = Split-Path -Parent $scriptDir
    if (Test-Path (Join-Path $parent "main.py")) {
        $projectRoot = $parent
    } else {
        $projectRoot = $scriptDir
    }
} else {
    $projectRoot = $scriptDir
}

$envFile = Join-Path $projectRoot ".env"
$token = $null

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim() -replace "^['`"]|['`"]$"
            if ($key -eq "NGROK_AUTHTOKEN" -or $key -eq "NGROCK_AUTOTOKEN" -or $key -eq "NGROK_TOKEN") {
                if ($val -and $val -ne "your_ngrok_authtoken_here") {
                    $token = $val
                }
            }
        }
    }
}

# Check ngrok executable candidates
$exeCandidates = @(
    $NgrokExe,
    "C:\Users\onela\AppData\Local\bin\ngrok.exe",
    (Join-Path $projectRoot "ngrok.exe"),
    (Join-Path $env:LOCALAPPDATA "bin\ngrok.exe"),
    (Join-Path $projectRoot "bin\ngrok.exe")
)

$resolvedExe = $null
foreach ($cand in $exeCandidates) {
    if ($cand -and (Test-Path $cand)) {
        $resolvedExe = $cand
        break
    }
}

if (-not $resolvedExe) {
    $cmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($cmd) {
        $resolvedExe = $cmd.Source
    }
}

# If ngrok executable is not installed globally, fallback to pyngrok in venv
if (-not $resolvedExe) {
    Write-Host "    ngrok.exe not found in PATH, launching via python pyngrok module..." -ForegroundColor Yellow
    $pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = "python"
    }

    $pyCode = "from src.system.ngrok_tunnel import ngrok_manager; res = ngrok_manager.start_tunnel(); print('STATUS:', res)"
    & $pythonExe -c $pyCode
    exit 0
}

Write-Host "    Ngrok binary: $resolvedExe" -ForegroundColor Gray

# Set authtoken if present
if ($token) {
    Write-Host "    Applying ngrok authtoken..." -ForegroundColor DarkGray
    & $resolvedExe config add-authtoken $token | Out-Null
}

# Stop previous ngrok processes
Write-Host "    Stopping existing ngrok processes..." -ForegroundColor DarkGray
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq 'ngrok.exe' } |
    ForEach-Object {
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            Write-Host "        Stopped PID $($_.ProcessId)" -ForegroundColor DarkGray
        } catch {}
    }

Start-Sleep -Seconds 1

# Prepare logs directory
$logsDir = Join-Path $projectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}
$logFilePath = Join-Path $logsDir "ngrok.log"

$argList = @("http", "$Port", "--log=stdout")

Write-Host "    Starting tunnel on port $Port in background..." -ForegroundColor Cyan
$ngrokProcess = Start-Process $resolvedExe -ArgumentList $argList -PassThru -WindowStyle Minimized -RedirectStandardOutput $logFilePath -RedirectStandardError $logFilePath

Start-Sleep -Seconds 3

# Query local inspector API
$publicUrl = $null
try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($resp.tunnels -and $resp.tunnels.Count -gt 0) {
        $publicUrl = $resp.tunnels[0].public_url
    }
} catch {}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ✅ NGROK TUNNEL STARTED!                                       " -ForegroundColor Green
if ($publicUrl) {
Write-Host "  Public URL:   $publicUrl                                      " -ForegroundColor Green
} else {
Write-Host "  Public URL:   (Starting up, check http://127.0.0.1:4040)      " -ForegroundColor Yellow
}
Write-Host "  Local Port:   $Port                                           " -ForegroundColor Gray
Write-Host "  Log file:     $logFilePath                                    " -ForegroundColor Gray
Write-Host "  PID:          $($ngrokProcess.Id)                             " -ForegroundColor Gray
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
