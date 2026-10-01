# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps System_Inspector - Tui
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`tui`).
#
# Usage Examples:
#   Python API:
#     import apps.system_inspector.tui as tui
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.system_inspector
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`tui`)."""

from apps.windows.tui import SystemInspectorState, render_inspector_ui as render_ui, RICH_AVAILABLE
__all__ = ['SystemInspectorState', 'render_ui', 'RICH_AVAILABLE']