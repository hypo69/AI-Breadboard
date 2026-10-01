# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI -   Init   Module
# =============================================================================
# Description:
#   Пакет chat агрегирует все чат‑модули провайдеров.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.ai.chat
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Пакет chat агрегирует все чат‑модули провайдеров.
Экспортирует основные классы для удобного импорта:
    from src.ai.chat import AgyChatBase, GeminiChatBase, ..."""

from .agy import *
from .foundry import *
from .gemini import *
from .gemini_cli import *
from .hf import *
from .ollama import *
from .onnx import *
from .openai_compat import *
from .unified import *