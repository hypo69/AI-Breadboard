# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins Developer-Plugins Rag_Cleaner -   Init  
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`__init__`).
#
# Usage Examples:
#   Python API:
#     from plugins.developer-plugins.rag_cleaner.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.developer-plugins.rag_cleaner
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Скрипт/модуль системы AI-Breadboard (`__init__`)."""

from typing import Any, Optional
from plugins.rag_cleaner.plugin import RAGCleanerPlugin
__all__ = ['RAGCleanerPlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> RAGCleanerPlugin:
    return RAGCleanerPlugin(ai_model=ai_model, config=config)