<#
.SYNOPSIS
    Проверка, генерация и установка локальных SSL-сертификатов для ai-assistant.

.DESCRIPTION
    1. Проверяет наличие сертификатов в $env:USERPROFILE\.certs (localhost+2.pem, localhost+2-key.pem).
    2. Генерирует их через mkcert (если установлен) или встроенным генератором (Python cryptography).
    3. Автоматически включает в сертификат: localhost, 127.0.0.1, ::1, имя компьютера и все текущие IP-адреса сети.
    4. Импортирует сертификат в хранилища Windows (CurrentUser\My и CurrentUser\Root).
#>

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$certsDir  = Join-Path $env:USERPROFILE ".certs"
$certPath  = Join-Path $certsDir "localhost+2.pem"
$keyPath   = Join-Path $certsDir "localhost+2-key.pem"
$pfxPath   = Join-Path $certsDir "localhost+2.pfx"
$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"

if (-not (Test-Path $certsDir)) {
    New-Item -ItemType Directory -Force -Path $certsDir | Out-Null
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              ai-assistant — НАСТРОЙКА SSL СЕРТИФИКАТОВ            ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Получаем все локальные IPv4 адреса
$localIps = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notmatch '^(169\.254)' } |
    Select-Object -ExpandProperty IPAddress -Unique)

$ipListStr = ($localIps | ForEach-Object { "'$_'" }) -join ", "

# 1. Проверка / Генерация сертификатов
$needsGeneration = $true
if ((Test-Path $certPath) -and (Test-Path $keyPath)) {
    # Проверяем, является ли текущий сертификат валидным с SERVER_AUTH
    $checkScript = "
from cryptography import x509
from pathlib import Path
p = Path(r'$certPath')
try:
    c = x509.load_pem_x509_certificate(p.read_bytes())
    has_eku = any(isinstance(e.value, x509.ExtendedKeyUsage) for e in c.extensions)
    is_ca = any(isinstance(e.value, x509.BasicConstraints) and e.value.ca for e in c.extensions)
    if has_eku and not is_ca:
        print('VALID')
    else:
        print('REGENERATE')
except Exception:
    print('REGENERATE')
"
    $pyTarget = if (Test-Path $pythonExe) { $pythonExe } else { "python" }
    $checkRes = & $pyTarget -c $checkScript 2>$null
    if ($checkRes -match 'VALID') {
        $needsGeneration = $false
    }
}

if ($needsGeneration) {
    Write-Host "[1/3] Настройка доверенных SSL-сертификатов..." -ForegroundColor Cyan

    $mkcertCmd = Get-Command mkcert -ErrorAction SilentlyContinue
    $generated = $false

    if ($mkcertCmd) {
        Write-Host "    Использование mkcert для генерации доверенного сертификата..." -ForegroundColor DarkGray
        try {
            & mkcert -install
            $mkcertArgs = @("-cert-file", $certPath, "-key-file", $keyPath, "localhost", "127.0.0.1", "::1", $env:COMPUTERNAME) + $localIps
            & mkcert $mkcertArgs
            $generated = $true
            Write-Host "    [OK] Сертификаты успешно сгенерированы через mkcert" -ForegroundColor Green
        } catch {
            Write-Host "    [WARN] Ошибка mkcert: $_" -ForegroundColor Yellow
        }
    }

    if (-not $generated) {
        Write-Host "    Генерация доверенного Root CA и сертификата через Python..." -ForegroundColor DarkGray
        $pyTarget = if (Test-Path $pythonExe) { $pythonExe } else { "python" }
        $genModule = Join-Path $scriptDir "scripts\maintenance\generate_ssl_certs.py"
        
        try {
            $genArgs = @($genModule) + $localIps
            $genOut = & $pyTarget @genArgs 2>&1
            if ($genOut -match 'SUCCESS') {
                $generated = $true
                Write-Host "    [OK] Сертификаты и Root CA успешно созданы:" -ForegroundColor Green
                Write-Host "        Сервер:  $certPath" -ForegroundColor Gray
                Write-Host "        Ключ:    $keyPath"  -ForegroundColor Gray
                Write-Host "        Root CA: $(Join-Path $certsDir 'rootCA.pem')" -ForegroundColor Gray
            } else {
                Write-Host "    [WARN] Ошибка генератора: $genOut" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    [WARN] Ошибка вызова Python: $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[1/3] Доверенные SSL-сертификаты уже настроены:" -ForegroundColor Green
    Write-Host "    $certPath" -ForegroundColor Gray
    Write-Host "    $keyPath"  -ForegroundColor Gray
}

# 2. Экспорт / Импорт в хранилища сертификатов Windows
if ((Test-Path $certPath) -and (Test-Path $keyPath)) {
    Write-Host ""
    Write-Host "[2/3] Добавление сертификата в доверенные сертификаты Windows..." -ForegroundColor Cyan
    try {
        $certObj = $null
        try {
            if ([System.Security.Cryptography.X509Certificates.X509Certificate2].GetMethod('CreateFromPemFile', [type[]]@([string], [string]))) {
                $certObj = [System.Security.Cryptography.X509Certificates.X509Certificate2]::CreateFromPemFile($certPath, $keyPath)
            }
        } catch {}

        if (-not $certObj) {
            $certBytes = [System.IO.File]::ReadAllBytes($certPath)
            $certObj = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
            $certObj.Import($certBytes)
        }
        
        # Импорт в Personal (My)
        $storeMy = New-Object System.Security.Cryptography.X509Certificates.X509Store("My", "CurrentUser")
        $storeMy.Open("ReadWrite")
        $storeMy.Add($certObj)
        $storeMy.Close()
        Write-Host "    [OK] Сертификат добавлен в CurrentUser\Personal" -ForegroundColor Green

        # Импорт в Trusted Root
        $storeRoot = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
        $storeRoot.Open("ReadWrite")
        $storeRoot.Add($certObj)
        $storeRoot.Close()
        Write-Host "    [OK] Сертификат добавлен в CurrentUser\Trusted Root" -ForegroundColor Green
    } catch {
        Write-Host "    [WARN] Не удалось автоматически импортировать в хранилище Windows: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "    [WARN] Файлы сертификатов отсутствуют — запуск сервера будет без SSL." -ForegroundColor Yellow
}


Write-Host ""
Write-Host "[3/3] Завершение настройки SSL" -ForegroundColor Cyan
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  SSL-СЕРТИФИКАТЫ ГОТОВЫ!                                      ║" -ForegroundColor Green
Write-Host "║  Локальный адрес: https://localhost:8000                      ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
