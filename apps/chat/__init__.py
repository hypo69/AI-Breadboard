# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Chat -   Init  
# =============================================================================
# Description:
#   Пакет автономного приложения AI Chat для AI-Breadboard.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.chat
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Пакет автономного приложения AI Chat для AI-Breadboard."""

from apps.chat.engine import ChatEngine
from apps.chat.router import init_router
__all__ = ['ChatEngine', 'init_router']