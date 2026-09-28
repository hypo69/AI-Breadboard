import pytest
from types import SimpleNamespace
from src.utils.convertors.dict import dict2ns, replace_key_in_dict

class TestDictUtils:
    """Class for testing dict.py module functions."""

    def test_dict2ns_happy_path(self):
        """Test normal scenario for converting dict to SimpleNamespace."""
        data: dict = {'a': 1, 'b': {'c': 2}}
        result = dict2ns(data)
        assert isinstance(result, SimpleNamespace)
        assert result.a == 1
        assert result.b.c == 2

    def test_replace_key_in_dict_happy_path(self):
        """Test normal scenario for key replacement."""
        data: dict = {'old': 1, 'nested': {'old': 2}}
        result = replace_key_in_dict(data, 'old', 'new')
        assert result == {'new': 1, 'nested': {'new': 2}}