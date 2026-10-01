# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins System-Plugins Application_Log_Analyzer -   Init  
# =============================================================================
# Description:
#   Фабрика плагина анализатора логов приложения.
#
# Usage Examples:
#   Python API:
#     from plugins.system-plugins.application_log_analyzer.__init__ import plugin
#
#     res = plugin()
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.system-plugins.application_log_analyzer
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

from __future__ import annotations
"""Фабрика плагина анализатора логов приложения.

Предоставляет точку входа для динамической инициализации плагина
`ApplicationLogAnalyzerPlugin`."""

from typing import Any, Optional
from plugins.application_log_analyzer.plugin import ApplicationLogAnalyzerPlugin, LogAnalyzerPlugin
__all__ = ['ApplicationLogAnalyzerPlugin', 'LogAnalyzerPlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> ApplicationLogAnalyzerPlugin:
    """Фабричная функция инициализации плагина Application Log Analyzer.

    Args:
        ai_model: Опциональный экземпляр модели ИИ.
        config: Переопределения конфигурации.

    Returns:
        ApplicationLogAnalyzerPlugin: Инициализированный экземпляр плагина.
    """
    return ApplicationLogAnalyzerPlugin(ai_model=ai_model, config=config)