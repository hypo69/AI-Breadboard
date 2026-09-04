# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Generative AI Main Module
# =============================================================================
# Description:
#   Main module for Google Generative AI integration.
#   Exports the unified GoogleGenerativeAI class.
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .api import GoogleGenerativeAI
from .core import GoogleGenerativeAICore, load_unsupported_models, add_unsupported_model
from .config import normalize_text, remove_html_blocks
from .embeddings import GoogleGenerativeAIEmbeddingsMixin
from .errors import GoogleGenerativeAIErrorMixin
from .history import GoogleGenerativeAIHistoryMixin
from .images import GoogleGenerativeAIImagesMixin

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
]
