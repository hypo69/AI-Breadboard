# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Application Package Initialization
# =============================================================================
# Description:
#   Package initialization for the Helpdesk standalone domain application
#   under the /apps microservices layer.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Helpdesk support management application and live operator desk."""

from apps.helpdesk.router import init_router, router

__all__ = ["router", "init_router"]
