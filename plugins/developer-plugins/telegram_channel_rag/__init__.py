# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins Developer-Plugins Telegram_Channel_Rag -   Init  
# =============================================================================
# Description:
#   Telegram Channel RAG & Fast Search Plugin Package.
#
# Usage Examples:
#   Python API:
#     from plugins.developer-plugins.telegram_channel_rag.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.developer-plugins.telegram_channel_rag
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Telegram Channel RAG & Fast Search Plugin Package."""

from typing import Any, Optional
from plugins.telegram_channel_rag.plugin import TelegramChannelRagPlugin
__all__ = ['TelegramChannelRagPlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> TelegramChannelRagPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        TelegramChannelRagPlugin: Configured plugin instance.
    """
    return TelegramChannelRagPlugin(ai_model=ai_model, config=config)