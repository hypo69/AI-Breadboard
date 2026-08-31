# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: JSON and CSV file handling utilities testing
# =============================================================================
# Description:
#   Testing functions for loading and saving JSON data with various formats and scenarios.
#
# File: test_jjson.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import json
from pathlib import Path
from core.utils.jjson import j_loads, j_dumps
from types import SimpleNamespace

# --- Tests for j_dumps ---

def test_j_dumps_happy_path(tmp_path):
    """Test saving JSON to file (successful scenario)."""
    # Arrange: test data
    data = {"key": "value"}
    file_path = tmp_path / "test.json"
    
    # Act: save
    result = j_dumps(data, file_path=file_path)
    
    # Assert
    assert result == data, "j_dumps should return original data"
    assert file_path.exists(), "File should be created"
    assert json.loads(file_path.read_text(encoding="utf-8")) == data, "File content does not match"

# --- Tests for j_loads ---

def test_j_loads_str_happy_path():
    """Test loading JSON from string (successful scenario)."""
    # Arrange
    json_str = '{"key": "value"}'
    
    # Act
    result = j_loads(json_str)
    
    # Assert
    assert result == {"key": "value"}, "Loaded data does not match"

def test_j_loads_file_happy_path(tmp_path):
    """Test loading JSON from file (successful scenario)."""
    # Arrange
    file_path = tmp_path / "data.json"
    data = {"key": "value"}
    file_path.write_text(json.dumps(data), encoding="utf-8")
    
    # Act
    result = j_loads(file_path)
    
    # Assert
    assert result == data, "Loaded file data does not match"
