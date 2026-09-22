# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Diagnostician
# =============================================================================
# Description:
#   Интеллектуальный диагност Windows, объединяющий собранные факты аудита
#   и рассуждения языковых моделей (LLM) для формирования экспертных отчетов.
#
# Examples:
#   >>> from apps.windows.ai.diagnostician import WindowsAIDiagnostician
#   >>> diagnostician = WindowsAIDiagnostician()
#   >>> report = await diagnostician.diagnose_system(mode="full")
#
# File: diagnostician.py
# Project: ai-breadboard
# Package: apps.windows.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""AI-диагност для комплексного анализа состояния Windows."""

from __future__ import annotations

from typing import Any, Dict, Optional

from logger import logger
from apps.windows.ai.prompt_templates import build_audit_prompt, build_system_prompt
from apps.windows.core.models import FullAuditReport
from apps.windows.core.root_cause_engine import RootCauseEngine


class WindowsAIDiagnostician:
    """Диагностический AI-сервис Windows."""

    def __init__(self, chat_model: Optional[Any] = None) -> None:
        """Инициализация AI-диагноста.

        Args:
            chat_model: Опциональная модель LLM.
        """
        self.chat_model = chat_model
        self.engine = RootCauseEngine()

    async def diagnose_system(self, mode: str = "full") -> FullAuditReport:
        """Выполнение аудита с AI-интерпретацией результатов.

        Args:
            mode: Режим проверки (full, quick, security, performance, drivers, clean, postinstall).

        Returns:
            FullAuditReport: Сводный отчет с AI-заключением.
        """
        report = self.engine.run_full_audit(mode=mode)
        
        # Генерация базового AI-заключения на основе фактов
        findings_count = report.health_score.total_findings
        score = report.health_score.score
        
        summary_text = (
            f"Аудит системы завершен в режиме '{mode}'. Индекс здоровья: {score}/100 ({report.health_score.status_label}). "
            f"Обнаружено аномалий и рекомендаций: {findings_count}. "
            f"Критических: {report.health_score.critical_count}, Требующих внимания: {report.health_score.medium_count}."
        )

        if self.chat_model and hasattr(self.chat_model, "ask"):
            try:
                domains_dict = {k: v.to_dict() for k, v in report.domains.items()}
                prompt = build_audit_prompt(domains_dict, score)
                sys_prompt = build_system_prompt()
                ai_res = await self.chat_model.ask(prompt, system_prompt=sys_prompt)
                if ai_res:
                    summary_text = ai_res
            except Exception as e:
                logger.warning(f"Ошибка вызова LLM для аудита: {e}")

        report.ai_summary = summary_text
        return report
