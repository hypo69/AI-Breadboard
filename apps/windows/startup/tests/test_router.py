# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Windows Startup Auditor FastAPI Router
# =============================================================================
# Description:
#   Интеграционные тесты для эндпоинтов FastAPI роутера приложения
#   Windows Startup Auditor.
#
# Examples:
#   $ pytest apps/windows_startup_auditor/tests/test_router.py -v
#
# File: test_router.py
# Project: ai-breadboard
# Package: apps.windows.startup.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты FastAPI роутера Startup Auditor."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.startup.router import init_router


def get_test_client() -> TestClient:
    """Создание тестового клиента FastAPI с роутером Startup Auditor."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_status_endpoint() -> None:
    """Проверка эндпоинта /api/v1/startup-auditor/status."""
    client = get_test_client()
    response = client.get("/api/v1/startup-auditor/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Windows Startup Auditor" in data["service"]


def test_locations_endpoint() -> None:
    """Проверка эндпоинта /api/v1/startup-auditor/locations."""
    client = get_test_client()
    response = client.get("/api/v1/startup-auditor/locations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_summary_endpoint() -> None:
    """Проверка эндпоинта /api/v1/startup-auditor/summary."""
    client = get_test_client()
    response = client.get("/api/v1/startup-auditor/summary")
    assert response.status_code == 200
    data = response.json()
    assert "health_score" in data
    assert "total_entries" in data


def test_entries_endpoint() -> None:
    """Проверка эндпоинта /api/v1/startup-auditor/entries."""
    client = get_test_client()
    response = client.get("/api/v1/startup-auditor/entries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_audit_endpoint() -> None:
    """Проверка полного отчета /api/v1/startup-auditor/audit."""
    client = get_test_client()
    response = client.get("/api/v1/startup-auditor/audit")
    assert response.status_code == 200
    data = response.json()
    assert "hostname" in data
    assert "summary" in data
    assert "entries" in data
    assert "recommendations" in data


def test_export_endpoint() -> None:
    """Проверка экспорта в форматах json и csv."""
    client = get_test_client()
    res_json = client.get("/api/v1/startup-auditor/export?format=json")
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]

    res_csv = client.get("/api/v1/startup-auditor/export?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]


def test_explain_endpoint_known_app() -> None:
    """Проверка эндпоинта /api/v1/startup-auditor/explain для известного приложения."""
    client = get_test_client()
    payload = {
        "name": "OneDrive",
        "publisher": "Microsoft Corporation",
        "executable_path": r"C:\Users\User\AppData\Local\Microsoft\OneDrive\OneDrive.exe",
        "command": r'"C:\Users\User\AppData\Local\Microsoft\OneDrive\OneDrive.exe" /background',
        "arguments": "/background",
        "location_type": "registry_run",
        "risk_level": "clean",
        "file_exists": True,
        "is_signed": True,
        "boot_impact": "Среднее",
    }
    res = client.post("/api/v1/startup-auditor/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "security_verdict" in data
    assert "startup_recommendation" in data
    assert "action_steps" in data
    assert isinstance(data["action_steps"], list)
    assert "OneDrive" in data["summary"] or "Microsoft" in data["summary"]


def test_explain_endpoint_broken_entry() -> None:
    """Проверка эндпоинта /explain для битой ссылки (файл не найден)."""
    client = get_test_client()
    payload = {
        "name": "electron.app.LM Studio",
        "publisher": "Неизвестен",
        "executable_path": r"C:\Program Files\LM Studio\LM Studio.exe",
        "command": r'"C:\Program Files\LM Studio\LM Studio.exe" --run-as-service',
        "arguments": "--run-as-service",
        "location_type": "registry_run",
        "risk_level": "warning",
        "file_exists": False,
        "is_signed": False,
    }
    res = client.post("/api/v1/startup-auditor/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "Битая ссылка" in data["category"] or "битая" in data["summary"].lower() or "отсутствующий" in data["summary"].lower()
    assert len(data["action_steps"]) > 0


def test_explain_endpoint_critical_risk() -> None:
    """Проверка эндпоинта /explain для критического риска (IFEO / вредоносная подмена)."""
    client = get_test_client()
    payload = {
        "name": "sethc.exe debugger",
        "publisher": "Неизвестен",
        "executable_path": r"C:\Windows\Temp\payload.exe",
        "command": r"C:\Windows\Temp\payload.exe",
        "location_type": "ifeo",
        "risk_level": "critical",
        "file_exists": True,
        "boot_impact": "Высокое",
    }
    res = client.post("/api/v1/startup-auditor/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "критический" in data["summary"].lower() or "ifeo" in data["category"].lower()
    assert "отключите" in data["startup_recommendation"].lower() or "сканирование" in data["startup_recommendation"].lower()

