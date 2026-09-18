# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Scenarios and Mini-Chat Skill Generator
# =============================================================================
# Description:
#   Тестирует FastAPI эндпоинты сценариев тестирования (/api/v1/scenarios),
#   включая список сценариев, запуск быстрой проверки (Smoke Test), аудит логов,
#   мини-чат с распознаванием мышей и автогенерацию навыков (.skills/).
#
# File: test_scenarios.py
# Project: AI-Breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for Scenarios, Smoke Tests, and AI Skills Assistant Mini-Chat."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from header import __root__
from main import app

client = TestClient(app)


class TestScenariosSuite:
    """Набор тестов для сценариев тестирования и ассистента навыков."""

    def test_list_scenarios(self):
        """Проверка получения списка доступных сценариев."""
        res = client.get("/api/v1/scenarios")
        assert res.status_code == 200
        scenarios = res.json()
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 5

        ids = [s["id"] for s in scenarios]
        assert "quick_check" in ids
        assert "log_audit" in ids
        assert "system_inspector" in ids
        assert "windows_admin" in ids
        assert "network_test" in ids
        assert "ai_providers_check" in ids

        # Quick check must have recommended flag
        quick_item = next(s for s in scenarios if s["id"] == "quick_check")
        assert quick_item["recommended"] is True

    def test_run_quick_check_scenario(self):
        """Запуск сценария быстрой проверки (Smoke Test)."""
        res = client.post("/api/v1/scenarios/run", json={"scenario_id": "quick_check"})
        assert res.status_code == 200
        data = res.json()

        assert data["scenario_id"] == "quick_check"
        assert data["status"] in ("ok", "warn", "error")
        assert "duration_ms" in data
        assert data["total_steps"] >= 4
        assert isinstance(data["steps"], list)
        assert len(data["steps"]) >= 4
        assert len(data["summary"]) > 0

        step_names = [s["name"] for s in data["steps"]]
        assert any("Python" in n for n in step_names)
        assert any("Конфигурационные" in n for n in step_names)
        assert any("Дисковое" in n for n in step_names)
        assert any("логов" in n for n in step_names)

    def test_run_log_audit_scenario(self):
        """Запуск сценария аудита логов."""
        res = client.post("/api/v1/scenarios/run", json={"scenario_id": "log_audit"})
        assert res.status_code == 200
        data = res.json()

        assert data["scenario_id"] == "log_audit"
        assert data["status"] in ("ok", "warn", "error")
        assert len(data["steps"]) >= 2
        assert any("Инвентаризация" in s["name"] for s in data["steps"])

    def test_run_unknown_scenario_returns_400(self):
        """Несуществующий сценарий должен возвращать HTTP 400."""
        res = client.post("/api/v1/scenarios/run", json={"scenario_id": "non_existent_12345"})
        assert res.status_code == 400
        assert "Неизвестный идентификатор" in res.json()["detail"]

    def test_scenario_chat_mouse_history_and_skill_generation(self):
        """Запрос в мини-чат о мышах должен вернуть список устройств и создать навык."""
        req_payload = {
            "message": "Какие мыши были подключены к этому компьютеру?",
            "auto_create_skill": True,
        }
        res = client.post("/api/v1/scenarios/chat", json=req_payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "ok"
        assert "reply" in data
        assert "мышей" in data["reply"].lower() or "манипуляторов" in data["reply"].lower()

        # Skill metadata check
        assert data["created_skill"] is not None
        skill_info = data["created_skill"]
        assert skill_info["name"] == "mouse-history-inspector"
        assert "SKILL.md" in skill_info["path"]

        # Verify skill file physically created on disk
        skill_file = __root__ / skill_info["path"]
        assert skill_file.exists(), f"Skill file {skill_file} must exist"
        skill_content = skill_file.read_text(encoding="utf-8")
        assert "mouse-history-inspector" in skill_content
        assert "Get-PnpDevice -Class Mouse" in skill_content

    def test_scenarios_tab_in_apps_index_html(self):
        """Вкладка 'Сценарии' должна присутствовать в apps/index.html и быть первой."""
        apps_html = __root__ / "src" / "api" / "webgui" / "apps" / "index.html"
        assert apps_html.exists()
        content = apps_html.read_text(encoding="utf-8")

        assert 'data-tab="tab-scenarios"' in content
        assert 'id="tab-scenarios"' in content

        # Check that tab-scenarios is placed before tab-chat
        scenarios_pos = content.find('data-tab="tab-scenarios"')
        chat_pos = content.find('data-tab="tab-chat"')
        assert scenarios_pos != -1
        assert chat_pos != -1
        assert scenarios_pos < chat_pos, "tab-scenarios must be the FIRST tab in navigation"
