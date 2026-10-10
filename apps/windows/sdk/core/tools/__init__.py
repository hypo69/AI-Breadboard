# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core Tools -   Init  
# =============================================================================
# Description:
#   Пакет инструментов и реестра подсистемы Windows.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.core.tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Пакет инструментов и реестра подсистемы Windows."""

from apps.windows.sdk.core.tools.base import BaseTool, ToolExecutionResult
from apps.windows.sdk.core.tools.dynamic_factory import CreateCustomToolMetaTool, DynamicSynthesizedTool, DynamicToolFactory, to_ascii_slug
from apps.windows.sdk.core.tools.registry import ToolRegistry
from apps.windows.sdk.core.tools.system_tools import SafePowerShellProbeTool, WindowsCollectorTool, register_system_tools
__all__ = ['BaseTool', 'ToolExecutionResult', 'ToolRegistry', 'WindowsCollectorTool', 'SafePowerShellProbeTool', 'register_system_tools', 'DynamicToolFactory', 'DynamicSynthesizedTool', 'CreateCustomToolMetaTool', 'to_ascii_slug']