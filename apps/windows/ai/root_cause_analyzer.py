# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Root Cause Analyzer
# =============================================================================
# Description:
#   AI-анализатор первопричин сбоев и замедлений Windows по пользовательским
#   описаниям инцидентов и собранным фактам телеметрии.
#
# Examples:
#   >>> from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer
#   >>> analyzer = WindowsAIRootCauseAnalyzer()
#   >>> res = await analyzer.analyze_incident("Тормозит после установки игры")
#
# File: root_cause_analyzer.py
# Project: ai-breadboard
# Package: apps.windows.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""AI-анализатор первопричин системных проблем Windows."""

from __future__ import annotations

from typing import Any, Optional

from logger import logger
from apps.windows.ai.prompt_templates import build_root_cause_prompt, build_system_prompt
from apps.windows.core.models import InvestigationReport
from apps.windows.core.root_cause_engine import RootCauseEngine


class WindowsAIRootCauseAnalyzer:
    """Интеллектуальный анализатор инцидентов."""

    def __init__(self, chat_model: Optional[Any] = None) -> None:
        """Инициализация анализатора инцидентов."""
        self.chat_model = chat_model
        self.engine = RootCauseEngine()

    async def analyze_incident(self, symptom: str) -> InvestigationReport:
        """Расследование инцидента с AI-интерпретацией.

        Args:
            symptom: Описание симптома проблемы.

        Returns:
            InvestigationReport: Результат расследования с гипотезой и планом устранения.
        """
        report = self.engine.investigate(symptom)

        if self.chat_model and hasattr(self.chat_model, "ask"):
            try:
                prompt = build_root_cause_prompt(symptom, report.evidence_chain)
                sys_prompt = build_system_prompt()
                ai_res = await self.chat_model.ask(prompt, system_prompt=sys_prompt)
                if ai_res:
                    report.ai_explanation = ai_res
            except Exception as e:
                logger.warning(f"Ошибка вызова LLM для анализа инцидента: {e}")

        return report
