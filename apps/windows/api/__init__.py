# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows API - Package Root
# =============================================================================
# Description:
#   Слой 7: Внутренний FastAPI-сервис подсистемы Windows и Auto-Discovery роутеров.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api import create_app, discover_and_register_routers
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:38:00
# =============================================================================

from __future__ import annotations
"""Внутренний FastAPI-сервис подсистемы Windows (Слой 7)."""

from apps.windows.api.server import (
    create_app,
    create_internal_app,
    discover_and_register_routers,
    load_config,
)

__all__ = [
    "create_app",
    "create_internal_app",
    "discover_and_register_routers",
    "load_config",
]