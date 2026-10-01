# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Root - Replace Escaped Arrows
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`replace_escaped_arrows`).
#
# Usage Examples:
#   Python API:
#     import replace_escaped_arrows
#
# File: replace_escaped_arrows.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:20:26
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`replace_escaped_arrows`)."""

import pathlib

root = pathlib.Path(r"C:\\Users\\onela\\AppData\\Local\\AI-Breadboard")
for py_path in root.rglob('*.py'):
    try:
        text = py_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f'Failed to read {py_path}: {e}')
        continue
    if '-\\u003e' in text:
        new_text = text.replace('-\\u003e', '->')
        try:
            py_path.write_text(new_text, encoding='utf-8')
            print(f'Modified {py_path}')
        except Exception as e:
            print(f'Failed to write {py_path}: {e}')
