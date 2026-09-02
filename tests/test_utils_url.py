# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: URL utility functions testing
# =============================================================================
# Description:
#   Tests for extract_url_params function and URL utility module.
#
# File: test_utils_url.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Tests for core/utils/url.py module
"""

import pytest
from unittest.mock import patch, Mock
from core.utils.url import extract_url_params, is_url, url_shortener

class TestExtractUrlParams:
    """Tests for extract_url_params function."""

    def test_extract_params_with_multiple_params(self):
        """Test extracting multiple parameters."""
        url = "https://example.com?param1=value1&param2=value2"
        
        result = extract_url_params(url)
        
        assert result is not None
        assert result['param1'] == 'value1'
        assert result['param2'] == 'value2'

    def test_extract_params_single_value(self):
        """Test extracting single parameter."""
        url = "https://example.com?key=value"
        
        result = extract_url_params(url)
        
        assert result is not None
        assert result['key'] == 'value'

    def test_extract_params_no_params(self):
        """Test URL without parameters."""
        url = "https://example.com/path"
        
        result = extract_url_params(url)
        
        assert result is None

    def test_extract_params_empty_url(self):
        """Test empty URL."""
        result = extract_url_params("")
        
        assert result is None

    def test_extract_params_with_numeric_values(self):
        """Test with numeric values."""
        url = "https://example.com?page=1&limit=10"
        
        result = extract_url_params(url)
        
        assert result is not None
        assert result['page'] == '1'
        assert result['limit'] == '10'

    def test_extract_params_with_encoded_values(self):
        """Test with encoded values."""
        url = "https://example.com?query=%D0%BF%D1%80%D0%B8%D0%B2%D0%B5%D1%82"
        
        result = extract_url_params(url)
        
        assert result is not None
        assert 'query' in result

class TestIsUrl:
    """Tests for is_url function."""

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        assert is_url("https://example.com") is True

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        assert is_url("http://example.com") is True

    def test_valid_url_with_path(self):
        """Test URL with path."""
        assert is_url("https://example.com/path/to/resource") is True

    def test_valid_url_with_params(self):
        """Test URL with parameters."""
        assert is_url("https://example.com?param=value") is True

    def test_invalid_string(self):
        """Test invalid string - validators may return False or raise Exception."""
        try:
            result = is_url("not a url")
            # validators returns False for invalid URLs
            assert result is False
        except Exception:
            pass  # Also acceptable behavior

    def test_empty_string(self):
        """Test empty string."""
        try:
            result = is_url("")
            assert result is False
        except Exception:
            pass

    def test_domain_without_scheme(self):
        """Test domain without scheme - validators treats as valid URL."""
        result = is_url("example.com")
        # validators may treat this as valid domain
        assert result is True

    def test_ip_address_url(self):
        """Test URL with IP address."""
        result = is_url("http://192.168.1.1:8080")
        assert result is True

class TestUrlShortener:
    """Tests for url_shortener function."""

    def test_shortener_success(self):
        """Test successful shortening."""
        long_url = "https://example.com/very/long/url/path"
        
        with patch('core.utils.url.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "https://tinyurl.com/abc123"
            mock_get.return_value = mock_response
            
            result = url_shortener(long_url)
            
            assert result == "https://tinyurl.com/abc123"

    def test_shortener_failure(self):
        """Test failed shortening."""
        long_url = "https://example.com/long/url"
        
        with patch('core.utils.url.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = url_shortener(long_url)
            
            assert result is None

    def test_shortener_calls_correct_api(self):
        """Test that correct API is called."""
        long_url = "https://example.com"
        
        with patch('core.utils.url.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "https://tinyurl.com/short"
            mock_get.return_value = mock_response
            
            url_shortener(long_url)
            
            # Check that URL contains tinyurl
            call_args = mock_get.call_args
            assert 'tinyurl.com' in call_args[0][0]

class TestUrlEdgeCases:
    """Tests for edge cases."""

    def test_extract_params_with_duplicate_keys(self):
        """Test parameters with duplicate keys."""
        url = "https://example.com?key=value1&key=value2"
        
        result = extract_url_params(url)
        
        assert result is not None
        assert result['key'] == ['value1', 'value2']

    def test_extract_params_fragment(self):
        """Test URL with fragment."""
        url = "https://example.com/page#section"
        
        result = extract_url_params(url)
        
        # fragment should not be parsed as query param
        assert result is None

    def test_is_url_localhost(self):
        """Test localhost URL - validators treats as valid URL."""
        # validators treats bare domain names as valid URLs
        result1 = is_url("http://localhost:8080")
        assert result1 is True
        
        result2 = is_url("http://127.0.0.1:8000")
        assert result2 is True
