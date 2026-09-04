# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing class for jjson module functions
# =============================================================================
# Description:
#   Comprehensive testing of all public functions in jjson module for JSON handling.
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
from src.utils.jjson import j_dumps, j_loads, j_loads_ns

class TestJJson:
    """Class for testing jjson module functions."""

    def test_j_loads_happy_path_str(self):
        """Test loading correct JSON string.

        Check: j_loads correctly parses simple JSON string to dictionary.
        """
        # --- Setup (Arrange) ---
        # Test JSON string: standard object with key 'a' and value 1.
        json_str: str = '{"a": 1}'
        
        # --- Execution (Act) ---
        # Call j_loads function to parse string.
        result: dict = j_loads(json_str)
        
        # --- Check (Assert) ---
        # Expected dictionary {'a': 1}.
        assert result == {'a': 1}, f"j_loads() should return {{'a': 1}}, got: {result!r}"

    def test_j_dumps_happy_path_dict(self):
        """Test dumping dictionary to JSON (in memory).

        Check: j_dumps returns correct dictionary when file is not specified.
        """
        # --- Setup (Arrange) ---
        # Test dictionary.
        data: dict = {'a': 1, 'b': 2}
        
        # --- Execution (Act) ---
        # Dump without specifying file (should return data).
        result: dict = j_dumps(data)
        
        # --- Check (Assert) ---
        assert result == data, f"j_dumps() should return {data!r}, got: {result!r}"
        
    def test_j_loads_empty_str(self):
        """Test edge case: empty string.
        
        Check: empty string should return empty dictionary (error in parsing logic).
        """
        # --- Setup (Arrange) ---
        empty_str: str = ""
        
        # --- Execution (Act) ---
        # Empty string causes parsing error inside string2dict.
        result = j_loads(empty_str)
        
        # --- Check (Assert) ---
        assert result == {}, f"j_loads() should return empty dictionary for empty string, got: {result!r}"
