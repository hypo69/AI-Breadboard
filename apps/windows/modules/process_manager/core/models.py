# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Process_Manager Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.process_manager.core.models import ProcessItem
#
#     service = ProcessItem()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.process_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProcessItem(BaseModel):
    """Информация о запущенном процессе."""
    pid: int
    name: str
    username: Optional[str] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    num_threads: int = 1
    create_time: str = ''
    exe_path: Optional[str] = None
    command_line: Optional[str] = None


class ProcessReport(BaseModel):
    """Сводный отчет о процессах хоста."""
    total_processes: int = 0
    total_threads: int = 0
    total_memory_used_mb: float = 0.0
    top_cpu_processes: List[ProcessItem] = Field(default_factory=list)
    top_memory_processes: List[ProcessItem] = Field(default_factory=list)
    processes: List[ProcessItem] = Field(default_factory=list)
    timestamp: str = ''


class ProcessKillRequest(BaseModel):
    """Запрос на завершение процесса."""
    pid: int
    kill_tree: bool = False
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'ProcessItem',
    'ProcessReport',
    'ProcessKillRequest',
]
