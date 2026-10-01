# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api ~Webgui - Generate Auto Fill Csv
# =============================================================================
# Description:
#   Генерирует CSV‑файл с переводами, где английский и иврит имеют те же тексты,
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.api.~webgui.generate_auto_fill_csv
#   Python API:
#     from apps.windows.api.~webgui.generate_auto_fill_csv import load_ru
#
#     res = load_ru()
#
# File: generate_auto_fill_csv.py
# Project: ai-breadboard
# Package: apps.windows.api.~webgui
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Генерирует CSV‑файл с переводами, где английский и иврит имеют те же тексты,"""

import csv
import json
import pathlib
import sys
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

LOCALES_DIR = pathlib.Path(__file__).resolve().parent / 'locales'
RU_FILE = LOCALES_DIR / 'ru.json'
CSV_OUT = LOCALES_DIR / 'auto_fill_translations.csv'

def load_ru():
    if not RU_FILE.is_file():
        logger.error('ru.json не найден')
        sys.exit(1)
    with RU_FILE.open('r', encoding='utf-8') as f:
        return json.load(f)

def write_csv(data):
    with CSV_OUT.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['key', 'en', 'he'])
        writer.writeheader()
        for key, val in data.items():
            writer.writerow({'key': key, 'en': val, 'he': val})
    logger.info('Создан CSV %s с %d строками', CSV_OUT.name, len(data))

if __name__ == '__main__':
    ru = load_ru()
    write_csv(ru)
