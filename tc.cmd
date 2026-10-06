:: Updated: 2026-10-06 08:31:58
@echo off
REM Запуск скрипта tc.ps1 с повышенными правами
SET "scriptPath=%~dp0tc.ps1"
powershell -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "%scriptPath%"' -Verb RunAs"
