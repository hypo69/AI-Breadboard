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

    [Alias('OAuth')]
    [Nullable[bool]]$EnableOAuth = $null,

    [Alias('TelegramBot', 'TG', 'Telegram')]
    [Nullable[bool]]$EnableTelegramBot = $null,

    [Alias('Worker', 'UnicornWorkers', 'unicorn_workers')]
    [Nullable[int]]$Workers = $null,

    [Alias('Autoreload', 'UnicornReload', 'unicorn_reload')]
    [Nullable[bool]]$Reload = $null,

    [Alias('Url', 'ClientUrl', 'TargetUrl')]
    [string]$OpenUrl,

    [Alias('Config', 'Cfg')]
    [string]$ConfigFile,

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
# DATABASE MIGRATIONS
# ============================================
Write-Host ""
Write-Host "[*] Checking database migrations..." -ForegroundColor Cyan
try {
    $dbMigOut = & $venvPython -m src.db.migrations --apply 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] Database schema is up to date" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Migration check returned: $dbMigOut" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    [WARN] Failed to run database migrations: $_" -ForegroundColor Yellow
}

# ============================================
# ============================================
# LOADING CONFIGURATION
# ============================================
Write-Host ""
Write-Host "[2/4] Loading configuration..." -ForegroundColor Cyan
$cfgFileName = "config.json"
if ($ConfigFile) {
    $cfgFileName = $ConfigFile
} elseif ($env:AIBREADBOARD_CONFIG) {
    $cfgFileName = $env:AIBREADBOARD_CONFIG
} elseif ($env:CONFIG_FILE) {
    $cfgFileName = $env:CONFIG_FILE
}

$candidateConfigPaths = @(
    & { ([System.IO.Path]::IsPathRooted($cfgFileName)) ? $cfgFileName : (Join-Path $projectRoot $cfgFileName) }
    Join-Path $projectRoot "start_scenarios_config\$([System.IO.Path]::GetFileName($cfgFileName))"
    Join-Path $projectRoot "config\$([System.IO.Path]::GetFileName($cfgFileName))"
    Join-Path $projectRoot $cfgFileName
    Join-Path $projectRoot "config.json"
)

$configPath = $candidateConfigPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $configPath) {
    $configPath = Join-Path $projectRoot "config.json"
}

$env:AIBREADBOARD_CONFIG = $configPath
$env:CONFIG_FILE = $configPath
$envFile    = Join-Path $projectRoot ".env"
$cfgHost    = "0.0.0.0"
$cfgPort    = "8000"
$workers    = 1
$useSsl     = $true
$reload     = $false
$clientUrl  = $null
$useCloudflared = $false

$mode    = "dev"
$debug   = "false"

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "PROTOCOL") { $useSsl = ($val.ToLower() -eq "https") }
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
            if ($key -eq "MODE") { $mode = $val.ToLower() }
            if ($key -eq "ENABLE_OAUTH") { $oauthEnabled = $val -in ("true","1","yes") }
            if ($key -eq "ENABLE_TELEGRAM_BOT") { $tgBotEnabled = $val -in ("true","1","yes") }
            if ($key -in ("UNICORN_RELOAD", "RELOAD")) { $reload = $val -in ("true","1","yes") }
            if ($key -in ("UNICORN_WORKERS", "WORKERS")) { $workers = [int]$val }
            if ($key -eq "USE_CLOUDFLARED") { $useCloudflared = $val -in ("true","1","yes") }
            if ($key -eq "CLIENT_URL" -and $val) { $clientUrl = $val }
            if ($key -eq "USER_DOMAIN" -and $val -and -not $clientUrl) { $clientUrl = "https://$val" }
        }
    }
}

if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($cfg -and $cfg.server) {
            if ($cfg.server.host) { $cfgHost = [string]$cfg.server.host }
            if ($cfg.server.port) { $cfgPort = [string]$cfg.server.port }
            if ($cfg.server.protocol) {
                $useSsl = ([string]$cfg.server.protocol.ToString().ToLower() -eq "https")
            } elseif ($cfg.server.use_ssl -ne $null) {
                $useSsl = [bool]$cfg.server.use_ssl
            }
            if ($cfg.server.enable_oauth -ne $null) { $oauthEnabled = [bool]$cfg.server.enable_oauth }
            if ($cfg.server.enable_telegram_bot -ne $null) { $tgBotEnabled = [bool]$cfg.server.enable_telegram_bot }
            if ($cfg.server.mode) { $mode = [string]$cfg.server.mode.ToString().ToLower() }
            if ($cfg.server.debug -ne $null) { $debug = if ($cfg.server.debug) { "true" } else { "false" } }
            if ($cfg.server.PSObject.Properties['use_cloudflared'] -and $cfg.server.use_cloudflared -ne $null) {
                $useCloudflared = [bool]$cfg.server.use_cloudflared
            }
            if ($cfg.server.PSObject.Properties['client_url'] -and $cfg.server.client_url) {
                $clientUrl = [string]$cfg.server.client_url
            } elseif ($cfg.server.PSObject.Properties['user_domain'] -and $cfg.server.user_domain) {
                $clientUrl = "https://$($cfg.server.user_domain)"
            }
            
            # Priority: unicorn_reload -> reload (default: false)
            if ($cfg.server.PSObject.Properties['unicorn_reload'] -and $cfg.server.unicorn_reload -ne $null) {
                $reload = [bool]$cfg.server.unicorn_reload
            } elseif ($cfg.server.PSObject.Properties['reload'] -and $cfg.server.reload -ne $null) {
                $reload = [bool]$cfg.server.reload
            }

            # Priority: unicorn_workers -> workers (default: 1)
            if ($cfg.server.PSObject.Properties['unicorn_workers'] -and $cfg.server.unicorn_workers -ne $null) {
                $workers = [int]$cfg.server.unicorn_workers
            } elseif ($cfg.server.PSObject.Properties['workers'] -and $cfg.server.workers -ne $null) {
                $workers = [int]$cfg.server.workers
            }
        }
    } catch {
        Write-Host "    [WARN] Could not parse $configPath, using defaults: $_" -ForegroundColor Yellow
    }
}

if ($EnableOAuth -ne $null) {
    $oauthEnabled = [bool]$EnableOAuth
}
$env:ENABLE_OAUTH = if ($oauthEnabled) { "true" } else { "false" }

if ($EnableTelegramBot -ne $null) {
    $tgBotEnabled = [bool]$EnableTelegramBot
}
$env:ENABLE_TELEGRAM_BOT = if ($tgBotEnabled) { "true" } else { "false" }

if ($Workers -ne $null) {
    $workers = [int]$Workers
}
if ($Reload -ne $null) {
    $reload = [bool]$Reload
}

$host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
$port  = if ($Port)        { [string]$Port }   else { [string]$cfgPort }

$protoDisplay = if ($useSsl) { "HTTPS (SSL)" } else { "HTTP" }
Write-Host "    Config:     $cfgFileName" -ForegroundColor Gray
Write-Host "    Host:       $host_" -ForegroundColor Gray
Write-Host "    Port:       $port"  -ForegroundColor Gray
Write-Host "    Protocol:   $protoDisplay" -ForegroundColor Gray
Write-Host "    OAuth:      $(if ($oauthEnabled) { 'ENABLED' } else { 'DISABLED (default)' })" -ForegroundColor $(if ($oauthEnabled) { 'Green' } else { 'Yellow' })
Write-Host "    Telegram:   $(if ($tgBotEnabled) { 'ENABLED (FastAPI Lifecycle)' } else { 'DISABLED (default)' })" -ForegroundColor $(if ($tgBotEnabled) { 'Green' } else { 'Yellow' })
Write-Host "    Autoreload: $(if ($reload) { 'ENABLED' } else { 'DISABLED' })" -ForegroundColor $(if ($reload) { 'Green' } else { 'Yellow' })
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
    
    if ($cfg -and $cfg.server -and $cfg.server.ssl) {
        if ($cfg.server.ssl.cert -and (Test-Path $cfg.server.ssl.cert)) { $certFile = $cfg.server.ssl.cert }
        if ($cfg.server.ssl.key -and (Test-Path $cfg.server.ssl.key)) { $keyFile = $cfg.server.ssl.key }
    }
    if ($env:SSL_CERT_FILE -and (Test-Path $env:SSL_CERT_FILE)) { $certFile = $env:SSL_CERT_FILE }
    if ($env:SSL_KEY_FILE -and (Test-Path $env:SSL_KEY_FILE)) { $keyFile = $env:SSL_KEY_FILE }

    if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
        $uvicornArgs += "--ssl-certfile", $certFile, "--ssl-keyfile", $keyFile
        Write-Host "    SSL: enabled ($certFile)" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Certificates not found — running without SSL" -ForegroundColor Yellow
        $useSsl = $false
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
$browserHost = if ($host_ -eq "0.0.0.0") { "localhost" } else { $host_ }
$localAdminUrl = "${browserProto}://${browserHost}:${port}/admin"

if ($OpenUrl) {
    $browserUrl = $OpenUrl
} elseif ($useCloudflared -and $clientUrl) {
    $browserUrl = "$($clientUrl.TrimEnd('/'))/admin"
} else {
    $browserUrl = $localAdminUrl
}

Start-Job -ScriptBlock {
    param($targetPort, $targetOpenUrl, $rootDir)
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
        $edgePaths = @(
            "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
            "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe",
            "${env:LocalAppData}\Microsoft\Edge\Application\msedge.exe"
        )
        $edgeExe = $edgePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
        $profileDir = Join-Path $rootDir "data\browser_profile"

        # Terminate any existing app window processes using this profile
        try {
            $oldAppProcs = Get-CimInstance Win32_Process -Filter "Name = 'msedge.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -and ($_.CommandLine -like "*$profileDir*" -or $_.CommandLine -like "*browser_profile*") }
            if ($oldAppProcs) {
                $oldAppProcs | ForEach-Object {
                    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                }
                Start-Sleep -Milliseconds 300
            }
        } catch {}

        if ($edgeExe) {
            $edgeArgs = @(
                "--app=$targetOpenUrl",
                "--user-data-dir=`"$profileDir`"",
                "--start-maximized"
            )
            Start-Process -FilePath $edgeExe -ArgumentList ($edgeArgs -join " ") -WindowStyle Maximized
        } else {
            Start-Process $targetOpenUrl
        }
    }
} -ArgumentList ([int]$port), $browserUrl, $projectRoot | Out-Null

Write-Host "[INFO] Server starting. App window will open automatically: $browserUrl" -ForegroundColor Green
Write-Host "[INFO] Launching uvicorn in current window..." -ForegroundColor Green
Push-Location $projectRoot
$cmdToRun = "set CONNECTED_DRIVES=$env:CONNECTED_DRIVES && set AIBREADBOARD_CONFIG=$env:AIBREADBOARD_CONFIG && set CONFIG_FILE=$env:CONFIG_FILE && `"$venvPython`" $argStr 2>&1"
cmd /c $cmdToRun | Tee-Object -FilePath $logFilePath
Pop-Location