<#
.SYNOPSIS
    Сценарий запуска и управления приложением Helpdesk (Служба поддержки).

.DESCRIPTION
    Запуск интерфейса, TUI консоли и FastAPI микросервиса Helpdesk (/apps/helpdesk, /helpdesk)
    для AI Breadboard в соответствии со стандартом приложений /apps.
    Поддерживает режимы start, stop, restart, status, dedicated микросервис (порт 8110)
    или запуск основного сервера с открытием веб-интерфейса /helpdesk.

.PARAMETER Action
    Действие: 'start' (по умолчанию), 'stop', 'restart', 'status'.

.PARAMETER Mode
    Режим работы: 'web' (веб-интерфейс в браузере, по умолчанию), 'server' (микросервис FastAPI 8110), 'tui' (консольный TUI).

.PARAMETER NewWindow
    Запуск в отдельном окне/процессе.

.PARAMETER Background
    Фоновый запуск без открытия окон.

.PARAMETER ConfigFile
    Файл конфигурации (по умолчанию: config.json).

.PARAMETER Port
    Переопределение порта привязки сервера.

.PARAMETER HostAddress
    Переопределение адреса сервера.

.PARAMETER NoBrowser
    Не открывать веб-браузер автоматически.

.PARAMETER Interactive
    Запуск в интерактивном режиме с выбором действий (-i).

.PARAMETER Help
    Отображение справки по использованию (-Help, -h, --help).

.EXAMPLE
    .\helpdesk.ps1
    .\helpdesk.ps1 -Mode tui
    .\helpdesk.ps1 -Mode server
    .\helpdesk.ps1 -Action status
    .\helpdesk.ps1 -Action stop
    .\helpdesk.ps1 -Action restart
    .\helpdesk.ps1 -Interactive
    .\helpdesk.ps1 --help
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [ValidateSet('web', 'server', 'tui')]
    [string]$Mode = 'web',

    [Alias('Window', 'SeparateWindow', 'w')]
    [switch]$NewWindow,

    [Alias('bg')]
    [switch]$Background,

    [Alias('Config', 'Cfg')]
    [string]$ConfigFile = 'config.json',

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
    Write-Host "║          helpdesk.ps1 — ЛОНЧЕР СЛУЖБЫ ПОДДЕРЖКИ (HELPDESK)    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Запуск и управление приложением службы поддержки Helpdesk (/apps/helpdesk):"
    Write-Host "  • Веб-интерфейс Helpdesk          (/helpdesk, /apps#tab-helpdesk)" -ForegroundColor White
    Write-Host "  • Автономный микросервис          (Port 8110, /api/v1/helpdesk)" -ForegroundColor White
    Write-Host "  • Консольный TUI терминал         (python -m apps.helpdesk)" -ForegroundColor White
    Write-Host "  • База данных тикетов             (data/helpdesk.db)" -ForegroundColor White
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\helpdesk.ps1 [-Action start|stop|restart|status] [-Mode web|server|tui] [-Port <порт>] [-NoBrowser]"
    Write-Host "  .\helpdesk.ps1 -Interactive"
    Write-Host "  .\helpdesk.ps1 --help"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\helpdesk.ps1                         # Запуск и открытие веб-интерфейса"
    Write-Host "  .\helpdesk.ps1 -Mode tui               # Запуск интерактивного терминала оператора"
    Write-Host "  .\helpdesk.ps1 -Mode server            # Запуск автономного микросервиса на порту 8110"
    Write-Host "  .\helpdesk.ps1 -Action status          # Проверка активности Helpdesk"
    Write-Host "  .\helpdesk.ps1 -Action stop            # Остановка Helpdesk"
    Write-Host "  .\helpdesk.ps1 -Action restart         # Перезапуск Helpdesk"
    Write-Host "  .\helpdesk.ps1 -Interactive            # Интерактивное меню управления"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        AI BREADBOARD — СЛУЖБА ПОДДЕРЖКИ (HELPDESK)            ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# РЕЖИМ TUI
# ============================================================================
if ($Mode -eq 'tui') {
    $venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    }
    Push-Location $scriptDir
    & $venvPython -m apps.helpdesk
    Pop-Location
    exit $LASTEXITCODE
}

# ============================================================================
# РЕЖИМ DEDICATED SERVER (Многопроцессный микросервис 8110)
# ============================================================================
if ($Mode -eq 'server') {
    $appLauncher = Join-Path $scriptDir "launchers\Run-Helpdesk.ps1"
    if (Test-Path $appLauncher) {
        $callParams = @{
            Action = $Action
        }
        if ($Port) { $callParams['Port'] = [int]$Port }
        if ($HostAddress) { $callParams['HostAddress'] = $HostAddress }
        if ($NewWindow) { $callParams['NewWindow'] = $true }
        & $appLauncher @callParams
        exit $LASTEXITCODE
    }
}

# ============================================================================
# РЕЖИМ WEB (Интегрированный сервер и веб-интерфейс /helpdesk)
# ============================================================================
$activeConfigFile = "config.json"
if ($ConfigFile -and (Test-Path (Join-Path $scriptDir $ConfigFile))) {
    $activeConfigFile = $ConfigFile
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
$helpdeskUrl = "${proto}://${browserHost}:${port_}/helpdesk"

# ============================================================================
# ИНТЕРАКТИВНЫЙ РЕЖИМ (ЕСЛИ -Interactive)
# ============================================================================
$isInteractive = $Interactive -and (-not $NonInteractive)

if ($isInteractive) {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host " 🎫 УПРАВЛЕНИЕ ИНТЕРФЕЙСОМ СЛУЖБЫ ПОДДЕРЖКИ (HELPDESK)" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "  [1] Web     - Запустить сервер и открыть веб-интерфейс /helpdesk" -ForegroundColor White
    Write-Host "  [2] TUI     - Запустить консольный терминал оператора" -ForegroundColor White
    Write-Host "  [3] Server  - Запустить выделенный микросервис (Port 8110)" -ForegroundColor White
    Write-Host "  [4] Status  - Проверить статус сервера и доступность /helpdesk" -ForegroundColor White
    Write-Host "  [5] Stop    - Остановить сервер" -ForegroundColor White
    Write-Host "  [6] Restart - Перезапустить сервер" -ForegroundColor White
    Write-Host "  [Enter] По умолчанию: $Action ($Mode)" -ForegroundColor Green
    Write-Host ""

    $actionChoice = Read-Host "Действие [Enter = $Action]"
    $actionChoice = $actionChoice.Trim()
    if ($actionChoice -eq "1") {
        $Action = "start"; $Mode = "web"
    } elseif ($actionChoice -eq "2") {
        $Mode = "tui"
        $venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
        if (-not (Test-Path $venvPython)) { $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source }
        Push-Location $scriptDir
        & $venvPython -m apps.helpdesk
        Pop-Location
        exit $LASTEXITCODE
    } elseif ($actionChoice -eq "3") {
        $Action = "start"; $Mode = "server"
        $appLauncher = Join-Path $scriptDir "launchers\Run-Helpdesk.ps1"
        & $appLauncher -Action start
        exit $LASTEXITCODE
    } elseif ($actionChoice -eq "4") {
        $Action = "status"
    } elseif ($actionChoice -eq "5") {
        $Action = "stop"
    } elseif ($actionChoice -eq "6") {
        $Action = "restart"
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

function Open-HelpdeskBrowser {
    param([string]$Url)
    if ($NoBrowser) { return }
    Write-Host "🌐 Открытие интерфейса Helpdesk: $Url" -ForegroundColor Green
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

function Stop-ServerProcess {
    param([int]$TargetPort)
    Write-Host "🛑 Остановка процессов, занимающих порт $TargetPort..." -ForegroundColor Yellow
    try {
        $conns = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue
        if ($conns) {
            $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($p in $pids) {
                if ($p -gt 4) {
                    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                    Write-Host "  [OK] Завершен процесс PID: $p" -ForegroundColor Green
                }
            }
        } else {
            Write-Host "  [INFO] Процессов на порту $TargetPort не обнаружено." -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "  [WARN] Ошибка при остановке процессов: $_" -ForegroundColor Yellow
    }
}

$isServerRunning = Test-PortListening -CheckPort ([int]$port_)

if ($Action -eq 'status') {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    if ($isServerRunning) {
        Write-Host "✅ Интерфейс Helpdesk активен: $helpdeskUrl" -ForegroundColor Green
    } else {
        Write-Host "❌ Сервер на порту $port_ не запущен." -ForegroundColor Yellow
        Write-Host "   Для запуска выполните: .\helpdesk.ps1" -ForegroundColor DarkGray
    }

    $isAppProcRunning = Test-PortListening -CheckPort 8110
    if ($isAppProcRunning) {
        Write-Host "✅ Выделенный микросервис Helpdesk (Port 8110) активен: http://127.0.0.1:8110" -ForegroundColor Green
    }
    Write-Host ""
    exit 0
}

if ($Action -eq 'stop') {
    Stop-ServerProcess -TargetPort ([int]$port_)
    $runHelpdesk = Join-Path $scriptDir "launchers\Run-Helpdesk.ps1"
    if (Test-Path $runHelpdesk) {
        & $runHelpdesk -Action stop
    }
    Write-Host "✅ Остановка Helpdesk завершена." -ForegroundColor Green
    exit 0
}

if ($Action -eq 'restart') {
    if ($isServerRunning) {
        Stop-ServerProcess -TargetPort ([int]$port_)
        Start-Sleep -Seconds 1
    }
    $isServerRunning = $false
}

if ($Action -in @('start', 'restart')) {
    if ($isServerRunning) {
        Write-Host "✅ Сервер уже работает на порту $port_." -ForegroundColor Green
        Open-HelpdeskBrowser -Url $helpdeskUrl
    } else {
        Write-Host "🚀 Запуск сервера с интерфейсом Helpdesk..." -ForegroundColor Cyan
        Write-Host "   URL интерфейса: $helpdeskUrl" -ForegroundColor Green
        Write-Host ""

        $unicornScript = Join-Path $scriptDir "launchers\Run-Unicorn.ps1"
        if (-not (Test-Path $unicornScript)) {
            $unicornScript = Join-Path $scriptDir "Run-Unicorn.ps1"
        }

        if (Test-Path $unicornScript) {
            $unicornCallArgs = @{
                Host_       = $host_
                Port        = $port_
                OpenUrl     = $helpdeskUrl
                EnableOAuth = $false
            }
            & $unicornScript @unicornCallArgs
        } else {
            Write-Host "[ERROR] Run-Unicorn.ps1 не найден: $unicornScript" -ForegroundColor Red
            exit 1
        }
    }
}
