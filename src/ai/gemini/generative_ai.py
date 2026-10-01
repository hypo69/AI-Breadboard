# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Generative Ai Module
# =============================================================================
# Description:
#   Модуль основной системы (`generative_ai`).
#
# Usage Examples:
#   Python API:
#     import src.ai.gemini.generative_ai as generative_ai
#
# File: generative_ai.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Модуль основной системы (`generative_ai`)."""

from google import genai
from .api import GoogleGenerativeAI
from .core import _DEFAULT_MODEL, load_unsupported_models, add_unsupported_model
from .config import normalize_text, remove_html_blocks
from src.ai.gemini.gemini_api_key_state import get_status, load_api_keys, mark_exhausted, next_available_in, update_last_run
__all__ = ['genai', 'GoogleGenerativeAI', '_DEFAULT_MODEL', 'load_unsupported_models', 'add_unsupported_model', 'normalize_text', 'remove_html_blocks', 'load_api_keys', 'get_status', 'mark_exhausted', 'next_available_in', 'update_last_run']