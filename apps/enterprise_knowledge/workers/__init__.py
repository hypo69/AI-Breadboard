# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Enterprise_Knowledge Workers -   Init  
# =============================================================================
# Description:
#   Рабочие процессы для Enterprise Knowledge Platform.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.enterprise_knowledge.workers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Рабочие процессы для Enterprise Knowledge Platform."""

from apps.enterprise_knowledge.workers.ingestion_worker import IngestionWorker
from apps.enterprise_knowledge.workers.extraction_worker import ExtractionWorker
from apps.enterprise_knowledge.workers.resolution_worker import ResolutionWorker
from apps.enterprise_knowledge.workers.consolidation_worker import ConsolidationWorker
__all__ = ['IngestionWorker', 'ExtractionWorker', 'ResolutionWorker', 'ConsolidationWorker']