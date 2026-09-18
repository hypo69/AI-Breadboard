<#
.SYNOPSIS
    Лончер для LibreHardwareMonitor (LHM) в скрытом/фоновом режиме.

.DESCRIPTION
    Запускает LibreHardwareMonitor.exe в фоновом режиме со скрытым окном,
    позволяет управлять процессами (start, stop, restart, status) и проверять
    доступность локального веб-сервера JSON API (http://127.0.0.1:8085/data.json).

.PARAMETER Action
    Действие: 'start' (по умолчанию), 'stop', 'restart', 'status'.

.PARAMETER Port
    Порт веб-сервера LHM (по умолчанию: 8085).

.PARAMETER HostAddress
    Адрес веб-сервера LHM (по умолчанию: 127.0.0.1).

.PARAMETER Method
    Способ запуска:
    - 'Standard' (по умолчанию): Start-Process с -WindowStyle Hidden и аргументами /sensors, /minimized.
    - 'Win32Hide': Запуск + принудительное скрытие окна через Win32 ShowWindow(SW_HIDE).
    - 'Wmi': Создание процесса через WMI (Win32_Process).

.PARAMETER Check
    Проверить доступность REST API веб-сервера (http://127.0.0.1:8085/data.json).

.PARAMETER Foreground
    Запустить в обычном видимом окне (для начальной настройки GUI и включения Remote Web Server).

.PARAMETER Help
    Показать справочную информацию.

.EXAMPLE
    .\launchers\Run-LHM.ps1
    .\launchers\Run-LHM.ps1 -Action status
    .\launchers\Run-LHM.ps1 -Action stop
    .\launchers\Run-LHM.ps1 -Method Win32Hide
    .\launchers\Run-LHM.ps1 -Foreground
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',

    [int]$Port = 8085,

    [Alias('Host', 'Address', 'IP')]
    [string]$HostAddress = '127.0.0.1',

    [ValidateSet('Standard', 'Win32Hide', 'Wmi')]
    [string]$Method = 'Standard',

    [switch]$Check,

    [Alias('Visible', 'Gui')]
    [switch]$Foreground,

    [Alias('h', '-help')]
    [switch]$Help
)

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Определение директории проекта
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

$projectRoot = $scriptDir
if ((Split-Path -Leaf $projectRoot) -eq "launchers" -or -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if ((Test-Path (Join-Path $parent "main.py")) -or (Test-Path (Join-Path $parent "bin\LibreHardwareMonitor"))) {
        $projectRoot = $parent
    }
}

$lhmExe = Join-Path $projectRoot "bin\LibreHardwareMonitor\LibreHardwareMonitor.exe"
$lhmUrl = "http://${HostAddress}:${Port}/data.json"

if ($Help) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          Run-LHM.ps1 — LibreHardwareMonitor Launcher          ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "НАЗНАЧЕНИЕ:" -ForegroundColor Yellow
    Write-Host "  Фоновый/скрытый запуск и управление LibreHardwareMonitor."
    Write-Host ""
    Write-Host "СИНТАКСИС:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-LHM.ps1 [-Action start|stop|restart|status] [-Method Standard|Win32Hide|Wmi] [-Port 8085] [-Check] [-Foreground]"
    Write-Host ""
    Write-Host "ПРИМЕРЫ:" -ForegroundColor Yellow
    Write-Host "  .\launchers\Run-LHM.ps1                        # Скрытый запуск по умолчанию"
    Write-Host "  .\launchers\Run-LHM.ps1 -Action status        # Проверка статуса и веб-сервера"
    Write-Host "  .\launchers\Run-LHM.ps1 -Action stop          # Остановка всех процессов LHM"
    Write-Host "  .\launchers\Run-LHM.ps1 -Foreground           # Видимое окно (для первой настройки)"
    Write-Host ""
    exit 0
}

# Проверка наличия бинарника
if (-not (Test-Path $lhmExe)) {
    Write-Host "❌ Исполняемый файл LHM не найден по пути: $lhmExe" -ForegroundColor Red
    exit 1
}

# Функция проверки прав администратора
function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    Write-Host "⚠️ Внимание: Скрипт запущен без прав администратора." -ForegroundColor Yellow
    Write-Host "   Некоторые аппаратные датчики LHM (CPU/GPU/чипсет) могут быть недоступны." -ForegroundColor DarkGray
}

# Функция получения запущенных процессов LHM
function Get-LHMProcesses {
    Get-Process -Name "LibreHardwareMonitor" -ErrorAction SilentlyContinue
}

# Функция проверки веб-сервера LHM
function Test-LHMWebServer {
    param([int]$TimeoutSeconds = 3)
    try {
        $response = Invoke-RestMethod -Uri $lhmUrl -TimeoutSec $TimeoutSeconds -ErrorAction Stop
        return @{ Success = $true; Data = $response }
    } catch {
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

$running = Get-LHMProcesses

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STATUS
# -------------------------------------------------------------
if ($Action -eq 'status') {
    Write-Host ""
    if ($running) {
        $pids = ($running | ForEach-Object { $_.Id }) -join ', '
        Write-Host "✅ LibreHardwareMonitor запущен (PID: $pids)" -ForegroundColor Green
        
        Write-Host "🔍 Проверка веб-сервера ($lhmUrl)..." -ForegroundColor Cyan
        $testResult = Test-LHMWebServer -TimeoutSeconds 3
        if ($testResult.Success) {
            $nodesCount = 0
            if ($testResult.Data -and $testResult.Data.Children) {
                $nodesCount = $testResult.Data.Children.Count
            }
            Write-Host "   [OK] Веб-сервер LHM активен и отвечает! Дочерних элементов: $nodesCount" -ForegroundColor Green
        } else {
            Write-Host "   [WARN] Веб-сервер LHM не отвечает: $($testResult.Error)" -ForegroundColor Yellow
            Write-Host "   Подсказка: Включите 'Options -> Remote Web Server -> Run' в GUI LHM." -ForegroundColor DarkGray
        }
    } else {
        Write-Host "❌ LibreHardwareMonitor не запущен." -ForegroundColor Yellow
    }
    Write-Host ""
    exit 0
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: STOP / RESTART
# -------------------------------------------------------------
if ($Action -in @('stop', 'restart')) {
    if ($running) {
        Write-Host "🛑 Остановка LibreHardwareMonitor..." -ForegroundColor Yellow
        $running | ForEach-Object {
            try {
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                Write-Host "   [OK] Остановлен PID $($_.Id)" -ForegroundColor DarkGray
            } catch {}
        }
        Start-Sleep -Milliseconds 800
    } else {
        Write-Host "ℹ️ LibreHardwareMonitor не был запущен." -ForegroundColor DarkGray
    }
    if ($Action -eq 'stop') {
        exit 0
    }
}

# -------------------------------------------------------------
# ДЕЙСТВИЕ: START / RESTART
# -------------------------------------------------------------
if ($Action -in @('start', 'restart')) {
    $existing = Get-LHMProcesses
    if ($existing) {
        $pids = ($existing | ForEach-Object { $_.Id }) -join ', '
        Write-Host "✅ LibreHardwareMonitor уже работает (PID: $pids)" -ForegroundColor Green
        if ($Check) {
            $testResult = Test-LHMWebServer -TimeoutSeconds 3
            if ($testResult.Success) {
                Write-Host "   [OK] Веб-сервер ($lhmUrl) доступен." -ForegroundColor Green
            } else {
                Write-Host "   [WARN] Веб-сервер ($lhmUrl) не отвечает." -ForegroundColor Yellow
            }
        }
        exit 0
    }

    Write-Host "🚀 Запуск LibreHardwareMonitor..." -ForegroundColor Cyan

    $proc = $null

    if ($Foreground) {
        # Запуск в видимом окне (GUI)
        Write-Host "   Режим: Видимый интерфейс (GUI)" -ForegroundColor DarkGray
        $proc = Start-Process -FilePath $lhmExe -WorkingDirectory (Split-Path -Parent $lhmExe) -PassThru
    }
    elseif ($Method -eq 'Wmi') {
        # Способ 3: Запуск через WMI (Win32_Process)
        Write-Host "   Способ: WMI (Win32_Process Create)" -ForegroundColor DarkGray
        $cmdLine = "`"$lhmExe`" /sensors /minimized"
        $wmiResult = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList $cmdLine
        if ($wmiResult.ReturnValue -eq 0) {
            $pId = $wmiResult.ProcessId
            $proc = Get-Process -Id $pId -ErrorAction SilentlyContinue
        } else {
            Write-Host "❌ Ошибка WMI при запуске: $($wmiResult.ReturnValue)" -ForegroundColor Red
        }
    }
    elseif ($Method -eq 'Win32Hide') {
        # Способ 2: Запуск + Win32 ShowWindow(SW_HIDE)
        Write-Host "   Способ: Win32 ShowWindow Hide" -ForegroundColor DarkGray
        $proc = Start-Process -FilePath $lhmExe `
                              -ArgumentList "/sensors","/minimized" `
                              -WorkingDirectory (Split-Path -Parent $lhmExe) `
                              -PassThru

        Start-Sleep -Seconds 2

        try {
            $win32Type = Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class LHMWin32 {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
}
"@ -PassThru -ErrorAction SilentlyContinue
            
            $hwnd = [LHMWin32]::FindWindow($null, "Libre Hardware Monitor")
            if ($hwnd -ne [IntPtr]::Zero) {
                [LHMWin32]::ShowWindow($hwnd, 0) | Out-Null
                Write-Host "   [OK] Окно LHM успешно скрыто." -ForegroundColor Green
            }
        } catch {
            Write-Host "   [WARN] Не удалось скрыть окно через Win32 API." -ForegroundColor Yellow
        }
    }
    else {
        # Способ 1: Стандартный скрытый запуск (Start-Process -WindowStyle Hidden)
        Write-Host "   Способ: Start-Process -WindowStyle Hidden" -ForegroundColor DarkGray
        $proc = Start-Process -FilePath $lhmExe `
                              -ArgumentList "/sensors","/minimized" `
                              -WorkingDirectory (Split-Path -Parent $lhmExe) `
                              -WindowStyle Hidden `
                              -PassThru
    }

    if ($proc) {
        Write-Host "✅ LibreHardwareMonitor запущен (PID: $($proc.Id))" -ForegroundColor Green
        
        # Ждем запуска веб-сервера
        Write-Host "⏳ Ожидание инициализации веб-сервера..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 3

        $testResult = Test-LHMWebServer -TimeoutSeconds 3
        if ($testResult.Success) {
            Write-Host ""
            Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
            Write-Host "  ✅ LHM СЕРВЕР ДАННЫХ ГОТОВ К РАБОТЕ!                          " -ForegroundColor Green
            Write-Host "  URL: $lhmUrl                                                  " -ForegroundColor Green
            Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
            Write-Host ""
        } else {
            Write-Host ""
            Write-Host "ℹ️ LHM запущен в фоне, но веб-сервер пока не ответил ($lhmUrl)." -ForegroundColor Yellow
            Write-Host "   Если это первый запуск, откройте LHM с флагом -Foreground и включите:" -ForegroundColor Yellow
            Write-Host "   'Options' -> 'Remote Web Server' -> 'Run' и порт 8085." -ForegroundColor Yellow
            Write-Host ""
        }
    } else {
        Write-Host "❌ Не удалось запустить LibreHardwareMonitor." -ForegroundColor Red
        exit 1
    }
}
