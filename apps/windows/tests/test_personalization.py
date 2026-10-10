# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Personalization Tests
# =============================================================================
# Description:
#   Комплексные модульные и интеграционные тесты для подсистемы персонализации
#   Windows, тем оформления (.theme), настройки курсора, обоев рабочего стола,
#   AI Spotlight («О фотографии») и фиксации изменений в telemetry.db.
#
# Usage Examples:
#   pytest apps/windows/tests/test_personalization.py -v
#
# Updated: 2026-10-06 18:35:00
# =============================================================================

"""Модульные тесты подсистемы Personalization & Appearance."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import FastAPI

from apps.windows.sdk.modules.personalization.models import (
    WindowsThemeInfo,
    ThemeApplyRequest,
    CursorSettings,
    CursorUpdateRequest,
    CursorColorScheme,
    WallpaperSettings,
    WallpaperUpdateRequest,
    WallpaperFitMode,
    WallpaperSourceMode,
    WindowsSpotlightSettings,
    AISpotlightLocation,
    AISpotlightImageInfo,
    PersonalizationOverviewResponse,
)
from apps.windows.sdk.modules.personalization.manager import PersonalizationManager
from apps.windows.sdk.modules.personalization.ai_spotlight import AISpotlightEngine
from apps.windows.sdk.modules.personalization.router import router as personalization_router
from apps.windows.sdk.modules.window_control_plane.history import WindowManagementHistoryManager


@pytest.fixture
def temp_history_mgr(tmp_path: Path) -> WindowManagementHistoryManager:
    """Фикстура изолированного менеджера истории в SQLite telemetry.db."""
    db_file = tmp_path / "test_telemetry.db"
    return WindowManagementHistoryManager(db_path=db_file)


@pytest.fixture
def temp_pers_mgr(temp_history_mgr: WindowManagementHistoryManager) -> PersonalizationManager:
    """Фикстура менеджера персонализации с тестовой БД."""
    return PersonalizationManager(history_manager=temp_history_mgr)


@pytest.fixture
def client(temp_pers_mgr: PersonalizationManager) -> TestClient:
    """Фикстура тестового клиента FastAPI с инъекцией менеджера."""
    from apps.windows.sdk.modules.personalization import router as r_mod

    r_mod._pm = temp_pers_mgr
    app = FastAPI()
    app.include_router(personalization_router, prefix="/api/v1/windows/personalization")
    return TestClient(app)


def test_theme_list_and_apply(temp_pers_mgr: PersonalizationManager):
    """Тест сканирования тем и применения темы оформления."""
    themes = temp_pers_mgr.get_theme_list()
    assert len(themes) > 0
    assert any("dark" in th.name.lower() or "windows" in th.name.lower() for th in themes)

    target_theme = themes[0]
    req = ThemeApplyRequest(theme_name_or_path=target_theme.name)
    result = temp_pers_mgr.apply_theme(req, operator="pytest-user")
    assert result.get("success") is True

    # Проверка записи в историю telemetry.db
    history = temp_pers_mgr.history_mgr.get_history(limit=5)
    assert len(history) >= 1
    assert "theme" in history[0]["setting_id"]


def test_cursor_settings_lifecycle(temp_pers_mgr: PersonalizationManager):
    """Тест считывания, изменения и фиксации параметров курсора."""
    current_cursor = temp_pers_mgr.get_cursor_settings()
    assert current_cursor.size >= 1
    assert current_cursor.pointer_speed >= 1

    # Изменение параметров курсора
    req = CursorUpdateRequest(
        size=48,
        color_scheme=CursorColorScheme.CUSTOM,
        custom_color_hex="#00FFCC",
        shadow=True,
        trails=False,
        hide_while_typing=True,
        show_location_on_ctrl=True,
        pointer_speed=14,
    )

    applied = temp_pers_mgr.update_cursor(req, operator="test-cursor-runner")
    assert applied.size == 48
    assert applied.color_scheme == CursorColorScheme.CUSTOM
    assert applied.pointer_speed == 14

    # Проверка сохранения в telemetry.db
    history = temp_pers_mgr.history_mgr.get_history(limit=5)
    cursor_rec = next((h for h in history if "cursor" in h["setting_id"]), None)
    assert cursor_rec is not None
    new_val = cursor_rec["new_value"]
    if isinstance(new_val, dict):
        assert new_val.get("size") == 48
    else:
        assert "48" in str(new_val)


def test_wallpaper_settings_lifecycle(temp_pers_mgr: PersonalizationManager):
    """Тест настройки обоев рабочего стола и режимов заполнения."""
    current_wp = temp_pers_mgr.get_wallpaper_settings()
    assert current_wp.mode in [
        WallpaperSourceMode.PICTURE,
        WallpaperSourceMode.SOLID_COLOR,
        WallpaperSourceMode.SLIDESHOW,
        WallpaperSourceMode.SPOTLIGHT,
    ]
    assert current_wp.fit_mode in [
        WallpaperFitMode.FILL,
        WallpaperFitMode.FIT,
        WallpaperFitMode.STRETCH,
        WallpaperFitMode.TILE,
        WallpaperFitMode.CENTER,
        WallpaperFitMode.SPAN,
    ]

    # Установка новых параметров обоев
    req = WallpaperUpdateRequest(
        mode=WallpaperSourceMode.PICTURE,
        fit_mode=WallpaperFitMode.FILL,
        image_path=r"C:\Windows\Web\Wallpaper\Windows\img0.jpg",
        background_color_hex="#0F172A",
    )

    applied_wp = temp_pers_mgr.update_wallpaper(req, operator="test-wallpaper-runner")
    assert applied_wp.mode == WallpaperSourceMode.PICTURE
    assert applied_wp.fit_mode == WallpaperFitMode.FILL

    # Проверка сохранения в telemetry.db
    history = temp_pers_mgr.history_mgr.get_history(limit=5)
    wp_rec = next((h for h in history if "wallpaper" in h["setting_id"]), None)
    assert wp_rec is not None


def test_ai_spotlight_intelligence():
    """Тест движка AI Spotlight и карточки «О фотографии»."""
    engine = AISpotlightEngine()
    spotlight_info = engine.get_current_spotlight_info()

    assert spotlight_info.title is not None
    assert spotlight_info.description_ru is not None
    assert spotlight_info.location is not None
    assert spotlight_info.location.country is not None
    assert len(spotlight_info.fun_facts) > 0
    assert len(spotlight_info.sources) > 0

    # Тест галереи кэша
    gallery = engine.list_cached_spotlight_images()
    assert len(gallery) > 0
    assert all(isinstance(img, AISpotlightImageInfo) for img in gallery)


def test_api_endpoints_integration(client: TestClient):
    """Интеграционный тест всех конечных точек Personalization API."""
    # 1. Overview
    resp_overview = client.get("/api/v1/windows/personalization/overview")
    assert resp_overview.status_code == 200
    overview_data = resp_overview.json()
    assert "current_theme" in overview_data
    assert "cursor" in overview_data
    assert "wallpaper" in overview_data

    # 2. Themes list & apply
    resp_themes = client.get("/api/v1/windows/personalization/themes")
    assert resp_themes.status_code == 200
    themes_list = resp_themes.json()
    assert len(themes_list) > 0

    resp_apply_theme = client.post(
        "/api/v1/windows/personalization/theme/apply",
        json={"theme_name_or_path": themes_list[0]["name"]},
    )
    assert resp_apply_theme.status_code == 200
    assert resp_apply_theme.json()["success"] is True

    # 3. Cursor API
    resp_cursor_get = client.get("/api/v1/windows/personalization/cursor")
    assert resp_cursor_get.status_code == 200

    resp_cursor_put = client.put(
        "/api/v1/windows/personalization/cursor",
        json={
            "size": 64,
            "color_scheme": "inverted",
            "shadow": True,
            "trails": False,
            "hide_while_typing": True,
            "show_location_on_ctrl": False,
            "pointer_speed": 12,
        },
    )
    assert resp_cursor_put.status_code == 200
    assert resp_cursor_put.json()["size"] == 64
    assert resp_cursor_put.json()["color_scheme"] == "inverted"

    # 4. Wallpaper API
    resp_wall_get = client.get("/api/v1/windows/personalization/wallpaper")
    assert resp_wall_get.status_code == 200

    resp_wall_put = client.put(
        "/api/v1/windows/personalization/wallpaper",
        json={
            "mode": "solid_color",
            "fit_mode": "fill",
            "background_color_hex": "#1E293B",
        },
    )
    assert resp_wall_put.status_code == 200
    assert resp_wall_put.json()["mode"] == "solid_color"

    # 5. AI Spotlight API
    resp_spotlight_current = client.get("/api/v1/windows/personalization/ai-spotlight/current")
    assert resp_spotlight_current.status_code == 200
    spotlight_data = resp_spotlight_current.json()
    assert "title" in spotlight_data
    assert "description_ru" in spotlight_data

    resp_spotlight_gallery = client.get("/api/v1/windows/personalization/ai-spotlight/gallery")
    assert resp_spotlight_gallery.status_code == 200
    assert len(resp_spotlight_gallery.json()) > 0
