# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Task_Scheduler Core - Models
# =============================================================================
# Description:
#   Модели данных для модуля планировщика задач Windows (Task Scheduler).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.task_scheduler.core.models import ScheduledTaskItem
#
#     service = ScheduledTaskItem()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.task_scheduler.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 12:35:00
# =============================================================================

from __future__ import annotations
"""Модели данных для модуля планировщика задач Windows (Task Scheduler)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScheduledTaskItem(BaseModel):
    """Информация о запланированном задании."""
    task_path: str = ''
    task_name: str = ''
    name: str = ''
    state: str = 'Ready'  # Ready, Running, Disabled, Queued, Unknown
    status: str = 'Ready'
    enabled: bool = True
    next_run_time: Optional[str] = None
    last_run_time: Optional[str] = None
    last_task_result: int = 0
    author: str = ''
    action: str = ''
    schedule_type: str = 'Custom'


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
    task_path: Optional[str] = None
    task_name: Optional[str] = None
    action: str  # run, stop, enable, disable, delete, schtasks_run, etc.
    dry_run: bool = False
    confirmed_by_user: bool = True


__all__ = [
    'ScheduledTaskItem',
    'TaskSchedulerReport',
    'TaskActionRequest',
]
