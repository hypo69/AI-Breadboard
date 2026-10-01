# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm -   Main  
# =============================================================================
# Description:
#   Точка входа для вызова модуля через py -m apps.windows.wikillm.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.wikillm.__main__
#   Python API:
#     import apps.windows.wikillm.__main__ as __main__
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Точка входа для вызова модуля через py -m apps.windows.wikillm."""

from .cli import main

if __name__ == "__main__":
    main()
