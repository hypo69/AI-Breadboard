# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля core/utils/convertors/html
# =============================================================================
# Описание:
#   Исчерпывающее тестирование функций модуля html.py: 
#   html2escape, escape2html, html2dict, html2ns.
#
# File: tests/test_utils_convertors_html.py
# Project: ai-assistant
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from types import SimpleNamespace
from core.utils.convertors.html import html2escape, escape2html, html2dict, html2ns

class TestHtmlUtils:
    """Класс для тестирования функций модуля html.py."""

    def test_html2escape_happy_path(self):
        """Тестирование корректного экранирования HTML-тегов."""
        # --- Подготовка (Arrange) ---
        html: str = "<p>Hello</p>"
        expected: str = "&lt;p&gt;Hello&lt;/p&gt;"
        
        # --- Выполнение (Act) ---
        result: str = html2escape(html)
        
        # --- Проверка (Assert) ---
        assert result == expected, f"Ожидалось {expected!r}, получено {result!r}"

    def test_escape2html_happy_path(self):
        """Тестирование корректного преобразования эскейп-последовательностей в HTML."""
        # --- Подготовка (Arrange) ---
        escaped: str = "&lt;p&gt;Hello&lt;/p&gt;"
        expected: str = "<p>Hello</p>"
        
        # --- Выполнение (Act) ---
        result: str = escape2html(escaped)
        
        # --- Проверка (Assert) ---
        assert result == expected, f"Ожидалось {expected!r}, получено {result!r}"

    def test_html2dict_happy_path(self):
        """Тестирование конвертации HTML в словарь."""
        # --- Подготовка (Arrange) ---
        html: str = "<p>Hello</p><a>World</a>"
        expected: dict = {"p": "Hello", "a": "World"}
        
        # --- Выполнение (Act) ---
        result: dict = html2dict(html)
        
        # --- Проверка (Assert) ---
        assert result == expected, f"Ожидалось {expected!r}, получено {result!r}"

    def test_html2ns_happy_path(self):
        """Тестирование конвертации HTML в SimpleNamespace."""
        # --- Подготовка (Arrange) ---
        html: str = "<p>Hello</p><a>World</a>"
        
        # --- Выполнение (Act) ---
        result = html2ns(html)
        
        # --- Проверка (Assert) ---
        assert isinstance(result, SimpleNamespace)
        assert result.p == "Hello"
        assert result.a == "World"
