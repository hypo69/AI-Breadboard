<#
.SYNOPSIS
    Launch FastAPI server via uvicorn (Unicorn) for ai-breadboard project.

.DESCRIPTION
    Activates virtual environment, loads parameters from config.json and .env,
    frees port, applies SSL if needed and runs FastAPI server in current
    PowerShell window.

.PARAMETER HostAddress
    IP address for binding (e.g.: 0.0.0.0 or 127.0.0.1).
    Aliases: -Host, -Address, -IP, -Host_.

.PARAMETER Port
    TCP port for server (e.g.: 8000).

.PARAMETER Help
    Display usage help for script (-Help, -h, --help).

.EXAMPLE
    .\Run-Unicorn.ps1
    .\Run-Unicorn.ps1 -Host 127.0.0.1 -Port 8000
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [Alias('Host', 'Address', 'IP', 'Host_')]
    [string]$HostAddress,

    [Parameter(Position = 1)]
    [string]$Port,

    [Alias('h', '-help')]
    [switch]$Help
)

if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║           Run-Unicorn.ps1 — HELP AND PARAMETERS               ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PURPOSE:" -ForegroundColor Yellow
    Write-Host "  Launch FastAPI server via uvicorn."
    Write-Host ""
    Write-Host "SYNTAX:" -ForegroundColor Yellow
    Write-Host "  .\Run-Unicorn.ps1 [-Host <0.0.0.0|127.0.0.1>] [-Port <port>]"
    Write-Host "  .\Run-Unicorn.ps1 --help"
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

$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
$venvActivate = Join-Path $projectRoot "venv\Scripts\Activate.ps1"
$env:PYTHONUTF8 = "1"
$env:AIBREADBOARD_DIR = $projectRoot
$env:ASSIST_DIR = $projectRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              LAUNCHING FastAPI SERVER                         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# ACTIVATING VIRTUAL ENVIRONMENT
# ============================================
Write-Host "[1/4] Checking virtual environment..." -ForegroundColor Cyan
if (Test-Path $venvActivate) {
    . $venvActivate
    Write-Host "    [OK] venv activated: $venvPython" -ForegroundColor Green
} else {
    $venvPython = (Get-Command python -ErrorAction Stop).Source
    Write-Host "    [WARN] venv not found, using: $venvPython" -ForegroundColor Yellow
}

# ============================================
# LOADING CONFIGURATION
# ============================================
Write-Host ""
Write-Host "[2/4] Loading configuration..." -ForegroundColor Cyan
$configPath = Join-Path $projectRoot "config.json"
$envFile    = Join-Path $projectRoot ".env"
$cfgHost    = "0.0.0.0"
$cfgPort    = "8000"
$workers    = 1
$useSsl     = $false
$reload     = $true

if (Test-Path $configPath) {
    $cfg     = Get-Content $configPath | ConvertFrom-Json
    if ($cfg.server.host) { $cfgHost = [string]$cfg.server.host }
    if ($cfg.server.port) { $cfgPort = [string]$cfg.server.port }
    $useSsl  = $cfg.server.use_ssl
    $mode    = $cfg.server.mode.ToLower()
    $debug   = if ($cfg.server.debug) { "true" } else { "false" }
    
    if ($cfg.server.PSObject.Properties['reload']) {
        $reload = [bool]$cfg.server.reload
    } else {
        $reload = $true
    }

    if ($cfg.server.PSObject.Properties['workers']) {
        $workers = [int]$cfg.server.workers
    }
} else {
    $mode = "dev"
    $debug = "true"
    $reload = $true
}

# Reading .env
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
            if ($key -eq "MODE") { $mode = $val.ToLower() }
        }
    }
}

$host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
$port  = if ($Port)        { [string]$Port }   else { [string]$cfgPort }

# Check for Gemini API key
$hasApiKey = $false
if ($env:GEMINI_API_KEY -or $env:GOOGLE_API_KEY -or $env:AGY_API_KEY) { $hasApiKey = $true }
$geminiKeysFile = Join-Path $projectRoot "core\secrets\gemini_keys.json"
if (-not $hasApiKey -and (Test-Path $geminiKeysFile)) {
    try {
        $jsonKeys = Get-Content $geminiKeysFile -Raw | ConvertFrom-Json
        foreach ($prop in $jsonKeys.PSObject.Properties) {
            if ($prop.Value.api_key) { $hasApiKey = $true; break }
        }
    } catch {}
}

Write-Host "    Host:       $host_" -ForegroundColor Gray
Write-Host "    Port:       $port"  -ForegroundColor Gray
Write-Host "    AI Keys:    $(if ($hasApiKey) { 'FOUND' } else { 'NOT CONFIGURED (https://aistudio.google.com/app/apikey)' })" -ForegroundColor $(if ($hasApiKey) { 'Green' } else { 'Yellow' })
Write-Host "    Autoreload: $(if ($reload) { 'ENABLED (config.json)' } else { 'DISABLED (config.json)' })" -ForegroundColor $(if ($reload) { 'Green' } else { 'Yellow' })
if (-not $reload) {
    Write-Host "    Workers:    $workers" -ForegroundColor Gray
}

# ============================================
# FREEING PORT
# ============================================
Write-Host ""
Write-Host "[3/4] Freeing port $port..." -ForegroundColor Cyan
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
# LAUNCHING UVICORN
# ============================================
Write-Host ""
if ($reload) {
    Write-Host "[4/4] Launching uvicorn in AUTORELOAD mode..." -ForegroundColor Cyan
} else {
    Write-Host "[4/4] Launching uvicorn with $workers workers..." -ForegroundColor Cyan
}

$uvicornArgs = @(
    "-m", "uvicorn",
    "main:app",
    "--host", $host_,
    "--port", $port,
    "--loop", "asyncio"
)

if ($reload) {
    $uvicornArgs += "--reload"
    $uvicornArgs += "--reload-dir", $projectRoot
    Write-Host "    [MODE] Autoreload active (tracking file changes in $projectRoot)" -ForegroundColor Green
} else {
    if ($workers -gt 1) {
        $uvicornArgs += "--workers", [string]$workers
    }
}

$is_debug = ($mode -in ("dev","debug")) -or ($debug -in ("true","1","yes"))
if ($is_debug) {
    $uvicornArgs += "--log-level", "debug"
} else {
    $uvicornArgs += "--log-level", "info"
}

# SSL
if ($useSsl) {
    $certsDir = Join-Path $env:USERPROFILE ".certs"
    $certFile = Join-Path $certsDir "localhost+2.pem"
    $keyFile  = Join-Path $certsDir "localhost+2-key.pem"
    if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
        $uvicornArgs += "--ssl-certfile", $certFile, "--ssl-keyfile", $keyFile
        Write-Host "    SSL: enabled ($certFile)" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Certificates not found — running without SSL" -ForegroundColor Yellow
    }
}

Write-Host "    Command: $venvPython $($uvicornArgs -join ' ')" -ForegroundColor Gray
Write-Host ""
if ($reload) {
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  AUTORELOAD: ENABLED (auto-restart on code changes)           ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
} else {
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  RUNNING $workers WORKERS — Ctrl+C to stop                    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}
Write-Host ""

# Running in current PowerShell window
$argStr = ($uvicornArgs | ForEach-Object { "`"$_`"" }) -join " "
$logsDir = Join-Path $projectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}
$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$logFilePath = Join-Path $logsDir "uvicorn_${timestamp}.log"
# Background watcher: waits for TCP port readiness and instantly opens browser
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notmatch '^(169\.254|127\.)' -and $_.InterfaceAlias -notmatch 'Loopback' } |
    Select-Object -ExpandProperty IPAddress -First 1)

$browserProto = if ($useSsl) { "https" } else { "http" }
$browserUrl   = "${browserProto}://localhost:${port}/"

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
$cmdToRun = "set CONNECTED_DRIVES=$env:CONNECTED_DRIVES && `"$venvPython`" $argStr 2>&1"
cmd /c $cmdToRun | Tee-Object -FilePath $logFilePath
Pop-Location