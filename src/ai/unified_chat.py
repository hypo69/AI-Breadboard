# -*- coding: utf-8 -*-
"""Thin wrapper module to preserve backward‑compatible import path.

Historically the project exposed ``UnifiedChatModel`` via ``src.ai.unified_chat``.
After refactoring the implementation was moved to ``src.ai.orchestration.unified_chat``.
Tests and external code still import the old location, so we re‑export the class
here without adding any additional logic.
"""

from src.ai.orchestration.unified_chat import UnifiedChatModel

__all__ = ["UnifiedChatModel"]
