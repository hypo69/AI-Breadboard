# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for AI Breadboard Admin FastAPI Router
# =============================================================================
# Description:
#   Интеграционное тестирование эндпоинтов приложения ai_breadboard_admin:
#   проверка статуса, параметров RAG, поиска, версий инструкций и пользователей.
#
# File: test_admin_router.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from apps.ai_breadboard_admin.router import init_router


@pytest.fixture
def client():
    """Фикстура TestClient для роутера администратора с отключенной авторизацией."""
    app = FastAPI()
    app.include_router(init_router())
    with patch("apps.ai_breadboard_admin.router._check_admin_auth", return_value=True):
        yield TestClient(app)


def test_router_status_endpoint(client: TestClient) -> None:
    """Happy Path: проверка эндпоинта /api/v1/ai_breadboard_admin/status."""
    response = client.get("/api/v1/ai_breadboard_admin/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai_breadboard_admin"


def test_router_rag_endpoints(client: TestClient) -> None:
    """Happy Path & Update: чтение и запись режима RAG."""
    # 1. GET
    res_get = client.get("/api/v1/ai_breadboard_admin/config/rag")
    assert res_get.status_code == 200
    assert "mode" in res_get.json()

    # 2. POST
    res_post = client.post("/api/v1/ai_breadboard_admin/config/rag", json={"mode": "rag+model"})
    assert res_post.status_code == 200
    assert res_post.json()["mode"] == "rag+model"


def test_router_web_search_endpoints(client: TestClient) -> None:
    """Happy Path: чтение и запись параметров поиска."""
    res_get = client.get("/api/v1/ai_breadboard_admin/config/web-search")
    assert res_get.status_code == 200

    payload = {
        "engine": "playwright",
        "gemini_model": "gemini-2.5-flash",
        "gemini_cli_model": "gemini-3.1-flash-lite",
        "agy_model": "agy-flash",
    }
    res_post = client.post("/api/v1/ai_breadboard_admin/config/web-search", json=payload)
    assert res_post.status_code == 200
    assert res_post.json()["status"] == "ok"


def test_router_instructions_endpoints(client: TestClient) -> None:
    """Happy Path: чтение инструкций и списка версий."""
    res_inst = client.get("/api/v1/ai_breadboard_admin/instructions?mode=chat")
    assert res_inst.status_code == 200
    assert "content" in res_inst.json()

    res_vers = client.get("/api/v1/ai_breadboard_admin/instructions/versions?mode=chat")
    assert res_vers.status_code == 200
    assert "versions" in res_vers.json()


def test_router_users_endpoints(client: TestClient) -> None:
    """Happy Path: получение списка пользователей."""
    with patch("apps.ai_breadboard_admin.src.user_admin_service.user_manager.get_all_users", return_value=[]):
        res = client.get("/api/v1/ai_breadboard_admin/users")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
