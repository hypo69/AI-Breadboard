# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Boot_Recovery Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.boot_recovery.core.models import BcdEntry
#
#     service = BcdEntry()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.boot_recovery.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BcdEntry(BaseModel):
    """Запись диспетчера загрузки BCD."""
    identifier: str
    description: str = ''
    device: str = ''
    path: str = ''
    is_default: bool = False
    is_current: bool = False
    safemode: Optional[str] = None


class WinReStatus(BaseModel):
    """Состояние среды аварийного восстановления WinRE."""
    enabled: bool = True
    location: str = '\\\\?\\GLOBALROOT\\device\\harddisk0\\partition4\\Recovery\\WindowsRE'
    boot_config_id: str = '{00000000-0000-0000-0000-000000000000}'
    custom_image_configured: bool = False


class BootReport(BaseModel):
    """Сводный отчет о загрузчике и среде восстановления."""
    timeout_seconds: int = 30
    default_os: str = 'Windows 11'
    entries: List[BcdEntry] = Field(default_factory=list)
    winre: WinReStatus = Field(default_factory=WinReStatus)
    secure_boot_enabled: bool = True
    timestamp: str = ''


class BootActionRequest(BaseModel):
    """Запрос действия с загрузчиком или WinRE."""
    action: str
    target: Optional[str] = None
    value: Optional[Any] = None
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'BcdEntry',
    'WinReStatus',
    'BootReport',
    'BootActionRequest',
]
