# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Messenger Package Export and Router Initializer
# =============================================================================
# Description:
#   Exports router factory and core connection hub for the real-time messenger.
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.fastapi.messenger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .router_messenger import init_router, router
from .ws_manager import hub, ConnectionHub
from .database import init_db, get_db

__all__ = [
    "init_router",
    "router",
    "hub",
    "ConnectionHub",
    "init_db",
    "get_db",
]
