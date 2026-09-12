# =============================================================================
# Process Name: Git and Gemini CLI installation
# =============================================================================
# Description:
#   Проверяется наличие Git, Node.js и Gemini CLI.
#   Отсутствующие компоненты устанавливаются автоматически.
#
# Requirements:
#   Windows 10/11
#   PowerShell 5.1+
#
# Example:
#   .\install-gemini-cli.ps1
# =============================================================================

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


function Refresh-Path {
    # Обновляется PATH текущего процесса после установки программ.
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')

    $env:Path = "$machinePath;$userPath"
}


function Install-Git {
    Write-Step 'Проверяется установка Git'

    if (Test-Command 'git') {
        $gitVersion = git --version

        Write-Host "Git уже установлен: $gitVersion" -ForegroundColor Green
        return
    }

    if (-not (Test-Command 'winget')) {
        throw 'winget не найден. Установите App Installer из Microsoft Store.'
    }

    Write-Host 'Git не найден. Выполняется установка...'

    winget install `
        --id Git.Git `
        --exact `
        --source winget `
        --accept-source-agreements `
        --accept-package-agreements `
        --silent

    if ($LASTEXITCODE -ne 0) {
        throw "Не удалось установить Git. Код: $LASTEXITCODE"
    }

    Refresh-Path

    if (-not (Test-Command 'git')) {
        throw 'Git установлен, но команда git пока недоступна. Перезапустите PowerShell и повторите запуск.'
    }

    $gitVersion = git --version

    Write-Host "Git установлен: $gitVersion" -ForegroundColor Green
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

    Refresh-Path

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

    if (Test-Command 'gemini') {
        $geminiVersion = gemini --version 2>$null

        Write-Host "Gemini CLI уже установлен: $geminiVersion" -ForegroundColor Green
        return
    }

    Write-Host 'Gemini CLI не найден. Выполняется установка...'

    npm install --global @google/gemini-cli

    if ($LASTEXITCODE -ne 0) {
        throw "Не удалось установить Gemini CLI. Код: $LASTEXITCODE"
    }

    Refresh-Path

    if (-not (Test-Command 'gemini')) {
        throw 'Gemini CLI установлен, но команда gemini не найдена в PATH. Перезапустите PowerShell и повторите запуск.'
    }

    $geminiVersion = gemini --version 2>$null

    Write-Host "Gemini CLI установлен: $geminiVersion" -ForegroundColor Green
}


function Test-Installation {
    Write-Step 'Проверяется результат установки'

    $gitVersion = git --version
    $nodeVersion = node --version
    $npmVersion = npm --version
    $geminiVersion = gemini --version

    Write-Host ''
    Write-Host "Git     : $gitVersion" -ForegroundColor Green
    Write-Host "Node.js : $nodeVersion" -ForegroundColor Green
    Write-Host "npm     : $npmVersion" -ForegroundColor Green
    Write-Host "Gemini  : $geminiVersion" -ForegroundColor Green

    Write-Host ''
    Write-Host 'Все компоненты готовы к работе.' -ForegroundColor Green
}


try {
    Write-Host 'Git + Gemini CLI Installer' -ForegroundColor Magenta
    Write-Host '===========================' -ForegroundColor Magenta

    Install-Git
    Install-NodeJs
    Install-GeminiCli
    Test-Installation
    # Another test to ensure gemini command is available
}
catch {
    Write-Host ''
    Write-Host "ОШИБКА: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}