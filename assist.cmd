@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set AIBREADBOARD_DIR=C:\Users\onela\AppData\Local\AI Breadboard
set ASSIST_DIR=C:\Users\onela\AppData\Local\AI Breadboard
set PYTHONPATH=%AIBREADBOARD_DIR%;%PYTHONPATH%
if exist "%AIBREADBOARD_DIR%\venv\Scripts\python.exe" (
    "%AIBREADBOARD_DIR%\venv\Scripts\python.exe" -m scripts.dev.assist_cli %*
) else (
    python -m scripts.dev.assist_cli %*
)
endlocal
