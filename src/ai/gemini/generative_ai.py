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

from .api import GoogleGenerativeAI
from .core import _DEFAULT_MODEL

__all__ = ['GoogleGenerativeAI', '_DEFAULT_MODEL']
