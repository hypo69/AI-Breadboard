@echo off
REM Кроссплатформенный лончер для запуска FastAPI сервера
REM Работает на Windows (cmd.exe и PowerShell)

setlocal enabledelayedexpansion
chcp 65001 >nul

set "PROJECT_ROOT=%~dp0"

set "AIBREADBOARD_DIR=%PROJECT_ROOT%"
set "ASSIST_DIR=%PROJECT_ROOT%"
set "PYTHONUTF8=1"
set "PYTHONPATH=%PROJECT_ROOT%;!PYTHONPATH!"

set "PYTHON=python"

if exist "%PROJECT_ROOT%venv\Scripts\python.exe" (
    set "PYTHON=%PROJECT_ROOT%venv\Scripts\python.exe"
)

"%PYTHON%" "%PROJECT_ROOT%launchers\run.py" %*
endlocal
