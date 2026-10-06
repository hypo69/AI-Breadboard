<#
=============================================================================
Process Name: AI-Breadboard Automation - Run Tests
=============================================================================
Description:
  Сценарий запуска полного набора модульных и интеграционных тестов платформы (pytest).

  Зачем нужен этот скрипт:
    1. Автоматизация TDD-контроля: единая команда для прогона всех тестов в каталоге tests/.
    2. Расчет и визуализация покрытия кода: генерация отчетов покрытия (--cov) и HTML-отчетов.
    3. Фильтрация и селективный запуск: поддержка запуска отдельных тестов, маркеров (-m)
       и режима остановки на первой ошибке (-x).

File: run_tests.ps1
Project: ai-breadboard
Package: launchers
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-06 00:05:00
=============================================================================

.SYNOPSIS
    Тестовый раннер для запуска pytest с расчетом покрытия кода и генерацией отчетов.

.DESCRIPTION
    Инициализирует тестовую среду Python, передает pytest аргументы фильтрации,
    собирает метрики coverage и опционально открывает HTML-отчет в браузере.

.PARAMETER TestPath
    Путь к конкретному тестовому файлу или директории (по умолчанию: tests/).

.PARAMETER Coverage
    Флаг включения сбора покрытия кода с отчетом в терминале.

.PARAMETER HtmlCoverage
    Генерация подробного HTML-отчета покрытия в папке htmlcov/ с открытием в браузере.

.PARAMETER Verbose
    Включение подробного вывода pytest (-v).

.PARAMETER FailFast
    Остановка выполнения тестов при первом упавшем тесте (-x).

.PARAMETER Marker
    Выполнение тестов только с указанным pytest-маркером (например: unit, integration).

.EXAMPLE
    .\run_tests.ps1
    Запуск всех тестов в стандартном режиме.

.EXAMPLE
    .\run_tests.ps1 -Coverage -HtmlCoverage
    Запуск всех тестов с расчетом покрытия и открытием HTML-отчета.
#>

param(
    [switch]$Coverage,
    [switch]$Verbose,
    [string]$Markers,
    [switch]$OpenCoverage
)

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) { $scriptDir = (Get-Location).Path }

# Project root detection (if script is in launchers/ directory)
$projectRoot = $scriptDir
if ((Split-Path -Leaf $projectRoot) -eq "launchers" -or -not (Test-Path (Join-Path $projectRoot "main.py"))) {
    $parent = Split-Path -Parent $projectRoot
    if (Test-Path (Join-Path $parent "main.py")) {
        $projectRoot = $parent
    }
}
Set-Location $projectRoot

# Path to Python
$python = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

# Checking for Python
if (-not (Get-Command $python -ErrorAction SilentlyContinue) -and -not (Test-Path $python)) {
    Write-Error "Python not found. Install Python 3.10+"
    exit 1
}

# Activating venv if available
$venvActivate = Join-Path $projectRoot "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
}

# Running pytest
$pytestExe = Join-Path $projectRoot "venv\Scripts\pytest.exe"
$pytestCmd = if (Test-Path $pytestExe) { $pytestExe } else { "pytest" }
$cmdArgs = @()

if ($Coverage) {
    $cmdArgs += "--cov=core"
    $cmdArgs += "--cov-report=term-missing"
    $cmdArgs += "--cov-report=html:tests/coverage"
    $cmdArgs += "--cov-report=xml:coverage.xml"
    $cmdArgs += "--cov-config=.coveragerc"
}
if ($Verbose) {
    $cmdArgs += "-v"
}
if ($Markers) {
    $cmdArgs += "-m", $Markers
}

Write-Host "Running tests: $pytestCmd $($cmdArgs -join ' ')" -ForegroundColor Cyan
& $pytestCmd @cmdArgs

# Result
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ All tests passed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n✗ Tests failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
}

# Opening report
if ($Coverage -and (Test-Path (Join-Path $projectRoot "tests\coverage\index.html"))) {
    if ($OpenCoverage) {
        Start-Process (Join-Path $projectRoot "tests\coverage\index.html")
    }
}

exit $LASTEXITCODE
