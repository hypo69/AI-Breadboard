# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for SafeSystemParamManager
# =============================================================================
# Description:
#   Тестирование безопасного менеджера параметров системы:
#   - Автоматическое создание точек восстановления при чувствительных параметрах
#   - Пропуск создания точек при безопасных параметрах
#   - Симуляция изменений (Dry-Run)
#   - Ведение журнала аудита и откат (Rollback)
#   - Интеграция с FastAPI роутером System Control Center
#
# File: test_system_param_manager.py
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для менеджера безопасного изменения параметров системы."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.system_control_center.router import init_router
from apps.windows.core.models import RiskLevel
from apps.windows.core.system_param_manager import (
    ParameterCategory,
    ParameterType,
    SafeSystemParamManager,
    SystemParameter,
)
from apps.windows.core.system_restore import WindowsSystemRestoreManager


@pytest.fixture
def mock_restore_manager() -> MagicMock:
    """Фикстура мока менеджера точек восстановления."""
    mock = MagicMock(spec=WindowsSystemRestoreManager)
    mock.create_restore_point.return_value = {
        "success": True,
        "description": "Mock Restore Point",
        "restore_point_type": "MODIFY_SETTINGS",
        "created_at": "2026-09-16T22:00:00",
        "message": "Точка восстановления успешно создана.",
    }
    mock.list_restore_points.return_value = [
        {
            "sequence_number": 1,
            "description": "Initial Checkpoint",
            "restore_point_type": "CHECKPOINT",
            "creation_time": "2026-09-16 10:00:00",
        }
    ]
    mock.save_local_state_snapshot.side_effect = lambda snapshot_id, data, description, storage_dir=None: {
        "success": True,
        "snapshot_id": snapshot_id,
        "path": f"/mock/snapshot_{snapshot_id}.json",
        "created_at": "2026-09-16T22:00:00",
    }
    return mock



@pytest.fixture
def temp_history_file(tmp_path: Path) -> Path:
    """Фикстура временного файла истории параметров."""
    return tmp_path / "test_param_history.json"


@pytest.fixture
def param_manager(mock_restore_manager: MagicMock, temp_history_file: Path) -> SafeSystemParamManager:
    """Фикстура менеджера параметров с изолированным хранилищем."""
    return SafeSystemParamManager(restore_manager=mock_restore_manager, history_file=temp_history_file)


class TestSafeSystemParamManager:
    """Набор тестов для SafeSystemParamManager."""

    def test_catalog_initialization(self, param_manager: SafeSystemParamManager) -> None:
        """Проверка наличия базовых параметров в каталоге."""
        params = param_manager.list_parameters()
        assert len(params) >= 7

        param_ids = [p["param_id"] for p in params]
        assert "sec.uac_level" in param_ids
        assert "srv.wuauserv_startup" in param_ids
        assert "platform.pprint_indent" in param_ids

    def test_sensitivity_classification(self, param_manager: SafeSystemParamManager) -> None:
        """Проверка правильности классификации чувствительных и безопасных параметров."""
        uac = param_manager.get_parameter("sec.uac_level")
        assert uac is not None
        assert uac.is_sensitive is True
        assert uac.risk == RiskLevel.CRITICAL

        pprint = param_manager.get_parameter("platform.pprint_indent")
        assert pprint is not None
        assert pprint.is_sensitive is False
        assert pprint.risk == RiskLevel.SAFE

    def test_preview_sensitive_parameter(self, param_manager: SafeSystemParamManager) -> None:
        """Проверка предварительного просмотра чувствительного параметра."""
        with patch.object(param_manager, "get_current_value", return_value=1):
            res = param_manager.preview_change("sec.uac_level", 0)

        assert res["success"] is True
        assert res["is_sensitive"] is True
        assert res["will_create_restore_point"] is True
        assert res["new_value"] == 0
        assert "Уровень контроля учетных записей" in res["name"]

    def test_preview_safe_parameter(self, param_manager: SafeSystemParamManager) -> None:
        """Проверка предварительного просмотра безопасного параметра."""
        with patch.object(param_manager, "get_current_value", return_value=6):
            res = param_manager.preview_change("platform.pprint_indent", 4)

        assert res["success"] is True
        assert res["is_sensitive"] is False
        assert res["will_create_restore_point"] is False
        assert res["risk"] == "safe"

    def test_apply_sensitive_parameter_triggers_restore_point(
        self,
        param_manager: SafeSystemParamManager,
        mock_restore_manager: MagicMock,
    ) -> None:
        """Проверка автоматического вызова создания точки восстановления при чувствительном параметре."""
        with patch.object(param_manager, "_write_parameter", return_value=True):
            result = param_manager.apply_change("sec.uac_level", 0)

        assert result["status"] == "SUCCESS"
        assert result["is_sensitive"] is True
        assert result["restore_point"] is not None
        assert result["restore_point"]["success"] is True
        assert result["local_snapshot"]["success"] is True
        mock_restore_manager.create_restore_point.assert_called_once()

    def test_apply_parameter_guarantees_immutable_local_snapshot_even_if_system_restore_limited(
        self,
        param_manager: SafeSystemParamManager,
        mock_restore_manager: MagicMock,
    ) -> None:
        """Проверка гарантии неизменяемого снимка состояния даже если создание точки Windows заблокировано лимитом."""
        mock_restore_manager.create_restore_point.return_value = {
            "success": False,
            "description": "RP limited",
            "is_frequency_limited": True,
            "message": "В системе действует ограничение частоты (1440 мин). Существующие точки сохранены.",
        }

        with patch.object(param_manager, "_write_parameter", return_value=True):
            result = param_manager.apply_change("sec.uac_level", 0)

        assert result["status"] == "SUCCESS"
        assert result["restore_point"]["is_frequency_limited"] is True
        assert result["local_snapshot"]["success"] is True
        # Локальный снимок гарантирует сохранность состояния
        assert result["local_snapshot"]["snapshot_id"] == result["change_id"]

    def test_apply_safe_parameter_skips_restore_point(
        self,
        param_manager: SafeSystemParamManager,
        mock_restore_manager: MagicMock,
    ) -> None:
        """Проверка пропуска создания точки восстановления при безопасном параметре."""
        with patch.object(param_manager, "_write_parameter", return_value=True):
            result = param_manager.apply_change("platform.pprint_indent", 4)

        assert result["status"] == "SUCCESS"
        assert result["is_sensitive"] is False
        assert result["restore_point"] is None
        assert result["local_snapshot"]["success"] is True
        mock_restore_manager.create_restore_point.assert_not_called()


    def test_history_and_rollback_workflow(
        self,
        param_manager: SafeSystemParamManager,
    ) -> None:
        """Проверка цикла сохранения истории и успешного отката (rollback)."""
        with patch.object(param_manager, "get_current_value", return_value=1), \
             patch.object(param_manager, "_write_parameter", return_value=True):
            res = param_manager.apply_change("sec.uac_level", 0)

        change_id = res["change_id"]
        history = param_manager.get_history()
        assert len(history) == 1
        assert history[0]["change_id"] == change_id
        assert history[0]["rolled_back"] is False

        # Выполняем откат
        with patch.object(param_manager, "_write_parameter", return_value=True):
            rb_res = param_manager.rollback_change(change_id)

        assert rb_res["status"] == "SUCCESS"
        assert rb_res["restored_value"] == 1

        # Повторный откат должен быть заблокирован
        rb_repeat = param_manager.rollback_change(change_id)
        assert rb_repeat["status"] == "ERROR"
        assert "уже было отменено" in rb_repeat["message"]


class TestSystemControlRouter:
    """Тестирование FastAPI эндпоинтов System Control Center."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Фикстура тестового клиента FastAPI."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(init_router())
        return TestClient(app)

    def test_get_restore_points_endpoint(self, client: TestClient) -> None:
        """Тест GET /api/system-control/restore-points."""
        response = client.get("/api/system-control/restore-points")
        assert response.status_code == 200
        data = response.json()
        assert "restore_points" in data

    def test_list_params_endpoint(self, client: TestClient) -> None:
        """Тест GET /api/system-control/params."""
        response = client.get("/api/system-control/params")
        assert response.status_code == 200
        data = response.json()
        assert "parameters" in data
        assert data["total"] > 0

    def test_preview_param_endpoint(self, client: TestClient) -> None:
        """Тест POST /api/system-control/params/preview."""
        payload = {"param_id": "sec.uac_level", "new_value": 0}
        response = client.post("/api/system-control/params/preview", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["is_sensitive"] is True
        assert data["will_create_restore_point"] is True

    @patch("apps.windows.core.system_param_manager.SafeSystemParamManager.apply_change")
    def test_apply_param_endpoint(self, mock_apply: MagicMock, client: TestClient) -> None:
        """Тест POST /api/system-control/params/apply."""
        mock_apply.return_value = {
            "status": "SUCCESS",
            "change_id": "1234-uuid",
            "param_id": "sec.uac_level",
            "param_name": "UAC",
            "old_value": 1,
            "new_value": 0,
            "is_sensitive": True,
            "restore_point": {"success": True, "description": "Test RP"},
            "message": "Параметр успешно изменен.",
        }
        payload = {"param_id": "sec.uac_level", "new_value": 0}
        response = client.post("/api/system-control/params/apply", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["is_sensitive"] is True
        assert data["restore_point"]["success"] is True

    def test_get_restore_policy_config_endpoint(self, client: TestClient) -> None:
        """Тест GET /api/system-control/restore-points/config."""
        response = client.get("/api/system-control/restore-points/config")
        assert response.status_code == 200
        data = response.json()
        assert "max_points" in data
        assert "schedule_trigger" in data

    @patch("apps.windows.core.system_restore.WindowsSystemRestoreManager.save_policy")
    def test_update_restore_policy_config_endpoint(self, mock_save: MagicMock, client: TestClient) -> None:
        """Тест POST /api/system-control/restore-points/config."""
        mock_save.return_value = {
            "success": True,
            "config": {"max_points": 7, "max_storage_size": "15%"},
            "message": "Политика обновлена",
        }
        payload = {
            "max_points": 7,
            "max_storage_size": "15%",
            "schedule_trigger": "weekly",
            "schedule_time": "02:00",
        }
        response = client.post("/api/system-control/restore-points/config", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["config"]["max_points"] == 7

    @patch("apps.windows.core.system_restore.WindowsSystemRestoreManager.prune_old_restore_points")
    def test_prune_restore_points_endpoint(self, mock_prune: MagicMock, client: TestClient) -> None:
        """Тест POST /api/system-control/restore-points/prune."""
        mock_prune.return_value = {
            "success": True,
            "deleted_count": 2,
            "target_keep": 5,
            "remaining_count": 5,
        }
        payload = {"keep_count": 5}
        response = client.post("/api/system-control/restore-points/prune", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 2

