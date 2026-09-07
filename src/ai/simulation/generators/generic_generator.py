# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Generic Dynamic Simulation Generator
# =============================================================================
# Description:
#   Fallback and dynamic generator for arbitrary mock entities (invoices, acts, profiles, etc.)
#   defined on the fly during dialogue.
#
# File: generic_generator.py
# Project: ai-breadboard
# Package: src.ai.simulation.generators
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import hashlib
import random
from datetime import datetime
from typing import Any, Dict

from src.ai.simulation.base_generator import BaseSimulationGenerator
from src.ai.simulation.models import EntityType, SimulationRequest, SimulationResult
from src.logger import logger


class GenericSimulationGenerator(BaseSimulationGenerator):
    """Fallback generator for arbitrary entity types."""

    @property
    def entity_type(self) -> str:
        """Return the generic entity type."""
        return EntityType.CUSTOM.value

    def can_handle(self, request: SimulationRequest) -> bool:
        """Always returns True as fallback handler."""
        return True

    def _seed(self, user_id: str, query: str) -> int:
        """Compute deterministic seed."""
        key = f"{user_id}_{query.strip().lower()}"
        return int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)

    async def generate(self, request: SimulationRequest) -> SimulationResult:
        """Generate generic simulated response."""
        rng = random.Random(self._seed(request.user_id, request.query))
        doc_id = f"SIM-{rng.randint(10000, 99999)}"
        created_at = datetime.now().strftime("%d.%m.%Y")

        entity_type = request.entity_type or EntityType.CUSTOM.value
        title = f"Документ / Запись #{doc_id}"

        structured_data: Dict[str, Any] = {
            "entity_type": entity_type,
            "document_id": doc_id,
            "created_at": created_at,
            "query": request.query,
            "status": "Подтверждено",
        }

        generated_text = (
            f"### 📋 {title}\n\n"
            f"- **Тип записи:** `{entity_type}`\n"
            f"- **Дата формирования:** {created_at}\n"
            f"- **Запрос:** *«{request.query}»*\n"
            f"- **Статус:** ✅ Актуально\n\n"
            f"> *Запись сгенерирована подсистемой имитации и сохранена в RAG.*"
        )

        logger.info(f"[Simulation] Generated generic entity '{entity_type}' ({doc_id}) for user {request.user_id}")

        return SimulationResult(
            entity_type=entity_type,
            title=title,
            generated_text=generated_text,
            structured_data=structured_data,
            is_indexed=False,
        )
