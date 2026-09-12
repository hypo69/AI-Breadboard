# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test provider toggle and remember config
# =============================================================================
# Description:
#   Test saving provider configurations with remember flag and config.json persistence.
#
# File: test_provider_remember_config.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Test provider toggle switch and remember config functionality."""

import json
from unittest.mock import patch
import pytest
from starlette.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)


def test_get_foundry_config(client):
    """Test getting Foundry config endpoint."""
    response = client.get("/api/foundry/config")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "url" in data
    assert "key" in data
    assert "model" in data


def test_save_foundry_config_remember_true(client, tmp_path):
    """Test saving Foundry config with remember=True persists to config.json."""
    fake_config = {"ai": {"use_foundry": False, "foundry_base_url": "http://old", "foundry_model_id": "old"}}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(fake_config), encoding="utf-8")

    with patch("main.__root__", tmp_path), patch("dotenv.set_key"):
        response = client.post(
            "/api/foundry/config",
            json={
                "enabled": True,
                "url": "http://localhost:54837",
                "key": "test_key",
                "model": "qwen2.5-1.5b",
                "remember": True,
            },
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        saved_data = json.loads(config_file.read_text(encoding="utf-8"))
        assert saved_data["ai"]["use_foundry"] is True
        assert saved_data["ai"]["foundry_base_url"] == "http://localhost:54837"
        assert saved_data["ai"]["foundry_model_id"] == "qwen2.5-1.5b"


def test_save_foundry_config_remember_false(client, tmp_path):
    """Test saving Foundry config with remember=False does NOT persist to config.json."""
    fake_config = {"ai": {"use_foundry": False, "foundry_base_url": "http://old", "foundry_model_id": "old"}}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(fake_config), encoding="utf-8")

    with patch("main.__root__", tmp_path), patch("dotenv.set_key"):
        response = client.post(
            "/api/foundry/config",
            json={
                "enabled": True,
                "url": "http://localhost:54837",
                "key": "test_key",
                "model": "qwen2.5-1.5b",
                "remember": False,
            },
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # config.json should remain unchanged
        saved_data = json.loads(config_file.read_text(encoding="utf-8"))
        assert saved_data["ai"]["use_foundry"] is False


def test_save_ollama_config_remember(client, tmp_path):
    """Test saving Ollama config with remember flag."""
    fake_config = {"ai": {"use_ollama": False}}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(fake_config), encoding="utf-8")

    with patch("main.__root__", tmp_path):
        response = client.post(
            "/api/ollama/config",
            json={
                "enabled": True,
                "url": "http://localhost:11434",
                "model": "llama3.1",
                "remember": True,
            },
        )
        assert response.status_code == 200
        saved_data = json.loads(config_file.read_text(encoding="utf-8"))
        assert saved_data["ai"]["use_ollama"] is True


def test_save_agy_config_remember(client, tmp_path):
    """Test saving AGY config with remember flag."""
    fake_config = {"ai": {"use_agy": False}}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(fake_config), encoding="utf-8")

    with patch("main.__root__", tmp_path), patch("dotenv.set_key"):
        response = client.post(
            "/api/agy/config",
            json={
                "enabled": True,
                "key": "",
                "model": "agy-flash",
                "remember": True,
            },
        )
        assert response.status_code == 200
        saved_data = json.loads(config_file.read_text(encoding="utf-8"))
        assert saved_data["ai"]["use_agy"] is True


def test_save_onnx_config_remember(client, tmp_path):
    """Test saving ONNX config with remember flag."""
    fake_config = {"onnx": {"enabled": False}}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(fake_config), encoding="utf-8")

    with patch("main.__root__", tmp_path):
        response = client.post(
            "/api/onnx/config",
            json={
                "enabled": True,
                "models_dir": "models/onnx",
                "execution_provider": "DirectMLExecutionProvider",
                "default_model": "phi-3.5-mini-instruct-onnx",
                "olive_precision": "int4",
                "remember": True,
            },
        )
        assert response.status_code == 200
        saved_data = json.loads(config_file.read_text(encoding="utf-8"))
        assert saved_data["onnx"]["enabled"] is True
