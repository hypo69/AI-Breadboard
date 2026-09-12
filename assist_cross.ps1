<#
.SYNOPSIS
    Кроссплатформенный CLI ассистент для AI-Breadboard (PowerShell обертка)
.DESCRIPTION
    Портирован для работы на Windows, Linux (WSL) и macOS.
    Используйте: assist start, assist stop, assist status и т.д.
.EXAMPLE
    .\assist_cross.ps1 start
    .\assist_cross.ps1 stop
    .\assist_cross.ps1 status
#>

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$ProjectDir = "C:\Users\onela\AppData\Local\AI Breadboard"
if (-not (Test-Path $ProjectDir) -and $env:AIBREADBOARD_DIR) {
    $ProjectDir = $env:AIBREADBOARD_DIR
}

$venvPython = Join-Path $ProjectDir "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $venvPython) {
        $venvPython = "python"
    }
}

$env:AIBREADBOARD_DIR = "$ProjectDir"
$env:ASSIST_DIR = "$ProjectDir"
$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = "$ProjectDir;$env:PYTHONPATH"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

& $venvPython "$ProjectDir\scripts\cli\assist.py" $Arguments
