import pytest
import os
from scripts.dev.save_file import save_file

class TestSaveFile_HappyPath:
    """Testing normal expected scenarios of save_file operation."""

    def test_save_file_success(self, tmp_path):
        """Test saving file with correct data.
        
        Check: file is created and content written correctly.
        """
        test_dir = tmp_path / 'test_subdir'
        test_file = test_dir / 'test.txt'
        content = 'Hello, world!'
        result = save_file(str(test_file), content)
        assert result is True, 'save_file should return True for correct input'
        assert test_file.exists(), 'File should be created'
        assert test_file.read_text(encoding='utf-8') == content, 'File content does not match'

class TestSaveFile_EdgeCases:
    """Testing boundary values and empty data."""

    def test_save_file_empty_content(self, tmp_path):
        """Test saving empty content.
        
        Check: empty string is written to file without errors.
        """
        test_file = tmp_path / 'empty.txt'
        content = ''
        result = save_file(str(test_file), content)
        assert result is True, 'Should return True for empty content'
        assert test_file.exists(), 'File should be created'
        assert test_file.read_text(encoding='utf-8') == '', 'File content should be empty'

class TestSaveFile_ErrorScenarios:
    """Testing error scenario handling."""

    def test_save_file_invalid_path(self):
        """Test saving to inaccessible path.
        
        Check: on write error function should return False.
        """
        invalid_path = 'Z:/invalid_directory/file.txt'