# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Enterprise_Knowledge Workers - Consolidation Worker
# =============================================================================
# Description:
#   Рабочий процесс консолидации знаний.
#
# Usage Examples:
#   Python API:
#     from apps.enterprise_knowledge.workers.consolidation_worker import ConsolidationWorker
#
#     service = ConsolidationWorker()
#
# File: consolidation_worker.py
# Project: ai-breadboard
# Package: apps.enterprise_knowledge.workers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Рабочий процесс консолидации знаний."""

from typing import Any
from apps.enterprise_knowledge.storage import KnowledgeStore
from apps.enterprise_knowledge.knowledge.consolidation import KnowledgeConsolidator

class ConsolidationWorker:
    """Рабочий процесс для консолидации знаний и проверки противоречий."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store
        self.consolidator = KnowledgeConsolidator(store)

    async def run_consolidation(self) -> dict[str, Any]:
        """Запустить консолидацию всех новых фактов."""
        return self.consolidator.run_batch_consolidation()