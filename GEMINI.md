# GEMINI.md

## 📋 Основная Info

Этот файл — **главный индекс инструкций** проекта. Содержит ссылки на все документы проекта, архитектурные принципы и стандарты разработки.

---

## 🚀 Быстрый старт

### Первый запуск
```powershell
.\install.ps1          # Установка проекта и venv
.\run.ps1              # Запуск сервера (FastAPI + Foundry)
```

### Документация и инструменты
- **Полная установка:** [`.ai/instructions/knowledge/INSTALLATION_GUIDE.md`](.ai/instructions/knowledge/INSTALLATION_GUIDE.md)
- **Запуск сервисов:** [`.ai/instructions/knowledge/LAUNCHER_GUIDE.md`](.ai/instructions/knowledge/LAUNCHER_GUIDE.md)
- **Консольные инструменты:** [`.ai/instructions/knowledge/scripts_tools.md`](.ai/instructions/knowledge/scripts_tools.md)

---

## 💡 Концепция проекта (AI Breadboard)

**Назначение:** Интерактивная "макетная плата" для изучения и тестирования различных AI моделей (Google Gemini, Microsoft AI Foundry, Ollama, OpenAI и др.).

**Ключевые особенности:**
- **Moduleная архитектура:** Модели работают через единый интерфейс `UnifiedChatModel` без дублирования бизнес-логики
- **Прямой запуск:** Всё работает на хосте (PowerShell лончеры + Python venv), полная наблюдаемость
- **Configuration вместо кодирования:** Поведение моделей управляется через файлы конфигурации и инструкции, а не через hardcode
- **Минимализм:** KISS-принцип без излишних слоёв абстракции

---

## 📚 Стандарты разработки

Все разработки **MUST** следовать инструкциям в `.ai/instructions/`:

### 1. **Стандарты кода**
📄 [`.ai/instructions/rules/CODE_RULES.md`](.ai/instructions/rules/CODE_RULES.md)

Содержит:
- Архитектурные принципы (Explicit, DRY, Single Responsibility)
- Запрет на использование `None`
- Правила комментирования и логирования
- Языковые стандарты (Python 3.12+, PHP 8.3+, JS ES2024)
- Работа с конфигурацией и секретами

### 2. **Документирование и TDD**
📄 [`.ai/instructions/rules/DOCS_RULES.md`](.ai/instructions/rules/DOCS_RULES.md)

Содержит:
- Обязательный TDD-workflow для всех `.py` изменений
- Структура docstrings в формате `hypo69 docblock`
- Правила документирования README.md для каждой директории
- Examples и best practices

### 3. **Архитектурная документация**
📄 [`.ai/instructions/knowledge/project_overview.md`](.ai/instructions/knowledge/project_overview.md)

- Общее описание системы
- Ключевые компоненты и их назначение
- Архитектурные диаграммы
- Процессы и workflows

---

## 🛠️ Основные инструменты и команды

### Запуск сервиса
```powershell
# Главный лончер (всё сразу)
.\run.ps1

# Только FastAPI сервер
.\launchers\Run-Unicorn.ps1

# Check статуса
assist status
```

### Управление через `manage_tools.py`
```powershell
# Универсальный CLI для скриптов
py manage_tools.py <группа> <команда> [аргументы]

# Examples
py manage_tools.py media scan --disk "диск 2"
py manage_tools.py torrents assign
py manage_tools.py check db
```

Полная справка: [`.ai/instructions/knowledge/scripts_tools.md`](.ai/instructions/knowledge/scripts_tools.md)

### Запуск тестов
```powershell
.\launchers\run_tests.ps1         # Полное тестирование
pytest tests/ --cov                # С подсчётом покрытия
```

---

## ⚙️ Архитектурные принципы

| Принцип | Описание | Ссылка |
|---------|----------|--------|
| **Explicit** | Передача зависимостей явно (DI) | CODE_RULES.md § 3.3 |
| **Fail-Fast** | Ранний возврат при ошибке | CODE_RULES.md § 3.4 |
| **Config > Hardcode** | Parameters из конфига, не из кода | CODE_RULES.md § 3.5 |
| **No None** | Запрет на использование `None` | CODE_RULES.md § 3.6 |
| **DRY** | Нет дублирования кода | CODE_RULES.md § 4.2 |
| **300-строк лимит** | Функции max 300 строк кода | CODE_RULES.md § 4.4 |
| **Документация** | Docstrings + README.md для каждого модуля | DOCS_RULES.md § 3-4 |

---

## 🔐 Configuration и секреты

### Configuration (`config.json`)
Все Parameters работы приложения хранятся в публичном файле:
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 3000,
    "workers": 1
  },
  "ai": {
    "use_foundry": true,
    "foundry_base_url": "http://localhost:54837"
  }
}
```

### Секреты (`.env`)
Только приватные данные (API ключи, токены, пароли):
```env
GEMINI_API_KEY_1=AIzaSy...
JWT_SECRET=secret_value
TELEGRAM_BOT_TOKEN=...
```

Правило: **Никогда не коммитить `.env`!** Используйте `.env.example` для примеров.

📄 Подробнее: CODE_RULES.md § 7 "Configuration и секреты"

---

## 📖 Полный указатель документации

| Документ | Где | Описание |
|----------|-----|---------|
| **CODE_RULES.md** | `.ai/instructions/rules/` | Стандарты кода, архитектура, языки |
| **DOCS_RULES.md** | `.ai/instructions/rules/` | TDD, docstrings, README.md |
| **INSTALLATION_GUIDE.md** | `.ai/instructions/knowledge/` | Установка и настройка проекта |
| **LAUNCHER_GUIDE.md** | `.ai/instructions/knowledge/` | Запуск сервисов и лончеры |
| **scripts_tools.md** | `.ai/instructions/knowledge/` | Справочник консольных инструментов |
| **project_overview.md** | `.ai/instructions/knowledge/` | Архитектура и компоненты |
| **legacy_project_knowledge.md** | `.ai/instructions/knowledge/` | Историческая справка (2026) |
| **api_documentation.md** | `.ai/instructions/knowledge/` | API эндпоинты |
| **chat.md** | `.ai/instructions/knowledge/` | Реализация чат-логики |
| **README.md** | `.ai/instructions/` | Справочник по инструкциям |

---

## ✅ Чек-лист перед коммитом

Перед каждым коммитом убедитесь:

- [ ] Заголовок файла соответствует стандарту (см. CODE_RULES.md § 6)
- [ ] Все публичные функции имеют docstring формата `hypo69 docblock` (DOCS_RULES.md § 3)
- [ ] В Python/PHP коде нет кириллицы (только в комментариях Python/PowerShell)
- [ ] Логирование через `core.logger.logger`, а не `print()`
- [ ] Все секреты перемещены в `.env`
- [ ] Коммит отражает **логически завершённое state** рабочего кода
- [ ] Тесты пройдены: `pytest tests/ --cov`
- [ ] Новые директории содержат `README.md`

---

## 🔗 Дополнительные ресурсы

- **Главный README:** [`README.ru.md`](README.ru.md)
- **Индекс документации:** [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md)
- **Инструменты проекта:** [`tools/README.md`](tools/README.md)

---

**Status:** ✅ Актуальна на август 2026  
**Версия:** 2.0 (переработана с удалением дублирования)  
**Автор:** hypo69