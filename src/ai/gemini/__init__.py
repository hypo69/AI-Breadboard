# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI -   Init   Module
# =============================================================================
# Description:
#   Модуль основной системы (`__init__`).
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 10:46:35
# =============================================================================

"""Модуль основной системы (`__init__`)."""

from .api import GoogleGenerativeAI
from .core import GoogleGenerativeAICore, load_unsupported_models, add_unsupported_model
from .config import normalize_text, remove_html_blocks
from .embeddings import GoogleGenerativeAIEmbeddingsMixin
from .errors import GoogleGenerativeAIErrorMixin
from .history import GoogleGenerativeAIHistoryMixin
from .images import GoogleGenerativeAIImagesMixin
from .rules import (
    matches_rule,
    is_gemini_model_unsupported,
    filter_unsupported_gemini_models,
    load_unsupported_rules_and_models,
    add_unsupported_gemini_model,
)

__all__ = [
    'GoogleGenerativeAI',
    'GoogleGenerativeAICore',
    'load_unsupported_models',
    'add_unsupported_model',
    'normalize_text',
    'remove_html_blocks',
    'GoogleGenerativeAIEmbeddingsMixin',
    'GoogleGenerativeAIErrorMixin',
    'GoogleGenerativeAIHistoryMixin',
    'GoogleGenerativeAIImagesMixin',
    'matches_rule',
    'is_gemini_model_unsupported',
    'filter_unsupported_gemini_models',
    'load_unsupported_rules_and_models',
    'add_unsupported_gemini_model',
]