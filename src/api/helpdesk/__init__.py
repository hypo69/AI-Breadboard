# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Subsystem Package Initialization
# =============================================================================
# Description:
#   Exports factory initializers, database managers, models, and WebSocket hub
#   for the centralized Helpdesk and user support management system.
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.api.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .router_helpdesk import init_router, router
from .ws_manager import hub, HelpdeskConnectionHub
from .database import init_db, get_db

__all__ = [
    "init_router",
    "router",
    "hub",
    "HelpdeskConnectionHub",
    "init_db",
    "get_db",
]
