# PowerShell скрипт для запуска тестов ai-assistant

param(
    [switch]$Coverage,
    [switch]$Verbose,
    [string]$Markers,
    [switch]$OpenCoverage
)

# Путь к Python
$python = "python"

# Проверка наличия Python
if (-not (Get-Command $python -ErrorAction SilentlyContinue)) {
    Write-Error "Python не найден. Установите Python 3.10+"
    exit 1
}

# Установка зависимостей если нужно
if (-not (Test-Path "venv")) {
    Write-Host "Создание виртуального окружения..."
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    pip install -r requirements-test.txt
}

# Запуск pytest
$cmd = "pytest"
if ($Coverage) {
    $cmd += " --cov=src --cov=plugins --cov=scripts"
    $cmd += " --cov-report=term-missing"
    $cmd += " --cov-report=html:htmlcov"
    $cmd += " --cov-report=xml:coverage.xml"
    $cmd += " --cov-config=.coveragerc"
}
if ($Verbose) {
    $cmd += " -v"
}
if ($Markers) {
    $cmd += " -m $Markers"
}

Write-Host "Запуск тестов: $cmd" -ForegroundColor Cyan
& $cmd

# Результат
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Все тесты пройдены успешно!" -ForegroundColor Green
} else {
    Write-Host "`n✗ Тесты провалились (exit code: $LASTEXITCODE)" -ForegroundColor Red
}

# Открытие отчета
if ($Coverage -and (Test-Path "htmlcov\index.html")) {
    if ($OpenCoverage) {
        Start-Process "htmlcov\index.html"
    }
}

exit $LASTEXITCODE
