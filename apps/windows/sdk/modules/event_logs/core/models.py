# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Event_Logs Core - Models
# =============================================================================
# Description:
#   Модели данных для модуля управления журналами событий Windows и Log Intelligence.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.event_logs.core.models import EventLogChannel, IntelligenceSearchRequest
#
#     service = EventLogChannel(name='System')
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.event_logs.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 02:28:00
# =============================================================================

from __future__ import annotations
"""Модели данных для модуля управления журналами событий Windows и Log Intelligence."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventLogChannel(BaseModel):
    """Информация о канале журнала событий."""
    name: str
    enabled: bool = True
    record_count: int = 0
    size_bytes: int = 0
    channel_type: str = 'Admin'


class EventLogEntry(BaseModel):
    """Запись события Windows."""
    channel: str
    event_id: int
    level: str = 'Information'  # Critical, Error, Warning, Information
    provider_name: str = ''
    time_created: str = ''
    message: str = ''


class EventLogReport(BaseModel):
    """Сводный отчет о журналах событий."""
    total_channels: int = 0
    critical_events_24h: int = 0
    error_events_24h: int = 0
    warning_events_24h: int = 0
    channels: List[EventLogChannel] = Field(default_factory=list)
    recent_errors: List[EventLogEntry] = Field(default_factory=list)
    timestamp: str = ''


class EventLogActionRequest(BaseModel):
    """Запрос на очистку или экспорт журнала."""
    channel_name: str
    action: str  # clear, export
    export_path: Optional[str] = None
    dry_run: bool = True
    confirmed_by_user: bool = False


class IntelligenceSearchRequest(BaseModel):
    """Запрос семантического/гибридного поиска по адаптивному RAG-индексу логов."""
    query: str = Field(..., description='Поисковый запрос на русском или английском языке')
    top_k: int = Field(5, ge=1, le=50, description='Максимальное количество результатов')
    channel: str = Field('', description='Фильтр по имени канала (опционально)')


class IntelligenceProfileSummary(BaseModel):
    """Сводный профиль EDA анализа массива логов."""
    channel: str
    total_events: int
    unique_templates: int
    redundancy_ratio_pct: float
    health_score: float
    critical_count: int
    error_count: int
    warning_count: int
    bursts_count: int
    novel_signatures_count: int


class IntelligenceDecisionSummary(BaseModel):
    """Решение Decision Gate о стратегии обработки."""
    strategy: str
    rationale: str
    chunks_generated: int
    recommended_llm_action: str


class IntelligenceProcessResponse(BaseModel):
    """Ответ полного цикла Log Intelligence (EDA -> Gate -> RAG)."""
    channel: str
    profile: IntelligenceProfileSummary
    decision: IntelligenceDecisionSummary
    rag_storage_dir: str
    generated_at: str


__all__ = [
    'EventLogChannel',
    'EventLogEntry',
    'EventLogReport',
    'EventLogActionRequest',
    'IntelligenceSearchRequest',
    'IntelligenceProfileSummary',
    'IntelligenceDecisionSummary',
    'IntelligenceProcessResponse',
]
