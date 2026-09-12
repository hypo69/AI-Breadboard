# Администраторская документация по Read the Docs

Данный документ содержит инструкции для администраторов по управлению документацией проекта AI-Breadboard на платформе Read the Docs.

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Настройка Read the Docs](#настройка-read-the-docs)
- [Добавление проекта](#добавление-проекта)
- [Конфигурация вебхука GitHub](#конфигурация-вебхука-github)
- [Управление версиями документации](#управление-версиями-документации)
- [Отладка ошибок сборки](#отладка-ошибок-сборки)
- [Обновление зависимостей](#обновление-зависимостей)
- [Типичные проблемы и решения](#типичные-проблемы-и-решения)

---

## Быстрый старт

### Предварительные условия

- Аккаунт на [Read the Docs](https://readthedocs.org)
- Доступ администратора к репозиторию GitHub
- Python 3.10 или выше
- Установленные зависимости: `pip install -r install/req/requirements-docs.txt`

### Сборка документации локально

```bash
# Установка зависимостей
pip install -r install/req/requirements-docs.txt

# Сборка документации MkDocs
mkdocs build

# Просмотр документации локально
mkdocs serve
```

Документация будет доступна по адресу: http://127.0.0.1:8000

---

## Настройка Read the Docs

### Конфигурационный файл `.readthedocs.yml`

Основная конфигурация расположена в файле `.readthedocs.yml` в корне репозитория.

#### Ключевые параметры

| Параметр | Значение | Описание |
|----------|----------|---------|
| `version` | 2 | Версия конфигурационного формата |
| `build.os` | ubuntu-22.04 | ОС для сборки |
| `build.tools.python` | 3.10 | Версия Python |
| `mkdocs.configuration` | mkdocs.yml | Путь к конфигурации MkDocs |
| `mkdocs.fail_on_warning` | true | Отказать сборку при предупреждениях |
| `python.install[0].requirements` | install/req/requirements-docs.txt | Путь к requirements |

#### Структура конфигурации

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

versions:
  build: all
  regular: latest
  earliest: earliest

formats:
  - pdf
  - epub

build_jobs:
  post_build:
    - printenv
```

---

## Добавление проекта

### Шаг 1: Подготовка репозитория

1. Убедитесь, что репозиторий содержит:
   - `.readthedocs.yml` в корне
   - `mkdocs.yml` в корне
   - `install/req/requirements-docs.txt` с зависимостями
   - Папка `docs/` со структурой документации

2. Проверьте синтаксис конфигурационных файлов:
   ```bash
   mkdocs build --strict
   ```

### Шаг 2: Регистрация на Read the Docs

1. Перейдите на [https://readthedocs.org](https://readthedocs.org)
2. Нажмите **Sign Up** и создайте аккаунт
3. Подтвердите email

### Шаг 3: Импорт проекта

1. На панели управления нажмите **Import a Project**
2. Выберите **Import Manually**
3. Заполните форму:
   - **Project name**: `ai-breadboard`
   - **Repository URL**: `https://github.com/hypo69/AI-Breadboard.git`
   - **Repository type**: Git
   - **Documentation type**: MkDocs
4. Нажмите **Next**

### Шаг 4: Конфигурация

1. На странице проекта перейдите в **Admin** → **Settings**
2. Проверьте параметры:
   - **Repository URL** должен быть корректным
   - **Documentation type** должен быть `MkDocs`
3. Сохраните изменения

### Шаг 5: Запуск первой сборки

1. Перейдите на вкладку **Builds**
2. Нажмите **Build Version**
3. Дождитесь завершения сборки

Если сборка пройдена успешно, документация будет доступна по адресу:
- Основной сайт: https://ai-breadboard.readthedocs.io
- Русская версия: https://ai-breadboard.readthedocs.io/ru/latest

---

## Конфигурация вебхука GitHub

### Автоматическое обновление документации

Для автоматического обновления документации при каждом пушу в репозиторий:

#### Шаг 1: Создание вебхука на Read the Docs

1. На странице проекта перейдите в **Admin** → **Integrations**
2. Нажмите **Add Integration**
3. Выберите **GitHub incoming webhook**
4. Скопируйте URL вебхука (будет выглядеть как `https://readthedocs.org/api/v2/webhook/ai-breadboard/...`)

#### Шаг 2: Добавление вебхука в GitHub

1. На странице репозитория перейдите в **Settings** → **Webhooks**
2. Нажмите **Add webhook**
3. Заполните форму:
   - **Payload URL**: Вставьте URL с Read the Docs
   - **Content type**: `application/json`
   - **Events**: Выберите **Just the push event**
   - **Active**: Отметьте галочку
4. Нажмите **Add webhook**

#### Шаг 3: Проверка

1. На странице вебхука перейдите на вкладку **Recent Deliveries**
2. Проверьте, что последняя доставка имела статус `200`

### Тестирование вебхука

```bash
# Выполните пуш в репозиторий
git push origin main

# Проверьте статус сборки на Read the Docs
# Перейдите в Admin → Builds
```

---

## Управление версиями документации

### Построение всех версий

По умолчанию Read the Docs собирает документацию для всех тегов и веток, указанных в конфигурации.

#### Конфигурация версий

```yaml
versions:
  build: all          # Собирать все версии
  regular: latest     # Основная версия
  earliest: earliest  # Самая старая версия
```

#### Построение конкретной версии

1. На странице проекта перейдите в **Versions**
2. Найдите нужную версию (ветка или тег)
3. Нажмите на версию для просмотра её статуса
4. Нажмите **Build** для пересборки

#### Активирование/Деактивирование версий

1. На странице **Versions** найдите версию
2. Используйте переключатель для активирования/деактивирования

### Управление тегами и ветками

#### Тги версий

Теги в Git автоматически создают новые версии документации:

```bash
# Создание тага
git tag -a v1.0.0 -m "Release version 1.0.0"

# Отправка тага на GitHub
git push origin v1.0.0
```

#### Главные ветки

По умолчанию документируются:
- `main` или `master` (основная версия)
- Другие важные ветки

---

## Отладка ошибок сборки

### Просмотр логов сборки

1. На странице проекта перейдите в **Builds**
2. Нажмите на сборку с ошибкой
3. Прокрутите вниз для просмотра полного лога

### Частые ошибки и решения

#### Ошибка: Python зависимости не установлены

**Сообщение в логе:**
```
ModuleNotFoundError: No module named 'mkdocs'
```

**Решение:**
```yaml
python:
  install:
    - requirements: install/req/requirements-docs.txt
```

#### Ошибка: MkDocs конфигурация не найдена

**Сообщение в логе:**
```
ConfigError: config file 'mkdocs.yml' does not exist
```

**Решение:**
- Проверьте, что `mkdocs.yml` находится в корне репозитория
- Обновите путь в `.readthedocs.yml` если необходимо

#### Ошибка: Warning как ошибка

**Сообщение в логе:**
```
ERROR: Build failed due to warnings
```

**Решение:**
1. Исправьте предупреждения в документации
2. Или установите `fail_on_warning: false` в `.readthedocs.yml`

### Локальная отладка

Для отладки ошибок локально:

```bash
# 1. Установите зависимости
pip install -r install/req/requirements-docs.txt

# 2. Запустите сборку с verbose режимом
mkdocs build --verbose

# 3. Проверьте результат
ls -la site/

# 4. Просмотрите результат в браузере
mkdocs serve
```

### Использование Docker для точной эмуляции

Read the Docs использует Docker. Для точной эмуляции окружения:

```bash
# Установите Docker
# Затем выполните:

docker run -it -v $(pwd):/docs ubuntu:22.04 bash

# Внутри контейнера:
apt-get update
apt-get install -y python3.10 python3-pip
pip install -r /docs/install/req/requirements-docs.txt
cd /docs
mkdocs build
```

---

## Обновление зависимостей

### Файл зависимостей: `install/req/requirements-docs.txt`

Этот файл содержит все Python пакеты, необходимые для сборки документации:

```
mkdocs>=1.5.0
mkdocs-material>=9.5.0
mkdocstrings[python]==0.22.0
pymdown-extensions>=10.0
pygments>=2.15.0
python-dotenv>=1.0.0
mkdocs-static-i18n>=1.2.0
```

### Процесс обновления

#### Шаг 1: Обновление локально

```bash
# Установите новую версию зависимости
pip install --upgrade mkdocs-material

# Проверьте совместимость
mkdocs build --strict

# Убедитесь, что всё работает
mkdocs serve
```

#### Шаг 2: Обновление файла требований

```bash
# Обновите версию в install/req/requirements-docs.txt
# Пример: mkdocs-material>=9.5.0 → mkdocs-material>=10.0.0

# Закоммитьте изменения
git add install/req/requirements-docs.txt
git commit -m "chore: update documentation dependencies"

# Отправьте на GitHub
git push origin main
```

#### Шаг 3: Проверка на Read the Docs

1. Перейдите в **Builds** на Read the Docs
2. Дождитесь, пока вебхук автоматически запустит сборку
3. Проверьте логи для ошибок

### Автоматическое обновление зависимостей

Можно использовать сервисы типа Dependabot для автоматических обновлений:

1. На странице репозитория перейдите в **Settings** → **Code security and analysis**
2. Включите **Dependabot alerts** и **Dependabot updates**
3. Создайте `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/install/req"
    schedule:
      interval: "weekly"
    allow:
      - dependency-type: "direct"
```

---

## Типичные проблемы и решения

### Проблема 1: Документация не обновляется после пуша

**Причины:**
- Вебхук не настроен
- Вебхук отключен в GitHub
- Ошибка в конфигурации

**Решение:**

```bash
# 1. Проверьте вебхук на GitHub
# Settings → Webhooks → нажмите на вебхук Read the Docs

# 2. Проверьте "Recent Deliveries"
# Если последняя доставка имеет красный значок - ошибка доставки

# 3. Переконфигурируйте вебхук
# Скопируйте URL с Read the Docs (Admin → Integrations)
# Обновите URL в GitHub

# 4. Протестируйте вебхук
# На странице вебхука нажмите "Redeliver" на последней доставке
```

### Проблема 2: Сборка тратит много времени

**Причины:**
- Большой размер репозитория
- Медленная установка зависимостей
- Обработка множества файлов

**Решение:**

```yaml
# .readthedocs.yml - Оптимизация сборки

# 1. Ограничьте глубину клонирования
build:
  os: ubuntu-22.04
  tools:
    python: "3.10"
  apt_packages:
    - git

# 2. Используйте кеширование
# (Включено по умолчанию на Read the Docs)

# 3. Оптимизируйте requirements
# - Удалите неиспользуемые зависимости
# - Используйте pinned версии для стабильности
```

### Проблема 3: Многоязычная документация не работает

**Причины:**
- Неправильная конфигурация i18n плагина
- Отсутствуют файлы локализации
- Неверная структура папок

**Решение:**

```yaml
# mkdocs.yml - Проверьте конфигурацию i18n

plugins:
  - i18n:
      docs_structure: folder  # Структура: docs/en, docs/ru, и т.д.
      languages:
        - locale: en
          name: English
          build: true
          default: true
        - locale: ru
          name: Русский
          build: true
```

**Структура папок:**
```
docs/
├── en/
│   ├── index.md
│   ├── getting-started.md
│   └── ...
├── ru/
│   ├── index.md
│   ├── getting-started.md
│   └── ...
└── es/
    ├── index.md
    ├── getting-started.md
    └── ...
```

### Проблема 4: Синтаксис Markdown не отображается

**Причины:**
- Неподдерживаемый расширение Markdown
- Неправильная конфигурация расширений
- Конфликт между расширениями

**Решение:**

```yaml
# mkdocs.yml - Проверьте расширения Markdown

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences
  - tables
  - toc:
      permalink: true
```

### Проблема 5: Внешние ссылки в документации неработающие

**Причины:**
- Неправильный формат ссылок
- Опечатки в URL
- Внешний сайт недоступен при сборке

**Решение:**

```markdown
# Правильный формат ссылок

[Текст ссылки](https://example.com/path)
[Относительная ссылка](../getting-started.md)
[Якорь](../getting-started.md#section)
```

### Проблема 6: Документация выглядит по-разному локально и на Read the Docs

**Причины:**
- Разные версии зависимостей
- Разные конфигурации
- Кешированные ресурсы

**Решение:**

```bash
# 1. Убедитесь, что используете точные версии зависимостей
pip install -r install/req/requirements-docs.txt --force-reinstall

# 2. Очистите кеш
rm -rf .mkdocs_cache/
rm -rf site/

# 3. Пересоберите документацию
mkdocs build --clean

# 4. Проверьте в браузере
mkdocs serve
```

---

## Контакты и ресурсы

### Документация и поддержка

- [Официальная документация Read the Docs](https://docs.readthedocs.io)
- [Документация MkDocs](https://www.mkdocs.org)
- [Документация Material for MkDocs](https://squidfunk.github.io/mkdocs-material)
- [Документация mkdocstrings](https://mkdocstrings.github.io)

### Полезные команды

```bash
# Проверка конфигурации MkDocs
mkdocs build --strict --verbose

# Сборка в определённую папку
mkdocs build -d my_output_folder

# Запуск локального сервера на другом порту
mkdocs serve --dev-addr 127.0.0.1:9000

# Очистка кеша
mkdocs build --clean
```

### Отладка в GitHub Actions

Если вы используете GitHub Actions для сборки:

```yaml
name: Documentation Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r install/req/requirements-docs.txt
      - run: mkdocs build --strict
      - uses: actions/upload-artifact@v3
        with:
          name: documentation
          path: site/
```

---

## Заключение

Данный документ содержит полную информацию для администрирования документации AI-Breadboard на Read the Docs. Для получения дополнительной информации обратитесь к официальной документации Read the Docs или посетите репозиторий проекта на GitHub.

**Последнее обновление:** 2024
**Версия:** 1.0
