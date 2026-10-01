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
# Package: src.ai.providers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Модуль основной системы (`__init__`)."""

from .base import BaseChatProvider
from .ollama import OllamaChatBase, OllamaClient
from .foundry import FoundryChatBase, FoundryClient
from .onnx import ONNXChatBase
from .huggingface import HFChatBase
from .openai import OpenAICompatChat
from .gemini_cli import GeminiCliChatBase
from .agy import AgyChatBase
from .gemini import GeminiChatBase
from .windows_ai import WindowsAIChatBase, probe_windows_ai_components
__all__ = ['BaseChatProvider', 'OllamaChatBase', 'OllamaClient', 'FoundryChatBase', 'FoundryClient', 'ONNXChatBase', 'HFChatBase', 'OpenAICompatChat', 'GeminiCliChatBase', 'AgyChatBase', 'GeminiChatBase', 'WindowsAIChatBase', 'probe_windows_ai_components']