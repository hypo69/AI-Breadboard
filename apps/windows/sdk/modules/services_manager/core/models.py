# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Services_Manager Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.services_manager.core.models import ServiceItem
#
#     service = ServiceItem()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.services_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ServiceItem(BaseModel):
    """Информация о службе Windows."""
    name: str
    display_name: str = ''
    status: str = 'STOPPED'  # RUNNING, STOPPED, PAUSED
    start_type: str = 'Manual'  # Auto, Manual, Disabled
    pid: Optional[int] = None
    binary_path: str = ''
    account: str = 'LocalSystem'
    is_orphaned: bool = False


class ServicesReport(BaseModel):
    """Сводный отчет о службах Windows."""
    total_services: int = 0
    running_services: int = 0
    stopped_services: int = 0
    auto_start_services: int = 0
    orphaned_services_count: int = 0
    services: List[ServiceItem] = Field(default_factory=list)
    timestamp: str = ''


class ServiceActionRequest(BaseModel):
    """Запрос на действие со службой."""
    name: str
    action: str  # start, stop, pause, continue, set_start_type
    start_type: Optional[str] = None
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'ServiceItem',
    'ServicesReport',
    'ServiceActionRequest',
]
