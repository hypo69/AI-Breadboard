# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Focus Session
# =============================================================================
# Description:
#   Модульные тесты для подсистемы управления сессиями фокусировки Windows Focus,
#   режимом «Не беспокоить» (Do Not Disturb) и REST API роутера.
#
# Usage Examples:
#   pytest apps/windows/tests/test_focus_session.py -v
#
# File: test_focus_session.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 19:35:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты роутера и менеджера сессий фокусировки внимания."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_focus import (
    FocusSessionManager,
    FocusSessionStateDTO,
    FocusSettingsDTO,
    init_router,
)


@pytest.fixture
def focus_manager() -> FocusSessionManager:
    """Фикстура изолированного экземпляра FocusSessionManager."""
    return FocusSessionManager()


@pytest.fixture
def test_client() -> TestClient:
    """Фикстура тестового клиента FastAPI с подключенным роутером focus."""
    app = FastAPI()
    router = init_router()
    app.include_router(router)
    return TestClient(app)


def test_focus_dto_defaults() -> None:
    """Проверка значений по умолчанию в DTO моделях Focus."""
    settings = FocusSettingsDTO()
    assert settings.session_duration_minutes == 30
    assert settings.show_timer_in_clock_app is True
    assert settings.hide_badges_on_taskbar is True
    assert settings.hide_flashing_on_taskbar is True
    assert settings.turn_on_do_not_disturb is True

    state = FocusSessionStateDTO()
    assert state.is_active is False
    assert state.session_duration_minutes == 30
    assert state.remaining_seconds == 0


@pytest.mark.asyncio
async def test_focus_manager_lifecycle(focus_manager: FocusSessionManager) -> None:
    """Проверка жизненного цикла сессии фокусировки (старт, таймер, остановка)."""
    # 1. Начальное состояние
    state = focus_manager.get_state()
    assert state.is_active is False

    # 2. Обновление настроек
    new_cfg = FocusSettingsDTO(
        session_duration_minutes=45,
        show_timer_in_clock_app=False,
        hide_badges_on_taskbar=True,
        hide_flashing_on_taskbar=False,
        turn_on_do_not_disturb=True,
    )
    updated = focus_manager.update_settings(new_cfg)
    assert updated.session_duration_minutes == 45
    assert updated.show_timer_in_clock_app is False

    # 3. Запуск сессии
    active_state = await focus_manager.start_session(duration_minutes=45)
    assert active_state.is_active is True
    assert active_state.session_duration_minutes == 45
    assert active_state.remaining_seconds > 0
    assert active_state.started_at is not None
    assert active_state.ends_at is not None

    # 4. Остановка сессии
    stopped_state = focus_manager.stop_session()
    assert stopped_state.is_active is False
    assert stopped_state.remaining_seconds == 0


def test_api_get_state(test_client: TestClient) -> None:
    """Проверка REST эндпоинта GET /api/windows/focus/state."""
    resp = test_client.get("/api/windows/focus/state")
    assert resp.status_code == 200
    data = resp.json()
    assert "is_active" in data
    assert "session_duration_minutes" in data
    assert "settings" in data


def test_api_update_settings(test_client: TestClient) -> None:
    """Проверка REST эндпоинта POST /api/windows/focus/settings."""
    payload = {
        "session_duration_minutes": 25,
        "show_timer_in_clock_app": True,
        "hide_badges_on_taskbar": True,
        "hide_flashing_on_taskbar": True,
        "turn_on_do_not_disturb": True,
    }
    resp = test_client.post("/api/windows/focus/settings", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_duration_minutes"] == 25


def test_api_session_start_and_stop(test_client: TestClient) -> None:
    """Проверка запуска и остановки сессии через REST API."""
    # Старт сессии
    resp_start = test_client.post("/api/windows/focus/session/start?duration_minutes=20")
    assert resp_start.status_code == 200
    data_start = resp_start.json()
    assert data_start["is_active"] is True
    assert data_start["session_duration_minutes"] == 20
    assert data_start["remaining_seconds"] > 0

    # Стоп сессии
    resp_stop = test_client.post("/api/windows/focus/session/stop")
    assert resp_stop.status_code == 200
    data_stop = resp_stop.json()
    assert data_stop["is_active"] is False


def test_api_open_actions(test_client: TestClient) -> None:
    """Проверка эндпоинтов вызова системных окон."""
    resp_settings = test_client.post("/api/windows/focus/open-settings")
    assert resp_settings.status_code == 200
    assert resp_settings.json()["target"] == "ms-settings:quiethours"

    resp_clock = test_client.post("/api/windows/focus/open-clock")
    assert resp_clock.status_code == 200
    assert resp_clock.json()["target"] == "ms-clock:focus"
