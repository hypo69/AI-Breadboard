# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Simulation System Data Models
# =============================================================================
# Description:
#   Data models and request/result schemas for synthetic simulation engine.
#
# File: models.py
# Project: ai-breadboard
# Package: src.ai.simulation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class EntityType(str, Enum):
    """Supported simulation entity types."""
    CONTRACT = "contract"
    INVOICE = "invoice"
    ACT = "act"
    PROFILE = "profile"
    CUSTOM = "custom"


@dataclass
class SimulationRequest:
    """Request payload for entity simulation."""
    query: str
    user_id: str
    api_key: str = ""
    entity_type: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResult:
    """Result produced by a simulation generator."""
    entity_type: str
    title: str
    generated_text: str
    structured_data: Dict[str, Any] = field(default_factory=dict)
    is_indexed: bool = False
    error: Optional[str] = None
