"""Telegram Channel RAG & Fast Search Plugin Package."""
from __future__ import annotations
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