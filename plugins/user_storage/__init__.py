# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Storage Plugin Package Interface
# =============================================================================
# Description:
#   Package initializer for User Storage & Documents plugin, providing per-user
#   sandboxed document storage, file quotas, and RAG document ingestion.
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.user_storage
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Optional

from plugins.user_storage.plugin import UserStoragePlugin

__all__ = ["UserStoragePlugin", "plugin"]


def plugin(ai_model: Any = None, config: Optional[dict] = None) -> UserStoragePlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        UserStoragePlugin: Configured plugin instance.
    """
    return UserStoragePlugin(ai_model=ai_model, config=config)
