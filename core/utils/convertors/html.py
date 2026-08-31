# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: HTML conversion and parsing utilities
# =============================================================================
# Description:
#   HTML conversion utilities for transforming HTML content to escape sequences,
#   dictionaries, and SimpleNamespace objects. Includes parsing functions for
#   HTML to structured data format conversions.
#
# File: html.py
# Project: ai-breadboard
# Package: core.utils.convertors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
HTML conversion utilities.

Functions:
    - `html2escape`: Convert HTML to escape sequences.
    - `escape2html`: Convert escape sequences to HTML.
    - `html2dict`: Convert HTML to dictionaries.
    - `html2ns`: Convert HTML to SimpleNamespace objects.
"""

import re
import html
from typing import Dict
from pathlib import Path
from core.logger.logger import logger
from types import SimpleNamespace
from html.parser import HTMLParser
try:
    from xhtml2pdf import pisa
except Exception as ex:
    logger.error(ex)
try:
    from weasyprint import HTML
except Exception as ex:
    logger.error(ex)

def html2escape(input_str: str) -> str:
    """
    Convert HTML to escape sequences.

    Args:
        input_str (str): The HTML code.

    Returns:
        str: HTML converted into escape sequences.

    Example:
        >>> html = "<p>Hello, world!</p>"
        >>> result = html2escape(html)
        >>> print(result)
        &lt;p&gt;Hello, world!&lt;/p&gt;
    """
    return html.escape(input_str)

def escape2html(input_str: str) -> str:
    """
    Convert escape sequences to HTML.

    Args:
        input_str (str): The string with escape sequences.

    Returns:
        str: The escape sequences converted back into HTML.

    Example:
        >>> escaped = "&lt;p&gt;Hello, world!&lt;/p&gt;"
        >>> result = escape2html(escaped)
        >>> print(result)
        <p>Hello, world!</p>
    """
    return html.unescape(input_str)

def html2dict(html_str: str) -> Dict[str, str]:
    """
    Convert HTML to a dictionary where tags are keys and content are values.

    Args:
        html_str (str): The HTML string to convert.

    Returns:
        dict: A dictionary with HTML tags as keys and their content as values.

    Example:
        >>> html = "<p>Hello</p><a href='link'>World</a>"
        >>> result = html2dict(html)
        >>> print(result)
        {'p': 'Hello', 'a': 'World'}
    """
    class HTMLToDictParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.result = {}
            self.current_tag = None

        def handle_starttag(self, tag, attrs):
            self.current_tag = tag

        def handle_endtag(self, tag):
            self.current_tag = None

        def handle_data(self, data):
            if self.current_tag:
                self.result[self.current_tag] = data.strip()

    parser = HTMLToDictParser()
    parser.feed(html_str)
    return parser.result

def html2ns(html_str: str) -> SimpleNamespace:
    """
    Convert HTML to a SimpleNamespace object where tags are attributes and content are values.

    Args:
        html_str (str): The HTML string to convert.

    Returns:
        SimpleNamespace: A SimpleNamespace object with HTML tags as attributes and their content as values.

    Example:
        >>> html = "<p>Hello</p><a href='link'>World</a>"
        >>> result = html2ns(html)
        >>> print(result.p)
        Hello
        >>> print(result.a)
        World
    """
    html_dict = html2dict(html_str)
    return SimpleNamespace(**html_dict)

# def html2pdf(html_str: str, pdf_file: str | Path) -> bool | None:
#     """Converts HTML content to a PDF file after removing unsupported CSS pseudo-selectors.
    
#     Args:
#         html_str (str): HTML content as a string.
#         pdf_file (str | Path): Path to the output PDF file.
    
#     Returns:
#         bool | None: Returns `True` if PDF generation is successful; `None` otherwise.
#     """
#     ...
#     def preprocess_css(css_content: str) -> str:
#         """
#         Remove unsupported pseudo-classes and simplify CSS for xhtml2pdf.
    
#         Args:
#             css_content (str): Original CSS content.

#         Returns:
#             str: Preprocessed CSS content without unsupported selectors.
#         """
#         # Remove `:not(...)`
#         css_content = re.sub(r':not\([^)]*\)', '', css_content)

#         return css_content
#     # Remove unsupported pseudo-classes if present
#     html_str = preprocess_css(html_str)

#     with open(pdf_file, "wb") as f:
#         pisa_status = pisa.CreatePDF(html_str, dest=f)

#     if pisa_status.err:
#         print("Error during PDF generation")
#         return
#     else:
#         return True

def html2pdf(html_str: str, pdf_file: str | Path) -> bool | None:
    """Converts HTML content to a PDF file using WeasyPrint."""
    try:
        HTML(string=html_str).write_pdf(pdf_file)
        return True
    except Exception as e:
        print(f"Error during PDF generation: {e}")
        return

