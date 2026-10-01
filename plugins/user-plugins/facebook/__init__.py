# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins User-Plugins Facebook -   Init  
# =============================================================================
# Description:
#   Facebook Publisher plugin package.
#
# Usage Examples:
#   Python API:
#     from plugins.user-plugins.facebook.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.user-plugins.facebook
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Facebook Publisher plugin package.

Provides Facebook Graph API integration for publishing posts, links, photos,
inspecting pages, and conversational AI routing."""

from typing import Any, Optional
from plugins.facebook.plugin import FacebookPlugin
from plugins.facebook.client import FacebookGraphClient
__all__ = ['FacebookPlugin', 'FacebookGraphClient', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> FacebookPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        FacebookPlugin: Configured plugin instance.

    Examples:
        >>> from plugins.facebook import plugin
        >>> instance = plugin()
        >>> instance.name
        'facebook'
    """
    return FacebookPlugin(ai_model=ai_model, config=config)