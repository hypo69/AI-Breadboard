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
     Конвертирует строку Markdown в HTML.

     Args:
         md_string (str): String Markdown для конвертации.
         extras (list, optional): List расширений markdown2. Defaults to None.

     Returns:
         str: HTML-представление Markdown.
     """
     try:
         if extras is None:
            return markdown(md_string)
         return markdown(md_string, extras=extras)
     except Exception as ex:
        logger.error("Error при преобразовании Markdown в HTML.", exc_info=True)
        return ""

def md2dict(md_string: str, extras: List[str] = None) -> Dict[str, list[str]]:
    """
    Конвертирует строку Markdown в структурированный dictionary.

    Args:
        md_string (str): String Markdown для конвертации.
        extras (list, optional): List расширений markdown2 для md2html. Defaults to None.

    Returns:
         Dict[str, list[str]]: Структурированное представление Markdown содержимого.
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
        logger.error("Error при парсинге Markdown в структурированный dictionary.", exc_info=True)
        return {}