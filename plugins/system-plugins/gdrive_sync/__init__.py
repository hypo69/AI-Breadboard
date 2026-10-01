# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins System-Plugins Gdrive_Sync -   Init  
# =============================================================================
# Description:
#   Plugin factory function called by plugin loader.
#
# Usage Examples:
#   Python API:
#     from plugins.system-plugins.gdrive_sync.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.system-plugins.gdrive_sync
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Plugin factory function called by plugin loader."""

from typing import Any, Optional
from plugins.gdrive_sync.plugin import GDriveSyncPlugin
__all__ = ['GDriveSyncPlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> GDriveSyncPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        GDriveSyncPlugin: Configured plugin instance.
    """
    return GDriveSyncPlugin(ai_model=ai_model, config=config)