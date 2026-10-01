# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Helpdesk -   Init  
# =============================================================================
# Description:
#   Helpdesk support management application and live operator desk.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Helpdesk support management application and live operator desk."""

from apps.helpdesk.routers.router import init_router, router
__all__ = ['router', 'init_router']