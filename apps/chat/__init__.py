# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Chat Application Package Initialization
# =============================================================================
# Description:
#   Package initialization for the standalone AI Chat application module.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.chat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет автономного приложения AI Chat для AI-Breadboard."""

from apps.chat.engine import ChatEngine
from apps.chat.router import init_router

__all__ = ["ChatEngine", "init_router"]
