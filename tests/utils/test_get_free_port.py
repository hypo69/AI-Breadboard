# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Utils - Test Get Free Port
# =============================================================================
# Description:
#   Test retrieving the first available port (without range).
#
# Usage Examples:
#   Python API:
#     from tests.utils.test_get_free_port import test_get_free_port_first_available
#
#     res = test_get_free_port_first_available()
#
# File: test_get_free_port.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Test retrieving the first available port (without range)."""

import pytest
from src.utils.get_free_port import get_free_port

def test_get_free_port_first_available():
    """Test retrieving the first available port (without range).
    
    Check: function should return integer starting from 1024.
    """
    host: str = 'localhost'
    port: int = get_free_port(host)
    assert port >= 1024, f'Port should be >= 1024, got: {port}'

def test_get_free_port_in_range():
    """Test retrieving port within specified range."""
    host: str = 'localhost'
    port_range: str = '3000-5000'
    port: int = get_free_port(host, port_range)
    assert 3000 <= port <= 5000, f'Port {port} outside range {port_range}'

def test_get_free_port_invalid_range():
    """Test error handling with invalid range."""
    host: str = 'localhost'
    port_range: str = 'invalid'
    with pytest.raises(ValueError):
        get_free_port(host, port_range)