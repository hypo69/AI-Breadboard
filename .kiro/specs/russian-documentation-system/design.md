# Дизайн системы документации AI-Breadboard (Russian Documentation System)

## 1. Обзор архитектуры

Система документации AI-Breadboard представляет собой комплексное решение для управления, генерации и публикации документации на русском языке. Архитектура состоит из четырёх основных уровней:

```
┌─────────────────────────────────────────────────────────────┐
│                    Read the Docs (Публикация)              │
│                 (Production Documentation)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│            GitHub Actions (CI/CD Pipeline)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Валидация Markdown    2. Генерация API              │ │
│  │ 3. Проверка ссылок       4. Сборка документации        │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│         Локальная разработка (Development Layer)            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ MkDocs / Sphinx | Скрипты сборки | Live Server         │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│          Исходные данные (Source Layer)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ docs/ru/        Python docstrings                      │ │
│  │ ├── manual/     ├── skills/                            │ │
│  │ ├── api/        ├── agents/                            │ │
│  │ ├── guides/     └── core/                              │ │
│  │ └── conf.py                                            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 2. Структура каталогов и компоненты

### 2.1 Структура `docs/ru/`

```
docs/
└── ru/
    ├── index.md                      # Главная страница документации
    ├── conf.py                       # Конфигурация Sphinx
    ├── requirements-docs.txt         # Зависимости для документации
    ├── manual/                       # Руководства и примеры
    │   ├── index.md
    │   ├── getting-started.md        # Начало работы
    │   ├── installation.md           # Установка
    │   ├── configuration.md          # Конфигурация
    │   ├── usage-examples.md         # Примеры использования
    │   └── troubleshooting.md        # Решение проблем
    ├── api/                          # Автогенерированная API-документация
    │   ├── index.md
    │   ├── skills.md                 # (auto-generated)
    │   ├── agents.md                 # (auto-generated)
    │   ├── core.md                   # (auto-generated)
    │   └── utils.md                  # (auto-generated)
    ├── guides/                       # Подробные руководства
    │   ├── developing-skills.md
    │   ├── creating-agents.md
    │   └── testing-strategy.md
    ├── architecture/                 # Документация по архитектуре
    │   ├── overview.md
    │   ├── components.md
    │   └── data-models.md
    ├── contributing.md               # Правила контрибуции
    ├── changelog.md                  # История изменений
    ├── _templates/                   # Шаблоны для Sphinx
    │   └── custom.html
    └── _static/                      # Статические ресурсы
        ├── css/
        ├── images/
        └── js/
```

### 2.2 Компоненты системы

#### Компонент 1: Sphinx/MkDocs Конфигуратор
**Назначение:** Управление конфигурацией сборки документации
**Входы:** `docs/conf.py`, `mkdocs.yml`
**Выходы:** Скомпилированная HTML-документация
**Ответственность:** 
- Парсинг конфигурации
- Управление темами и плагинами
- Настройка локализации

#### Компонент 2: Генератор API-документации
**Назначение:** Автоматическое создание API-документации из Python docstrings
**Входы:** Python-файлы с docstrings
**Выходы:** `.md` файлы в `docs/ru/api/`
**Ответственность:**
- Парсинг docstrings (Google-style)
- Генерация структурированных Markdown
- Создание примеров кода

#### Компонент 3: Валидатор документации
**Назначение:** Проверка качества и согласованности документации
**Входы:** Файлы документации (`.md`)
**Выходы:** Отчёты об ошибках
**Ответственность:**
- Валидация Markdown синтаксиса
- Проверка ссылок (внутренних и внешних)
- Валидация обязательных разделов

#### Компонент 4: GitHub Actions Оркестратор
**Назначение:** Управление CI/CD pipeline
**Входы:** Git events (push, pull_request)
**Выходы:** Artifacts, уведомления
**Ответственность:**
- Запуск workflow'ов
- Координация компонентов валидации и генерации
- Создание артефактов

#### Компонент 5: Read the Docs Интегратор
**Назначение:** Публикация документации на платформе
**Входы:** Конфиг `.readthedocs.yml`
**Выходы:** Публичная документация
**Ответственность:**
- Синхронизация с репозиторием
- Управление версионированием
- Активация вебхуков

#### Компонент 6: Локальный разработчик
**Назначение:** Поддержка локальной разработки
**Входы:** Команды из CLI
**Выходы:** Локальный сервер с документацией
**Ответственность:**
- Горячая перезагрузка при изменениях
- Live preview сервер

## 3. Конфигурационные файлы

### 3.1 `.readthedocs.yml` (Read the Docs конфигурация)

```yaml
# Конфигурация Read the Docs для проекта AI-Breadboard
version: 2

# Версия Python для сборки
python:
  version: "3.10"
  install:
    - requirements: docs/ru/requirements-docs.txt

# Сборка документации
build:
  os: ubuntu-22.04
  tools:
    python: "3.10"

# Конфигурация Sphinx
sphinx:
  configuration: docs/ru/conf.py
  fail_on_warning: true

# Версионирование
versions:
  active: latest
  builds:
    latest:
      commands: "pip install -r docs/ru/requirements-docs.txt && sphinx-build -b html docs/ru docs/ru/_build/html"

# Redirects (перенаправления)
redirects:
  old-api-page: /en/latest/api/new-page/

# Включение функций
features:
  - versioning

# Notifications
notifications:
  webhooks:
    - url: "{{ env.WEBHOOK_URL }}"
      events: [build.success, build.failed]
```

### 3.2 `.github/workflows/docs.yml` (GitHub Actions workflow)

```yaml
# GitHub Actions Workflow для сборки и валидации документации
name: Documentation Build & Validation

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'docs/ru/**'
      - 'src/**'
      - '.github/workflows/docs.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'docs/ru/**'
      - 'src/**'

jobs:
  # Задача 1: Валидация Markdown и структуры
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Установка Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Установка зависимостей
        run: |
          python -m pip install --upgrade pip
          pip install -r docs/ru/requirements-docs.txt
      
      - name: Валидация Markdown синтаксиса
        run: |
          pip install mdformat markdownlint-cli2
          markdownlint-cli2 'docs/ru/**/*.md'
      
      - name: Проверка структуры документации
        run: python scripts/docs/validate_structure.py
      
      - name: Проверка ссылок в документации
        run: python scripts/docs/check_links.py

  # Задача 2: Генерация API-документации
  generate-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Установка Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Установка зависимостей
        run: |
          python -m pip install --upgrade pip
          pip install -r docs/ru/requirements-docs.txt
          pip install pdoc sphinx-autodoc-typehints
      
      - name: Генерация API-документации
        run: python scripts/docs/generate_api.py
      
      - name: Проверка сгенерированных файлов
        run: |
          if [ -z "$(git diff --name-only docs/ru/api/*.md)" ]; then
            echo "API документация актуальна"
          else
            echo "WARNING: API документация требует обновления"
            git diff docs/ru/api/*.md
          fi

  # Задача 3: Сборка документации Sphinx
  build:
    needs: [validate, generate-api]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Установка Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Установка зависимостей
        run: |
          python -m pip install --upgrade pip
          pip install -r docs/ru/requirements-docs.txt
      
      - name: Сборка Sphinx документации
        run: |
          sphinx-build -W --keep-going -b html -d docs/ru/_build/doctrees docs/ru docs/ru/_build/html
      
      - name: Сборка PDF (опционально)
        run: |
          apt-get update && apt-get install -y latexmk texlive-xetex
          sphinx-build -b latex docs/ru docs/ru/_build/latex
          cd docs/ru/_build/latex && make all-pdf
        continue-on-error: true
      
      - name: Загрузка артефактов
        uses: actions/upload-artifact@v3
        with:
          name: html-documentation
          path: docs/ru/_build/html/
          retention-days: 30

  # Задача 4: Опубликованное уведомление
  notify:
    if: always()
    needs: [build]
    runs-on: ubuntu-latest
    steps:
      - name: Отправка уведомления в Slack
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Ошибка при сборке документации AI-Breadboard'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 3.3 `docs/conf.py` (Конфигурация Sphinx)

```python
"""
Конфигурация Sphinx для документации AI-Breadboard на русском языке.

Параметры конфигурации для сборки документации с поддержкой:
- Русского языка локализации
- Автоматической генерации API-документации
- Темизации
- Расширений
"""

import os
import sys
from datetime import datetime

# Добавление путей для поиска модулей
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

# Основные параметры проекта
project = 'AI-Breadboard'
copyright = f'{datetime.now().year}, AI-Breadboard Contributors'
author = 'AI-Breadboard Team'
version = '1.0'
release = '1.0.0'

# Параметры локализации
language = 'ru'
locale_paths = ['locale']

# Расширения Sphinx
extensions = [
    'sphinx.ext.autodoc',              # Автоматическая генерация из docstrings
    'sphinx.ext.autosummary',          # Автоматические таблицы кода
    'sphinx.ext.intersphinx',          # Перекрёстные ссылки между проектами
    'sphinx.ext.viewcode',             # Ссылки на исходный код
    'sphinx.ext.napoleon',             # Поддержка Google-style docstrings
    'sphinx_autodoc_typehints',        # Типизация в автодоке
    'sphinx_rtd_theme',                # Read the Docs тема
    'myst_parser',                     # Поддержка Markdown
    'sphinx_design',                   # Компоненты дизайна
    'sphinx_copybutton',               # Кнопка копирования кода
]

# Конфигурация источников
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Главный файл
master_doc = 'index'

# Шаблоны и статика
templates_path = ['_templates']
html_static_path = ['_static']

# Исключения
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    '*.egg-info',
]

# Параметры HTML
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'logo_only': True,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    'github_url': 'https://github.com/breadboard-ai/breadboard',
    'language': 'ru',
}

html_logo = '_static/images/logo.png'
html_favicon = '_static/images/favicon.ico'

# Параметры LaTeX (для PDF)
latex_elements = {
    'papersize': 'a4',
    'pointsize': '11pt',
    'preamble': r'\usepackage[utf8]{inputenc}\usepackage[russian]{babel}',
    'fontenc': '',
    'inputenc': '',
}

latex_documents = [
    ('index', 'ai-breadboard-ru.tex', 'Документация AI-Breadboard', 'AI-Breadboard Team', 'manual'),
]

# Параметры автодока
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': False,
    'show-inheritance': True,
    'typehints': 'description',
}

# Параметры intersphinx
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master', None),
}

# Параметры Markdown
myst_enable_extensions = [
    'colon_fence',
    'dollarmath',
    'linkify',
    'substitution',
    'tasklist',
]

# Функции обработки
def setup(app):
    """Инициализация расширений Sphinx."""
    app.add_config_value('suppress_warnings', [], '')
    app.connect('config-inited', process_docs)

def process_docs(app, config):
    """Пост-обработка конфигурации."""
    pass
```

### 3.4 `requirements-docs.txt` (Зависимости документации)

```
# Основные инструменты для сборки документации
sphinx>=7.0.0           # Генератор документации
sphinx-rtd-theme>=1.3.0 # Read the Docs тема
myst-parser>=1.0.0      # Поддержка Markdown

# Расширения Sphinx
sphinx-autodoc-typehints>=1.25.0    # Поддержка type hints
sphinx-design>=0.5.0                # Дизайн компоненты
sphinx-copybutton>=0.5.2             # Кнопка копирования кода
sphinx-notfound-page>=0.8.3         # Страница 404

# Генерация API-документации
pdoc>=13.0.0            # Альтернативный генератор API
black>=23.0.0           # Форматирование Python кода

# Валидация и проверки
markdownlint-cli2>=0.10.0  # Валидация Markdown
linkchecker>=10.2.1        # Проверка ссылок
yamllint>=1.31.0           # Валидация YAML

# Утилиты
Pillow>=10.0.0          # Обработка изображений
PyYAML>=6.0             # Работа с YAML
python-dateutil>=2.8.0  # Работа с датами
```

## 4. Скрипты автоматизации

### 4.1 `scripts/docs/generate_api.py` (Генератор API-документации)

```python
"""
Скрипт для автоматической генерации API-документации из Python docstrings.

Использует ast для парсинга и создаёт структурированные Markdown файлы.
"""

import os
import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class DocstringParser:
    """Парсер Python docstrings в Google-формате."""
    
    @staticmethod
    def parse_function(func_node: ast.FunctionDef) -> Dict:
        """Парсит функцию и извлекает информацию из docstring."""
        docstring = ast.get_docstring(func_node) or "Документация отсутствует"
        
        return {
            'name': func_node.name,
            'type': 'function',
            'docstring': docstring,
            'args': [arg.arg for arg in func_node.args.args],
            'lineno': func_node.lineno,
        }
    
    @staticmethod
    def parse_class(class_node: ast.ClassDef) -> Dict:
        """Парсит класс и методы."""
        docstring = ast.get_docstring(class_node) or "Документация отсутствует"
        
        methods = []
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                methods.append(DocstringParser.parse_function(node))
        
        return {
            'name': class_node.name,
            'type': 'class',
            'docstring': docstring,
            'methods': methods,
            'lineno': class_node.lineno,
        }

class MarkdownGenerator:
    """Генератор Markdown из распарсенной информации."""
    
    @staticmethod
    def generate_header(title: str, level: int = 1) -> str:
        """Генерирует Markdown заголовок."""
        return f"{'#' * level} {title}\n\n"
    
    @staticmethod
    def generate_function_docs(func: Dict) -> str:
        """Генерирует документацию функции в Markdown."""
        md = f"### `{func['name']}`\n\n"
        md += f"{func['docstring']}\n\n"
        
        if func['args']:
            md += "**Параметры:**\n"
            for arg in func['args']:
                md += f"- `{arg}`\n"
            md += "\n"
        
        return md
    
    @staticmethod
    def generate_class_docs(cls: Dict) -> str:
        """Генерирует документацию класса в Markdown."""
        md = f"## `{cls['name']}`\n\n"
        md += f"{cls['docstring']}\n\n"
        
        if cls['methods']:
            md += "### Методы\n\n"
            for method in cls['methods']:
                md += MarkdownGenerator.generate_function_docs(method)
        
        return md

class APIDocumentationGenerator:
    """Главный генератор API-документации."""
    
    def __init__(self, src_root: Path, docs_root: Path):
        self.src_root = src_root
        self.docs_root = docs_root
        self.api_dir = docs_root / 'ru' / 'api'
        self.api_dir.mkdir(parents=True, exist_ok=True)
    
    def process_python_file(self, file_path: Path) -> Dict:
        """Обрабатывает Python файл и извлекает документацию."""
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        docs = {
            'file': str(file_path.relative_to(self.src_root)),
            'classes': [],
            'functions': [],
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docs['classes'].append(DocstringParser.parse_class(node))
            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                docs['functions'].append(DocstringParser.parse_function(node))
        
        return docs
    
    def generate_module_docs(self, module_name: str) -> str:
        """Генерирует документацию для модуля."""
        module_path = self.src_root / module_name.replace('.', '/') / '__init__.py'
        
        if not module_path.exists():
            return f"# Модуль `{module_name}`\n\nДокументация отсутствует.\n"
        
        docs = self.process_python_file(module_path)
        
        md = MarkdownGenerator.generate_header(f"Модуль `{module_name}`", 1)
        
        for cls in docs['classes']:
            md += MarkdownGenerator.generate_class_docs(cls)
        
        for func in docs['functions']:
            md += MarkdownGenerator.generate_function_docs(func)
        
        return md
    
    def generate(self, modules: List[str]) -> None:
        """Генерирует API-документацию для перечисленных модулей."""
        for module in modules:
            output_file = self.api_dir / f'{module}.md'
            content = self.generate_module_docs(module)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ Сгенерирована документация для модуля: {module}")
        
        # Генерируем индекс API
        self.generate_api_index(modules)
    
    def generate_api_index(self, modules: List[str]) -> None:
        """Генерирует индексный файл API-документации."""
        index_file = self.api_dir / 'index.md'
        
        md = MarkdownGenerator.generate_header("API Документация", 1)
        md += "Автоматически сгенерированная документация API\n\n"
        
        md += "## Модули\n\n"
        for module in sorted(modules):
            md += f"- [`{module}`]({module}.md)\n"
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"✓ Сгенерирован индекс API")

if __name__ == '__main__':
    # Конфигурация путей
    project_root = Path(__file__).parent.parent.parent
    src_root = project_root / 'src'
    docs_root = project_root / 'docs'
    
    # Модули для генерации документации
    modules = [
        'breadboard.skills',
        'breadboard.agents',
        'breadboard.core',
        'breadboard.utils',
    ]
    
    # Генерирование
    generator = APIDocumentationGenerator(src_root, docs_root)
    generator.generate(modules)
```

### 4.2 `scripts/docs/validate_structure.py` (Валидатор структуры)

```python
"""
Скрипт для валидации структуры документации и проверки обязательных разделов.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class DocumentationValidator:
    """Валидатор структуры документации."""
    
    REQUIRED_SECTIONS = {
        'index.md': ['# ', 'Содержание', 'Разделы'],
        'manual/index.md': ['# ', 'Руководства'],
        'api/index.md': ['# ', 'API', 'Модули'],
    }
    
    REQUIRED_FILES = [
        'index.md',
        'conf.py',
        'manual/index.md',
        'api/index.md',
    ]
    
    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_file_exists(self, relative_path: str) -> bool:
        """Проверяет, что файл существует."""
        file_path = self.docs_root / relative_path
        exists = file_path.exists()
        
        if not exists:
            self.errors.append(f"❌ Отсутствует обязательный файл: {relative_path}")
        
        return exists
    
    def validate_sections(self, relative_path: str, required_sections: List[str]) -> bool:
        """Проверяет наличие обязательных разделов в файле."""
        file_path = self.docs_root / relative_path
        
        if not file_path.exists():
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        all_present = True
        for section in required_sections:
            if section not in content:
                self.warnings.append(
                    f"⚠️  В файле {relative_path} отсутствует раздел: '{section}'"
                )
                all_present = False
        
        return all_present
    
    def validate_markdown_syntax(self, file_path: Path) -> bool:
        """Проверяет синтаксис Markdown."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Простые проверки синтаксиса
            if content.count('```') % 2 != 0:
                self.errors.append(f"❌ Несбалансированные блоки кода в {file_path}")
                return False
            
            return True
        except Exception as e:
            self.errors.append(f"❌ Ошибка чтения файла {file_path}: {e}")
            return False
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        """Выполняет полную валидацию."""
        print("🔍 Валидация структуры документации...")
        
        # Проверка обязательных файлов
        for required_file in self.REQUIRED_FILES:
            self.validate_file_exists(required_file)
        
        # Проверка обязательных разделов
        for file_path, sections in self.REQUIRED_SECTIONS.items():
            self.validate_sections(file_path, sections)
        
        # Проверка всех Markdown файлов
        for md_file in self.docs_root.rglob('*.md'):
            self.validate_markdown_syntax(md_file)
        
        success = len(self.errors) == 0
        
        return success, self.errors + self.warnings

if __name__ == '__main__':
    docs_root = Path(__file__).parent.parent.parent / 'docs' / 'ru'
    
    validator = DocumentationValidator(docs_root)
    success, messages = validator.validate_all()
    
    for msg in messages:
        print(msg)
    
    sys.exit(0 if success else 1)
```

### 4.3 `scripts/docs/check_links.py` (Проверка ссылок)

```python
"""
Скрипт для проверки внутренних и внешних ссылок в документации.
"""

import re
from pathlib import Path
from typing import List, Set, Tuple
import sys

class LinkChecker:
    """Проверяет ссылки в документации."""
    
    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.errors: List[str] = []
        self.all_files: Set[str] = set()
    
    def collect_all_files(self) -> None:
        """Собирает все доступные файлы документации."""
        for md_file in self.docs_root.rglob('*.md'):
            rel_path = md_file.relative_to(self.docs_root)
            self.all_files.add(str(rel_path).replace('\\', '/'))
    
    def extract_links(self, content: str) -> List[str]:
        """Извлекает ссылки из Markdown контента."""
        # Ссылки вида [text](url)
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(pattern, content)
        return [url for _, url in matches]
    
    def validate_internal_link(self, link: str, source_file: str) -> bool:
        """Проверяет внутреннюю ссылку."""
        if link.startswith('http'):
            return True  # Внешняя ссылка, пропускаем
        
        if link.startswith('#'):
            return True  # Якорь, пропускаем
        
        # Удаляем якоря
        target = link.split('#')[0]
        
        if not target:
            return True
        
        # Нормализуем путь
        target = target.replace('\\', '/')
        
        if target not in self.all_files:
            self.errors.append(f"❌ Неверная ссылка в {source_file}: {link}")
            return False
        
        return True
    
    def check_file(self, md_file: Path) -> None:
        """Проверяет ссылки в файле."""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        links = self.extract_links(content)
        rel_path = md_file.relative_to(self.docs_root)
        
        for link in links:
            self.validate_internal_link(link, str(rel_path))
    
    def check_all(self) -> Tuple[bool, List[str]]:
        """Проверяет все файлы."""
        print("🔗 Проверка ссылок в документации...")
        
        self.collect_all_files()
        
        for md_file in self.docs_root.rglob('*.md'):
            self.check_file(md_file)
        
        success = len(self.errors) == 0
        return success, self.errors

if __name__ == '__main__':
    docs_root = Path(__file__).parent.parent.parent / 'docs' / 'ru'
    
    checker = LinkChecker(docs_root)
    success, messages = checker.check_all()
    
    for msg in messages:
        print(msg)
    
    sys.exit(0 if success else 1)
```

## 5. Интеграция компонентов

### 5.1 Поток данных при коммите

```
GitHub Push Event
    ↓
GitHub Actions Trigger
    ├→ Валидация Markdown синтаксиса (check-syntax.sh)
    ├→ Проверка структуры (validate_structure.py)
    ├→ Генерация API-документации (generate_api.py)
    ├→ Проверка ссылок (check_links.py)
    ├→ Сборка Sphinx (sphinx-build)
    └→ Загрузка артефактов
         ↓
    На успех: Read the Docs webhook
         ↓
    Сборка на Read the Docs
         ↓
    Публикация документации
         ↓
    Рассылка уведомлений
```

### 5.2 Локальный workflow разработчика

```
Разработчик редактирует docs/ru/*.md
    ↓
Сохранение файла
    ↓
Watch-скрипт обнаруживает изменение
    ↓
Перестроение изменённого раздела
    ↓
Live reload в браузере (localhost:8000)
    ↓
Разработчик просматривает изменения
    ↓
Коммит и push в репозиторий
```

## 6. Структура данных и модели

### 6.1 Модель документа

```python
@dataclass
class DocstringMetadata:
    """Метаданные экстрактированные из docstring."""
    name: str
    type: str  # 'function' | 'class' | 'method'
    description: str
    parameters: Dict[str, str]  # name -> type
    returns: Optional[str]
    raises: List[str]
    examples: List[str]
    lineno: int

@dataclass
class DocumentationFile:
    """Структура файла документации."""
    path: Path
    title: str
    sections: List[str]
    links: List[str]
    api_references: List[DocstringMetadata]
    language: str = 'ru'
```

### 6.2 Модель конфигурации

```yaml
docs:
  title: "AI-Breadboard Документация"
  language: "ru"
  source_dir: "docs/ru"
  build_dir: "docs/ru/_build"
  
api:
  enabled: true
  output_dir: "docs/ru/api"
  modules:
    - "breadboard.skills"
    - "breadboard.agents"
    - "breadboard.core"

validation:
  check_links: true
  check_syntax: true
  check_sections: true
  
build:
  theme: "sphinx_rtd_theme"
  format: "html"
  pdf: true
```

## 7. Обработка ошибок и восстановление

### 7.1 Стратегия обработки ошибок

| Ошибка | Обработка | Восстановление |
|--------|-----------|-----------------|
| Неверный синтаксис Markdown | Перерывает сборку | Отправляет отчёт, требует исправления |
| Broken links | Предупреждение | Генерирует отчёт, не перерывает |
| Missing docstrings | Предупреждение | Создаёт заполнители в API-документации |
| Build timeout | Повтор (3 попытки) | Отправляет уведомление при отказе |
| Read the Docs недоступен | Очередь | Повторяет попытку с экспоненциальной задержкой |

### 7.2 Логирование

```
docs/
├── _build/
│   ├── html/
│   ├── logs/
│   │   ├── build.log      # Основной лог сборки
│   │   ├── errors.log     # Ошибки валидации
│   │   ├── api-gen.log    # Логи генерации API
│   │   └── validation.log # Результаты проверок
```

## 8. Correctness Properties

*Свойство представляет собой характеристику или поведение, которые должны быть истинны для всех допустимых выполнений системы — это формальное утверждение о том, что должна делать система. Свойства служат мостом между понятными человеку спецификациями и механически проверяемыми гарантиями корректности.*

### Property 1: Структурная консистентность иерархии документов

*Для любого набора документов в `docs/ru/`, если добавляется новый файл `.md` в соответствующую директорию с корректным именем, система должна автоматически включить его в навигацию через обновление конфигурации.*

**Validates: Requirements 1.3, 1.4**

### Property 2: API-документация полнота

*Для любого Python-модуля с функциями и классами, содержащими Google-style docstrings, система должна генерировать Markdown-файл в `docs/ru/api/`, содержащий все извлечённые описания функций, параметры, типы возвращаемых значений и примеры.*

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Docstring обновление трансляция

*Для любого Python-файла, если docstring функции или класса обновляется, и система запускает процесс регенерации API-документации, то соответствующий `.md` файл в `docs/ru/api/` должен быть обновлён с новым контентом.*

**Validates: Requirements 2.5**

### Property 4: Валидация Markdown синтаксиса

*Для любого файла документации с расширением `.md` в директории `docs/ru/`, система должна проверить синтаксис Markdown и отклонить сборку, если обнаружены синтаксические ошибки.*

**Validates: Requirements 4.2, 7.3**

### Property 5: Консистентность ссылок

*Для любой внутренней ссылки (вида `[текст](путь/к/файлу.md)`) в документации, если целевой файл существует в структуре `docs/ru/`, ссылка должна быть валидна; если файла не существует, система должна сгенерировать отчёт об ошибке.*

**Validates: Requirements 7.2**

### Property 6: Обязательные разделы наличие

*Для любого файла документации с типом "руководство" или "API", система должна проверить наличие всех обязательных разделов (название, описание, примеры) и сгенерировать отчёт о пропущенных разделах.*

**Validates: Requirements 7.1**

### Property 7: Языковая консистентность

*Для всех элементов навигации, заголовков, комментариев конфигураций и сообщений системы, контент должен быть на русском языке (кроме кода и идентификаторов).*

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 8: Версионирование с тегами

*Для любого Git-тега (например `v1.0.0`) в репозитории, если система выполняет сборку документации для этого тега, Read the Docs должна создать версию документации с уникальным URL, содержащим номер версии.*

**Validates: Requirements 5.3, 5.4**

### Property 9: Локальная перестройка инкрементальность

*Для любого файла документации, если он изменяется в локальной разработке с активным watch-процессом, система должна перестроить только изменённый раздел (плюс зависимости) и отразить изменения в браузере в течение 5 секунд.*

**Validates: Requirements 8.3**

### Property 10: CI/CD pipeline последовательность

*Для любого push-события в главный репозиторий, система должна выполнить задачи валидации и генерации в правильном порядке: валидация → генерация API → сборка → артефакты; если любой этап не пройдёт, последующие этапы должны быть пропущены и отправлено уведомление.*

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

## 9. План реализации

### Фаза 1: Инфраструктура (Неделя 1-2)
- [ ] Создание структуры `docs/ru/`
- [ ] Настройка Sphinx и конфигурации
- [ ] Инициализация GitHub Actions workflow

### Фаза 2: Валидация (Неделя 2-3)
- [ ] Реализация скриптов валидации
- [ ] Интеграция проверок в CI/CD
- [ ] Создание отчётов об ошибках

### Фаза 3: API-генерация (Неделя 3-4)
- [ ] Разработка генератора API-документации
- [ ] Интеграция с Sphinx
- [ ] Тестирование на реальных модулях

### Фаза 4: Публикация (Неделя 4-5)
- [ ] Настройка Read the Docs
- [ ] Конфигурация вебхуков
- [ ] Тестирование полного цикла

### Фаза 5: Локальная разработка (Неделя 5-6)
- [ ] Создание скриптов сборки
- [ ] Реализация live-reload
- [ ] Документация для разработчиков

## 10. Риски и митигация

| Риск | Вероятность | Impact | Митигация |
|------|-------------|--------|-----------|
| Непредвиденные изменения в docstrings | Средняя | Средний | Версионирование, backup strategy |
| Read the Docs недоступен | Низкая | Высокий | Fallback хостинг, локальная сборка |
| Производительность сборки | Средняя | Средний | Кэширование, параллельная обработка |
| Конфликты версий зависимостей | Средняя | Средний | Lock-файлы, тестирование в CI |

