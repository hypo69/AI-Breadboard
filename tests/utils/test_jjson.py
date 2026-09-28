import pytest
import json
from pathlib import Path
from src.utils.jjson import j_loads, j_dumps
from types import SimpleNamespace

def test_j_dumps_happy_path(tmp_path):
    """Test saving JSON to file (successful scenario)."""
    data = {'key': 'value'}
    file_path = tmp_path / 'test.json'
    result = j_dumps(data, file_path=file_path)
    assert result == data, 'j_dumps should return original data'
    assert file_path.exists(), 'File should be created'
    assert json.loads(file_path.read_text(encoding='utf-8')) == data, 'File content does not match'

def test_j_loads_str_happy_path():
    """Test loading JSON from string (successful scenario)."""
    json_str = '{"key": "value"}'
    result = j_loads(json_str)
    assert result == {'key': 'value'}, 'Loaded data does not match'

def test_j_loads_file_happy_path(tmp_path):
    """Test loading JSON from file (successful scenario)."""
    file_path = tmp_path / 'data.json'
    data = {'key': 'value'}
    file_path.write_text(json.dumps(data), encoding='utf-8')
    result = j_loads(file_path)
    assert result == data, 'Loaded file data does not match'