# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar Tests - Unit & Integration Tests
# =============================================================================
# Description:
#   Тесты для TaskbarController, SettingsManager, WindowManager, HistoryManager (telemetry.db) и REST API.
#
# Usage Examples:
#   pytest apps/windows/modules/taskbar/tests/test_taskbar.py
#
# File: test_taskbar.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.taskbar.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:58:00
# =============================================================================

from __future__ import annotations
"""Модульные и интеграционные тесты для подсистемы Taskbar & Windows Controller."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import MagicMock, patch

from apps.windows.sdk.modules.taskbar.core.app_manager import TaskbarAppManager
from apps.windows.sdk.modules.taskbar.core.command_registry import (
    TaskbarCommandMetadata,
    get_command_by_id,
    get_taskbar_command_catalog,
)
from apps.windows.sdk.modules.taskbar.core.history_manager import TaskbarHistoryManager
from apps.windows.sdk.modules.taskbar.core.manager import TaskbarController
from apps.windows.sdk.modules.taskbar.core.models import (
    AppLaunchRequest,
    AppPinRequest,
    CommandExecutionRequest,
    CommandExecutionResponse,
    PinnedAppItem,
    TaskbarOverlayRequest,
    TaskbarProgressRequest,
    TaskbarSettings,
    TaskbarSettingsUpdate,
    TaskbarSummaryReport,
    WindowBatchActionRequest,
    WindowItem,
    WindowMoveRequest,
    WindowRect,
)
from apps.windows.sdk.modules.taskbar.core.settings_manager import TaskbarSettingsManager
from apps.windows.sdk.modules.taskbar.core.window_manager import WindowManager
from apps.windows.sdk.modules.taskbar.router import init_router, router, set_controller


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Фикстура временного файла базы данных telemetry.db."""
    return tmp_path / "test_telemetry.db"


@pytest.fixture
def controller(temp_db: Path) -> TaskbarController:
    """Фикстура создания TaskbarController с изолированной telemetry.db."""
    hist = TaskbarHistoryManager(db_path=temp_db)
    return TaskbarController(history_mgr=hist)


@pytest.fixture
def client(controller: TaskbarController) -> TestClient:
    """Фикстура TestClient для тестирования REST API."""
    set_controller(controller)
    app = FastAPI()
    app.include_router(init_router(controller))
    return TestClient(app)



def test_models_validation():
    """Проверка создания и валидации моделей Pydantic."""
    rect = WindowRect(left=10, top=20, right=810, bottom=620, width=800, height=600)
    assert rect.width == 800
    assert rect.height == 600

    win = WindowItem(
        hwnd=12345,
        title="Тестовое окно",
        process_id=456,
        process_name="notepad.exe",
        class_name="Notepad",
        is_visible=True,
        is_minimized=False,
        is_maximized=False,
        is_foreground=True,
        rect=rect,
    )
    assert win.hwnd == 12345
    assert win.title == "Тестовое окно"


def test_history_manager_record_and_rollback(temp_db: Path):
    """Проверка записи действий в telemetry.db и выполнения отката."""
    hist = TaskbarHistoryManager(db_path=temp_db)
    rec_id = hist.record_action(
        command_id="TASKBAR.SET_ALIGNMENT",
        category="taskbar",
        action_type="set_alignment",
        previous_state={"alignment": 0},
        new_state={"alignment": 1},
        details={"applied": True},
        status="SUCCESS",
    )
    assert rec_id > 0

    history = hist.get_history(limit=10)
    assert len(history) == 1
    assert history[0]["command_id"] == "TASKBAR.SET_ALIGNMENT"
    assert history[0]["previous_state"]["alignment"] == 0

    # Проверка отката с мокированием
    mock_ctrl = MagicMock()
    mock_ctrl.update_settings.return_value = {"status": "SUCCESS"}
    res_rb = hist.rollback(rec_id, mock_ctrl)
    assert res_rb["status"] == "SUCCESS"

    # Повторный откат должен быть заблокирован
    res_repeat = hist.rollback(rec_id, mock_ctrl)
    assert res_repeat["status"] == "ERROR"


def test_controller_history_and_rollback(controller: TaskbarController):
    """Проверка сквозного аудита изменений через TaskbarController."""
    with patch.object(controller.settings_mgr, "_write_registry_dword", return_value=True):
        with patch.object(controller.settings_mgr, "notify_settings_changed"):
            res = controller.update_settings(TaskbarSettingsUpdate(alignment=1))
            assert res["status"] == "SUCCESS"
            assert "history_id" in res

            history = controller.get_history(limit=5)
            assert len(history) >= 1
            assert history[0]["category"] == "taskbar"


def test_fastapi_history_endpoints(client: TestClient):
    """Интеграционное тестирование эндпоинтов истории и Rollback."""
    # 1. Summary
    resp_sum = client.get("/api/v1/taskbar/summary")
    assert resp_sum.status_code == 200

    # 2. History
    resp_hist = client.get("/api/v1/taskbar/history")
    assert resp_hist.status_code == 200
    assert isinstance(resp_hist.json(), list)

    # 3. Settings update (creates history)
    with patch("winreg.CreateKey"):
        with patch("winreg.SetValueEx"):
            with patch("winreg.OpenKey"):
                with patch("winreg.QueryValueEx", return_value=(0, 4)):
                    resp_up = client.put("/api/v1/taskbar/settings", json={"alignment": 1})
                    assert resp_up.status_code == 200

    # 4. History check after update
    resp_hist2 = client.get("/api/v1/taskbar/history")
    assert resp_hist2.status_code == 200
    records = resp_hist2.json()
    assert len(records) >= 1
    last_id = records[0]["id"]

    # 5. Rollback endpoint
    resp_rb = client.post(f"/api/v1/taskbar/history/{last_id}/rollback")
    assert resp_rb.status_code == 200
    assert resp_rb.json()["status"] == "SUCCESS"

    # 6. Rollback last
    resp_rbl = client.post("/api/v1/taskbar/history/rollback-last")
    assert resp_rbl.status_code in (200, 400)
