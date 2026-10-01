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
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Модуль основной системы (`__init__`)."""

from .api import GoogleGenerativeAI
from .core import GoogleGenerativeAICore, load_unsupported_models, add_unsupported_model
from .config import normalize_text, remove_html_blocks
from .embeddings import GoogleGenerativeAIEmbeddingsMixin
from .errors import GoogleGenerativeAIErrorMixin
from .history import GoogleGenerativeAIHistoryMixin
from .images import GoogleGenerativeAIImagesMixin
__all__ = ['GoogleGenerativeAI', 'GoogleGenerativeAICore', 'load_unsupported_models', 'add_unsupported_model', 'normalize_text', 'remove_html_blocks', 'GoogleGenerativeAIEmbeddingsMixin', 'GoogleGenerativeAIErrorMixin', 'GoogleGenerativeAIHistoryMixin', 'GoogleGenerativeAIImagesMixin']