<#
.SYNOPSIS
    Standalone applications launcher for AI Breadboard (/apps microservices and web portal).

.DESCRIPTION
    Launches only the applications block configured in config_tc.json or config.json:
    - Dedicated /apps web interface
    - Configured microservices (Network, System Inspector, Sysadmin, Cloudflared, GCloud, Website Monitor)

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER NewWindow
    Launch microservices in visible standalone console windows (default: $true).

.PARAMETER Background
    Launch microservices in background processes without opening visible windows.

.PARAMETER ConfigFile
    Custom configuration JSON file name (default: config_tc.json or config.json).

.PARAMETER Port
    Override server bind port (default: from config_tc.json / config.json or 8000).

.PARAMETER HostAddress
    Override server bind address (default: from config_tc.json / config.json or 127.0.0.1).

.PARAMETER NoBrowser
    Do not automatically open the web browser.

.PARAMETER Interactive
    Run in interactive menu selection mode (-i).

.PARAMETER Help
    Display usage help for the launcher (-Help, -h, --help).

.EXAMPLE
    .\tc.ps1
    .\tc.ps1 -Action status
    .\tc.ps1 -Action stop
    .\tc.ps1 -Action restart
    .\tc.ps1 -ConfigFile config_tc.json
    .\tc.ps1 -Background
    .\tc.ps1 -Interactive
    .\tc.ps1 --help
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

$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

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

$env:AIBREADBOARD_DIR = $scriptDir
$env:ASSIST_DIR = $scriptDir
$env:ENABLE_OAUTH = "false"
$env:DISABLE_AUTH = "true"

# ============================================================================
# STAGE 1 — СПРАВКА И ПАРАМЕТРЫ
# ============================================================================
if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║              tc.ps1 — ЛОНЧЕР БЛОКА ПРИЛОЖЕНИЙ                 ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Запуск ТОЛЬКО блока приложений и автономных микросервисов из /apps,"
    Write-Host "  настроенных в config_tc.json или config.json:"
    Write-Host "  • Веб-интерфейс приложений       (/apps)" -ForegroundColor White
    Write-Host "  • Настройки запуска приложений   (config_tc.json)" -ForegroundColor White
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\tc.ps1 [-Action start|stop|restart|status] [-ConfigFile <config_tc.json>] [-NewWindow] [-Background] [-NoBrowser]"
    Write-Host "  .\tc.ps1 -Interactive"
    Write-Host "  .\tc.ps1 --help"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\tc.ps1                               # Запуск приложений по config_tc.json"
    Write-Host "  .\tc.ps1 -Action status                # Проверка статуса работы всех микросервисов"
    Write-Host "  .\tc.ps1 -ConfigFile config_tc.json    # Явное указание файла конфигурации"
    Write-Host "  .\tc.ps1 -Action stop                  # Остановка сервисов"
    Write-Host "  .\tc.ps1 -Action restart               # Перезапуск сервисов"
    Write-Host "  .\tc.ps1 -Background                   # Фоновый запуск без открытия окон"
    Write-Host "  .\tc.ps1 -Interactive                  # Интерактивное меню управления"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           AI BREADBOARD — ЗАПУСК БЛОКА ПРИЛОЖЕНИЙ             ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STAGE 2 — ЗАГРУЗКА КОНФИГУРАЦИИ (config_tc.json -> config.json)
# ============================================================================
$activeConfigFile = "config.json"
if ($ConfigFile -and (Test-Path (Join-Path $scriptDir $ConfigFile))) {
    $activeConfigFile = $ConfigFile
} elseif (Test-Path (Join-Path $scriptDir "config_ts.json")) {
    $activeConfigFile = "config_ts.json"
} elseif (Test-Path (Join-Path $scriptDir "config_tc.json")) {
    $activeConfigFile = "config_tc.json"
}

$cfgPath = Join-Path $scriptDir $activeConfigFile
$env:CONFIG_FILE = $activeConfigFile
$env:AIBREADBOARD_CONFIG = $activeConfigFile
$envFile = Join-Path $scriptDir ".env"
$cfgHost = "127.0.0.1"
$cfgPort = "8000"
$useSsl  = $false
$cfgApps = $null

if (Test-Path $cfgPath) {
    try {
        $cfg = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($cfg.server) {
            if ($cfg.server.host) { $cfgHost = [string]$cfg.server.host }
            if ($cfg.server.port) { $cfgPort = [string]$cfg.server.port }
            if ($cfg.server.protocol) {
                $useSsl = ([string]$cfg.server.protocol.ToString().ToLower() -eq "https")
            } elseif ($cfg.server.use_ssl -ne $null) {
                $useSsl = [bool]$cfg.server.use_ssl
            }
        }
        if ($cfg.apps) {
            $cfgApps = $cfg.apps
        }
        Write-Host "  [OK] Загружена конфигурация: $($activeConfigFile)" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Ошибка чтения $($activeConfigFile): $_" -ForegroundColor Yellow
    }
}

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "PROTOCOL") { $useSsl = ($val.ToLower() -eq "https") }
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
        }
    }
}

$host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
$port_ = if ($Port) { [string]$Port } else { [string]$cfgPort }
$proto = if ($useSsl) { "https" } else { "http" }
$browserHost = if ($host_ -eq "0.0.0.0") { "localhost" } else { $host_ }
$appsUrl = "${proto}://${browserHost}:${port_}/tc"

# ============================================================================
# STAGE 3 — ИНТЕРАКТИВНЫЙ РЕЖИМ (ЕСЛИ -Interactive)
# ============================================================================
$isInteractive = $Interactive -and (-not $NonInteractive)

if ($isInteractive) {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host " 📱 УПРАВЛЕНИЕ МИКРОСЕРВИСАМИ И ВЕБ-ИНТЕРФЕЙСОМ /tc" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "  [1] Start   - Запустить приложения и открыть веб-интерфейс /tc" -ForegroundColor White
    Write-Host "  [2] Status  - Проверить статус запущенных микросервисов и сервера" -ForegroundColor White
    Write-Host "  [3] Stop    - Остановить микросервисы" -ForegroundColor White
    Write-Host "  [4] Restart - Перезапустить микросервисы" -ForegroundColor White
    Write-Host "  [Enter] По умолчанию: $Action" -ForegroundColor Green
    Write-Host ""

    $actionChoice = Read-Host "Действие [Enter = $Action]"
    $actionChoice = $actionChoice.Trim()
    if ($actionChoice -eq "1") {
        $Action = "start"
    } elseif ($actionChoice -eq "2") {
        $Action = "status"
    } elseif ($actionChoice -eq "3") {
        $Action = "stop"
    } elseif ($actionChoice -eq "4") {
        $Action = "restart"
    }
}

# ============================================================================
# STAGE 4 — ОПРЕДЕЛЕНИЕ ПАРАМЕТРОВ ОКОН
# ============================================================================
$openNewWindow = $true
if ($Background) {
    $openNewWindow = $false
} elseif ($PSBoundParameters.ContainsKey('NewWindow')) {
    $openNewWindow = [bool]$NewWindow
}

# ============================================================================
# STAGE 5 — ОБРАБОТКА ДЕЙСТВИЯ (STATUS, STOP, RESTART, START)
# ============================================================================
function Test-PortListening {
    param([int]$CheckPort)
    try {
        $conns = Get-NetTCPConnection -LocalPort $CheckPort -State Listen -ErrorAction SilentlyContinue
        return ($null -ne $conns)
    } catch {
        return $false
    }
}

function Open-AppsBrowser {
    param([string]$Url)
    if ($NoBrowser) { return }
    Write-Host "🌐 Открытие веб-интерфейса приложений: $Url" -ForegroundColor Green
    $edgePaths = @(
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe",
        "${env:LocalAppData}\Microsoft\Edge\Application\msedge.exe"
    )
    $edgeExe = $edgePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    $profileDir = Join-Path $scriptDir "data\browser_profile"

    if ($edgeExe) {
        $edgeArgs = @(
            "--app=$Url",
            "--user-data-dir=`"$profileDir`"",
            "--window-size=1280,850"
        )
        Start-Process -FilePath $edgeExe -ArgumentList ($edgeArgs -join " ")
    } else {
        Start-Process $Url
    }
}

# 1. Проверяем и запускаем микросервисы через Run-Apps.ps1 с учетом config_tc.json
$appsLauncher = Join-Path $scriptDir "launchers\Run-Apps.ps1"
if (-not (Test-Path $appsLauncher)) {
    $appsLauncher = Join-Path $scriptDir "Run-Apps.ps1"
}

if (Test-Path $appsLauncher) {
    $callArgs = @{
        Action     = $Action
        ConfigFile = $activeConfigFile
    }
    if ($openNewWindow -and $Action -in @('start', 'restart')) {
        $callArgs['NewWindow'] = $true
    }
    & $appsLauncher @callArgs
}

# 2. Проверяем состояние основного сервера (для shared-режима)
$isServerRunning = Test-PortListening -CheckPort ([int]$port_)

if ($Action -eq 'status') {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    if ($isServerRunning) {
        Write-Host "✅ Веб-интерфейс приложений активен: $appsUrl" -ForegroundColor Green
    } else {
        Write-Host "❌ Веб-сервер на порту $port_ не запущен." -ForegroundColor Yellow
        Write-Host "   Для запуска выполните: .\tc.ps1" -ForegroundColor DarkGray
    }
    Write-Host ""
    exit 0
}

if ($Action -eq 'stop') {
    Write-Host "✅ Остановка приложений завершена." -ForegroundColor Green
    exit 0
}

if ($Action -in @('start', 'restart')) {
    if ($isServerRunning) {
        Write-Host "✅ Веб-сервер уже работает на порту $port_." -ForegroundColor Green
        Open-AppsBrowser -Url $appsUrl
    } else {
        Write-Host "🚀 Запуск веб-сервера с интерфейсом приложений..." -ForegroundColor Cyan
        Write-Host "   URL интерфейса: $appsUrl" -ForegroundColor Green
        Write-Host ""

        $unicornScript = Join-Path $scriptDir "launchers\Run-Unicorn.ps1"
        if (-not (Test-Path $unicornScript)) {
            $unicornScript = Join-Path $scriptDir "Run-Unicorn.ps1"
        }

        if (Test-Path $unicornScript) {
            $unicornCallArgs = @{
                Host_       = $host_
                Port        = $port_
                OpenUrl     = $appsUrl
                EnableOAuth = $false
                ConfigFile  = $activeConfigFile
            }
            & $unicornScript @unicornCallArgs
        } else {
            Write-Host "[ERROR] Run-Unicorn.ps1 не найден: $unicornScript" -ForegroundColor Red
            exit 1
        }
    }
}
