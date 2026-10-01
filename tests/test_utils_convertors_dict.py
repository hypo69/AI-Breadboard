# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Utils Convertors Dict
# =============================================================================
# Description:
#   Class for testing dict.py module functions.
#
# Usage Examples:
#   Python API:
#     from tests.test_utils_convertors_dict import TestDictUtils
#
#     service = TestDictUtils()
#
# File: test_utils_convertors_dict.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Class for testing dict.py module functions."""

import pytest
from types import SimpleNamespace
from src.utils.convertors.dict import dict2ns, replace_key_in_dict

class TestDictUtils:
    """Class for testing dict.py module functions."""

    def test_dict2ns_happy_path(self):
        """Test normal scenario for converting dict to SimpleNamespace."""
        data: dict = {'a': 1, 'b': {'c': 2}}
        result = dict2ns(data)
        assert isinstance(result, SimpleNamespace)
        assert result.a == 1
        assert result.b.c == 2

    def test_replace_key_in_dict_happy_path(self):
        """Test normal scenario for key replacement."""
        data: dict = {'old': 1, 'nested': {'old': 2}}
        result = replace_key_in_dict(data, 'old', 'new')
        assert result == {'new': 1, 'nested': {'new': 2}}