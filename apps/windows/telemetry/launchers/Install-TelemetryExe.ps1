<#
=============================================================================
Process Name: AI-Breadboard Automation - Install TelemetryExe
=============================================================================
Description:
  Сборка исполняемого файла AITelemetry.exe (Windows Service), развертывание
  в %ProgramFiles%\AITelemetry, подготовка структуры %ProgramData%\AITelemetry
  и установка автозапуска службы Windows от имени администратора при старте системы.

Usage Examples:
  PowerShell Execution (от имени Администратора):
    # Полная компиляция, установка и запуск службы Windows
    .\Install-TelemetryExe.ps1

    # Только сборка без установки в Program Files
    .\Install-TelemetryExe.ps1 -BuildOnly

    # Проверка статуса установленной службы
    .\Install-TelemetryExe.ps1 -Status

    # Запуск / Остановка / Перезапуск службы
    .\Install-TelemetryExe.ps1 -Start
    .\Install-TelemetryExe.ps1 -Stop
    .\Install-TelemetryExe.ps1 -Restart

    # Удаление службы из Windows Service Control Manager
    .\Install-TelemetryExe.ps1 -Uninstall

File: Install-TelemetryExe.ps1
Project: ai-breadboard
Package: apps/windows/telemetry/launchers
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-06 07:58:00
=============================================================================
.SYNOPSIS
    Компиляция и установка фоновой службы AITelemetry как нативного Windows Service.
.DESCRIPTION
    Скрипт компилирует исходные файлы телеметрии через PyInstaller в нативный бинарник
    AITelemetry.exe, развертывает структуру каталогов в %ProgramFiles%\AITelemetry
    и %ProgramData%\AITelemetry, регистрирует службу в Windows Service Control Manager (SCM)
    с автоматическим запуском при старте системы (start=auto) и правами LocalSystem/Admin.
#>

[CmdletBinding(DefaultParameterSetName = 'Install')]
param (
    [Parameter(ParameterSetName = 'Install')]
    [Parameter(ParameterSetName = 'BuildOnly')]
    [ValidateSet('hybrid', 'minimal', 'full')]
    [string]$Mode = 'hybrid',

    [Parameter(ParameterSetName = 'Install')]
    [Parameter(ParameterSetName = 'Uninstall')]
    [Parameter(ParameterSetName = 'Status')]
    [Parameter(ParameterSetName = 'Start')]
    [Parameter(ParameterSetName = 'Stop')]
    [Parameter(ParameterSetName = 'Restart')]
    [string]$InstallDir = "$env:ProgramFiles\AITelemetry",

    [Parameter(ParameterSetName = 'Install')]
    [string]$DataDir = "$env:ProgramData\AITelemetry",

    [string]$ServiceName = 'AITelemetry',
    [string]$ServiceDisplayName = 'AI-Breadboard Telemetry Service',
    [string]$ServiceDescription = 'AI-Breadboard Background Telemetry and System Metrics Collector Service',

    [string]$PythonPath,

    [Parameter(ParameterSetName = 'Install')]
    [switch]$Install,

    [Parameter(ParameterSetName = 'Uninstall')]
    [switch]$Uninstall,

    [Parameter(ParameterSetName = 'BuildOnly')]
    [switch]$BuildOnly,

    [Parameter(ParameterSetName = 'Rebuild')]
    [switch]$Rebuild,

    [Parameter(ParameterSetName = 'Start')]
    [switch]$Start,

    [Parameter(ParameterSetName = 'Stop')]
    [switch]$Stop,

    [Parameter(ParameterSetName = 'Restart')]
    [switch]$Restart,

    [Parameter(ParameterSetName = 'Status')]
    [switch]$Status,

    [Parameter(ParameterSetName = 'Install')]
    [switch]$NoStart,

    [switch]$Clean,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# =============================================================================
# 1. ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА И САМОВОЗВЫШЕНИЕ (ELEVATION)
# =============================================================================
function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Assert-AdminPrivileges {
    param ([string]$ActionDescription = "Выполнение данной операции")
    if (-not (Test-IsAdministrator)) {
        Write-Warning "⚠️ Для '$ActionDescription' требуются права Администратора."
        
        # Если запущено интерактивно в PowerShell
        if ($Host.Name -notmatch "ServerRemoteHost" -and $PSCommandPath) {
            Write-Host "🔄 Попытка автоматического перезапуска PowerShell с правами Администратора..." -ForegroundColor Yellow
            $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
            if ($PSBoundParameters.Count -gt 0) {
                foreach ($key in $PSBoundParameters.Keys) {
                    $val = $PSBoundParameters[$key]
                    if ($val -is [System.Management.Automation.SwitchParameter]) {
                        if ($val.IsPresent) { $argList += " -$key" }
                    } else {
                        $argList += " -$key `"$val`""
                    }
                }
            }
            try {
                Start-Process powershell.exe -Verb RunAs -ArgumentList $argList -Wait
                exit 0
            } catch {
                Write-Error "❌ Не удалось запросить повышение прав (UAC): $_"
                exit 1
            }
        } else {
            Write-Error "❌ Пожалуйста, перезапустите PowerShell от имени Администратора (Run as Administrator)."
            exit 1
        }
    }
}

# =============================================================================
# 2. ПОИСК КОРНЯ РЕПОЗИТОРИЯ И ИНТЕРПРЕТАТОРА PYTHON
# =============================================================================
$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir) -and $MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}

# Ищем корень проекта
$projectRoot = $scriptDir
while ($projectRoot -and -not (Test-Path (Join-Path $projectRoot "pyproject.toml")) -and -not (Test-Path (Join-Path $projectRoot "apps\windows\telemetry"))) {
    $parent = Split-Path -Parent $projectRoot
    if ($parent -eq $projectRoot) { break }
    $projectRoot = $parent
}
if (-not (Test-Path (Join-Path $projectRoot "apps\windows\telemetry"))) {
    $projectRoot = (Get-Location).Path
}

function Find-PythonExecutable {
    param ([string]$ExplicitPath, [string]$Root)

    if ($ExplicitPath -and (Test-Path $ExplicitPath)) {
        return (Resolve-Path $ExplicitPath).Path
    }

    # 1. Проверяем venv в корне проекта
    $venvPy = Join-Path $Root "venv\Scripts\python.exe"
    if (Test-Path $venvPy) { return $venvPy }

    $dotVenvPy = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $dotVenvPy) { return $dotVenvPy }

    # 2. Проверяем системный python / py
    $sysPython = Get-Command python -ErrorAction SilentlyContinue
    if ($sysPython -and $sysPython.Source -and (Test-Path $sysPython.Source)) {
        return $sysPython.Source
    }

    $sysPy = Get-Command py -ErrorAction SilentlyContinue
    if ($sysPy -and $sysPy.Source -and (Test-Path $sysPy.Source)) {
        return $sysPy.Source
    }

    throw "Интерпретатор Python не найден. Убедитесь, что активирован venv или Python установлен в PATH."
}

# =============================================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ SCM СЛУЖБЫ
# =============================================================================
function Get-AITelemetryServiceStatus {
    param ([string]$Name)
    $service = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if ($null -eq $service) {
        return @{
            Exists = $false
            Status = 'NotInstalled'
            DisplayName = ''
            StartType = ''
        }
    }
    return @{
        Exists = $true
        Status = $service.Status.ToString()
        DisplayName = $service.DisplayName
        StartType = $service.StartType.ToString()
        Service = $service
    }
}

function Stop-AITelemetryService {
    param ([string]$Name)
    $st = Get-AITelemetryServiceStatus -Name $Name
    if ($st.Exists -and $st.Status -ne 'Stopped') {
        Write-Host "⏳ Остановка службы '$Name'..." -ForegroundColor Yellow
        try {
            Stop-Service -Name $Name -Force -ErrorAction Stop
            $timeout = 10
            while ($timeout -gt 0) {
                $check = Get-AITelemetryServiceStatus -Name $Name
                if ($check.Status -eq 'Stopped') { break }
                Start-Sleep -Seconds 1
                $timeout--
            }
            Write-Host "✅ Служба '$Name' успешно остановлена." -ForegroundColor Green
        } catch {
            Write-Warning "Не удалось остановить службу через Stop-Service, применяем net.exe stop: $_"
            & net.exe stop $Name | Out-Null
        }
    }
}

function Start-AITelemetryService {
    param ([string]$Name)
    $st = Get-AITelemetryServiceStatus -Name $Name
    if (-not $st.Exists) {
        Write-Error "❌ Служба '$Name' не установлена в системе."
        return
    }
    if ($st.Status -eq 'Running') {
        Write-Host "ℹ️ Служба '$Name' уже запущена (Running)." -ForegroundColor Cyan
        return
    }
    Write-Host "🚀 Запуск службы '$Name'..." -ForegroundColor Cyan
    try {
        Start-Service -Name $Name -ErrorAction Stop
        Write-Host "✅ Служба '$Name' успешно запущена." -ForegroundColor Green
    } catch {
        Write-Warning "Попытка запуска через net.exe start..."
        & net.exe start $Name
    }
}

# =============================================================================
# 4. ОБРАБОТКА КОМАНД СТАТУСА, УПРАВЛЕНИЯ И УДАЛЕНИЯ
# =============================================================================

# СТАТУС
if ($Status) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "         AITelemetry - Статус Windows Service" -ForegroundColor White
    Write-Host "============================================================" -ForegroundColor Cyan

    $svcStatus = Get-AITelemetryServiceStatus -Name $ServiceName
    if ($svcStatus.Exists) {
        $color = if ($svcStatus.Status -eq 'Running') { "Green" } else { "Yellow" }
        Write-Host "  • Статус службы (SCM):    $($svcStatus.Status)" -ForegroundColor $color
        Write-Host "  • Отображаемое имя:       $($svcStatus.DisplayName)" -ForegroundColor White
        Write-Host "  • Тип запуска:            $($svcStatus.StartType)" -ForegroundColor White
    } else {
        Write-Host "  • Статус службы (SCM):    ❌ Не установлена в системе" -ForegroundColor Red
    }

    $binExe = Join-Path $InstallDir "AITelemetry.exe"
    Write-Host "  • Исполняемый файл:       $binExe (Существует: $(Test-Path $binExe))" -ForegroundColor DarkGray

    $cfgFile = Join-Path $DataDir "config\config.json"
    Write-Host "  • Файл конфигурации:      $cfgFile (Существует: $(Test-Path $cfgFile))" -ForegroundColor DarkGray

    $dbFile = Join-Path $DataDir "data\telemetry.db"
    $dbSize = if (Test-Path $dbFile) { "$([math]::Round((Get-Item $dbFile).Length / 1MB, 2)) МБ" } else { "Отсутствует" }
    Write-Host "  • База данных SQLite:     $dbFile (Размер: $dbSize)" -ForegroundColor DarkGray

    $logFile = Join-Path $DataDir "logs\telemetry.log"
    Write-Host "  • Журнал службы (Log):    $logFile (Существует: $(Test-Path $logFile))" -ForegroundColor DarkGray

    Write-Host "============================================================" -ForegroundColor Cyan
    exit 0
}

# УПРАВЛЕНИЕ (START / STOP / RESTART)
if ($Start) {
    Assert-AdminPrivileges -ActionDescription "Запуск службы"
    Start-AITelemetryService -Name $ServiceName
    exit 0
}
if ($Stop) {
    Assert-AdminPrivileges -ActionDescription "Остановка службы"
    Stop-AITelemetryService -Name $ServiceName
    exit 0
}
if ($Restart) {
    Assert-AdminPrivileges -ActionDescription "Перезапуск службы"
    Stop-AITelemetryService -Name $ServiceName
    Start-Sleep -Seconds 1
    Start-AITelemetryService -Name $ServiceName
    exit 0
}

# УДАЛЕНИЕ СЛУЖБЫ
if ($Uninstall) {
    Assert-AdminPrivileges -ActionDescription "Удаление службы AITelemetry"
    Write-Host "🗑️ Удаление службы '$ServiceName'..." -ForegroundColor Yellow
    Stop-AITelemetryService -Name $ServiceName

    $svcStatus = Get-AITelemetryServiceStatus -Name $ServiceName
    if ($svcStatus.Exists) {
        & sc.exe delete $ServiceName | Out-Null
        Write-Host "✅ Служба '$ServiceName' успешно удалена из Windows Service Control Manager." -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Служба '$ServiceName' не найдена в SCM." -ForegroundColor DarkGray
    }

    if ($Force -and (Test-Path $InstallDir)) {
        Write-Host "🗑️ Удаление файлов установки из $InstallDir..." -ForegroundColor Yellow
        Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    exit 0
}

# =============================================================================
# 5. КОМПИЛЯЦИЯ EXECUTABLE (PYINSTALLER)
# =============================================================================
$python = Find-PythonExecutable -ExplicitPath $PythonPath -Root $projectRoot
Write-Host "🐍 Используется Python: $python" -ForegroundColor DarkCyan

# Проверка наличия pyinstaller
$hasPyinstaller = & $python -c "import importlib.util; print(bool(importlib.util.find_spec('PyInstaller')))" 2>$null
if ($hasPyinstaller -ne "True") {
    Write-Host "📦 PyInstaller не найден в окружении. Установка пакета pyinstaller..." -ForegroundColor Yellow
    & $python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Не удалось установить PyInstaller."
        exit 1
    }
}

# Проверка pywin32
$hasPywin32 = & $python -c "import importlib.util; print(bool(importlib.util.find_spec('win32service')))" 2>$null
if ($hasPywin32 -ne "True") {
    Write-Host "📦 pywin32 не найден. Установка пакета pywin32..." -ForegroundColor Yellow
    & $python -m pip install pywin32
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Не удалось установить pywin32."
        exit 1
    }
}

$buildWorkDir = Join-Path $projectRoot "build\pyinstaller_telemetry"
$distWorkDir = Join-Path $projectRoot "dist"
$serviceSrc = Join-Path $projectRoot "apps\windows\telemetry\win_service.py"
$ctlSrc = Join-Path $projectRoot "apps\windows\telemetry\ctl.py"

if (-not (Test-Path $serviceSrc)) {
    Write-Error "❌ Исходный файл точки входа службы не найден: $serviceSrc"
    exit 1
}

if ($Clean -or $Rebuild) {
    Write-Host "🧹 Очистка временных каталогов сборки..." -ForegroundColor Yellow
    if (Test-Path $buildWorkDir) { Remove-Item -Path $buildWorkDir -Recurse -Force -ErrorAction SilentlyContinue }
    $distTarget = Join-Path $distWorkDir "AITelemetry"
    if (Test-Path $distTarget) { Remove-Item -Path $distTarget -Recurse -Force -ErrorAction SilentlyContinue }
}

Write-Host ""
Write-Host "🔨 Компиляция AITelemetry.exe (Windows Service onedir)..." -ForegroundColor Cyan
$pyinstallerArgs = @(
    "-m", "PyInstaller",
    "--name", "AITelemetry",
    "--onedir",
    "--noconfirm",
    "--clean",
    "--workpath", $buildWorkDir,
    "--distpath", $distWorkDir,
    "--hidden-import", "win32timezone",
    "--hidden-import", "win32service",
    "--hidden-import", "win32serviceutil",
    "--hidden-import", "win32event",
    "--hidden-import", "servicemanager",
    "--hidden-import", "psutil",
    "--hidden-import", "sqlite3",
    "--collect-submodules", "apps.windows.telemetry",
    $serviceSrc
)

$prevCwd = (Get-Location).Path
try {
    Set-Location $projectRoot
    & $python $pyinstallerArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Ошибка компиляции AITelemetry через PyInstaller."
        exit 1
    }

    # Компиляция AITelemetryCtl.exe
    if (Test-Path $ctlSrc) {
        Write-Host "🔨 Компиляция AITelemetryCtl.exe (CLI Controller)..." -ForegroundColor Cyan
        $ctlArgs = @(
            "-m", "PyInstaller",
            "--name", "AITelemetryCtl",
            "--onedir",
            "--noconfirm",
            "--clean",
            "--workpath", $buildWorkDir,
            "--distpath", $distWorkDir,
            "--collect-submodules", "apps.windows.telemetry",
            $ctlSrc
        )
        & $python $ctlArgs
        if ($LASTEXITCODE -eq 0) {
            # Копируем бинарник Ctl в общий каталог AITelemetry
            $ctlDist = Join-Path $distWorkDir "AITelemetryCtl\AITelemetryCtl.exe"
            $destDist = Join-Path $distWorkDir "AITelemetry\AITelemetryCtl.exe"
            if (Test-Path $ctlDist) {
                Copy-Item -Path $ctlDist -Destination $destDist -Force
            }
        }
    }
} finally {
    Set-Location $prevCwd
}

$compiledExe = Join-Path $distWorkDir "AITelemetry\AITelemetry.exe"
if (-not (Test-Path $compiledExe)) {
    Write-Error "❌ Скомпилированный файл не найден: $compiledExe"
    exit 1
}
Write-Host "✅ Сборка успешно завершена: $compiledExe" -ForegroundColor Green

if ($BuildOnly) {
    Write-Host "🎉 Режим -BuildOnly: компиляция выполнена. Установка не требуется." -ForegroundColor Green
    exit 0
}

# =============================================================================
# 6. РАЗВЕРТЫВАНИЕ В %ProgramFiles% И %ProgramData%
# =============================================================================
Assert-AdminPrivileges -ActionDescription "Установка службы в $InstallDir и регистрация в SCM"

Write-Host ""
Write-Host "📁 Подготовка каталогов ProgramData ($DataDir)..." -ForegroundColor Cyan
$subDirs = @('config', 'logs', 'data', 'cache', 'snapshots')
foreach ($sub in $subDirs) {
    $dirPath = Join-Path $DataDir $sub
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
    }
}

# Развертывание базовой конфигурации config.json если отсутствует
$targetConfig = Join-Path $DataDir "config\config.json"
if (-not (Test-Path $targetConfig)) {
    $srcConfig = Join-Path $projectRoot "apps\windows\telemetry\config.json"
    if (Test-Path $srcConfig) {
        Write-Host "📄 Развертывание шаблона конфигурации в $targetConfig..." -ForegroundColor DarkCyan
        Copy-Item -Path $srcConfig -Destination $targetConfig -Force
    } else {
        # Создаем базовый config.json
        $baseCfg = @{
            mode = $Mode
            interval_seconds = 5.0
            heavy_interval_seconds = 60.0
            top_processes = 10
            retention_days = 7
            max_db_size_mb = 50.0
            buffer_mode = "memory"
        } | ConvertTo-Json -Depth 4
        Set-Content -Path $targetConfig -Value $baseCfg -Encoding UTF8
    }
}

# Остановка существующей службы перед перезаписью файлов
Stop-AITelemetryService -Name $ServiceName

Write-Host "📦 Развертывание файлов в каталог $InstallDir..." -ForegroundColor Cyan
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

$distFolder = Join-Path $distWorkDir "AITelemetry"
Copy-Item -Path "$distFolder\*" -Destination $InstallDir -Recurse -Force
Write-Host "✅ Файлы успешно скопированы в $InstallDir." -ForegroundColor Green

# =============================================================================
# 7. РЕГИСТРАЦИЯ СЛУЖБЫ В WINDOWS SCM (АВТОЗАПУСК ПРИ СТАРТЕ СИСТЕМЫ)
# =============================================================================
Write-Host "⚙️ Регистрация службы '$ServiceName' в Windows SCM..." -ForegroundColor Cyan
$targetExe = Join-Path $InstallDir "AITelemetry.exe"
$svcStatus = Get-AITelemetryServiceStatus -Name $ServiceName

if ($svcStatus.Exists) {
    Write-Host "ℹ️ Служба уже зарегистрирована. Обновление бинарного пути и параметров..." -ForegroundColor DarkCyan
    & sc.exe config $ServiceName binPath= "`"$targetExe`"" start= auto DisplayName= "$ServiceDisplayName" | Out-Null
} else {
    Write-Host "➕ Создание новой службы Windows '$ServiceName' (start=auto)..." -ForegroundColor DarkCyan
    & sc.exe create $ServiceName binPath= "`"$targetExe`"" start= auto DisplayName= "$ServiceDisplayName" | Out-Null
}

# Описание службы и политика восстановления при сбое
& sc.exe description $ServiceName "$ServiceDescription" | Out-Null
& sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/10000/restart/30000 | Out-Null

Write-Host "✅ Служба '$ServiceName' успешно сконфигурирована с автозапуском при старте системы." -ForegroundColor Green

# =============================================================================
# 8. ЗАПУСК И ИТОГОВАЯ ПРОВЕРКА
# =============================================================================
if (-not $NoStart) {
    Start-AITelemetryService -Name $ServiceName
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "       🎉 AITelemetry Windows Service Успешно Установлена!" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
$finalStatus = Get-AITelemetryServiceStatus -Name $ServiceName
Write-Host "  • Статус службы:    $($finalStatus.Status)" -ForegroundColor Cyan
Write-Host "  • Исполняемый файл: $targetExe" -ForegroundColor White
Write-Host "  • Данные и логи:    $DataDir" -ForegroundColor White
Write-Host "  • Контроллер CLI:   $InstallDir\AITelemetryCtl.exe" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
