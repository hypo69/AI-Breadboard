@echo off
REM Batch script for Google Drive synchronization management

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "SETUP_SCRIPT=%SCRIPT_DIR%scripts\setup_google_drive_sync.py"

REM Default command is help
set "COMMAND=%1"
if "%COMMAND%"=="" (
    set "COMMAND=help"
)

REM Process command
if /i "%COMMAND%"=="init" (
    echo 🔧 Initializing Google Drive synchronization...
    python "%SETUP_SCRIPT%" --init
    goto end
)

if /i "%COMMAND%"=="sync" (
    echo ⏳ Starting synchronization...
    python "%SETUP_SCRIPT%" --sync-now
    goto end
)

if /i "%COMMAND%"=="start" (
    echo 🚀 Starting automatic synchronization scheduler...
    echo 💡 Tip: You can close this window. The scheduler will continue running.
    echo.
    python "%SETUP_SCRIPT%" --start-scheduler
    goto end
)

if /i "%COMMAND%"=="status" (
    echo 📊 Synchronization Status:
    python "%SETUP_SCRIPT%" --status
    goto end
)

REM Default: show help
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║       Google Drive Synchronization Management Tool            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Usage:
echo   sync.cmd [COMMAND]
echo.
echo Commands:
echo   init              - Initialize synchronization (first time setup)
echo   sync              - Synchronize data now
echo   start             - Start automatic scheduler
echo   status            - Show synchronization status
echo   help              - Show this help message
echo.
echo Examples:
echo   sync.cmd init
echo   sync.cmd sync
echo   sync.cmd start
echo   sync.cmd status
echo.

:end
endlocal
