# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Intelligence Package
# =============================================================================
# Description:
#   Пакет AI-диагностики, генерации гипотез и анализа первопричин Windows.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Экспорт AI-модулей диагностики Windows."""

from apps.windows.ai.diagnostician import WindowsAIDiagnostician
from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer

__all__ = [
    "WindowsAIDiagnostician",
    "WindowsAIRootCauseAnalyzer",
]
