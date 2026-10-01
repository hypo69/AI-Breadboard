# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Log_Intelligence Src - Models
# =============================================================================
# Description:
#   Enumeration of standard log severity levels.
#
# Usage Examples:
#   Python API:
#     from apps.windows.log_intelligence.src.models import LogSeverity
#
#     service = LogSeverity()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.log_intelligence.src
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Enumeration of standard log severity levels."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional

class LogSeverity(StrEnum):
    """Enumeration of standard log severity levels."""
    CRITICAL = 'Critical'
    ERROR = 'Error'
    WARNING = 'Warning'
    INFORMATION = 'Information'
    VERBOSE = 'Verbose'
    DEBUG = 'Debug'

class IngestionStrategy(StrEnum):
    """Стратегия обработки и индексации данных, выбранная Decision Gate."""
    SNAPSHOT_ONLY = 'snapshot_only'
    INCIDENT_FOCUSED = 'incident_focused'
    NOVELTY_SIGNATURE = 'novelty_signature'
    NOISE_MASKED = 'noise_masked'

@dataclass
class LogEntry:
    """Нормализованная запись журнала событий Windows."""
    timestamp: str = ''
    level: str = LogSeverity.INFORMATION.value
    source: str = ''
    provider: str = ''
    channel: str = ''
    event_id: int = 0
    computer: str = ''
    user: str = ''
    process: str = ''
    process_id: int = 0
    thread_id: int = 0
    service: str = ''
    message: str = ''
    raw_data: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TimeBurst:
    """Временной всплеск частоты событий (Rate Spike)."""
    time_window: str = ''
    event_count: int = 0
    dominant_level: str = 'Information'
    dominant_provider: str = ''
    summary: str = ''

@dataclass
class DataProfileReport:
    """Аналитический профиль массива логов от Data Researcher (EDA)."""
    channel: str = ''
    total_events: int = 0
    unique_templates_count: int = 0
    redundancy_ratio_pct: float = 0.0
    health_score: float = 100.0
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    dominant_noise_provider: str = ''
    bursts: List[TimeBurst] = field(default_factory=list)
    critical_incidents: List[Dict[str, Any]] = field(default_factory=list)
    novel_signatures: List[Dict[str, Any]] = field(default_factory=list)
    top_patterns: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: str = ''

@dataclass
class IngestionDecision:
    """Решение Decision Gate о том, как обрабатывать и индексировать массив."""
    strategy: IngestionStrategy = IngestionStrategy.SNAPSHOT_ONLY
    rationale: str = ''
    chunks_to_generate: int = 0
    target_time_windows: List[str] = field(default_factory=list)
    skip_providers: List[str] = field(default_factory=list)
    recommended_llm_action: str = ''