# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research Application Package Initialization
# =============================================================================
# Description:
#   Инициализация пакета приложения исследования телеметрии.
#   Предоставляет доступ к TelemetryResearchEngine, моделям данных
#   и функции инициализации FastAPI роутера init_router.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Приложение для комплексного исследования данных телеметрии."""

from apps.telemetry_research.engine import TelemetryResearchEngine
from apps.telemetry_research.models import (
    CorrelationMatrixItem,
    DeepResearchReport,
    HypothesisResult,
    ResearchScenarioRequest,
)
from apps.telemetry_research.router import init_router

__all__ = [
    "TelemetryResearchEngine",
    "ResearchScenarioRequest",
    "DeepResearchReport",
    "HypothesisResult",
    "CorrelationMatrixItem",
    "init_router",
]
