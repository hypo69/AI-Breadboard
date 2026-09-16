# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Log Intelligence Data Models
# =============================================================================
# Description:
#   Unified data structures for data profiling, EDA statistics,
#   decision gate outcomes, and targeted RAG indexing chunks.
#
# File: models.py
# Project: AI-Breadboard
# Package: apps.windows.log_intelligence.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional


class LogSeverity(StrEnum):
    """Enumeration of standard log severity levels."""
    CRITICAL = "Critical"
    ERROR = "Error"
    WARNING = "Warning"
    INFORMATION = "Information"
    VERBOSE = "Verbose"
    DEBUG = "Debug"


class IngestionStrategy(StrEnum):
    """Стратегия обработки и индексации данных, выбранная Decision Gate."""
    SNAPSHOT_ONLY = "snapshot_only"            # Здоровая система: только агрегированная сводка (0 сырых событий)
    INCIDENT_FOCUSED = "incident_focused"      # Сбой/аномалия: точечная векторизация каскада вокруг сбоя
    NOVELTY_SIGNATURE = "novelty_signature"    # Новая неизвестная сигнатура: обогащение базы знаний
    NOISE_MASKED = "noise_masked"              # Массовый шторм повторов: 1 сжатый шаблонный дайджест


@dataclass
class LogEntry:
    """Нормализованная запись журнала событий Windows."""
    timestamp: str = ""
    level: str = LogSeverity.INFORMATION.value
    source: str = ""
    provider: str = ""
    channel: str = ""
    event_id: int = 0
    computer: str = ""
    user: str = ""
    process: str = ""
    process_id: int = 0
    thread_id: int = 0
    service: str = ""
    message: str = ""
    raw_data: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeBurst:
    """Временной всплеск частоты событий (Rate Spike)."""
    time_window: str = ""
    event_count: int = 0
    dominant_level: str = "Information"
    dominant_provider: str = ""
    summary: str = ""


@dataclass
class DataProfileReport:
    """Аналитический профиль массива логов от Data Researcher (EDA)."""
    channel: str = ""
    total_events: int = 0
    unique_templates_count: int = 0
    redundancy_ratio_pct: float = 0.0          # Степень избыточности/дублирования (0 - 100%)
    health_score: float = 100.0                # Индекс здоровья системы (0 - 100)
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    dominant_noise_provider: str = ""
    bursts: List[TimeBurst] = field(default_factory=list)
    critical_incidents: List[Dict[str, Any]] = field(default_factory=list)
    novel_signatures: List[Dict[str, Any]] = field(default_factory=list)
    top_patterns: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""


@dataclass
class IngestionDecision:
    """Решение Decision Gate о том, как обрабатывать и индексировать массив."""
    strategy: IngestionStrategy = IngestionStrategy.SNAPSHOT_ONLY
    rationale: str = ""
    chunks_to_generate: int = 0
    target_time_windows: List[str] = field(default_factory=list)
    skip_providers: List[str] = field(default_factory=list)
    recommended_llm_action: str = ""
