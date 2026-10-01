# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Telemetry Bridge
# =============================================================================
# Description:
#   Мост интеграции между подсистемой телеметрии Windows (IncidentDetector,
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.telemetry_bridge import TelemetryWikiBridge
#
#     service = TelemetryWikiBridge()
#
# File: telemetry_bridge.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Мост интеграции между подсистемой телеметрии Windows (IncidentDetector,"""

from typing import Any, Dict, List, Optional
from logger import logger
from .engine import WikiLLMEngine
from .extractor import ArtifactExtractor
from .models import ArtifactInput, ResolutionResult


class TelemetryWikiBridge:
    """Мост между телеметрией Windows и базой знаний WikiLLM."""

    def __init__(self, engine: WikiLLMEngine) -> None:
        """Инициализирует мост телеметрии.

        Args:
            engine: Экземпляр движка WikiLLMEngine.
        """
        self.engine = engine

    async def enrich_incident(
        self, incident_data: Dict[str, Any], sync_gemini: bool = False
    ) -> Dict[str, Any]:
        """Обогащает инцидент телеметрии структурированными знаниями из WikiLLM.

        Args:
            incident_data: Словарь с описанием инцидента.
            sync_gemini: Флаг синхронного вызова Gemini при отсутствии данных в кэше.

        Returns:
            Обогащенный словарь инцидента с секцией 'wiki_knowledge'.
        """
        artifacts = ArtifactExtractor.from_incident(incident_data)
        enriched_knowledge: List[Dict[str, Any]] = []
        all_causes: List[str] = []
        all_actions: List[Dict[str, Any]] = []

        co_occurring_keys = [
            self.engine.exact_resolver.storage.db_path
            for _ in [1]
        ]  # placeholder if needed

        extracted_keys = []
        for art in artifacts:
            res: ResolutionResult = await self.engine.resolve(
                art,
                sync_gemini=sync_gemini,
                record_observation=True,
            )
            extracted_keys.append(res.canonical_key)
            if res.entity:
                item_data = {
                    "canonical_key": res.canonical_key,
                    "name": res.entity.name,
                    "summary": res.entity.summary,
                    "severity": res.entity.severity,
                    "confidence": res.confidence,
                    "lookup_level": res.lookup_level.value,
                }
                if res.entity.diagnostic_info:
                    item_data["possible_causes"] = res.entity.diagnostic_info.possible_causes
                    item_data["remediation_steps"] = [
                        step.model_dump() for step in res.entity.diagnostic_info.remediation_steps
                    ]
                    all_causes.extend(res.entity.diagnostic_info.possible_causes)
                    all_actions.extend([s.model_dump() for s in res.entity.diagnostic_info.remediation_steps])

                enriched_knowledge.append(item_data)

        # Добавляем историю наблюдений и обогащенную сводку
        incident_copy = dict(incident_data)
        incident_copy["wiki_enrichment"] = {
            "resolved_entities": enriched_knowledge,
            "suggested_causes": list(dict.fromkeys(all_causes)),
            "recommended_actions": all_actions,
            "total_artifacts_analyzed": len(artifacts),
        }

        return incident_copy

    async def ingest_event_stream(
        self, events: List[Dict[str, Any]], sync_gemini: bool = False
    ) -> int:
        """Принимает поток событий и отправляет их на нормализацию и разрешение.

        Args:
            events: Список словарей событий Windows.
            sync_gemini: Флаг синхронного обращения к Gemini (False для массовой телеметрии).

        Returns:
            Число успешно обработанных событий.
        """
        count = 0
        for ev in events:
            art = ArtifactExtractor.from_event_dict(ev)
            await self.engine.resolve(art, sync_gemini=sync_gemini, record_observation=True)
            count += 1
        return count
