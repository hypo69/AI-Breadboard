# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing class for dict.py module functions
# =============================================================================
# Description:
#   Comprehensive testing of dict.py module functions for dictionary conversion.
#
# File: test_utils_convertors_dict.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from types import SimpleNamespace
from src.utils.convertors.dict import dict2ns, replace_key_in_dict

class TestDictUtils:
    """Class for testing dict.py module functions."""

    def test_dict2ns_happy_path(self):
        """Test normal scenario for converting dict to SimpleNamespace."""
        # --- Setup (Arrange) ---
        data: dict = {"a": 1, "b": {"c": 2}}
        
        # --- Execution (Act) ---
        result = dict2ns(data)
        
        # --- Check (Assert) ---
        assert isinstance(result, SimpleNamespace)
        assert result.a == 1
        assert result.b.c == 2

    def test_replace_key_in_dict_happy_path(self):
        """Test normal scenario for key replacement."""
        # --- Setup (Arrange) ---
        data: dict = {"old": 1, "nested": {"old": 2}}
        
        # --- Execution (Act) ---
        result = replace_key_in_dict(data, "old", "new")
        
        # --- Check (Assert) ---
        assert result == {"new": 1, "nested": {"new": 2}}
