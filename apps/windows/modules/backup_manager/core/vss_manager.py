# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Backup_Manager Core - Vss Manager
# =============================================================================
# Description:
#   Модуль управления теневыми копиями томов VSS в Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.backup_manager.core.vss_manager import VssManager
#
#     service = VssManager()
#
# File: vss_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 21:50:00
# =============================================================================

from __future__ import annotations
"""Модуль управления теневыми копиями томов VSS в Windows."""

import json
import re
import subprocess
from typing import List
from logger import logger
from apps.windows.modules.backup_manager.core.models import VssSnapshot

class VssManager:
    """Менеджер теневых копий томов VSS."""

    def list_snapshots(self) -> List[VssSnapshot]:
        """Возвращает список существующих теневых копий томов через vssadmin.

        Returns:
            List[VssSnapshot]: Список обнаруженных теневых снимков.
        """
        snapshots: List[VssSnapshot] = []
        try:
            cmd = ['vssadmin.exe', 'list', 'shadows']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                logger.debug(f'vssadmin list shadows завершился с кодом {res.returncode}')
                return snapshots
            raw_text = res.stdout
            blocks = raw_text.split('Shadow Copy Set ID:')
            for block in blocks:
                if not block.strip():
                    continue
                id_match = re.search('Shadow Copy ID:\\s*({[a-fA-F0-9\\-]+})', block)
                vol_match = re.search('Original Volume:\\s*\\(([A-Za-z]:)?\\\\\\)', block) or re.search('Original Volume:\\s*([^\\r\\n]+)', block)
                time_match = re.search('Creation Time:\\s*([^\\r\\n]+)', block)
                path_match = re.search('Shadow Copy Volume Name:\\s*([^\\r\\n]+)', block)
                if id_match:
                    snap_id = id_match.group(1).strip()
                    orig_vol = vol_match.group(1).strip() if vol_match else 'Unknown'
                    c_time = time_match.group(1).strip() if time_match else None
                    s_path = path_match.group(1).strip() if path_match else None
                    snapshots.append(VssSnapshot(snapshot_id=snap_id, original_volume=orig_vol, creation_time=c_time, shadow_volume_path=s_path))
        except Exception as ex:
            logger.warning(f'Ошибка получения теневых копий VSS: {ex}')
        return snapshots

    def create_snapshot(self, volume: str) -> VssSnapshot:
        """Создает теневую копию тома через WMI ``Win32_ShadowCopy.Create`` (ClientAccessible).

        Args:
            volume: Том, например ``C:/``.

        Returns:
            VssSnapshot: Созданный снимок с ``DeviceObject`` в ``shadow_volume_path``.

        Raises:
            PermissionError: Недостаточно прав (нужен администратор).
            RuntimeError: WMI вернул ошибку или недоступен.
        """
        script = (
            "$r = Invoke-CimMethod -ClassName Win32_ShadowCopy -MethodName Create "
            f"-Arguments @{{Volume='{volume}'; Context='ClientAccessible'}}; "
            "if ($r.ReturnValue -ne 0) { @{rc=[int]$r.ReturnValue} | ConvertTo-Json -Compress; exit 0 }; "
            "$s = Get-CimInstance Win32_ShadowCopy -Filter \"ID='$($r.ShadowID)'\"; "
            "@{rc=0; id=$r.ShadowID; dev=$s.DeviceObject} | ConvertTo-Json -Compress"
        )
        res = subprocess.run(['powershell.exe', '-NoProfile', '-Command', script], capture_output=True, text=True, timeout=60)
        out = res.stdout.strip()
        if res.returncode != 0 or not out:
            if 'denied' in res.stderr.lower() or 'отказано' in res.stderr.lower():
                raise PermissionError(res.stderr.strip())
            raise RuntimeError(f'Не удалось создать VSS-снимок: {res.stderr.strip()}')
        data = json.loads(out)
        if data['rc'] != 0:
            # Коды Win32_ShadowCopy.Create: 2 — отказ в доступе
            if data['rc'] == 2:
                raise PermissionError('E_ACCESSDENIED')
            raise RuntimeError(f"Win32_ShadowCopy.Create вернул код {data['rc']}")
        return VssSnapshot(snapshot_id=data['id'], original_volume=volume, shadow_volume_path=data['dev'])

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Удаляет теневую копию по идентификатору (``vssadmin delete shadows``).

        Returns:
            bool: True, если снимок удален.
        """
        res = subprocess.run(['vssadmin.exe', 'delete', 'shadows', f'/shadow={snapshot_id}', '/quiet'], capture_output=True, text=True, timeout=30)
        return res.returncode == 0
