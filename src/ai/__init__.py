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
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Модуль основной системы (`__init__`)."""

from .chat.agy import AgyChatBase
from .chat.foundry import FoundryChatBase, FoundryClient, FoundrySimpleChat, get_foundry_chat, set_foundry_chat
from .chat.gemini_cli import GeminiCliChatBase, GeminiCliProvider, GeminiCliResponse
from .chat.openai_compat import OpenAICompatChat
from .chat.onnx import ONNXChatBase
from .chat.hf import HFChatBase
from .chat.ollama import OllamaChatBase, OllamaClient
from .providers.base import BaseChatProvider
from .gemini import GoogleGenerativeAI
from .agents import MediaSearchAgent, MCPClientManager
from .orchestration import get_available_models, actualize_all_models, add_unsupported_model, load_unsupported_models, UnifiedChatModel
from .voice import generate_voiceover_chunks
__all__ = ['BaseChatProvider', 'GoogleGenerativeAI', 'GeminiCliChatBase', 'GeminiCliProvider', 'GeminiCliResponse', 'AgyChatBase', 'OllamaChatBase', 'OllamaClient', 'FoundryChatBase', 'FoundryClient', 'FoundrySimpleChat', 'get_foundry_chat', 'set_foundry_chat', 'ONNXChatBase', 'HFChatBase', 'OpenAICompatChat', 'UnifiedChatModel', 'get_available_models', 'actualize_all_models', 'add_unsupported_model', 'load_unsupported_models', 'MediaSearchAgent', 'MCPClientManager', 'generate_voiceover_chunks']