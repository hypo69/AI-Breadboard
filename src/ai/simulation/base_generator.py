# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Base Simulation Generator Interface
# =============================================================================
# Description:
#   Abstract base class defining the contract for entity simulation generators.
#
# File: base_generator.py
# Project: ai-breadboard
# Package: src.ai.simulation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.ai.simulation.models import SimulationRequest, SimulationResult


class BaseSimulationGenerator(ABC):
    """Abstract interface for all simulation generators."""

    @property
    @abstractmethod
    def entity_type(self) -> str:
        """Return the primary entity type supported by this generator."""
        pass

    @abstractmethod
    def can_handle(self, request: SimulationRequest) -> bool:
        """Determine whether this generator can handle the simulation request.

        Args:
            request: Incoming simulation request.

        Returns:
            bool: True if this generator matches the request, False otherwise.
        """
        pass

    @abstractmethod
    async def generate(self, request: SimulationRequest) -> SimulationResult:
        """Generate simulated entity content.

        Args:
            request: Simulation request containing query, user_id, and parameters.

        Returns:
            SimulationResult: Generated mock entity data and presentation text.
        """
        pass
