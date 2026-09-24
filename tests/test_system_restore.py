# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for WindowsSystemRestoreManager
# =============================================================================
# Description:
#   Тестирование создания и листинга точек восстановления Windows,
#   обработки ошибок PowerShell и WMI, таймаутов и статуса защиты.
#
# File: test_system_restore.py
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для менеджера точек восстановления Windows."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from apps.windows.core.system_restore import WindowsSystemRestoreManager



class TestWindowsSystemRestoreManager:
    """Набор тестов для класса WindowsSystemRestoreManager."""

    def test_init_defaults(self) -> None:
        """Проверка значений по умолчанию при инициализации."""
        mgr = WindowsSystemRestoreManager(timeout_seconds=30)
        assert mgr.timeout_seconds == 30

    @patch("subprocess.run")
    def test_check_protection_status_enabled(self, mock_run: MagicMock) -> None:
        """Проверка успешного определения включенной защиты системы."""
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = json.dumps({"SequenceNumber": 1, "Description": "Test RP"})
        mock_res.stderr = ""
        mock_run.return_value = mock_res

        mgr = WindowsSystemRestoreManager()
        status = mgr.check_protection_status()

        assert status["system_protection_enabled"] is True
        assert status["target_drive"] == "C:"
        assert status["error"] is None

    @patch("subprocess.run")
    def test_check_protection_status_disabled(self, mock_run: MagicMock) -> None:
        """Проверка определения отключенной защиты системы при ошибке."""
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = ""
        mock_res.stderr = "System Protection is disabled"
        mock_run.return_value = mock_res

        mgr = WindowsSystemRestoreManager()
        status = mgr.check_protection_status()

        assert status["system_protection_enabled"] is False
        assert status["target_drive"] == "C:"
        assert "disabled" in status["error"]

    @patch("subprocess.run")
    def test_list_restore_points_success(self, mock_run: MagicMock) -> None:
        """Проверка парсинга списка точек восстановления."""
        mock_points = [
            {
                "SequenceNumber": 10,
                "Description": "Windows Update Baseline",
                "RestorePointType": "APPLICATION_INSTALL",
                "CreationTime": "2026-09-15 10:00:00",
            },
            {
                "SequenceNumber": 11,
                "Description": "AI-Breadboard Pre-Config",
                "RestorePointType": "MODIFY_SETTINGS",
                "CreationTime": "2026-09-16 12:00:00",
            },
        ]
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = json.dumps(mock_points)
        mock_run.return_value = mock_res

        mgr = WindowsSystemRestoreManager()
        points = mgr.list_restore_points()

        assert len(points) == 2
        assert points[0]["sequence_number"] == 10
        assert points[0]["description"] == "Windows Update Baseline"
        assert points[1]["sequence_number"] == 11
        assert points[1]["restore_point_type"] == "MODIFY_SETTINGS"

    @patch("subprocess.run")
    def test_list_restore_points_empty_on_failure(self, mock_run: MagicMock) -> None:
        """Проверка возврата пустого списка при сбое команды."""
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = ""
        mock_res.stderr = "Access Denied"
        mock_run.return_value = mock_res

        mgr = WindowsSystemRestoreManager()
        points = mgr.list_restore_points()

        assert points == []

    @patch("subprocess.run")
    def test_create_restore_point_success(self, mock_run: MagicMock) -> None:
        """Проверка успешного создания контрольной точки восстановления."""
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = ""
        mock_res.stderr = ""
        mock_run.return_value = mock_res

        mgr = WindowsSystemRestoreManager()
        result = mgr.create_restore_point("Pre-UAC Modification", "MODIFY_SETTINGS")

        assert result["success"] is True
        assert result["description"] == "Pre-UAC Modification"
        assert result["restore_point_type"] == "MODIFY_SETTINGS"
        assert "успешно создана" in result["message"]

    @patch("subprocess.run")
    def test_create_restore_point_failure_with_frequency_limit(self, mock_run: MagicMock) -> None:
        """Проверка обработки ограничения частоты создания точек (1440 минут) без замещения существующих точек."""
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = ""
        mock_res.stderr = "A new system restore point cannot be created because one has already been created within the past 1440 minutes."
        mock_run.return_value = mock_res

        mgr = WindowsSystemRestoreManager()
        result = mgr.create_restore_point("Test RP")

        assert result["success"] is False
        assert result["is_frequency_limited"] is True
        assert "Существующие точки сохранены" in result["message"]

    @patch("subprocess.run")
    def test_get_shadow_storage_info_detection(self, mock_run: MagicMock) -> None:
        """Проверка анализа емкости хранилища теневых копий VSS и предупреждения о риске вытеснения."""
        mock_data = {
            "AllocatedSpace": 10737418240,  # 10 GB
            "UsedSpace": 9663676416,        # 9 GB (90%)
            "MaxSpace": 10737418240,        # 10 GB
        }
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = json.dumps(mock_data)
        mock_run.return_value = mock_res

        mgr = WindowsSystemRestoreManager()
        info = mgr.get_shadow_storage_info()

        assert info["available"] is True
        assert info["usage_percent"] == 90.0
        assert info["at_risk_of_eviction"] is True

    def test_save_local_state_snapshot_immutability(self, tmp_path: Path) -> None:
        """Проверка создания и защиты от перезаписи локальных снимков состояния."""
        mgr = WindowsSystemRestoreManager()
        storage = str(tmp_path / "snapshots")
        
        # 1. Первичное сохранение
        res1 = mgr.save_local_state_snapshot(
            snapshot_id="snap-100",
            data={"param": "uac", "value": 1},
            description="Initial snapshot",
            storage_dir=storage,
        )
        assert res1["success"] is True
        assert Path(res1["path"]).exists()

        # 2. Попытка перезаписать существующий снимок должна быть отклонена
        res2 = mgr.save_local_state_snapshot(
            snapshot_id="snap-100",
            data={"param": "uac", "value": 0},
            description="Overwriting attempt",
            storage_dir=storage,
        )
        assert res2["success"] is False
        assert "перезапись запрещена" in res2["error"]

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="powershell", timeout=10))
    def test_create_restore_point_timeout(self, mock_run: MagicMock) -> None:
        """Проверка обработки таймаута при создании точки восстановления."""
        mgr = WindowsSystemRestoreManager(timeout_seconds=10)
        result = mgr.create_restore_point("Timeout RP")

        assert result["success"] is False
        assert "Таймаут" in result["error"]

    @patch("subprocess.run")
    def test_set_shadow_storage_max_size(self, mock_run: MagicMock) -> None:
        """Проверка изменения лимита дискового пространства теневых копий."""
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Successfully resized the shadow copy storage association"
        mock_res.stderr = ""
        mock_run.return_value = mock_res

        mgr = WindowsSystemRestoreManager()
        res = mgr.set_shadow_storage_max_size(drive="C:", max_size="15%")

        assert res["success"] is True
        assert res["max_size"] == "15%"
        assert res["drive"] == "C:"

    def test_get_and_set_policy_config(self, tmp_path: Path) -> None:
        """Проверка чтения и сохранения политики хранения и расписания."""
        policy_file = str(tmp_path / "system_restore_policy.json")
        mgr = WindowsSystemRestoreManager(policy_file=policy_file)

        # Проверка дефолтных настроек
        cfg = mgr.get_policy_config()
        assert cfg["max_points"] == 5
        assert cfg["auto_prune"] is True
        assert cfg["schedule_trigger"] == "daily"

        # Проверка обновления политики
        with patch.object(mgr, "set_shadow_storage_max_size", return_value={"success": True, "max_size": "20%"}):
            with patch.object(mgr, "set_schedule_config", return_value={"success": True}):
                res = mgr.save_policy(
                    max_points=10,
                    auto_prune=True,
                    max_storage_size="20%",
                    schedule_trigger="weekly",
                    schedule_time="04:00",
                    frequency_limit_minutes=0,
                )
                assert res["success"] is True
                assert res["config"]["max_points"] == 10
                assert res["config"]["schedule_trigger"] == "weekly"

        # Проверка персистентности в файле
        saved_cfg = mgr.get_policy_config()
        assert saved_cfg["max_points"] == 10
        assert saved_cfg["schedule_trigger"] == "weekly"

    @patch("subprocess.run")
    def test_prune_old_restore_points(self, mock_run: MagicMock) -> None:
        """Проверка удаления старых точек восстановления при превышении лимита."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Deleted shadow copies", stderr="")
        mgr = WindowsSystemRestoreManager()

        # Мокаем список из 6 точек
        mock_points = [
            {"sequence_number": i, "description": f"RP {i}", "restore_point_type": "MODIFY_SETTINGS", "creation_time": f"2026-09-0{i} 10:00:00"}
            for i in range(1, 7)
        ]
        with patch.object(mgr, "list_restore_points", return_value=mock_points):
            res = mgr.prune_old_restore_points(keep_count=3)
            assert res["success"] is True
            assert res["deleted_count"] == 3
            assert res["target_keep"] == 3


