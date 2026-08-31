#!/bin/bash
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Кроссплатформенный установщик AI Breadboard для Linux/macOS
# =============================================================================
# Description:
#   Bash установщик для Unix-подобных систем с поддержкой мультиязычности
#   (RU/EN/ES/HE) и модульной архитектурой.
#
# Examples:
#   bash install.sh
#   bash install.sh --language en --install-dir /opt/ai-breadboard
#
# File: install.sh
# Project: AI Breadboard
# Package: Installation
# Module: Core
# Function: main
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

set -euo pipefail

# Определение платформы
PLATFORM=$(uname -s)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${INSTALL_DIR:-.}"
VENV_DIR="${INSTALL_DIR}/venv"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Язык по умолчанию
LANGUAGE="${LANGUAGE:-en}"

# Словарь сообщений
declare -A MESSAGES_EN=(
    [welcome]="🚀 Welcome to AI Breadboard Installer"
    [select_lang]="Select installation language:"
    [lang_selected]="✓ Selected language: %s"
    [step_1]="[1/6] Checking Python interpreter..."
    [step_1_found]="✓ Found Python %s: %s"
    [step_1_not_found]="✗ Python not found. Install Python 3.10+"
    [step_2]="[2/6] Creating virtual environment..."
    [step_2_ok]="✓ Virtual environment created"
    [step_2_exists]="✓ Virtual environment already exists"
    [step_3]="[3/6] Upgrading pip and tools..."
    [step_3_ok]="✓ pip upgraded"
    [step_4]="[4/6] Installing dependencies..."
    [step_4_menu]="Select installation profile:"
    [step_4_opt_1]="[1] Full installation (recommended)"
    [step_4_opt_2]="[2] Core only"
    [step_4_opt_3]="[3] Core + AI"
    [step_4_opt_4]="[4] Full + Dev"
    [step_4_opt_5]="[5] Skip"
    [step_4_ok]="✓ Dependencies installed"
    [step_5]="[5/6] Checking SSL certificates..."
    [step_5_ok]="✓ SSL certificates found"
    [step_6]="[6/6] Final verification..."
    [step_6_ok]="✓ Environment ready"
    [finish]="✅ Installation completed successfully!"
    [error]="✗ Error: %s"
)

declare -A MESSAGES_RU=(
    [welcome]="🚀 Добро пожаловать в установщик AI Breadboard"
    [select_lang]="Выберите язык установки:"
    [lang_selected]="✓ Выбран язык: %s"
    [step_1]="[1/6] Проверка Python интерпретатора..."
    [step_1_found]="✓ Найден Python %s: %s"
    [step_1_not_found]="✗ Python не найден. Установите Python 3.10+"
    [step_2]="[2/6] Создание виртуального окружения..."
    [step_2_ok]="✓ Виртуальное окружение создано"
    [step_2_exists]="✓ Виртуальное окружение уже существует"
    [step_3]="[3/6] Обновление pip и инструментов..."
    [step_3_ok]="✓ pip обновлен"
    [step_4]="[4/6] Установка зависимостей..."
    [step_4_menu]="Выберите профиль установки:"
    [step_4_opt_1]="[1] Полная установка (рекомендуется)"
    [step_4_opt_2]="[2] Только Core"
    [step_4_opt_3]="[3] Core + AI"
    [step_4_opt_4]="[4] Полная + Dev"
    [step_4_opt_5]="[5] Пропустить"
    [step_4_ok]="✓ Зависимости установлены"
    [step_5]="[5/6] Проверка SSL сертификатов..."
    [step_5_ok]="✓ SSL сертификаты найдены"
    [step_6]="[6/6] Финальная проверка..."
    [step_6_ok]="✓ Окружение готово к работе"
    [finish]="✅ Установка завершена успешно!"
    [error]="✗ Ошибка: %s"
)

declare -A MESSAGES_ES=(
    [welcome]="🚀 Bienvenido al instalador de AI Breadboard"
    [select_lang]="Seleccione idioma de instalación:"
    [lang_selected]="✓ Idioma seleccionado: %s"
    [step_1]="[1/6] Verificando intérprete Python..."
    [step_1_found]="✓ Python %s encontrado: %s"
    [step_1_not_found]="✗ Python no encontrado. Instale Python 3.10+"
    [step_2]="[2/6] Creando entorno virtual..."
    [step_2_ok]="✓ Entorno virtual creado"
    [step_2_exists]="✓ Entorno virtual ya existe"
    [step_3]="[3/6] Actualizando pip..."
    [step_3_ok]="✓ pip actualizado"
    [step_4]="[4/6] Instalando dependencias..."
    [step_4_menu]="Seleccione perfil de instalación:"
    [step_4_opt_1]="[1] Instalación completa (recomendado)"
    [step_4_opt_2]="[2] Solo Core"
    [step_4_opt_3]="[3] Core + AI"
    [step_4_opt_4]="[4] Completo + Dev"
    [step_4_opt_5]="[5] Omitir"
    [step_4_ok]="✓ Dependencias instaladas"
    [step_5]="[5/6] Verificando certificados SSL..."
    [step_5_ok]="✓ Certificados SSL encontrados"
    [step_6]="[6/6] Verificación final..."
    [step_6_ok]="✓ Entorno listo"
    [finish]="✅ ¡Instalación completada exitosamente!"
    [error]="✗ Error: %s"
)

# Функция получения сообщения
msg() {
    local key="$1"
    local lang_var="MESSAGES_${LANGUAGE^^}"
    local -n messages="${lang_var}"
    
    if [[ -v messages[$key] ]]; then
        printf "${messages[$key]}" "${@:2}"
    else
        echo "$key"
    fi
}

# Функция выбора языка
select_language() {
    echo -e "${BLUE}Select language / Выберите язык / Seleccione idioma:${NC}"
    echo "[1] English"
    echo "[2] Русский"
    echo "[3] Español"
    echo ""
    read -p "Choice [1]: " choice
    choice=${choice:-1}
    
    case "$choice" in
        1) LANGUAGE="en" ;;
        2) LANGUAGE="ru" ;;
        3) LANGUAGE="es" ;;
        *) LANGUAGE="en" ;;
    esac
    
    echo -e "${GREEN}$(msg lang_selected "$LANGUAGE")${NC}"
}

# Функция поиска Python
find_python() {
    echo -e "${BLUE}$(msg step_1)${NC}"
    
    local versions=("3.13" "3.12" "3.11" "3.10")
    
    for version in "${versions[@]}"; do
        if command -v "python${version}" &> /dev/null; then
            local python_path=$(command -v "python${version}")
            echo -e "${GREEN}$(msg step_1_found "$version" "$python_path")${NC}"
            echo "$python_path"
            return 0
        fi
    done
    
    if command -v python3 &> /dev/null; then
        local python_path=$(command -v python3)
        echo -e "${GREEN}$(msg step_1_found "3.x" "$python_path")${NC}"
        echo "$python_path"
        return 0
    fi
    
    echo -e "${RED}$(msg step_1_not_found)${NC}"
    return 1
}

# Функция создания venv
create_venv() {
    local python_path="$1"
    
    echo -e "${BLUE}$(msg step_2)${NC}"
    
    if [[ -d "$VENV_DIR" ]]; then
        echo -e "${GREEN}$(msg step_2_exists)${NC}"
        return 0
    fi
    
    if "$python_path" -m venv "$VENV_DIR"; then
        echo -e "${GREEN}$(msg step_2_ok)${NC}"
        return 0
    else
        return 1
    fi
}

# Функция обновления pip
upgrade_pip() {
    echo -e "${BLUE}$(msg step_3)${NC}"
    
    local python_path="$VENV_DIR/bin/python"
    
    if "$python_path" -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1; then
        echo -e "${GREEN}$(msg step_3_ok)${NC}"
        return 0
    else
        return 1
    fi
}

# Функция установки зависимостей
install_dependencies() {
    local profile="${1:-1}"
    
    echo -e "${BLUE}$(msg step_4)${NC}"
    
    local python_path="$VENV_DIR/bin/python"
    local req_files=()
    
    case "$profile" in
        1) req_files=("requirements.txt") ;;
        2) req_files=("install/req/requirements-core.txt") ;;
        3) req_files=("install/req/requirements-core.txt" "install/req/requirements-ai.txt") ;;
        4) req_files=("requirements.txt" "install/req/requirements-test.txt" "install/req/requirements-docs.txt") ;;
        5) return 0 ;;
        *) req_files=("requirements.txt") ;;
    esac
    
    local cmd=("$python_path" "-m" "pip" "install")
    
    for req_file in "${req_files[@]}"; do
        local req_path="$INSTALL_DIR/$req_file"
        if [[ -f "$req_path" ]]; then
            cmd+=("-r" "$req_path")
        fi
    done
    
    if "${cmd[@]}" > /dev/null 2>&1; then
        echo -e "${GREEN}$(msg step_4_ok)${NC}"
        return 0
    else
        return 1
    fi
}

# Функция проверки окружения
verify_environment() {
    echo -e "${BLUE}$(msg step_6)${NC}"
    
    local python_path="$VENV_DIR/bin/python"
    local modules=("fastapi" "uvicorn" "dotenv" "pydantic")
    
    for module in "${modules[@]}"; do
        if ! "$python_path" -c "import $module" 2>/dev/null; then
            return 1
        fi
    done
    
    echo -e "${GREEN}$(msg step_6_ok)${NC}"
    return 0
}

# Главная функция
main() {
    echo -e "${BLUE}$(msg welcome)${NC}"
    echo ""
    
    select_language
    echo ""
    
    read -p "Installation directory [current]: " input_dir
    INSTALL_DIR="${input_dir:-.}"
    VENV_DIR="$INSTALL_DIR/venv"
    
    local python_path
    python_path=$(find_python) || return 1
    echo ""
    
    create_venv "$python_path" || return 1
    echo ""
    
    upgrade_pip || return 1
    echo ""
    
    echo -e "${BLUE}$(msg step_4_menu)${NC}"
    echo "$(msg step_4_opt_1)"
    echo "$(msg step_4_opt_2)"
    echo "$(msg step_4_opt_3)"
    echo "$(msg step_4_opt_4)"
    echo "$(msg step_4_opt_5)"
    echo ""
    
    read -p "Choice [1]: " profile
    profile=${profile:-1}
    echo ""
    
    install_dependencies "$profile" || return 1
    echo ""
    
    verify_environment || return 1
    echo ""
    
    echo -e "${GREEN}$(msg finish)${NC}"
    return 0
}

# Обработка аргументов командной строки
while [[ $# -gt 0 ]]; do
    case $1 in
        --language)
            LANGUAGE="$2"
            shift 2
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Запуск установщика
if main; then
    exit 0
else
    echo -e "${RED}$(msg error "Installation failed")${NC}"
    exit 1
fi
