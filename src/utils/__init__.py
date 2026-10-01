# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard UTILS -   Init   Module
# =============================================================================
# Description:
#   Модуль утилит для AI-Breadboard.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Модуль утилит для AI-Breadboard.

Содержит различные вспомогательные инструменты и функции для работы с:
- CSV файлами
- Датой и временем
- Файловой системой
- FTP
- Изображениями
- JSON
- PDF
- SMTP
- URL
- Видео
- Excel файлами"""

from . import csv, date_time, file, ftp, get_free_port, header, image, jjson, printer, smtp, url, versioning, video, xls, archive, docx, pdf_extractor
try:
    from . import pdf
except ImportError:
    pdf = None
__all__ = ['archive', 'csv', 'date_time', 'docx', 'file', 'ftp', 'get_free_port', 'header', 'image', 'jjson', 'pdf', 'pdf_extractor', 'pformat', 'pprint', 'printer', 'smtp', 'url', 'versioning', 'video', 'xls']
from .printer import pformat, pprint