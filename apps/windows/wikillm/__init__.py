# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm -   Init  
# =============================================================================
# Description:
#   Инициализатор пакета WikiLLM (Progressive Knowledge Acquisition + Retrieval)
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Инициализатор пакета WikiLLM (Progressive Knowledge Acquisition + Retrieval)"""

from .code_indexer import CodeKnowledgeIndexer
from .config import WikiLLMConfig, load_config
from .engine import WikiLLMEngine
from .extractor import ArtifactExtractor
from .models import (
    ArtifactInput,
    ArtifactType,
    Claim,
    CodeKnowledge,
    DiagnosticKnowledge,
    Evidence,
    KnowledgeEntity,
    KnowledgeSource,
    LookupLevel,
    ObservationRecord,
    ResolutionAction,
    ResolutionResult,
)
from .normalizer import CanonicalKeyNormalizer
from .router import init_router, router
from .storage import WikiStorage
from .telemetry_bridge import TelemetryWikiBridge

__all__ = [
    "WikiLLMEngine",
    "WikiStorage",
    "WikiLLMConfig",
    "load_config",
    "ArtifactExtractor",
    "CanonicalKeyNormalizer",
    "CodeKnowledgeIndexer",
    "TelemetryWikiBridge",
    "router",
    "init_router",
    "ArtifactInput",
    "ArtifactType",
    "KnowledgeEntity",
    "KnowledgeSource",
    "LookupLevel",
    "ResolutionResult",
    "ResolutionAction",
    "Claim",
    "Evidence",
    "ObservationRecord",
    "DiagnosticKnowledge",
    "CodeKnowledge",
]
