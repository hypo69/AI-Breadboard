# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Event_Logs Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.event_logs.core.models import EventLogChannel
#
#     service = EventLogChannel()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.event_logs.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

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


__all__ = [
    'EventLogChannel',
    'EventLogEntry',
    'EventLogReport',
    'EventLogActionRequest',
]
