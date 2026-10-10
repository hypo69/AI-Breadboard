# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Logger - Header
# =============================================================================
# Description:
#   Module for project root path determination and meta information initialization.
#
# Usage Examples:
#   Python API:
#     import logger.header as header
#
# File: header.py
# Project: ai-breadboard
# Package: logger
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:29:02
# =============================================================================

"""Module for project root path determination and meta information initialization.

Solves two primary tasks:
1. Determines project root directory by searching for marker files
2. Loads and initializes project meta information from configuration files"""

import sys
import json
import logging
from packaging.version import Version
try:
    from pathlib import Path
    _proj_root = Path(__file__).resolve().parents[1]
    if str(_proj_root) not in sys.path:
        sys.path.insert(0, str(_proj_root))
    import header as _root_header
    __root__ = getattr(_root_header, "__root__", _proj_root)
    set_project_root = getattr(_root_header, "set_project_root", lambda *args, **kwargs: _proj_root)
except Exception:
    __root__ = Path(__file__).resolve().parents[1]
    def set_project_root(*args, **kwargs):
        return __root__

def _load_project_settings() -> Dict[str, str]:
    """
    Loads метаинформацию проекта из файла конфигурации.
    
    Поиск конфигурации:
    1. Сначала пытается найти settings.json в core/
    2. Если не найден, Returns empty dictionary
    
    Returns:
        Dict: Dictionary с параметрами проекта или empty dictionary при ошибке.
    """
    settings: Dict[str, str] = {}
    try:
        from src import gs
        if gs:
            settings_path = gs.path.root / 'core' / 'settings.json'
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as settings_file:
                    settings = json.load(settings_file)
    except (ImportError, FileNotFoundError, json.JSONDecodeError, AttributeError) as ex:
        logging.debug(f'Не удалось загрузить settings.json: {ex}')
    return settings

def _load_project_documentation() -> str:
    """
    Loads документацию проекта из README файла.
    
    Returns:
        str: Содержимое документации или пустая string при ошибке.
    """
    doc_str: str = ''
    try:
        from src import gs
        if gs:
            readme_path = gs.path.root / 'core' / 'README.MD'
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as readme_file:
                    doc_str = readme_file.read()
    except (ImportError, FileNotFoundError, AttributeError) as ex:
        logging.debug(f'Не удалось загрузить документацию: {ex}')
    return doc_str
settings: Dict[str, str] = _load_project_settings()
doc_str: str = _load_project_documentation()
__project_name__: str = settings.get('project_name', 'ai-breadboard') if settings else 'ai-breadboard'
'Название проекта'
__version__: str = settings.get('version', '1.0.0') if settings else '1.0.0'
'Версия проекта'
__doc__: str = doc_str if doc_str else 'AI Breadboard - Интеллектуальная система анализа'
'Документация проекта'
__author__: str = settings.get('author', 'Development Team') if settings else 'Development Team'
'Автор проекта'
__copyright__: str = settings.get('copyright', '© 2026 Development Team') if settings else '© 2026 Development Team'
'Копирайт проекта'
__cofee__: str = settings.get('cofee', 'Treat the developer to a cup of coffee for boosting enthusiasm in development: https://boosty.to/hypo69') if settings else 'Treat the developer to a cup of coffee for boosting enthusiasm in development: https://boosty.to/hypo69'
'Сообщение благодарности для разработчика'