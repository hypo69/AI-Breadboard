# =============================================================================
# Process Name: AI-Breadboard Automation - Start-Geminicli Script
# =============================================================================
# Description:
#   PowerShell-сценарий системного обслуживания и запуска (Start-GeminiCli).
#
# Usage Examples:
#   PowerShell Execution:
#     .\Start-GeminiCli.ps1
#
# File: Start-GeminiCli.ps1
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:20:26
# =============================================================================

# -----------------------------------------------------------------------------
# Файл: Start-GeminiCli.ps1
# Назначение: Активация виртуального окружения и запуск Gemini CLI.
# -----------------------------------------------------------------------------

# Активация виртуального окружения Python
$venvPath = Join-Path -Path $PSScriptRoot -ChildPath "venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    . $venvPath
} else {
    Write-Error "Виртуальное окружение не найдено по пути: $venvPath"
    exit 1
}

# Запуск Gemini CLI
gemini --model "gemini-3.1-flash-lite"
