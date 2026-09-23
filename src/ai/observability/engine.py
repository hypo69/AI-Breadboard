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

from logger import logger
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
        stages: List[Dict[str, Any]] = [
            {
                "stage": "init",
                "title": "Сбор телеметрии",
                "message": "🔌 Получение актуального среза телеметрии и сенсоров хоста...",
                "details": "WMI, LibreHardwareMonitor, системные процессы и ресурсы хранилища",
            },
            {
                "stage": "heuristics",
                "title": "Эвристический анализ",
                "message": "⚙️ Выполнение глубокого эвристического анализа подсистем...",
                "details": "Проверка пороговых значений CPU, RAM, дискового пространства и температурных датчиков",
            },
        ]

        score, anomalies, recommendations = self.evaluate_heuristics(data)
        
        summary_text = (
            f"Health score: {score}/100. "
            f"Detected anomalies: {len(anomalies)}."
        )

        model_name = "Heuristic Analyzer"
        generated_prompt: Optional[str] = None
        raw_response: Optional[str] = None

        if self.chat_model is not None:
            # Генерация сжатого промпта на основе аномалий
            prompt = (
                "Analyze the following detected system anomalies and provide actionable recommendations:\n\n"
                f"Anomalies: {[a.model_dump() for a in anomalies]}\n"
                f"Summary: {summary_text}\n\n"
                "Provide a 2-3 sentence executive assessment and 2 key action recommendations."
            )
            generated_prompt = prompt

            stages.append({
                "stage": "prompt",
                "title": "Формирование промпта",
                "message": "📝 Формирование диагностического контекста и промпта для AI-модели...",
                "details": f"Передано {len(anomalies)} аномалий и текущий индекс здоровья ({score}/100)",
                "generated_prompt": prompt,
            })

            stages.append({
                "stage": "synthesizing",
                "title": "Синтез рекомендаций",
                "message": "🧠 Интеллектуальный синтез анализа через языковую модель...",
                "details": "Генерация экспертной оценки и ключевых мер по оптимизации",
                "generated_prompt": prompt,
            })

            try:
                response = await self.chat_model.ask(prompt)
                raw_response = str(response) if response is not None else None
                if response and isinstance(response, str) and response.strip():
                    summary_text = response.strip()
                    model_name = getattr(self.chat_model, "active_provider", "Unified AI")
            except Exception as ex:
                raw_response = f"Exception: {ex}"
                logger.debug(f"LLM diagnosis skipped, using heuristic fallback: {ex}")
        else:
            stages.append({
                "stage": "heuristics_complete",
                "title": "Завершение анализа",
                "message": "✅ Эвристический аудит завершён без вызова внешней языковой модели",
                "details": "Использован локальный профиль правил",
            })

        return SystemDiagnosticReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            health_score=score,
            summary=summary_text,
            anomalies=anomalies,
            recommendations=recommendations,
            ai_model_used=model_name,
            generated_prompt=generated_prompt,
            raw_response=raw_response,
            stages=stages,
        )
