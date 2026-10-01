# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins Developer-Plugins Generate_Rag_From_Codebase -   Init  
# =============================================================================
# Description:
#   Generate RAG from Codebase Plugin Package.
#
# Usage Examples:
#   Python API:
#     from plugins.developer-plugins.generate_rag_from_codebase.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.developer-plugins.generate_rag_from_codebase
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Generate RAG from Codebase Plugin Package."""

from typing import Any, Optional
from plugins.generate_rag_from_codebase.plugin import GenerateRagCodebasePlugin
__all__ = ['GenerateRagCodebasePlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> GenerateRagCodebasePlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        GenerateRagCodebasePlugin: Configured plugin instance.
    """
    return GenerateRagCodebasePlugin(ai_model=ai_model, config=config)