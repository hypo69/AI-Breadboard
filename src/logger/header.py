# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Project root path determination and meta information initialization
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: header.py
# Project: ai-breadboard
# Package: src.logger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Module for project root path determination and meta information initialization.

Solves two primary tasks:
1. Determines project root directory by searching for marker files
2. Loads and initializes project meta information from configuration files"""

import sys
import json
import logging
from packaging.version import Version
from pathlib import Path
from typing import Dict, Optional, Tuple

def set_project_root(marker_files: Tuple[str, ...] = ('__root__', '.git')) -> Path:
    """
    Определяет корневую директорию проекта, поднимаясь вверх по иерархии папок.
    
    Алгоритм:
    1. Начинает с директории, где расположен этот файл
    2. Поднимается вверх по папкам в поиске маркерных файлов/папок
    3. Первая найденная маркер-папка считается корнем проекта
    4. Добавляет корень в sys.path для импортов
    
    Args:
        marker_files: Tuple имён маркерных файлов/папок для идентификации корня.
                     По умолчанию ищет '__root__' или '.git'.
    
    Returns:
        Path: Путь к корневой директории проекта.
              Если не найдена, Returns директорию скрипта.
    
    Example:
        >>> root = set_project_root()
        >>> print(root)
        /path/to/project
    """
    __root__: Path
    current_path: Path = Path(__file__).resolve().parent
    __root__ = current_path
    
    # Поиск маркера в текущей папке и всех родительских папках
    for parent in [current_path] + list(current_path.parents):
        if any((parent / marker).exists() for marker in marker_files):
            __root__ = parent
            break
    
    # Добавление корня в sys.path для импортов
    if __root__ not in sys.path:
        sys.path.insert(0, str(__root__))
    
    return __root__

# Получение корневой директории проекта
__root__: Path = set_project_root()
"""__root__ (Path): Путь к корневой директории проекта"""

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
        logging.debug(f"Не удалось загрузить settings.json: {ex}")
    
    return settings

def _load_project_documentation() -> str:
    """
    Loads документацию проекта из README файла.
    
    Returns:
        str: Содержимое документации или пустая string при ошибке.
    """
    doc_str: str = ""
    try:
        from src import gs
        if gs:
            readme_path = gs.path.root / 'core' / 'README.MD'
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as readme_file:
                    doc_str = readme_file.read()
    except (ImportError, FileNotFoundError, AttributeError) as ex:
        logging.debug(f"Не удалось загрузить документацию: {ex}")
    
    return doc_str

# Loading метаинформации проекта
settings: Dict[str, str] = _load_project_settings()
doc_str: str = _load_project_documentation()

# МетаInfo о проекте (используется при импорте модуля)
__project_name__: str = settings.get("project_name", 'ai-breadboard') if settings else 'ai-breadboard'
"""Название проекта"""

__version__: str = settings.get("version", '1.0.0') if settings else '1.0.0'
"""Версия проекта"""

__doc__: str = doc_str if doc_str else 'AI Breadboard - Интеллектуальная система анализа'
"""Документация проекта"""

__author__: str = settings.get("author", 'Development Team') if settings else 'Development Team'
"""Автор проекта"""

__copyright__: str = settings.get("copyright", '© 2026 Development Team') if settings else '© 2026 Development Team'
"""Копирайт проекта"""

__cofee__: str = settings.get("cofee", "Treat the developer to a cup of coffee for boosting enthusiasm in development: https://boosty.to/hypo69") if settings else "Treat the developer to a cup of coffee for boosting enthusiasm in development: https://boosty.to/hypo69"
"""Сообщение благодарности для разработчика"""

