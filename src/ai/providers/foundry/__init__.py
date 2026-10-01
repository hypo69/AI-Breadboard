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
# Package: src.ai.providers.foundry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Модуль основной системы (`__init__`)."""

from .client import FoundryClient
from .chat import FoundryChatBase, FoundrySimpleChat, get_foundry_chat, set_foundry_chat
__all__ = ['FoundryClient', 'FoundryChatBase', 'FoundrySimpleChat', 'get_foundry_chat', 'set_foundry_chat']