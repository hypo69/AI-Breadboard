# GEMINI.md

## 📋 Master Overview

Этот файл является **главным индексом инструкций** для проекта. Он связывает все проектные документы, архитектурные принципы и инженерные стандарты.

> [!IMPORTANT]
> **Языковой стандарт**: Вся документация, docstrings, комментарии к коду, сообщения коммитов и описания тестов **ДОЛЖНЫ** быть написаны строго на **русском языке**. (Имена переменных, функций и классов в коде остаются на английском языке в соответствии с PEP 8).

---


- **Developer Guide:** [`docs/en/developer/index.md`](docs/en/developer/index.md)
- **Installation Guide:** [`.ai/instructions/knowledge/INSTALLATION_GUIDE.md`](.ai/instructions/knowledge/INSTALLATION_GUIDE.md)
- **Launcher Guide:** [`.ai/instructions/knowledge/LAUNCHER_GUIDE.md`](.ai/instructions/knowledge/LAUNCHER_GUIDE.md)
- **Menu Systems Guide:** [`.ai/instructions/knowledge/MENU_CREATION_AND_USAGE_GUIDE.md`](.ai/instructions/knowledge/MENU_CREATION_AND_USAGE_GUIDE.md) | [`docs/en/menus_guide.md`](docs/en/menus_guide.md)
- **CLI Tools Reference:** [`.ai/instructions/knowledge/scripts_tools.md`](.ai/instructions/knowledge/scripts_tools.md)
- **RAG Document Cleaner**: [`.ai/instructions/knowledge/rag_cleaner.md`](.ai/instructions/knowledge/rag_cleaner.md)
- **Universal Diagnostics Framework**: [`src/ai/diagnostics/README.md`](src/ai/diagnostics/README.md)
- **TDD & Doc Standards**: [`.ai/instructions/knowledge/tdd_standards.md`](.ai/instructions/knowledge/tdd_standards.md)
- **Agent Skills:** `.skills/` (Directly contained in `.skills` directory)

---

## 💡 Концепция проекта (AI Breadboard)

**Назначение:** Интерактивный «макет» (breadboard) для тестирования, бенчмаркинга и бесшовной маршрутизации между различными провайдерами и средами выполнения ИИ (Windows AI APIs, Microsoft Foundry Local, Windows ML / ONNX Runtime, Ollama, Google Gemini, OpenAI-совместимые API и HuggingFace).

**Ключевые архитектурные принципы:**
- **Capability-Driven Routing:** Рабочие нагрузки распределяются на основе требований к возможностям (`chat`, `vision`, `ocr`, `embedding`, `code`) и ограничений политик (`local_only`, `privacy_strict`, `performance_first`, `cloud_fallback`).
- **Dynamic Discovery & Hardware Awareness:** Автоматическое обнаружение CPU, GPU (CUDA, DirectML), NPU (QNN, DirectML), компонентов Windows AI и портов локальных демонов без сбоев на неподдерживаемом оборудовании.
- **Provider Modularization:** Каждый провайдер находится в собственном пакете в `src/ai/providers/` с выделенной логикой и `README.md` на русском языке.
- **Zero-Hardcode Configuration:** Поведение моделей и правила маршрутизации объявляются в файлах JSON-конфигурации и политик.
- **Hub & Spoke Peripheral Ecosystem:** Ядро (`src/`) защищено от прямых побочных эффектов, а внешние взаимодействия (веб, ОС, мессенджеры, облако) делегируются через 4 внешних слоя: Плагины (`plugins/`), Микро-приложения (`apps/`), MCP-серверы (`.mcp/`) и Навыки агентов (`skills/`).
- **Direct Host Execution:** Всё выполняется нативно на хосте Windows с полной наблюдаемостью.

---

## 📚 Стандарты разработки

Вся разработка **ДОЛЖНА** следовать инструкциям в `.ai/instructions/`:

### 1. **Инженерные стандарты**
📄 [`.ai/instructions/rules/CODE_RULES.md`](.ai/instructions/rules/CODE_RULES.md)

Ключевые требования:
- Архитектурные принципы: Явное внедрение зависимостей (DI), Fail-Fast, DRY, Single Responsibility
- Стандарты языка: Python 3.12+ (код на Python по PEP 8, docstrings и комментарии строго на русском языке)
- Запрет недокументированных возвратов `None`
- Стандартизированное логирование через `src.logger.logger`
- Строгое разделение конфигурации (`config.json`) и секретов (`.env`)


### 2. **Повторное использование кода и аудит существующего кода**
📄 [`.ai/instructions/rules/REUSE_RULES.md`](.ai/instructions/rules/REUSE_RULES.md)

Ключевые требования:
- **Обязательный предварительный аудит:** Перед разработкой новых функций, компонентов UI или утилит выполните поиск по кодовой базе (`grep_search`, `find_by_name`) для поиска готовых реализаций.
- **Единообразие кода:** Повторно используйте или расширяйте существующие реализации (выпадающие списки, модальные окна, паттерны API); не создавайте дублирующие реализации.

### 3. **Документирование и TDD**
📄 [`.ai/instructions/rules/DOCS_RULES.md`](.ai/instructions/rules/DOCS_RULES.md)

Ключевые требования:
- Обязательный рабочий процесс TDD для всех изменений Python
- Стандартизированная структура docstring (`hypo69 docblock` на русском языке)
- `README.md` на русском языке в каждой директории и пакете провайдеров

### 4. **Архитектурная документация**
📄 [`.ai/instructions/knowledge/project_overview.md`](.ai/instructions/knowledge/project_overview.md)

- Полная архитектура системы и диаграммы диспетчеризации возможностей
- Уровни выполнения: Windows AI, Foundry Local, ONNX/DirectML, Ollama, Gemini

---

## 🛠️ Основные команды

### Запуск сервисов
```powershell
# Единый запуск (всё)
.\run.ps1

# Запуск только сервера FastAPI
.\launchers\Run-Unicorn.ps1

# Проверка статуса
assist status
```

### Запуск скриптов через `manage_tools.py`
```powershell
# Универсальный CLI
py manage_tools.py <group> <command> [arguments]

# Примеры
py manage_tools.py skills list
py manage_tools.py rag build
py manage_tools.py db check-integrity
py manage_tools.py docs generate
```

### Тестирование
```powershell
.\launchers\run_tests.ps1         # Полный запуск тестов
pytest tests/ --cov                # Pytest с отчётом о покрытии
```

---

## ⚙️ Основные архитектурные принципы

| Принцип | Описание | Ссылка |
|---|---|---|
| **Explicit DI** | Передавайте зависимости явно; избегайте скрытых глобальных переменных | CODE_RULES.md § 3.3 |
| **Fail-Fast** | Ранний возврат при невалидных входных данных или нарушении предусловий | CODE_RULES.md § 3.4 |
| **Config > Hardcode** | Системные параметры загружаются из конфигурации | CODE_RULES.md § 3.5 |
| **No None Ambiguity** | Явные типы и надёжная обработка fallback | CODE_RULES.md § 3.6 |
| **DRY & Reuse** | Сначала ищите готовый код; переиспользуйте/расширяйте существующие компоненты | REUSE_RULES.md § 1-3 |
| **Русский язык** | Docstrings, комментарии, документация и логи на русском языке | CODE_RULES.md § 5.3 |
| **500-Line Limit** | Максимум 500 строк функционального кода (до +15% при необходимости) | CODE_RULES.md § 4.4 |
| **App Lifecycle** | Стандартный протокол интеграции приложений из `/apps` в общий сервер и меню | CODE_RULES.md § 4.5 |
| **Документация** | Docstrings + README.md на русском языке в каждой директории | DOCS_RULES.md § 3-4 |

---

## 🔐 Конфигурация и секреты

### Конфигурация (`config.json`)
Публичные системные настройки:
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 1
  },
  "logging": {
    "enable_log_analyzer": false,
    "max_size_mb": 10.0
  },
  "pprint": {
    "json_indent": 6
  },
  "ai": {
    "use_foundry": true,
    "foundry_base_url": "http://localhost:54837",
    "use_ollama": true,
    "ollama_base_url": "http://localhost:11434",
    "use_windows_ai": false
  }
}
```

### Секреты (`.env`)
Приватные учётные данные, токены и ключи:
```env
GEMINI_API_KEY_1=AIzaSy...
JWT_SECRET=secret_value
TELEGRAM_BOT_TOKEN=...
```

Правило: **Никогда не коммитьте `.env`!** Используйте `.env.example` как шаблон.

---

## ✅ Чек-лист перед коммитом

Перед каждым коммитом проверьте:

- [ ] Выполнен поиск готовых решений в кодовой базе (REUSE_RULES.md)
- [ ] Заголовок файла соответствует стандарту (CODE_RULES.md § 6)
- [ ] Все docstrings, комментарии, логи и документация написаны на **русском языке**
- [ ] Все публичные функции и классы содержат docstrings в формате `hypo69 docblock`
- [ ] Логирование выполняется через `src.logger.logger` (без прямых вызовов `print`)
- [ ] Все секреты и ключи вынесены в `.env`
- [ ] Новые приложения в `/apps` зарегистрированы в общем сервере (`src/app/__init__.py`) и меню администратора (`index.html`, `main.js`) (CODE_RULES.md § 4.5)
- [ ] Коммит представляет собой **логически завершённое, протестированное состояние** рабочего кода
- [ ] Тесты проходят: `pytest tests/ --cov`
- [ ] Новые директории содержат `README.md` на русском языке

---

**Status:** ✅ Active (Русский стандарт)  
**Version:** 3.1  
**Author:** hypo69