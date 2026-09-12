# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Inspector Application Router Re-export
# =============================================================================
# Description:
#   FastAPI endpoint re-exports for system telemetry, hardware inspection,
#   and AI performance diagnosis.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.system_inspector.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.system_inspector
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for System Inspector."""

from src.fastapi.router_system import init_router

__all__ = [
    "init_router",
]
