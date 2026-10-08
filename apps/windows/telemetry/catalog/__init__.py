# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Catalog - Package Root
# =============================================================================
# Description:
#   Каталог событий Windows, реестр провайдеров и Sysmon слои.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.catalog.event_catalog import WindowsEventCatalog
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.catalog
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:36:00
# =============================================================================

from __future__ import annotations
"""Каталог событийных журналов и реестр провайдеров ETW/Sysmon."""

from apps.windows.telemetry.catalog.event_catalog import WindowsEventCatalog

__all__ = [
    "WindowsEventCatalog",
]
