<#
.SYNOPSIS
    Перезапускает туннель Cloudflare Tunnel (cloudflared).

.DESCRIPTION
    Завершает существующие процессы cloudflared, находит исполняемый файл
    (включая C:\Users\onela\AppData\Local\bin\cloudflared.exe или PATH),
    и запускает туннель с использованием CLOUDFLARE_TUNNEL_TOKEN из .env.

.EXAMPLE
    .\launchers\Run-Cloudflared.ps1
#>

[CmdletBinding()]
param (
    [string]$CloudflaredExe = ''
)

$ErrorActionPreference = 'Stop'

Write-Host ''
Write-Host '╔═══════════════════════════════════════════════════════════════╗' -ForegroundColor Cyan
Write-Host '║              CLOUDFLARE TUNNEL (kino.davidka.net)             ║' -ForegroundColor Cyan
Write-Host '╚═══════════════════════════════════════════════════════════════╝' -ForegroundColor Cyan

# Определение корня проекта
$scriptDir = $PSScriptRoot
if ((Split-Path -Leaf $scriptDir) -eq "launchers" -or -not (Test-Path (Join-Path $scriptDir "main.py"))) {
    $parent = Split-Path -Parent $scriptDir
    if (Test-Path (Join-Path $parent "main.py")) {
        $projectRoot = $parent
    } else {
        $projectRoot = $scriptDir
    }
} else {
    $projectRoot = $scriptDir
}

$envFile = Join-Path $projectRoot ".env"
$token = $null

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim() -replace "^['`"]|['`"]$"
            if ($key -eq "CLOUDFLARE_TUNNEL_TOKEN") {
                $token = $val
            }
        }
    }
}

if (-not $token) {
    Write-Host "[ERROR] CLOUDFLARE_TUNNEL_TOKEN не найден в .env!" -ForegroundColor Red
    Write-Host "Пожалуйста, добавьте CLOUDFLARE_TUNNEL_TOKEN в .env" -ForegroundColor Yellow
    exit 1
}

# Поиск cloudflared.exe
$exeCandidates = @(
    $CloudflaredExe,
    "C:\Users\onela\AppData\Local\bin\cloudflared.exe",
    (Join-Path $projectRoot "cloudflared.exe"),
    (Join-Path $env:LOCALAPPDATA "bin\cloudflared.exe")
)

$resolvedExe = $null
foreach ($cand in $exeCandidates) {
    if ($cand -and (Test-Path $cand)) {
        $resolvedExe = $cand
        break
    }
}

if (-not $resolvedExe) {
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) {
        $resolvedExe = $cmd.Source
    }
}

if (-not $resolvedExe) {
    Write-Host "[ERROR] cloudflared.exe не найден ни в AppData\Local\bin, ни в PATH." -ForegroundColor Red
    exit 1
}

Write-Host "    Исполняемый файл: $resolvedExe" -ForegroundColor Gray

# Завершение существующих процессов cloudflared
Write-Host "    Остановка предыдущих процессов cloudflared..." -ForegroundColor DarkGray
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq 'cloudflared.exe' } |
    ForEach-Object {
        try {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            Write-Host "        Остановлен PID $($_.ProcessId)" -ForegroundColor DarkGray
        } catch {}
    }

Start-Sleep -Seconds 1

# Подготовка директории логов
$logsDir = Join-Path $projectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}
$logFilePath = Join-Path $logsDir "cloudflared.log"

$argList = @("--no-autoupdate", "--loglevel", "error", "--logfile", $logFilePath, "tunnel", "run", "--token", $token)

Write-Host "    Запуск туннеля в фоновом режиме..." -ForegroundColor Cyan
$cfProcess = Start-Process $resolvedExe -ArgumentList $argList -PassThru -WindowStyle Minimized

if (-not $cfProcess) {
    Write-Host "[ERROR] Не удалось запустить cloudflared." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ✅ CLOUDFLARE TUNNEL ЗАПУЩЕН!                                  " -ForegroundColor Green
Write-Host "  Внешний адрес: https://kino.davidka.net                       " -ForegroundColor Green
Write-Host "  Лог-файл:      $logFilePath                                    " -ForegroundColor Gray
Write-Host "  PID процесса:  $($cfProcess.Id)                               " -ForegroundColor Gray
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
