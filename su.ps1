<#
.SYNOPSIS
    Standalone applications launcher for AI Breadboard SU console (su.ps1).

.DESCRIPTION
    Launches only the SU console applications block configured in su.json:
    - Dedicated SU web interface
    - Configured SU microservices (Chat, Admin Panel, User Assistant)

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER NewWindow
    Launch microservices in visible standalone console windows (default: $true).

.PARAMETER Background
    Launch microservices in background processes without opening visible windows.

.PARAMETER ConfigFile
    Custom configuration JSON file name (default: su.json).

.PARAMETER Port
    Override server bind port (default: from su.json or 8080).

.PARAMETER HostAddress
    Override server bind address (default: from su.json or 127.0.0.1).

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
    .\su.ps1
    .\su.ps1 -Action status
    .\su.ps1 -Action stop
    .\su.ps1 -Action restart
    .\su.ps1 -ConfigFile su.json
    .\su.ps1 -Background
    .\su.ps1 -Interactive
    .\su.ps1 -DisableCloseButton
    .\su.ps1 --help
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
    [string]$ConfigFile = 'su.json',

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
    Write-Host "║            su.ps1 — ЛОНЧЕР БЛОКА ПРИЛОЖЕНИЙ                   ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Запуск ТОЛЬКО блока приложений и автономных микросервисов из /apps,"
    Write-Host "  настроенных в su.json:"
    Write-Host "  • Веб-интерфейс приложений       (/apps)" -ForegroundColor White
    Write-Host "  • Настройки запуска приложений   (su.json)" -ForegroundColor White
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\su.ps1 [start|stop|restart|status] [-ConfigFile <su.json>] [-NewWindow] [-Background] [-NoBrowser]"
    Write-Host "  .\su.ps1 -Interactive"
    Write-Host "  .\su.ps1 --help"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\su.ps1                               # Запуск приложений по su.json"
    Write-Host "  .\su.ps1 -Action status                # Проверка статуса работы всех микросервисов"
    Write-Host "  .\su.ps1 -ConfigFile su.json           # Явное указание файла конфигурации"
    Write-Host "  .\su.ps1 -Action stop                  # Остановка сервисов"
    Write-Host "  .\su.ps1 -Action restart               # Перезапуск сервисов"
    Write-Host "  .\su.ps1 -Background                   # Фоновый запуск без открытия окон"
    Write-Host "  .\su.ps1 -Interactive                  # Интерактивное меню управления"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║            AI BREADBOARD — ЗАПУСК SU БЛОКА                    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STAGE 2 — ЗАГРУЗКА КОНФИГУРАЦИИ (su.json)
# ============================================================================
# AI configuration - defaults before reading config
$aiProvider = "gemini"
$aiGeminiModel = "gemini-2.5-flash"
$aiGeminiCliModel = "gemini-3.1-flash-lite"
$aiAgyModel = "gemini-3.6-flash"
$aiAgyEffort = "medium"

$activeConfigFile = "start_scenarios_config/su.json"
if ($ConfigFile -and (Test-Path (Join-Path $scriptDir $ConfigFile))) {
    $activeConfigFile = $ConfigFile
} elseif (Test-Path (Join-Path $scriptDir "start_scenarios_config\su.json")) {
    $activeConfigFile = "start_scenarios_config\su.json"
} elseif (Test-Path (Join-Path $scriptDir "su.json")) {
    $activeConfigFile = "su.json"
} elseif (Test-Path (Join-Path $scriptDir "config\su.json")) {
    $activeConfigFile = "config\su.json"
} elseif (Test-Path (Join-Path $scriptDir "config.json")) {
    $activeConfigFile = "config.json"
} elseif (Test-Path (Join-Path $scriptDir "config\config.json")) {
    $activeConfigFile = "config\config.json"
} elseif (Test-Path (Join-Path $scriptDir "config_tc.json")) {
    $activeConfigFile = "config_tc.json"
}

$cfgPath = Join-Path $scriptDir $activeConfigFile
$envFile = Join-Path $scriptDir ".env"
$cfgHost = "127.0.0.1"
$cfgPort = "8080"
$useSsl  = $true
$cfgApps = $null
$enableTrayVal = $true

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
            # Поддержка новой структуры: ai.providers.<provider>.model
            if ($cfg.ai.providers) {
                foreach ($provName in @('gemini', 'gemini_cli', 'agy', 'ollama', 'foundry')) {
                    $prov = $cfg.ai.providers.$provName
                    if ($prov -and $prov.enabled -eq $true -and -not $aiProvider) {
                        $aiProvider = $provName
                    }
                    if ($prov -and $prov.model) {
                        switch ($provName) {
                            'gemini'     { $aiGeminiModel    = [string]$prov.model }
                            'gemini_cli' { $aiGeminiCliModel = [string]$prov.model }
                            'agy'        { $aiAgyModel       = [string]$prov.model; if ($prov.effort) { $aiAgyEffort = [string]$prov.effort } }
                        }
                    }
                }
            }
            # Поддержка старой структуры (обратная совместимость)
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

# Set environment variables AFTER reading config (so AI config values are correct)
$env:CONFIG_FILE = $activeConfigFile
$env:AIBREADBOARD_CONFIG = $activeConfigFile
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

$host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
$port_ = if ($Port) { [string]$Port } else { [string]$cfgPort }
$proto = if ($useSsl) { "https" } else { "http" }
$browserHost = if ($host_ -eq "0.0.0.0") { "localhost" } else { $host_ }
$appsUrl = "${proto}://${browserHost}:${port_}/su"

# ============================================================================
# STAGE 3 — ИНТЕРАКТИВНЫЙ РЕЖИМ (ЕСЛИ -Interactive)
# ============================================================================
$isInteractive = $Interactive -and (-not $NonInteractive)

if ($isInteractive) {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host " 📱 УПРАВЛЕНИЕ МИКРОСЕРВИСАМИ И ВЕБ-ИНТЕРФЕЙСОМ /su" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "  [1] Start   - Запустить приложения и открыть веб-интерфейс /su" -ForegroundColor White
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
    $appDataDir = $env:APPDATA
    if (-not $appDataDir) {
        $appDataDir = Join-Path $env:USERPROFILE "AppData\Roaming"
    }
    $profileDir = Join-Path $appDataDir "AI-Breadboard\browser_profile"

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

# 1. Проверяем и запускаем микросервисы через Run-Apps.ps1 с учетом admin.json
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
        Write-Host "   Для запуска выполните: .\su.ps1" -ForegroundColor DarkGray
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
                    Title  = "AI Breadboard - SU Console (/su)"
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
