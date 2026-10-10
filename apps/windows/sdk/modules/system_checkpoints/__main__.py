# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints -   Main  
# =============================================================================
# Description:
#   Точка входа для запуска Windows System Checkpoints & Recovery Manager.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.sdk.modules.system_checkpoints.__main__
#   Python API:
#     import apps.windows.sdk.modules.system_checkpoints.__main__ as __main__
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.system_checkpoints
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Точка входа для запуска Windows System Checkpoints & Recovery Manager."""

from apps.windows.system_checkpoints.tui import run_interactive_tui

if __name__ == "__main__":
    run_interactive_tui()
