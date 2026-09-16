# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Universal AI Diagnostics Engine
# =============================================================================
# Description:
#   Abstract base for heuristic and AI-driven anomaly detection.
#   Designed to be extensible for system telemetry, cloud logs, or 
#   application metrics.
#
# File: engine.py
# Project: ai-breadboard
# Package: src.ai.observability
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Universal AI-powered diagnostic analyzer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from src.logger import logger
from apps.windows.telemetry.models import AnomalyItem, SystemDiagnosticReport


class DiagnosticEngine(ABC):
    """Abstract base class for diagnostic engines."""

    def __init__(self, chat_model: Optional[Any] = None) -> None:
        self.chat_model = chat_model

    @abstractmethod
    def evaluate_heuristics(self, data: Any) -> Tuple[int, List[AnomalyItem], List[str]]:
        """Run rule-based checks."""
        pass

    async def diagnose(self, data: Any) -> SystemDiagnosticReport:
        """Run heuristic and AI LLM analysis."""
        score, anomalies, recommendations = self.evaluate_heuristics(data)
        
        summary_text = (
            f"Health score: {score}/100. "
            f"Detected anomalies: {len(anomalies)}."
        )

        model_name = "Heuristic Analyzer"
        if self.chat_model is not None:
            try:
                # Генерация сжатого промпта на основе аномалий
                prompt = (
                    "Analyze the following detected system anomalies and provide actionable recommendations:\n\n"
                    f"Anomalies: {[a.model_dump() for a in anomalies]}\n"
                    f"Summary: {summary_text}\n\n"
                    "Provide a 2-3 sentence executive assessment and 2 key action recommendations."
                )

                response = await self.chat_model.ask(prompt)
                if response and isinstance(response, str) and response.strip():
                    summary_text = response.strip()
                    model_name = getattr(self.chat_model, "active_provider", "Unified AI")
            except Exception as ex:
                logger.debug(f"LLM diagnosis skipped, using heuristic fallback: {ex}")

        return SystemDiagnosticReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            health_score=score,
            summary=summary_text,
            anomalies=anomalies,
            recommendations=recommendations,
            ai_model_used=model_name,
        )
