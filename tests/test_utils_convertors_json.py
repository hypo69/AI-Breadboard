# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing class for json.py module functions
# =============================================================================
# Description:
#   Comprehensive testing of json.py module functions for data conversion.
#
# File: test_utils_convertors_json.py
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
    """Class for testing json.py module functions."""

    def test_json2ns_happy_path(self):
        """Test conversion from JSON to SimpleNamespace."""
        # --- Setup (Arrange) ---
        data: dict = {"a": 1, "b": 2}
        
        # --- Execution (Act) ---
        result = json2ns(data)
        
        # --- Check (Assert) ---
        assert isinstance(result, SimpleNamespace)
        assert result.a == 1
        assert result.b == 2

    def test_json2xml_happy_path(self):
        """Test conversion from JSON to XML."""
        # --- Setup (Arrange) ---
        data: dict = {"a": 1}

        # --- Execution (Act) ---
        result = json2xml(data)

        # --- Check (Assert) ---
        # Check result as string (decode bytes if necessary)
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        assert "<a>1</a>" in result

    def test_json2xls_happy_path(self, tmp_path):
        """Test conversion from JSON to XLS."""
        import sys
        try:
            import xlsxwriter
        except ImportError:
            pytest.skip("xlsxwriter not installed")

        # --- Setup (Arrange) ---
        data: list = [{"a": 1, "b": 2}]
        xls_file = tmp_path / "test.xls"

        # --- Execution (Act) ---
        result = json2xls(data, xls_file)

        # --- Check (Assert) ---
        assert result is True
        assert xls_file.exists()
