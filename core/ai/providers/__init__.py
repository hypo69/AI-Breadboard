# -*- coding: utf-8 -*-
# =============================================================================
# Package: core.ai.providers
# Description: Modular AI Provider Registry & Adapters
# =============================================================================

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

__all__ = [
    "BaseChatProvider",
    "OllamaChatBase",
    "OllamaClient",
    "FoundryChatBase",
    "FoundryClient",
    "ONNXChatBase",
    "HFChatBase",
    "OpenAICompatChat",
    "GeminiCliChatBase",
    "AgyChatBase",
    "GeminiChatBase",
    "WindowsAIChatBase",
    "probe_windows_ai_components",
]
