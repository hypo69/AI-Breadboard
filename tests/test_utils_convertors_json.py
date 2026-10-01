# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Utils Convertors Json
# =============================================================================
# Description:
#   Class for testing json.py module functions.
#
# Usage Examples:
#   Python API:
#     from tests.test_utils_convertors_json import TestJsonUtils
#
#     service = TestJsonUtils()
#
# File: test_utils_convertors_json.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Class for testing json.py module functions."""

import pytest
import json
from pathlib import Path
from types import SimpleNamespace
from src.utils.convertors.json import json2csv, json2ns, json2xml, json2xls

class TestJsonUtils:
    """Class for testing json.py module functions."""

    def test_json2ns_happy_path(self):
        """Test conversion from JSON to SimpleNamespace."""
        data: dict = {'a': 1, 'b': 2}
        result = json2ns(data)
        assert isinstance(result, SimpleNamespace)
        assert result.a == 1
        assert result.b == 2

    def test_json2xml_happy_path(self):
        """Test conversion from JSON to XML."""
        data: dict = {'a': 1}
        result = json2xml(data)
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        assert '<a>1</a>' in result

    def test_json2xls_happy_path(self, tmp_path):
        """Test conversion from JSON to XLS."""
        import sys
        try:
            import xlsxwriter
        except ImportError:
            pytest.skip('xlsxwriter not installed')
        data: list = [{'a': 1, 'b': 2}]
        xls_file = tmp_path / 'test.xls'
        result = json2xls(data, xls_file)
        assert result is True
        assert xls_file.exists()