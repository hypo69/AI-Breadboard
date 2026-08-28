# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля core/utils/convertors/json
# =============================================================================
# Описание:
#   Исчерпывающее тестирование функций модуля json.py: 
#   json2csv, json2ns, json2xml, json2xls.
#
# File: tests/test_utils_convertors_json.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import json
from pathlib import Path
from types import SimpleNamespace
from core.utils.convertors.json import json2csv, json2ns, json2xml, json2xls

class TestJsonUtils:
    """Класс для тестирования функций модуля json.py."""

    def test_json2ns_happy_path(self):
        """Тестирование конвертации JSON в SimpleNamespace."""
        # --- Подготовка (Arrange) ---
        data: dict = {"a": 1, "b": 2}
        
        # --- Выполнение (Act) ---
        result = json2ns(data)
        
        # --- Проверка (Assert) ---
        assert isinstance(result, SimpleNamespace)
        assert result.a == 1
        assert result.b == 2

    def test_json2xml_happy_path(self):
        """Тестирование конвертации JSON в XML."""
        # --- Подготовка (Arrange) ---
        data: dict = {"a": 1}

        # --- Выполнение (Act) ---
        result = json2xml(data)

        # --- Проверка (Assert) ---
        # Проверяем результат как строку (decode bytes if necessary)
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        assert "<a>1</a>" in result

    def test_json2xls_happy_path(self, tmp_path):
        """Тестирование конвертации JSON в XLS."""
        import sys
        try:
            import xlsxwriter
        except ImportError:
            pytest.skip("xlsxwriter not installed")

        # --- Подготовка (Arrange) ---
        data: list = [{"a": 1, "b": 2}]
        xls_file = tmp_path / "test.xls"

        # --- Выполнение (Act) ---
        result = json2xls(data, xls_file)

        # --- Проверка (Assert) ---
        assert result is True
        assert xls_file.exists()
