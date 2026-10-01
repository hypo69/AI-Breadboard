# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins User-Plugins User_Storage -   Init  
# =============================================================================
# Description:
#   Plugin factory function called by plugin loader.
#
# Usage Examples:
#   Python API:
#     from plugins.user-plugins.user_storage.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.user-plugins.user_storage
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Plugin factory function called by plugin loader."""

from typing import Any, Optional
from plugins.user_storage.plugin import UserStoragePlugin
__all__ = ['UserStoragePlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> UserStoragePlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        UserStoragePlugin: Configured plugin instance.
    """
    return UserStoragePlugin(ai_model=ai_model, config=config)