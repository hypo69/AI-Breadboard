# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows -   Main  
# =============================================================================
# Description:
#   Точка входа в AI Windows Diagnostic & Administration Center.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.__main__
#   Python API:
#     import apps.windows.__main__ as __main__
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Точка входа в AI Windows Diagnostic & Administration Center."""

import sys

if __name__ == '__main__':
    cli_flags = {
        '--mode', '--inspector', '--investigate', '--tui', '--logs',
        '--hardware', '--hw-monitor', '--hw-json', '--providers', '--cross-check'
    }
    if any(arg in cli_flags for arg in sys.argv[1:]):
        from apps.windows.cli import main
        main()
    else:
        from apps.windows.main import main
        main()