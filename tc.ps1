<#
.SYNOPSIS
    Standalone applications launcher for AI Breadboard (/apps microservices).

.DESCRIPTION
    Launches only the applications block (standalone /apps microservices):
    - Windows System Administrator (Port 8100)
    - Network Analyzer Terminal (Port 8101)
    - System Inspector (Port 8102)
    - Exchange Trading Terminal (Port 8103)
    - Cloudflare Tunnel Monitor (Port 8104)

.PARAMETER Action
    Action to perform: 'start' (default), 'stop', 'restart', 'status'.

.PARAMETER NewWindow
    Launch microservices in visible standalone console windows (default: $true).

.PARAMETER Background
    Launch microservices in background processes without opening visible windows.

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
    Write-Host "  Запуск ТОЛЬКО блока приложений и автономных микросервисов из /apps:"
    Write-Host "  • Windows System Administrator   (порт 8100)" -ForegroundColor White
    Write-Host "  • Network Analyzer Terminal      (порт 8101)" -ForegroundColor White
    Write-Host "  • System Inspector               (порт 8102)" -ForegroundColor White
    Write-Host "  • Exchange Trading Terminal      (порт 8103)" -ForegroundColor White
    Write-Host "  • Cloudflare Tunnel Monitor      (порт 8104)" -ForegroundColor White
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\tc.ps1 [-Action start|stop|restart|status] [-NewWindow] [-Background]"
    Write-Host "  .\tc.ps1 -Interactive"
    Write-Host "  .\tc.ps1 --help"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\tc.ps1                  # Запуск всех приложений в отдельных окнах"
    Write-Host "  .\tc.ps1 -Action status   # Проверка статуса работы всех микросервисов"
    Write-Host "  .\tc.ps1 -Action stop     # Остановка всех микросервисов"
    Write-Host "  .\tc.ps1 -Action restart  # Перезапуск всех микросервисов"
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
# STAGE 2 — ИНТЕРАКТИВНЫЙ РЕЖИМ (ЕСЛИ -Interactive)
# ============================================================================
$isInteractive = $Interactive -and (-not $NonInteractive)

if ($isInteractive) {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host " 📱 УПРАВЛЕНИЕ МИКРОСЕРВИСАМИ /apps" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "  [1] Start   - Запустить все микросервисы в отдельных окнах" -ForegroundColor White
    Write-Host "  [2] Status  - Проверить статус запущенных микросервисов" -ForegroundColor White
    Write-Host "  [3] Stop    - Остановить все запущенные микросервисы" -ForegroundColor White
    Write-Host "  [4] Restart - Перезапустить все микросервисы" -ForegroundColor White
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
# STAGE 3 — ОПРЕДЕЛЕНИЕ ПАРАМЕТРОВ ОКОН
# ============================================================================
# По умолчанию при старте/перезапуске открываются отдельные окна консоли,
# если только явно не указан флаг -Background.
$openNewWindow = $true
if ($Background) {
    $openNewWindow = $false
} elseif ($PSBoundParameters.ContainsKey('NewWindow')) {
    $openNewWindow = [bool]$NewWindow
}

# ============================================================================
# STAGE 4 — ВЫЗОВ ОРКЕСТРАТОРА ПРИЛОЖЕНИЙ (launchers/Run-Apps.ps1)
# ============================================================================
$appsLauncher = Join-Path $scriptDir "launchers\Run-Apps.ps1"
if (-not (Test-Path $appsLauncher)) {
    $appsLauncher = Join-Path $scriptDir "Run-Apps.ps1"
}

if (-not (Test-Path $appsLauncher)) {
    Write-Host "[ERROR] Run-Apps.ps1 не найден: $appsLauncher" -ForegroundColor Red
    exit 1
}

$callArgs = @{
    Action = $Action
}
if ($openNewWindow -and $Action -in @('start', 'restart')) {
    $callArgs['NewWindow'] = $true
}

& $appsLauncher @callArgs
