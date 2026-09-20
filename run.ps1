<#
.SYNOPSIS
    Главный лончер проекта ai-breadboard. Запускает FastAPI-сервер и сопутствующие сервисы.

.DESCRIPTION
    Загружает конфигурацию из config.json и .env,
    в интерактивном режиме запрашивает адрес хоста (0.0.0.0, 127.0.0.1 или свой IP),
    порт и параметры сопутствующих сервисов (Foundry),
    освобождает порт и запускает FastAPI-сервер через Run-Unicorn.ps1.

.PARAMETER HostAddress
    IP-адрес или хост для привязки сервера (например: 0.0.0.0, 127.0.0.1, localhost).
    Алиасы параметра: -Host, -Address, -IP, -Host_.
    При явной передаче интерактивный запрос адреса пропускается.

.PARAMETER Port
    TCP-порт для запуска сервера (по умолчанию: из config.json или 8000).

.PARAMETER Interactive
    Запуск в интерактивном диалоговом режиме с вопросами пользователю (по умолчанию выключен).

.PARAMETER Cloudflared
    Включить туннель Cloudflare Tunnel (cloudflared). По умолчанию выключен ($false).

.PARAMETER EnableOAuth
    Включить авторизацию через Google OAuth. По умолчанию выключен ($false).
    Алиасы: -OAuth.

.PARAMETER EnableTelegramBot
    Включить запуск Telegram-бота. По умолчанию включен ($true).
    Алиасы: -Telegram, -EnableTelegram, -TelegramBot, -tg.

.PARAMETER EnableAssist
    Включить запуск терминала с ассистентом assist.ps1. По умолчанию выключен ($false).
    Алиасы: -Assist, -enable_assist.

.PARAMETER Help
    Отображение справки по использованию лончера (-Help, -h, --help).

.EXAMPLE
    .\run.ps1
    .\run.ps1 -EnableOAuth
    .\run.ps1 -EnableTelegramBot
    .\run.ps1 -Cloudflared
    .\run.ps1 -Interactive
    .\run.ps1 -Host 0.0.0.0
    .\run.ps1 -Host 127.0.0.1 -Port 8000
    .\run.ps1 --help
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [Alias('Host', 'Address', 'IP', 'Host_')]
    [string]$HostAddress,

    [Parameter(Position = 1)]
    [string]$Port,

    [Alias('i')]
    [switch]$Interactive,

    [switch]$NonInteractive,

    [Alias('Tunnel', 'cf')]
    [switch]$Cloudflared,

    [Alias('OAuth')]
    [Nullable[bool]]$EnableOAuth = $null,

    [Alias('Telegram', 'EnableTelegram', 'TelegramBot', 'tg')]
    [Nullable[bool]]$EnableTelegramBot = $null,

    [Alias('Assist', 'enable_assist')]
    [Nullable[bool]]$EnableAssist = $null,

    [Alias('Apps', 'enable_apps')]
    [Nullable[bool]]$EnableApps = $null,

    [Alias('WindowsAdmin', 'sysadmin')]
    [Nullable[bool]]$EnableWindowsAdmin = $null,

    [Alias('NetworkTerminal', 'netterm')]
    [Nullable[bool]]$EnableNetworkTerminal = $null,

    [Alias('SystemInspector', 'sysinspect')]
    [Nullable[bool]]$EnableSystemInspector = $null,

    [Alias('TradingTerminal', 'trading')]
    [Nullable[bool]]$EnableTradingTerminal = $null,

    [Alias('CloudflaredMonitor', 'cfmon')]
    [Nullable[bool]]$EnableCloudflaredMonitor = $null,

    [Alias('GCloudMonitor', 'gcloud')]
    [Nullable[bool]]$EnableGCloudMonitor = $null,

    [Alias('WebsiteMonitor', 'webmon')]
    [Nullable[bool]]$EnableWebsiteMonitor = $null,

    [Alias('SystemLogViewer', 'syslogs', 'logs_viewer')]
    [Nullable[bool]]$EnableSystemLogViewer = $null,

    [Alias('SystemControlCenter', 'syscontrol', 'control_center')]
    [Nullable[bool]]$EnableSystemControlCenter = $null,

    [Alias('WikipediaResearch', 'wiki_lab', 'wikipedia')]
    [Nullable[bool]]$EnableWikipediaResearch = $null,

    [Alias('UserAssistant', 'assistant')]
    [Nullable[bool]]$EnableUserAssistant = $null,

    [Alias('AIBreadboardAdmin', 'admin_app')]
    [Nullable[bool]]$EnableAIBreadboardAdmin = $null,

    [Alias('ResearchAndStatistic', 'research_stat')]
    [Nullable[bool]]$EnableResearchAndStatistic = $null,

    [Alias('Helpdesk', 'it_support')]
    [Nullable[bool]]$EnableHelpdesk = $null,

    [Alias('Tray', 'tray_mode', 'SystemTray')]
    [Nullable[bool]]$EnableTray = $null,

    # [Alias('TestComputer', 'tc', 'apps_mode')]
    # [switch]$TestComputer,

    [Alias('Config', 'Cfg')]
    [string]$ConfigFile,

    [Alias('Worker', 'UnicornWorkers', 'unicorn_workers')]
    [Nullable[int]]$Workers = $null,

    [Alias('Autoreload', 'UnicornReload', 'unicorn_reload')]
    [Nullable[bool]]$Reload = $null,

    [Alias('SkipUpdate', 'NoUpdate')]
    [switch]$SkipUpdateCheck,

    [Alias('h', '-help', '?')]
    [switch]$Help
)

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

$env:PYTHONUTF8 = "1"
$env:AIBREADBOARD_DIR = $scriptDir
$env:ASSIST_DIR = $scriptDir
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Get-AppServerMode {
    <#
    .SYNOPSIS
        Определяет режим сервера аппликации (dedicated / shared) из src/apps/<name>/config.json или apps/<name>/config.json.
    #>
    param (
        [string]$AppName,
        [string]$BaseDir = $scriptDir
    )
    $candidatePaths = @(
        (Join-Path $BaseDir "src\apps\$AppName\config.json"),
        (Join-Path $BaseDir "apps\$AppName\config.json")
    )
    foreach ($path in $candidatePaths) {
        if (Test-Path $path) {
            try {
                $raw = Get-Content $path -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($raw.server) {
                    if ($raw.server.PSObject.Properties['dedicated'] -ne $null) {
                        if ($raw.server.dedicated -eq $true -or $raw.server.dedicated -eq 'true') {
                            return "dedicated"
                        } else {
                            return "shared"
                        }
                    }
                    if ($raw.server -is [string]) {
                        return $raw.server.Trim().ToLower()
                    }
                    if ($raw.server.mode) {
                        return $raw.server.mode.ToString().Trim().ToLower()
                    }
                    if ($raw.server.type) {
                        return $raw.server.type.ToString().Trim().ToLower()
                    }
                }
            } catch {
                # Fallback to dedicated on parse error
            }
        }
    }
    return "dedicated"
}

# ============================================================================
# STAGE 1 — ОБРАБОТКА ПАРАМЕТРОВ И СПРАВКИ
# ----------------------------------------------------------------------------
# Проверяется запрос справки. Если справка запрошена, отображается описание
# лончера, доступные параметры и примеры запуска, после чего выполнение
# завершается без запуска сервисов.
# ============================================================================
if ($HostAddress -in @('-h', '--help', '-help', '/?', '-?')) {
    $Help = $true
    $HostAddress = $null
}

if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║              run.ps1 — СПРАВКА И ПАРАМЕТРЫ                    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Главный лончер проекта ai-breadboard."
    Write-Host "  По умолчанию запускается автоматически без лишних вопросов (значения по умолчанию)."
    Write-Host "  Запускает FastAPI-сервер и сопутствующие сервисы (Foundry, Cloudflare Tunnel)."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\run.ps1"
    Write-Host "  .\run.ps1 [-Cloudflared] [-Interactive] [-Host <хост>] [-Port <порт>]"
    Write-Host "  .\run.ps1 --help"
    Write-Host ""
    Write-Host "ПАРАМЕТРЫ:" -ForegroundColor Yellow
    Write-Host "  -Host, -Address, -IP  IP-адрес привязки (0.0.0.0, 127.0.0.1, localhost)."
    Write-Host "  -Port <string>        Порт сервера (по умолчанию: из config.json или 8000)."
    Write-Host "  -Interactive, -i      Включить интерактивный режим (диалоговые вопросы)."
    Write-Host "  -NonInteractive       Неинтерактивный режим (включен по умолчанию)."
    Write-Host "  -Cloudflared, -cf     Включить туннель Cloudflare Tunnel (по умолчанию выключен)."
    Write-Host "  -EnableOAuth, -OAuth  Включить авторизацию через Google OAuth (по умолчанию включена)."
    Write-Host "  -EnableTelegramBot    Включить запуск Telegram-бота (по умолчанию включен, алиас: -tg)."
    Write-Host "  -EnableApps           Включить все микросервисы из /apps (порты 8100-8104)."
    Write-Host "  -EnableWindowsAdmin   Запустить Windows System Administrator (порт 8100)."
    Write-Host "  -EnableNetworkTerminal Запустить Network Analyzer Terminal (порт 8101)."
    Write-Host "  -EnableSystemInspector Запустить System Inspector (порт 8102)."
    Write-Host "  -EnableTradingTerminal Запустить Trading Terminal (порт 8103)."
    Write-Host "  -EnableCloudflaredMonitor Запустить Cloudflared Monitor (порт 8104)."
    Write-Host "  -EnableAssist, -Assist Включить терминал с assist.ps1 (по умолчанию выключен, алиас: -enable_assist)."
    Write-Host "  -SkipUpdateCheck      Пропустить предварительную проверку обновлений."
    Write-Host "  -Help, -h, --help     Показать эту справку и выйти."
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\run.ps1"
    Write-Host "  .\run.ps1 -EnableTelegramBot"
    Write-Host "  .\run.ps1 -Cloudflared"
    Write-Host "  .\run.ps1 -Interactive"
    Write-Host "  .\run.ps1 -Host 0.0.0.0"
    Write-Host "  .\run.ps1 -Host 127.0.0.1 -Port 8000"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              ЗАПУСК FastAPI СЕРВЕРА (ai-breadboard)           ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STAGE 1.5 — ПРОВЕРКА ВЕРСИИ И ОБНОВЛЕНИЙ
# ----------------------------------------------------------------------------
# Проверяется наличие новой версии в Git-репозитории.
# Если обнаружена новая версия, пользователю предлагается обновиться y/[N].
# ============================================================================
if (-not $SkipUpdateCheck) {
    Write-Host "[0/3] Проверка версии приложения..." -ForegroundColor Cyan
    if (Get-Command git -ErrorAction SilentlyContinue) {
        try {
            $localCommit = git rev-parse --short HEAD 2>$null
            $currentTag  = git describe --tags --always 2>$null

            # Быстрый запрос HEAD из удаленного репозитория
            $remoteHead = git ls-remote origin HEAD 2>$null
            if ($remoteHead) {
                $remoteCommit = ($remoteHead -split '\s+')[0]
                if ($remoteCommit.Length -ge 7) {
                    $remoteCommit = $remoteCommit.Substring(0, 7)
                }

                if ($localCommit -and $remoteCommit -and ($localCommit -ne $remoteCommit)) {
                    Write-Host ""
                    Write-Host "┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
                    Write-Host " 🚀 ДОСТУПНА НОВАЯ ВЕРСИЯ AI-BREADBOARD                       " -ForegroundColor Yellow
                    Write-Host "    Текущая версия: $currentTag ($localCommit)" -ForegroundColor White
                    Write-Host "    Новая версия:   $remoteCommit" -ForegroundColor Green
                    Write-Host "└─────────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
                    Write-Host ""

                    if (-not $NonInteractive) {
                        $updateChoice = Read-Host "Обновить приложение сейчас? (y/N) [Enter = n]"
                        $updateChoice = $updateChoice.Trim().ToLower()
                        if ($updateChoice -in @("y", "yes", "д", "да", "1")) {
                            Write-Host "    Загрузка и применение обновлений (git pull)..." -ForegroundColor Cyan
                            $gitPullOut = git pull origin 2>&1
                            if ($LASTEXITCODE -eq 0) {
                                Write-Host "    [OK] Приложение успешно обновлено!" -ForegroundColor Green
                                
                                # Автоматическое обновление структуры баз данных
                                Write-Host "    Проверка и применение миграций баз данных..." -ForegroundColor Cyan
                                $venvPy = Join-Path $scriptDir "venv\Scripts\python.exe"
                                $pyExec = if (Test-Path $venvPy) { $venvPy } else { "python" }
                                $migOut = & $pyExec -m src.db.migrations --apply 2>&1
                                if ($LASTEXITCODE -eq 0) {
                                    Write-Host "    [OK] Базы данных актуализированы." -ForegroundColor Green
                                } else {
                                    Write-Host "    [WARN] Ошибка применения миграций БД: $migOut" -ForegroundColor Yellow
                                }
                            } else {
                                Write-Host "    [WARN] Ошибка при обновлении: $gitPullOut" -ForegroundColor Yellow
                            }
                        } else {
                            Write-Host "    Обновление пропущено пользователем." -ForegroundColor DarkGray
                        }
                    }
                } else {
                    Write-Host "    [OK] Версия актуальна ($currentTag)" -ForegroundColor Green
                }
            } else {
                Write-Host "    [INFO] Текущая версия: $currentTag (удаленный репозиторий недоступен)" -ForegroundColor DarkGray
            }
        } catch {
            Write-Host "    [WARN] Ошибка при проверке версии: $_" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "    [INFO] Git не найден, проверка версии пропущена." -ForegroundColor DarkGray
    }
}

# ============================================================================
# STAGE 2 — ЗАГРУЗКА КОНФИГУРАЦИИ И ОКРУЖЕНИЯ
# ----------------------------------------------------------------------------
# Загружаются базовые параметры из config.json и значения, переопределяющие
# их из .env. Одновременно определяются параметры SSL, Foundry и предварительной
# загрузки Silero. В конце этапа определяется локальный сетевой IP, который
# используется только для подсказки пользователю.
# ============================================================================
Write-Host ""
Write-Host "[1/3] Загрузка конфигурации..." -ForegroundColor Cyan
$activeConfigFile = "config.json"
if ($ConfigFile -and (Test-Path (Join-Path $scriptDir $ConfigFile))) {
    $activeConfigFile = $ConfigFile
} elseif ($TestComputer -and (Test-Path (Join-Path $scriptDir "config_tc.json"))) {
    $activeConfigFile = "config_tc.json"
} elseif ($env:AIBREADBOARD_CONFIG -and (Test-Path (Join-Path $scriptDir $env:AIBREADBOARD_CONFIG))) {
    $activeConfigFile = $env:AIBREADBOARD_CONFIG
} elseif ($env:CONFIG_FILE -and (Test-Path (Join-Path $scriptDir $env:CONFIG_FILE))) {
    $activeConfigFile = $env:CONFIG_FILE
}

$configPath = Join-Path $scriptDir $activeConfigFile
$env:CONFIG_FILE = $activeConfigFile
$env:AIBREADBOARD_CONFIG = $activeConfigFile
$envFile = Join-Path $scriptDir ".env"
$cfgHost = "0.0.0.0"
$cfgPort = "8000"
$useSsl = $false
$useFoundry = $false
$useOllama = $false
$useCloudflared = $true
$enableOAuthVal = $true
$enableTelegramBotVal = $true
$enableAppsVal = $false
$enableWindowsAdminVal = $false
$enableNetworkTerminalVal = $false
$enableSystemInspectorVal = $false
$enableTradingTerminalVal = $false
$enableCloudflaredMonitorVal = $false
$enableAssistVal = $false
$enableTrayVal = $true
$preloadSilero = $false
$clientUrl = $null

$cfgAppsEnabled = @()
$cfgAppsDisabled = @()
$hasAppsEnabledList = $false
$hasAppsDisabledList = $false
$cfgAppsObj = $null

function Get-IsAppConfigEnabled {
    param(
        [string]$AppKey,
        [string]$AppFolder,
        [string[]]$Aliases = @()
    )
    $allAliases = @($AppKey.ToLower(), $AppFolder.ToLower())
    foreach ($al in $Aliases) {
        if ($al) { $allAliases += $al.ToLower() }
    }

    # 1. Проверка явного отключения в disabled
    foreach ($al in $allAliases) {
        if ($cfgAppsDisabled -contains $al) {
            return $false
        }
    }

    # 2. Проверка включения в список enabled
    if ($hasAppsEnabledList) {
        foreach ($al in $allAliases) {
            if ($cfgAppsEnabled -contains $al) {
                return $true
            }
        }
        return $false
    }

    # 3. Проверка индивидуального булева флага в словаре
    if ($cfgAppsObj) {
        if ($cfgAppsObj.PSObject.Properties[$AppKey] -ne $null) {
            return [bool]$cfgAppsObj.$AppKey
        }
        if ($cfgAppsObj.PSObject.Properties[$AppFolder] -ne $null) {
            return [bool]$cfgAppsObj.$AppFolder
        }
    }

    return [bool]$enableAppsVal
}

if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath | ConvertFrom-Json
        if ($cfg.server.host) { $cfgHost = [string]$cfg.server.host }
        if ($cfg.server.port) { $cfgPort = [string]$cfg.server.port }
        if ($cfg.server.protocol) {
            $useSsl = ([string]$cfg.server.protocol.ToString().ToLower() -eq "https")
        } elseif ($cfg.server.use_ssl -ne $null) {
            $useSsl = [bool]$cfg.server.use_ssl
        }
        if ($cfg.server.enable_oauth -ne $null) { $enableOAuthVal = [bool]$cfg.server.enable_oauth }
        if ($cfg.server.enable_telegram_bot -ne $null) { $enableTelegramBotVal = [bool]$cfg.server.enable_telegram_bot }
        if ($cfg.server.enable_apps -ne $null) { $enableAppsVal = [bool]$cfg.server.enable_apps }
        if ($cfg.apps) {
            $cfgAppsObj = $cfg.apps
            $isAppsArray = ($cfg.apps -is [System.Collections.IEnumerable]) -and ($cfg.apps -isnot [string]) -and ($cfg.apps.PSObject.Properties['enable_all'] -eq $null) -and ($cfg.apps.PSObject.Properties['enabled'] -eq $null)
            $hasEnabledProp = ($cfg.apps.PSObject.Properties['enabled'] -ne $null -and ($cfg.apps.enabled -is [System.Collections.IEnumerable]))
            $hasDisabledProp = ($cfg.apps.PSObject.Properties['disabled'] -ne $null -and ($cfg.apps.disabled -is [System.Collections.IEnumerable]))

            if ($isAppsArray) {
                $hasAppsEnabledList = $true
                foreach ($item in $cfg.apps) {
                    if ($item) { $cfgAppsEnabled += $item.ToString().Trim().ToLower() }
                }
            } elseif ($hasEnabledProp) {
                $hasAppsEnabledList = $true
                foreach ($item in $cfg.apps.enabled) {
                    if ($item) { $cfgAppsEnabled += $item.ToString().Trim().ToLower() }
                }
            }

            if ($hasDisabledProp) {
                $hasAppsDisabledList = $true
                foreach ($item in $cfg.apps.disabled) {
                    if ($item) { $cfgAppsDisabled += $item.ToString().Trim().ToLower() }
                }
            }

            if ($isAppsArray -or $hasEnabledProp) {
                $enableAppsVal = $false
            } elseif ($cfg.apps.enable_all -ne $null) {
                $enableAppsVal = [bool]$cfg.apps.enable_all
            }
            if ($cfg.apps.enable_windows_admin -ne $null) { $enableWindowsAdminVal = [bool]$cfg.apps.enable_windows_admin }
            if ($cfg.apps.enable_network_terminal -ne $null) { $enableNetworkTerminalVal = [bool]$cfg.apps.enable_network_terminal }
            if ($cfg.apps.enable_system_inspector -ne $null) { $enableSystemInspectorVal = [bool]$cfg.apps.enable_system_inspector }
            if ($cfg.apps.enable_trading_terminal -ne $null) { $enableTradingTerminalVal = [bool]$cfg.apps.enable_trading_terminal }
            if ($cfg.apps.enable_cloudflared_monitor -ne $null) { $enableCloudflaredMonitorVal = [bool]$cfg.apps.enable_cloudflared_monitor }
        }
        if ($cfg.server.enable_assist -ne $null) { $enableAssistVal = [bool]$cfg.server.enable_assist }
        if ($cfg.server.auto_start_assist_cli -ne $null) { $enableAssistVal = [bool]$cfg.server.auto_start_assist_cli }
        if ($cfg.server.enable_tray -ne $null) { $enableTrayVal = [bool]$cfg.server.enable_tray }
        if ($cfg.server.client_url) { $clientUrl = [string]$cfg.server.client_url }
        elseif ($cfg.server.user_domain) { $clientUrl = "https://$($cfg.server.user_domain)" }
        if ($cfg.ai.use_foundry -ne $null) { $useFoundry = [bool]$cfg.ai.use_foundry }
        if ($cfg.ai.use_ollama -ne $null) { $useOllama = [bool]$cfg.ai.use_ollama }
        if ($cfg.server.use_cloudflared -ne $null) { $useCloudflared = [bool]$cfg.server.use_cloudflared }
        if ($cfg.ai.preload_silero -ne $null) { $preloadSilero = [bool]$cfg.ai.preload_silero }
        Write-Host "    [OK] Конфигурация config.json загружена" -ForegroundColor Green
    } catch {
        Write-Host "    [ERROR] Ошибка чтения конфигурации: $_" -ForegroundColor Red
    }
} else {
    Write-Host "    [WARN] Файл конфигурации не найден: $configPath" -ForegroundColor Yellow
}

# Значения из .env используются для переопределения соответствующих параметров.
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "PROTOCOL") { $useSsl = ($val.ToLower() -eq "https") }
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
            if ($key -eq "ENABLE_OAUTH") { $enableOAuthVal = $val -in ("true","1","yes") }
            if ($key -eq "ENABLE_TELEGRAM_BOT") { $enableTelegramBotVal = $val -in ("true","1","yes") }
            if ($key -eq "ENABLE_ASSIST") { $enableAssistVal = $val -in ("true","1","yes") }
            if ($key -eq "AUTO_START_ASSIST_CLI") { $enableAssistVal = $val -in ("true","1","yes") }
            if ($key -eq "ENABLE_TRAY") { $enableTrayVal = $val -in ("true","1","yes") }
            if ($key -eq "USE_FOUNDRY") { $useFoundry = $val -in ("true","1","yes") }
            if ($key -eq "USE_OLLAMA") { $useOllama = $val -in ("true","1","yes") }
            if ($key -eq "USE_CLOUDFLARED") { $useCloudflared = $val -in ("true","1","yes") }
            if ($key -eq "CLOUDFLARE_TUNNEL_TOKEN") { $cfTunnelToken = $val }
            if ($key -eq "CLIENT_URL" -and $val) { $clientUrl = $val }
            if ($key -eq "USER_DOMAIN" -and $val -and -not $clientUrl) { $clientUrl = "https://$val" }
            if ($key -eq "AUTO_LAUNCH_ENABLED") { $autoLaunchEnabled = $val -in ("true","1","yes") }
            if ($key -eq "AUTO_LAUNCH_DELAY_SECONDS" -and $val -match '^\d+$') { $autoLaunchDelay = [int]$val }
        }
    }
}

# Если передан явный CLI-параметр -Cloudflared, он принудительно включает туннель
if ($Cloudflared) {
    $useCloudflared = $true
}

# Если передан явный CLI-параметр -EnableOAuth, он переопределяет значение
if ($EnableOAuth -ne $null) {
    $enableOAuthVal = [bool]$EnableOAuth
}

# Если передан явный CLI-параметр -EnableTelegramBot, он переопределяет значение
if ($EnableTelegramBot -ne $null) {
    $enableTelegramBotVal = [bool]$EnableTelegramBot
}

# Если передан явный CLI-параметр -EnableAssist, он переопределяет значение
if ($EnableAssist -ne $null) {
    $enableAssistVal = [bool]$EnableAssist
}

# Если переданы явные CLI-параметры для аппликаций
if ($EnableApps -ne $null) {
    $enableAppsVal = [bool]$EnableApps
}
if ($EnableWindowsAdmin -ne $null) {
    $enableWindowsAdminVal = [bool]$EnableWindowsAdmin
}
if ($EnableNetworkTerminal -ne $null) {
    $enableNetworkTerminalVal = [bool]$EnableNetworkTerminal
}
if ($EnableSystemInspector -ne $null) {
    $enableSystemInspectorVal = [bool]$EnableSystemInspector
}
if ($EnableTradingTerminal -ne $null) {
    $enableTradingTerminalVal = [bool]$EnableTradingTerminal
}
if ($EnableCloudflaredMonitor -ne $null) {
    $enableCloudflaredMonitorVal = [bool]$EnableCloudflaredMonitor
}
if ($EnableGCloudMonitor -ne $null) {
    $enableGCloudMonitorVal = [bool]$EnableGCloudMonitor
}
if ($EnableWebsiteMonitor -ne $null) {
    $enableWebsiteMonitorVal = [bool]$EnableWebsiteMonitor
}
if ($EnableSystemLogViewer -ne $null) {
    $enableSystemLogViewerVal = [bool]$EnableSystemLogViewer
}
if ($EnableSystemControlCenter -ne $null) {
    $enableSystemControlCenterVal = [bool]$EnableSystemControlCenter
}
if ($EnableWikipediaResearch -ne $null) {
    $enableWikipediaResearchVal = [bool]$EnableWikipediaResearch
}
if ($EnableUserAssistant -ne $null) {
    $enableUserAssistantVal = [bool]$EnableUserAssistant
}
if ($EnableAIBreadboardAdmin -ne $null) {
    $enableAIBreadboardAdminVal = [bool]$EnableAIBreadboardAdmin
}
if ($EnableResearchAndStatistic -ne $null) {
    $enableResearchAndStatisticVal = [bool]$EnableResearchAndStatistic
}
if ($EnableHelpdesk -ne $null) {
    $enableHelpdeskVal = [bool]$EnableHelpdesk
}

# Если передан явный CLI-параметр -EnableTray, он переопределяет значение
if ($EnableTray -ne $null) {
    $enableTrayVal = [bool]$EnableTray
}

# Определяется сетевой IPv4-адрес машины для отображения пользователю.
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notmatch '^(169\.254|127\.)' -and $_.InterfaceAlias -notmatch 'Loopback' } |
    Select-Object -ExpandProperty IPAddress -First 1)

# ============================================================================
# STAGE 3 — ВЫБОР ПАРАМЕТРОВ ЗАПУСКА
# ----------------------------------------------------------------------------
# Определяются конечные значения Host и Port. В интерактивном режиме
# пользователь может выбрать сетевой интерфейс, порт и необходимость запуска
# Microsoft AI Foundry. В неинтерактивном режиме используются переданные
# параметры или значения из config.json.
# ============================================================================
# Проверка переменных автозапуска
$autoLaunchEnabled = $env:AUTO_LAUNCH_ENABLED -in ("true","1","yes")
$autoLaunchDelay = 0
if ($env:AUTO_LAUNCH_DELAY_SECONDS -match '^\d+$') {
    $autoLaunchDelay = [int]$env:AUTO_LAUNCH_DELAY_SECONDS
}

# Если задержка задана в config.json, используем её
if (-not $autoLaunchEnabled -and $configPath -and (Test-Path $configPath)) {
    try {
        $cfg = Get-Content $configPath | ConvertFrom-Json
        if ($cfg.server.auto_launch -and $cfg.server.auto_launch.enabled -eq $true) {
            $autoLaunchEnabled = $true
            if ($cfg.server.auto_launch.delay_seconds -match '^\d+$') {
                $autoLaunchDelay = [int]$cfg.server.auto_launch.delay_seconds
            }
        }
    } catch {}
}

# Интерактивный режим включается только явно флагом -Interactive (-i)
$isInteractive = $Interactive -and (-not $NonInteractive) -and (-not $HostAddress)

# Если включён автозапуск и задержка > 0, показать предупреждение и подождать
if ($isInteractive -and $autoLaunchEnabled -and $autoLaunchDelay -gt 0) {
    Write-Host ""
    Write-Host "┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
    Write-Host " ⚠️  АВТОЗАПУСК САРВЕРА С ЗАДЕРЖКОЙ $autoLaunchDelay СЕК" -ForegroundColor Yellow
    Write-Host "    Используются параметры из config.json:" -ForegroundColor White
    Write-Host "    Хост: $cfgHost, Порт: $cfgPort" -ForegroundColor Gray
    Write-Host "    Нажмите Ctrl+C для отмены..." -ForegroundColor Yellow
    Write-Host "└─────────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
    Write-Host ""
    Start-Sleep -Seconds $autoLaunchDelay
}

if ($isInteractive -and -not $autoLaunchEnabled) {
    Write-Host ""
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host " 🌐 ИНТЕРАКТИВНЫЙ ВЫБОР АДРЕСА И ПОРТА" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "Выберите сетевой интерфейс для запуска сервера:" -ForegroundColor White
    Write-Host "  [1] 0.0.0.0   - Все сетевые интерфейсы (доступен с других ПК и телефонов)" -ForegroundColor White
    if ($lanIp) {
        Write-Host "                  (Ваш IP в локальной сети: $lanIp)" -ForegroundColor DarkGray
    }
    Write-Host "  [2] 127.0.0.1 - Только локально на этом ПК (localhost)" -ForegroundColor White
    Write-Host "  [3] Ввести произвольный IP / Hostname вручную" -ForegroundColor White
    Write-Host "  [Enter] По умолчанию из config.json: $cfgHost" -ForegroundColor Green
    Write-Host ""

    $hostChoice = Read-Host "Адрес / Вариант [Enter = $cfgHost]"
    $hostChoice = $hostChoice.Trim()

    if ([string]::IsNullOrWhiteSpace($hostChoice)) {
        $host_ = $cfgHost
    } elseif ($hostChoice -eq "1") {
        $host_ = "0.0.0.0"
    } elseif ($hostChoice -eq "2") {
        $host_ = "127.0.0.1"
    } elseif ($hostChoice -eq "3") {
        $customHost = Read-Host "  Введите IP-адрес или хост"
        $customHost = $customHost.Trim()
        $host_ = if ($customHost) { $customHost } else { $cfgHost }
    } else {
        # В качестве значения Host допускается непосредственный ввод IP-адреса
# или имени хоста вместо выбора пункта меню.
        $host_ = $hostChoice
    }

    # Запрашивается порт, если он не был передан параметром командной строки.
    if (-not $Port) {
        $portChoice = Read-Host "Порт сервера [Enter = $cfgPort]"
        $portChoice = $portChoice.Trim()
        if ([string]::IsNullOrWhiteSpace($portChoice)) {
            $port = $cfgPort
        } else {
            $port = $portChoice
        }
    } else {
        $port = $Port
    }

    # Пользователь подтверждает или отключает запуск Microsoft AI Foundry.
    $foundryDefaultHint = if ($useFoundry) { "y" } else { "n" }
    $foundryPrompt = if ($useFoundry) { "Y/n" } else { "y/N" }
    $foundryChoice = Read-Host "Запустить Microsoft AI Foundry? ($foundryPrompt) [Enter = $foundryDefaultHint]"
    $foundryChoice = $foundryChoice.Trim().ToLower()
    if ($foundryChoice -in @("y", "yes", "д", "да", "1")) {
        $useFoundry = $true
    } elseif ($foundryChoice -in @("n", "no", "н", "нет", "0")) {
        $useFoundry = $false
    }

    # Пользователь подтверждает или отключает запуск Ollama.
    $ollamaDefaultHint = if ($useOllama) { "y" } else { "n" }
    $ollamaPrompt = if ($useOllama) { "Y/n" } else { "y/N" }
    $ollamaChoice = Read-Host "Запустить Ollama (localhost:11434)? ($ollamaPrompt) [Enter = $ollamaDefaultHint]"
    $ollamaChoice = $ollamaChoice.Trim().ToLower()
    if ($ollamaChoice -in @("y", "yes", "д", "да", "1")) {
        $useOllama = $true
    } elseif ($ollamaChoice -in @("n", "no", "н", "нет", "0")) {
        $useOllama = $false
    }

    # Пользователь подтверждает запуск Cloudflare Tunnel (только если настроен токен)
    if ($cfTunnelToken) {
        $cfDefaultHint = if ($useCloudflared) { "y" } else { "n" }
        $cfPrompt = if ($useCloudflared) { "Y/n" } else { "y/N" }
        $cfChoice = Read-Host "Запустить Cloudflare Tunnel (kino.davidka.net)? ($cfPrompt) [Enter = $cfDefaultHint]"
        $cfChoice = $cfChoice.Trim().ToLower()
        if ($cfChoice -in @("y", "yes", "д", "да", "1")) {
            $useCloudflared = $true
        } elseif ($cfChoice -in @("n", "no", "н", "нет", "0")) {
            $useCloudflared = $false
        }
    }

    # Пользователь подтверждает или отключает Google OAuth (если не передан явный ключ -EnableOAuth)
    if ($EnableOAuth -eq $null) {
        $oauthDefaultHint = if ($enableOAuthVal) { "y" } else { "n" }
        $oauthPrompt = if ($enableOAuthVal) { "Y/n" } else { "y/N" }
        $oauthChoice = Read-Host "Включить авторизацию Google OAuth? ($oauthPrompt) [Enter = $oauthDefaultHint]"
        $oauthChoice = $oauthChoice.Trim().ToLower()
        if ($oauthChoice -in @("y", "yes", "д", "да", "1")) {
            $enableOAuthVal = $true
        } elseif ($oauthChoice -in @("n", "no", "н", "нет", "0")) {
            $enableOAuthVal = $false
        }
    }

    # Пользователь подтверждает запуск Telegram-бота (если не передан явный ключ -EnableTelegramBot)
    if ($EnableTelegramBot -eq $null) {
        $tgDefaultHint = if ($enableTelegramBotVal) { "y" } else { "n" }
        $tgPrompt = if ($enableTelegramBotVal) { "Y/n" } else { "y/N" }
        $tgChoice = Read-Host "Запустить Telegram-бота? ($tgPrompt) [Enter = $tgDefaultHint]"
        $tgChoice = $tgChoice.Trim().ToLower()
        if ($tgChoice -in @("y", "yes", "д", "да", "1")) {
            $enableTelegramBotVal = $true
        } elseif ($tgChoice -in @("n", "no", "н", "нет", "0")) {
            $enableTelegramBotVal = $false
        }
    }

    # Пользователь подтверждает запуск микросервисов /apps (если не передан явный ключ -EnableApps)
    if ($EnableApps -eq $null) {
        $appsDefaultHint = if ($enableAppsVal) { "y" } else { "n" }
        $appsPrompt = if ($enableAppsVal) { "Y/n" } else { "y/N" }
        $appsChoice = Read-Host "Запустить все микросервисы /apps (порты 8100-8104) в отдельных окнах? ($appsPrompt) [Enter = $appsDefaultHint]"
        $appsChoice = $appsChoice.Trim().ToLower()
        if ($appsChoice -in @("y", "yes", "д", "да", "1")) {
            $enableAppsVal = $true
        } elseif ($appsChoice -in @("n", "no", "н", "нет", "0")) {
            $enableAppsVal = $false
        }
    }

    # Пользователь подтверждает запуск терминала Assist (если не передан явный ключ -EnableAssist)
    if ($EnableAssist -eq $null) {
        $assistDefaultHint = if ($enableAssistVal) { "y" } else { "n" }
        $assistPrompt = if ($enableAssistVal) { "Y/n" } else { "y/N" }
        $assistChoice = Read-Host "Запустить ассистент assist.ps1 в новом терминале? ($assistPrompt) [Enter = $assistDefaultHint]"
        $assistChoice = $assistChoice.Trim().ToLower()
        if ($assistChoice -in @("y", "yes", "д", "да", "1")) {
            $enableAssistVal = $true
        } elseif ($assistChoice -in @("n", "no", "н", "нет", "0")) {
            $enableAssistVal = $false
        }
    }

    # Выбор стартового интерфейса (/admin или /tc)
    if (-not $TestComputer) {
        Write-Host ""
        Write-Host "Выберите стартовый интерфейс для открытия в браузере:" -ForegroundColor White
        Write-Host "  [1] Панель администратора (/admin) — по умолчанию" -ForegroundColor White
        Write-Host "  [2] Test Computer (/tc)           — блок системных приложений и диагностики" -ForegroundColor White
        $modeChoice = Read-Host "Интерфейс [Enter = /admin]"
        $modeChoice = $modeChoice.Trim()
        if ($modeChoice -in @("2", "tc", "/tc", "apps")) {
            $TestComputer = $true
        }
    }
} else {
    # Автозапуск или неинтерактивный режим
    $host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
    $port  = if ($Port)        { [string]$Port }        else { [string]$cfgPort }
}



# ============================================================================
# STAGE 5 — ФОРМИРОВАНИЕ ИТОГОВОЙ КОНФИГУРАЦИИ
# ----------------------------------------------------------------------------
# На основе выбранных параметров формируются протокол и URL, по которому
# приложение будет доступно из браузера. Для привязки к 0.0.0.0 в браузере
# используется localhost, а сетевой адрес выводится отдельно ниже.
# ============================================================================
$proto = if ($useSsl) { "https" } else { "http" }
$browserHost = if ($host_ -eq "0.0.0.0") { "localhost" } else { $host_ }
$targetPath = if ($TestComputer) { "tc" } else { "admin" }
$localUrl = "${proto}://${browserHost}:${port}/${targetPath}"
$openUrl = if ($useCloudflared -and $clientUrl) { "$($clientUrl.TrimEnd('/'))/${targetPath}" } else { $localUrl }

# Вывод параметров запуска (без задержки для автозапуска)
if (-not $autoLaunchEnabled) {
    Write-Host ""
}
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "ИТОГОВЫЕ ПАРАМЕТРЫ ЗАПУСКА:" -ForegroundColor Cyan
Write-Host "  • Хост:            $host_" -ForegroundColor White
Write-Host "  • Порт:            $port" -ForegroundColor White
Write-Host "  • Протокол:        $($proto.ToUpper()) $(if ($useSsl) {'(SSL активен)'} else {'(без SSL)'})" -ForegroundColor White
Write-Host "  • Локальный URL:   $localUrl" -ForegroundColor Green
if ($lanIp -and $host_ -eq "0.0.0.0") {
    Write-Host "  • Сетевой URL:     ${proto}://${lanIp}:${port}/admin" -ForegroundColor Yellow
}
if ($useCloudflared -and $clientUrl) {
    Write-Host "  • URL в браузере:  $openUrl" -ForegroundColor Cyan
} else {
    Write-Host "  • URL в браузере:  $localUrl" -ForegroundColor Cyan
}
Write-Host "  • AI Foundry:      $(if ($useFoundry) {'ВКЛЮЧЁН'} else {'ВЫКЛЮЧЕН'})" -ForegroundColor White
Write-Host "  • Ollama:          $(if ($useOllama) {'ВКЛЮЧЕНА (localhost:11434)'} else {'ВЫКЛЮЧЕНА'})" -ForegroundColor White
Write-Host "  • Google OAuth:    $(if ($enableOAuthVal) {'ВКЛЮЧЁН'} else {'ВЫКЛЮЧЕН (по умолчанию)'})" -ForegroundColor White
Write-Host "  • Telegram Bot:    $(if ($enableTelegramBotVal) {'ВКЛЮЧЁН (по умолчанию)'} else {'ВЫКЛЮЧЕН'})" -ForegroundColor White
Write-Host "  • Apps / Microservices: $(if ($enableAppsVal) {'ВКЛЮЧЕНЫ (все)'} else {'НАСТРОЕНЫ ИНДИВИДУАЛЬНО'})" -ForegroundColor White
$appsOverviewList = @(
    @{ Name = "Windows Sysadmin";         App = "windows_sysadmin";        Port = 8100; Enabled = (Get-IsAppConfigEnabled -AppKey "windows_sysadmin" -AppFolder "windows_sysadmin" -Aliases @("windows_admin", "windowsadmin", "sysadmin")) },
    @{ Name = "Network Terminal";         App = "network_terminal";        Port = 8101; Enabled = (Get-IsAppConfigEnabled -AppKey "network_terminal" -AppFolder "network_terminal" -Aliases @("network")) },
    @{ Name = "System Inspector";         App = "system_inspector";        Port = 8102; Enabled = (Get-IsAppConfigEnabled -AppKey "system_inspector" -AppFolder "system_inspector" -Aliases @("inspector")) },
    @{ Name = "Trading Terminal";         App = "trading_terminal";        Port = 8103; Enabled = (Get-IsAppConfigEnabled -AppKey "trading_terminal" -AppFolder "trading_terminal" -Aliases @("trading")) },
    @{ Name = "Cloudflared Monitor";      App = "cloudflared_monitor";     Port = 8104; Enabled = ($useCloudflared -and (Get-IsAppConfigEnabled -AppKey "cloudflared_monitor" -AppFolder "cloudflared_monitor" -Aliases @("cloudflared"))) },
    @{ Name = "User Assistant";           App = "user_assistant";          Port = 8105; Enabled = (Get-IsAppConfigEnabled -AppKey "user_assistant" -AppFolder "user_assistant" -Aliases @("assistant", "userassistant")) },
    @{ Name = "Google Cloud Monitor";     App = "gcloud_monitor";          Port = 8106; Enabled = (Get-IsAppConfigEnabled -AppKey "gcloud_monitor" -AppFolder "gcloud_monitor" -Aliases @("gcloud", "google_cloud")) },
    @{ Name = "Website Monitor";          App = "website_monitor";         Port = 8107; Enabled = (Get-IsAppConfigEnabled -AppKey "website_monitor" -AppFolder "website_monitor" -Aliases @("website", "website_intelligence")) },
    @{ Name = "System Control Center";    App = "system_control_center";   Port = 8109; Enabled = (Get-IsAppConfigEnabled -AppKey "system_control_center" -AppFolder "system_control_center" -Aliases @("system_control", "control_center")) },
    @{ Name = "Wikipedia Research Lab";   App = "wikipedia_research";      Port = 8110; Enabled = (Get-IsAppConfigEnabled -AppKey "wikipedia_research" -AppFolder "wikipedia_research" -Aliases @("wikipedia", "wiki_lab")) },
    @{ Name = "AI Breadboard Admin";      App = "ai_breadboard_admin";      Port = 8110; Enabled = (Get-IsAppConfigEnabled -AppKey "ai_breadboard_admin" -AppFolder "ai_breadboard_admin" -Aliases @("admin", "admin_panel")) },
    @{ Name = "Research & Statistics";    App = "research_and_statistic";  Port = 8111; Enabled = (Get-IsAppConfigEnabled -AppKey "research_and_statistic" -AppFolder "research_and_statistic" -Aliases @("research_stat", "research")) },
    @{ Name = "Helpdesk & Support";       App = "helpdesk";                Port = 8110; Enabled = (Get-IsAppConfigEnabled -AppKey "helpdesk" -AppFolder "helpdesk" -Aliases @("helpdesk", "it_support")) }
)
foreach ($appItem in $appsOverviewList) {
    if ($appItem.Enabled) {
        $appMode = Get-AppServerMode $appItem.App
        if ($appMode -eq "dedicated") {
            Write-Host "    - $($appItem.Name) (dedicated): http://localhost:$($appItem.Port)" -ForegroundColor DarkCyan
        } else {
            Write-Host "    - $($appItem.Name) (shared):    http://localhost:$port (через основной сервер)" -ForegroundColor DarkGray
        }
    }
}
Write-Host "  • Assist Terminal: $(if ($enableAssistVal) {'ВКЛЮЧЁН'} else {'ВЫКЛЮЧЕН'})" -ForegroundColor White
Write-Host "  • Cloudflare:      $(if ($useCloudflared -and $cfTunnelToken) {'ВКЛЮЧЁН (https://kino.davidka.net)'} elseif (-not $cfTunnelToken) {'ТОКЕН НЕ ЗАДАН'} else {'ВЫКЛЮЧЕН'})" -ForegroundColor White
if ($autoLaunchEnabled -and $autoLaunchDelay -gt 0) {
    Write-Host "  • Автозапуск:      ВКЛЮЧЁН (задержка: $autoLaunchDelay сек)" -ForegroundColor Yellow
}
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray

# ============================================================================
# STAGE 6 — ПОДГОТОВКА TCP-ПОРТА
# ----------------------------------------------------------------------------
# Проверяется, занят ли выбранный порт. Если порт используется другим
# процессом, определяется его PID и процесс принудительно завершается, чтобы
# FastAPI мог занять порт без конфликта.
# ============================================================================
Write-Host ""
Write-Host "[2/3] Проверка порта $port..." -ForegroundColor Cyan

# Определяется наличие процессов, использующих выбранный TCP-порт.
$netstatOutput = netstat -aon 2>$null
$occupied = $netstatOutput | Select-String ":${port}\s" | ForEach-Object { ($_ -split '\s+')[-1] } | Where-Object { $_ -match '^\d+$' -and $_ -ne '0' } | Select-Object -Unique

if ($occupied) {
    Write-Host "    [WARN] Порт $port занят!" -ForegroundColor Yellow
    foreach ($pid_ in $occupied) {
        try {
            $proc = Get-Process -Id $pid_ -ErrorAction Stop
            Write-Host "        PID $pid_ | $($proc.ProcessName) | $($proc.Path)" -ForegroundColor Yellow
            Write-Host "        Завершение процесса..." -ForegroundColor DarkGray
            Stop-Process -Id $pid_ -Force -ErrorAction Stop
            Write-Host "        [OK] Завершен" -ForegroundColor Green
        } catch {
            Write-Host "        [ERROR] Не удалось завершить PID ${pid_}: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "    [OK] Порт свободен" -ForegroundColor Green
}

# ============================================================================
# STAGE 7 — ЗАПУСК СОПУТСТВУЮЩИХ СЕРВИСОВ
# ----------------------------------------------------------------------------
# После подготовки основной конфигурации запускаются сервисы, необходимые
# приложению. На текущем этапе таким сервисом является локальный Foundry,
# если он был включён пользователем или конфигурацией.
# ============================================================================
Write-Host ""
Write-Host "[3/3] Проверка сопутствующих сервисов..." -ForegroundColor Cyan

# ----------------------------------------------------------------------------
# SUBSTAGE 7.1 — MICROSOFT AI FOUNDRY
# ----------------------------------------------------------------------------
# Проверяется наличие Run-Foundry.ps1 и передаётся ему команда запуска.
# При отключённом Foundry этот блок полностью пропускается.
# ----------------------------------------------------------------------------
if ($useFoundry) {
    Write-Host ""
    Write-Host "    Запуск локальной службы Foundry..." -ForegroundColor Cyan
    $foundryScript = Join-Path $scriptDir "launchers\Run-Foundry.ps1"
    if (-not (Test-Path $foundryScript)) {
        $foundryScript = Join-Path $scriptDir "Run-Foundry.ps1"
    }
    if (Test-Path $foundryScript) {
        Write-Host "    Вызов Run-Foundry.ps1..." -ForegroundColor DarkGray
        & $foundryScript -Action start
    } else {
        Write-Host "    [WARN] Run-Foundry.ps1 не найден: $foundryScript" -ForegroundColor Yellow
    }
}

# ----------------------------------------------------------------------------
# SUBSTAGE 7.2 — OLLAMA LOCAL SERVICE (localhost:11434)
# ----------------------------------------------------------------------------
# Проверяется наличие Run-Ollama.ps1 и передаётся ему команда запуска.
# При отключённой Ollama этот блок полностью пропускается.
# ----------------------------------------------------------------------------
if ($useOllama) {
    Write-Host ""
    Write-Host "    Запуск локальной службы Ollama..." -ForegroundColor Cyan
    $ollamaScript = Join-Path $scriptDir "launchers\Run-Ollama.ps1"
    if (-not (Test-Path $ollamaScript)) {
        $ollamaScript = Join-Path $scriptDir "Run-Ollama.ps1"
    }
    if (Test-Path $ollamaScript) {
        Write-Host "    Вызов Run-Ollama.ps1..." -ForegroundColor DarkGray
        & $ollamaScript -Action start
    } else {
        Write-Host "    [WARN] Run-Ollama.ps1 не найден: $ollamaScript" -ForegroundColor Yellow
    }
}

# ----------------------------------------------------------------------------
# SUBSTAGE 7.3 — CLOUDFLARE TUNNEL (kino.davidka.net)
# ----------------------------------------------------------------------------
if ($useCloudflared) {
    if ($cfTunnelToken) {
        Write-Host ""
        Write-Host "    Запуск службы Cloudflare Tunnel..." -ForegroundColor Cyan
        $cfScript = Join-Path $scriptDir "launchers\Run-Cloudflared.ps1"
        if (-not (Test-Path $cfScript)) {
            $cfScript = Join-Path $scriptDir "Run-Cloudflared.ps1"
        }
        if (Test-Path $cfScript) {
            Write-Host "    Вызов Run-Cloudflared.ps1..." -ForegroundColor DarkGray
            & $cfScript
        } else {
            Write-Host "    [WARN] Run-Cloudflared.ps1 не найден: $cfScript" -ForegroundColor Yellow
        }
    } else {
        Write-Host ""
        Write-Host "    [WARN] Cloudflare Tunnel включен, но CLOUDFLARE_TUNNEL_TOKEN отсутствует в .env" -ForegroundColor Yellow
    }
}

# ----------------------------------------------------------------------------
# SUBSTAGE 7.4 — TELEGRAM BOT (Embedded in FastAPI Server Lifecycle)
# ----------------------------------------------------------------------------
# Telegram-бот теперь интегрирован напрямую в жизненный цикл FastAPI (main.py)
# как плагин telegram_bot с единым доступом ко всем плагинам и моделям.
# При $enableTelegramBotVal = $true он запустится вместе с сервером.
# ----------------------------------------------------------------------------
if ($enableTelegramBotVal) {
    Write-Host ""
    Write-Host "    [INTEGRATED] Telegram-бот будет запущен внутри жизненного цикла FastAPI..." -ForegroundColor Green
    $env:ENABLE_TELEGRAM_BOT = "true"
} else {
    $env:ENABLE_TELEGRAM_BOT = "false"
    # Убеждаемся что автономные фоновые процессы бота (если были) остановлены
    $tgScript = Join-Path $scriptDir "launchers\Run-TelegramBot.ps1"
    if (-not (Test-Path $tgScript)) {
        $tgScript = Join-Path $scriptDir "Run-TelegramBot.ps1"
    }
    if (Test-Path $tgScript) {
        & $tgScript -Action stop
    }
}

# ----------------------------------------------------------------------------
# SUBSTAGE 7.4.5 — STANDALONE APPS / MICROSERVICES (/apps)
# ----------------------------------------------------------------------------
# Проверка режима (dedicated / shared) в src/apps/<appname>/config.json или apps/<appname>/config.json.
# Если режим dedicated — запускается соответствующий автономный лончер на своём порту.
# Если режим shared — микросервис обслуживается через основной FastAPI сервер.
# ----------------------------------------------------------------------------
$launchersDir = Join-Path $scriptDir "launchers"

$appLaunchConfigs = @(
    @{ Name = "Windows System Administrator"; App = "windows_sysadmin";        Launcher = "Run-WindowsAdmin.ps1";        Port = 8100; Enabled = (Get-IsAppConfigEnabled -AppKey "windows_sysadmin" -AppFolder "windows_sysadmin" -Aliases @("windows_admin", "windowsadmin", "sysadmin")) },
    @{ Name = "Network Analyzer Terminal";    App = "network_terminal";        Launcher = "Run-NetworkTerminal.ps1";     Port = 8101; Enabled = (Get-IsAppConfigEnabled -AppKey "network_terminal" -AppFolder "network_terminal" -Aliases @("network")) },
    @{ Name = "System Inspector";             App = "system_inspector";        Launcher = "Run-SystemInspector.ps1";     Port = 8102; Enabled = (Get-IsAppConfigEnabled -AppKey "system_inspector" -AppFolder "system_inspector" -Aliases @("inspector")) },
    @{ Name = "Exchange Trading Terminal";    App = "trading_terminal";        Launcher = "Run-TradingTerminal.ps1";     Port = 8103; Enabled = (Get-IsAppConfigEnabled -AppKey "trading_terminal" -AppFolder "trading_terminal" -Aliases @("trading")) },
    @{ Name = "Cloudflare Tunnel Monitor";    App = "cloudflared_monitor";     Launcher = "Run-CloudflaredMonitor.ps1"; Port = 8104; Enabled = ($useCloudflared -and (Get-IsAppConfigEnabled -AppKey "cloudflared_monitor" -AppFolder "cloudflared_monitor" -Aliases @("cloudflared"))) },
    @{ Name = "User Assistant";               App = "user_assistant";          Launcher = "Run-Apps.ps1";               Port = 8105; Enabled = (Get-IsAppConfigEnabled -AppKey "user_assistant" -AppFolder "user_assistant" -Aliases @("assistant", "userassistant")) },
    @{ Name = "Google Cloud Monitor";         App = "gcloud_monitor";          Launcher = "Run-GCloudMonitor.ps1";       Port = 8106; Enabled = (Get-IsAppConfigEnabled -AppKey "gcloud_monitor" -AppFolder "gcloud_monitor" -Aliases @("gcloud", "google_cloud")) },
    @{ Name = "Website Intelligence Monitor"; App = "website_monitor";         Launcher = "Run-WebsiteMonitor.ps1";      Port = 8107; Enabled = (Get-IsAppConfigEnabled -AppKey "website_monitor" -AppFolder "website_monitor" -Aliases @("website", "website_intelligence")) },
    @{ Name = "System Control Center";        App = "system_control_center";   Launcher = "Run-SystemControlCenter.ps1"; Port = 8109; Enabled = (Get-IsAppConfigEnabled -AppKey "system_control_center" -AppFolder "system_control_center" -Aliases @("system_control", "control_center")) },
    @{ Name = "Wikipedia Research Lab";       App = "wikipedia_research";      Launcher = "Run-WikipediaResearch.ps1";  Port = 8110; Enabled = (Get-IsAppConfigEnabled -AppKey "wikipedia_research" -AppFolder "wikipedia_research" -Aliases @("wikipedia", "wiki_lab")) },
    @{ Name = "AI Breadboard Admin";          App = "ai_breadboard_admin";      Launcher = "Run-Apps.ps1";               Port = 8110; Enabled = (Get-IsAppConfigEnabled -AppKey "ai_breadboard_admin" -AppFolder "ai_breadboard_admin" -Aliases @("admin", "admin_panel")) },
    @{ Name = "Research & Statistics";        App = "research_and_statistic";  Launcher = "Run-Apps.ps1";               Port = 8111; Enabled = (Get-IsAppConfigEnabled -AppKey "research_and_statistic" -AppFolder "research_and_statistic" -Aliases @("research_stat", "research")) },
    @{ Name = "Helpdesk & Support";           App = "helpdesk";                Launcher = "Run-Helpdesk.ps1";           Port = 8110; Enabled = (Get-IsAppConfigEnabled -AppKey "helpdesk" -AppFolder "helpdesk" -Aliases @("helpdesk", "it_support")) }
)

foreach ($item in $appLaunchConfigs) {
    if ($item.Enabled) {
        $serverMode = Get-AppServerMode $item.App
        if ($serverMode -eq "dedicated") {
            $launcherPath = Join-Path $launchersDir $item.Launcher
            if (-not (Test-Path $launcherPath)) {
                $launcherPath = Join-Path $scriptDir $item.Launcher
            }
            if (Test-Path $launcherPath) {
                Write-Host ""
                Write-Host "    Запуск $($item.Name) ($($item.Port), dedicated) в отдельном окне..." -ForegroundColor Cyan
                & $launcherPath -Action start -NewWindow
            } else {
                Write-Host "    [WARN] Лончер $($item.Launcher) не найден: $launcherPath" -ForegroundColor Yellow
            }
        } else {
            Write-Host ""
            Write-Host "    [SHARED] $($item.Name) сконфигурирован в shared-режиме (маршрутизируется через основной FastAPI сервер)..." -ForegroundColor DarkGray
        }
    }
}

# ----------------------------------------------------------------------------
# SUBSTAGE 7.5 — ASSIST CLI TERMINAL (assist.ps1)
# ----------------------------------------------------------------------------
# При включённом параметре EnableAssist запускается отдельное окно терминала
# с интерактивным окружением assist.ps1.
# ----------------------------------------------------------------------------
if ($enableAssistVal) {
    Write-Host ""
    Write-Host "    Запуск терминала Assist (assist.ps1)..." -ForegroundColor Cyan
    $assistScript = Join-Path $scriptDir "assist.ps1"
    if (Test-Path $assistScript) {
        try {
            $hasWt = Get-Command wt.exe -ErrorAction SilentlyContinue
            $hasPwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
            $shellExe = if ($hasPwsh) { "pwsh.exe" } else { "powershell.exe" }

            if ($hasWt) {
                Start-Process wt.exe -ArgumentList "-d `"$scriptDir`" $shellExe -NoExit -ExecutionPolicy Bypass -File `"$assistScript`""
            } else {
                Start-Process $shellExe -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$assistScript`"" -WorkingDirectory $scriptDir
            }
            Write-Host "    [OK] Терминал Assist запущен" -ForegroundColor Green
        } catch {
            Write-Host "    [WARN] Не удалось запустить терминал Assist: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "    [WARN] assist.ps1 не найден: $assistScript" -ForegroundColor Yellow
    }
}

# ----------------------------------------------------------------------------
# SUBSTAGE 7.6 — SYSTEM TRAY COMPANION (ShowHide-InTray.ps1)
# ----------------------------------------------------------------------------
# При включённом параметре EnableTray инициализируется иконка в трее Windows
# с возможностью скрывать/разворачивать окно и предотвращать аварийное закрытие.
# ----------------------------------------------------------------------------
if ($enableTrayVal) {
    Write-Host ""
    Write-Host "    Инициализация системного трея (ShowHide-InTray.ps1)..." -ForegroundColor Cyan
    $trayScript = Join-Path $scriptDir "launchers\ShowHide-InTray.ps1"
    if (-not (Test-Path $trayScript)) {
        $trayScript = Join-Path $scriptDir "ShowHide-InTray.ps1"
    }
    if (Test-Path $trayScript) {
        try {
            & $trayScript -Action start -WebUrl $openUrl -Title "AI Breadboard ($port)"
        } catch {
            Write-Host "    [WARN] Не удалось инициализировать системный трей: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "    [WARN] ShowHide-InTray.ps1 не найден: $trayScript" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[SUCCESS] Настройка завершена. Запуск сервера..." -ForegroundColor Green
# ============================================================================
# STAGE 8 — ЗАПУСК FASTAPI-СЕРВЕРА
# ----------------------------------------------------------------------------
# Все параметры запуска подготовлены, порт освобождён, а необходимые
# сопутствующие сервисы запущены. Управление передаётся Run-Unicorn.ps1,
# который запускает FastAPI-сервер в текущем окне PowerShell.
# ============================================================================
$env:PRELOAD_SILERO = $preloadSilero
$env:ENABLE_OAUTH = if ($enableOAuthVal) { "true" } else { "false" }
$unicornScript = Join-Path $scriptDir "launchers\Run-Unicorn.ps1"
if (-not (Test-Path $unicornScript)) {
    $unicornScript = Join-Path $scriptDir "Run-Unicorn.ps1"
}
if (Test-Path $unicornScript) {
    $unicornCallArgs = @{
        Host_      = $host_
        Port       = $port
        OpenUrl    = $openUrl
        ConfigFile = $activeConfigFile
    }
    if ($enableOAuthVal -ne $null) { $unicornCallArgs['EnableOAuth'] = $enableOAuthVal }
    if ($enableTelegramBotVal -ne $null) { $unicornCallArgs['EnableTelegramBot'] = $enableTelegramBotVal }
    if ($Workers -ne $null) { $unicornCallArgs['Workers'] = $Workers }
    if ($Reload -ne $null) { $unicornCallArgs['Reload'] = $Reload }
    Write-Host "    Запуск Run-Unicorn.ps1 с параметрами -Host_ $host_ -Port $port -OpenUrl $openUrl -EnableOAuth $enableOAuthVal -EnableTelegramBot $enableTelegramBotVal..." -ForegroundColor DarkGray
    & $unicornScript @unicornCallArgs
} else {
    Write-Host "    [ERROR] Run-Unicorn.ps1 не найден: $unicornScript" -ForegroundColor Red
    exit 1
}
