# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Utils File
# =============================================================================
# Description:
#   Class for testing file.py module functions.
#
# Usage Examples:
#   Python API:
#     from tests.test_utils_file import TestFileUtils
#
#     service = TestFileUtils()
#
# File: test_utils_file.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Class for testing file.py module functions."""

import pytest
import os
from pathlib import Path
from src.utils.file import save_text_file, read_text_file, get_filenames, remove_bom

class TestFileUtils:
    """Class for testing file.py module functions."""

    def test_save_and_read_text_file_happy_path(self, tmp_path):
        """Test normal scenario for writing and reading text.
        
        Check: data written to file is correctly read back.
        """
        test_file: Path = tmp_path / 'test.txt'
        content: str = 'Test string'
        save_result: bool = save_text_file(content, test_file)
        read_result: str | None = read_text_file(test_file)
        assert save_result is True, 'save_text_file() should return True'
        assert read_result == content, f'Expected {content!r}, got {read_result!r}'

    def test_save_and_read_dict_happy_path(self, tmp_path):
        """Test writing and reading dictionary in JSON format."""
        test_file: Path = tmp_path / 'test.json'
        data: dict = {'key': 'value'}
        save_result: bool = save_text_file(data, test_file)
        read_result_str: str | None = read_text_file(test_file)
        assert save_result is True
        import json
        assert json.loads(read_result_str) == data

    def test_remove_bom(self, tmp_path):
        """Test function for BOM cleanup."""
        test_file: Path = tmp_path / 'bom.txt'
        content_with_bom: str = '\ufeffText with BOM'
        test_file.write_text(content_with_bom, encoding='utf-8')
        remove_bom(test_file)
        content_without_bom = test_file.read_text(encoding='utf-8')
        assert '\ufeff' not in content_without_bom
        assert content_without_bom == 'Text with BOM'