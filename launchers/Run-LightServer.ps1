<#
.SYNOPSIS
    Launch lightweight local server for ai-breadboard project.

.DESCRIPTION
    Activates virtual environment, frees port if needed and runs local FastAPI/uvicorn
    server in lightweight mode (1 worker, no external tunnels).

.PARAMETER mode
    Host binding mode:
    - '0.0.0.0' (default): available from all network interfaces and devices on local network
    - 'localhost': available only locally (127.0.0.1)

.PARAMETER port
    Server port (default 8000 or from config.json).

.PARAMETER Help
    Display usage help for script (-Help, -h, --help, -?).

.EXAMPLE
    .\Run-LightServer.ps1
    .\Run-LightServer.ps1 -mode 0.0.0.0
    .\Run-LightServer.ps1 -mode localhost
    .\Run-LightServer.ps1 -mode 0.0.0.0 -port 8000
    .\Run-LightServer.ps1 --help
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [ValidateSet('localhost', '0.0.0.0', '127.0.0.1', 'help', '-h', '--help', '-help')]
    [string]$mode = '0.0.0.0',

    [Parameter(Position = 1)]
    [int]$port = 0,

    [Alias('h', '-help')]
    [switch]$Help
)

$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# ============================================
# HELP OUTPUT (--help / -h / -Help / help)
# ============================================
if ($Help -or $mode -in @('help', '-h', '--help', '-help')) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║       Run-LightServer.ps1 — HELP AND PARAMETERS               ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch lightweight FastAPI/uvicorn server (1 worker, no external tunnels)."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\Run-LightServer.ps1 [-mode <0.0.0.0|localhost>] [-port <port>]"
    Write-Host "  .\Run-LightServer.ps1 --help"
    Write-Host ""
    Write-Host "PARAMETERS:" -ForegroundColor Yellow
    Write-Host "  -mode <string>      IP binding mode (default: 0.0.0.0):"
    Write-Host "                        0.0.0.0               — accessible from all devices on local network."
    Write-Host "                        localhost / 127.0.0.1 — only for local machine."
    Write-Host "  -port <int>         Server port (default: from config.json or 8000)."
    Write-Host "  -Help, -h, --help   Show this help and exit."
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\Run-LightServer.ps1"
    Write-Host "  .\Run-LightServer.ps1 -mode localhost"
    Write-Host "  .\Run-LightServer.ps1 -mode 0.0.0.0"
    Write-Host "  .\Run-LightServer.ps1 -mode 0.0.0.0 -port 8000"
    Write-Host "  .\Run-LightServer.ps1 --help"
    Write-Host ""
    exit 0
}

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir) -and $env:AIBREADBOARD_DIR -and (Test-Path $env:AIBREADBOARD_DIR)) {
    $scriptDir = $env:AIBREADBOARD_DIR
}
if ([string]::IsNullOrEmpty($scriptDir) -and $MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

# Определение корня проекта (если скрипт находится в директории launchers/)
$projectRoot = $scriptDir
if ((Split-Path -Leaf $projectRoot) -eq "launchers" -or -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if (Test-Path (Join-Path $parent "main.py")) {
        $projectRoot = $parent
    }
}

$venvPython   = Join-Path $projectRoot "venv\Scripts\python.exe"
$venvActivate = Join-Path $projectRoot "venv\Scripts\Activate.ps1"
$configPath   = Join-Path $projectRoot "config.json"
$envFile      = Join-Path $projectRoot ".env"
$env:AIBREADBOARD_DIR = $projectRoot
$env:ASSIST_DIR = $projectRoot

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         LAUNCHING LOCAL SERVER (LIGHT MODE)                   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# [1/4] ACTIVATING VIRTUAL ENVIRONMENT
# ============================================
Write-Host "[1/4] Checking virtual environment..." -ForegroundColor Cyan
if (Test-Path $venvPython) {
    if (Test-Path $venvActivate) { . $venvActivate }
    Write-Host "    [OK] venv activated: $venvPython" -ForegroundColor Green
} else {
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $venvPython) {
        Write-Host "    [ERROR] Python not found! Run install.cmd" -ForegroundColor Red
        exit 1
    }
    Write-Host "    [WARN] venv not found, using: $venvPython" -ForegroundColor Yellow
}

# ============================================
# [2/4] SERVER CONFIGURATION
# ============================================
# Determining IP binding based on -mode parameter
if ($mode -eq '0.0.0.0') {
    $host_ = '0.0.0.0'
} else {
    $host_ = '127.0.0.1'
}

# Default values
$defaultPort = 8000
$workers     = 1
$useSsl      = $false
$debugMode   = "dev"

# Reading config.json
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($port -eq 0 -and $cfg.server.port) {
            $port = [int]$cfg.server.port
        }
        if ($cfg.server.use_ssl -ne $null) {
            $useSsl = [bool]$cfg.server.use_ssl
        }
    } catch {}
}

if ($port -eq 0) {
    $port = $defaultPort
}

# Reading .env
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
            if ($key -eq "MODE") { $debugMode = $val.ToLower() }
        }
    }
}

Write-Host "    Mode (mode): $mode ($host_)" -ForegroundColor Gray
Write-Host "    Port:        $port" -ForegroundColor Gray
Write-Host "    SSL:         $(if ($useSsl) { 'ENABLED' } else { 'DISABLED' })" -ForegroundColor Gray

# ============================================
# [3/4] FREEING PORT
# ============================================
Write-Host ""
Write-Host "[2/4] Checking and freeing port $port..." -ForegroundColor Cyan
try {
    $conns = Get-NetTCPConnection -LocalPort ([int]$port) -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns.OwningProcess | Select-Object -Unique
        Write-Host "    [WARN] Port occupied. Terminating PID: $pids" -ForegroundColor Yellow
        $pids | Where-Object { $_ -gt 0 } | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    } else {
        Write-Host "    [OK] Port is free" -ForegroundColor Green
    }
} catch {
    Write-Host "    [WARN] Failed to check port: $_" -ForegroundColor Yellow
}

# ============================================
# [4/4] PREPARING AND LAUNCHING UVICORN
# ============================================
Write-Host ""
Write-Host "[3/4] Preparing uvicorn (Light mode, 1 worker)..." -ForegroundColor Cyan

$uvicornArgs = @(
    "-m", "uvicorn",
    "main:app",
    "--host", $host_,
    "--port", [string]$port,
    "--workers", [string]$workers,
    "--loop", "asyncio"
)

if ($debugMode -in @("dev", "debug")) {
    $uvicornArgs += "--log-level", "debug"
} else {
    $uvicornArgs += "--log-level", "info"
}

# SSL certificates
$proto = "http"
if ($useSsl) {
    $certsDir = Join-Path $env:USERPROFILE ".certs"
    $certFile = Join-Path $certsDir "localhost+2.pem"
    $keyFile  = Join-Path $certsDir "localhost+2-key.pem"
    if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
        $uvicornArgs += "--ssl-certfile", $certFile, "--ssl-keyfile", $keyFile
        $proto = "https"
        Write-Host "    SSL: enabled ($certFile)" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Certificates not found — running over HTTP" -ForegroundColor Yellow
    }
}

$url = "${proto}://${host_}:${port}"

# Determining network IP for devices on local network
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notmatch '^(169\.254|127\.)' -and $_.InterfaceAlias -notmatch 'Loopback' } |
    Select-Object -ExpandProperty IPAddress -First 1)

# For local browser use localhost (valid for SSL certificate)
$browserUrl = "${proto}://localhost:${port}/"

Write-Host "    Command: $venvPython $($uvicornArgs -join ' ')" -ForegroundColor Gray
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  LOCAL SERVER READY TO WORK                                   ║" -ForegroundColor Cyan
Write-Host "║  Mode:            -mode $mode                                ║" -ForegroundColor Cyan
Write-Host "║  Local address:   ${proto}://localhost:${port}/                      ║" -ForegroundColor Green
if ($lanIp -and $mode -eq '0.0.0.0') {
Write-Host "║  Network address: ${proto}://${lanIp}:${port}/                ║" -ForegroundColor Yellow
}
Write-Host "║  (no external tunnels, 1 worker, Ctrl+C to stop)              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""


$logsDir = Join-Path $projectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}
$logFilePath = Join-Path $logsDir "uvicorn_light.log"

$argStr = ($uvicornArgs | ForEach-Object { "`"$_`"" }) -join " "
$cmdToRun = "`"$venvPython`" $argStr 2>&1"

# Background watcher: waits for TCP port readiness and instantly opens browser
Start-Job -ScriptBlock {
    param($targetPort, $targetOpenUrl)
    $maxAttempts = 40
    $connected = $false
    for ($i = 0; $i -lt $maxAttempts; $i++) {
        Start-Sleep -Milliseconds 400
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("127.0.0.1", $targetPort)
            if ($tcp.Connected) {
                $tcp.Close()
                $connected = $true
                break
            }
        } catch {}
    }
    if ($connected) {
        Start-Sleep -Milliseconds 200
        Start-Process $targetOpenUrl
    }
} -ArgumentList ([int]$port), $browserUrl | Out-Null

Write-Host "[INFO] Server starting. Browser will open automatically: $browserUrl" -ForegroundColor Green
Write-Host "[INFO] Launching uvicorn in current window..." -ForegroundColor Green
Push-Location $projectRoot
cmd /c $cmdToRun | Tee-Object -FilePath $logFilePath
Pop-Location