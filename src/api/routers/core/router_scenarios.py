# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Scenarios Bridge Module
# =============================================================================
# Description:
#   Модуль-мост роутера сценариев, перенаправляющий вызовы на нативный роутер apps.windows.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_scenarios import init_router
#
#     router = init_router()
#
# File: router_scenarios.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 16:35:00
# =============================================================================

"""Модуль-мост роутера сценариев для интеграции apps.windows.api.routers.router_scenarios в ядро."""

from apps.windows.api.routers.router_scenarios import (
    AVAILABLE_SCENARIOS,
    ScenarioChatRequest,
    ScenarioChatResponse,
    ScenarioCreatedSkillInfo,
    ScenarioExecuteFixRequest,
    ScenarioExecuteFixResponse,
    ScenarioItem,
    ScenarioQuestionsConfig,
    ScenarioRemediationActionInfo,
    ScenarioRunRequest,
    ScenarioRunResult,
    ScenarioSaveApprovedResponseRequest,
    ScenarioSaveApprovedResponseResponse,
    ScenarioSaveSkillRequest,
    ScenarioStepResult,
    ScenarioToolPlanInfo,
    init_router,
)

router = init_router()

__all__ = [
    "router",
    "init_router",
    "AVAILABLE_SCENARIOS",
    "ScenarioQuestionsConfig",
    "ScenarioRunResult",
    "ScenarioRunRequest",
    "ScenarioItem",
    "ScenarioStepResult",
    "ScenarioChatRequest",
    "ScenarioChatResponse",
    "ScenarioCreatedSkillInfo",
    "ScenarioToolPlanInfo",
    "ScenarioSaveSkillRequest",
    "ScenarioRemediationActionInfo",
    "ScenarioExecuteFixRequest",
    "ScenarioExecuteFixResponse",
    "ScenarioSaveApprovedResponseRequest",
    "ScenarioSaveApprovedResponseResponse",
]
