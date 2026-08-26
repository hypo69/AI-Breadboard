## \file /src/utils/convertors/md2dict.py
# -*- coding: utf-8 -*-

#! .pyenv/bin/python3

"""
.. module:: src.utils.convertors.md2dict 
	:platform: Windows, Unix
	:synopsis: Модуль для конвертации строки Markdown в структурированный словарь, включая извлечение JSON содержимого, если оно присутствует.
"""

import re
from typing import Dict, List, Any
from markdown2 import markdown
from core.logger.logger import logger



def md2html(md_string: str, extras: List[str] = None) -> str:
     """
     Конвертирует строку Markdown в HTML.

     Args:
         md_string (str): Строка Markdown для конвертации.
         extras (list, optional): Список расширений markdown2. Defaults to None.

     Returns:
         str: HTML-представление Markdown.
     """
     try:
         if extras is None:
            return markdown(md_string)
         return markdown(md_string, extras=extras)
     except Exception as ex:
        logger.error("Ошибка при преобразовании Markdown в HTML.", exc_info=True)
        return ""


def md2dict(md_string: str, extras: List[str] = None) -> Dict[str, list[str]]:
    """
    Конвертирует строку Markdown в структурированный словарь.

    Args:
        md_string (str): Строка Markdown для конвертации.
        extras (list, optional): Список расширений markdown2 для md2html. Defaults to None.

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
        logger.error("Ошибка при парсинге Markdown в структурированный словарь.", exc_info=True)
        return {}