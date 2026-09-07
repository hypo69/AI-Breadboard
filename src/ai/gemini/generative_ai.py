# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Integration with Google Generative AI (Gemini) models
# =============================================================================
# Description:
#   Manages interaction with Google Generative AI API through official SDK.
#   Implements API key pool management, model rotation on failures, stream response generation,
#   tool support, and media file handling with comprehensive error recovery mechanisms.
#
# File: generative_ai.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from google import genai

from .api import GoogleGenerativeAI
from .core import _DEFAULT_MODEL, load_unsupported_models, add_unsupported_model
from .config import normalize_text, remove_html_blocks
from src.secrets.api_key_state import (
    get_status,
    load_api_keys,
    mark_exhausted,
    next_available_in,
    update_last_run,
)

__all__ = [
    'genai',
    'GoogleGenerativeAI',
    '_DEFAULT_MODEL',
    'load_unsupported_models',
    'add_unsupported_model',
    'normalize_text',
    'remove_html_blocks',
    'load_api_keys',
    'get_status',
    'mark_exhausted',
    'next_available_in',
    'update_last_run',
]




