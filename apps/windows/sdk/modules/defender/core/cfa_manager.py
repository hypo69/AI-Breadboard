# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Defender Core - Cfa Manager
# =============================================================================
# Description:
#   Модуль управления защитой от программ-вымогателей Controlled Folder Access.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.defender.core.cfa_manager import ControlledFolderAccessManager
#
#     service = ControlledFolderAccessManager()
#
# File: cfa_manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 04:11:30
# =============================================================================

from __future__ import annotations
"""Модуль управления защитой от программ-вымогателей Controlled Folder Access."""

import os
from typing import List, Optional
from logger import logger
from apps.windows.sdk.modules.defender.core.defender_service import DefenderService
from apps.windows.sdk.modules.defender.core.models import ControlledFolderAccessInfo, ProtectionState

class ControlledFolderAccessManager:
    """Менеджер Controlled Folder Access (CFA)."""
    DEFAULT_PROTECTED_DIRS = [os.path.expanduser('~\\Documents'), os.path.expanduser('~\\Pictures'), os.path.expanduser('~\\Videos'), os.path.expanduser('~\\Music'), os.path.expanduser('~\\Desktop'), os.path.expanduser('~\\Favorites')]

    def __init__(self, defender_service: Optional[DefenderService]=None) -> None:
        """Инициализация CFA менеджера."""
        self._service = defender_service or DefenderService()

    def get_cfa_status(self) -> ControlledFolderAccessInfo:
        """Получение текущего состояния защиты папок от вымогателей.

        Returns:
            ControlledFolderAccessInfo: Информация о CFA, папках и доверенных программах.
        """
        pref_data = self._service._run_powershell_json('Get-MpPreference')
        if not pref_data:
            return ControlledFolderAccessInfo(enabled=False, mode=ProtectionState.DISABLED, protected_folders=self.DEFAULT_PROTECTED_DIRS, allowed_applications=[])
        cfa_val = pref_data.get('EnableControlledFolderAccess', 0)
        mode_map = {0: (False, ProtectionState.DISABLED), 1: (True, ProtectionState.ENABLED), 2: (True, ProtectionState.AUDIT), 3: (True, ProtectionState.WARN)}
        enabled, mode = mode_map.get(cfa_val, (False, ProtectionState.DISABLED))
        custom_folders = pref_data.get('ControlledFolderAccessProtectedFolders') or []
        if isinstance(custom_folders, str):
            custom_folders = [custom_folders]
        all_folders = list(dict.fromkeys(self.DEFAULT_PROTECTED_DIRS + custom_folders))
        allowed_apps = pref_data.get('ControlledFolderAccessAllowedApplications') or []
        if isinstance(allowed_apps, str):
            allowed_apps = [allowed_apps]
        return ControlledFolderAccessInfo(enabled=enabled, mode=mode, protected_folders=all_folders, allowed_applications=allowed_apps)