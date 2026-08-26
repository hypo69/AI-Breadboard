<#
.SYNOPSIS
    Главный оркестратор установки AI Breadboard с модульной архитектурой и поддержкой i18n (RU, EN, ES, HE).
.DESCRIPTION
    Загружает конфигурацию из install/install.json, подключает модули интернационализации,
    выбора директории (%LOCALAPPDATA%\AI Breadboard или пользовательский путь),
    создания venv, установки зависимостей, генерации SSL и регистрации AIBREADBOARD_DIR.
.EXAMPLE
    irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
    .\install.ps1
#>

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Определение каталога текущего скрипта
$runningScriptDir = ""
try {
    if ($PSScriptRoot) {
        $runningScriptDir = $PSScriptRoot
    } elseif ($MyInvocation.MyCommand.Path) {
        $runningScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    }
} catch {}

$localInstallDir = if ($runningScriptDir) { Join-Path $runningScriptDir "install" } else { "" }

# 1. Загрузка конфигурации install.json
$config = $null
$configPath = if ($localInstallDir) { Join-Path $localInstallDir "install.json" } else { "" }
if ($configPath -and (Test-Path $configPath)) {
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
    } catch {}
}

# 2. Подключение модуля i18n
$i18nScript = if ($localInstallDir) { Join-Path $localInstallDir "Install-I18n.ps1" } else { "" }
if ($i18nScript -and (Test-Path $i18nScript)) {
    . $i18nScript
} else {
    # Fallback загрузка i18n из веб-репозитория
    $rawI18nUrl = "https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install/Install-I18n.ps1"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
        $webI18n = Invoke-RestMethod -Uri $rawI18nUrl -UseBasicParsing
        . ([ScriptBlock]::Create($webI18n))
    } catch {
        Write-Host "[ERROR] Failed to load I18n module: $_" -ForegroundColor Red
        exit 1
    }
}

# 3. Выбор языка пользователем
$defaultLang = if ($config -and $config.defaults -and $config.defaults.language) { $config.defaults.language } else { "en" }
Select-InstallerLanguage -DefaultLang $defaultLang

# 4. Модуль выбора директории
$dirScript = if ($localInstallDir) { Join-Path $localInstallDir "Install-Directory.ps1" } else { "" }
$targetDir = ""
if ($dirScript -and (Test-Path $dirScript)) {
    $targetDir = & $dirScript -Config $config -SourceDir $runningScriptDir
} else {
    $rawDirUrl = "https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install/Install-Directory.ps1"
    $webDir = Invoke-RestMethod -Uri $rawDirUrl -UseBasicParsing
    $targetDir = & ([ScriptBlock]::Create($webDir)) -Config $config -SourceDir $runningScriptDir
}

if (-not $targetDir) {
    $targetDir = Join-Path $env:LOCALAPPDATA 'AI Breadboard'
}

$InstallDir = $targetDir
$installedModulesDir = Join-Path $InstallDir "install"

# 5. Инициализация логирования установки в tmp/logs/install.log
$tmpLogsDir = Join-Path $InstallDir "tmp\logs"
if (-not (Test-Path $tmpLogsDir)) {
    New-Item -ItemType Directory -Force -Path $tmpLogsDir | Out-Null
}
$installLogFile = Join-Path $tmpLogsDir "install.log"
try {
    Start-Transcript -Path $installLogFile -Append -Force -ErrorAction SilentlyContinue | Out-Null
} catch {}

# Перезагружаем config.json из целевой директории, если он там появился
if (Test-Path (Join-Path $installedModulesDir "install.json")) {
    try {
        $config = Get-Content (Join-Path $installedModulesDir "install.json") -Raw | ConvertFrom-Json
    } catch {}
}

# 6. Снятие блокировки файлов Windows
Write-Host (Msg "step_1") -ForegroundColor Cyan
Get-ChildItem -Path $InstallDir -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\\.git\\' } |
    Unblock-File -ErrorAction SilentlyContinue
Write-Host (Msg "step_1_ok") -ForegroundColor Green

# 7. Модуль venv
$venvScript = Join-Path $installedModulesDir "Install-Venv.ps1"
$PythonPath = & $venvScript -InstallDir $InstallDir -Config $config

# 8. Модуль зависимостей
$depsScript = Join-Path $installedModulesDir "Install-Deps.ps1"
& $depsScript -InstallDir $InstallDir -PythonPath $PythonPath -Config $config

# 9. Модуль сертификатов SSL
$certsScript = Join-Path $installedModulesDir "Install-Certs.ps1"
& $certsScript -InstallDir $InstallDir -Config $config

# 10. Модуль CLI assist и переменных среды
$cliScript = Join-Path $installedModulesDir "Install-Cli.ps1"
& $cliScript -InstallDir $InstallDir -Config $config

# 11. Модуль верификации и финализации
$verifyScript = Join-Path $installedModulesDir "Install-Verify.ps1"
& $verifyScript -InstallDir $InstallDir -PythonPath $PythonPath -Config $config

# Завершение логирования установки
try {
    Stop-Transcript -ErrorAction SilentlyContinue | Out-Null
} catch {}
