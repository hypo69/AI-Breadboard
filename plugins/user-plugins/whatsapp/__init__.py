# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins User-Plugins Whatsapp -   Init  
# =============================================================================
# Description:
#   Пакет модульного плагина WhatsApp для платформы AI Breadboard.
#
# Usage Examples:
#   Python API:
#     from plugins.user-plugins.whatsapp.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.user-plugins.whatsapp
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Пакет модульного плагина WhatsApp для платформы AI Breadboard."""

from typing import Any, Optional
from .client import WhatsAppClient, normalize_phone_number
from .plugin import WhatsAppPlugin
__all__ = ['WhatsAppPlugin', 'WhatsAppClient', 'normalize_phone_number', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> WhatsAppPlugin:
    """Фабричная функция для инициализации плагина загрузчиком плагинов.

    Args:
        ai_model (Any): Опциональная модель ИИ.
        config (Optional[dict]): Переопределения конфигурации.

    Returns:
        WhatsAppPlugin: Экземпляр плагина.
    """
    return WhatsAppPlugin(ai_model=ai_model, config=config)