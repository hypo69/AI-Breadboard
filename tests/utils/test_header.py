# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Utils - Test Header
# =============================================================================
# Description:
#   Test successful finding of project root.
#
# Usage Examples:
#   Python API:
#     from tests.utils.test_header import test_set_project_root_success
#
#     res = test_set_project_root_success()
#
# File: test_header.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Test successful finding of project root."""

import pytest
from pathlib import Path
from src.utils.header import set_project_root

def test_set_project_root_success():
    """Test successful finding of project root.
    
    Check: function should find directory with '__root__' marker.
    """
    expected_root = Path(__file__).resolve().parents[2]
    root = set_project_root()
    assert root == expected_root, f'Project root not found, expected {expected_root}, got {root}'

def test_set_project_root_nonexistent_marker():
    """Test finding root when markers do not exist."""
    marker = ('nonexistent_file_12345',)
    root = set_project_root(marker_files=marker)
    assert isinstance(root, Path), 'Result should be a Path object'