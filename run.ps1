<#
.SYNOPSIS
    Главный лончер проекта ai-breadboard. Запускает FastAPI-сервер и сопутствующие сервисы.

.DESCRIPTION
    Активирует виртуальное окружение, загружает конфигурацию из config.json и .env,
    в интерактивном режиме запрашивает адрес хоста (0.0.0.0, 127.0.0.1 или свой IP),
    порт и параметры сопутствующих сервисов (Foundry), проверяет зависимости,
    освобождает порт и запускает FastAPI-сервер через Run-Unicorn.ps1.

.PARAMETER HostAddress
    IP-адрес или хост для привязки сервера (например: 0.0.0.0, 127.0.0.1, localhost).
    Алиасы параметра: -Host, -Address, -IP, -Host_.
    При явной передаче интерактивный запрос адреса пропускается.

.PARAMETER Port
    TCP-порт для запуска сервера (по умолчанию: из config.json или 8000).

.PARAMETER NonInteractive
    Запуск в неинтерактивном режиме без диалоговых вопросов (использует переданные параметры или config.json).

.PARAMETER Help
    Отображение справки по использованию лончера (-Help, -h, --help).

.EXAMPLE
    .\run.ps1
    .\run.ps1 -Host 0.0.0.0
    .\run.ps1 -Host 127.0.0.1 -Port 8000
    .\run.ps1 -NonInteractive
    .\run.ps1 --help
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [Alias('Host', 'Address', 'IP', 'Host_')]
    [string]$HostAddress,

    [Parameter(Position = 1)]
    [string]$Port,

    [switch]$NonInteractive,

    [Alias('h', '-help')]
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

$venvActivate = Join-Path $scriptDir "venv\Scripts\Activate.ps1"
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
if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║              run.ps1 — СПРАВКА И ПАРАМЕТРЫ                    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Главный интерактивный лончер проекта ai-breadboard."
    Write-Host "  Запускает FastAPI-сервер и сопутствующие сервисы (Foundry)."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\run.ps1"
    Write-Host "  .\run.ps1 [-Host <хост>] [-Port <порт>] [-NonInteractive]"
    Write-Host "  .\run.ps1 --help"
    Write-Host ""
    Write-Host "ПАРАМЕТРЫ:" -ForegroundColor Yellow
    Write-Host "  -Host, -Address, -IP  IP-адрес привязки (0.0.0.0, 127.0.0.1, localhost)."
    Write-Host "  -Port <string>        Порт сервера (по умолчанию: из config.json или 8000)."
    Write-Host "  -NonInteractive       Пропустить интерактивные запросы и запустить сразу."
    Write-Host "  -Help, -h, --help     Показать эту справку и выйти."
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\run.ps1"
    Write-Host "  .\run.ps1 -Host 0.0.0.0"
    Write-Host "  .\run.ps1 -Host 127.0.0.1 -Port 8000"
    Write-Host "  .\run.ps1 -NonInteractive"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         ЗАПУСК FastAPI СЕРВЕРА - ИНТЕРАКТИВНЫЙ ЛОНЧЕР         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STAGE 2 — ПОДГОТОВКА PYTHON-ОКРУЖЕНИЯ
# ----------------------------------------------------------------------------
# Определяется Python, используемый проектом. В первую очередь проверяется
# виртуальное окружение проекта. Если оно отсутствует, используется Python,
# доступный в системном PATH.
#
# На этом этапе также активируется venv, если его скрипт активации найден.
# ============================================================================
Write-Host "[1/5] Проверка виртуального окружения..." -ForegroundColor Cyan

# Используется прямой путь к Python из venv, чтобы выбор интерпретатора
# не зависел от PATH и возможных заглушек Microsoft Store.
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "    [OK] Виртуальное окружение найдено" -ForegroundColor Green
    Write-Host "    Активация..." -ForegroundColor DarkGray
    if (Test-Path $venvActivate) { . $venvActivate }
    Write-Host "    [OK] Виртуальное окружение активировано" -ForegroundColor Green

    # Python из виртуального окружения используется напрямую, минуя PATH.
    $pythonPath = $venvPython
    Write-Host "    Python: $pythonPath" -ForegroundColor Gray
} else {
    Write-Host "    [WARN] Виртуальное окружение не найдено: $venvPython" -ForegroundColor Yellow
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $pythonPath) {
        Write-Host "    [ERROR] Python не найден! Установите Python с python.org и пересоздайте venv." -ForegroundColor Red
        exit 1
    }
    Write-Host "    [WARN] Используется системный Python: $pythonPath" -ForegroundColor Yellow
}

# ============================================================================
# STAGE 3 — ПРОВЕРКА PYTHON-ЗАВИСИМОСТЕЙ
# ----------------------------------------------------------------------------
# Проверяется наличие основных библиотек, необходимых для запуска приложения:
# FastAPI, Uvicorn, python-dotenv и PyJWT. Ошибка на этом этапе не прерывает
# лончер, а выводится как предупреждение с указанием способа установки.
# ============================================================================
Write-Host ""
Write-Host "[2/5] Проверка зависимостей..." -ForegroundColor Cyan
try {
    $packages = & $pythonPath -c "import fastapi, uvicorn, dotenv, jwt; print('fastapi, uvicorn, python-dotenv, PyJWT - OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] Основные зависимости загружены" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Некоторые зависимости не установлены. Запустите install.cmd" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    [ERROR] Ошибка при проверке зависимостей: $_" -ForegroundColor Red
    Write-Host "    Установка: install.cmd или pip install -r requirements.txt" -ForegroundColor Yellow
}

# ============================================================================
# STAGE 4 — ЗАГРУЗКА КОНФИГУРАЦИИ И ОКРУЖЕНИЯ
# ----------------------------------------------------------------------------
# Загружаются базовые параметры из config.json и значения, переопределяющие
# их из .env. Одновременно определяются параметры SSL, Foundry и предварительной
# загрузки Silero. В конце этапа определяется локальный сетевой IP, который
# используется только для подсказки пользователю.
# ============================================================================
Write-Host ""
Write-Host "[3/5] Загрузка конфигурации..." -ForegroundColor Cyan
$configPath = Join-Path $scriptDir "config.json"
$envFile = Join-Path $scriptDir ".env"
$cfgHost = "0.0.0.0"
$cfgPort = "8000"
$useSsl = $true
$useFoundry = $false
$preloadSilero = $false

if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath | ConvertFrom-Json
        if ($cfg.server.host) { $cfgHost = [string]$cfg.server.host }
        if ($cfg.server.port) { $cfgPort = [string]$cfg.server.port }
        if ($cfg.server.use_ssl -ne $null) { $useSsl = [bool]$cfg.server.use_ssl }
        if ($cfg.ai.use_foundry -ne $null) { $useFoundry = [bool]$cfg.ai.use_foundry }
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
            if ($key -eq "USE_FOUNDRY") { $useFoundry = $val -in ("true","1","yes") }
            if ($key -eq "CLOUDFLARE_TUNNEL_TOKEN") { $cfTunnelToken = $val }
            if ($key -eq "AUTO_LAUNCH_ENABLED") { $autoLaunchEnabled = $val -in ("true","1","yes") }
            if ($key -eq "AUTO_LAUNCH_DELAY_SECONDS" -and $val -match '^\d+$') { $autoLaunchDelay = [int]$val }
        }
    }
}

# Определяется сетевой IPv4-адрес машины для отображения пользователю.
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notmatch '^(169\.254|127\.)' -and $_.InterfaceAlias -notmatch 'Loopback' } |
    Select-Object -ExpandProperty IPAddress -First 1)

# ============================================================================
# STAGE 5 — ВЫБОР ПАРАМЕТРОВ ЗАПУСКА
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

$isInteractive = (-not $NonInteractive) -and (-not $HostAddress)

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
} else {
    # Автозапуск или неинтерактивный режим
    $host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
    $port  = if ($Port)        { [string]$Port }        else { [string]$cfgPort }
}

# ============================================================================
# STAGE 6 — ПРОВЕРКА КОНФИГУРАЦИИ AI
# ----------------------------------------------------------------------------
# Проверяется наличие API-ключа Gemini в переменных окружения, .env и локальном
# хранилище core/secrets/gemini_keys.json. Если ключ отсутствует и запуск
# интерактивный, пользователю предлагается ввести его и сохранить в проекте.
# ============================================================================
$geminiKeysFile = Join-Path $scriptDir "core\secrets\gemini_keys.json"
$hasApiKey = $false

if ($env:GEMINI_API_KEY -or $env:GOOGLE_API_KEY -or $env:AGY_API_KEY) {
    $hasApiKey = $true
}

if (-not $hasApiKey -and (Test-Path $envFile)) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^(GEMINI_API_KEY|GOOGLE_API_KEY|AGY_API_KEY)=(.*)$") {
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($val -and $val.Length -ge 10) { $hasApiKey = $true }
        }
    }
}

if (-not $hasApiKey -and (Test-Path $geminiKeysFile)) {
    try {
        $jsonKeys = Get-Content $geminiKeysFile -Raw | ConvertFrom-Json
        foreach ($prop in $jsonKeys.PSObject.Properties) {
            $entry = $prop.Value
            if ($entry.api_key -and $entry.api_key.Length -ge 10) {
                $hasApiKey = $true
                break
            }
        }
    } catch {}
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
            # Обновляется файл .env: существующие значения заменяются, отсутствующие
# параметры добавляются.
            $envLines = @()
            if (Test-Path $envFile) { $envLines = Get-Content $envFile }
            $hasGemini = $false
            $hasNames = $false
            $newLines = @()
            foreach ($line in $envLines) {
                if ($line -match "^GEMINI_API_KEY=") {
                    $newLines += "GEMINI_API_KEY=$keyInput"
                    $hasGemini = $true
                } elseif ($line -match "^GEMINI_API_KEY_NAMES=") {
                    $newLines += "GEMINI_API_KEY_NAMES=default"
                    $hasNames = $true
                } elseif ($line -match "^GOOGLE_API_KEY=") {
                    $newLines += "GOOGLE_API_KEY=$keyInput"
                } else {
                    $newLines += $line
                }
            }
            if (-not $hasGemini) {
                $newLines += "GEMINI_API_KEY=$keyInput"
                $newLines += "GOOGLE_API_KEY=$keyInput"
            }
            if (-not $hasNames) {
                $newLines += "GEMINI_API_KEY_NAMES=default"
            }
            Set-Content -Path $envFile -Value $newLines -Encoding UTF8
            
            # Обновляется локальное хранилище API-ключей Gemini.
            $secretsDir = Join-Path $scriptDir "core\secrets"
            if (-not (Test-Path $secretsDir)) { New-Item -ItemType Directory -Force -Path $secretsDir | Out-Null }
            $keysObj = [ordered]@{
                "default" = [ordered]@{
                    "api_key" = $keyInput
                    "status" = "active"
                    "last_run" = ""
                    "exhausted_at" = ""
                }
            }
            $keysObj | ConvertTo-Json -Depth 5 | Set-Content -Path $geminiKeysFile -Encoding UTF8
            $hasApiKey = $true
            Write-Host "    [OK] API-ключ сохранён в .env и core/secrets/gemini_keys.json" -ForegroundColor Green
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
# STAGE 7 — ФОРМИРОВАНИЕ ИТОГОВОЙ КОНФИГУРАЦИИ
# ----------------------------------------------------------------------------
# На основе выбранных параметров формируются протокол и URL, по которому
# приложение будет доступно из браузера. Для привязки к 0.0.0.0 в браузере
# используется localhost, а сетевой адрес выводится отдельно ниже.
# ============================================================================
$proto = if ($useSsl) { "https" } else { "http" }
$browserHost = if ($host_ -eq "0.0.0.0") { "localhost" } else { $host_ }
$url = "${proto}://${browserHost}:${port}"

# Вывод параметров запуска (без задержки для автозапуска)
if (-not $autoLaunchEnabled) {
    Write-Host ""
}
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "ИТОГОВЫЕ ПАРАМЕТРЫ ЗАПУСКА:" -ForegroundColor Cyan
Write-Host "  • Хост:            $host_" -ForegroundColor White
Write-Host "  • Порт:            $port" -ForegroundColor White
Write-Host "  • Протокол:        $($proto.ToUpper()) $(if ($useSsl) {'(SSL активен)'} else {'(без SSL)'})" -ForegroundColor White
Write-Host "  • Локальный URL:   $url" -ForegroundColor Green
if ($lanIp -and $host_ -eq "0.0.0.0") {
    Write-Host "  • Сетевой URL:     ${proto}://${lanIp}:${port}/" -ForegroundColor Yellow
}
Write-Host "  • AI Foundry:      $(if ($useFoundry) {'ВКЛЮЧЁН'} else {'ВЫКЛЮЧЕН'})" -ForegroundColor White
if ($cfTunnelToken) {
    Write-Host "  • Тоннель Cloudflare: https://kino.davidka.net" -ForegroundColor Cyan
}
if ($autoLaunchEnabled -and $autoLaunchDelay -gt 0) {
    Write-Host "  • Автозапуск:      ВКЛЮЧЁН (задержка: $autoLaunchDelay сек)" -ForegroundColor Yellow
}
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray

# ============================================================================
# STAGE 8 — ПОДГОТОВКА TCP-ПОРТА
# ----------------------------------------------------------------------------
# Проверяется, занят ли выбранный порт. Если порт используется другим
# процессом, определяется его PID и процесс принудительно завершается, чтобы
# FastAPI мог занять порт без конфликта.
# ============================================================================
Write-Host ""
Write-Host "[4/5] Проверка порта $port..." -ForegroundColor Cyan

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
# STAGE 9 — ЗАПУСК СОПУТСТВУЮЩИХ СЕРВИСОВ
# ----------------------------------------------------------------------------
# После подготовки основной конфигурации запускаются сервисы, необходимые
# приложению. На текущем этапе таким сервисом является локальный Foundry,
# если он был включён пользователем или конфигурацией.
# ============================================================================
Write-Host ""
Write-Host "[5/5] Проверка сопутствующих сервисов..." -ForegroundColor Cyan

# ----------------------------------------------------------------------------
# SUBSTAGE 9.1 — MICROSOFT AI FOUNDRY
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
# SUBSTAGE 9.2 — CLOUDFLARE TUNNEL (kino.davidka.net)
# ----------------------------------------------------------------------------
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
}

Write-Host ""
Write-Host "[SUCCESS] Настройка завершена. Запуск сервера..." -ForegroundColor Green
# ============================================================================
# STAGE 10 — ЗАПУСК FASTAPI-СЕРВЕРА
# ----------------------------------------------------------------------------
# Все параметры запуска подготовлены, порт освобождён, а необходимые
# сопутствующие сервисы запущены. Управление передаётся Run-Unicorn.ps1,
# который запускает FastAPI-сервер в текущем окне PowerShell.
# ============================================================================
$env:PRELOAD_SILERO = $preloadSilero
$unicornScript = Join-Path $scriptDir "launchers\Run-Unicorn.ps1"
if (-not (Test-Path $unicornScript)) {
    $unicornScript = Join-Path $scriptDir "Run-Unicorn.ps1"
}
if (Test-Path $unicornScript) {
    Write-Host "    Запуск Run-Unicorn.ps1 с параметрами -Host_ $host_ -Port $port..." -ForegroundColor DarkGray
    & $unicornScript -Host_ $host_ -Port $port
} else {
    Write-Host "    [ERROR] Run-Unicorn.ps1 не найден: $unicornScript" -ForegroundColor Red
    exit 1
}
