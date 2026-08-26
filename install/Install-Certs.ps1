<#
.SYNOPSIS
    Модуль проверки и генерации SSL-сертификатов.
.DESCRIPTION
    Проверяет наличие локальных сертификатов для безопасного HTTPS (localhost+2.pem)
    или запускает генератор install_ssl_cert.ps1.
#>

param (
    [string]$InstallDir,
    [PSCustomObject]$Config
)

Write-Host ''
Write-Host (Msg "step_5") -ForegroundColor Cyan

$certsDir = Join-Path $env:USERPROFILE ".certs"
$certFile = Join-Path $certsDir "localhost+2.pem"
$keyFile  = Join-Path $certsDir "localhost+2-key.pem"
$sslScriptPath = Join-Path $InstallDir "install_ssl_cert.ps1"

if ($Config -and $Config.paths) {
    if ($Config.paths.certs_dir) {
        $expandedCerts = [System.Environment]::ExpandEnvironmentVariables($Config.paths.certs_dir)
        $certsDir = $expandedCerts
    }
    if ($Config.paths.cert_file) { $certFile = Join-Path $certsDir $Config.paths.cert_file }
    if ($Config.paths.key_file)  { $keyFile  = Join-Path $certsDir $Config.paths.key_file }
    if ($Config.paths.ssl_script) { $sslScriptPath = Join-Path $InstallDir $Config.paths.ssl_script }
}

if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
    Write-Host (Msg "step_5_found" @($certFile)) -ForegroundColor Green
} else {
    Write-Host (Msg "step_5_not_found") -ForegroundColor Yellow
    if (Test-Path $sslScriptPath) {
        & $sslScriptPath
    } else {
        Write-Host (Msg "step_5_missing_script" @($sslScriptPath)) -ForegroundColor Yellow
    }
}
