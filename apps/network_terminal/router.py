# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network Terminal FastAPI Router Integration
# =============================================================================
# Description:
#   FastAPI endpoint exports for network packet analysis, PCAP inspection,
#   and real-time live capture WebSocket streaming.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.network_terminal.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.network_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for Network Terminal."""

from src.fastapi.router_network import init_router, AnalyzeResponse

__all__ = [
    "init_router",
    "AnalyzeResponse",
]
