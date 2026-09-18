# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Universal Diagnostic & Table Explanation Router
# =============================================================================
# Description:
#   Тестирование универсального эндпоинта /api/v1/diagnostics/explain
#   для различных типов сущностей и таблиц интерфейса.
#
# Examples:
#   $ pytest tests/test_router_diagnostics.py -v
#
# File: test_router_diagnostics.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты универсального роутера AI-диагностики таблиц."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.router_diagnostics import init_router


def get_test_client() -> TestClient:
    """Создание тестового клиента FastAPI с роутером диагностики."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_explain_software_item() -> None:
    """Проверка AI-объяснения для установленного ПО (Software Audit)."""
    client = get_test_client()
    payload = {
        "table_type": "software",
        "title": "Google Chrome",
        "subtitle": "Google LLC",
        "metadata": {
            "version": "122.0.6261.95",
            "size_mb": 340.5,
            "category": "Браузер",
        },
        "raw_data": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    }
    res = client.post("/api/v1/diagnostics/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "Google" in data["developer"] or "Google" in data["summary"]
    assert len(data["action_steps"]) > 0


def test_explain_process_item() -> None:
    """Проверка AI-объяснения для процесса Windows (System Inspector)."""
    client = get_test_client()
    payload = {
        "table_type": "process",
        "title": "explorer.exe",
        "subtitle": "PID: 4120 | DOMAIN\\User",
        "metadata": {
            "pid": 4120,
            "cpu_percent": 1.2,
            "memory_mb": 145.0,
            "num_threads": 48,
        },
        "raw_data": r"C:\Windows\explorer.exe",
    }
    res = client.post("/api/v1/diagnostics/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "Системный" in data["category"] or "explorer" in data["summary"].lower()
    assert "explorer.exe" in data["summary"]


def test_explain_service_item() -> None:
    """Проверка AI-объяснения для службы Windows (System Control)."""
    client = get_test_client()
    payload = {
        "table_type": "service",
        "title": "wuauserv",
        "subtitle": "Windows Update Service",
        "metadata": {
            "status": "Running",
            "start_type": "Auto",
        },
        "raw_data": r"C:\Windows\system32\svchost.exe -k netsvcs -p",
    }
    res = client.post("/api/v1/diagnostics/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "служба" in data["category"].lower() or "wuauserv" in data["summary"].lower()


def test_explain_network_item() -> None:
    """Проверка AI-объяснения для сетевого пакета/сокета (Network Monitor)."""
    client = get_test_client()
    payload = {
        "table_type": "network",
        "title": "Сетевой сокет TCP",
        "subtitle": "192.168.1.50:52344 -> 142.250.180.14:443",
        "metadata": {
            "protocol": "TLS",
            "local_address": "192.168.1.50:52344",
            "remote_address": "142.250.180.14:443",
            "length": 1420,
        },
        "raw_data": "TLSv1.3 Application Data",
    }
    res = client.post("/api/v1/diagnostics/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "network" in data["category"].lower() or "сетев" in data["category"].lower() or "соединение" in data["summary"].lower()


def test_explain_registry_item() -> None:
    """Проверка AI-объяснения для ключа реестра (Registry Viewer)."""
    client = get_test_client()
    payload = {
        "table_type": "registry",
        "title": "EnableLUA",
        "subtitle": r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
        "metadata": {
            "type": "REG_DWORD",
        },
        "raw_data": "1",
    }
    res = client.post("/api/v1/diagnostics/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "реестр" in data["category"].lower() or "параметр" in data["summary"].lower()


def test_explain_website_item() -> None:
    """Проверка AI-объяснения для веб-страницы/сайта (Website Monitor)."""
    client = get_test_client()
    payload = {
        "table_type": "website",
        "title": "/pricing",
        "subtitle": "https://example.com/pricing",
        "metadata": {
            "status_code": 200,
            "latency_ms": 142,
            "screen_page_views": 1250,
        },
    }
    res = client.post("/api/v1/diagnostics/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "веб" in data["category"].lower() or "200" in data["summary"]


def test_explain_rag_doc_item() -> None:
    """Проверка AI-объяснения для документа RAG базы знаний."""
    client = get_test_client()
    payload = {
        "table_type": "rag_doc",
        "title": "architecture_guide.md",
        "metadata": {
            "chunks": 42,
            "size": "128 KB",
            "status": "indexed",
        },
        "raw_data": "docs/architecture_guide.md",
    }
    res = client.post("/api/v1/diagnostics/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "RAG" in data["developer"] or "знаний" in data["summary"].lower() or "42" in data["summary"]


def test_explain_disk_item() -> None:
    """Проверка AI-объяснения для накопителя/диска."""
    client = get_test_client()
    payload = {
        "table_type": "disk",
        "title": "C:\\",
        "subtitle": "Системный диск NTFS",
        "metadata": {
            "free": "84 GB",
            "total": "512 GB",
            "percent": 83.5,
        },
    }
    res = client.post("/api/v1/diagnostics/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "диск" in data["category"].lower() or "накопитель" in data["summary"].lower()


def test_get_prompts_list() -> None:
    """Проверка получения списка шаблонов промптов для всех таблиц."""
    client = get_test_client()
    res = client.get("/api/v1/diagnostics/prompts")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    types = [item["table_type"] for item in data]
    assert "software" in types
    assert "process" in types
    assert "service" in types
    assert "network" in types
    assert "generic" in types


def test_get_and_update_prompt_template() -> None:
    """Проверка получения, обновления и сброса кастомного шаблона промпта."""
    client = get_test_client()
    
    # 1. Получение дефолтного шаблона
    res = client.get("/api/v1/diagnostics/prompts/software")
    assert res.status_code == 200
    initial_data = res.json()
    assert initial_data["table_type"] == "software"
    assert "Аудит установленного ПО" in initial_data["name"]

    # 2. Обновление пользовательского шаблона
    update_payload = {
        "name": "Кастомный аудит ПО",
        "description": "Модифицированное описание",
        "system_instruction": "Ты — кастомный агент безопасности. Отвечай строго в формате чистого JSON.",
        "prompt_template": "Кастомный промпт: {title} {subtitle} {metadata} {raw_data}"
    }
    update_res = client.post("/api/v1/diagnostics/prompts/software", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["name"] == "Кастомный аудит ПО"
    assert updated_data["is_customized"] is True
    assert "Кастомный промпт" in updated_data["prompt_template"]

    # 3. Сброс шаблона к дефолту
    reset_res = client.post("/api/v1/diagnostics/prompts/software/reset")
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["is_customized"] is False
    assert "Аудит установленного ПО" in reset_data["name"]
