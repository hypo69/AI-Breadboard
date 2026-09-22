# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Restore Manager
# =============================================================================
# Description:
#   Управление точками восстановления Windows (System Restore Points).
#   Позволяет создавать точки восстановления через WMI/PowerShell, получать список
#   существующих точек и проверять статус защиты системы.
#
# Examples:
#   >>> from apps.windows.core.system_restore import WindowsSystemRestoreManager
#   >>> manager = WindowsSystemRestoreManager()
#   >>> result = manager.create_restore_point("Pre-Config Change")
#   >>> print(result["success"])
#   True
#
# File: system_restore.py
# Project: AI-Breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль создания и управления точками восстановления Windows."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import logger



class WindowsSystemRestoreManager:
    """Менеджер точек восстановления Windows (System Restore)."""

    def __init__(self, timeout_seconds: int = 45) -> None:
        """Инициализация менеджера точек восстановления.

        Args:
            timeout_seconds: Таймаут выполнения команд PowerShell в секундах.
        """
        self.timeout_seconds = timeout_seconds

    def check_protection_status(self) -> Dict[str, Any]:
        """Проверка статуса защиты системы (System Protection) на системном диске.

        Returns:
            Dict[str, Any]: Словарь со статусом защиты диска C:.
        """
        ps_cmd = (
            "Get-ComputerRestorePoint -ErrorAction SilentlyContinue | "
            "Select-Object -First 1 | ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            # Если команда выполнилась без ошибок доступа к API, защита доступна
            is_enabled = res.returncode == 0
            return {
                "system_protection_enabled": is_enabled,
                "target_drive": "C:",
                "error": res.stderr.strip() if res.returncode != 0 else None,
            }
        except Exception as ex:
            logger.warning(f"Ошибка проверки статуса защиты системы: {ex}")
            return {
                "system_protection_enabled": False,
                "target_drive": "C:",
                "error": str(ex),
            }

    def list_restore_points(self) -> List[Dict[str, Any]]:
        """Получение списка всех доступных точек восстановления системы.

        Returns:
            List[Dict[str, Any]]: Список словарей с описанием точек восстановления.
        """
        ps_cmd = (
            "Get-ComputerRestorePoint -ErrorAction SilentlyContinue | "
            "Select-Object SequenceNumber, Description, RestorePointType, CreationTime | "
            "ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            if res.returncode != 0 or not res.stdout.strip():
                return []

            data = json.loads(res.stdout.strip())
            if isinstance(data, dict):
                data = [data]

            points: List[Dict[str, Any]] = []
            for item in data:
                raw_time = item.get("CreationTime", "")
                points.append({
                    "sequence_number": item.get("SequenceNumber", 0),
                    "description": item.get("Description", "Unnamed Restore Point"),
                    "restore_point_type": str(item.get("RestorePointType", "MODIFY_SETTINGS")),
                    "creation_time": raw_time,
                })
            return points
        except Exception as ex:
            logger.warning(f"Не удалось получить список точек восстановления: {ex}")
            return []

    def get_shadow_storage_info(self) -> Dict[str, Any]:
        """Получение информации о выделенном пространстве теневых копий (VSS).

        Позволяет оценить доступность места и предотвратить непреднамеренное вытеснение
        старых точек восстановления операционной системой.

        Returns:
            Dict[str, Any]: Сведения о выделенном, используемом и максимальном объеме хранилища.
        """
        ps_cmd = (
            "Get-CimInstance -ClassName Win32_ShadowStorage -ErrorAction SilentlyContinue | "
            "Select-Object AllocatedSpace, UsedSpace, MaxSpace | ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                used = int(data.get("UsedSpace", 0))
                allocated = int(data.get("AllocatedSpace", 0))
                max_space = int(data.get("MaxSpace", 0))
                usage_percent = round((used / max_space * 100), 1) if max_space > 0 else 0.0
                return {
                    "available": True,
                    "used_bytes": used,
                    "allocated_bytes": allocated,
                    "max_bytes": max_space,
                    "usage_percent": usage_percent,
                    "at_risk_of_eviction": usage_percent > 85.0,
                }
        except Exception as ex:
            logger.debug(f"Не удалось получить сведения о теневом хранилище: {ex}")

        return {
            "available": False,
            "used_bytes": 0,
            "allocated_bytes": 0,
            "max_bytes": 0,
            "usage_percent": 0.0,
            "at_risk_of_eviction": False,
        }

    def save_local_state_snapshot(
        self,
        snapshot_id: str,
        data: Dict[str, Any],
        description: str,
        storage_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Сохранение неизменяемого локального снимка состояния (Immutable State Snapshot).

        Гарантирует, что при ограничениях системы на количество или частоту точек
        восстановления существующие состояния не будут перезаписаны или потеряны.

        Args:
            snapshot_id: Уникальный идентификатор снимка (UUID).
            data: Структура сохраненных данных состояния.
            description: Описание снимка.
            storage_dir: Директория хранения (по умолчанию data/state_snapshots).

        Returns:
            Dict[str, Any]: Метаданные сохраненного снимка.
        """
        target_dir = Path(storage_dir or "data/state_snapshots")
        target_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = target_dir / f"snapshot_{snapshot_id}.json"

        # Проверка защиты от перезаписи
        if snapshot_file.exists():
            logger.warning(f"Попытка перезаписи существующего снимка {snapshot_id} отклонена для защиты данных.")
            return {
                "success": False,
                "snapshot_id": snapshot_id,
                "error": "Снимок состояния с таким ID уже существует (перезапись запрещена).",
            }

        payload = {
            "snapshot_id": snapshot_id,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "data": data,
            "immutable": True,
        }

        try:
            with open(snapshot_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Локальный снимок состояния сохранен: {snapshot_file}")
            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "path": str(snapshot_file),
                "created_at": payload["created_at"],
            }
        except Exception as ex:
            logger.error(f"Ошибка сохранения локального снимка: {ex}", exc_info=True)
            return {
                "success": False,
                "snapshot_id": snapshot_id,
                "error": str(ex),
            }

    def create_restore_point(
        self,
        description: str,
        restore_point_type: str = "MODIFY_SETTINGS",
        event_type: str = "BEGIN_SYSTEM_CHANGE",
    ) -> Dict[str, Any]:
        """Создание новой точки восстановления Windows с проверкой лимитов.

        Если в ОС действует лимит частоты или места, существующие точки не замещаются,
        а результат возвращает статус и причину для безопасного fallback.

        Args:
            description: Понятное текстовое описание причины создания точки.
            restore_point_type: Тип точки.
            event_type: Тип события.

        Returns:
            Dict[str, Any]: Результат создания точки с флагом успеха и метаданными.
        """
        clean_desc = description.replace('"', "'").strip()
        if not clean_desc:
            clean_desc = f"AI-Breadboard Parameter Change {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Проверка теневого хранилища
        storage_info = self.get_shadow_storage_info()
        eviction_warning = storage_info.get("at_risk_of_eviction", False)
        if eviction_warning:
            logger.warning(
                f"Внимание: заполнение хранилища теневых копий составляет {storage_info.get('usage_percent')}%."
            )

        logger.info(f"Создание точки восстановления Windows: '{clean_desc}' (Type: {restore_point_type})")

        ps_cmd = (
            f"Checkpoint-Computer -Description \"{clean_desc}\" "
            f"-RestorePointType \"{restore_point_type}\" "
            f"-ErrorAction Stop"
        )

        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )

            if res.returncode == 0:
                logger.info(f"Точка восстановления успешно создана: '{clean_desc}'")
                return {
                    "success": True,
                    "description": clean_desc,
                    "restore_point_type": restore_point_type,
                    "created_at": datetime.now().isoformat(),
                    "storage_info": storage_info,
                    "message": f"Точка восстановления '{clean_desc}' успешно создана.",
                }
            else:
                err_msg = res.stderr.strip() or res.stdout.strip()
                is_freq_limit = "1440 minutes" in err_msg or "frequency" in err_msg.lower()
                logger.warning(f"Ошибка создания точки восстановления Windows: {err_msg}")
                return {
                    "success": False,
                    "description": clean_desc,
                    "error": err_msg,
                    "is_frequency_limited": is_freq_limit,
                    "storage_info": storage_info,
                    "message": (
                        "В системе действует ограничение частоты (1440 мин). Существующие точки сохранены."
                        if is_freq_limit
                        else f"Не удалось создать точку восстановления Windows: {err_msg}"
                    ),
                }
        except subprocess.TimeoutExpired:
            msg = f"Таймаут ({self.timeout_seconds} сек) при создании точки восстановления"
            logger.error(msg)
            return {"success": False, "description": clean_desc, "error": msg, "message": msg}
        except Exception as ex:
            logger.error(f"Исключение при создании точки восстановления: {ex}", exc_info=True)
            return {"success": False, "description": clean_desc, "error": str(ex), "message": str(ex)}

