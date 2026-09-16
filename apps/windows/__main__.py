# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Diagnostic Center Main Entrypoint
# =============================================================================
# Description:
#   Точка входа для запуска пакета apps.windows через python -m apps.windows
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа в AI Windows Diagnostic & Administration Center."""

from apps.windows.cli import main

if __name__ == "__main__":
    main()
