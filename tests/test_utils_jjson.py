# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Class для тестирования функций модуля jjson.
# =============================================================================
# Description:
#   Исчерпывающее тестирование всех публичных функций модуля jjson:
#
# File: test_utils_jjson.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import json
from pathlib import Path
from types import SimpleNamespace
from core.utils.jjson import j_dumps, j_loads, j_loads_ns

class TestJJson:
    """Class для тестирования функций модуля jjson."""

    def test_j_loads_happy_path_str(self):
        """Тестирование загрузки корректной JSON-строки.

        Check: j_loads корректно парсит простую JSON-строку в dictionary.
        """
        # --- Подготовка (Arrange) ---
        # Тестовая JSON-string: стандартный объект с ключом 'a' и значением 1.
        json_str: str = '{"a": 1}'
        
        # --- Выполнение (Act) ---
        # Вызов функции j_loads для парсинга строки.
        result: dict = j_loads(json_str)
        
        # --- Check (Assert) ---
        # Ожидается dictionary {'a': 1}.
        assert result == {'a': 1}, f"j_loads() должна вернуть {'a': 1}, получено: {result!r}"

    def test_j_dumps_happy_path_dict(self):
        """Тестирование дампирования словаря в JSON (в память).

        Check: j_dumps Returns correct dictionary при отсутствии файла.
        """
        # --- Подготовка (Arrange) ---
        # Тестовый dictionary.
        data: dict = {'a': 1, 'b': 2}
        
        # --- Выполнение (Act) ---
        # Дампирование без указания файла (должно вернуть данные).
        result: dict = j_dumps(data)
        
        # --- Check (Assert) ---
        assert result == data, f"j_dumps() должна вернуть {data!r}, получено: {result!r}"
        
    def test_j_loads_empty_str(self):
        """Тестирование граничного случая: пустая string.
        
        Check: пустая string должна возвращать empty dictionary (Error логики парсинга).
        """
        # --- Подготовка (Arrange) ---
        empty_str: str = ""
        
        # --- Выполнение (Act) ---
        # Пустая string приводит к ошибке парсинга внутри string2dict.
        result = j_loads(empty_str)
        
        # --- Check (Assert) ---
        assert result == {}, f"j_loads() должна вернуть empty dictionary для empty строки, получено: {result!r}"

