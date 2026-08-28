<#
.SYNOPSIS
    PowerShell скрипт для запуска тестов ai-breadboard / AI Breadboard.
#>

param(
    [switch]$Coverage,
    [switch]$Verbose,
    [string]$Markers,
    [switch]$OpenCoverage
)

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) { $scriptDir = (Get-Location).Path }

# Определение корня проекта (если скрипт находится в директории launchers/)
$projectRoot = $scriptDir
if ((Split-Path -Leaf $projectRoot) -eq "launchers" -or -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if (Test-Path (Join-Path $parent "main.py")) {
        $projectRoot = $parent
    }
}
Set-Location $projectRoot

# Путь к Python
$python = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

# Проверка наличия Python
if (-not (Get-Command $python -ErrorAction SilentlyContinue) -and -not (Test-Path $python)) {
    Write-Error "Python не найден. Установите Python 3.10+"
    exit 1
}

# Активация venv если есть
$venvActivate = Join-Path $projectRoot "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
}

# Запуск pytest
$pytestExe = Join-Path $projectRoot "venv\Scripts\pytest.exe"
$pytestCmd = if (Test-Path $pytestExe) { $pytestExe } else { "pytest" }
$cmdArgs = @()

if ($Coverage) {
    $cmdArgs += "--cov=core"
    $cmdArgs += "--cov-report=term-missing"
    $cmdArgs += "--cov-report=html:htmlcov"
    $cmdArgs += "--cov-report=xml:coverage.xml"
    $cmdArgs += "--cov-config=.coveragerc"
}
if ($Verbose) {
    $cmdArgs += "-v"
}
if ($Markers) {
    $cmdArgs += "-m", $Markers
}

Write-Host "Запуск тестов: $pytestCmd $($cmdArgs -join ' ')" -ForegroundColor Cyan
& $pytestCmd @cmdArgs

# Результат
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Все тесты пройдены успешно!" -ForegroundColor Green
} else {
    Write-Host "`n✗ Тесты провалились (exit code: $LASTEXITCODE)" -ForegroundColor Red
}

# Открытие отчета
if ($Coverage -and (Test-Path (Join-Path $projectRoot "htmlcov\index.html"))) {
    if ($OpenCoverage) {
        Start-Process (Join-Path $projectRoot "htmlcov\index.html")
    }
}

exit $LASTEXITCODE
