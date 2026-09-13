# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Log Analyzer Plugin Factory
# =============================================================================
# Description:
#   Exposes the plugin factory for dynamic loading by the Admin UI plugin manager.
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.log_analyzer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Optional
from plugins.log_analyzer.plugin import LogAnalyzerPlugin

__all__ = ["LogAnalyzerPlugin", "plugin"]


def plugin(ai_model: Any = None, config: Optional[dict] = None) -> LogAnalyzerPlugin:
    """Factory function for initializing the Log Analyzer plugin.

    Args:
        ai_model: Optional AI model instance.
        config: Initial configuration overrides.

    Returns:
        LogAnalyzerPlugin: Initialized plugin instance.
    """
    return LogAnalyzerPlugin(ai_model=ai_model, config=config)
