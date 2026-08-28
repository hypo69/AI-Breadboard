<#
.SYNOPSIS
    Модуль привязки путей проекта и генерации глобальных команд assist.
.DESCRIPTION
    Устанавливает постоянную системную переменную AIBREADBOARD_DIR (и ASSIST_DIR),
    генерирует assist.ps1, assist.cmd и bash-скрипт assist с жесткой привязкой каталога,
    копирует их в %USERPROFILE%\.local\bin, добавляет пути в PATH и регистрирует
    функцию assist в профилях PowerShell.
#>

param (
    [string]$InstallDir,
    [PSCustomObject]$Config
)

Write-Host ''
Write-Host (Msg "step_6") -ForegroundColor Cyan

try {
    [System.Environment]::SetEnvironmentVariable('AIBREADBOARD_DIR', $InstallDir, 'User')
    [System.Environment]::SetEnvironmentVariable('ASSIST_DIR', $InstallDir, 'User')
    $env:AIBREADBOARD_DIR = $InstallDir
    $env:ASSIST_DIR = $InstallDir
    Write-Host (Msg "step_6_env_ok" @($InstallDir)) -ForegroundColor Green
} catch {}

$assistPs1Content = @"
<#
.SYNOPSIS
    CLI ассистент для управления проектом AI Breadboard.
.DESCRIPTION
    Передает команды в scripts.dev.assist_cli с жесткой фиксацией путей проекта.
.EXAMPLE
    assist start
    assist status
    assist providers
    assist stop
#>

`$projectDir = "$InstallDir"
if (-not (Test-Path `$projectDir) -and `$env:AIBREADBOARD_DIR) {
    `$projectDir = `$env:AIBREADBOARD_DIR
}

`$venvPython = Join-Path `$projectDir "venv\Scripts\python.exe"
if (-not (Test-Path `$venvPython)) {
    `$venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
}

`$env:AIBREADBOARD_DIR = "`$projectDir"
`$env:ASSIST_DIR = "`$projectDir"
`$env:PYTHONUTF8 = "1"
`$env:PYTHONPATH = "`$projectDir;`$env:PYTHONPATH"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
`$OutputEncoding = [System.Text.Encoding]::UTF8

& `$venvPython -m scripts.dev.assist_cli @args
"@
Set-Content -Path (Join-Path $InstallDir 'assist.ps1') -Value $assistPs1Content -Encoding UTF8

$assistCmdContent = @"
@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set AIBREADBOARD_DIR=$InstallDir
set ASSIST_DIR=$InstallDir
set PYTHONPATH=%AIBREADBOARD_DIR%;%PYTHONPATH%
if exist "%AIBREADBOARD_DIR%\venv\Scripts\python.exe" (
    "%AIBREADBOARD_DIR%\venv\Scripts\python.exe" -m scripts.dev.assist_cli %*
) else (
    python -m scripts.dev.assist_cli %*
)
endlocal
"@
Set-Content -Path (Join-Path $InstallDir 'assist.cmd') -Value $assistCmdContent -Encoding UTF8

$localBin = Join-Path $env:USERPROFILE '.local\bin'
if (-not (Test-Path $localBin)) {
    New-Item -ItemType Directory -Force -Path $localBin | Out-Null
}
Copy-Item (Join-Path $InstallDir 'assist.cmd') (Join-Path $localBin 'assist.cmd') -Force
Copy-Item (Join-Path $InstallDir 'assist.ps1') (Join-Path $localBin 'assist.ps1') -Force

$bashWrapper = @"
#!/usr/bin/env bash
export PYTHONUTF8=1
export AIBREADBOARD_DIR="$($InstallDir -replace '\\', '/')"
export ASSIST_DIR="$($InstallDir -replace '\\', '/')"
export PYTHONPATH="`$AIBREADBOARD_DIR:`$PYTHONPATH"

# CLI aliases for manage_tools.py
rag() { python "`$AIBREADBOARD_DIR/manage_tools.py" rag "`$@"; }
skills() { python "`$AIBREADBOARD_DIR/manage_tools.py" skills "`$@"; }
knowledge() { python "`$AIBREADBOARD_DIR/manage_tools.py" knowledge "`$@"; }
docs() { python "`$AIBREADBOARD_DIR/manage_tools.py" docs "`$@"; }
assist() { python -m scripts.dev.assist_cli "`$@"; }

# Main command dispatcher
if [ -f "`$AIBREADBOARD_DIR/venv/Scripts/python.exe" ]; then
    "`$AIBREADBOARD_DIR/venv/Scripts/python.exe" -m scripts.dev.assist_cli "`$@"
else
    python -m scripts.dev.assist_cli "`$@"
fi
"@
Set-Content -Path (Join-Path $localBin 'assist') -Value $bashWrapper -Encoding UTF8

try {
    $userPath = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $pathsToAdd = @($localBin, $InstallDir)
    $pathUpdated = $false
    foreach ($p in $pathsToAdd) {
        if ($userPath -notmatch [regex]::Escape($p)) {
            $userPath = "$userPath;$p"
            $pathUpdated = $true
        }
    }
    if ($pathUpdated) {
        [System.Environment]::SetEnvironmentVariable('Path', $userPath, 'User')
    }
    Write-Host (Msg "step_6_path_ok") -ForegroundColor Green
} catch {}

$profileDirs = @(
    (Join-Path $env:USERPROFILE 'Documents\PowerShell'),
    (Join-Path $env:USERPROFILE 'Documents\WindowsPowerShell')
)
$fnSnippet = @"

# ==========================================
# AIBREADBOARD CLI GLOBAL ALIASES
# ==========================================
`$env:AIBREADBOARD_DIR = "$InstallDir"

function assist {
    & "$InstallDir\assist.ps1" @args
}

function rag {
    python "$InstallDir\manage_tools.py" rag @args
}

function skills {
    python "$InstallDir\manage_tools.py" skills @args
}

function knowledge {
    python "$InstallDir\manage_tools.py" knowledge @args
}

function docs {
    python "$InstallDir\manage_tools.py" docs @args
}
"@

foreach ($pDir in $profileDirs) {
    try {
        if (-not (Test-Path $pDir)) { New-Item -ItemType Directory -Force -Path $pDir | Out-Null }
        $profFile = Join-Path $pDir 'Microsoft.PowerShell_profile.ps1'
        $existing = if (Test-Path $profFile) { Get-Content $profFile -Raw } else { '' }
        if ($existing -notmatch 'function rag') {
            Add-Content -Path $profFile -Value $fnSnippet -Encoding UTF8
        }
    } catch {}
}
Write-Host (Msg "step_6_prof_ok") -ForegroundColor Green
