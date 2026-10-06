<#
=============================================================================
Process Name: AI-Breadboard Automation - Start Gemini CLI
=============================================================================
Description:
  Быстрый запуск сессии Google Gemini CLI в контексте проекта AI Breadboard.

  Зачем нужен этот скрипт:
    1. Автоматическая изоляция среды: активирует виртуальное окружение venv перед запуском.
    2. Вызов интерактивной консоли: стартует утилиту gemini с предустановленной быстрой моделью gemini-3.1-flash-lite.

File: Start-GeminiCli.ps1
Project: ai-breadboard
Package: root
Author: hypo69
Copyright: © 2026 hypo69
Updated: 2026-10-06 00:05:00
=============================================================================

.SYNOPSIS
    Активация venv и запуск Gemini CLI.

.DESCRIPTION
    Выполняет проверку и активацию окружения Python, после чего передает управление
    интерактивному CLI-интерфейсу модели Gemini.

.EXAMPLE
    .\Start-GeminiCli.ps1
#>

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
