# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Utils Convertors Html
# =============================================================================
# Description:
#   Class for testing html.py module functions.
#
# Usage Examples:
#   Python API:
#     from tests.test_utils_convertors_html import TestHtmlUtils
#
#     service = TestHtmlUtils()
#
# File: test_utils_convertors_html.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Class for testing html.py module functions."""

import pytest
from types import SimpleNamespace
from src.utils.convertors.html import html2escape, escape2html, html2dict, html2ns

class TestHtmlUtils:
    """Class for testing html.py module functions."""

    def test_html2escape_happy_path(self):
        """Test proper HTML tag escaping."""
        html: str = '<p>Hello</p>'
        expected: str = '&lt;p&gt;Hello&lt;/p&gt;'
        result: str = html2escape(html)
        assert result == expected, f'Expected {expected!r}, got {result!r}'

    def test_escape2html_happy_path(self):
        """Test proper conversion of escape sequences to HTML."""
        escaped: str = '&lt;p&gt;Hello&lt;/p&gt;'
        expected: str = '<p>Hello</p>'
        result: str = escape2html(escaped)
        assert result == expected, f'Expected {expected!r}, got {result!r}'

    def test_html2dict_happy_path(self):
        """Test conversion of HTML to dictionary."""
        html: str = '<p>Hello</p><a>World</a>'
        expected: dict = {'p': 'Hello', 'a': 'World'}
        result: dict = html2dict(html)
        assert result == expected, f'Expected {expected!r}, got {result!r}'

    def test_html2ns_happy_path(self):
        """Test conversion of HTML to SimpleNamespace."""
        html: str = '<p>Hello</p><a>World</a>'
        result = html2ns(html)
        assert isinstance(result, SimpleNamespace)
        assert result.p == 'Hello'
        assert result.a == 'World'