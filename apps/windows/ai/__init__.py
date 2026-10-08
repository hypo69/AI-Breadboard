# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows AI - Package Root
# =============================================================================
# Description:
#   Слой 6: Контур ИИ, RAG, WikiLLM и интеллектуальная диагностика Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.ai import WindowsAIDiagnostician, WindowsAIRootCauseAnalyzer
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:38:00
# =============================================================================

from __future__ import annotations
"""Контур ИИ, базы знаний и интеллектуальной диагностики (Слой 6)."""

from apps.windows.ai.diagnostician import WindowsAIDiagnostician
from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer
from apps.windows.ai.tool_engine import (
    DynamicToolPlan,
    DynamicToolFactory,
    ToolRegistry,
    SafePowerShellProbeTool,
    WindowsCollectorTool,
)

__all__ = [
    "WindowsAIDiagnostician",
    "WindowsAIRootCauseAnalyzer",
    "DynamicToolPlan",
    "DynamicToolFactory",
    "ToolRegistry",
    "SafePowerShellProbeTool",
    "WindowsCollectorTool",
]