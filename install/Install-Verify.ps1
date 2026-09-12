<#
.SYNOPSIS
    Модуль верификации и финализации установки AI Breadboard.
.DESCRIPTION
    Проверяет импорт ключевых модулей Python, сохраняет выбранный язык в config.json
    и отображает финальный баннер завершения.
#>

param (
    [string]$InstallDir,
    [string]$PythonPath,
    [PSCustomObject]$Config,
    [switch]$InstallLightVersion
)

Write-Host ''
Write-Host (Msg "step_7") -ForegroundColor Cyan

$modulesList = "['fastapi', 'uvicorn', 'dotenv', 'pydantic', 'aiohttp', 'cryptography']"
if ($InstallLightVersion) {
    $modulesList = "['fastapi', 'uvicorn', 'dotenv', 'pydantic', 'aiohttp', 'google.genai', 'google_antigravity']"
} elseif ($Config -and $Config.verify -and $Config.verify.modules) {
    $mArr = ($Config.verify.modules | ForEach-Object { "'$_'" }) -join ", "
    $modulesList = "[$mArr]"
}

$testScript = @"
import sys
modules = $modulesList
loaded = []
failed = []
for m in modules:
    try:
        __import__(m)
        loaded.append(m)
    except ImportError:
        failed.append(m)
print('loaded=' + ','.join(loaded))
if failed:
    print('missing=' + ','.join(failed))
"@

$checkOutput = & $PythonPath -c $testScript 2>&1

if ($LASTEXITCODE -eq 0 -and $checkOutput -match 'loaded=') {
    Write-Host (Msg "step_7_ok") -ForegroundColor Green
    Write-Host (Msg "step_7_py_path" @($PythonPath)) -ForegroundColor Green
} else {
    Write-Host (Msg "step_7_warn" @($checkOutput)) -ForegroundColor Yellow
}

# Обновляем config.json
$configPath = Join-Path $InstallDir "config.json"
if (Test-Path $configPath) {
    try {
        $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json
        if (-not $jsonContent.user_settings) {
            $jsonContent | Add-Member -NotePropertyName "user_settings" -NotePropertyValue (New-Object PSObject) -Force
        }
        $jsonContent.user_settings | Add-Member -NotePropertyName "language" -NotePropertyValue $Global:CurrentLang -Force
        
        if ($InstallLightVersion) {
            # При легкой установке настраиваем хост на 127.0.0.1, отключаем туннели и локальные провайдеры
            if ($jsonContent.server) {
                $jsonContent.server | Add-Member -NotePropertyName "host" -NotePropertyValue "127.0.0.1" -Force
                $jsonContent.server | Add-Member -NotePropertyName "use_cloudflared" -NotePropertyValue $false -Force
                $jsonContent.server | Add-Member -NotePropertyName "client_url" -NotePropertyValue "http://127.0.0.1:8000" -Force
            }
            if ($jsonContent.ai) {
                $jsonContent.ai | Add-Member -NotePropertyName "use_foundry" -NotePropertyValue $false -Force
                $jsonContent.ai | Add-Member -NotePropertyName "use_ollama" -NotePropertyValue $false -Force
                $jsonContent.ai | Add-Member -NotePropertyName "use_gemini_cli" -NotePropertyValue $true -Force
                $jsonContent.ai | Add-Member -NotePropertyName "use_agy" -NotePropertyValue $true -Force
            }
        }

        $jsonContent | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
    } catch {}
}

Write-Host ''
Write-Host '╔═══════════════════════════════════════════════════════════════╗' -ForegroundColor Green
Write-Host (Msg "finish_banner_1") -ForegroundColor Green
Write-Host '║                                                               ║' -ForegroundColor Green
Write-Host (Msg "finish_banner_2") -ForegroundColor Green
Write-Host '╚═══════════════════════════════════════════════════════════════╝' -ForegroundColor Green
Write-Host ''
Write-Host (Msg "finish_hint") -ForegroundColor Cyan
Write-Host ''
