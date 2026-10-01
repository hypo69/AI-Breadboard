# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Software_Manager Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.software_manager.core.models import InstalledPackage
#
#     service = InstalledPackage()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.software_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InstalledPackage(BaseModel):
    """Информация об установленном пакете ПО."""
    name: str
    package_id: str
    version: str
    available_version: Optional[str] = None
    source: str = 'winget'  # winget, msstore, msi, registry
    install_date: Optional[str] = None


class SoftwareReport(BaseModel):
    """Сводный отчет об установленном ПО."""
    total_packages: int = 0
    updates_available_count: int = 0
    winget_available: bool = True
    packages: List[InstalledPackage] = Field(default_factory=list)
    timestamp: str = ''


class PackageActionRequest(BaseModel):
    """Запрос на установку, обновление или удаление пакета."""
    package_id: str
    action: str  # install, uninstall, upgrade
    version: Optional[str] = None
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'InstalledPackage',
    'SoftwareReport',
    'PackageActionRequest',
]
