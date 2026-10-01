# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api -   Init  
# =============================================================================
# Description:
#   Внутренний FastAPI-сервис подсистемы Windows.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Внутренний FastAPI-сервис подсистемы Windows."""

from .internal_app import create_internal_app, load_config

__all__ = [
    'create_internal_app',
    'load_config',
]