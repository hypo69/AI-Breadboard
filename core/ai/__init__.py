# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Module
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: __init__.py
# Project: ai-breadboard
# Package: core.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from .gemini import GoogleGenerativeAI
from .gemini_cli_chat import GeminiCliChatBase
from .agy_chat import AgyChatBase
from .ollama_chat import OllamaChatBase
from .foundry_chat import FoundryChatBase, FoundrySimpleChat, get_foundry_chat, set_foundry_chat
from .unified_chat import UnifiedChatModel
from .model_manager import (
    actualize_all_models,
    get_available_models,
    add_unsupported_model,
    load_unsupported_models,
)