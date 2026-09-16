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

# ============================================================================
# Основные параметры проекта
# ============================================================================

project = 'AI-Breadboard'
copyright = f'{datetime.now().year}, AI-Breadboard Contributors'
author = 'AI-Breadboard Team'
version = '1.0'
release = '1.0.0'

# ============================================================================
# Параметры локализации
# ============================================================================

language = 'ru'
locale_paths = ['locale']

# ============================================================================
# Расширения Sphinx
# ============================================================================

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

# ============================================================================
# Конфигурация источников
# ============================================================================

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Главный файл
master_doc = 'index'

# ============================================================================
# Пути и исключения
# ============================================================================

# Шаблоны и статика
templates_path = ['_templates']
html_static_path = ['_static']

# Исключения
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    '*.egg-info',
    '.git',
    'node_modules',
]

# ============================================================================
# Параметры HTML-вывода
# ============================================================================

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

# ============================================================================
# Параметры LaTeX (для PDF)
# ============================================================================

latex_elements = {
    'papersize': 'a4',
    'pointsize': '11pt',
    'preamble': r'''
\usepackage[utf8]{inputenc}
\usepackage[russian]{babel}
''',
    'fontenc': '',
    'inputenc': '',
}

latex_documents = [
    ('index', 'ai-breadboard-ru.tex', 'Документация AI-Breadboard', 
     'AI-Breadboard Team', 'manual'),
]

# ============================================================================
# Параметры autodoc (автоматическая генерация из docstrings)
# ============================================================================

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': False,
    'show-inheritance': True,
    'typehints': 'description',
}

# Включить автосуммаризацию
autosummary_generate = True

# ============================================================================
# Параметры intersphinx (перекрёстные ссылки)
# ============================================================================

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master', None),
}

# ============================================================================
# Параметры MyST (поддержка Markdown)
# ============================================================================

myst_enable_extensions = [
    'colon_fence',
    'dollarmath',
    'linkify',
    'substitution',
    'tasklist',
]

# Использовать порядковые номера для заголовков
numfig = True
numfig_format = {
    'figure': 'Рис. %s',
    'table': 'Таблица %s',
    'code-block': 'Листинг %s',
    'section': 'Раздел %s',
}

# ============================================================================
# Параметры napoleon (поддержка Google-style docstrings)
# ============================================================================

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None

# ============================================================================
# Параметры sphinx_design
# ============================================================================

# Параметры дизайна компонентов (определяются темой)

# ============================================================================
# Параметры sphinx_copybutton
# ============================================================================

# Кнопка копирования кода включена по умолчанию

# ============================================================================
# Обработка и инициализация
# ============================================================================

def setup(app):
    """
    Инициализация расширений Sphinx и подключение обработчиков событий.
    
    Args:
        app: Объект приложения Sphinx
    """
    app.add_config_value('suppress_warnings', [], '')
    app.connect('config-inited', process_docs)


def process_docs(app, config):
    """
    Пост-обработка конфигурации Sphinx.
    
    Args:
        app: Объект приложения Sphinx
        config: Конфигурация Sphinx
    """
    # Здесь могут быть добавлены дополнительные обработчики
    pass


# ============================================================================
# Дополнительные параметры
# ============================================================================

# Включить показ исходного кода
viewcode_line_numbers = True

# Префикс для перекрестных ссылок
html_search_language = 'ru'

# Включить полнотекстовый поиск
html_search_options = {
    'type': 'default'
}

# Параметры для генерации HTML
html_add_permalinks = '¶'
html_last_updated_fmt = '%Y-%m-%d'

# Включить нумерацию разделов
html_use_index = True
html_use_modindex = True

# Параметры для параллельной сборки
parallel_read_safe = True
parallel_write_safe = True

# ============================================================================
# Конец конфигурации Sphinx
# ============================================================================
