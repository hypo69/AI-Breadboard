# -*- coding: utf-8 -*-
from __future__ import annotations

# Providers
from .providers.base import BaseChatProvider
from .providers.ollama import OllamaChatBase, OllamaClient
from .providers.foundry import FoundryChatBase, FoundryClient, FoundrySimpleChat, get_foundry_chat, set_foundry_chat
from .providers.onnx import ONNXChatBase
from .providers.huggingface import HFChatBase
from .providers.openai import OpenAICompatChat
from .providers.gemini_cli import GeminiCliChatBase
from .providers.agy import AgyChatBase
from .gemini import GoogleGenerativeAI

# Agents
from .agents import MediaSearchAgent, MCPClientManager

# Orchestration
from .orchestration import (
    get_available_models,
    actualize_all_models,
    add_unsupported_model,
    load_unsupported_models,
    UnifiedChatModel,
)

# Voice
from .voice import generate_voiceover_chunks

__all__ = [
    "BaseChatProvider",
    "GoogleGenerativeAI",
    "GeminiCliChatBase",
    "AgyChatBase",
    "OllamaChatBase",
    "OllamaClient",
    "FoundryChatBase",
    "FoundryClient",
    "FoundrySimpleChat",
    "get_foundry_chat",
    "set_foundry_chat",
    "ONNXChatBase",
    "HFChatBase",
    "OpenAICompatChat",
    "UnifiedChatModel",
    "get_available_models",
    "actualize_all_models",
    "add_unsupported_model",
    "load_unsupported_models",
    "MediaSearchAgent",
    "MCPClientManager",
    "generate_voiceover_chunks",
]
