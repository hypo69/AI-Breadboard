# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Trading Terminal Package Initialization
# =============================================================================
# Description:
#   Package exports for trading desk engine, TUI renderer, and FastAPI router.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.trading_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Exchange Trading Terminal standalone application."""

from .engine import (
    TradingDeskEngine,
    TradingState,
    MarketTicker,
    OrderRequest,
    OrderRecord,
)
from .tui import run_dashboard, render_ui
from .router import init_router, get_engine

__all__ = [
    "TradingDeskEngine",
    "TradingState",
    "MarketTicker",
    "OrderRequest",
    "OrderRecord",
    "run_dashboard",
    "render_ui",
    "init_router",
    "get_engine",
]
