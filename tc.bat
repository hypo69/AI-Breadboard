:: Updated: 2026-10-06 08:31:52
@echo off
REM Запуск скрипта tc.ps1 с повышенными правами
SET "scriptPath=%~dp0tc.ps1"
"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -Command "Start-Process \"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe\" -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "%scriptPath%"' -Verb RunAs"
