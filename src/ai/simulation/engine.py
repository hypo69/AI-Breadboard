# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Simulation Engine Core Coordinator
# =============================================================================
# Description:
#   Central coordinator for simulated entity generation, dynamic intent routing,
#   LLM-based enrichment, and automated persistence into user's client RAG memory store.
#
# File: engine.py
# Project: ai-breadboard
# Package: src.ai.simulation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
from typing import Any, List, Optional

from src.ai.gemini.user_query_rag import index_user_query
from src.ai.simulation.base_generator import BaseSimulationGenerator
from src.ai.simulation.generators.contract_generator import ContractSimulationGenerator
from src.ai.simulation.generators.generic_generator import GenericSimulationGenerator
from src.ai.simulation.llm_enricher import enrich_simulation_with_llm
from src.ai.simulation.models import SimulationRequest, SimulationResult
from src.logger import logger


class SimulationEngine:
    """Core engine coordinating entity simulation, LLM enrichment, and client RAG indexing."""

    def __init__(
        self,
        generators: Optional[List[BaseSimulationGenerator]] = None,
        llm_model: Optional[Any] = None,
    ) -> None:
        """Initialize SimulationEngine with default or custom generators and LLM model.

        Args:
            generators: Optional list of generator instances.
            llm_model: Optional default AI model instance for intelligent enrichment.
        """
        self._generators: List[BaseSimulationGenerator] = generators or [
            ContractSimulationGenerator(),
            GenericSimulationGenerator(),
        ]
        self._llm_model: Optional[Any] = llm_model

    @property
    def llm_model(self) -> Optional[Any]:
        """Return connected LLM model."""
        return self._llm_model

    @llm_model.setter
    def llm_model(self, model: Any) -> None:
        """Set or update default LLM model for simulation enrichment."""
        self._llm_model = model

    def register_generator(self, generator: BaseSimulationGenerator, prepend: bool = True) -> None:
        """Register a new simulation generator into the engine.

        Args:
            generator: Generator implementing BaseSimulationGenerator.
            prepend: If True, prioritize this generator over generic fallbacks.
        """
        if prepend:
            self._generators.insert(0, generator)
        else:
            self._generators.append(generator)
        logger.info(f"[SimulationEngine] Registered generator for entity '{generator.entity_type}'")

    def find_generator(self, request: SimulationRequest) -> BaseSimulationGenerator:
        """Find the first matching generator for the given request.

        Args:
            request: Incoming simulation request.

        Returns:
            BaseSimulationGenerator: Matched generator or fallback.
        """
        for gen in self._generators:
            if gen.can_handle(request):
                return gen
        # Fallback to last generator (usually GenericSimulationGenerator)
        return self._generators[-1]

    async def simulate(
        self,
        request: SimulationRequest,
        auto_index: bool = True,
        enrich_with_llm: bool = True,
    ) -> SimulationResult:
        """Execute simulation, optionally enrich via LLM, and index result into client RAG.

        Args:
            request: Simulation request containing query, user_id, and parameters.
            auto_index: If True, persist response into user's personal RAG index.
            enrich_with_llm: If True and an LLM model is available, enrich output.

        Returns:
            SimulationResult: Generated mock document with indexing status.
        """
        if not request.query or not request.query.strip():
            return SimulationResult(
                entity_type="unknown",
                title="Пустой запрос",
                generated_text="",
                is_indexed=False,
                error="Query string is empty",
            )

        try:
            generator = self.find_generator(request)
            result = await generator.generate(request)

            # LLM-based enrichment step
            active_model = request.params.get("llm_model") or self._llm_model
            should_enrich = enrich_with_llm and request.params.get("enrich_with_llm", True)
            if should_enrich and active_model is not None:
                enriched_text = await enrich_simulation_with_llm(
                    model=active_model,
                    entity_type=result.entity_type,
                    raw_text=result.generated_text,
                    structured_data=result.structured_data,
                    query=request.query,
                )
                if enriched_text:
                    result.generated_text = enriched_text

            if auto_index and request.user_id:
                # Perform indexing in worker thread to avoid blocking event loop
                indexed = await asyncio.to_thread(
                    index_user_query,
                    request.user_id,
                    request.api_key,
                    request.query,
                    result.generated_text,
                )
                result.is_indexed = bool(indexed)
                logger.info(
                    f"[SimulationEngine] Simulated entity '{result.entity_type}' indexed={result.is_indexed} "
                    f"for user={request.user_id}"
                )

            return result

        except Exception as ex:
            logger.error(f"[SimulationEngine] Simulation failed for user {request.user_id}: {ex}", ex, False)
            return SimulationResult(
                entity_type="error",
                title="Ошибка симуляции",
                generated_text=f"Произошла ошибка при генерации фиктивных данных: {ex}",
                is_indexed=False,
                error=str(ex),
            )


# Global singleton instance
_DEFAULT_ENGINE: Optional[SimulationEngine] = None


def get_simulation_engine() -> SimulationEngine:
    """Retrieve or initialize global SimulationEngine singleton.

    Returns:
        SimulationEngine: Active simulation engine instance.
    """
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = SimulationEngine()
    return _DEFAULT_ENGINE
