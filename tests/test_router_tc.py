# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Computer (TC) Router Unit Tests
# =============================================================================
# Description:
#   Тестирование REST эндпоинтов /tc/model_instruction, /tc/model
#   и /tc/model_provider (GET/POST/PUT), валидации входных данных и алиасов.
#
# File: test_router_tc.py
# Project: AI-Breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Юнит-тесты для FastAPI роутера Test Computer (src/api/router_tc.py)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.router_tc import init_router


@pytest.fixture
def test_app() -> FastAPI:
    """Фикстура для создания тестового приложения FastAPI с роутером TC."""
    app = FastAPI()
    router = init_router()
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Фикстура для создания тестового клиента."""
    return TestClient(test_app)


class TestTcModelInstructionEndpoints:
    """Набор тестов для роутов системной инструкции (/tc/model_instruction)."""

    def test_get_tc_model_instruction(self, client: TestClient) -> None:
        """Проверка GET /tc/model_instruction возвращает системную инструкцию."""
        response = client.get("/tc/model_instruction")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert "instruction" in data
        assert "system_instruction" in data
        assert "model" in data
        assert "provider" in data

    def test_get_tc_model_instruction_aliases(self, client: TestClient) -> None:
        """Проверка алиасов для получения инструкции: /tc/model-instruction и /api/tc/model_instruction."""
        resp1 = client.get("/tc/model-instruction")
        assert resp1.status_code == 200
        assert resp1.json().get("status") == "success"

        resp2 = client.get("/api/tc/model_instruction")
        assert resp2.status_code == 200
        assert resp2.json().get("status") == "success"

        resp3 = client.get("/api/v1/tc/model_instruction")
        assert resp3.status_code == 200
        assert resp3.json().get("status") == "success"

    def test_set_tc_model_instruction_success(self, client: TestClient, tmp_path: Path) -> None:
        """Проверка POST /tc/model_instruction обновляет системную инструкцию."""
        new_instruction = "Вы — тестовый сервисный инженер TC."
        with patch("src.api.router_tc.__root__", tmp_path):
            response = client.post(
                "/tc/model_instruction",
                json={
                    "instruction": new_instruction,
                    "save_to_disk": True,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "success"
            assert data.get("instruction") == new_instruction

            # Проверка записи на диск
            saved_file = tmp_path / "prompts" / "tc" / "system_instruction.md"
            assert saved_file.exists()
            assert saved_file.read_text(encoding="utf-8") == new_instruction

    def test_set_tc_model_instruction_put_method(self, client: TestClient) -> None:
        """Проверка PUT /tc/model_instruction обновляет системную инструкцию."""
        new_instruction = "Инструкция через PUT."
        response = client.put(
            "/tc/model_instruction",
            json={"system_instruction": new_instruction, "save_to_disk": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("instruction") == new_instruction

    def test_set_tc_model_instruction_empty_error(self, client: TestClient) -> None:
        """Проверка POST /tc/model_instruction с пустой инструкцией возвращает 400."""
        response = client.post("/tc/model_instruction", json={"instruction": ""})
        assert response.status_code == 400
        assert "Инструкция не может быть пустой" in response.json().get("detail", "")


class TestTcModelEndpoints:
    """Набор тестов для роутов модели (/tc/model)."""

    def test_get_tc_model(self, client: TestClient) -> None:
        """Проверка GET /tc/model возвращает имя активной модели."""
        response = client.get("/tc/model")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert "model" in data
        assert "provider" in data
        assert "display" in data

    def test_get_tc_model_aliases(self, client: TestClient) -> None:
        """Проверка алиасов: /tc/active_model, /tc/active-model, /api/tc/model."""
        for path in ("/tc/active_model", "/tc/active-model", "/api/tc/model", "/api/v1/tc/model"):
            resp = client.get(path)
            assert resp.status_code == 200
            assert resp.json().get("status") == "success"

    def test_set_tc_model_success(self, client: TestClient, tmp_path: Path) -> None:
        """Проверка POST /tc/model и POST /tc/set_model обновляет модель TC."""
        cfg_file = tmp_path / "start_scenarios_config" / "tc.json"
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        cfg_file.write_text(json.dumps({"ai": {"provider": "gemini_cli", "gemini_cli": {"model": "gemini-3.1-flash-lite"}}}), encoding="utf-8")

        with patch("src.api.router_tc._find_tc_config_path", return_value=cfg_file):
            response = client.post(
                "/tc/model",
                json={
                    "model": "gemini-2.5-flash",
                    "provider": "gemini",
                    "save_to_config": True,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "success"
            assert data.get("model") == "gemini-2.5-flash"
            assert data.get("provider") == "GEMINI"

            # Проверка обновления файла tc.json
            updated_data = json.loads(cfg_file.read_text(encoding="utf-8"))
            assert updated_data["ai"]["provider"] == "gemini"
            assert updated_data["ai"]["gemini"]["model"] == "gemini-2.5-flash"

    def test_set_tc_model_via_put(self, client: TestClient) -> None:
        """Проверка PUT /tc/model обновляет модель."""
        response = client.put(
            "/tc/model",
            json={"model": "llama3.1", "provider": "ollama", "save_to_config": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("model") == "llama3.1"
        assert data.get("provider") == "OLLAMA"

    def test_set_tc_model_empty_error(self, client: TestClient) -> None:
        """Проверка POST /tc/model с пустым именем модели возвращает 400."""
        response = client.post("/tc/model", json={"model": ""})
        assert response.status_code == 400
        assert "Имя модели не может быть пустым" in response.json().get("detail", "")


class TestTcModelProviderEndpoints:
    """Набор тестов для роутов провайдера (/tc/model_provider)."""

    def test_get_tc_model_provider(self, client: TestClient) -> None:
        """Проверка GET /tc/model_provider возвращает активного провайдера."""
        response = client.get("/tc/model_provider")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert "provider" in data
        assert "model" in data

    def test_get_tc_model_provider_aliases(self, client: TestClient) -> None:
        """Проверка алиасов: /tc/provider, /tc/model-provider, /api/tc/model_provider, /api/tc/provider."""
        for path in ("/tc/provider", "/tc/model-provider", "/api/tc/model_provider", "/api/tc/provider"):
            resp = client.get(path)
            assert resp.status_code == 200
            assert resp.json().get("status") == "success"

    def test_set_tc_model_provider_success(self, client: TestClient, tmp_path: Path) -> None:
        """Проверка POST /tc/model_provider и POST /tc/set_provider обновляет провайдера TC."""
        cfg_file = tmp_path / "start_scenarios_config" / "tc.json"
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        cfg_file.write_text(json.dumps({"ai": {"provider": "gemini_cli", "gemini_cli": {"model": "gemini-3.1-flash-lite"}}}), encoding="utf-8")

        with patch("src.api.router_tc._find_tc_config_path", return_value=cfg_file):
            response = client.post(
                "/tc/model_provider",
                json={
                    "provider": "agy",
                    "model": "gemini-3.6-flash",
                    "save_to_config": True,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "success"
            assert data.get("provider") == "AGY"
            assert data.get("model") == "gemini-3.6-flash"

            # Проверка файла
            updated_data = json.loads(cfg_file.read_text(encoding="utf-8"))
            assert updated_data["ai"]["provider"] == "agy"
            assert updated_data["ai"]["agy"]["model"] == "gemini-3.6-flash"

    def test_set_tc_model_provider_empty_error(self, client: TestClient) -> None:
        """Проверка POST /tc/model_provider с пустым провайдером возвращает 400."""
        response = client.post("/tc/model_provider", json={"provider": ""})
        assert response.status_code == 400
        assert "Имя провайдера не может быть пустым" in response.json().get("detail", "")


class TestTcTelemetryEndpoints:
    """Набор тестов для роутов телеметрии сенсоров (/tc/telemetry)."""

    def test_post_tc_telemetry_sensor_readings(self, client: TestClient, tmp_path: Path) -> None:
        """Проверка POST /tc/telemetry сохраняет показания реальных сенсоров."""
        db_file = tmp_path / "telemetry_test.db"
        fake_storage = MagicMock()
        fake_storage.save_sensor_polls.return_value = 2

        with patch("apps.windows.telemetry.storage.TelemetryStorage.get_instance", return_value=fake_storage):
            payload = {
                "source": "hardware_sensor",
                "readings": [
                    {
                        "id": "cpu_temp_core_0",
                        "hardware_name": "Intel Core i9",
                        "hardware_type": "cpu",
                        "sensor_category": "Temperature",
                        "sensor_name": "CPU Core #1",
                        "unit": "°C",
                        "value": 54.5,
                    },
                    {
                        "id": "gpu_load_total",
                        "hardware_name": "NVIDIA GeForce RTX 4090",
                        "hardware_type": "gpu",
                        "sensor_category": "Load",
                        "sensor_name": "GPU Core Load",
                        "unit": "%",
                        "value": 32.0,
                    },
                ],
            }
            response = client.post("/tc/telemetry", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "success"
            assert data.get("saved_count") == 2
            assert data.get("source") == "hardware_sensor"
            fake_storage.save_sensor_polls.assert_called_once()

    def test_get_tc_telemetry_from_db(self, client: TestClient) -> None:
        """Проверка GET /tc/telemetry считывает показания сенсоров из базы данных."""
        fake_records = [
            {
                "id": 1,
                "sensor_id": "cpu_temp_core_0",
                "timestamp": "2026-09-26T07:40:00Z",
                "hardware_name": "Intel Core i9",
                "hardware_type": "cpu",
                "sensor_category": "Temperature",
                "sensor_name": "CPU Core #1",
                "unit": "°C",
                "value": 54.5,
            }
        ]
        fake_storage = MagicMock()
        fake_storage.get_latest_sensor_polls.return_value = fake_records

        with patch("apps.windows.telemetry.storage.TelemetryStorage.get_instance", return_value=fake_storage):
            response = client.get("/tc/telemetry?limit=50&hardware_type=cpu")
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "success"
            assert data.get("count") == 1
            assert data.get("telemetry") == fake_records
            fake_storage.get_latest_sensor_polls.assert_called_once_with(
                limit=50,
                sensor_id=None,
                hardware_type="cpu",
            )

