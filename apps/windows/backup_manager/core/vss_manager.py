# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows VSS Shadow Copy Manager
# =============================================================================
# Description:
#   Интеграция с подсистемой теневых копий томов Windows (Volume Shadow Copies).
#   Чтение существующих моментальных снимков томов и управление ими.
#
# Examples:
#   >>> from apps.windows.backup_manager.core.vss_manager import VssManager
#   >>> vss = VssManager()
#   >>> snapshots = vss.list_snapshots()
#
# File: vss_manager.py
# Project: ai-breadboard
# Package: apps.windows.backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль управления теневыми копиями томов VSS в Windows."""

from __future__ import annotations

import re
import subprocess
from typing import List

from logger import logger
from apps.windows.backup_manager.core.models import VssSnapshot


class VssManager:
    """Менеджер теневых копий томов VSS."""

    def list_snapshots(self) -> List[VssSnapshot]:
        """Возвращает список существующих теневых копий томов через vssadmin.

        Returns:
            List[VssSnapshot]: Список обнаруженных теневых снимков.
        """
        snapshots: List[VssSnapshot] = []
        try:
            cmd = ["vssadmin.exe", "list", "shadows"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                logger.debug(f"vssadmin list shadows завершился с кодом {res.returncode}")
                return snapshots

            raw_text = res.stdout
            # Блоки теневых копий
            blocks = raw_text.split("Shadow Copy Set ID:")
            for block in blocks:
                if not block.strip():
                    continue

                id_match = re.search(r"Shadow Copy ID:\s*({[a-fA-F0-9\-]+})", block)
                vol_match = re.search(r"Original Volume:\s*\(([A-Za-z]:)?\\\)", block) or re.search(r"Original Volume:\s*([^\r\n]+)", block)
                time_match = re.search(r"Creation Time:\s*([^\r\n]+)", block)
                path_match = re.search(r"Shadow Copy Volume Name:\s*([^\r\n]+)", block)

                if id_match:
                    snap_id = id_match.group(1).strip()
                    orig_vol = vol_match.group(1).strip() if vol_match else "Unknown"
                    c_time = time_match.group(1).strip() if time_match else None
                    s_path = path_match.group(1).strip() if path_match else None

                    snapshots.append(
                        VssSnapshot(
                            snapshot_id=snap_id,
                            original_volume=orig_vol,
                            creation_time=c_time,
                            shadow_volume_path=s_path,
                        )
                    )
        except Exception as ex:
            logger.warning(f"Ошибка получения теневых копий VSS: {ex}")

        return snapshots