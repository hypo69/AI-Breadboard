<#
.SYNOPSIS
    Модуль инициализации и настройки учетной записи администратора по умолчанию.
.DESCRIPTION
    Запрашивает у пользователя email, имя и пароль для системного администратора
    или использует безопасные значения по умолчанию (admin@localhost / Admin / onela).
    Запускает скрипт scripts/create_initial_user.py в созданном виртуальном окружении.
.EXAMPLE
    .\Install-User.ps1 -InstallDir $InstallDir -PythonPath $PythonPath -Config $Config
#>

param (
    [string]$InstallDir = '',
    [string]$PythonPath = '',
    [PSCustomObject]$Config = $null,
    [switch]$NonInteractive
)

$ErrorActionPreference = 'Continue'

Write-Host ''
Write-Host '╔═══════════════════════════════════════════════════════════════╗' -ForegroundColor Cyan
Write-Host (Msg "step_user_header") -ForegroundColor Cyan
Write-Host '╚═══════════════════════════════════════════════════════════════╝' -ForegroundColor Cyan
Write-Host (Msg "step_user") -ForegroundColor Cyan
Write-Host ''

if (-not $PythonPath) {
    $venvPython = Join-Path $InstallDir 'venv\Scripts\python.exe'
    if (Test-Path $venvPython) {
        $PythonPath = $venvPython
    } else {
        $PythonPath = 'python'
    }
}

$userScript = Join-Path $InstallDir 'scripts\create_initial_user.py'
if (-not (Test-Path $userScript)) {
    Write-Host (Msg "step_user_err" @("scripts/create_initial_user.py not found")) -ForegroundColor Yellow
    return
}

try {
    if ($NonInteractive) {
        & $PythonPath $userScript --non-interactive
        if ($LASTEXITCODE -eq 0) {
            Write-Host (Msg "step_user_ok" @("admin@localhost")) -ForegroundColor Green
        }
    } else {
        $email = Read-Host (Msg "step_user_prompt_email")
        $email = $email.Trim()
        if (-not $email) { $email = "admin@localhost" }

        $name = Read-Host (Msg "step_user_prompt_name")
        $name = $name.Trim()
        if (-not $name) { $name = "Admin" }

        $passPrompt = Msg "step_user_prompt_pass"
        $passSecure = Read-Host $passPrompt -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($passSecure)
        $password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

        if (-not $password) { $password = "onela" }

        & $PythonPath $userScript --email $email --name $name --password $password --non-interactive
        if ($LASTEXITCODE -eq 0) {
            Write-Host (Msg "step_user_ok" @($email)) -ForegroundColor Green
        } else {
            Write-Host (Msg "step_user_err" @("exit code $LASTEXITCODE")) -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host (Msg "step_user_err" @($_.Exception.Message)) -ForegroundColor Yellow
}
