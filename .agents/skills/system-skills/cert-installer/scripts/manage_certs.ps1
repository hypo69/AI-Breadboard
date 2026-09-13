<#
.SYNOPSIS
    Проверка, генерация и установка локальных SSL-сертификатов для ai-breadboard.
.DESCRIPTION
    1. Проверяет наличие сертификатов в $env:USERPROFILE\.certs (localhost+2.pem, localhost+2-key.pem).
    2. Если -Force, удаляет старые и генерирует новые.
    3. Генерирует их через mkcert (если установлен) или встроенным генератором (Python cryptography).
    4. Автоматически включает в сертификат: localhost, 127.0.0.1, ::1, имя компьютера и все текущие IP-адреса сети.
    5. Импортирует сертификат в хранилища Windows (CurrentUser\My и CurrentUser\Root).
#>

param (
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$certsDir  = Join-Path $env:USERPROFILE ".certs"
$certPath  = Join-Path $certsDir "localhost+2.pem"
$keyPath   = Join-Path $certsDir "localhost+2-key.pem"
$rootDir   = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path) # Root of the skill
$projectRoot = Split-Path -Parent (Split-Path -Parent $rootDir) # Path to AI-Breadboard
$pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"

if (-not (Test-Path $certsDir)) {
    New-Item -ItemType Directory -Force -Path $certsDir | Out-Null
}

if ($Force) {
    Write-Host "[Cert] Форсированное обновление сертификатов..." -ForegroundColor Yellow
    if (Test-Path $certPath) { Remove-Item $certPath -Force }
    if (Test-Path $keyPath) { Remove-Item $keyPath -Force }
}

# (Existing logic from install_ssl_cert.ps1 continues here...)
$localIps = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notmatch '^(169\.254)' } |
    Select-Object -ExpandProperty IPAddress -Unique)

$needsGeneration = $true
if (-not $Force -and (Test-Path $certPath) -and (Test-Path $keyPath)) {
    # Check valid logic...
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
        Write-Host "    Использование mkcert..." -ForegroundColor DarkGray
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
        Write-Host "    Генерация через Python..." -ForegroundColor DarkGray
        $pyTarget = if (Test-Path $pythonExe) { $pythonExe } else { "python" }
        $genModule = Join-Path $projectRoot "scripts\maintenance\generate_ssl_certs.py"
        
        try {
            $genArgs = @($genModule) + $localIps
            $genOut = & $pyTarget @genArgs 2>&1
            if ($genOut -match 'SUCCESS') {
                $generated = $true
                Write-Host "    [OK] Сертификаты успешно созданы." -ForegroundColor Green
            } else {
                Write-Host "    [WARN] Ошибка генератора: $genOut" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    [WARN] Ошибка вызова Python: $_" -ForegroundColor Yellow
        }
    }
}

# (Import logic...)
if ((Test-Path $certPath) -and (Test-Path $keyPath)) {
    Write-Host "[2/3] Добавление в доверенные Windows..." -ForegroundColor Cyan
    try {
        $certObj = $null
        $certBytes = [System.IO.File]::ReadAllBytes($certPath)
        $certObj = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
        $certObj.Import($certBytes)
        
        $storeMy = New-Object System.Security.Cryptography.X509Certificates.X509Store("My", "CurrentUser")
        $storeMy.Open("ReadWrite")
        $storeMy.Add($certObj)
        $storeMy.Close()

        $storeRoot = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
        $storeRoot.Open("ReadWrite")
        $storeRoot.Add($certObj)
        $storeRoot.Close()
        Write-Host "    [OK] Сертификаты импортированы в хранилище" -ForegroundColor Green
    } catch {
        Write-Host "    [WARN] Ошибка импорта в хранилище: $_" -ForegroundColor Yellow
    }
}
