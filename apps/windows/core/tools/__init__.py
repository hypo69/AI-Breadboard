# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Tools Package
# =============================================================================
# Description:
#   Экспорт базовых классов, реестра и фабрики динамических инструментов.
#
# File: __init__.py
# Project: AI-Breadboard
# Package: apps.windows.core.tools
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет инструментов и реестра подсистемы Windows."""

from apps.windows.core.tools.base import BaseTool, ToolExecutionResult
from apps.windows.core.tools.dynamic_factory import (
    CreateCustomToolMetaTool,
    DynamicSynthesizedTool,
    DynamicToolFactory,
    to_ascii_slug,
)
from apps.windows.core.tools.registry import ToolRegistry
from apps.windows.core.tools.system_tools import (
    SafePowerShellProbeTool,
    WindowsCollectorTool,
    register_system_tools,
)

__all__ = [
    "BaseTool",
    "ToolExecutionResult",
    "ToolRegistry",
    "WindowsCollectorTool",
    "SafePowerShellProbeTool",
    "register_system_tools",
    "DynamicToolFactory",
    "DynamicSynthesizedTool",
    "CreateCustomToolMetaTool",
    "to_ascii_slug",
]

