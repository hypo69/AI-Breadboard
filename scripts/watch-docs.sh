#!/bin/bash

# Скрипт для автоматической пересборки документации
# Использует fswatch или find + sleep для отслеживания изменений в docs/ru/
#
# Требования: 8.2, 8.3
#
# Использование:
#   ./scripts/watch-docs.sh              # Пересборка при изменении файлов
#   ./scripts/watch-docs.sh --serve      # Пересборка + live-server на порту 8000
#
# Зависимости:
#   - bash >= 4.0
#   - find (встроено в bash)
#   - fswatch (опционально, используется если установлен)
#   - Python 3.9+ (для http.server, если используется --serve)

set -e

# ═══════════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

# Абсолютный путь к проекту
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Директории
DOCS_DIR="${PROJECT_ROOT}/docs/ru"
BUILD_SCRIPT="${PROJECT_ROOT}/scripts/build-docs.sh"
SERVE_SCRIPT="${PROJECT_ROOT}/scripts/serve-docs.sh"

# Временные переменные
SERVE_MODE=false
SERVE_PID=""
WATCH_METHOD="auto"  # auto, fswatch, find
CHECK_INTERVAL=2     # Интервал проверки изменений для find метода

# Цвета для вывода
COLOR_RESET='\033[0m'
COLOR_BOLD='\033[1m'
COLOR_GREEN='\033[32m'
COLOR_BLUE='\033[36m'
COLOR_YELLOW='\033[33m'
COLOR_RED='\033[31m'

# ═══════════════════════════════════════════════════════════════════════════════
# ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

# Функция для красивого вывода сообщений
print_header() {
    echo -e "\n${COLOR_BOLD}${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_BLUE}  $1${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}\n"
}

print_success() {
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} $1"
}

print_info() {
    echo -e "${COLOR_BLUE}ℹ${COLOR_RESET} $1"
}

print_warning() {
    echo -e "${COLOR_YELLOW}⚠${COLOR_RESET} $1"
}

print_error() {
    echo -e "${COLOR_RED}✗${COLOR_RESET} $1"
}

# Функция для вывода справки
show_help() {
    cat << 'EOF'
Автоматическая пересборка документации

Использование:
  ./scripts/watch-docs.sh [опции]

Опции:
  --serve              Запустить live-server параллельно (порт 8000)
  --method METHOD      Метод отслеживания: auto, fswatch, find (по умолчанию: auto)
  --interval СECS      Интервал проверки для find метода в секундах (по умолчанию: 2)
  --help               Показать эту справку

Примеры:
  # Просто пересборка при изменении файлов
  ./scripts/watch-docs.sh

  # Пересборка + live-server
  ./scripts/watch-docs.sh --serve

  # Использовать явно find метод
  ./scripts/watch-docs.sh --method find --interval 3

  # Использовать fswatch (более быстро)
  ./scripts/watch-docs.sh --method fswatch --serve

EOF
}

# Проверка наличия скриптов сборки
check_dependencies() {
    print_info "Проверка зависимостей..."

    if [[ ! -f "${BUILD_SCRIPT}" ]]; then
        print_error "Скрипт сборки не найден: ${BUILD_SCRIPT}"
        return 1
    fi
    print_success "Скрипт сборки найден"

    if [[ ! -d "${DOCS_DIR}" ]]; then
        print_error "Директория документации не найдена: ${DOCS_DIR}"
        return 1
    fi
    print_success "Директория документации найдена"

    return 0
}

# Определение метода отслеживания изменений
detect_watch_method() {
    # Проверка наличия fswatch
    if command -v fswatch &> /dev/null; then
        WATCH_METHOD="fswatch"
        print_success "Обнаружен fswatch - будет использоваться быстрое отслеживание"
        return
    fi

    # Fallback на find метод
    WATCH_METHOD="find"
    print_info "fswatch не установлен, используется find + sleep для отслеживания"
}

# Получение хеша всех файлов в директории
get_files_hash() {
    find "${DOCS_DIR}" -type f \( -name "*.md" -o -name "*.py" -o -name "*.yml" -o -name "*.yaml" \) -printf '%T@' -quit 2>/dev/null | md5sum 2>/dev/null | awk '{print $1}' || echo "0"
}

# Функция для запуска пересборки
rebuild_docs() {
    local changed_file="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo ""
    print_header "Пересборка документации"
    print_info "Время: ${timestamp}"
    print_info "Изменён файл: ${changed_file}"

    if bash "${BUILD_SCRIPT}"; then
        print_success "Документация успешно пересобрана!"
        echo ""
        print_info "Обновление доступно по адресу: http://localhost:8000"
        echo ""
    else
        print_error "Ошибка при пересборке документации!"
        echo ""
    fi
}

# Функция для запуска live-server
start_live_server() {
    print_info "Запуск live-server на порту 8000..."

    if bash "${SERVE_SCRIPT}" &
    then
        SERVE_PID=$!
        print_success "Live-server запущен (PID: ${SERVE_PID})"
        print_info "Документация доступна на: http://localhost:8000"
    else
        print_error "Ошибка при запуске live-server"
        return 1
    fi
}

# Функция для остановки live-server
stop_live_server() {
    if [[ -n "${SERVE_PID}" ]] && kill -0 "${SERVE_PID}" 2>/dev/null; then
        print_info "Остановка live-server (PID: ${SERVE_PID})..."
        kill "${SERVE_PID}" 2>/dev/null || true
        wait "${SERVE_PID}" 2>/dev/null || true
        print_success "Live-server остановлен"
    fi
}

# Watch метод с fswatch
watch_with_fswatch() {
    print_header "Отслеживание изменений файлов"
    print_info "Используется: fswatch"
    print_info "Отслеживаемая директория: ${DOCS_DIR}"
    print_info "Нажмите Ctrl+C для выхода"
    echo ""

    # fswatch следит за изменениями в директории
    fswatch -r "${DOCS_DIR}" 2>/dev/null | while read -r changed_file; do
        # Пропускаем файлы в _build директории
        if [[ "${changed_file}" == *"_build"* ]] || [[ "${changed_file}" == *"__pycache__"* ]]; then
            continue
        fi

        rebuild_docs "${changed_file}"
    done
}

# Watch метод с find + sleep
watch_with_find() {
    print_header "Отслеживание изменений файлов"
    print_info "Используется: find + sleep (интервал: ${CHECK_INTERVAL}с)"
    print_info "Отслеживаемая директория: ${DOCS_DIR}"
    print_info "Нажмите Ctrl+C для выхода"
    echo ""

    local prev_hash=""
    local new_hash=""

    while true; do
        # Получаем текущий хеш времени изменения файлов
        new_hash=$(get_files_hash)

        # Сравниваем с предыдущим хешем
        if [[ "${new_hash}" != "${prev_hash}" ]] && [[ -n "${prev_hash}" ]]; then
            # Файлы изменились
            changed_file=$(find "${DOCS_DIR}" -type f \( -name "*.md" -o -name "*.py" -o -name "*.yml" -o -name "*.yaml" \) -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | awk '{print $2}' || echo "unknown")
            rebuild_docs "${changed_file}"
        fi

        prev_hash="${new_hash}"

        # Небольшая задержка перед следующей проверкой
        sleep "${CHECK_INTERVAL}"
    done
}

# Главная функция watch
start_watching() {
    # Определяем метод если это "auto"
    if [[ "${WATCH_METHOD}" == "auto" ]]; then
        detect_watch_method
    fi

    # Выполняем начальную сборку
    print_header "Начальная сборка документации"
    if ! bash "${BUILD_SCRIPT}"; then
        print_error "Ошибка при начальной сборке!"
        return 1
    fi
    print_success "Начальная сборка завершена"

    # Запускаем live-server если нужно
    if [[ "${SERVE_MODE}" == true ]]; then
        echo ""
        start_live_server || return 1
    fi

    # Запускаем наблюдение
    echo ""
    if [[ "${WATCH_METHOD}" == "fswatch" ]]; then
        watch_with_fswatch
    else
        watch_with_find
    fi
}

# Обработчик сигнала для чистого завершения
cleanup() {
    echo ""
    print_info "Получен сигнал завершения..."
    stop_live_server
    print_info "Завершение работы скрипта"
    exit 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# ОСНОВНОЙ КОД
# ═══════════════════════════════════════════════════════════════════════════════

# Обработка аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --serve)
            SERVE_MODE=true
            shift
            ;;
        --method)
            WATCH_METHOD="$2"
            shift 2
            ;;
        --interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
done

# Регистрация обработчика для Ctrl+C
trap cleanup SIGINT SIGTERM

# Основной поток
print_header "Автоматическая пересборка документации AI-Breadboard"
print_info "Проект: ${PROJECT_ROOT}"
print_info "Документация: ${DOCS_DIR}"

if [[ "${SERVE_MODE}" == true ]]; then
    print_info "Режим: Пересборка + Live-server"
else
    print_info "Режим: Только пересборка"
fi

echo ""

# Проверка зависимостей
if ! check_dependencies; then
    print_error "Ошибка при проверке зависимостей"
    exit 1
fi

echo ""

# Запуск наблюдения
if ! start_watching; then
    print_error "Ошибка при запуске наблюдения"
    exit 1
fi
