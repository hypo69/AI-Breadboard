# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Dev - Trading Terminal
# =============================================================================
# Description:
#   Backward compatibility wrapper for apps.trading_terminal.
#
# Usage Examples:
#   CLI:
#     python -m scripts.dev.trading_terminal
#   Python API:
#     import scripts.dev.trading_terminal as trading_terminal
#
# File: trading_terminal.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

"""Backward compatibility wrapper for apps.trading_terminal."""

from apps.trading_terminal import TradingDeskEngine, render_ui, run_dashboard
from apps.trading_terminal.__main__ import main
__all__ = ['TradingDeskEngine', 'render_ui', 'run_dashboard', 'main']
if __name__ == '__main__':
    main()