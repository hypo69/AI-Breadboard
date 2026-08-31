<#
.SYNOPSIS
    Модуль выбора и скачивания моделей для локальных AI провайдеров.
.DESCRIPTION
    Получает список доступных моделей от Ollama, Foundry и других локальных провайдеров,
    предлагает пользователю выбрать модели для скачивания и загружает их.
#>

param (
    [string]$InstallDir,
    [PSCustomObject]$Config
)

Write-Host ''
Write-Host (Msg "step_8") -ForegroundColor Cyan
Write-Host ''

# Получение списка моделей через Python и model_manager
function Get-LocalModels {
    param([string]$Provider, [string]$PythonPath)
    
    $script = @"
import sys
sys.path.insert(0, r"$InstallDir")

try:
    from core.ai.model_manager import get_available_models
    models = get_available_models(provider='$Provider', force_refresh=False)
    print('|'.join(models) if models else '')
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
"@
    
    $result = & $PythonPath -c $script 2>&1
    return $result
}

# Выбор моделей из списка
function Select-Models {
    param(
        [string]$ProviderName,
        [array]$Models,
        [string]$DefaultModels = ""
    )
    
    if (-not $Models -or $Models.Count -eq 0) {
        Write-Host (Msg "step_8_no_models" @($ProviderName)) -ForegroundColor Yellow
        return @()
    }
    
    Write-Host (Msg "step_8_available" @($ProviderName)) -ForegroundColor Cyan
    Write-Host ''
    
    for ($i = 0; $i -lt $Models.Count; $i++) {
        Write-Host "  [$($i+1)] $($Models[$i])" -ForegroundColor White
    }
    Write-Host ''
    
    if ($DefaultModels) {
        Write-Host (Msg "step_8_default_hint" @($DefaultModels)) -ForegroundColor Gray
    }
    
    $choice = Read-Host (Msg "step_8_prompt")
    $choice = $choice.Trim()
    
    if ([string]::IsNullOrWhiteSpace($choice)) {
        if ($DefaultModels) {
            return $DefaultModels -split ','
        }
        return @()
    }
    
    # Разбор пользовательского ввода (можно указать номера через запятую или диапазон)
    $selected = @()
    $parts = $choice -split ','
    
    foreach ($part in $parts) {
        $part = $part.Trim()
        if ($part -match '^(\d+)-(\d+)$') {
            # Диапазон: 1-3
            $start = [int]$matches[1]
            $end = [int]$matches[2]
            for ($i = $start; $i -le $end -and $i -le $Models.Count; $i++) {
                if ($i -ge 1) {
                    $selected += $Models[$i-1]
                }
            }
        } elseif ($part -match '^\d+$') {
            # Одиночный номер
            $idx = [int]$part
            if ($idx -ge 1 -and $idx -le $Models.Count) {
                $selected += $Models[$idx-1]
            }
        }
    }
    
    return $selected
}

# Скачивание модели для конкретного провайдера
function Download-Model {
    param(
        [string]$Provider,
        [string]$ModelId,
        [string]$InstallDir
    )
    
    Write-Host (Msg "step_8_downloading" @($Provider, $ModelId)) -ForegroundColor Cyan
    
    switch ($Provider) {
        "ollama" {
            # Загрузка через ollama pull
            try {
                & ollama pull $ModelId 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host (Msg "step_8_success" @($ModelId)) -ForegroundColor Green
                    return $true
                }
            } catch {
                Write-Host (Msg "step_8_failed" @($ModelId, $_.Exception.Message)) -ForegroundColor Red
                return $false
            }
        }
        "foundry" {
            # Foundry загружает модели автоматически при первом использовании
            # Но можно проверить доступность через API
            Write-Host (Msg "step_8_foundry_hint") -ForegroundColor Gray
            Write-Host (Msg "step_8_success" @($ModelId)) -ForegroundColor Green
            return $true
        }
        "onnx" {
            # ONNX модели загружаются через Transformers при первом использовании
            Write-Host (Msg "step_8_onnx_hint") -ForegroundColor Gray
            Write-Host (Msg "step_8_success" @($ModelId)) -ForegroundColor Green
            return $true
        }
        "hf" {
            # HuggingFace модели также загружаются автоматически
            Write-Host (Msg "step_8_hf_hint") -ForegroundColor Gray
            Write-Host (Msg "step_8_success" @($ModelId)) -ForegroundColor Green
            return $true
        }
        default {
            Write-Host (Msg "step_8_skipped" @($Provider, $ModelId)) -ForegroundColor Yellow
            return $false
        }
    }
}

# Основная логика
try {
    # Определение пути к Python из venv
    $venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Host (Msg "step_8_no_venv") -ForegroundColor Red
        return
    }
    
    Write-Host '┌─────────────────────────────────────────────────────────────┐' -ForegroundColor Cyan
    Write-Host '│           ВЫБОР И ЗАГРУЗКА МОДЕЛЕЙ ДЛЯ ЛОКАЛЬНЫХ ПРОВАЙДЕРОВ │' -ForegroundColor Cyan
    Write-Host '└─────────────────────────────────────────────────────────────┘' -ForegroundColor Cyan
    Write-Host ''
    
    # Проверка доступности провайдеров
    $availableProviders = @()
    
    # Проверка Ollama
    $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollamaCmd) {
        $availableProviders += "ollama"
    }
    
    # Проверка Foundry
    $foundryCmd = Get-Command foundry -ErrorAction SilentlyContinue
    if ($foundryCmd) {
        $availableProviders += "foundry"
    }
    
    # Получение моделей для каждого доступного провайдера
    $selectedModels = @{}
    
    foreach ($provider in $availableProviders) {
        $models = Get-LocalModels -Provider $provider -PythonPath $venvPython
        
        if ($models -and -not $models.StartsWith("ERROR:")) {
            $modelsArray = $models -split '\|' | Where-Object { $_ -and $_ -notmatch '^ERROR:' }
            
            # Получение моделей по умолчанию из конфигурации
            $defaultModels = ""
            if ($Config -and $Config.defaults -and $Config.defaults.default_models) {
                $defaultModels = $Config.defaults.default_models
            }
            
            $selected = Select-Models -ProviderName $provider -Models $modelsArray -DefaultModels $defaultModels
            
            if ($selected -and $selected.Count -gt 0) {
                $selectedModels[$provider] = $selected
            }
        } else {
            Write-Host (Msg "step_8_failed_fetch" @($provider, $models)) -ForegroundColor Yellow
        }
    }
    
    # Загрузка выбранных моделей
    Write-Host ''
    Write-Host (Msg "step_8_start_download") -ForegroundColor Cyan
    Write-Host ''
    
    foreach ($provider in $selectedModels.Keys) {
        foreach ($model in $selectedModels[$provider]) {
            Download-Model -Provider $provider -ModelId $model -InstallDir $InstallDir
        }
    }
    
    Write-Host ''
    Write-Host (Msg "step_8_completed") -ForegroundColor Green
    Write-Host ''
    
} catch {
    Write-Host (Msg "step_8_error" @($_.Exception.Message)) -ForegroundColor Red
    Write-Host (Msg "step_8_skip") -ForegroundColor Yellow
}

return $null