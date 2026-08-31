# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Markdown to dictionary conversion utilities
# =============================================================================
# Description:
#   Converts Markdown strings to structured dictionaries including extraction
#   of JSON content if present. Supports structured parsing of markdown documents.
#
# File: md.py
# Project: ai-breadboard
# Package: core.utils.convertors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Markdown to dictionary conversion module.
Provides parsing functions for converting markdown strings to structured format.
"""

import re
from typing import Dict, List, Any
from markdown2 import markdown
from core.logger.logger import logger

def md2html(md_string: str, extras: List[str] = None) -> str:
    """
    Convert Markdown string to HTML.

    Args:
        md_string (str): Markdown string for conversion.
        extras (list, optional): List of markdown2 extensions. Defaults to None.

    Returns:
        str: HTML representation of Markdown.
    """
    try:
        if extras is None:
            return markdown(md_string)
        return markdown(md_string, extras=extras)
    except Exception as ex:
        logger.error("Error during Markdown to HTML conversion.", exc_info=True)
        return ""

def md2dict(md_string: str, extras: List[str] = None) -> Dict[str, list[str]]:
    """
    Convert Markdown string to structured dictionary.

    Args:
        md_string (str): Markdown string for conversion.
        extras (list, optional): List of markdown2 extensions for md2html. Defaults to None.

    Returns:
        Dict[str, list[str]]: Structured representation of Markdown content.
    """
    try:

        html = md2html(md_string, extras)
        sections: Dict[str, list[str]] = {}
        current_section: str | None = None

        for line in html.splitlines():
            if line.startswith('<h'):
                heading_level_match = re.search(r'h(\d)', line)
                if heading_level_match:
                    heading_level = int(heading_level_match.group(1))
                    section_title = re.sub(r'<.*?>', '', line).strip()
                    if heading_level == 1:
                        current_section = section_title
                        sections[current_section] = []
                    elif current_section:
                        sections[current_section].append(section_title)

            elif line.strip() and current_section:
                clean_text = re.sub(r'<.*?>', '', line).strip()
                sections[current_section].append(clean_text)

        return sections

    except Exception as ex:
        logger.error("Error parsing Markdown to structured dictionary.", exc_info=True)
        return {}
