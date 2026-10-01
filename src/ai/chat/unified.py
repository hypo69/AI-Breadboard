# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unified AI Provider Router & Dispatcher
# =============================================================================
# Description:
#   Единый диспетчер маршрутизации запросов к ИИ-провайдерам (Ollama, Gemini, OpenAI, Foundry, ONNX).
#
# Usage Examples:
#   Python API:
#     from src.ai.chat.unified import UnifiedAIChat
#
#     chat = UnifiedAIChat()
#     response = chat.generate_text(prompt="Привет, ИИ!")
#     print(response.text)
#
# File: unified.py
# Project: ai-breadboard
# Package: src.ai.chat
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Единый диспетчер маршрутизации запросов к ИИ-провайдерам (Ollama, Gemini, OpenAI, Foundry, ONNX)."""

from src.ai.orchestration.unified_chat import *