# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Task_Scheduler Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.task_scheduler.core.models import ScheduledTaskItem
#
#     service = ScheduledTaskItem()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.task_scheduler.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScheduledTaskItem(BaseModel):
    """Информация о запланированном задании."""
    task_path: str
    task_name: str
    state: str = 'Ready'  # Ready, Running, Disabled
    next_run_time: Optional[str] = None
    last_run_time: Optional[str] = None
    last_task_result: int = 0
    author: str = ''
    action: str = ''


class TaskSchedulerReport(BaseModel):
    """Сводный отчет о заданиях Task Scheduler."""
    total_tasks: int = 0
    ready_tasks: int = 0
    running_tasks: int = 0
    disabled_tasks: int = 0
    tasks: List[ScheduledTaskItem] = Field(default_factory=list)
    timestamp: str = ''


class TaskActionRequest(BaseModel):
    """Запрос на управление заданием планировщика."""
    task_path: str
    action: str  # run, stop, enable, disable, delete
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'ScheduledTaskItem',
    'TaskSchedulerReport',
    'TaskActionRequest',
]
