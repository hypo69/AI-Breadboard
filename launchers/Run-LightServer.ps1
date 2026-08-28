<#
.SYNOPSIS
    Запуск облегченного локального сервера проекта ai-breadboard.

.DESCRIPTION
    Активирует виртуальное окружение, освобождает порт при необходимости и запускает
    локальный сервер FastAPI/uvicorn в облегченном режиме (1 воркер, без внешних туннелей).

.PARAMETER mode
    Режим привязки хоста:
    - '0.0.0.0' (по умолчанию): доступен со всех сетевых интерфейсов и устройств в локальной сети
    - 'localhost': доступен только локально (127.0.0.1)

.PARAMETER port
    Порт сервера (по умолчанию 8000 или из config.json).

.PARAMETER Help
    Отображение справки по использованию скрипта (-Help, -h, --help, -?).

.EXAMPLE
    .\Run-LightServer.ps1
    .\Run-LightServer.ps1 -mode 0.0.0.0
    .\Run-LightServer.ps1 -mode localhost
    .\Run-LightServer.ps1 -mode 0.0.0.0 -port 8000
    .\Run-LightServer.ps1 --help
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [ValidateSet('localhost', '0.0.0.0', '127.0.0.1', 'help', '-h', '--help', '-help')]
    [string]$mode = '0.0.0.0',

    [Parameter(Position = 1)]
    [int]$port = 0,

    [Alias('h', '-help')]
    [switch]$Help
)

$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# ============================================
# ВЫВОД СПРАВКИ (--help / -h / -Help / help)
# ============================================
if ($Help -or $mode -in @('help', '-h', '--help', '-help')) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║       Run-LightServer.ps1 — СПРАВКА И ПАРАМЕТРЫ               ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Запуск облегченного сервера FastAPI/uvicorn (1 воркер, без внешних туннелей)."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\Run-LightServer.ps1 [-mode <0.0.0.0|localhost>] [-port <порт>]"
    Write-Host "  .\Run-LightServer.ps1 --help"
    Write-Host ""
    Write-Host "ПАРАМЕТРЫ:" -ForegroundColor Yellow
    Write-Host "  -mode <string>      Режим привязки IP (по умолчанию: 0.0.0.0):"
    Write-Host "                        0.0.0.0               — доступ со всех устройств локальной сети."
    Write-Host "                        localhost / 127.0.0.1 — только для локального ПК."
    Write-Host "  -port <int>         Порт сервера (по умолчанию: из config.json или 8000)."
    Write-Host "  -Help, -h, --help   Показать эту справку и выйти."
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\Run-LightServer.ps1"
    Write-Host "  .\Run-LightServer.ps1 -mode localhost"
    Write-Host "  .\Run-LightServer.ps1 -mode 0.0.0.0"
    Write-Host "  .\Run-LightServer.ps1 -mode 0.0.0.0 -port 8000"
    Write-Host "  .\Run-LightServer.ps1 --help"
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

$venvPython   = Join-Path $projectRoot "venv\Scripts\python.exe"
$venvActivate = Join-Path $projectRoot "venv\Scripts\Activate.ps1"
$configPath   = Join-Path $projectRoot "config.json"
$envFile      = Join-Path $projectRoot ".env"
$env:AIBREADBOARD_DIR = $projectRoot
$env:ASSIST_DIR = $projectRoot

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         ЗАПУСК ЛОКАЛЬНОГО СЕРВЕРА (LIGHT)                     ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# [1/4] АКТИВАЦИЯ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ
# ============================================
Write-Host "[1/4] Проверка виртуального окружения..." -ForegroundColor Cyan
if (Test-Path $venvPython) {
    if (Test-Path $venvActivate) { . $venvActivate }
    Write-Host "    [OK] venv активирован: $venvPython" -ForegroundColor Green
} else {
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $venvPython) {
        Write-Host "    [ERROR] Python не найден! Запустите install.cmd" -ForegroundColor Red
        exit 1
    }
    Write-Host "    [WARN] venv не найден, используется: $venvPython" -ForegroundColor Yellow
}

# ============================================
# [2/4] КОНФИГУРАЦИЯ СЕРВЕРА
# ============================================
# Определение IP привязки на основе параметра -mode
if ($mode -eq '0.0.0.0') {
    $host_ = '0.0.0.0'
} else {
    $host_ = '127.0.0.1'
}

# Значения по умолчанию
$defaultPort = 8000
$workers     = 1
$useSsl      = $false
$debugMode   = "dev"

# Чтение config.json
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($port -eq 0 -and $cfg.server.port) {
            $port = [int]$cfg.server.port
        }
        if ($cfg.server.use_ssl -ne $null) {
            $useSsl = [bool]$cfg.server.use_ssl
        }
    } catch {}
}

if ($port -eq 0) {
    $port = $defaultPort
}

# Чтение .env
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "USE_SSL") { $useSsl = $val -in ("true","1","yes") }
            if ($key -eq "MODE") { $debugMode = $val.ToLower() }
        }
    }
}

Write-Host "    Режим (mode): $mode ($host_)" -ForegroundColor Gray
Write-Host "    Порт:         $port" -ForegroundColor Gray
Write-Host "    SSL:          $(if ($useSsl) { 'ВКЛЮЧЁН' } else { 'ВЫКЛЮЧЕН' })" -ForegroundColor Gray

# ============================================
# [3/4] ОСВОБОЖДЕНИЕ ПОРТА
# ============================================
Write-Host ""
Write-Host "[2/4] Проверка и освобождение порта $port..." -ForegroundColor Cyan
try {
    $conns = Get-NetTCPConnection -LocalPort ([int]$port) -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns.OwningProcess | Select-Object -Unique
        Write-Host "    [WARN] Порт занят. Завершение PID: $pids" -ForegroundColor Yellow
        $pids | Where-Object { $_ -gt 0 } | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    } else {
        Write-Host "    [OK] Порт свободен" -ForegroundColor Green
    }
} catch {
    Write-Host "    [WARN] Не удалось проверить порт: $_" -ForegroundColor Yellow
}

# ============================================
# [4/4] ПОДГОТОВКА И ЗАПУСК UVICORN
# ============================================
Write-Host ""
Write-Host "[3/4] Подготовка uvicorn (Light-режим, 1 воркер)..." -ForegroundColor Cyan

$uvicornArgs = @(
    "-m", "uvicorn",
    "main:app",
    "--host", $host_,
    "--port", [string]$port,
    "--workers", [string]$workers,
    "--loop", "asyncio"
)

if ($debugMode -in @("dev", "debug")) {
    $uvicornArgs += "--log-level", "debug"
} else {
    $uvicornArgs += "--log-level", "info"
}

# SSL сертификаты
$proto = "http"
if ($useSsl) {
    $certsDir = Join-Path $env:USERPROFILE ".certs"
    $certFile = Join-Path $certsDir "localhost+2.pem"
    $keyFile  = Join-Path $certsDir "localhost+2-key.pem"
    if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
        $uvicornArgs += "--ssl-certfile", $certFile, "--ssl-keyfile", $keyFile
        $proto = "https"
        Write-Host "    SSL: включён ($certFile)" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Сертификаты не найдены — запуск по HTTP" -ForegroundColor Yellow
    }
}

$url = "${proto}://${host_}:${port}"

# Определение сетевого IP для устройств в локальной сети
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notmatch '^(169\.254|127\.)' -and $_.InterfaceAlias -notmatch 'Loopback' } |
    Select-Object -ExpandProperty IPAddress -First 1)

# Для локального браузера используем localhost (валидный для SSL-сертификата)
$browserUrl = "${proto}://localhost:${port}/"

Write-Host "    Команда: $venvPython $($uvicornArgs -join ' ')" -ForegroundColor Gray
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ЛОКАЛЬНЫЙ СЕРВЕР ГОТОВ К РАБОТЕ                              ║" -ForegroundColor Cyan
Write-Host "║  Режим:           -mode $mode                                ║" -ForegroundColor Cyan
Write-Host "║  Локальный адрес: ${proto}://localhost:${port}/                      ║" -ForegroundColor Green
if ($lanIp -and $mode -eq '0.0.0.0') {
Write-Host "║  Сетевой адрес:   ${proto}://${lanIp}:${port}/                ║" -ForegroundColor Yellow
}
Write-Host "║  (без внешних туннелей, 1 воркер, Ctrl+C для остановки)       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""


$logsDir = Join-Path $projectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}
$logFilePath = Join-Path $logsDir "uvicorn_light.log"

$argStr = ($uvicornArgs | ForEach-Object { "`"$_`"" }) -join " "
$cmdToRun = "`"$venvPython`" $argStr 2>&1"

# Фоновый watcher: ждет готовности TCP-порта и мгновенно открывает браузер
Start-Job -ScriptBlock {
    param($targetPort, $targetOpenUrl)
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
        Start-Process $targetOpenUrl
    }
} -ArgumentList ([int]$port), $browserUrl | Out-Null

Write-Host "[INFO] Сервер запускается. Браузер откроется автоматически: $browserUrl" -ForegroundColor Green
Write-Host "[INFO] Запуск uvicorn в текущем окне..." -ForegroundColor Green
Push-Location $projectRoot
cmd /c $cmdToRun | Tee-Object -FilePath $logFilePath
Pop-Location

