# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Performance_Tracing Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.performance_tracing.core.models import PerformanceCounterSample
#
#     service = PerformanceCounterSample()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.performance_tracing.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PerformanceCounterSample(BaseModel):
    """Моментальное значение счетчика производительности."""
    path: str
    value: float
    unit: str = '%'
    timestamp: str = ''


class DataCollectorSet(BaseModel):
    """Набор сборщиков данных ETW / Performance Counters."""
    name: str
    status: str = 'Stopped'  # Running, Stopped
    collector_type: str = 'PerformanceCounter'
    output_location: Optional[str] = None


class PerformanceTracingReport(BaseModel):
    """Сводный отчет о производительности хоста."""
    cpu_usage_percent: float = 0.0
    ram_usage_percent: float = 0.0
    disk_queue_length: float = 0.0
    network_utilization_kbps: float = 0.0
    collectors: List[DataCollectorSet] = Field(default_factory=list)
    counter_samples: List[PerformanceCounterSample] = Field(default_factory=list)
    timestamp: str = ''


class CollectorActionRequest(BaseModel):
    """Запрос на запуск или остановку сборщика трассировки."""
    collector_name: str
    action: str  # start, stop, create, delete
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'PerformanceCounterSample',
    'DataCollectorSet',
    'PerformanceTracingReport',
    'CollectorActionRequest',
]
