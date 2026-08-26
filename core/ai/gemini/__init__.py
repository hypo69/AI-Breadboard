# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Модуль интеграции с моделями Google Gemini
# =============================================================================
# Описание:
#   Предоставление основного интерфейса GoogleGenerativeAI для работы с моделями
#   семейства Gemini в рамках подсистемы искусственного интеллекта проекта.
#
# Примеры:
#   >>> from core.ai.gemini import GoogleGenerativeAI
#   >>> model = GoogleGenerativeAI()
#
# File: __init__.py
# Project: ai-assistant
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Пакет интеграции с Google Gemini."""

from core.ai.gemini.generative_ai import (
    GoogleGenerativeAI,
    add_unsupported_model,
    load_unsupported_models,
    normalize_text,
    remove_html_blocks,
)

__all__: list[str] = [
    'GoogleGenerativeAI',
    'add_unsupported_model',
    'load_unsupported_models',
    'normalize_text',
    'remove_html_blocks',
]
