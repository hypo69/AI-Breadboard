# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: WhatsApp Plugin Package Interface
# =============================================================================
# Description:
#   Инициализатор пакета плагина WhatsApp, экспортирующий фабричную функцию
#   plugin(), клиент WhatsAppClient и класс WhatsAppPlugin.
#
# File: __init__.py
# Package: plugins.whatsapp
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Пакет модульного плагина WhatsApp для платформы AI Breadboard."""

from __future__ import annotations

from typing import Any, Optional

from .client import WhatsAppClient, normalize_phone_number
from .plugin import WhatsAppPlugin

__all__ = ["WhatsAppPlugin", "WhatsAppClient", "normalize_phone_number", "plugin"]


def plugin(ai_model: Any = None, config: Optional[dict] = None) -> WhatsAppPlugin:
    """Фабричная функция для инициализации плагина загрузчиком плагинов.

    Args:
        ai_model (Any): Опциональная модель ИИ.
        config (Optional[dict]): Переопределения конфигурации.

    Returns:
        WhatsAppPlugin: Экземпляр плагина.
    """
    return WhatsAppPlugin(ai_model=ai_model, config=config)
