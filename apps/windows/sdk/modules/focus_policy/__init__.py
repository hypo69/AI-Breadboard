# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Focus_Policy - Init
# =============================================================================
# Description:
#   Пакет Focus Policy Engine (профили, расписание, подавление уведомлений).
#
# Usage Examples:
#   from apps.windows.sdk.modules.focus_policy import WindowsFocusController, init_router
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.focus_policy
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:05:00
# =============================================================================

"""Пакет Focus Policy Engine."""

from apps.windows.sdk.modules.focus_policy.controller import WindowsFocusController
from apps.windows.sdk.modules.focus_policy.models import FocusProfile
from apps.windows.sdk.modules.focus_policy.router import init_router

__all__ = ['WindowsFocusController', 'FocusProfile', 'init_router']
