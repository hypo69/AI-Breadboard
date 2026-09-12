# =============================================================================
# Process Name: Gemini CLI installation
# =============================================================================
# Description:
#   Проверяется наличие Node.js, npm и Gemini CLI.
#   Отсутствующие компоненты устанавливаются автоматически.
#
# Requirements:
#   Windows 10/11
#   PowerShell 5.1+
#
# Example:
#   .\Install-Gemini-cli.ps1
# =============================================================================

param (
    [string]$InstallDir = '',
    [PSCustomObject]$Config = $null
)

$ErrorActionPreference = 'Stop'

function Write-Step {
    param(
        [Parameter(Mandatory)]
        [string]$Message
    )

    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-Command {
    param(
        [Parameter(Mandatory)]
        [string]$Command
    )

    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-NodeMajorVersion {
    if (-not (Test-Command 'node')) {
        return $null
    }

    $version = node --version

    if ($version -match '^v(\d+)') {
        return [int]$Matches[1]
    }

    return $null
}

function Install-NodeJs {
    Write-Step 'Проверяется установка Node.js'

    $nodeVersion = Get-NodeMajorVersion

    if ($null -ne $nodeVersion -and $nodeVersion -ge 20) {
        Write-Host "Node.js уже установлен: v$nodeVersion" -ForegroundColor Green
        return
    }

    if (-not (Test-Command 'winget')) {
        throw 'winget не найден. Установите App Installer из Microsoft Store.'
    }

    Write-Host 'Node.js >= 20 не найден. Выполняется установка Node.js LTS...'

    winget install `
        --id OpenJS.NodeJS.LTS `
        --exact `
        --source winget `
        --accept-source-agreements `
        --accept-package-agreements `
        --silent

    if ($LASTEXITCODE -ne 0) {
        throw "Не удалось установить Node.js. Код: $LASTEXITCODE"
    }

    # Обновляется PATH текущего процесса после установки Node.js.
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')

    if (-not (Test-Command 'node')) {
        throw 'Node.js установлен, но команда node пока недоступна. Перезапустите PowerShell и повторите запуск.'
    }

    $nodeVersion = Get-NodeMajorVersion

    if ($nodeVersion -lt 20) {
        throw "Требуется Node.js >= 20. Обнаружена версия: v$nodeVersion"
    }

    Write-Host "Node.js установлен: v$nodeVersion" -ForegroundColor Green
}

function Install-GeminiCli {
    Write-Step 'Проверяется установка Gemini CLI'

    if (-not (Test-Command 'npm')) {
        throw 'npm не найден. Установка Node.js не завершилась успешно.'
    }

    $geminiCommand = Get-Command 'gemini' -ErrorAction SilentlyContinue

    if ($null -ne $geminiCommand) {
        $geminiVersion = gemini --version 2>$null

        Write-Host "Gemini CLI уже установлен: $geminiVersion" -ForegroundColor Green
        return
    }

    Write-Host 'Gemini CLI не найден. Выполняется установка...'

    npm install --global @google/gemini-cli

    if ($LASTEXITCODE -ne 0) {
        throw "Не удалось установить Gemini CLI. Код: $LASTEXITCODE"
    }

    # Обновляется PATH текущего процесса после установки npm-пакета.
    $npmGlobalPath = npm prefix --global

    if ($LASTEXITCODE -eq 0 -and $npmGlobalPath) {
        $env:Path = "$npmGlobalPath;$env:Path"
    }

    if (-not (Test-Command 'gemini')) {
        throw 'Gemini CLI установлен, но команда gemini не найдена в PATH. Перезапустите PowerShell и повторите запуск.'
    }

    $geminiVersion = gemini --version 2>$null

    Write-Host "Gemini CLI установлен: $geminiVersion" -ForegroundColor Green
}

function Test-Installation {
    Write-Step 'Проверяется результат установки'

    $nodeVersion = node --version 2>$null
    $npmVersion = npm --version 2>$null
    $geminiVersion = gemini --version 2>$null

    Write-Host ''
    Write-Host "Node.js : $nodeVersion" -ForegroundColor Green
    Write-Host "npm     : $npmVersion" -ForegroundColor Green
    Write-Host "Gemini  : $geminiVersion" -ForegroundColor Green

    Write-Host ''
    Write-Host 'Gemini CLI готов к работе.' -ForegroundColor Green
}

try {
    Write-Host ''
    Write-Host '╔═══════════════════════════════════════════════════════════════╗' -ForegroundColor Magenta
    Write-Host '║              GEMINI CLI INSTALLATION                          ║' -ForegroundColor Magenta
    Write-Host '╚═══════════════════════════════════════════════════════════════╝' -ForegroundColor Magenta

    Install-NodeJs
    Install-GeminiCli
    Test-Installation
}
catch {
    Write-Host ''
    Write-Host "ОШИБКА: $($_.Exception.Message)" -ForegroundColor Red
}
