# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Controlled Folder Access (CFA) Manager
# =============================================================================
# Description:
#   Аудит и управление функцией Controlled Folder Access (защита от вымогателей).
#   Сбор списка защищенных пользовательских директорий и доверенных приложений.
#
# File: cfa_manager.py
# Project: ai-breadboard
# Package: apps.windows_defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль управления защитой от программ-вымогателей Controlled Folder Access."""

from __future__ import annotations

import os
from typing import List, Optional

from logger import logger
from apps.windows_defender.core.defender_service import DefenderService
from apps.windows_defender.core.models import ControlledFolderAccessInfo, ProtectionState


class ControlledFolderAccessManager:
    """Менеджер Controlled Folder Access (CFA)."""

    DEFAULT_PROTECTED_DIRS = [
        os.path.expanduser(r"~\Documents"),
        os.path.expanduser(r"~\Pictures"),
        os.path.expanduser(r"~\Videos"),
        os.path.expanduser(r"~\Music"),
        os.path.expanduser(r"~\Desktop"),
        os.path.expanduser(r"~\Favorites"),
    ]

    def __init__(self, defender_service: Optional[DefenderService] = None) -> None:
        """Инициализация CFA менеджера."""
        self._service = defender_service or DefenderService()

    def get_cfa_status(self) -> ControlledFolderAccessInfo:
        """Получение текущего состояния защиты папок от вымогателей.

        Returns:
            ControlledFolderAccessInfo: Информация о CFA, папках и доверенных программах.
        """
        pref_data = self._service._run_powershell_json("Get-MpPreference")
        if not pref_data:
            return ControlledFolderAccessInfo(
                enabled=False,
                mode=ProtectionState.DISABLED,
                protected_folders=self.DEFAULT_PROTECTED_DIRS,
                allowed_applications=[],
            )

        cfa_val = pref_data.get("EnableControlledFolderAccess", 0)
        mode_map = {
            0: (False, ProtectionState.DISABLED),
            1: (True, ProtectionState.ENABLED),  # Block
            2: (True, ProtectionState.AUDIT),
            3: (True, ProtectionState.WARN),
        }
        enabled, mode = mode_map.get(cfa_val, (False, ProtectionState.DISABLED))

        # Сбор дополнительных защищенных папок
        custom_folders = pref_data.get("ControlledFolderAccessProtectedFolders") or []
        if isinstance(custom_folders, str):
            custom_folders = [custom_folders]

        all_folders = list(dict.fromkeys(self.DEFAULT_PROTECTED_DIRS + custom_folders))

        # Сбор доверенных приложений
        allowed_apps = pref_data.get("ControlledFolderAccessAllowedApplications") or []
        if isinstance(allowed_apps, str):
            allowed_apps = [allowed_apps]

        return ControlledFolderAccessInfo(
            enabled=enabled,
            mode=mode,
            protected_folders=all_folders,
            allowed_applications=allowed_apps,
        )
