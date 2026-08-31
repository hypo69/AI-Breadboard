# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Project root finding and header module testing
# =============================================================================
# Description:
#   Comprehensive testing of all public functions in the header module for locating project root.
#
# File: test_header.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from pathlib import Path
from core.utils.header import set_project_root

def test_set_project_root_success():
    """Test successful finding of project root.
    
    Check: function should find directory with '__root__' marker.
    """
    # --- Setup (Arrange) ---
    expected_root = Path(__file__).resolve().parents[2]
    
    # --- Execution (Act) ---
    root = set_project_root()
    
    # --- Check (Assert) ---
    assert root == expected_root, f"Project root not found, expected {expected_root}, got {root}"

def test_set_project_root_nonexistent_marker():
    """Test finding root when markers do not exist."""
    # --- Setup (Arrange) ---
    # Marker that definitely does not exist in the project tree.
    marker = ('nonexistent_file_12345',)
    
    # --- Execution (Act) ---
    root = set_project_root(marker_files=marker)
    
    # --- Check (Assert) ---
    # Function behavior: if not found, returns script directory.
    assert isinstance(root, Path), "Result should be a Path object"
