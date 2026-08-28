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

$projectDir = "C:\Users\onela\AppData\Local\AI Breadboard"
if (-not (Test-Path $projectDir) -and $env:AIBREADBOARD_DIR) {
    $projectDir = $env:AIBREADBOARD_DIR
}

$venvPython = Join-Path $projectDir "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = (Get-Command python -ErrorAction SilentlyContinue).Source
}

$env:AIBREADBOARD_DIR = "$projectDir"
$env:ASSIST_DIR = "$projectDir"
$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = "$projectDir;$env:PYTHONPATH"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

& $venvPython -m scripts.dev.assist_cli @args
