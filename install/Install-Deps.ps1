<#
.SYNOPSIS
    Модуль установки зависимостей AI Breadboard.
.DESCRIPTION
    Предоставляет меню выбора профиля установки (Full, Core, Core+AI, Dev, Skip)
    и запускает установку через pip.
#>

param (
    [string]$InstallDir,
    [string]$PythonPath,
    [PSCustomObject]$Config,
    [switch]$InstallLightVersion
)

Write-Host ''
Write-Host (Msg "step_4") -ForegroundColor Cyan

$reqMain  = Join-Path $InstallDir 'requirements.txt'
$reqLight = Join-Path $InstallDir 'install\req\requirements-light.txt'
$reqCore  = Join-Path $InstallDir 'install\req\requirements-core.txt'
$reqAi    = Join-Path $InstallDir 'install\req\requirements-ai.txt'
$reqTest  = Join-Path $InstallDir 'install\req\requirements-test.txt'
$reqDocs  = Join-Path $InstallDir 'install\req\requirements-docs.txt'

if ($Config -and $Config.paths) {
    if ($Config.paths.requirements_main)  { $reqMain  = Join-Path $InstallDir $Config.paths.requirements_main }
    if ($Config.paths.requirements_light) { $reqLight = Join-Path $InstallDir $Config.paths.requirements_light }
    if ($Config.paths.requirements_core)  { $reqCore  = Join-Path $InstallDir $Config.paths.requirements_core }
    if ($Config.paths.requirements_ai)    { $reqAi    = Join-Path $InstallDir $Config.paths.requirements_ai }
    if ($Config.paths.requirements_test)  { $reqTest  = Join-Path $InstallDir $Config.paths.requirements_test }
    if ($Config.paths.requirements_docs)  { $reqDocs  = Join-Path $InstallDir $Config.paths.requirements_docs }
}

if ($InstallLightVersion) {
    Write-Host "    [LIGHT MODE] Установка только базовых пакетов и Google AI (Gemini, AGY)..." -ForegroundColor Green
    if (Test-Path $reqLight) {
        & $PythonPath -m pip install -r $reqLight
    } else {
        & $PythonPath -m pip install -r $reqCore google-antigravity google-genai langchain-google-genai
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host (Msg "step_4_pip_error") -ForegroundColor Red
        exit 1
    }
    return
}

Write-Host (Msg "step_4_menu_title") -ForegroundColor Gray
Write-Host (Msg "step_4_opt_1") -ForegroundColor White
Write-Host (Msg "step_4_opt_2") -ForegroundColor White
Write-Host (Msg "step_4_opt_3") -ForegroundColor White
Write-Host (Msg "step_4_opt_4") -ForegroundColor White
Write-Host (Msg "step_4_opt_5") -ForegroundColor White
Write-Host ''

$choice = Read-Host (Msg "step_4_choice_prompt")
$choice = $choice.Trim()

switch ($choice) {
    '1' {
        Write-Host ''
        Write-Host (Msg "step_4_installing_all") -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqMain
    }
    '2' {
        Write-Host ''
        Write-Host (Msg "step_4_installing_core") -ForegroundColor Cyan
        if (Test-Path $reqCore) { & $PythonPath -m pip install -r $reqCore }
        else { & $PythonPath -m pip install -r $reqMain }
    }
    '3' {
        Write-Host ''
        Write-Host (Msg "step_4_installing_ai") -ForegroundColor Cyan
        if ((Test-Path $reqCore) -and (Test-Path $reqAi)) {
            & $PythonPath -m pip install -r $reqCore -r $reqAi
        } else {
            & $PythonPath -m pip install -r $reqMain
        }
    }
    '4' {
        Write-Host ''
        Write-Host (Msg "step_4_installing_dev") -ForegroundColor Cyan
        $argsList = @('-r', $reqMain)
        if (Test-Path $reqTest) { $argsList += @('-r', $reqTest) }
        if (Test-Path $reqDocs) { $argsList += @('-r', $reqDocs) }
        & $PythonPath -m pip install @argsList
    }
    '5' {
        Write-Host (Msg "step_4_skipped") -ForegroundColor Yellow
    }
    default {
        Write-Host ''
        Write-Host (Msg "step_4_default_msg") -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqMain
    }
}

if ($choice -ne '5' -and $LASTEXITCODE -ne 0) {
    Write-Host (Msg "step_4_pip_error") -ForegroundColor Red
    exit 1
}
