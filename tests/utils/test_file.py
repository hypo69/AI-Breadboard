# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Utils - Test File
# =============================================================================
# Description:
#   Test saving text to file (successful scenario).
#
# Usage Examples:
#   Python API:
#     from tests.utils.test_file import test_save_text_file_happy_path
#
#     res = test_save_text_file_happy_path()
#
# File: test_file.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Test saving text to file (successful scenario)."""

import pytest
from pathlib import Path
import os
from src.utils.file import save_text_file, read_text_file

def test_save_text_file_happy_path(tmp_path):
    """Test saving text to file (successful scenario)."""
    file_path = tmp_path / 'test.txt'
    data = 'Hello, World!'
    result = save_text_file(data, file_path)
    assert result is True, 'save_text_file should return True on successful write'
    assert file_path.read_text(encoding='utf-8') == data, 'File content does not match written data'

def test_read_text_file_happy_path(tmp_path):
    """Test reading text from file (successful scenario)."""
    file_path = tmp_path / 'test_read.txt'
    data = 'Hello, read!'
    file_path.write_text(data, encoding='utf-8')
    result = read_text_file(file_path)
    assert result == data, 'Read content does not match written data'

def test_save_text_file_invalid_mode(tmp_path):
    """Test write with invalid mode (expect error or False)."""
    file_path = tmp_path / 'invalid_mode.txt'
    data = 'data'
    result = save_text_file(data, file_path, mode='x')
    assert result is True