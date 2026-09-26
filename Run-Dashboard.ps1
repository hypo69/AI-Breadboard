<#
.SYNOPSIS
    Запускает FastAPI-сервер AI Breadboard.

.DESCRIPTION
    Читает конфигурацию из config/dashboard.json и .env.
    Параметры -Host и -Port переопределяют значения из конфига.

.EXAMPLE
    .\Run-Dashboard.ps1
    .\Run-Dashboard.ps1 -Host 0.0.0.0 -Port 8000
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
$env:AIBREADBOARD_DIR = $scriptDir
$env:ASSIST_DIR       = $scriptDir

# ============================================================================
# ЗАГРУЗКА КОНФИГУРАЦИИ
# ============================================================================
$configPath = Join-Path $scriptDir 'start_scenarios_config\dashboard.json'
if (-not (Test-Path $configPath)) {
    $altConfig = Join-Path $scriptDir 'config\dashboard.json'
    if (Test-Path $altConfig) {
        $configPath = $altConfig
    } elseif (Test-Path (Join-Path $scriptDir 'config.json')) {
        $configPath = Join-Path $scriptDir 'config.json'
    }
}
$envFile    = Join-Path $scriptDir '.env'

# Defaults
$cfgHost        = '0.0.0.0'
$cfgPort        = '8000'
$useSsl         = $true
$useFoundry     = $false
$useOllama      = $false
$useCloudflared = $false
$cfTunnelToken  = $null
$clientUrl      = $null
$enableOAuth    = $true
$enableTelegram = $true
$enableAssist   = $false
$enableTray     = $true
$preloadSilero  = $false
$cfgAppsEnabled = @()
$cfgAppsDisabled = @()

if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json

        if ($cfg.server.host)     { $cfgHost = [string]$cfg.server.host }
        if ($cfg.server.port)     { $cfgPort = [string]$cfg.server.port }
        if ($cfg.server.protocol) { $useSsl  = $cfg.server.protocol.ToLower() -eq 'https' }
        elseif ($null -ne $cfg.server.use_ssl) { $useSsl = [bool]$cfg.server.use_ssl }

        if ($null -ne $cfg.server.use_cloudflared)   { $useCloudflared = [bool]$cfg.server.use_cloudflared }
        if ($null -ne $cfg.server.enable_oauth)       { $enableOAuth    = [bool]$cfg.server.enable_oauth }
        if ($null -ne $cfg.server.enable_telegram_bot){ $enableTelegram = [bool]$cfg.server.enable_telegram_bot }
        if ($null -ne $cfg.server.enable_assist)      { $enableAssist   = [bool]$cfg.server.enable_assist }
        if ($null -ne $cfg.server.auto_start_assist_cli) { $enableAssist = [bool]$cfg.server.auto_start_assist_cli }
        if ($null -ne $cfg.server.enable_tray)        { $enableTray     = [bool]$cfg.server.enable_tray }
        if ($cfg.server.client_url)  { $clientUrl = [string]$cfg.server.client_url }
        elseif ($cfg.server.user_domain) { $clientUrl = "https://$($cfg.server.user_domain)" }

        # Поддержка новой структуры ai.providers.*
        if ($cfg.ai.providers) {
            if ($null -ne $cfg.ai.providers.foundry.PSObject.Properties['enabled']) { 
                $useFoundry = [bool]$cfg.ai.providers.foundry.enabled 
            }
            if ($null -ne $cfg.ai.providers.ollama.PSObject.Properties['enabled']) { 
                $useOllama = [bool]$cfg.ai.providers.ollama.enabled 
            }
        }
        # Поддержка старой структуры (обратная совместимость)
        if ($null -ne $cfg.ai.PSObject.Properties['use_foundry']) { $useFoundry = [bool]$cfg.ai.use_foundry }
        if ($null -ne $cfg.ai.PSObject.Properties['use_ollama'])  { $useOllama  = [bool]$cfg.ai.use_ollama }
        if ($null -ne $cfg.ai.PSObject.Properties['preload_silero']) { $preloadSilero = [bool]$cfg.ai.preload_silero }

        if ($cfg.apps.PSObject.Properties['enabled'])  { $cfgAppsEnabled  = $cfg.apps.enabled  }
        if ($cfg.apps.PSObject.Properties['disabled']) { $cfgAppsDisabled = $cfg.apps.disabled }

        Write-Host "[OK] config/dashboard.json загружен" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Ошибка чтения config/dashboard.json: $_" -ForegroundColor Red
    }
} else {
    Write-Host "[WARN] config/dashboard.json не найден: $configPath" -ForegroundColor Yellow
}

# Переопределение из .env
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $k = $Matches[1].Trim(); $v = $Matches[2].Trim().Trim('"').Trim("'")
            switch ($k) {
                'CLOUDFLARE_TUNNEL_TOKEN' { $cfTunnelToken  = $v }
                'CLIENT_URL'             { if ($v) { $clientUrl = $v } }
                'USER_DOMAIN'            { if ($v -and -not $clientUrl) { $clientUrl = "https://$v" } }
                'USE_CLOUDFLARED'        { $useCloudflared = $v -in ('true','1','yes') }
                'ENABLE_OAUTH'           { $enableOAuth    = $v -in ('true','1','yes') }
                'ENABLE_TELEGRAM_BOT'    { $enableTelegram = $v -in ('true','1','yes') }
            }
        }
    }
}

# CLI-параметры переопределяют конфиг
$host_ = if ($HostAddress) { $HostAddress } else { $cfgHost }
$port_ = if ($Port)        { $Port }        else { $cfgPort }
$proto = if ($useSsl) { 'https' } else { 'http' }
$browserHost = if ($host_ -eq '0.0.0.0') { 'localhost' } else { $host_ }
$localUrl    = "${proto}://${browserHost}:${port_}/admin"
$openUrl     = if ($useCloudflared -and $clientUrl) { "$($clientUrl.TrimEnd('/'))/admin" } else { $localUrl }

$env:CONFIG_FILE        = if ($configPath.StartsWith($scriptDir)) { $configPath.Substring($scriptDir.Length).TrimStart('\', '/') } else { $configPath }
$env:AIBREADBOARD_CONFIG = $env:CONFIG_FILE
$env:ENABLE_OAUTH       = if ($enableOAuth)    { 'true' } else { 'false' }
$env:ENABLE_TELEGRAM_BOT = if ($enableTelegram) { 'true' } else { 'false' }
$env:PRELOAD_SILERO     = if ($preloadSilero)  { 'true' } else { 'false' }

Write-Host ""
Write-Host "  Хост:    $host_"    -ForegroundColor White
Write-Host "  Порт:    $port_"    -ForegroundColor White
Write-Host "  URL:     $openUrl"  -ForegroundColor Cyan
Write-Host "  OAuth:   $enableOAuth  | Telegram: $enableTelegram  | SSL: $useSsl" -ForegroundColor DarkGray
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
# СОПУТСТВУЮЩИЕ СЕРВИСЫ
# ============================================================================
function Start-Launcher {
    param([string]$Name, [string]$Script, [string[]]$Args = @())
    $path = Join-Path $scriptDir "launchers\$Script"
    if (-not (Test-Path $path)) { $path = Join-Path $scriptDir $Script }
    if (Test-Path $path) {
        Write-Host "  Запуск $Name..." -ForegroundColor Cyan
        & $path @Args
    } else {
        Write-Host "  [WARN] $Script не найден" -ForegroundColor Yellow
    }
}

if ($useFoundry)     { Start-Launcher 'Foundry'           'Run-Foundry.ps1'     @('-Action', 'start') }
if ($useOllama)      { Start-Launcher 'Ollama'            'Run-Ollama.ps1'      @('-Action', 'start') }
if ($useCloudflared -and $cfTunnelToken) {
                       Start-Launcher 'Cloudflare Tunnel' 'Run-Cloudflared.ps1' }
elseif ($useCloudflared) {
    Write-Host "  [WARN] use_cloudflared=true, но CLOUDFLARE_TUNNEL_TOKEN не задан в .env" -ForegroundColor Yellow
}

if (-not $enableTelegram) {
    $tgScript = Join-Path $scriptDir 'launchers\Run-TelegramBot.ps1'
    if (Test-Path $tgScript) { & $tgScript -Action stop }
}

# Запуск dedicated-приложений из apps.enabled
# launcher берётся из apps/<name>/config.json — поле "launcher"
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
        $appCfg  = Get-Content $appCfgPath -Raw | ConvertFrom-Json
        $launcher = $appCfg.launcher
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

if ($enableAssist) {
    $assistScript = Join-Path $scriptDir 'assist.ps1'
    if (Test-Path $assistScript) {
        $shell = if (Get-Command pwsh.exe -ErrorAction SilentlyContinue) { 'pwsh.exe' } else { 'powershell.exe' }
        Start-Process $shell -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$assistScript`"" -WorkingDirectory $scriptDir
    }
}

if ($enableTray) {
    $trayScript = Join-Path $scriptDir 'launchers\ShowHide-InTray.ps1'
    if (-not (Test-Path $trayScript)) { $trayScript = Join-Path $scriptDir 'ShowHide-InTray.ps1' }
    if (Test-Path $trayScript) {
        try { & $trayScript -Action start -WebUrl $openUrl -Title "AI Breadboard ($port_)" }
        catch { Write-Host "  [WARN] Трей: $_" -ForegroundColor Yellow }
    }
}

# ============================================================================
# ЗАПУСК СЕРВЕРА
# ============================================================================
$unicornScript = Join-Path $scriptDir 'launchers\Run-Unicorn.ps1'
if (-not (Test-Path $unicornScript)) { $unicornScript = Join-Path $scriptDir 'Run-Unicorn.ps1' }

if (Test-Path $unicornScript) {
    & $unicornScript -Host_ $host_ -Port $port_ -OpenUrl $openUrl `
                     -EnableOAuth $enableOAuth -EnableTelegramBot $enableTelegram `
                     -ConfigFile $configPath
} else {
    Write-Host "[ERROR] Run-Unicorn.ps1 не найден" -ForegroundColor Red
    exit 1
}
