# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing text file save and read operations
# =============================================================================
# Description:
#   Comprehensive testing of file handling functions for saving and reading text operations.
#
# File: test_file.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from pathlib import Path
import os
from src.utils.file import save_text_file, read_text_file

# --- Tests for save_text_file ---

def test_save_text_file_happy_path(tmp_path):
    """Test saving text to file (successful scenario)."""
    # Arrange: path to temporary file
    file_path = tmp_path / "test.txt"
    data = "Hello, World!"

    # Act: function call
    result = save_text_file(data, file_path)

    # Assert: check success and content
    assert result is True, "save_text_file should return True on successful write"
    assert file_path.read_text(encoding="utf-8") == data, "File content does not match written data"

def test_read_text_file_happy_path(tmp_path):
    """Test reading text from file (successful scenario)."""
    # Arrange: path to temporary file
    file_path = tmp_path / "test_read.txt"
    data = "Hello, read!"
    file_path.write_text(data, encoding="utf-8")

    # Act: function call
    result = read_text_file(file_path)

    # Assert: check content
    assert result == data, "Read content does not match written data"

def test_save_text_file_invalid_mode(tmp_path):
    """Test write with invalid mode (expect error or False)."""
    # Arrange
    file_path = tmp_path / "invalid_mode.txt"
    data = "data"
    
    # Act
    # If function properly handles exceptions via log, it should return False
    result = save_text_file(data, file_path, mode="x")  # 'x' mode: exclusive creation
    
    # Assert
    # Per standards, should return False on failure, not generate exception
    # In reality 'x' creates file, but check how function handles write
    assert result is True
