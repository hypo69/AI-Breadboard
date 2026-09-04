# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Generative AI Models Management
# =============================================================================
# Description:
#   Model management for Google Generative AI.
#   Provides methods for loading, adding, and managing unsupported models.
#
# File: models.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .core import load_unsupported_models, add_unsupported_model, GoogleGenerativeAICore

__all__ = ['load_unsupported_models', 'add_unsupported_model', 'GoogleGenerativeAICore']
