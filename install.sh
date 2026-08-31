#!/bin/bash
#
# Кроссплатформенный установщик AI Breadboard
# Работает на Linux, macOS и Windows (WSL/Git Bash)
#
# Использование:
#   ./install.sh
#   ./install.sh --lang ru
#   ./install.sh --install-dir /opt/ai-breadboard
#   ./install.sh --skip-models
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Установить переменные окружения
export AIBREADBOARD_DIR="$PROJECT_ROOT"
export ASSIST_DIR="$PROJECT_ROOT"
export PYTHONUTF8=1
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Найти Python интерпретатор
PYTHON=""

if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON="$PROJECT_ROOT/venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "❌ Python не найден. Пожалуйста, установите Python 3.10+"
    exit 1
fi

# Выполнить установщик
"$PYTHON" "$PROJECT_ROOT/scripts/cli/installer.py" "$@"
