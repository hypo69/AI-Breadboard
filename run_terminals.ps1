<#
.SYNOPSIS
    Главный лончер мульти-терминального пространства AI Breadboard и Trading Control Desk.

.DESCRIPTION
    Запускает рабочую среду терминалов (в едином окне Windows Terminal с разделением на панели,
    в отдельных вкладках или в отдельных окнах). Поддерживает интерактивный выбор пресетов
    (AI Breadboard, Биржевой пульт управления, кастомный набор).

.PARAMETER Preset
    Предустановленный набор терминалов:
    - 'breadboard': Сервер FastAPI, Assist CLI, Telegram-бот, Live-логи.
    - 'trading': Биржевой пульт (стакан, тикеры, сделки, PnL, Kill-Switch).
    - 'custom': Выбор в интерактивном режиме.
    По умолчанию: 'breadboard'.

.PARAMETER Layout
    Расположение терминалов:
    - 'grid': Сетка разделения экрана (Split-panes в Windows Terminal)
    - 'tabs': Вкладки в одном окне
    - 'windows': Отдельные независимые окна
    По умолчанию: 'grid'.

.PARAMETER Interactive
    Включить интерактивный диалоговый режим с вопросами пользователю (-i).

.PARAMETER Help
    Отображение справки (-Help, -h, --help).

.EXAMPLE
    .\run_terminals.ps1
    .\run_terminals.ps1 -Preset trading
    .\run_terminals.ps1 -Preset breadboard -Layout tabs
    .\run_terminals.ps1 -Interactive
    .\run_terminals.ps1 --help
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [ValidateSet('breadboard', 'trading', 'network', 'custom')]
    [string]$Preset = 'breadboard',

    [Parameter(Position = 1)]
    [ValidateSet('grid', 'split', 'tabs', 'windows')]
    [string]$Layout = 'grid',

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
    Write-Host "║          run_terminals.ps1 — СПРАВКА И ПАРАМЕТРЫ              ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Лончер мульти-терминального пространства AI Breadboard и Trading Desk."
    Write-Host "  Объединяет сервисы в единое окно Windows Terminal (сплит-сетка / вкладки)"
    Write-Host "  или запускает отдельные консольные окна."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\run_terminals.ps1 [-Preset <breadboard|trading|network|custom>] [-Layout <grid|tabs|windows>]"
    Write-Host "  .\run_terminals.ps1 -Interactive"
    Write-Host "  .\run_terminals.ps1 --help"
    Write-Host ""
    Write-Host "ПРЕСЕТЫ:" -ForegroundColor Yellow
    Write-Host "  breadboard  Основной стек: FastAPI Unicorn + Assist CLI + Telegram Bot + Logs"
    Write-Host "  trading     Биржевой пульт: Стакан & Тикеры + Ордера + Монитор PnL/Позиций"
    Write-Host "  network     Сетевой терминал: TShark DPI + Поток пакетов + AI Аномалии"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        ЗАПУСК МУЛЬТИ-ТЕРМИНАЛЬНОГО ОКНА (ai-breadboard)       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STAGE 2 — ИНТЕРАКТИВНЫЙ ВЫБОР (ЕСЛИ -Interactive)
# ============================================================================
$isInteractive = $Interactive -and (-not $NonInteractive)

if ($isInteractive) {
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host " 🖥️ ВЫБОР ПРЕСЕТА РАБОЧЕГО ОКНА" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "  [1] AI Breadboard Core   (FastAPI + Assist CLI + Telegram Bot + Logs)" -ForegroundColor White
    Write-Host "  [2] Trading Control Desk (BTC/USDT & ETH/USDT терминалы + Event Feed)" -ForegroundColor White
    Write-Host "  [3] Network Terminal     (TShark Packet Capture + AI Diagnostics)" -ForegroundColor White
    Write-Host "  [Enter] По умолчанию: $Preset" -ForegroundColor Green
    Write-Host ""

    $pChoice = Read-Host "Выберите пресет [Enter = $Preset]"
    $pChoice = $pChoice.Trim()
    if ($pChoice -eq "1") {
        $Preset = "breadboard"
    } elseif ($pChoice -eq "2") {
        $Preset = "trading"
    } elseif ($pChoice -eq "3") {
        $Preset = "network"
    }

    Write-Host ""
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host " 📐 ВЫБОР РАСПОЛОЖЕНИЯ ТЕРМИНАЛОВ" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "  [1] Grid (Сетка панелей в одном окне Windows Terminal)" -ForegroundColor White
    Write-Host "  [2] Tabs (Вкладки в одном окне Windows Terminal)" -ForegroundColor White
    Write-Host "  [3] Windows (Отдельные независимые окна консоли)" -ForegroundColor White
    Write-Host "  [Enter] По умолчанию: $Layout" -ForegroundColor Green
    Write-Host ""

    $lChoice = Read-Host "Выберите расположение [Enter = $Layout]"
    $lChoice = $lChoice.Trim()
    if ($lChoice -eq "1") {
        $Layout = "grid"
    } elseif ($lChoice -eq "2") {
        $Layout = "tabs"
    } elseif ($lChoice -eq "3") {
        $Layout = "windows"
    }
}

# ============================================================================
# STAGE 3 — ДЕЛЕГИРОВАНИЕ В launchers/Run-Terminals.ps1
# ============================================================================
$terminalLauncher = Join-Path $scriptDir "launchers\Run-Terminals.ps1"
if (-not (Test-Path $terminalLauncher)) {
    Write-Host "[ERROR] Run-Terminals.ps1 не найден: $terminalLauncher" -ForegroundColor Red
    exit 1
}

& $terminalLauncher -Preset $Preset -Layout $Layout
