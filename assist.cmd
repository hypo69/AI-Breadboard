@echo off
REM Кроссплатформенный CLI ассистент для AI-Breadboard
REM Работает на Windows (cmd.exe и PowerShell)
REM
REM Использование:
REM   assist start
REM   assist stop
REM   assist status
REM   assist providers

setlocal enabledelayedexpansion
chcp 65001 >nul

REM Определить директорию проекта
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"

REM Использовать переменную окружения если установлена
if not "!AIBREADBOARD_DIR!"=="" set "PROJECT_ROOT=!AIBREADBOARD_DIR!"

REM Установить переменные окружения
set "AIBREADBOARD_DIR=%PROJECT_ROOT%"
set "ASSIST_DIR=%PROJECT_ROOT%"
set "PYTHONUTF8=1"
set "PYTHONPATH=%PROJECT_ROOT%;!PYTHONPATH!"

REM Найти Python интерпретатор
set "PYTHON=python"

if exist "%PROJECT_ROOT%\venv\Scripts\python.exe" (
    set "PYTHON=%PROJECT_ROOT%\venv\Scripts\python.exe"
)

REM Выполнить CLI ассистент (новый Python скрипт)
"%PYTHON%" "%PROJECT_ROOT%\scripts\cli\assist.py" %*
endlocal
