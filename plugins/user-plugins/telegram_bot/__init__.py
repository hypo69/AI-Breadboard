# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins User-Plugins Telegram_Bot -   Init  
# =============================================================================
# Description:
#   Telegram Bot plugin package.
#
# Usage Examples:
#   Python API:
#     from plugins.user-plugins.telegram_bot.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.user-plugins.telegram_bot
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Telegram Bot plugin package.

Provides Telegram Bot & Mini App remote control integration, notification routing,
voice narration, and user account linking."""

from typing import Any, Optional
from plugins.telegram_bot.plugin import TelegramBotPlugin
from plugins.telegram_bot.tts import handle_telegram_voiceover_request
__all__ = ['TelegramBotPlugin', 'plugin', 'handle_telegram_voiceover_request']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> TelegramBotPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        TelegramBotPlugin: Configured plugin instance.

    Examples:
        >>> from plugins.telegram_bot import plugin
        >>> instance = plugin()
        >>> instance.name
        'telegram_bot'
    """
    return TelegramBotPlugin(ai_model=ai_model, config=config)