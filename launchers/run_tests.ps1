<#
.SYNOPSIS
    PowerShell script for running ai-breadboard / AI Breadboard tests.

.DESCRIPTION
    Test runner script for executing pytest with optional coverage reporting,
    verbose output, marker filtering, and automatic HTML coverage report opening.
    Supports virtual environment activation and cross-platform execution.

.PARAMETER Coverage
    Enable code coverage reporting (generates HTML and XML reports).

.PARAMETER Verbose
    Display verbose test output (-v flag).

.PARAMETER Markers
    Run only tests matching specified pytest markers.

.PARAMETER OpenCoverage
    Automatically open HTML coverage report in browser after tests complete.

.EXAMPLE
    .\run_tests.ps1
    .\run_tests.ps1 -Coverage -OpenCoverage
    .\run_tests.ps1 -Verbose -Markers "unit"
    .\run_tests.ps1 -Coverage -Verbose
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
