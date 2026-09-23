# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Diagnostic Data Models
# =============================================================================
# Description:
#   Common models for diagnostic results used by DiagnosticEngine.
#
# File: models.py
# Project: ai-breadboard
# Package: src.ai.observability
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnomalyItem(BaseModel):
    """Specific detected anomaly or performance bottleneck."""

    subsystem: str = Field(..., description="Subsystem (e.g., CPU, Trading, Network)")
    severity: str = Field(default="warning", description="Severity level: info, warning, critical")
    title: str = Field(..., description="Brief anomaly summary")
    description: str = Field(..., description="Detailed diagnostic description")


class SystemDiagnosticReport(BaseModel):
    """AI-powered diagnostic audit report."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Audit timestamp",
    )
    health_score: int = Field(default=100, description="System health score (0-100)")
    summary: str = Field(..., description="High-level health and performance summary")
    anomalies: List[AnomalyItem] = Field(default_factory=list, description="List of detected anomalies")
    recommendations: List[str] = Field(default_factory=list, description="Actionable optimization suggestions")
    ai_model_used: str = Field(default="heuristic", description="AI Model identifier or heuristic engine")
    generated_prompt: Optional[str] = Field(default=None, description="Exact prompt sent to AI model")
    raw_response: Optional[str] = Field(default=None, description="Raw response text from AI provider")
    stages: List[Dict[str, Any]] = Field(default_factory=list, description="Step-by-step audit stages")
