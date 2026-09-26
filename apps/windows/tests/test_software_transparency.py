# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Software Transparency Tests
# =============================================================================
# Description:
#   Unit- и интеграционные тесты для подсистемы прозрачности ПО в составе
#   модуля apps/windows.
#
# File: test_software_transparency.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты модуля инспекции прозрачности ПО в составе apps/windows."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.core.software_transparency import (
    ConfigFile,
    ConfigInspector,
    EvidenceStatus,
    GeminiAppResearch,
    GeminiResearcher,
    NetworkTracker,
    SoftwareItem,
    SoftwareInventory,
    StorageAnalyzer,
    init_software_transparency_router,
)


def test_models_creation():
    """Проверка создания Pydantic моделей карточек ПО."""
    app = SoftwareItem(
        id="test-app",
        name="Test App",
        version="1.0.0",
        publisher="Test Corp",
    )
    assert app.name == "Test App"
    assert app.architecture == "x64"
    assert app.config_files == []


def test_secret_sanitizer():
    """Проверка очистки конфиденциальных секретов в конфигах."""
    inspector = ConfigInspector()

    raw_text = """
    {
        "api_key": "AIzaSyB3129381293812938129381293812",
        "password": "MySuperSecretP@ss123",
        "auth_header": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDcSemACt8x4iTMCda8Yhe3iZaWbvV5XKSTbuAn0M",
        "update_interval": 3600
    }
    """
    sanitized = inspector.sanitize_secrets(raw_text)
    assert "MySuperSecretP@ss123" not in sanitized
    assert "AIzaSy" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized or "[REDACTED_API_KEY]" in sanitized or "[REDACTED_JWT_TOKEN]" in sanitized
    assert "3600" in sanitized


def test_software_inventory_scan():
    """Проверка работы инвентаризатора ПО."""
    inv = SoftwareInventory()
    apps = inv.scan_installed_software()
    assert isinstance(apps, list)
    assert len(apps) > 0
    first_app = apps[0]
    assert first_app.id is not None
    assert first_app.name != ""


def test_storage_analyzer():
    """Проверка анализатора мест хранения данных."""
    analyzer = StorageAnalyzer()
    app = SoftwareItem(
        id="test-app",
        name="Chrome",
        version="140.0",
        publisher="Google LLC",
    )
    dirs = analyzer.discover_storage_for_app(app)
    assert isinstance(dirs, list)


def test_network_tracker():
    """Проверка сетевого трекера приложений."""
    tracker = NetworkTracker()
    app = SoftwareItem(
        id="google-chrome",
        name="Google Chrome",
        version="140.0",
        publisher="Google LLC",
    )
    cfgs = [
        ConfigFile(
            path="C:\\test\\config.json",
            display_path="%APPDATA%\\test\\config.json",
            filename="config.json",
            format="json",
            sample_content='{"api_url": "https://api.example.com"}',
            status=EvidenceStatus.LOCAL_OBSERVED,
        )
    ]
    endpoints = tracker.track_app_network(app, cfgs)
    assert len(endpoints) > 0
    domains = [e.domain_or_ip for e in endpoints]
    assert "api.example.com" in domains or any("google" in d for d in domains)


@pytest.mark.asyncio
async def test_gemini_researcher_fallback():
    """Проверка работы ИИ-исследователя прозрачности ПО."""
    researcher = GeminiResearcher()
    app = SoftwareItem(
        id="google-chrome",
        name="Google Chrome",
        version="140.0",
        publisher="Google LLC",
    )
    res = await researcher.research_software(app)
    assert isinstance(res, GeminiAppResearch)
    assert "Google Chrome" in res.summary
    assert len(res.confirmed_facts) > 0


def test_fastapi_router():
    """Проверка эндпоинтов роутера прозрачности ПО."""
    app = FastAPI()
    app.include_router(init_software_transparency_router())
    client = TestClient(app)

    # Status
    res_status = client.get("/api/v1/software-scanner/status")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "online"

    # Full scan
    res_scan = client.get("/api/v1/software-scanner/scan")
    assert res_scan.status_code == 200
    data = res_scan.json()
    assert "summary" in data
    assert "apps" in data
    assert len(data["apps"]) > 0

    first_app_id = data["apps"][0]["id"]

    # Get single app
    res_single = client.get(f"/api/v1/software-scanner/apps/{first_app_id}")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == first_app_id

    # Research
    res_research = client.post("/api/v1/software-scanner/research", json={"app_id": first_app_id})
    assert res_research.status_code == 200
    assert "summary" in res_research.json()
