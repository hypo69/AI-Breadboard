# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Facebook Publisher Plugin Package Interface
# =============================================================================
# Description:
#   Package initializer for the Facebook Publisher plugin, exporting the plugin
#   factory function plugin() and main FacebookPlugin class.
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.facebook
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Facebook Publisher plugin package.

Provides Facebook Graph API integration for publishing posts, links, photos,
inspecting pages, and conversational AI routing.
"""

from __future__ import annotations

from typing import Any, Optional

from plugins.facebook.plugin import FacebookPlugin
from plugins.facebook.client import FacebookGraphClient

__all__ = ["FacebookPlugin", "FacebookGraphClient", "plugin"]


def plugin(ai_model: Any = None, config: Optional[dict] = None) -> FacebookPlugin:
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
