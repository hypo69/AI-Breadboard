<#
.SYNOPSIS
    Модуль инициализации Python виртуального окружения (venv).
.DESCRIPTION
    Ищет поддерживаемый интерпретатор Python, создает venv и обновляет pip.
#>

param (
    [string]$InstallDir,
    [PSCustomObject]$Config
)

Write-Host ''
Write-Host (Msg "step_2") -ForegroundColor Cyan

$venvName = "venv"
if ($Config -and $Config.defaults -and $Config.defaults.venv_dir) {
    $venvName = $Config.defaults.venv_dir
}

$VenvDir    = Join-Path $InstallDir $venvName
$PythonPath = Join-Path $VenvDir 'Scripts\python.exe'

$venvOk = $false
if (Test-Path $PythonPath) {
    try {
        $pyVer = & $PythonPath --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host (Msg "step_2_existing" @($VenvDir, $pyVer)) -ForegroundColor Green
            $venvOk = $true
        } else {
            Write-Host (Msg "step_2_damaged") -ForegroundColor Yellow
        }
    } catch {
        Write-Host (Msg "step_2_err_launch" @($_)) -ForegroundColor Yellow
    }
}

if (-not $venvOk) {
    Write-Host (Msg "step_2_searching") -ForegroundColor Gray
    
    $sysPython = $null
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    $preferredVersions = @("3.13", "3.12", "3.11", "3.10")
    if ($Config -and $Config.defaults -and $Config.defaults.python_preferred_versions) {
        $preferredVersions = $Config.defaults.python_preferred_versions
    }

    if ($pyLauncher) {
        foreach ($ver in $preferredVersions) {
            try {
                $testPy = & py -$ver -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $testPy) {
                    $sysPython = $testPy.Trim()
                    Write-Host (Msg "step_2_py_found" @($sysPython)) -ForegroundColor Green
                    break
                }
            } catch {}
        }
    }
    
    if (-not $sysPython) {
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonCmd) {
            try {
                $verOut = & python --version 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $sysPython = $pythonCmd.Source
                    Write-Host (Msg "step_2_sys_found" @($sysPython, $verOut)) -ForegroundColor Green
                }
            } catch {}
        }
    }
    
    if (-not $sysPython) {
        Write-Host (Msg "step_2_py_not_found") -ForegroundColor Red
        Write-Host (Msg "step_2_py_install_tip") -ForegroundColor Yellow
        exit 1
    }
    
    if (Test-Path $VenvDir) {
        Write-Host (Msg "step_2_remove_old") -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvDir -ErrorAction SilentlyContinue
    }
    
    Write-Host (Msg "step_2_creating" @($VenvDir)) -ForegroundColor Cyan
    
    try {
        $venvResult = & $sysPython -m venv $VenvDir 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host (Msg "step_2_create_fail") -ForegroundColor Red
            Write-Host "Error details: $venvResult" -ForegroundColor Yellow
            exit 1
        }
    } catch {
        Write-Host (Msg "step_2_create_fail") -ForegroundColor Red
        Write-Host "Exception: $_" -ForegroundColor Yellow
        exit 1
    }
    
    if (-not (Test-Path $PythonPath)) {
        Write-Host (Msg "step_2_create_fail") -ForegroundColor Red
        exit 1
    }
    
    # Verify venv python works
    try {
        $pyVer = & $PythonPath --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host (Msg "step_2_create_fail") -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host (Msg "step_2_create_fail") -ForegroundColor Red
        exit 1
    }
    
    Write-Host (Msg "step_2_created_ok") -ForegroundColor Green
}

# Обновление pip, setuptools, wheel
Write-Host ''
Write-Host (Msg "step_3") -ForegroundColor Cyan
try {
    & $PythonPath -m pip install --upgrade pip setuptools wheel --quiet
    Write-Host (Msg "step_3_ok") -ForegroundColor Green
} catch {
    Write-Host (Msg "step_3_warn") -ForegroundColor Yellow
}

return $PythonPath
