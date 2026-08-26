<#
.SYNOPSIS
    Запуск и управление локальным сервером Microsoft Foundry.

.DESCRIPTION
    Скрипт для проверки, запуска и управления локальной службой Microsoft AI Foundry.
    Использует CLI команду 'foundry server start' и определяет активный порт.

.PARAMETER Action
    start | stop | restart | status

.EXAMPLE
    .\Run-Foundry.ps1
    .\Run-Foundry.ps1 -Action restart
    .\Run-Foundry.ps1 -Action stop
#>

[CmdletBinding()]
param (
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start'
)

$ErrorActionPreference = 'Continue'

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir) -and $env:AIBREADBOARD_DIR -and (Test-Path $env:AIBREADBOARD_DIR)) {
    $scriptDir = $env:AIBREADBOARD_DIR
}
if ([string]::IsNullOrEmpty($scriptDir) -and $MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = (Get-Location).Path
}
$env:AIBREADBOARD_DIR = $scriptDir
$env:ASSIST_DIR = $scriptDir

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              MICROSOFT AI FOUNDRY LOCAL SERVICE               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия CLI
function Test-FoundryCli {
    try {
        Get-Command foundry -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Определение порта
function Get-FoundryPort {
    try {
        $output = foundry server status 2>&1 | Out-String
        $match  = [regex]::Match($output, 'http://127\.0\.0\.1:(\d+)')
        if ($match.Success) {
            $port = $match.Groups[1].Value
            try {
                $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" `
                    -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                if ($r.StatusCode -eq 200) {
                    return $port
                }
            } catch { }
        }
    } catch {}
    return $null
}

if (-not (Test-FoundryCli)) {
    Write-Error "Foundry CLI ('foundry') не найден в вашей переменной PATH."
    Write-Host "Пожалуйста, установите Microsoft AI Foundry Local CLI." -ForegroundColor Yellow
    exit 1
}

if ($Action -eq 'stop') {
    Write-Host "🛑 Останавливаем службу Microsoft AI Foundry..." -ForegroundColor Yellow
    try {
        foundry server stop 2>&1 | Out-Host
        Write-Host "✅ Служба успешно остановлена." -ForegroundColor Green
    } catch {
        Write-Error "Не удалось остановить Foundry: $_"
    }
    exit 0
}

if ($Action -eq 'restart') {
    Write-Host "🔄 Перезапускаем службу Microsoft AI Foundry..." -ForegroundColor Yellow
    try {
        foundry server stop 2>&1 | Out-Host
        Start-Sleep -Seconds 2
    } catch {}
    $Action = 'start'
}

$port = Get-FoundryPort

if ($Action -eq 'status') {
    if ($port) {
        Write-Host "✅ Foundry запущен на порту $port" -ForegroundColor Green
        Write-Host "Base URL: http://localhost:$port/v1/" -ForegroundColor Gray
    } else {
        Write-Host "❌ Foundry не запущен." -ForegroundColor Red
    }
    exit 0
}

if ($Action -eq 'start') {
    if ($port) {
        Write-Host "✅ Foundry уже запущен на порту $port" -ForegroundColor Green
        Write-Host "Base URL: http://localhost:$port/v1/" -ForegroundColor Gray
    } else {
        Write-Host "🚀 Запуск локальной службы Microsoft AI Foundry..." -ForegroundColor Cyan
        try {
            $logsDir = Join-Path $scriptDir "logs"
            if (-not (Test-Path $logsDir)) {
                New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
            }
            $logOutPath = Join-Path $logsDir "foundry_stdout.log"
            $logErrPath = Join-Path $logsDir "foundry_stderr.log"
            Start-Process -FilePath "foundry" -ArgumentList "server", "start" -RedirectStandardOutput $logOutPath -RedirectStandardError $logErrPath -WindowStyle Minimized
            
            for ($i = 1; $i -le 15; $i++) {
                Start-Sleep -Seconds 2
                $port = Get-FoundryPort
                if ($port) {
                    Write-Host ""
                    Write-Host "✅ Foundry успешно запущен!" -ForegroundColor Green
                    Write-Host "Порт:     $port" -ForegroundColor Gray
                    Write-Host "Base URL: http://localhost:$port/v1/" -ForegroundColor Green
                    Write-Host ""
                    
                    # Записываем FOUNDRY_BASE_URL в .env для автоматической настройки
                    $envFile = Join-Path $scriptDir ".env"
                    if (Test-Path $envFile) {
                        $content = Get-Content $envFile
                        $updated = $false
                        $newContent = @()
                        foreach ($line in $content) {
                            if ($line -match "^FOUNDRY_BASE_URL=") {
                                $newContent += "FOUNDRY_BASE_URL=http://localhost:$port"
                                $updated = $true
                            } else {
                                $newContent += $line
                            }
                        }
                        if (-not $updated) {
                            $newContent += "FOUNDRY_BASE_URL=http://localhost:$port"
                        }
                        $newContent | Set-Content $envFile
                        Write-Host "📝 Обновлен FOUNDRY_BASE_URL в файле .env" -ForegroundColor Gray
                    }
                    break
                }
                Write-Host "⏳ Ожидание запуска Foundry... ($i/15)" -ForegroundColor Gray
            }
            if (-not $port) {
                Write-Error "Таймаут запуска службы Foundry. Проверьте логи через 'foundry server status'"
            }
        } catch {
            Write-Error "Критическая ошибка при запуске Foundry: $_"
        }
    }
}
