# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Utils Jjson
# =============================================================================
# Description:
#   Class for testing jjson module functions.
#
# Usage Examples:
#   Python API:
#     from tests.test_utils_jjson import TestJJson
#
#     service = TestJJson()
#
# File: test_utils_jjson.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Class for testing jjson module functions."""

import pytest
import json
from pathlib import Path
from types import SimpleNamespace
from src.utils.jjson import j_dumps, j_loads, j_loads_ns

class TestJJson:
    """Class for testing jjson module functions."""

    def test_j_loads_happy_path_str(self):
        """Test loading correct JSON string.

        Check: j_loads correctly parses simple JSON string to dictionary.
        """
        json_str: str = '{"a": 1}'
        result: dict = j_loads(json_str)
        assert result == {'a': 1}, f"j_loads() should return {{'a': 1}}, got: {result!r}"

    def test_j_dumps_happy_path_dict(self):
        """Test dumping dictionary to JSON (in memory).

        Check: j_dumps returns correct dictionary when file is not specified.
        """
        data: dict = {'a': 1, 'b': 2}
        result: dict = j_dumps(data)
        assert result == data, f'j_dumps() should return {data!r}, got: {result!r}'

    def test_j_loads_empty_str(self):
        """Test edge case: empty string.
        
        Check: empty string should return empty dictionary (error in parsing logic).
        """
        empty_str: str = ''
        result = j_loads(empty_str)
        assert result == {}, f'j_loads() should return empty dictionary for empty string, got: {result!r}'