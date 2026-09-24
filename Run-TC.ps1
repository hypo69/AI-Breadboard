<#
.SYNOPSIS
    Запускает блок приложений Test Computer (AI Breadboard /tc).

.DESCRIPTION
    Читает конфигурацию из config/tc.json.
    Параметры -Host и -Port переопределяют значения из конфига.

.EXAMPLE
    .\Run-TC.ps1
    .\Run-TC.ps1 -Host 127.0.0.1 -Port 8080
#>

[CmdletBinding()]
param (
    [Alias('Host', 'Address', 'IP')]
    [string]$HostAddress,

    [string]$Port
)

$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) { $scriptDir = (Get-Location).Path }
$env:AIBREADBOARD_DIR  = $scriptDir
$env:ASSIST_DIR        = $scriptDir
$env:ENABLE_OAUTH      = 'false'
$env:DISABLE_AUTH      = 'true'

# ============================================================================
# ЗАГРУЗКА КОНФИГУРАЦИИ
# ============================================================================
$configPath = Join-Path $scriptDir 'start_scenarios_config\tc.json'
if (-not (Test-Path $configPath)) {
    $altConfig = Join-Path $scriptDir 'config\tc.json'
    if (Test-Path $altConfig) {
        $configPath = $altConfig
    }
}

# Defaults
$cfgHost       = '127.0.0.1'
$cfgPort       = '8000'
$useSsl        = $true
$enableTray    = $true
$cfgAppsEnabled  = @()
$cfgAppsDisabled = @()

if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json

        if ($cfg.server.host)     { $cfgHost = [string]$cfg.server.host }
        if ($cfg.server.port)     { $cfgPort = [string]$cfg.server.port }
        if ($cfg.server.protocol) { $useSsl  = $cfg.server.protocol.ToLower() -eq 'https' }
        elseif ($null -ne $cfg.server.use_ssl) { $useSsl = [bool]$cfg.server.use_ssl }
        if ($null -ne $cfg.server.enable_tray) { $enableTray = [bool]$cfg.server.enable_tray }

        if ($cfg.apps.PSObject.Properties['enabled'])  { $cfgAppsEnabled  = $cfg.apps.enabled  }
        if ($cfg.apps.PSObject.Properties['disabled']) { $cfgAppsDisabled = $cfg.apps.disabled }

        # AI-переменные окружения для провайдеров
        if ($cfg.ai.provider)          { $env:AI_PROVIDER         = $cfg.ai.provider }
        if ($cfg.ai.gemini.model)      { $env:AI_GEMINI_MODEL      = $cfg.ai.gemini.model }
        if ($cfg.ai.gemini_cli.model)  { $env:AI_GEMINI_CLI_MODEL  = $cfg.ai.gemini_cli.model }
        if ($cfg.ai.agy.model)         { $env:AI_AGY_MODEL         = $cfg.ai.agy.model }
        if ($cfg.ai.agy.effort)        { $env:AI_AGY_EFFORT        = $cfg.ai.agy.effort }

        $cfgRelative = if ($configPath.StartsWith($scriptDir)) { $configPath.Substring($scriptDir.Length).TrimStart('\', '/') } else { $configPath }
        Write-Host "[OK] $cfgRelative загружен" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Ошибка чтения конфигурации ($configPath): $_" -ForegroundColor Red
    }
} else {
    Write-Host "[WARN] Файл конфигурации не найден: $configPath" -ForegroundColor Yellow
}

$env:CONFIG_FILE         = if ($configPath.StartsWith($scriptDir)) { $configPath.Substring($scriptDir.Length).TrimStart('\', '/') } else { 'start_scenarios_config/tc.json' }
$env:AIBREADBOARD_CONFIG = $env:CONFIG_FILE

$host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
$port_ = if ($Port)        { $Port }        else { $cfgPort }
$proto = if ($useSsl) { 'https' } else { 'http' }
$browserHost = if ($host_ -eq '0.0.0.0') { 'localhost' } else { $host_ }
$tcUrl = "${proto}://${browserHost}:${port_}/tc"

Write-Host ""
Write-Host "  Хост:  $host_"  -ForegroundColor White
Write-Host "  Порт:  $port_"  -ForegroundColor White
Write-Host "  URL:   $tcUrl"  -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# ОСВОБОЖДЕНИЕ ПОРТА
# ============================================================================
$occupied = netstat -aon 2>$null |
    Select-String ":${port_}\s" |
    ForEach-Object { ($_ -split '\s+')[-1] } |
    Where-Object { $_ -match '^\d+$' -and $_ -ne '0' } |
    Select-Object -Unique

foreach ($pid_ in $occupied) {
    try {
        Stop-Process -Id $pid_ -Force -ErrorAction Stop
        Write-Host "[OK] Освобождён порт $port_ (PID $pid_)" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Не удалось завершить PID ${pid_}: $_" -ForegroundColor Yellow
    }
}

# ============================================================================
# ЗАПУСК DEDICATED-ПРИЛОЖЕНИЙ
# launcher и server.dedicated берутся из apps/<name>/config.json
# ============================================================================
$launchersDir = Join-Path $scriptDir 'launchers'

foreach ($appName in $cfgAppsEnabled) {
    if ($cfgAppsDisabled -contains $appName) { continue }

    $appCfgPath = @(
        (Join-Path $scriptDir "apps\$appName\config.json"),
        (Join-Path $scriptDir "apps\windows\$appName\config.json"),
        (Join-Path $scriptDir "src\apps\$appName\config.json")
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $appCfgPath) { continue }

    try {
        $appCfg   = Get-Content $appCfgPath -Raw | ConvertFrom-Json
        $launcher  = $appCfg.launcher
        $dedicated = $appCfg.server.dedicated -eq $true
        if (-not $dedicated -and $appCfg.server.mode) {
            $dedicated = $appCfg.server.mode.ToLower() -eq 'dedicated'
        }
    } catch { continue }

    if ($dedicated -and $launcher) {
        $launcherPath = Join-Path $launchersDir $launcher
        if (Test-Path $launcherPath) {
            Write-Host "  Запуск $appName (dedicated)..." -ForegroundColor Cyan
            & $launcherPath -Action start -NewWindow
        } else {
            Write-Host "  [WARN] Лончер не найден: $launcherPath" -ForegroundColor Yellow
        }
    }
}

# ============================================================================
# LibreHardwareMonitor (фоновый сбор аппаратных метрик)
# ============================================================================
$lhmScript = Join-Path $scriptDir 'launchers\Run-LHM.ps1'
if (Test-Path $lhmScript) {
    Write-Host "  Запуск LibreHardwareMonitor..." -ForegroundColor Cyan
    & $lhmScript -Action start
}

# ============================================================================
# СИСТЕМНЫЙ ТРЕЙ
# ============================================================================
if ($enableTray) {
    $trayScript = Join-Path $scriptDir 'launchers\ShowHide-InTray.ps1'
    if (-not (Test-Path $trayScript)) { $trayScript = Join-Path $scriptDir 'ShowHide-InTray.ps1' }
    if (Test-Path $trayScript) {
        try { & $trayScript -Action start -WebUrl $tcUrl -Title "AI Breadboard TC ($port_)" }
        catch { Write-Host "  [WARN] Трей: $_" -ForegroundColor Yellow }
    }
}

# ============================================================================
# ЗАПУСК СЕРВЕРА
# ============================================================================
$unicornScript = Join-Path $scriptDir 'launchers\Run-Unicorn.ps1'
if (-not (Test-Path $unicornScript)) { $unicornScript = Join-Path $scriptDir 'Run-Unicorn.ps1' }

if (Test-Path $unicornScript) {
    & $unicornScript -Host_ $host_ -Port $port_ -OpenUrl $tcUrl `
                     -EnableOAuth $false -ConfigFile $configPath
} else {
    Write-Host "[ERROR] Run-Unicorn.ps1 не найден" -ForegroundColor Red
    exit 1
}
