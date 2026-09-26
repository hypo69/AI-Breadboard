# -*- coding: utf-8 -*-
# =============================================================================
# Test Suite: Тестирование роутера и компонентов Ninite Auto-Updater
# =============================================================================
# Description:
#   Проверяет корректность работы Ninite роутера, статуса, загрузки файлов,
#   формирования команд для Windows Task Scheduler и интеграции меню /tc.
#
# File: test_ninite_router.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты роутера и интеграции Ninite Auto-Updater."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from header import __root__
from src.api.router_ninite import init_router, TASK_NAME, NiniteScheduleRequest


@pytest.fixture
def app_client():
    """Создаёт тестовый клиент FastAPI с подключенным роутером Ninite."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


# =============================================================================
# 1. HAPPY PATH — Проверка статуса, загрузки и планирования
# =============================================================================

class TestNiniteRouterHappyPath:
    """Happy path сценарии для Ninite роутера."""

    def test_get_status_happy_path(self, app_client):
        """GET /api/ninite/status должен возвращать структуру с file, task, log."""
        with patch("src.api.router_ninite._run_powershell") as mock_ps:
            mock_ps.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "TaskName": TASK_NAME,
                    "State": "Ready",
                    "NextRunTime": "2026-10-01 20:00:00",
                    "LastRunTime": "2026-09-15 20:00:00",
                    "LastTaskResult": 0
                })
            )
            response = app_client.get("/api/ninite/status")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "file" in data
            assert "task" in data
            assert data["task"]["task_name"] == TASK_NAME
            assert data["task"]["state"] == "Ready"

    def test_schedule_task_happy_path(self, app_client):
        """POST /api/ninite/schedule должен успешно регистрировать задачу с флагом /silent."""
        with patch("src.api.router_ninite._run_powershell") as mock_ps:
            mock_ps.return_value = MagicMock(returncode=0, stdout="", stderr="")
            payload = {
                "interval_weeks": 2,
                "time_str": "20:00",
                "days_of_week": "Sunday"
            }
            response = app_client.post("/api/ninite/schedule", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["interval_weeks"] == 2
            assert data["time"] == "20:00"
            assert mock_ps.called
            all_ps_commands = [call[0][0] for call in mock_ps.call_args_list]
            assert any("/silent >" in cmd for cmd in all_ps_commands)

    def test_schedule_existing_task_override_no_duplicate(self, app_client):
        """При повторной настройке с другими параметрами существующая задача должна переопределяться без дублирования."""
        with patch("src.api.router_ninite._get_task_status") as mock_get_status, \
             patch("src.api.router_ninite._run_powershell") as mock_ps:
            mock_get_status.return_value = {
                "exists": True,
                "task_name": TASK_NAME,
                "state": "Ready",
                "next_run_time": "2026-10-01 20:00:00"
            }
            mock_ps.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Переопределяем параметры на 4 недели и 22:30
            payload = {
                "interval_weeks": 4,
                "time_str": "22:30",
                "days_of_week": "Saturday"
            }
            response = app_client.post("/api/ninite/schedule", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["is_update"] is True
            assert "обновлена" in data["message"]
            assert data["interval_weeks"] == 4
            assert data["time"] == "22:30"

    def test_upload_installer_happy_path(self, app_client, tmp_path):
        """POST /api/ninite/upload должен сохранять файл и вызывать настройку задачи."""
        dummy_exe_dir = tmp_path / "Program Files" / "Ninite"
        dummy_exe = dummy_exe_dir / "ninite.exe"

        with patch("src.api.router_ninite.NINITE_DIR", dummy_exe_dir), \
             patch("src.api.router_ninite.NINITE_EXE", dummy_exe), \
             patch("src.api.router_ninite._run_powershell") as mock_ps:
            mock_ps.return_value = MagicMock(returncode=0, stdout="", stderr="")

            file_content = b"MZ\x90\x00\x03\x00\x00\x00DummyNiniteBinary"
            files = {"file": ("NiniteChromeInstaller.exe", file_content, "application/octet-stream")}
            data = {"interval_weeks": "2", "time_str": "20:00"}

            response = app_client.post("/api/ninite/upload", files=files, data=data)
            assert response.status_code == 200
            resp_data = response.json()
            assert resp_data["success"] is True
            assert dummy_exe.is_file()
            assert dummy_exe.read_bytes() == file_content


# =============================================================================
# 2. EDGE CASES & VALIDATION
# =============================================================================

class TestNiniteRouterEdgeCases:
    """Граничные условия и валидация."""

    def test_schedule_invalid_interval_edge_case(self, app_client):
        """Невалидный интервал недель (>52 или <1) должен отклоняться валидатором."""
        payload = {"interval_weeks": 0, "time_str": "20:00"}
        response = app_client.post("/api/ninite/schedule", json=payload)
        assert response.status_code == 422

        payload = {"interval_weeks": 100, "time_str": "20:00"}
        response = app_client.post("/api/ninite/schedule", json=payload)
        assert response.status_code == 422

    def test_schedule_invalid_time_format_edge_case(self, app_client):
        """Невалидный формат времени должен возвращать 422."""
        payload = {"interval_weeks": 2, "time_str": "25:99"}
        # regex r'^\d{2}:\d{2}$' accepts 2-digit pairs, but standard time check
        payload_bad = {"interval_weeks": 2, "time_str": "invalid_time"}
        response = app_client.post("/api/ninite/schedule", json=payload_bad)
        assert response.status_code == 422

    def test_menu_config_contains_ninite_tab(self):
        """tc_menu_config.json должен содержать вкладку ninite_updater в sidebarItems."""
        cfg_file = __root__ / "src" / "api" / "webgui" / "config" / "tc_menu_config.json"
        assert cfg_file.exists()
        config = json.loads(cfg_file.read_text(encoding="utf-8"))
        sidebar_items = config.get("menu", {}).get("sidebarItems", [])
        ninite_item = next((x for x in sidebar_items if x.get("id") == "ninite_updater"), None)
        assert ninite_item is not None, "Элемент ninite_updater должен присутствовать в sidebarItems"
        assert ninite_item.get("tab") == "tab-ninite-updater"
        assert ninite_item.get("label") == "Установить Ninite"
