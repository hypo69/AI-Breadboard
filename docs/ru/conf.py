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
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))
project = 'AI-Breadboard'
copyright = f'{datetime.now().year}, AI-Breadboard Contributors'
author = 'AI-Breadboard Team'
version = '1.0'
release = '1.0.0'
language = 'ru'
locale_paths = ['locale']
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.autosummary', 'sphinx.ext.intersphinx', 'sphinx.ext.viewcode', 'sphinx.ext.napoleon', 'sphinx_autodoc_typehints', 'sphinx_rtd_theme', 'myst_parser', 'sphinx_design', 'sphinx_copybutton']
source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}
master_doc = 'index'
templates_path = ['_templates']
html_static_path = ['_static']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '*.egg-info', '.git', 'node_modules']
html_theme = 'sphinx_rtd_theme'
html_theme_options = {'logo_only': True, 'display_version': True, 'prev_next_buttons_location': 'bottom', 'style_external_links': False, 'collapse_navigation': True, 'sticky_navigation': True, 'navigation_depth': 4, 'includehidden': True, 'titles_only': False, 'github_url': 'https://github.com/breadboard-ai/breadboard', 'language': 'ru'}
html_logo = '_static/images/logo.png'
html_favicon = '_static/images/favicon.ico'
latex_elements = {'papersize': 'a4', 'pointsize': '11pt', 'preamble': '\n\\usepackage[utf8]{inputenc}\n\\usepackage[russian]{babel}\n', 'fontenc': '', 'inputenc': ''}
latex_documents = [('index', 'ai-breadboard-ru.tex', 'Документация AI-Breadboard', 'AI-Breadboard Team', 'manual')]
autodoc_default_options = {'members': True, 'member-order': 'bysource', 'special-members': '__init__', 'undoc-members': False, 'show-inheritance': True, 'typehints': 'description'}
autosummary_generate = True
intersphinx_mapping = {'python': ('https://docs.python.org/3', None), 'sphinx': ('https://www.sphinx-doc.org/en/master', None)}
myst_enable_extensions = ['colon_fence', 'dollarmath', 'linkify', 'substitution', 'tasklist']
numfig = True
numfig_format = {'figure': 'Рис. %s', 'table': 'Таблица %s', 'code-block': 'Листинг %s', 'section': 'Раздел %s'}
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None

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
    pass
viewcode_line_numbers = True
html_search_language = 'ru'
html_search_options = {'type': 'default'}
html_add_permalinks = '¶'
html_last_updated_fmt = '%Y-%m-%d'
html_use_index = True
html_use_modindex = True
parallel_read_safe = True
parallel_write_safe = True