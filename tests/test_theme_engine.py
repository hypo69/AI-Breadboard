# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests - Theme Engine & Contrast Themes
# =============================================================================
# Description:
#   Модульные тесты для проверки шаблонизатора тем ThemeEngine, высокой контрастности
#   тёмной темы, а также светлой «Кирпичной» (Brick) и тёмной «Терминал» (Terminal) тем.
#
# Usage Examples:
#   pytest tests/test_theme_engine.py -v
#
# File: test_theme_engine.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 12:12:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для проверки шаблонизатора тем и контрастности интерфейса."""

import json
from pathlib import Path
import re
import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_WEBGUI_DIR = _PROJECT_ROOT / 'apps' / 'windows' / 'api' / 'webgui'


def test_theme_engine_js_exists_and_valid() -> None:
    """Проверяет наличие и структуру модуля шаблонизатора theme-engine.js."""
    engine_file = _WEBGUI_DIR / 'js' / 'theme-engine.js'
    assert engine_file.is_file(), f'Файл {engine_file} должен существовать'

    content = engine_file.read_text(encoding='utf-8')
    assert 'class ThemeEngine' in content, 'ThemeEngine класс должен быть объявлен'
    assert 'registerTheme(' in content, 'Метод registerTheme должен присутствовать'
    assert 'renderOptionsHTML(' in content, 'Метод renderOptionsHTML должен присутствовать'
    assert 'applyTheme(' in content, 'Метод applyTheme должен присутствовать'
    assert 'brick' in content, 'Тема brick должна быть зарегистрирована'
    assert 'terminal' in content, 'Тема terminal должна быть зарегистрирована'
    assert 'dark' in content, 'Тема dark должна быть зарегистрирована'
    assert 'light' in content, 'Тема light должна быть зарегистрирована'
    assert 'system' in content, 'Системный режим должен присутствовать'


def test_theme_js_facade() -> None:
    """Проверяет фасад theme.js на экспорт функций обратной совместимости."""
    theme_js = _WEBGUI_DIR / 'js' / 'theme.js'
    assert theme_js.is_file(), f'Файл {theme_js} должен существовать'

    content = theme_js.read_text(encoding='utf-8')
    assert 'getThemeMode' in content
    assert 'getResolvedTheme' in content
    assert 'setTheme' in content
    assert 'initTheme' in content
    assert 'themeEngine' in content


def test_variables_css_has_all_themes_and_high_contrast() -> None:
    """Проверяет наличие токенов для dark (контрастной), brick, terminal в variables.css."""
    variables_css = _WEBGUI_DIR / 'css' / 'variables.css'
    assert variables_css.is_file(), f'Файл {variables_css} должен существовать'

    content = variables_css.read_text(encoding='utf-8')

    # Проверка селекторов тем
    assert '[data-theme="light"]' in content
    assert '[data-theme="brick"]' in content
    assert '[data-theme="dark"]' in content
    assert '[data-theme="terminal"]' in content

    # Проверка высокой контрастности темной темы
    assert '#f3f6fa' in content, 'Яркий контрастный текст должен присутствовать в темной теме'
    assert '#0b0f17' in content, 'Глубокий контрастный фон страницы должен присутствовать в темной теме'
    assert '#3b4758' in content, 'Четкие границы должны присутствовать в темной теме'

    # Проверка кирпичной темы
    assert '#b84228' in content, 'Кирпично-терракотовый акцент должен присутствовать'
    assert '#f7f3ee' in content, 'Светлый клинкерный фон должен присутствовать'

    # Проверка темы терминал
    assert '#00ff66' in content or '#39ff14' in content, 'Зеленый терминальный фосфор должен присутствовать'
    assert '#060a06' in content, 'CRT смоляной черный фон должен присутствовать'


def test_locales_theme_keys() -> None:
    """Проверяет наличие переводов для всех тем в файлах локализации ru, en, he."""
    locales_dir = _WEBGUI_DIR / 'locales'

    for lang in ['ru', 'en', 'he']:
        file_path = locales_dir / f'{lang}.json'
        assert file_path.is_file(), f'Файл локали {file_path} должен существовать'

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'theme' in data, f'Секция theme должна присутствовать в {lang}.json'
        assert 'brick' in data['theme']
        assert 'terminal' in data['theme']

        assert 'userSettings' in data, f'Секция userSettings должна присутствовать в {lang}.json'
        assert 'themeBrick' in data['userSettings']
        assert 'themeTerminal' in data['userSettings']


def test_index_html_files_updated() -> None:
    """Проверяет, что файлы index.html и apps/index.html содержат обновленные опции и ассеты."""
    apps_index = _WEBGUI_DIR / 'apps' / 'index.html'
    root_index = _WEBGUI_DIR / 'index.html'

    assert apps_index.is_file()
    assert root_index.is_file()

    apps_content = apps_index.read_text(encoding='utf-8')
    assert 'value="brick"' in apps_content, 'Опция brick должна присутствовать в apps/index.html'
    assert 'value="terminal"' in apps_content, 'Опция terminal должна присутствовать в apps/index.html'
    assert 'v=20261004_v17' in apps_content, 'Версия ассетов v17 должна быть в apps/index.html'

    root_content = root_index.read_text(encoding='utf-8')
    assert 'value="brick"' in root_content, 'Опция brick должна присутствовать в index.html'
    assert 'value="terminal"' in root_content, 'Опция terminal должна присутствовать в index.html'
