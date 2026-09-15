<#
.SYNOPSIS
    Standalone applications launcher for AI Breadboard (/apps microservices and web portal).

.DESCRIPTION
    Launches only the applications block (standalone /apps microservices & dedicated /apps web interface):
    - Windows System Administrator (Port 8100)
    - Network Analyzer Terminal (Port 8101)
    - System Inspector (Port 8102)
    - Exchange Trading Terminal (Port 8103)
    - Cloudflare Tunnel Monitor (Port 8104)
    - Shared Applications Web Interface (/apps)

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER NewWindow
    Launch microservices in visible standalone console windows (default: $true).

.PARAMETER Background
    Launch microservices in background processes without opening visible windows.

.PARAMETER Port
    Override server bind port (default: from config.json or 8000).

.PARAMETER HostAddress
    Override server bind address (default: 0.0.0.0 or 127.0.0.1).

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
    Write-Host "  а также специализированного веб-интерфейса /apps:"
    Write-Host "  • Веб-интерфейс приложений       (/apps)" -ForegroundColor White
    Write-Host "  • Windows System Administrator   (порт 8100)" -ForegroundColor White
    Write-Host "  • Network Analyzer Terminal      (порт 8101)" -ForegroundColor White
    Write-Host "  • System Inspector               (порт 8102)" -ForegroundColor White
    Write-Host "  • Exchange Trading Terminal      (порт 8103)" -ForegroundColor White
    Write-Host "  • Cloudflare Tunnel Monitor      (порт 8104)" -ForegroundColor White
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\tc.ps1 [-Action start|stop|restart|status] [-NewWindow] [-Background] [-NoBrowser]"
    Write-Host "  .\tc.ps1 -Interactive"
    Write-Host "  .\tc.ps1 --help"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\tc.ps1                  # Запуск приложений и открытие веб-интерфейса /apps"
    Write-Host "  .\tc.ps1 -Action status   # Проверка статуса работы всех микросервисов"
    Write-Host "  .\tc.ps1 -Action stop     # Остановка сервисов"
    Write-Host "  .\tc.ps1 -Action restart  # Перезапуск сервисов"
    Write-Host "  .\tc.ps1 -Background      # Фоновый запуск без открытия окон"
    Write-Host "  .\tc.ps1 -Interactive     # Интерактивное меню управления"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           AI BREADBOARD — ЗАПУСК БЛОКА ПРИЛОЖЕНИЙ             ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STAGE 2 — ЗАГРУЗКА КОНФИГУРАЦИИ
# ============================================================================
$configPath = Join-Path $scriptDir "config.json"
$envFile = Join-Path $scriptDir ".env"
$cfgHost = "0.0.0.0"
$cfgPort = "8000"
$useSsl = $false
$clientUrl = $null
$useCloudflared = $false

if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($cfg.server.host) { $cfgHost = [string]$cfg.server.host }
        if ($cfg.server.port) { $cfgPort = [string]$cfg.server.port }
        if ($cfg.server.use_ssl -ne $null) { $useSsl = [bool]$cfg.server.use_ssl }
        if ($cfg.server.use_cloudflared -ne $null) { $useCloudflared = [bool]$cfg.server.use_cloudflared }
        if ($cfg.server.client_url) { $clientUrl = [string]$cfg.server.client_url }
        elseif ($cfg.server.user_domain) { $clientUrl = "https://$($cfg.server.user_domain)" }
    } catch {}
}

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
            if ($key -eq "USE_CLOUDFLARED") { $useCloudflared = $val -in ("true","1","yes") }
            if ($key -eq "CLIENT_URL" -and $val) { $clientUrl = $val }
            if ($key -eq "USER_DOMAIN" -and $val -and -not $clientUrl) { $clientUrl = "https://$val" }
        }
    }
}

$host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
$port_ = if ($Port) { [string]$Port } else { [string]$cfgPort }
$proto = if ($useSsl) { "https" } else { "http" }
$browserHost = if ($host_ -eq "0.0.0.0") { "localhost" } else { $host_ }
$appsUrl = "${proto}://${browserHost}:${port_}/apps"

# ============================================================================
# STAGE 3 — ИНТЕРАКТИВНЫЙ РЕЖИМ (ЕСЛИ -Interactive)
# ============================================================================
$isInteractive = $Interactive -and (-not $NonInteractive)

if ($isInteractive) {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host " 📱 УПРАВЛЕНИЕ МИКРОСЕРВИСАМИ И ВЕБ-ИНТЕРФЕЙСОМ /apps" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "  [1] Start   - Запустить приложения и открыть веб-интерфейс /apps" -ForegroundColor White
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

# 1. Проверяем автономные микросервисы через Run-Apps.ps1
$appsLauncher = Join-Path $scriptDir "launchers\Run-Apps.ps1"
if (-not (Test-Path $appsLauncher)) {
    $appsLauncher = Join-Path $scriptDir "Run-Apps.ps1"
}

if (Test-Path $appsLauncher) {
    $callArgs = @{ Action = $Action }
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
                Host_   = $host_
                Port    = $port_
                OpenUrl = $appsUrl
            }
            & $unicornScript @unicornCallArgs
        } else {
            Write-Host "[ERROR] Run-Unicorn.ps1 не найден: $unicornScript" -ForegroundColor Red
            exit 1
        }
    }
}
