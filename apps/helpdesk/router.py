# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Application FastAPI Router Bridge
# =============================================================================
# Description:
#   FastAPI REST and WebSocket router for apps.helpdesk microservice.
#   Provides standard /api/v1/helpdesk prefix compatibility along with core endpoints.
#
# File: router.py
# Project: ai-breadboard
# Package: apps.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for Helpdesk application."""

from __future__ import annotations

from fastapi import APIRouter
from src.api.helpdesk.router_helpdesk import router as core_helpdesk_router

router = APIRouter(prefix="/api/v1/helpdesk", tags=["Helpdesk Application"])

# Mount core router endpoints under /api/v1/helpdesk prefix
router.include_router(core_helpdesk_router, prefix="")


def init_router() -> APIRouter:
    """Initialize and export Helpdesk application APIRouter instance.

    Returns:
        APIRouter: Configured FastAPI router for the Helpdesk application.
    """
    return router
