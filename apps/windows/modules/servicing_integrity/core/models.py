# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Servicing_Integrity Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.servicing_integrity.core.models import WindowsFeature
#
#     service = WindowsFeature()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.servicing_integrity.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WindowsFeature(BaseModel):
    """Компонент Windows (Windows Optional Feature)."""
    name: str
    state: str = 'Enabled'
    restart_required: bool = False


class IntegrityReport(BaseModel):
    """Сводный отчет целостности образа и защищенных файлов."""
    sfc_status: str = 'Clean'
    sfc_last_scan: str = ''
    dism_component_store_status: str = 'Healthy'
    dism_cleanup_recommended: bool = False
    corrupted_files_count: int = 0
    features_count: int = 0
    features: List[WindowsFeature] = Field(default_factory=list)
    timestamp: str = ''


class ServicingActionRequest(BaseModel):
    """Запрос на сканирование или восстановление целостности."""
    tool: str = 'dism'  # sfc or dism
    action: str = 'check_health'
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'WindowsFeature',
    'IntegrityReport',
    'ServicingActionRequest',
]
