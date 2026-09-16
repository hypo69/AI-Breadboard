# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google OAuth System Plugin Package Interface
# =============================================================================
# Description:
#   Package initializer for Google OAuth system plugin, providing token management,
#   account pool discovery, and credentials refresh.
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.google_oauth
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Optional
from plugins.google_oauth.plugin import GoogleOAuthPlugin

__all__ = ["GoogleOAuthPlugin", "plugin"]


def plugin(ai_model: Any = None, config: Optional[dict] = None) -> GoogleOAuthPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        GoogleOAuthPlugin: Configured plugin instance.
    """
    return GoogleOAuthPlugin(ai_model=ai_model, config=config)
