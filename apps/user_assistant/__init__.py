# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps User_Assistant -   Init  
# =============================================================================
# Description:
#   Пакет приложения User Assistant.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.user_assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Пакет приложения User Assistant.

Updated: 2026-10-01 06:40:00"""

from apps.user_assistant.engine import UserAssistantEngine
from apps.user_assistant.routers.router import router, init_router

__all__ = ['UserAssistantEngine', 'router', 'init_router']