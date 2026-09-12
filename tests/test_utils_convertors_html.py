# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing class for html.py module functions
# =============================================================================
# Description:
#   Comprehensive testing of html.py module functions for HTML conversion.
#
# File: test_utils_convertors_html.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from types import SimpleNamespace
from src.utils.convertors.html import html2escape, escape2html, html2dict, html2ns

class TestHtmlUtils:
    """Class for testing html.py module functions."""

    def test_html2escape_happy_path(self):
        """Test proper HTML tag escaping."""
        # --- Setup (Arrange) ---
        html: str = "<p>Hello</p>"
        expected: str = "&lt;p&gt;Hello&lt;/p&gt;"
        
        # --- Execution (Act) ---
        result: str = html2escape(html)
        
        # --- Check (Assert) ---
        assert result == expected, f"Expected {expected!r}, got {result!r}"

    def test_escape2html_happy_path(self):
        """Test proper conversion of escape sequences to HTML."""
        # --- Setup (Arrange) ---
        escaped: str = "&lt;p&gt;Hello&lt;/p&gt;"
        expected: str = "<p>Hello</p>"
        
        # --- Execution (Act) ---
        result: str = escape2html(escaped)
        
        # --- Check (Assert) ---
        assert result == expected, f"Expected {expected!r}, got {result!r}"

    def test_html2dict_happy_path(self):
        """Test conversion of HTML to dictionary."""
        # --- Setup (Arrange) ---
        html: str = "<p>Hello</p><a>World</a>"
        expected: dict = {"p": "Hello", "a": "World"}
        
        # --- Execution (Act) ---
        result: dict = html2dict(html)
        
        # --- Check (Assert) ---
        assert result == expected, f"Expected {expected!r}, got {result!r}"

    def test_html2ns_happy_path(self):
        """Test conversion of HTML to SimpleNamespace."""
        # --- Setup (Arrange) ---
        html: str = "<p>Hello</p><a>World</a>"
        
        # --- Execution (Act) ---
        result = html2ns(html)
        
        # --- Check (Assert) ---
        assert isinstance(result, SimpleNamespace)
        assert result.p == "Hello"
        assert result.a == "World"
