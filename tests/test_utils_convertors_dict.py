# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Class для тестирования функций модуля dict.py.
# =============================================================================
# Description:
#   Исчерпывающее тестирование функций модуля dict.py:
#
# File: test_utils_convertors_dict.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from types import SimpleNamespace
from core.utils.convertors.dict import dict2ns, replace_key_in_dict

class TestDictUtils:
    """Class для тестирования функций модуля dict.py."""

    def test_dict2ns_happy_path(self):
        """Тестирование нормального сценария конвертации dict в SimpleNamespace."""
        # --- Подготовка (Arrange) ---
        data: dict = {"a": 1, "b": {"c": 2}}
        
        # --- Выполнение (Act) ---
        result = dict2ns(data)
        
        # --- Check (Assert) ---
        assert isinstance(result, SimpleNamespace)
        assert result.a == 1
        assert result.b.c == 2

    def test_replace_key_in_dict_happy_path(self):
        """Тестирование нормального сценария замены ключа."""
        # --- Подготовка (Arrange) ---
        data: dict = {"old": 1, "nested": {"old": 2}}
        
        # --- Выполнение (Act) ---
        result = replace_key_in_dict(data, "old", "new")
        
        # --- Check (Assert) ---
        assert result == {"new": 1, "nested": {"new": 2}}
        
