# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins System-Plugins Google_Oauth -   Init  
# =============================================================================
# Description:
#   Plugin factory function called by plugin loader.
#
# Usage Examples:
#   Python API:
#     from plugins.system-plugins.google_oauth.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.system-plugins.google_oauth
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Plugin factory function called by plugin loader."""

from typing import Any, Optional
from plugins.google_oauth.plugin import GoogleOAuthPlugin
__all__ = ['GoogleOAuthPlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> GoogleOAuthPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        GoogleOAuthPlugin: Configured plugin instance.
    """
    return GoogleOAuthPlugin(ai_model=ai_model, config=config)