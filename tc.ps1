<#
=============================================================================
Process Name: AI-Breadboard Automation - Tc
=============================================================================
Description:
  Точка входа и лончер внутреннего сервера Windows System API (Terminal Controller / TC)
  с поддержкой BCP 47 локалей/регионов (?region=ru-RU, ?language-region=ru-RU)
  и переключения телеметрии реального времени (TC mode) на лету.

  Зачем нужен этот скрипт:
    1. Запуск низкоуровневого API: поднимает FastAPI сервер модуля apps/windows/api (порт 8001).
    2. Управление конфликтами портов: автоматически выявляет и освобождает занятый порт
       перед запуском сервера.
    3. Управление режимом телеметрии: активирует режим реального времени (TC mode, flush 5s)
       с авто-возвратом в стандартный режим через 5 минут.
    4. Локализация и BCP 47: поддержка передачи региона/языка в параметрах командной строки
       и маршрутизация в веб-интерфейс.

File: tc.ps1
Project: ai-breadboard
Package: root
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-08 05:30:00
=============================================================================

.SYNOPSIS
    Запуск автономного FastAPI сервера Windows System API (модуль /tc).

.DESCRIPTION
    Проверяет доступность порта 8001 (или переопределенного), завершает старые процессы
    при необходимости, активирует режим реального времени телеметрии и запускает сервер.
    Позволяет сразу передать региональные и языковые параметры интерфейса (BCP 47).

.PARAMETER HostAddress
    Сетевой адрес для прослушивания запросов (по умолчанию: 127.0.0.1).

.PARAMETER Port
    Сетевой порт сервиса (по умолчанию: 8001).

.PARAMETER LanguageRegion
    Код языка и региона по стандарту BCP 47 (например: ru-RU, he-IL, uk-UA, en-US).
    Автоматически нормализует переданные теги (ru-ru -> ru-RU).
    Алиасы: -Region, -Locale, -Lang, -Language_Region.

.PARAMETER RealtimeTelemetry
    Включить телеметрию в реальном времени (TC mode, сброс каждые 5с, автоотключение через 5 мин).
    По умолчанию: $true.

.PARAMETER DisableRealtimeTelemetry
    Принудительно оставить стандартный режим телеметрии (сброс каждые 30с, лимит 100МБ).

.PARAMETER GodMode
    Открыть специальную панель Windows God Mode (All Tasks / все настройки системы) или перевести на неё фокус.

.EXAMPLE
    .\tc.ps1
    Запуск Windows API сервера с телеметрией реального времени.

.EXAMPLE
    .\tc.ps1 -Region "ru-ru"
    Запуск с автоматическим формированием ссылки с локалью BCP 47 (ru-RU).

.EXAMPLE
    .\tc.ps1 -GodMode
    Запуск Windows API сервера и открытие/фокусировка папки God Mode.

.EXAMPLE
    .\tc.ps1 -DisableRealtimeTelemetry
    Запуск в стандартном режиме сбора телеметрии.
#>

[CmdletBinding()]
param (
    [Alias('Host', 'Address', 'IP')]
    [string]$HostAddress,

    [string]$Port,

    [Alias('Region', 'Locale', 'Lang', 'Language_Region', 'language-region')]
    [string]$LanguageRegion,

    [switch]$RealtimeTelemetry = $true,

    [switch]$DisableRealtimeTelemetry,

    [switch]$GodMode
)

$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) { $scriptDir = (Get-Location).Path }

$windowsConfig = Join-Path $scriptDir "apps\windows\config.json"
if (Test-Path $windowsConfig) {
    $env:AIBREADBOARD_CONFIG = $windowsConfig
    $env:CONFIG_FILE = $windowsConfig
    Write-Host "  [⚙️ Config Profile]: apps\windows\config.json" -ForegroundColor DarkCyan
}

$pythonExe = if ($env:PYTHON_HOME) { Join-Path $env:PYTHON_HOME 'python.exe' } else { 'python' }

$host_ = if ($HostAddress) { $HostAddress } else { '127.0.0.1' }
$port_ = if ($Port)        { $Port }        else { '8001' }

$regionQuery = ''
if ($LanguageRegion) {
    # Очистка и нормализация тега по стандарту BCP 47 (language-REGION)
    $cleanTag = $LanguageRegion.Trim().Trim("'").Trim('"').Trim('`').Replace('_', '-')
    if ($cleanTag -match '^([a-zA-Z]{2,3})(?:-([a-zA-Z]{2,4}))?$') {
        $langPart = $Matches[1].ToLower()
        $defaultRegions = @{ 
            'ru' = 'RU'
            'he' = 'IL'
            'uk' = 'UA'
            'en' = 'US'
            'de' = 'DE'
            'fr' = 'FR'
            'es' = 'ES'
            'pt' = 'BR'
            'zh' = 'CN'
            'ja' = 'JP'
        }
        $regPart = if ($Matches[2]) { 
            $Matches[2].ToUpper() 
        } elseif ($defaultRegions.ContainsKey($langPart)) { 
            $defaultRegions[$langPart] 
        } else { 
            $langPart.ToUpper() 
        }
        $normalizedTag = "${langPart}-${regPart}"
    } else {
        $normalizedTag = $cleanTag
    }
    $regionQuery = "?region=${normalizedTag}"
    Write-Host "  [🌐 BCP 47 Locale]: $normalizedTag" -ForegroundColor Cyan
}

if ($GodMode) {
    $godModeGuid = "ED7BA470-8E54-465E-825C-99712043E01C"
    $focused = $false
    try {
        $shell = New-Object -ComObject Shell.Application
        foreach ($w in $shell.Windows()) {
            $url = "$($w.LocationURL)"
            $name = "$($w.LocationName)"
            if ($url -like "*$godModeGuid*" -or $name -like "*$godModeGuid*") {
                $hwnd = $w.HWND
                if ($hwnd) {
                    $sig = '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow); [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); [DllImport("user32.dll")] public static extern void SwitchToThisWindow(IntPtr hWnd, bool fAltTab);'
                    $type = Add-Type -MemberDefinition $sig -Name "Win32Focus_$((Get-Random))" -Namespace "TC" -PassThru -ErrorAction SilentlyContinue
                    $type::ShowWindow([IntPtr]$hwnd, 9)
                    $type::SetForegroundWindow([IntPtr]$hwnd)
                    $type::SwitchToThisWindow([IntPtr]$hwnd, $true)
                    $focused = $true
                    break
                }
            }
        }
    } catch {}

    if (-not $focused) {
        $godModeFolder = Join-Path $scriptDir "bin\.{ED7BA470-8E54-465E-825C-99712043E01C}"
        if (Test-Path $godModeFolder) {
            Start-Process explorer.exe $godModeFolder
        } else {
            Start-Process explorer.exe "shell:::{ED7BA470-8E54-465E-825C-99712043E01C}"
        }
    }
    Write-Host "  [⚡ God Mode (All Tasks): активирован / переведён фокус]" -ForegroundColor Yellow
}

# Освобождаем порт если он занят
$occupied = netstat -aon 2>$null |
    Select-String ":${port_}\s" |
    ForEach-Object { ($_ -split '\s+')[-1] } |
    Where-Object { $_ -match '^\d+$' -and $_ -ne '0' } |
    Select-Object -Unique

foreach ($pid_ in $occupied) {
    try {
        Stop-Process -Id $pid_ -Force -ErrorAction Stop
        Write-Host "[OK] Освобождён занятый порт $port_ (PID $pid_)" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Не удалось завершить PID ${pid_}: $_" -ForegroundColor Yellow
    }
}

Write-Host "  [Windows Internal API] TC UI: http://${host_}:${port_}/tc${regionQuery}" -ForegroundColor Cyan

& $pythonExe -m apps.windows.api --host $host_ --port $port_