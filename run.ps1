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
$configPath = Join-Path $scriptDir "config.json"
$envFile = Join-Path $scriptDir ".env"
$cfgHost = "0.0.0.0"
$cfgPort = "8000"
$useSsl = $true
$useFoundry = $false
$useOllama = $false
$useCloudflared = $true
$enableOAuthVal = $true
$enableTelegramBotVal = $true
$enableAssistVal = $false
$preloadSilero = $false
$clientUrl = $null

if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath | ConvertFrom-Json
        if ($cfg.server.host) { $cfgHost = [string]$cfg.server.host }
        if ($cfg.server.port) { $cfgPort = [string]$cfg.server.port }
        if ($cfg.server.use_ssl -ne $null) { $useSsl = [bool]$cfg.server.use_ssl }
        if ($cfg.server.enable_oauth -ne $null) { $enableOAuthVal = [bool]$cfg.server.enable_oauth }
        if ($cfg.server.enable_telegram_bot -ne $null) { $enableTelegramBotVal = [bool]$cfg.server.enable_telegram_bot }
        if ($cfg.server.enable_assist -ne $null) { $enableAssistVal = [bool]$cfg.server.enable_assist }
        if ($cfg.server.auto_start_assist_cli -ne $null) { $enableAssistVal = [bool]$cfg.server.auto_start_assist_cli }
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
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
            if ($key -eq "ENABLE_OAUTH") { $enableOAuthVal = $val -in ("true","1","yes") }
            if ($key -eq "ENABLE_TELEGRAM_BOT") { $enableTelegramBotVal = $val -in ("true","1","yes") }
            if ($key -eq "ENABLE_ASSIST") { $enableAssistVal = $val -in ("true","1","yes") }
            if ($key -eq "AUTO_START_ASSIST_CLI") { $enableAssistVal = $val -in ("true","1","yes") }
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
} else {
    # Автозапуск или неинтерактивный режим
    $host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
    $port  = if ($Port)        { [string]$Port }        else { [string]$cfgPort }
}

# ============================================================================
# STAGE 4 — ПРОВЕРКА КОНФИГУРАЦИИ AI
# ----------------------------------------------------------------------------
# ============================================================================
# STAGE 4.4 — ПРОВЕРКА НАЛИЧИЯ API-КЛЮЧА GOOGLE GEMINI (AI)
# ----------------------------------------------------------------------------
# Проверяется наличие API-ключа Gemini в переменных окружения и .env.
# Если ключ отсутствует и запуск интерактивный, пользователю предлагается ввести
# его и сохранить в .env.
# ============================================================================
$hasApiKey = $false

if ($env:GEMINI_API_KEY -or $env:GEMINI_ANTIGRAVITY_API_KEY -or $env:AGY_API_KEY) {
    $hasApiKey = $true
}

if (-not $hasApiKey -and (Test-Path $envFile)) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^(GEMINI_API_KEY|GEMINI_API_KEY_\d+|GEMINI_ANTIGRAVITY_API_KEY|AGY_API_KEY)=(.*)$") {
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($val -and $val.Length -ge 10) { $hasApiKey = $true }
        }
    }
}

if (-not $hasApiKey) {
    if ($isInteractive) {
        Write-Host ""
        Write-Host "┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
        Write-Host " 🔑 НАСТРОЙКА API-КЛЮЧА GOOGLE GEMINI (AI)" -ForegroundColor Yellow
        Write-Host "  API-ключ не найден. Для работы чата и ИИ-моделей нужен ключ." -ForegroundColor White
        Write-Host "  Бесплатный ключ можно получить: https://aistudio.google.com/app/apikey" -ForegroundColor Cyan
        Write-Host "└─────────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
        Write-Host ""
        $keyInput = Read-Host "Введите Gemini API Key (Enter — пропустить и настроить позже)"
        $keyInput = $keyInput.Trim().Trim('"').Trim("'")
        if ($keyInput) {
            # Обновляется файл .env: существующие значения заменяются, отсутствующие параметры добавляются.
            $envLines = @()
            if (Test-Path $envFile) { $envLines = Get-Content $envFile }
            $hasGemini = $false
            $newLines = @()
            foreach ($line in $envLines) {
                if ($line -match "^GEMINI_API_KEY=") {
                    $newLines += "GEMINI_API_KEY=$keyInput"
                    $hasGemini = $true
                } else {
                    $newLines += $line
                }
            }
            if (-not $hasGemini) {
                $newLines += "GEMINI_API_KEY=$keyInput"
            }
            Set-Content -Path $envFile -Value $newLines -Encoding UTF8
            $hasApiKey = $true
            Write-Host "    [OK] API-ключ сохранён в .env" -ForegroundColor Green
        } else {
            Write-Host "    [WARN] Запуск без API-ключа. ИИ-функции будут ограничены." -ForegroundColor Yellow
        }
    } else {
        Write-Host "    [WARN] API-ключ Gemini не настроен. Настройте в .env или Web UI" -ForegroundColor Yellow
    }
} else {
    Write-Host "    [OK] API-ключ ИИ обнаружен" -ForegroundColor Green
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
$localUrl = "${proto}://${browserHost}:${port}/admin"
$openUrl = if ($clientUrl) { "$($clientUrl.TrimEnd('/'))/admin" } else { $localUrl }

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
if ($clientUrl) {
    Write-Host "  • URL в браузере:  $openUrl" -ForegroundColor Cyan
}
Write-Host "  • AI Foundry:      $(if ($useFoundry) {'ВКЛЮЧЁН'} else {'ВЫКЛЮЧЕН'})" -ForegroundColor White
Write-Host "  • Ollama:          $(if ($useOllama) {'ВКЛЮЧЕНА (localhost:11434)'} else {'ВЫКЛЮЧЕНА'})" -ForegroundColor White
Write-Host "  • Google OAuth:    $(if ($enableOAuthVal) {'ВКЛЮЧЁН'} else {'ВЫКЛЮЧЕН (по умолчанию)'})" -ForegroundColor White
Write-Host "  • Telegram Bot:    $(if ($enableTelegramBotVal) {'ВКЛЮЧЁН (по умолчанию)'} else {'ВЫКЛЮЧЕН'})" -ForegroundColor White
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
# SUBSTAGE 7.4 — TELEGRAM BOT (scripts/dev/bot_runner.py)
# ----------------------------------------------------------------------------
# Проверяется наличие Run-TelegramBot.ps1 и передаётся ему команда запуска.
# При отключённом Telegram-боте этот блок полностью пропускается.
# ----------------------------------------------------------------------------
if ($enableTelegramBotVal) {
    Write-Host ""
    Write-Host "    Запуск Telegram-бота в отдельном окне терминала..." -ForegroundColor Cyan
    $tgScript = Join-Path $scriptDir "launchers\Run-TelegramBot.ps1"
    if (-not (Test-Path $tgScript)) {
        $tgScript = Join-Path $scriptDir "Run-TelegramBot.ps1"
    }
    if (Test-Path $tgScript) {
        Write-Host "    Вызов Run-TelegramBot.ps1 (-NewWindow)..." -ForegroundColor DarkGray
        & $tgScript -Action start -NewWindow
    } else {
        Write-Host "    [WARN] Run-TelegramBot.ps1 не найден: $tgScript" -ForegroundColor Yellow
    }
} else {
    # Если бот отключён, убеждаемся что фоновые процессы бота остановлены
    $tgScript = Join-Path $scriptDir "launchers\Run-TelegramBot.ps1"
    if (-not (Test-Path $tgScript)) {
        $tgScript = Join-Path $scriptDir "Run-TelegramBot.ps1"
    }
    if (Test-Path $tgScript) {
        & $tgScript -Action stop
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
        Host_   = $host_
        Port    = $port
        OpenUrl = $openUrl
    }
    if ($enableOAuthVal -ne $null) { $unicornCallArgs['EnableOAuth'] = $enableOAuthVal }
    if ($Workers -ne $null) { $unicornCallArgs['Workers'] = $Workers }
    if ($Reload -ne $null) { $unicornCallArgs['Reload'] = $Reload }
    Write-Host "    Запуск Run-Unicorn.ps1 с параметрами -Host_ $host_ -Port $port -OpenUrl $openUrl -EnableOAuth $enableOAuthVal..." -ForegroundColor DarkGray
    & $unicornScript @unicornCallArgs
} else {
    Write-Host "    [ERROR] Run-Unicorn.ps1 не найден: $unicornScript" -ForegroundColor Red
    exit 1
}
