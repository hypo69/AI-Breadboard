# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API -   Init   Module
# =============================================================================
# Description:
#   Модуль основной системы (`__init__`).
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.api.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Модуль основной системы (`__init__`)."""

from .router_helpdesk import init_router, router
from .ws_manager import hub, HelpdeskConnectionHub
from .database import init_db, get_db
__all__ = ['init_router', 'router', 'hub', 'HelpdeskConnectionHub', 'init_db', 'get_db']