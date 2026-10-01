# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Unified Chat Module
# =============================================================================
# Description:
#   Thin wrapper module to preserve backward‑compatible import path.
#
# Usage Examples:
#   Python API:
#     import src.ai.unified_chat as unified_chat
#
# File: unified_chat.py
# Project: ai-breadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Thin wrapper module to preserve backward‑compatible import path.

Historically the project exposed ``UnifiedChatModel`` via ``src.ai.unified_chat``.
After refactoring the implementation was moved to ``src.ai.orchestration.unified_chat``.
Tests and external code still import the old location, so we re‑export the class
here without adding any additional logic."""

from src.ai.orchestration.unified_chat import UnifiedChatModel

__all__ = ["UnifiedChatModel"]
