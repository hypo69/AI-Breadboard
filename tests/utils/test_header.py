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