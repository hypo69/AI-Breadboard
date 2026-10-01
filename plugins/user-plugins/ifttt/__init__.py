# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins User-Plugins Ifttt -   Init  
# =============================================================================
# Description:
#   Factory function to instantiate the IFTTT Smart Home plugin.
#
# Usage Examples:
#   Python API:
#     from plugins.user-plugins.ifttt.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.user-plugins.ifttt
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Factory function to instantiate the IFTTT Smart Home plugin."""

from typing import Any, Dict, Optional
from plugins.ifttt.client import IFTTTClient, send_ifttt_event
from plugins.ifttt.plugin import IFTTTPlugin
__all__ = ['IFTTTClient', 'IFTTTPlugin', 'plugin', 'send_ifttt_event']

def plugin(ai_model: Any=None, config: Optional[Dict[str, Any]]=None) -> IFTTTPlugin:
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