# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api ~Webgui - Restore Html From Ru
# =============================================================================
# Description:
#   Восстанавливает оригинальные русские строки в index.html,
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.api.~webgui.restore_html_from_ru
#   Python API:
#     from apps.windows.api.~webgui.restore_html_from_ru import load_ru
#
#     res = load_ru()
#
# File: restore_html_from_ru.py
# Project: ai-breadboard
# Package: apps.windows.api.~webgui
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Восстанавливает оригинальные русские строки в index.html,"""

import json
import pathlib
import re
import sys
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

BASE_DIR = pathlib.Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / "index.html"
RU_JSON = BASE_DIR / "locales" / "ru.json"

SPAN_PATTERN = re.compile(r"<span\s+data-i18n=\"(?P<key>[^\"]+)\"\s*>(?P<inner>.*?)</span>", re.DOTALL)

def load_ru() -> dict:
    with RU_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)

def restore_html():
    ru = load_ru()
    content = HTML_PATH.read_text(encoding="utf-8")
    def repl(match):
        key = match.group("key")
        original = ru.get(key, "")
        if not original:
            logger.warning("Ключ %s не найден в ru.json, оставляю пустым", key)
        return original
    new_content = SPAN_PATTERN.sub(repl, content)
    HTML_PATH.write_text(new_content, encoding="utf-8")
    logger.info("HTML восстановлен из ru.json")

if __name__ == "__main__":
    restore_html()
