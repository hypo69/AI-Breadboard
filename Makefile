################################################################################
# AI-Breadboard Документация - Makefile
# 
# Удобные команды для локальной разработки документации на русском языке
# Требования: 8.1, 8.2, 8.3
#
# Использование:
#   make docs-help          - Справка по всем командам
#   make docs-build         - Полная сборка документации
#   make docs-serve         - Запуск локального сервера (порт 8000)
#   make docs-clean         - Очистка артефактов сборки
#   make docs-watch         - Наблюдение с автоматической пересборкой
#   make docs-validate      - Только валидация
#   make docs-api           - Только генерация API
#   make docs-all           - Build + serve (параллельно)
################################################################################

# Переменные для путей и команд
.PHONY: docs-help docs-build docs-serve docs-clean docs-watch docs-validate docs-api docs-all

# Директории и пути
DOCS_DIR := docs/ru
SCRIPTS_DIR := scripts/docs
BUILD_DIR := $(DOCS_DIR)/_build
DOCTREES_DIR := $(BUILD_DIR)/doctrees
HTML_DIR := $(BUILD_DIR)/html
PYTHON := python
SPHINX_BUILD := sphinx-build
HTTP_SERVER_PORT := 8000

# Цвета для вывода в консоль
COLOR_RESET := \033[0m
COLOR_BLUE := \033[36m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_RED := \033[31m

# ============================================================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================================================

.PHONY: docs-help
docs-help: ## Справка - Показать все доступные команды
	@echo "$(COLOR_BLUE)╔════════════════════════════════════════════════════════════════╗$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)║   AI-Breadboard: Команды для разработки документации            ║$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)╚════════════════════════════════════════════════════════════════╝$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)📚 ОСНОВНЫЕ КОМАНДЫ:$(COLOR_RESET)"
	@echo "  $(COLOR_YELLOW)make docs-build$(COLOR_RESET)         Полная сборка (генерация → валидация → Sphinx)"
	@echo "  $(COLOR_YELLOW)make docs-serve$(COLOR_RESET)         Запуск локального сервера на порту $(HTTP_SERVER_PORT)"
	@echo "  $(COLOR_YELLOW)make docs-clean$(COLOR_RESET)         Очистка артефактов сборки (_build, .doctrees)"
	@echo ""
	@echo "$(COLOR_GREEN)🔄 РАЗРАБОТКА:$(COLOR_RESET)"
	@echo "  $(COLOR_YELLOW)make docs-watch$(COLOR_RESET)         Наблюдение с автоматической пересборкой"
	@echo "  $(COLOR_YELLOW)make docs-validate$(COLOR_RESET)      Только валидация документации"
	@echo "  $(COLOR_YELLOW)make docs-api$(COLOR_RESET)           Только генерация API из docstrings"
	@echo ""
	@echo "$(COLOR_GREEN)⚡ КОМБИНИРОВАННЫЕ:$(COLOR_RESET)"
	@echo "  $(COLOR_YELLOW)make docs-all$(COLOR_RESET)           Build + serve одной командой (параллельно)"
	@echo ""
	@echo "$(COLOR_BLUE)════════════════════════════════════════════════════════════════$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)💡 ПРИМЕРЫ:$(COLOR_RESET)"
	@echo "  # Полная сборка с проверками"
	@echo "  $$ make docs-build"
	@echo ""
	@echo "  # Локальный просмотр (автоматическая пересборка)"
	@echo "  $$ make docs-watch &"
	@echo "  $$ make docs-serve"
	@echo ""
	@echo "  # Только проверка валидности"
	@echo "  $$ make docs-validate"
	@echo ""
	@echo "$(COLOR_GREEN)📖 СТРУКТУРА ДОКУМЕНТАЦИИ:$(COLOR_RESET)"
	@echo "  $(DOCS_DIR)/"
	@echo "  ├── index.md              - Главная страница"
	@echo "  ├── conf.py               - Конфигурация Sphinx"
	@echo "  ├── manual/               - Руководства и примеры"
	@echo "  ├── api/                  - API-документация (автогенерированная)"
	@echo "  ├── guides/               - Подробные руководства"
	@echo "  ├── architecture/         - Документация по архитектуре"
	@echo "  └── _build/               - Собранная документация"
	@echo ""
	@echo "$(COLOR_BLUE)════════════════════════════════════════════════════════════════$(COLOR_RESET)"

# ============================================================================
# КОМАНДА: docs-build - Полная сборка
# ============================================================================

.PHONY: docs-build
docs-build: ## Полная сборка документации (генерация → валидация → Sphinx)
	@echo "$(COLOR_GREEN)▶ Начинается полная сборка документации...$(COLOR_RESET)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	
	@echo "$(COLOR_BLUE)📝 Шаг 1: Генерация API-документации$(COLOR_RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/generate_api.py
	@echo ""
	
	@echo "$(COLOR_BLUE)✓ Шаг 2: Валидация структуры документации$(COLOR_RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/validate_structure.py || true
	@echo ""
	
	@echo "$(COLOR_BLUE)🔗 Шаг 3: Проверка ссылок в документации$(COLOR_RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/check_links.py || true
	@echo ""
	
	@echo "$(COLOR_BLUE)🏗 Шаг 4: Сборка Sphinx документации$(COLOR_RESET)"
	@$(SPHINX_BUILD) -b html -W --keep-going \
		-d $(DOCTREES_DIR) \
		-j auto \
		$(DOCS_DIR) $(HTML_DIR)
	@echo ""
	
	@echo "$(COLOR_GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)✓ Сборка завершена успешно!$(COLOR_RESET)"
	@echo ""
	@echo "📂 Результат находится в: $(COLOR_YELLOW)$(HTML_DIR)$(COLOR_RESET)"
	@echo "🌐 Для просмотра выполните: $(COLOR_YELLOW)make docs-serve$(COLOR_RESET)"
	@echo ""

# ============================================================================
# КОМАНДА: docs-serve - Локальный сервер
# ============================================================================

.PHONY: docs-serve
docs-serve: ## Запуск локального сервера на порту 8000
	@if [ ! -d "$(HTML_DIR)" ]; then \
		echo "$(COLOR_RED)✗ Ошибка: документация не собрана$(COLOR_RESET)"; \
		echo "Выполните сначала: $(COLOR_YELLOW)make docs-build$(COLOR_RESET)"; \
		exit 1; \
	fi
	@echo "$(COLOR_GREEN)▶ Запуск локального HTTP-сервера...$(COLOR_RESET)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "🌐 Документация доступна по адресу:"
	@echo ""
	@echo "   $(COLOR_YELLOW)http://localhost:$(HTTP_SERVER_PORT)$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BLUE)Документ в директории:$(COLOR_RESET) $(HTML_DIR)"
	@echo ""
	@echo "$(COLOR_GREEN)Для остановки сервера нажмите: Ctrl+C$(COLOR_RESET)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@cd $(HTML_DIR) && $(PYTHON) -m http.server $(HTTP_SERVER_PORT)

# ============================================================================
# КОМАНДА: docs-clean - Очистка артефактов
# ============================================================================

.PHONY: docs-clean
docs-clean: ## Очистка артефактов сборки (_build, .doctrees)
	@echo "$(COLOR_YELLOW)🗑 Очистка артефактов сборки...$(COLOR_RESET)"
	@echo ""
	
	@if [ -d "$(BUILD_DIR)" ]; then \
		echo "  Удаление: $(BUILD_DIR)"; \
		rm -rf $(BUILD_DIR); \
		echo "  ✓ Удалено"; \
	else \
		echo "  $(COLOR_BLUE)ℹ Директория $(BUILD_DIR) не найдена$(COLOR_RESET)"; \
	fi
	
	@if [ -d "$(DOCTREES_DIR)" ]; then \
		echo "  Удаление: $(DOCTREES_DIR)"; \
		rm -rf $(DOCTREES_DIR); \
		echo "  ✓ Удалено"; \
	else \
		echo "  $(COLOR_BLUE)ℹ Директория $(DOCTREES_DIR) не найдена$(COLOR_RESET)"; \
	fi
	
	@echo ""
	@echo "$(COLOR_GREEN)✓ Очистка завершена$(COLOR_RESET)"
	@echo ""

# ============================================================================
# КОМАНДА: docs-watch - Наблюдение с автоматической пересборкой
# ============================================================================

.PHONY: docs-watch
docs-watch: ## Наблюдение с автоматической пересборкой (требует fswatch или watchman)
	@echo "$(COLOR_GREEN)▶ Запуск наблюдения за изменениями документации...$(COLOR_RESET)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "$(COLOR_BLUE)Отслеживаемые директории:$(COLOR_RESET)"
	@echo "  - $(DOCS_DIR)/"
	@echo "  - $(SCRIPTS_DIR)/"
	@echo ""
	@echo "$(COLOR_YELLOW)При изменении файлов будет автоматически запущена пересборка$(COLOR_RESET)"
	@echo ""
	
	@command -v fswatch >/dev/null 2>&1 && \
		( \
			echo "$(COLOR_GREEN)Используется fswatch$(COLOR_RESET)"; \
			echo ""; \
			fswatch -r $(DOCS_DIR) $(SCRIPTS_DIR) | while read -r file; do \
				echo "$(COLOR_BLUE)✓ Обнаружено изменение: $$file$(COLOR_RESET)"; \
				echo "$(COLOR_YELLOW)▶ Пересборка...$(COLOR_RESET)"; \
				$(MAKE) docs-build; \
				echo ""; \
			done \
		) || \
	command -v watchman >/dev/null 2>&1 && \
		( \
			echo "$(COLOR_GREEN)Используется watchman$(COLOR_RESET)"; \
			echo ""; \
			watchman watch $(DOCS_DIR); \
			watchman watch $(SCRIPTS_DIR); \
		) || \
		( \
			echo "$(COLOR_RED)✗ Ошибка: не найден инструмент для наблюдения$(COLOR_RESET)"; \
			echo ""; \
			echo "$(COLOR_BLUE)Установите один из них:$(COLOR_RESET)"; \
			echo "  macOS:  brew install fswatch"; \
			echo "  Linux:  apt-get install fswatch"; \
			echo "  Все ОС: npm install -g watchman"; \
			exit 1; \
		)
	@echo "$(COLOR_YELLOW)Наблюдение остановлено (Ctrl+C)$(COLOR_RESET)"

# ============================================================================
# КОМАНДА: docs-validate - Только валидация
# ============================================================================

.PHONY: docs-validate
docs-validate: ## Только валидация документации (без сборки)
	@echo "$(COLOR_GREEN)▶ Валидация документации...$(COLOR_RESET)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	
	@echo "$(COLOR_BLUE)✓ Проверка структуры документации$(COLOR_RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/validate_structure.py
	@echo ""
	
	@echo "$(COLOR_BLUE)🔗 Проверка ссылок в документации$(COLOR_RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/check_links.py
	@echo ""
	
	@echo "$(COLOR_GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)✓ Валидация завершена$(COLOR_RESET)"
	@echo ""

# ============================================================================
# КОМАНДА: docs-api - Только генерация API
# ============================================================================

.PHONY: docs-api
docs-api: ## Только генерация API-документации из docstrings
	@echo "$(COLOR_GREEN)▶ Генерация API-документации...$(COLOR_RESET)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	
	@$(PYTHON) $(SCRIPTS_DIR)/generate_api.py
	@echo ""
	
	@echo "$(COLOR_GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)✓ Генерация API завершена$(COLOR_RESET)"
	@echo ""
	@echo "📂 Результат находится в: $(COLOR_YELLOW)$(DOCS_DIR)/api/$(COLOR_RESET)"
	@echo ""

# ============================================================================
# КОМАНДА: docs-all - Build + serve (параллельно)
# ============================================================================

.PHONY: docs-all
docs-all: ## Build + serve - Полная сборка и запуск сервера одной командой
	@echo "$(COLOR_GREEN)▶ Начинается процесс build + serve...$(COLOR_RESET)"
	@echo ""
	$(MAKE) docs-build && $(MAKE) docs-serve

# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ СЛУЖЕБНЫЕ КОМАНДЫ (внутренние, не отображаются в help)
# ============================================================================

.PHONY: check-python
check-python: ## Проверка установки Python (служебная)
	@command -v $(PYTHON) >/dev/null 2>&1 || \
		( echo "$(COLOR_RED)✗ Ошибка: Python не установлен$(COLOR_RESET)"; exit 1 )

.PHONY: check-sphinx
check-sphinx: ## Проверка установки Sphinx (служебная)
	@command -v $(SPHINX_BUILD) >/dev/null 2>&1 || \
		( echo "$(COLOR_RED)✗ Ошибка: Sphinx не установлен$(COLOR_RESET)"; exit 1 )

# ============================================================================
# УМОЛЧАНИЕ ДЛЯ ПЕРЕМЕННОЙ PHONY
# ============================================================================

.DEFAULT_GOAL := docs-help

# Конец Makefile
