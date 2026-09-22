<#
.SYNOPSIS
    Standalone applications launcher for AI Breadboard (/tc and /apps Test Computer microservices).

.DESCRIPTION
    Launches only the test computer applications block configured in config_tc.json:
    - Dedicated /tc web interface
    - Configured system test microservices (Network, System Inspector, Sysadmin, Control Center, Log Viewer, Software Audit, Registry Viewer, Startup Auditor)

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

.PARAMETER EnableTray
    Включить интеграцию с системным треем Windows (по умолчанию: $true).
    Алиасы: -Tray, -SystemTray, -tray_mode.

.PARAMETER DisableCloseButton
    Отключить кнопку закрытия консоли ([X]) для предотвращения случайного завершения процесса.
    Алиасы: -ProtectClose, -NoClose.

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
    .\tc.ps1 -DisableCloseButton
    .\tc.ps1 --help
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'sensorsonly')]
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

    [Alias('Tray', 'SystemTray', 'tray_mode')]
    [Nullable[bool]]$EnableTray = $null,

    [Alias('ProtectClose', 'NoClose')]
    [switch]$DisableCloseButton,

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
    Write-Host "  .\tc.ps1 [sensorsonly|start|stop|restart|status] [-ConfigFile <config_tc.json>] [-NewWindow] [-Background] [-NoBrowser]"
    Write-Host "  .\tc.ps1 -Interactive"
    Write-Host "  .\tc.ps1 --help"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\tc.ps1                               # Запуск приложений по config_tc.json"
    Write-Host "  .\tc.ps1 sensorsonly                   # Запуск только сенсоров и автологгирования"
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
# STAGE 2 — ЗАГРУЗКА КОНФИГУРАЦИИ (config_tc.json)
# ============================================================================
$activeConfigFile = "config_tc.json"
if ($ConfigFile -and (Test-Path (Join-Path $scriptDir $ConfigFile))) {
    $activeConfigFile = $ConfigFile
} elseif (Test-Path (Join-Path $scriptDir "config_tc.json")) {
    $activeConfigFile = "config_tc.json"
} elseif (Test-Path (Join-Path $scriptDir "config_ts.json")) {
    $activeConfigFile = "config_ts.json"
} elseif (Test-Path (Join-Path $scriptDir "config.json")) {
    $activeConfigFile = "config.json"
}

$cfgPath = Join-Path $scriptDir $activeConfigFile
$env:CONFIG_FILE = $activeConfigFile
$env:AIBREADBOARD_CONFIG = $activeConfigFile
# Set environment variables for Python AI models
$env:AIBREADBOARD_CONFIG = $activeConfigFile
$env:CONFIG_FILE = $activeConfigFile
$env:AI_PROVIDER = $aiProvider
$env:AI_GEMINI_MODEL = $aiGeminiModel
$env:AI_GEMINI_CLI_MODEL = $aiGeminiCliModel
$env:AI_AGY_MODEL = $aiAgyModel
$env:AI_AGY_EFFORT = $aiAgyEffort
Write-Host "  [OK] Переменные окружения для AI модели установлены:" -ForegroundColor Cyan
Write-Host "    AI_PROVIDER: $aiProvider" -ForegroundColor DarkGray
Write-Host "    AI_GEMINI_MODEL: $aiGeminiModel" -ForegroundColor DarkGray
Write-Host "    AI_GEMINI_CLI_MODEL: $aiGeminiCliModel" -ForegroundColor DarkGray
Write-Host "    AI_AGY_MODEL: $aiAgyModel" -ForegroundColor DarkGray
Write-Host "    AI_AGY_EFFORT: $aiAgyEffort" -ForegroundColor DarkGray
$envFile = Join-Path $scriptDir ".env"
$cfgHost = "127.0.0.1"
$cfgPort = "8000"
$useSsl  = $false
$cfgApps = $null
$enableTrayVal = $true

# AI configuration
$aiProvider = "gemini"
$aiGeminiModel = "gemini-2.5-flash"
$aiGeminiCliModel = "gemini-3.1-flash-lite"
$aiAgyModel = "gemini-3.6-flash"
$aiAgyEffort = "medium"

# Set environment variables for Python AI models
$env:AIBREADBOARD_CONFIG = $activeConfigFile
$env:CONFIG_FILE = $activeConfigFile
$env:AI_PROVIDER = $aiProvider
$env:AI_GEMINI_MODEL = $aiGeminiModel
$env:AI_GEMINI_CLI_MODEL = $aiGeminiCliModel
$env:AI_AGY_MODEL = $aiAgyModel
$env:AI_AGY_EFFORT = $aiAgyEffort

Write-Host "  [OK] Переменные окружения для AI модели установлены:" -ForegroundColor Cyan
Write-Host "    AI_PROVIDER: $aiProvider" -ForegroundColor DarkGray
Write-Host "    AI_GEMINI_MODEL: $aiGeminiModel" -ForegroundColor DarkGray
Write-Host "    AI_GEMINI_CLI_MODEL: $aiGeminiCliModel" -ForegroundColor DarkGray
Write-Host "    AI_AGY_MODEL: $aiAgyModel" -ForegroundColor DarkGray
Write-Host "    AI_AGY_EFFORT: $aiAgyEffort" -ForegroundColor DarkGray

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
            if ($cfg.server.enable_tray -ne $null) {
                $enableTrayVal = [bool]$cfg.server.enable_tray
            }
        }
        if ($cfg.ai) {
            # Load AI configuration from config_tc.json format
            if ($cfg.ai.provider) {
                $aiProvider = [string]$cfg.ai.provider
            }
            if ($cfg.ai.gemini) {
                if ($cfg.ai.gemini.model) {
                    $aiGeminiModel = [string]$cfg.ai.gemini.model
                }
            }
            if ($cfg.ai.gemini_cli) {
                if ($cfg.ai.gemini_cli.model) {
                    $aiGeminiCliModel = [string]$cfg.ai.gemini_cli.model
                }
            }
            if ($cfg.ai.agy) {
                if ($cfg.ai.agy.model) {
                    $aiAgyModel = [string]$cfg.ai.agy.model
                }
                if ($cfg.ai.agy.effort) {
                    $aiAgyEffort = [string]$cfg.ai.agy.effort
                }
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
            if ($key -eq "ENABLE_TRAY") { $enableTrayVal = $val -in ("true","1","yes") }
        }
    }
}

if ($EnableTray -ne $null) {
    $enableTrayVal = [bool]$EnableTray
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
# STAGE 5 — ОБРАБОТКА ДЕЙСТВИЯ (STATUS, STOP, RESTART, START, SENSORSONLY)
# ============================================================================

# Если действие sensorsonly, запускаем только сенсоры
if ($Action -eq 'sensorsonly') {
    $sensorsLauncher = Join-Path $scriptDir "launchers\Run-AI-Sensors.ps1"
    if (-not (Test-Path $sensorsLauncher)) {
        $sensorsLauncher = Join-Path $scriptDir "Run-AI-Sensors.ps1"
    }
    
    if (Test-Path $sensorsLauncher) {
        Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
        Write-Host "🚀 ЗАПУСК AI-SENSORS ТЕЛЕМЕТРИИ" -ForegroundColor Cyan
        Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
        & $sensorsLauncher -Action start -Interval 60.0
        exit 0
    } else {
        Write-Host "[ERROR] Run-AI-Sensors.ps1 не найден: $sensorsLauncher" -ForegroundColor Red
        exit 1
    }
}

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
            "--start-maximized"
        )
        Start-Process -FilePath $edgeExe -ArgumentList ($edgeArgs -join " ") -WindowStyle Maximized
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

# 1.1 Запуск LibreHardwareMonitor в скрытом фоновом режиме для сбора аппаратных метрик
$lhmLauncher = Join-Path $scriptDir "launchers\Run-LHM.ps1"
if (-not (Test-Path $lhmLauncher)) {
    $lhmLauncher = Join-Path $scriptDir "Run-LHM.ps1"
}
if (Test-Path $lhmLauncher) {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    & $lhmLauncher -Action $Action
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
    # Инициализация системного трея (ShowHide-InTray.ps1)
    if ($enableTrayVal) {
        Write-Host ""
        Write-Host "    Инициализация системного трея (ShowHide-InTray.ps1)..." -ForegroundColor Cyan
        $trayScript = Join-Path $scriptDir "launchers\ShowHide-InTray.ps1"
        if (-not (Test-Path $trayScript)) {
            $trayScript = Join-Path $scriptDir "ShowHide-InTray.ps1"
        }
        if (Test-Path $trayScript) {
            try {
                $trayCallArgs = @{
                    Action = 'start'
                    WebUrl = $appsUrl
                    Title  = "AI Breadboard - Test Computer (/tc)"
                }
                if ($DisableCloseButton) {
                    $trayCallArgs['DisableCloseButton'] = $true
                }
                & $trayScript @trayCallArgs
            } catch {
                Write-Host "    [WARN] Не удалось инициализировать системный трей: $_" -ForegroundColor Yellow
            }
        } else {
            Write-Host "    [WARN] ShowHide-InTray.ps1 не найден: $trayScript" -ForegroundColor Yellow
        }
    }

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
