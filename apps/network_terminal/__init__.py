# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network Terminal Package Initialization
# =============================================================================
# Description:
#   Package exports for Network Analyzer Terminal application, TUI dashboard,
#   state manager, and FastAPI router integration.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.network_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Network Analyzer Terminal standalone application."""

from .router import init_router
from .tui import NetworkTerminalState, render_ui, run_network_dashboard

__all__ = [
    "NetworkTerminalState",
    "render_ui",
    "run_network_dashboard",
    "init_router",
]
