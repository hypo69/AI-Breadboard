# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Log Intelligence Pipeline Coordinator
# =============================================================================
# Description:
#   Main entry-point coordinating Data Researcher profiling, Decision Gate
#   strategy selection, and Adaptive RAG storage.
#
# Examples:
#   >>> from apps.windows.log_intelligence.src.pipeline import LogIntelligencePipeline
#   >>> pipeline = LogIntelligencePipeline()
#   >>> result = pipeline.process_events(entries, channel="System")
#
# File: pipeline.py
# Project: AI-Breadboard
# Package: apps.windows.log_intelligence.src
# Class: LogIntelligencePipeline
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .adaptive_rag import AdaptiveLogRAG
from .data_researcher import LogDataResearcher
from .decision_gate import DecisionGate
from .models import DataProfileReport, IngestionDecision, LogEntry


class LogIntelligencePipeline:
    """Единый фасад пайплайна: Data Researcher -> Decision Gate -> Adaptive RAG."""

    def __init__(self, storage_dir: Optional[Any] = None) -> None:
        self.researcher = LogDataResearcher()
        self.gate = DecisionGate()
        self.rag = AdaptiveLogRAG(storage_dir=storage_dir)

    def process_events(self, entries: List[LogEntry], channel: str = "System") -> Dict[str, Any]:
        """Выполнить полный цикл аналитики, принятия решения и адаптивной индексации."""
        # Шаг 1: EDA и профилирование данных
        profile: DataProfileReport = self.researcher.profile_data(entries, channel=channel)

        # Шаг 2: Шлюз принятия решений
        decision: IngestionDecision = self.gate.evaluate(profile)

        # Шаг 3: Целевая индексация RAG
        chunks_created = self.rag.ingest(profile, decision)

        return {
            "channel": channel,
            "profile": {
                "total_events": profile.total_events,
                "unique_templates": profile.unique_templates_count,
                "redundancy_ratio_pct": profile.redundancy_ratio_pct,
                "health_score": profile.health_score,
                "critical_count": profile.critical_count,
                "error_count": profile.error_count,
                "warning_count": profile.warning_count,
                "bursts_count": len(profile.bursts),
                "novel_signatures_count": len(profile.novel_signatures),
            },
            "decision": {
                "strategy": decision.strategy.value,
                "rationale": decision.rationale,
                "chunks_generated": chunks_created,
                "recommended_llm_action": decision.recommended_llm_action,
            },
            "rag_storage_dir": str(self.rag.storage_dir),
            "generated_at": profile.generated_at,
        }

    def search_rag(self, query: str, top_k: int = 5, channel: str = "") -> List[Dict[str, Any]]:
        """Поиск по адаптивным документам RAG."""
        return self.rag.search(query=query, top_k=top_k, channel=channel)
