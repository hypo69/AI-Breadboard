# AI Breadboard — Документация (Русский)

Полная русскоязычная документация проекта. Все разделы собраны здесь.

## 📖 О документации

Эта папка содержит полную русскоязычную документацию проекта AI-Breadboard, которая включает руководства, архитектуру, примеры кода и справочники. Документация опубликована на [Read the Docs](https://ai-breadboard.readthedocs.io/ru/latest) и автоматически обновляется при каждом пуше в репозиторий.

### Структура документации

```
docs/
├── en/                 # English documentation
├── ru/                 # Русская документация (этот раздел)
│   ├── api/           # API справочник
│   ├── architecture/  # Архитектурные документы
│   ├── cook-book/     # Учебное пособие (8 глав)
│   ├── guides/        # Практические руководства
│   ├── plugins/       # Плагины системы и расширения
│   ├── skills/        # Навыки моделей (Skills)
│   ├── manual/        # Справочники
│   ├── index.md       # Главная страница
│   ├── ARCHITECTURE.md
│   ├── DOCUMENTATION.md
│   ├── contributing.md
│   └── README.md      # Этот файл
├── es/                 # Spanish documentation
├── ar/                 # Arabic documentation
├── he/                 # Hebrew documentation
├── assets/            # Общие ресурсы (логотипы, иконки)
└── stylesheets/       # Пользовательские стили CSS
```

### Технология и инструменты

- **MkDocs** — генератор статических сайтов документации
- **Material for MkDocs** — профессиональная тема оформления
- **Read the Docs** — хостинг и управление версиями документации
- **mkdocs-static-i18n** — поддержка многоязычности

---

## 🚀 Начало работы

| Документ | Описание |
|----------|----------|
| [Руководство по установке](manual/installation.md) | Установка и первый запуск на Windows/Linux/macOS |
| [Запуск сервисов](manual/RUN.md) | Режимы запуска бэкенда, порты и флаги |
| [Конфигурация системы](manual/config.md) | Работа с `config.json`, `.env`, путями |

---

## 🏗️ Архитектура

| Документ | Описание |
|----------|----------|
| [Архитектура системы](ARCHITECTURE.md) | Слои архитектуры, кроссплатформенность, потоки выполнения |
| [Обзор архитектуры](architecture/overview.md) | Оркестратор провайдеров, поддерживаемые модели |
| [Компоненты](architecture/components.md) | Детальное описание подсистем и модулей |
| [Итоги портирования](ported.md) | Детали кроссплатформенного портирования |

---

## 📚 Учебная книга (8 глав)

Практическое руководство по работе со стендом AI Breadboard:

| Глава | Тема |
|-------|------|
| [Глава 1](cook-book/ch01_philosophy.md) | Архитектура макетной платы и среда |
| [Глава 2](cook-book/ch02_orchestration.md) | Оркестратор моделей и отказоустойчивость |
| [Глава 3](cook-book/ch03_local_inference.md) | Локальный инференс (HF и DirectML) |
| [Глава 4](cook-book/ch04_rag_architecture.md) | Архитектура RAG и векторный поиск |
| [Глава 5](cook-book/ch05_optimization_finetuning.md) | Оптимизация, экспорт и Fine-Tuning |
| [Глава 6](cook-book/ch06_agents_and_mcp.md) | ReAct-агенты, MCP и мультимодальность |
| [Глава 7](cook-book/ch07_skills_management.md) | Создание и управление навыками |
| [Глава 8](cook-book/ch08_laboratory_practicum.md) | Практикум: 10 лабораторных работ |

---

## 🧩 Плагины системы

| Документ | Описание |
|----------|----------|
| [Обзор плагинов](plugins/index.md) | Концепция плагинов, сравнение с навыками и MCP |
| [Архитектура плагинов](plugins/architecture.md) | Класс `BasePlugin`, жизненный цикл, экшены, i18n |
| [Разработка плагинов](plugins/development.md) | Пошаговое руководство, `Plugin Factory`, тесты |
| [Каталог плагинов](plugins/catalog.md) | Описание предустановленных плагинов проекта |

---

## 🧠 Навыки моделей (Skills)

| Документ | Описание |
|----------|----------|
| [Обзор навыков](skills/index.md) | Концепция Progressive Disclosure, структура навыков |
| [Архитектура навыков](skills/architecture.md) | `SkillRegistry`, `SkillDefinition`, алгоритм поиска и приоритеты |
| [Разработка навыков](skills/development.md) | Манифест `SKILL.md`, фабрика `skill-factory`, скрипты |
| [Каталог навыков](skills/catalog.md) | Справочник всех 27 встроенных навыков |

---

## 📱 Микро-приложения (Apps)

| Документ | Описание |
|----------|----------|
| [Обзор приложений](apps/index.md) | Архитектура подсистемы `apps/`, стек и порты 8100-8105 |
| [Каталог приложений](apps/catalog.md) | Справочник всех 6 автономных микро-сервисов |

---

## 🔌 MCP Серверы (Model Context Protocol)

| Документ | Описание |
|----------|----------|
| [Обзор MCP](mcp/index.md) | Интеграция протокола Model Context Protocol в AI Breadboard |
| [Каталог MCP серверов](mcp/catalog.md) | Список серверов поиска, FastAPI, LangChain, браузера |
| [Руководство по интеграции](mcp/guide.md) | Подключение к Claude Desktop, Cursor и Antigravity |

---

## 🛠️ Справочник разработчика

| Документ | Описание |
|----------|----------|
| [Разработчику](developer/index.md) | Руководство для контрибьюторов и разработчиков |
| [Стандарты документации](DOCUMENTATION.md) | Правила оформления кода и docstrings |
| [Правила участия](contributing.md) | Процесс внесения изменений и Pull Requests |

---

## 📦 Документация модулей

| Модуль | Документ |
|--------|----------|
| `src/` | [Архитектура системы](architecture/overview.md) |
| `launchers/` | [Запуск сервисов](manual/RUN.md) |
| `plugins/` | [Каталог плагинов](plugins/catalog.md) |
| `.agents/skills/` | [Каталог навыков](skills/catalog.md) |
| `config.json` | [Справочник конфигурации](manual/config.md) |
| `secrets` | [Управление секретами](manual/configuration.md) |

---

## 📋 Технические документы

| Документ | Описание |
|----------|----------|
| [Журнал изменений](changelog.md) | История версий |
| [Портирование](ported.md) | Детали кроссплатформенного портирования |
| [Руководство по миграции базы знаний](guides/agy-knowledge-base-migration.md) | Перенос сессий и артефактов |

---

## 🔗 Связанные ресурсы

- **GitHub:** https://github.com/hypo69/AI-Breadboard
- **Issues:** https://github.com/hypo69/AI-Breadboard/issues
- **Автор:** hypo69@yandex.com

---

## 🏗️ Сборка документации локально

### Предварительные условия

- Python 3.10 или выше
- pip (менеджер пакетов Python)
- Git

### Быстрый старт

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/hypo69/AI-Breadboard.git
   cd AI-Breadboard
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r install/req/requirements-docs.txt
   ```

3. **Соберите документацию:**
   ```bash
   mkdocs build
   ```

4. **Запустите локальный сервер:**
   ```bash
   mkdocs serve
   ```

   Документация будет доступна по адресу: **http://127.0.0.1:8000**

### Часто используемые команды

| Команда | Описание |
|---------|----------|
| `mkdocs serve` | Запуск локального сервера с автоперезагрузкой |
| `mkdocs build` | Сборка статических файлов в папку `site/` |
| `mkdocs build --strict` | Сборка с проверкой на ошибки и предупреждения |
| `mkdocs build --clean` | Очистка кеша перед сборкой |
| `mkdocs build -d custom_folder` | Сборка в определённую папку |

### Отладка локально

```bash
# Сборка с подробным выводом
mkdocs build --verbose

# Проверка конфигурации MkDocs
mkdocs build --strict --verbose

# Запуск сервера на другом порту
mkdocs serve --dev-addr 127.0.0.1:9000
```

---

## 📤 Публикация на Read the Docs

### Автоматическая публикация

Документация автоматически обновляется на [Read the Docs](https://ai-breadboard.readthedocs.io) при каждом пуше в главную ветку репозитория.

**Процесс:**
1. Вы делаете коммит и пушите изменения в `main`
2. GitHub отправляет сигнал на Read the Docs через вебхук
3. Read the Docs автоматически:
   - Клонирует новую версию репозитория
   - Устанавливает зависимости из `install/req/requirements-docs.txt`
   - Запускает `mkdocs build` с конфигурацией из `.readthedocs.yml`
   - Опубликовывает результат

### Проверка статуса публикации

1. Перейдите на страницу проекта: https://readthedocs.org/projects/ai-breadboard/
2. Откройте вкладку **Builds**
3. Найдите последнюю сборку
4. Проверьте её статус (успешно ✓ или ошибка ✗)

### Ручная сборка на Read the Docs

Если нужно пересобрать документацию вручную:

1. Перейдите на страницу проекта: https://readthedocs.org/projects/ai-breadboard/
2. Откройте вкладку **Builds**
3. Нажмите кнопку **Build Version**
4. Выберите версию (например, `latest` или конкретный тег)
5. Нажмите **Build**

### Ссылки на документацию

После публикации документация доступна по адресам:

| Язык | URL |
|------|-----|
| Последняя версия (en) | https://ai-breadboard.readthedocs.io/en/latest |
| Последняя версия (ru) | https://ai-breadboard.readthedocs.io/ru/latest |
| Конкретная версия | https://ai-breadboard.readthedocs.io/ru/v1.0.0 |

### Конфигурация Read the Docs

Вся конфигурация находится в файле `.readthedocs.yml`:

```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.10"

mkdocs:
  configuration: mkdocs.yml
  fail_on_warning: true

python:
  install:
    - requirements: install/req/requirements-docs.txt
```

---

## 🤝 Внесение вклада в документацию

### Редактирование документации

1. **Создайте ветку для изменений:**
   ```bash
   git checkout -b docs/my-changes
   ```

2. **Отредактируйте нужные файлы .md**

3. **Проверьте локально:**
   ```bash
   mkdocs serve
   ```

4. **Сделайте коммит:**
   ```bash
   git add docs/
   git commit -m "docs: update Russian documentation"
   ```

5. **Создайте Pull Request на GitHub**

### Требования к документации

- Используйте синтаксис Markdown
- Добавляйте заголовки для структуры
- Используйте примеры кода с указанием языка
- Добавляйте внутренние ссылки между документами
- Проверяйте орфографию на русском языке

### Полезные ссылки для контрибьюторов

- [CONTRIBUTING.md](contributing.md) — Правила внесения вклада
- [DOCUMENTATION.md](DOCUMENTATION.md) — Стандарты документирования кода
- [Справочник разработчика](developer/index.md) — Для разработчиков

---

## ❓ Часто задаваемые вопросы

### Как добавить новый документ?

1. Создайте файл `.md` в нужной папке
2. Добавьте ссылку на файл в `mkdocs.yml` (в раздел `nav:`)
3. Проверьте локально с `mkdocs serve`
4. Сделайте коммит и пуш

### Почему документация не обновляется?

Возможные причины:
- Сборка на Read the Docs завершилась с ошибкой (проверьте логи в **Builds**)
- Вебхук не настроен
- Кеш браузера (очистите кеш или откройте в приватном режиме)

### Как использовать синтаксис Markdown Material?

Смотрите официальную документацию: https://squidfunk.github.io/mkdocs-material/

### Как добавить новый язык документации?

1. Создайте папку `docs/LANG_CODE/` (например, `docs/fr/` для французского)
2. Скопируйте структуру из `docs/en/`
3. Обновите `mkdocs.yml` в разделе `i18n`:
   ```yaml
   - locale: fr
     name: Français
     build: true
   ```
4. Переведите документы
5. Сделайте коммит и пуш

---

## 📞 Поддержка и контакты

Если у вас есть вопросы по документации:

- **Откройте Issue:** https://github.com/hypo69/AI-Breadboard/issues
- **Email:** hypo69@yandex.com
- **GitHub Discussions:** https://github.com/hypo69/AI-Breadboard/discussions
