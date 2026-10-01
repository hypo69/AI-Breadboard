# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Helpdesk Routers - Router
# =============================================================================
# Description:
#   FastAPI router integration for Helpdesk application.
#
# Usage Examples:
#   Python API:
#     from apps.helpdesk.routers.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.helpdesk.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""FastAPI router integration for Helpdesk application."""

from fastapi import APIRouter
from src.api.helpdesk.router_helpdesk import router as core_helpdesk_router
router = APIRouter(prefix='/api/v1/helpdesk', tags=['Helpdesk Application'])
router.include_router(core_helpdesk_router, prefix='')

def init_router() -> APIRouter:
    """Initialize and export Helpdesk application APIRouter instance.

    Returns:
        APIRouter: Configured FastAPI router for the Helpdesk application.
    """
    return router