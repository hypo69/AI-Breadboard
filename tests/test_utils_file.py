# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing class for file.py module functions
# =============================================================================
# Description:
#   Comprehensive testing of file handling functions in file.py module.
#
# File: test_utils_file.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import os
from pathlib import Path
from core.utils.file import save_text_file, read_text_file, get_filenames, remove_bom

class TestFileUtils:
    """Class for testing file.py module functions."""

    def test_save_and_read_text_file_happy_path(self, tmp_path):
        """Test normal scenario for writing and reading text.
        
        Check: data written to file is correctly read back.
        """
        # --- Setup (Arrange) ---
        # Temporary folder tmp_path (pytest fixture).
        test_file: Path = tmp_path / "test.txt"
        content: str = "Test string"
        
        # --- Execution (Act) ---
        # Write text.
        save_result: bool = save_text_file(content, test_file)
        # Read text.
        read_result: str | None = read_text_file(test_file)
        
        # --- Check (Assert) ---
        assert save_result is True, "save_text_file() should return True"
        assert read_result == content, f"Expected {content!r}, got {read_result!r}"

    def test_save_and_read_dict_happy_path(self, tmp_path):
        """Test writing and reading dictionary in JSON format."""
        # --- Setup (Arrange) ---
        test_file: Path = tmp_path / "test.json"
        data: dict = {"key": "value"}
        
        # --- Execution (Act) ---
        save_result: bool = save_text_file(data, test_file)
        # When reading JSON file via read_text_file we get JSON string.
        read_result_str: str | None = read_text_file(test_file)
        
        # --- Check (Assert) ---
        assert save_result is True
        # Check that file contains valid JSON structure.
        import json
        assert json.loads(read_result_str) == data
        
    def test_remove_bom(self, tmp_path):
        """Test function for BOM cleanup."""
        # --- Setup (Arrange) ---
        test_file: Path = tmp_path / "bom.txt"
        # Create file with BOM (UTF-8 signature).
        content_with_bom: str = "\ufeffText with BOM"
        test_file.write_text(content_with_bom, encoding="utf-8")
        
        # --- Execution (Act) ---
        remove_bom(test_file)
        
        # --- Check (Assert) ---
        content_without_bom = test_file.read_text(encoding="utf-8")
        assert "\ufeff" not in content_without_bom
        assert content_without_bom == "Text with BOM"
