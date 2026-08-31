# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing for available port retrieval
# =============================================================================
# Description:
#   Comprehensive testing of all public functions in the get_free_port module for finding available ports.
#
# File: test_get_free_port.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from core.utils.get_free_port import get_free_port

def test_get_free_port_first_available():
    """Test retrieving the first available port (without range).
    
    Check: function should return integer starting from 1024.
    """
    # --- Setup (Arrange) ---
    # Localhost host — standard for local testing.
    host: str = 'localhost'
    
    # --- Execution (Act) ---
    # Search for first available port without restrictions.
    port: int = get_free_port(host)
    
    # --- Check (Assert) ---
    # Check: port should be >= 1024.
    assert port >= 1024, f"Port should be >= 1024, got: {port}"

def test_get_free_port_in_range():
    """Test retrieving port within specified range."""
    # --- Setup (Arrange) ---
    host: str = 'localhost'
    port_range: str = '3000-5000'
    
    # --- Execution (Act) ---
    port: int = get_free_port(host, port_range)
    
    # --- Check (Assert) ---
    assert 3000 <= port <= 5000, f"Port {port} outside range {port_range}"

def test_get_free_port_invalid_range():
    """Test error handling with invalid range."""
    # --- Setup (Arrange) ---
    host: str = 'localhost'
    port_range: str = 'invalid'
    
    # --- Execution (Act) & Check (Assert) ---
    with pytest.raises(ValueError):
        get_free_port(host, port_range)
