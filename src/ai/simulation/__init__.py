# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Simulation System Package Init
# =============================================================================
# Description:
#   Root package init for AI Breadboard simulation and synthetic data generation system.
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.ai.simulation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from src.ai.simulation.base_generator import BaseSimulationGenerator
from src.ai.simulation.engine import SimulationEngine, get_simulation_engine
from src.ai.simulation.generators.contract_generator import ContractSimulationGenerator
from src.ai.simulation.generators.generic_generator import GenericSimulationGenerator
from src.ai.simulation.llm_enricher import enrich_simulation_with_llm
from src.ai.simulation.models import EntityType, SimulationRequest, SimulationResult

__all__ = [
    "BaseSimulationGenerator",
    "ContractSimulationGenerator",
    "EntityType",
    "GenericSimulationGenerator",
    "SimulationEngine",
    "SimulationRequest",
    "SimulationResult",
    "enrich_simulation_with_llm",
    "get_simulation_engine",
]
