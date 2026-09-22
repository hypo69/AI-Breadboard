"""Рабочие процессы для Enterprise Knowledge Platform."""

from apps.enterprise_knowledge.workers.ingestion_worker import IngestionWorker
from apps.enterprise_knowledge.workers.extraction_worker import ExtractionWorker
from apps.enterprise_knowledge.workers.resolution_worker import ResolutionWorker
from apps.enterprise_knowledge.workers.consolidation_worker import ConsolidationWorker

__all__ = ["IngestionWorker", "ExtractionWorker", "ResolutionWorker", "ConsolidationWorker"]
