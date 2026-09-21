# GEMINI.md

## 📋 Master Overview

Этот файл является **главным индексом инструкций** для проекта. Он связывает все проектные документы, архитектурные принципы и инженерные стандарты.

> [!IMPORTANT]
> **Языковой стандарт**: Вся документация, docstrings, комментарии к коду, сообщения коммитов и описания тестов **ДОЛЖНЫ** быть написаны строго на **русском языке**. (Имена переменных, функций и классов в коде остаются на английском языке в соответствии с PEP 8).

---



- **CODE TDD & Doc Standards**: [`.ai\instructions\standards`](.ai/instructions/knowledge/tdd_standards.md)
- **Agent Skills:** `.skills/` (Directly contained in `.skills` directory)

---



## 💡 Концепция проекта (AI Breadboard)

**Назначение:** Интерактивный «макет» (breadboard) для тестирования, бенчмаркинга и бесшовной маршрутизации между различными провайдерами и средами выполнения ИИ (Windows AI APIs, Microsoft Foundry Local, Windows ML / ONNX Runtime, Ollama, Google Gemini, OpenAI-совместимые API и HuggingFace).



## 📚 Стандарты разработки

Вся разработка **ДОЛЖНА** следовать инструкциям в `.ai/instructions/`:

### 1. **Инженерные стандарты**
📄 [`.ai/instructions/standards/ENGINEERING.md`](.ai/instructions/standards/ENGINEERING.md)

Ключевые требования:
- Архитектурные принципы: Явное внедрение зависимостей (DI), Fail-Fast, DRY, Single Responsibility
- Стандарты языка: Python 3.12+ (код на Python по PEP 8, docstrings и комментарии строго на русском языке)
- Запрет недокументированных возвратов `None`
- Стандартизированное логирование через `src.logger.logger`
- Строгое разделение конфигурации (`config.json`) и секретов (`.env`)


### 2. **Повторное использование кода и аудит существующего кода**
📄 [`.ai/instructions/standards/REUSE.md`](.ai/instructions/standards/REUSE.md)

Ключевые требования:
- **Обязательный предварительный аудит:** Перед разработкой новых функций, компонентов UI или системных инструментов выполните поиск по кодовой базе (`grep_search`, `find_by_name`). Обязательно проверяйте реализованные подсистемы в `/apps` и особенно системный стек в [`/apps/windows`](apps/windows) (`SystemCollector`, `SystemSnapshot`, `apps/windows/core`, `apps/windows/hardware`).
- **Запрет изолированных инструментов-дубликатов:** Запрещено строить отдельные функции/скрипты для операций, под которые в `/apps` уже создана модульная архитектура. Все новые параметры и операции интегрируются строго в существующие классы, коллекторы и модели данных.
- **Единообразие кода:** Повторно используйте или расширяйте существующие реализации (выпадающие списки, модальные окна, паттерны API); не создавайте дублирующие реализации.

### 3. **Документирование и TDD**
📄 [`.ai/instructions/standards/DOCUMENTATION.md`](.ai/instructions/standards/DOCUMENTATION.md)

Ключевые требования:
- Обязательный рабочий процесс TDD для всех изменений Python
- Стандартизированная структура docstring (`hypo69 docblock` на русском языке)
- `README.md` на русском языке в каждой директории и пакете провайдеров

### 4. **Архитектурная документация**
📄 [`.ai/instructions/knowledge/project_overview.md`](.ai/instructions/knowledge/project_overview.md)

- Полная архитектура системы и диаграммы диспетчеризации возможностей
- Уровни выполнения: Windows AI, Foundry Local, ONNX/DirectML, Ollama, Gemini

---

## 👤 Ролевые инструкции
Для активации роли используйте команду: "Твоя роль <имя>".

- **Техник:** [`.ai/instructions/roles/TECHNICIAN.md`](.ai/instructions/roles/TECHNICIAN.md)
- **Персональный секретарь:** [`.ai/instructions/roles/SECRETARY.md`](.ai/instructions/roles/SECRETARY.md)
- **Администратор:** [`.ai/instructions/roles/ADMINISTRATOR.md`](.ai/instructions/roles/ADMINISTRATOR.md)


### Запуск сервисов
```powershell
# Единый запуск (всё)
.\run.ps1

# Сценарий Test Computer (роут /tc, приложения /apps по config_tc.json)
.\tc.ps1

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

## 📧 Почтовая инфраструктура

Все почтовые ящики (IMAP/SMTP) должны управляться централизованно через файл `src/secrets/mailboxes.json`.

**Правила:**
- **Single Source of Truth**: Все агенты и скрипты обязаны считывать конфигурацию из `src/secrets/mailboxes.json`. Жесткое кодирование параметров запрещено.
- **Алиасы**: Используйте поле `aliases` в `mailboxes.json` для выбора ящика через естественный язык.
- **Унифицированный агент**: Для работы с почтой используйте унифицированный почтовый диспетчер, который обеспечивает прозрачный доступ ко всем настроенным ящикам.

> [!WARNING]
> Никогда не коммитьте `src/secrets/mailboxes.json` в репозиторий. Используйте `src/secrets/mailboxes.json.example`.

---

## ✅ Чек-лист перед коммитом

Перед каждым коммитом проверьте:

- [ ] Выполнен поиск готовых решений в кодовой базе и аудит подсистем `/apps` (особенно `/apps/windows`) (REUSE_RULES.md)
- [ ] Заголовок файла соответствует стандарту (CODE_RULES.md § 6)
- [ ] Все docstrings, комментарии, логи и документация написаны на **русском языке**
- [ ] Все публичные функции и классы содержат docstrings в формате `hypo69 docblock`
- [ ] Логирование выполняется через `src.logger.logger` (без прямых вызовов `print`)
- [ ] Все секреты и ключи вынесены в `.env`
- [ ] Новые приложения в `/apps` зарегистрированы в общем сервере (`src/app/__init__.py`) и меню администратора (`index.html`, `main.js`) (CODE_RULES.md § 4.5)
- [ ] При изменениях фронтенда (HTML/CSS/JS/JSON) обновлена версия ассетов `?v=YYYYMMDD_vN` и обеспечен cache-busting для предотвращения показа кешированных данных
- [ ] Коммит представляет собой **логически завершённое, протестированное состояние** рабочего кода
- [ ] Тесты проходят: `pytest tests/ --cov`
- [ ] Новые директории содержат `README.md` на русском языке

---

**Status:** ✅ Active (Русский стандарт)  
**Version:** 3.1  
**Author:** hypo69