# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: IFTTT Plugin Module Exports and Factory
# =============================================================================
# Description:
#   Exports plugin() factory and core classes for IFTTT Smart Home integration.
#
# Examples:
#   >>> from plugins.ifttt import plugin
#   >>> p = plugin()
#   >>> p.name
#   'ifttt'
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.ifttt
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, Optional

from plugins.ifttt.client import IFTTTClient, send_ifttt_event
from plugins.ifttt.plugin import IFTTTPlugin

__all__ = [
    "IFTTTClient",
    "IFTTTPlugin",
    "plugin",
    "send_ifttt_event",
]


def plugin(ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> IFTTTPlugin:
    """Factory function to instantiate the IFTTT Smart Home plugin.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[Dict[str, Any]]): Configuration dictionary.

    Returns:
        IFTTTPlugin: Configured plugin instance.

    Examples:
        >>> p = plugin()
        >>> p.name
        'ifttt'
    """
    return IFTTTPlugin(ai_model=ai_model, config=config)
