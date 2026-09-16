<#
.SYNOPSIS
    Standalone launcher for Log Audit & Intelligence application (/tc#tab-system-logs).

.DESCRIPTION
    Launches only the Log Audit & Intelligence application:
    - Runs the web server with direct navigation to /tc#tab-system-logs
    - Supports start, stop, restart, and status checks
    - Opens dedicated web interface or runs in background/foreground

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER NewWindow
    Launch application server in a separate console window.

.PARAMETER Background
    Launch application server in background process without visible console.

.PARAMETER ConfigFile
    Custom configuration JSON file name (default: config_tc.json or config.json).

.PARAMETER Port
    Override server bind port (default: from config or 8000).

.PARAMETER HostAddress
    Override server bind address (default: from config or 127.0.0.1).

.PARAMETER NoBrowser
    Do not automatically open the web browser.

.PARAMETER Interactive
    Run in interactive menu selection mode (-i).

.PARAMETER Help
    Display usage help for the launcher (-Help, -h, --help).

.EXAMPLE
    .\log_audit.ps1
    .\log_audit.ps1 -Action status
    .\log_audit.ps1 -Action stop
    .\log_audit.ps1 -Action restart
    .\log_audit.ps1 -Background
    .\log_audit.ps1 -Interactive
    .\log_audit.ps1 --help
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
    Write-Host "║        log_audit.ps1 — ЛОНЧЕР АУДИТА СИСТЕМНЫХ ЖУРНАЛОВ       ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Запуск ТОЛЬКО приложения Аудита и Анализа системных журналов:"
    Write-Host "  • Интерактивный UI аудита       (/tc#tab-system-logs)" -ForegroundColor White
    Write-Host "  • Data Researcher & Шлюз EDA    (Анализ шума, всплесков и аномалий)" -ForegroundColor White
    Write-Host "  • Адаптивный локальный RAG      (%APPDATA%\AI-Breadboard\apps\system_log_viewer)" -ForegroundColor White
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\log_audit.ps1 [-Action start|stop|restart|status] [-ConfigFile <config_tc.json>] [-NewWindow] [-Background] [-NoBrowser]"
    Write-Host "  .\log_audit.ps1 -Interactive"
    Write-Host "  .\log_audit.ps1 --help"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\log_audit.ps1                               # Запуск аудита логов и открытие интерфейса"
    Write-Host "  .\log_audit.ps1 -Action status                # Проверка статуса сервиса аудита логов"
    Write-Host "  .\log_audit.ps1 -Action stop                  # Остановка сервера"
    Write-Host "  .\log_audit.ps1 -Action restart               # Перезапуск сервиса аудита"
    Write-Host "  .\log_audit.ps1 -Background                   # Фоновый запуск без открытия окна"
    Write-Host "  .\log_audit.ps1 -Interactive                  # Интерактивное меню управления"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       AI BREADBOARD — АУДИТ И АНАЛИЗ СИСТЕМНЫХ ЖУРНАЛОВ       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STAGE 2 — ЗАГРУЗКА КОНФИГУРАЦИИ
# ============================================================================
$activeConfigFile = "config.json"
if ($ConfigFile -and (Test-Path (Join-Path $scriptDir $ConfigFile))) {
    $activeConfigFile = $ConfigFile
} elseif (Test-Path (Join-Path $scriptDir "config_tc.json")) {
    $activeConfigFile = "config_tc.json"
} elseif (Test-Path (Join-Path $scriptDir "config_ts.json")) {
    $activeConfigFile = "config_ts.json"
}

$cfgPath = Join-Path $scriptDir $activeConfigFile
$env:CONFIG_FILE = $activeConfigFile
$env:AIBREADBOARD_CONFIG = $activeConfigFile
$envFile = Join-Path $scriptDir ".env"
$cfgHost = "127.0.0.1"
$cfgPort = "8000"
$useSsl  = $false

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
$auditUrl = "${proto}://${browserHost}:${port_}/tc#tab-system-logs"

# ============================================================================
# STAGE 3 — ИНТЕРАКТИВНЫЙ РЕЖИМ (ЕСЛИ -Interactive)
# ============================================================================
$isInteractive = $Interactive -and (-not $NonInteractive)

if ($isInteractive) {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host " 📜 УПРАВЛЕНИЕ ПРИЛОЖЕНИЕМ АУДИТА ЛОГОВ (SYSTEM LOG AUDIT)" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "  [1] Start   - Запустить приложение аудита логов и открыть UI" -ForegroundColor White
    Write-Host "  [2] Status  - Проверить статус приложения и сервера" -ForegroundColor White
    Write-Host "  [3] Stop    - Остановить сервер" -ForegroundColor White
    Write-Host "  [4] Restart - Перезапустить сервис аудита логов" -ForegroundColor White
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
# STAGE 4 — ОБРАБОТКА ДЕЙСТВИЯ (STATUS, STOP, RESTART, START)
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

function Open-AuditBrowser {
    param([string]$Url)
    if ($NoBrowser) { return }
    Write-Host "🌐 Открытие интерфейса аудита логов: $Url" -ForegroundColor Green
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
            "--window-size=1366,880"
        )
        Start-Process -FilePath $edgeExe -ArgumentList ($edgeArgs -join " ")
    } else {
        Start-Process $Url
    }
}

$isServerRunning = Test-PortListening -CheckPort ([int]$port_)

if ($Action -eq 'status') {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    if ($isServerRunning) {
        Write-Host "✅ Приложение аудита логов доступно: $auditUrl" -ForegroundColor Green
    } else {
        Write-Host "❌ Сервер на порту $port_ не запущен." -ForegroundColor Yellow
        Write-Host "   Для запуска выполните: .\log_audit.ps1" -ForegroundColor DarkGray
    }
    Write-Host ""
    exit 0
}

if ($Action -eq 'stop') {
    Write-Host "🛑 Остановка сервисов AI Breadboard..." -ForegroundColor Yellow
    $unicornPids = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match "uvicorn" -and $_.CommandLine -match "src\.app:app"
    }
    if ($unicornPids) {
        $unicornPids | ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Host "    [OK] Остановлен PID $($_.ProcessId)" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Seconds 1
        Write-Host "✅ Приложение аудита логов остановлено." -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Сервер не был запущен." -ForegroundColor DarkGray
    }
    exit 0
}

if ($Action -in @('start', 'restart')) {
    if ($Action -eq 'restart' -and $isServerRunning) {
        Write-Host "🔄 Перезапуск сервера..." -ForegroundColor Yellow
        $unicornPids = Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -and $_.CommandLine -match "uvicorn" -and $_.CommandLine -match "src\.app:app"
        }
        if ($unicornPids) {
            $unicornPids | ForEach-Object {
                try {
                    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                } catch {}
            }
            Start-Sleep -Seconds 1
        }
        $isServerRunning = $false
    }

    if ($isServerRunning) {
        Write-Host "✅ Сервер уже работает на порту $port_." -ForegroundColor Green
        Open-AuditBrowser -Url $auditUrl
    } else {
        Write-Host "🚀 Запуск приложения аудита логов..." -ForegroundColor Cyan
        Write-Host "   URL интерфейса: $auditUrl" -ForegroundColor Green
        Write-Host ""

        $unicornScript = Join-Path $scriptDir "launchers\Run-Unicorn.ps1"
        if (-not (Test-Path $unicornScript)) {
            $unicornScript = Join-Path $scriptDir "Run-Unicorn.ps1"
        }

        if (Test-Path $unicornScript) {
            $unicornCallArgs = @{
                Host_       = $host_
                Port        = $port_
                OpenUrl     = $auditUrl
                EnableOAuth = $false
                ConfigFile  = $activeConfigFile
            }
            if ($NoBrowser) {
                $unicornCallArgs.Remove('OpenUrl')
            }
            & $unicornScript @unicornCallArgs
        } else {
            Write-Host "[ERROR] Run-Unicorn.ps1 не найден: $unicornScript" -ForegroundColor Red
            exit 1
        }
    }
}
