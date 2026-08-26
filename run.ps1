<#
.SYNOPSIS
    Главный лончер проекта ai-assistant. Запускает FastAPI-сервер и сопутствующие сервисы.

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

# ============================================
# ВЫВОД СПРАВКИ (--help / -h / -Help)
# ============================================
if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║              run.ps1 — СПРАВКА И ПАРАМЕТРЫ                    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Главный интерактивный лончер проекта ai-assistant."
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

# ============================================
# АКТИВАЦИЯ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ
# ============================================
Write-Host "[1/5] Проверка виртуального окружения..." -ForegroundColor Cyan

# Явный путь к python внутри venv — не зависит от $PATH и сломанных Store-заглушек
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "    [OK] Виртуальное окружение найдено" -ForegroundColor Green
    Write-Host "    Активация..." -ForegroundColor DarkGray
    if (Test-Path $venvActivate) { . $venvActivate }
    Write-Host "    [OK] Виртуальное окружение активировано" -ForegroundColor Green

    # Берём python напрямую из venv, минуя $PATH
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

# ============================================
# ПРОВЕРКА ЗАВИСИМОСТЕЙ
# ============================================
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

# ============================================
# ЗАГРУЗКА БАЗОВОЙ КОНФИГУРАЦИИ И ОКРУЖЕНИЯ (.env)
# ============================================
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

# Чтение .env
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
            if ($key -eq "USE_FOUNDRY") { $useFoundry = $val -in ("true","1","yes") }
        }
    }
}

# Определение сетевого IP машины для подсказки
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notmatch '^(169\.254|127\.)' -and $_.InterfaceAlias -notmatch 'Loopback' } |
    Select-Object -ExpandProperty IPAddress -First 1)

# ============================================
# ИНТЕРАКТИВНЫЙ ВЫБОР ПАРАМЕТРОВ
# ============================================
$isInteractive = (-not $NonInteractive) -and (-not $HostAddress)

if ($isInteractive) {
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
        # Если пользователь сразу ввёл IP или адрес (например: 192.168.1.55 или localhost)
        $host_ = $hostChoice
    }

    # Запрос порта (если не был передан аргументом)
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

    # Интерактивный запрос запуска Foundry
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
    $host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
    $port  = if ($Port)        { $Port }        else { $cfgPort }
}

# ============================================
# ПРОВЕРКА И НАСТРОЙКА API-КЛЮЧЕЙ ИИ
# ============================================
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
            # Update .env
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
            
            # Update core/secrets/gemini_keys.json
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

$proto = if ($useSsl) { "https" } else { "http" }
$browserHost = if ($host_ -eq "0.0.0.0") { "localhost" } else { $host_ }
$url = "${proto}://${browserHost}:${port}"

Write-Host ""
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
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray

# ============================================
# ЗАВЕРШЕНИЕ ПРОЦЕССОВ НА ПОРТЕ
# ============================================
Write-Host ""
Write-Host "[4/5] Проверка порта $port..." -ForegroundColor Cyan

# Проверяем, занят ли порт
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

# ============================================
# ЗАПУСК СОПУТСТВУЮЩИХ СЕРВИСОВ
# ============================================
Write-Host ""
Write-Host "[5/5] Проверка сопутствующих сервисов..." -ForegroundColor Cyan

# ============================================
# ЗАПУСК LOCAL FOUNDRY SERVICE
# ============================================
if ($useFoundry) {
    Write-Host ""
    Write-Host "    Запуск локальной службы Foundry..." -ForegroundColor Cyan
    $foundryScript = Join-Path $scriptDir "Run-Foundry.ps1"
    if (Test-Path $foundryScript) {
        Write-Host "    Вызов Run-Foundry.ps1..." -ForegroundColor DarkGray
        & $foundryScript -Action start
    } else {
        Write-Host "    [WARN] Run-Foundry.ps1 не найден: $foundryScript" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[SUCCESS] Настройка завершена. Запуск сервера..." -ForegroundColor Green
# ЗАПУСК СЕРВЕРА В ТЕКУЩЕМ ОКНЕ (Unicorn)
# ============================================
$env:PRELOAD_SILERO = $preloadSilero
$unicornScript = Join-Path $scriptDir "Run-Unicorn.ps1"
if (Test-Path $unicornScript) {
    Write-Host "    Запуск Run-Unicorn.ps1 с параметрами -Host_ $host_ -Port $port..." -ForegroundColor DarkGray
    & $unicornScript -Host_ $host_ -Port $port
} else {
    Write-Host "    [ERROR] Run-Unicorn.ps1 не найден: $unicornScript" -ForegroundColor Red
    exit 1
}
