"""Фабрика плагина анализатора логов приложения.

Предоставляет точку входа для динамической инициализации плагина
`ApplicationLogAnalyzerPlugin`.
"""
from __future__ import annotations
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