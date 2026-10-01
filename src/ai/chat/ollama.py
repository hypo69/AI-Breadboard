# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Ollama Local Models Client
# =============================================================================
# Description:
#   Клиент взаимодействия с локальным инстансом Ollama.
#
# Usage Examples:
#   Python API:
#     from src.ai.chat.ollama import OllamaChat
#
#     ollama = OllamaChat(model_name="llama3")
#     answer = ollama.query("Объясни TDD")
#     print(answer)
#
# File: ollama.py
# Project: ai-breadboard
# Package: src.ai.chat
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Клиент взаимодействия с локальным инстансом Ollama."""

from src.ai.providers.ollama import OllamaChatBase, OllamaClient