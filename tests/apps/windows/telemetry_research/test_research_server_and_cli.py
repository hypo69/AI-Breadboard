# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry_Research - Test Research Server And Cli
# =============================================================================
# Description:
#   Тесты FastAPI REST API и интерфейса командной строки telemetry_research.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry_research.test_research_server_and_cli import TestTelemetryResearchServer
#
#     service = TestTelemetryResearchServer()
#
# File: test_research_server_and_cli.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Тесты FastAPI REST API и интерфейса командной строки telemetry_research.

Updated: 2026-10-01 11:30:00"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.windows.telemetry_research.server import app
from apps.windows.telemetry_research.cli import parse_args, main


@pytest.fixture
def client():
    """Фикстура TestClient для тестирования эндпоинтов FastAPI."""
    return TestClient(app)


class TestTelemetryResearchServer:
    """Тестирование REST API эндпоинтов FastAPI сервера."""

    def test_health_check(self, client):
        """Проверка работоспособности эндпоинта /api/health."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data

    def test_api_extract_current_state(self, client):
        """Проверка извлечения текущего состояния системы /api/current-state."""
        response = client.get("/api/current-state")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_api_scenario_execution(self, client):
        """Проверка вызова исследовательского сценария /api/run-research."""
        payload = {
            "subsystems": ["cpu", "ram"],
            "enable_hypotheses_check": True,
        }
        response = client.post("/api/run-research", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "report_id" in data

    def test_api_assistant_chat(self, client):
        """Проверка веб-чат эндпоинта ассистента /api/chat."""
        payload = {
            "message": "покажи статус использования CPU",
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data

    def test_api_sql_query_endpoint(self, client):
        """Проверка эндпоинта прямого SQL запроса /api/telemetry-sql/query."""
        payload = {
            "sql": "SELECT 1 as test_val",
        }
        response = client.post("/api/telemetry-sql/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "rows" in data


class TestTelemetryResearchCLI:
    """Тестирование аргументов и функции точки входа CLI."""

    def test_parse_args_defaults(self, monkeypatch):
        """Проверка значений аргументов по умолчанию."""
        monkeypatch.setattr("sys.argv", ["cli.py"])
        args = parse_args()
        assert args.source is None
        assert args.format == "html"

    def test_cli_main_summary_format(self, monkeypatch, tmp_path: Path):
        """Проверка запуска main() с выводом в формате summary."""
        log_file = tmp_path / "dummy.jsonl"
        log_file.write_text(json.dumps({"timestamp": "2026-10-01T00:00:00Z", "cpu": {"total_percent": 10.0}}))

        monkeypatch.setattr("sys.argv", ["cli.py", "--source", str(log_file), "--format", "summary"])
        exit_code = main()
        assert exit_code == 0
