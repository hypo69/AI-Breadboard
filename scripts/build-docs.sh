#!/bin/bash

################################################################################
# Скрипт для сборки документации проекта AI-Breadboard
#
# Функциональность:
# 1. Установка зависимостей из docs/ru/requirements-docs.txt
# 2. Генерация API-документации через generate_api.py
# 3. Валидация структуры документации через validate_structure.py
# 4. Проверка ссылок через check_links.py
# 5. Сборка документации с помощью Sphinx (-W, -j auto)
# 6. Вывод пути к собранной документации
#
# Требования: 8.1, 8.2
# Язык: Bash с русскими комментариями
################################################################################

set -e  # Завершить скрипт при ошибке

# ============================================================================
# ЦВЕТНОЙ ВЫВОД
# ============================================================================

# Цвета для терминала
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода с цветом
print_section() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================================
# ПРОВЕРКА ЗАВИСИМОСТЕЙ
# ============================================================================

print_section "ЭТАП 1: Проверка зависимостей"

# Проверяем наличие необходимых команд
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "Команда '$1' не найдена"
        return 1
    else
        print_success "Команда '$1' найдена"
        return 0
    fi
}

# Проверяем необходимые инструменты
DEPS_OK=true
check_command "python3" || DEPS_OK=false
check_command "pip3" || DEPS_OK=false

if [ "$DEPS_OK" = false ]; then
    print_error "Требуется установить Python 3 и pip"
    exit 1
fi

# Получаем версию Python
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_info "Найдена версия Python: $PYTHON_VERSION"

# ============================================================================
# ОПРЕДЕЛЕНИЕ ПУТЕЙ
# ============================================================================

# Получаем директорию скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_RU_DIR="$PROJECT_ROOT/docs/ru"
DOCS_BUILD_DIR="$PROJECT_ROOT/docs/_build"
SCRIPTS_DOCS_DIR="$SCRIPT_DIR/docs"

print_info "Корневая директория проекта: $PROJECT_ROOT"
print_info "Директория документации: $DOCS_RU_DIR"
print_info "Директория скриптов: $SCRIPTS_DOCS_DIR"

# Проверяем существование необходимых директорий
if [ ! -d "$DOCS_RU_DIR" ]; then
    print_error "Директория документации не найдена: $DOCS_RU_DIR"
    exit 1
fi

if [ ! -d "$SCRIPTS_DOCS_DIR" ]; then
    print_error "Директория скриптов документации не найдена: $SCRIPTS_DOCS_DIR"
    exit 1
fi

print_success "Все необходимые директории найдены"

# ============================================================================
# УСТАНОВКА ЗАВИСИМОСТЕЙ PIP
# ============================================================================

print_section "ЭТАП 2: Установка зависимостей из requirements"

# Определяем файлы требований
REQUIREMENTS_FILES=(
    "$DOCS_RU_DIR/requirements-docs.txt"
    "$PROJECT_ROOT/req/requirements-docs.txt"
    "$PROJECT_ROOT/requirements-docs.txt"
)

REQUIREMENTS_FOUND=false

for REQ_FILE in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "$REQ_FILE" ]; then
        print_info "Найден файл требований: $REQ_FILE"
        
        # Проверяем, что файл не пуст
        if [ -s "$REQ_FILE" ]; then
            print_info "Установка зависимостей из $REQ_FILE..."
            
            # Проверяем, включает ли файл другой файл через -r
            if grep -q "^-r" "$REQ_FILE"; then
                print_info "Файл включает зависимости из других файлов"
            fi
            
            if pip3 install -q -r "$REQ_FILE"; then
                print_success "Зависимости установлены из $REQ_FILE"
                REQUIREMENTS_FOUND=true
                break
            else
                print_warning "Ошибка при установке из $REQ_FILE, пробуем следующий..."
            fi
        else
            print_warning "Файл требований пуст: $REQ_FILE"
        fi
    fi
done

if [ "$REQUIREMENTS_FOUND" = false ]; then
    print_warning "Файлы требований не найдены или пусты, продолжаем с установленными пакетами"
    print_info "Убедитесь, что установлены: sphinx, sphinx-rtd-theme, myst-parser"
fi

# Проверяем установку Sphinx
if ! python3 -c "import sphinx" 2>/dev/null; then
    print_warning "Sphinx не установлен, пытаемся установить минимальные зависимости"
    pip3 install -q sphinx sphinx-rtd-theme myst-parser
fi

print_success "Зависимости готовы к использованию"

# ============================================================================
# ГЕНЕРАЦИЯ API-ДОКУМЕНТАЦИИ
# ============================================================================

print_section "ЭТАП 3: Генерация API-документации"

GENERATE_API_SCRIPT="$SCRIPTS_DOCS_DIR/generate_api.py"

if [ -f "$GENERATE_API_SCRIPT" ]; then
    print_info "Запуск generate_api.py..."
    
    if python3 "$GENERATE_API_SCRIPT"; then
        print_success "API-документация успешно сгенерирована"
    else
        print_error "Ошибка при генерации API-документации"
        print_info "Продолжаем, несмотря на ошибку..."
    fi
else
    print_warning "Скрипт generate_api.py не найден: $GENERATE_API_SCRIPT"
fi

# ============================================================================
# ВАЛИДАЦИЯ СТРУКТУРЫ ДОКУМЕНТАЦИИ
# ============================================================================

print_section "ЭТАП 4: Валидация структуры документации"

VALIDATE_SCRIPT="$SCRIPTS_DOCS_DIR/validate_structure.py"

if [ -f "$VALIDATE_SCRIPT" ]; then
    print_info "Запуск validate_structure.py..."
    
    if python3 "$VALIDATE_SCRIPT" "$DOCS_RU_DIR"; then
        print_success "Структура документации валидна"
    else
        print_error "Ошибка валидации структуры документации"
        print_info "Продолжаем, несмотря на ошибку..."
    fi
else
    print_warning "Скрипт validate_structure.py не найден: $VALIDATE_SCRIPT"
fi

# ============================================================================
# ПРОВЕРКА ССЫЛОК
# ============================================================================

print_section "ЭТАП 5: Проверка ссылок в документации"

LINKS_CHECK_SCRIPT="$SCRIPTS_DOCS_DIR/check_links.py"

if [ -f "$LINKS_CHECK_SCRIPT" ]; then
    print_info "Запуск check_links.py..."
    
    if python3 "$LINKS_CHECK_SCRIPT" "$DOCS_RU_DIR"; then
        print_success "Проверка ссылок завершена успешно"
    else
        print_warning "Найдены проблемы со ссылками"
        print_info "Продолжаем сборку документации..."
    fi
else
    print_warning "Скрипт check_links.py не найден: $LINKS_CHECK_SCRIPT"
fi

# ============================================================================
# СБОРКА SPHINX
# ============================================================================

print_section "ЭТАП 6: Сборка документации с помощью Sphinx"

# Определяем конфиг файл Sphinx
SPHINX_CONF="$DOCS_RU_DIR/conf.py"

if [ ! -f "$SPHINX_CONF" ]; then
    print_error "Файл конфигурации Sphinx не найден: $SPHINX_CONF"
    exit 1
fi

print_info "Используется конфигурация Sphinx: $SPHINX_CONF"

# Создаём директорию для сборки если её нет
if [ ! -d "$DOCS_BUILD_DIR" ]; then
    print_info "Создаём директорию сборки: $DOCS_BUILD_DIR"
    mkdir -p "$DOCS_BUILD_DIR"
fi

# Очищаем предыдущую сборку
print_info "Очистка предыдущей сборки..."
rm -rf "$DOCS_BUILD_DIR/html"

# Запускаем Sphinx с опциями:
# -W: warnings as errors (ошибки при предупреждениях)
# -j auto: параллельная обработка (автоматическое количество потоков)
# -a: перестраиваем всё (all)
# -E: не используем кэш

print_info "Запуск Sphinx с параметрами: -W -j auto -a -E..."
print_info "Исходная директория: $DOCS_RU_DIR"
print_info "Выходная директория: $DOCS_BUILD_DIR/html"

if sphinx-build -W -j auto -a -E -b html "$DOCS_RU_DIR" "$DOCS_BUILD_DIR/html"; then
    print_success "Документация успешно собрана"
else
    BUILD_EXIT_CODE=$?
    print_error "Ошибка при сборке документации (код выхода: $BUILD_EXIT_CODE)"
    exit $BUILD_EXIT_CODE
fi

# ============================================================================
# ВЫВОД РЕЗУЛЬТАТА
# ============================================================================

print_section "РЕЗУЛЬТАТ СБОРКИ"

OUTPUT_DIR="$DOCS_BUILD_DIR/html"

if [ -d "$OUTPUT_DIR" ]; then
    print_success "Документация собрана успешно!"
    echo ""
    echo -e "${GREEN}Путь к собранной документации:${NC}"
    echo -e "${YELLOW}$OUTPUT_DIR${NC}"
    echo ""
    
    # Выводим статистику
    HTML_FILES=$(find "$OUTPUT_DIR" -name "*.html" -type f | wc -l)
    JS_FILES=$(find "$OUTPUT_DIR" -name "*.js" -type f | wc -l)
    CSS_FILES=$(find "$OUTPUT_DIR" -name "*.css" -type f | wc -l)
    
    print_info "Файлы собраны:"
    echo "  - HTML файлов: $HTML_FILES"
    echo "  - JavaScript файлов: $JS_FILES"
    echo "  - CSS файлов: $CSS_FILES"
    
    echo ""
    print_info "Для просмотра документации откройте в браузере:"
    echo "  $OUTPUT_DIR/index.html"
    
else
    print_error "Директория с собранной документацией не найдена"
    exit 1
fi

print_section "Сборка завершена успешно!"

exit 0
