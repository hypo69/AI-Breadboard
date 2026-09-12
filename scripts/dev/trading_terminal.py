# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Trading Control Desk & Terminal (Legacy Shim)
# =============================================================================
# Description:
#   Backward compatibility shim for Trading Desk Terminal.
#   Directs all executions to the standalone package `apps.trading_terminal`.
#
# Examples:
#   $ python -m scripts.dev.trading_terminal --symbol BTC/USDT
#
# File: trading_terminal.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Backward compatibility wrapper for apps.trading_terminal."""

from apps.trading_terminal import (
    TradingDeskEngine,
    render_ui,
    run_dashboard,
)
from apps.trading_terminal.__main__ import main

__all__ = [
    "TradingDeskEngine",
    "render_ui",
    "run_dashboard",
    "main",
]

if __name__ == "__main__":
    main()
