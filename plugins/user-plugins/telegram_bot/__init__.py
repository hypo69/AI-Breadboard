# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Bot Plugin Package Interface
# =============================================================================
# Description:
#   Package initializer for the Telegram bot plugin, exporting plugin factory
#   function plugin() and main TelegramBotPlugin class.
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.telegram_bot
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Telegram Bot plugin package.

Provides Telegram Bot & Mini App remote control integration, notification routing,
voice narration, and user account linking.
"""

from __future__ import annotations

from typing import Any, Optional

from plugins.telegram_bot.plugin import TelegramBotPlugin
from plugins.telegram_bot.tts import handle_telegram_voiceover_request

__all__ = ["TelegramBotPlugin", "plugin", "handle_telegram_voiceover_request"]


def plugin(ai_model: Any = None, config: Optional[dict] = None) -> TelegramBotPlugin:
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
