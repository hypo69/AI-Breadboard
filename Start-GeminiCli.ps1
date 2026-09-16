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
