# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps User_Assistant - Router
# =============================================================================
# Description:
#   Реэкспорт роутера User Assistant.
#
# Usage Examples:
#   Python API:
#     import apps.user_assistant.router as router
#
# File: router.py
# Project: ai-breadboard
# Package: apps.user_assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Реэкспорт роутера User Assistant.

Updated: 2026-10-01 06:40:00"""

from apps.user_assistant.routers.router import router, init_router

__all__ = ['router', 'init_router']
