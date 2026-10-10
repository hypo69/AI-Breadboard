# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Window Control Plane
# =============================================================================
# Description:
#   Комплексный набор модульных тестов (TDD) для Windows Window Management Control Plane.
#   Проверяет целостность каталога (295 параметров по 15 категориям), поиск, резолвер,
#   предварительный просмотр (Dry-Run), применение, пакетные операции, откат и FastAPI роутер.
#
# Usage Examples:
#   pytest apps/windows/tests/test_window_control_plane.py -v
#
# File: test_window_control_plane.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:00:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для Windows Window Management Control Plane (295 параметров)."""

import pytest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.sdk.modules.window_control_plane.catalog import (
    WindowControlPlaneCatalog,
    get_window_catalog,
)
from apps.windows.sdk.modules.window_control_plane.models import (
    BatchApplyRequest,
    BatchSettingItem,
    DocStatus,
    RiskLevel,
    SettingApplyRequest,
    SettingCategory,
    SettingValueType,
    SupportStatus,
)
from apps.windows.sdk.modules.window_control_plane.resolver import WindowBackendResolver
from apps.windows.sdk.modules.window_control_plane.manager import WindowManagementControlPlane
from apps.windows.sdk.modules.window_control_plane.router import init_router


@pytest.fixture
def catalog() -> WindowControlPlaneCatalog:
    """Фикстура каталога параметров."""
    return get_window_catalog()


@pytest.fixture
def resolver() -> WindowBackendResolver:
    """Фикстура низкоуровневого резолвера."""
    return WindowBackendResolver()


@pytest.fixture
def temp_plane(tmp_path: Path, catalog: WindowControlPlaneCatalog, resolver: WindowBackendResolver) -> WindowManagementControlPlane:
    """Фикстура изолированного Control Plane с временной базой SQLite и файлом аудита."""
    from apps.windows.sdk.modules.window_control_plane.history import WindowManagementHistoryManager

    history_file = tmp_path / "test_history.json"
    history_db = tmp_path / "temp_telemetry.db"
    history_mgr = WindowManagementHistoryManager(db_path=history_db)

    return WindowManagementControlPlane(
        catalog=catalog,
        resolver=resolver,
        history_manager=history_mgr,
        history_file=history_file,
    )


@pytest.fixture
def test_client() -> TestClient:
    """Фикстура тестового HTTP-клиента FastAPI."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


# =============================================================================
# 1. Тесты полноты и целостности каталога (295 параметров)
# =============================================================================
def test_catalog_total_count(catalog: WindowControlPlaneCatalog):
    """Проверка точного количества параметров в каталоге (ровно 295)."""
    items = catalog.get_all()
    assert len(items) == 295, f"Ожидалось 295 параметров, получено {len(items)}"


def test_catalog_indices_integrity(catalog: WindowControlPlaneCatalog):
    """Проверка непрерывности и уникальности индексов от 1 до 295."""
    items = catalog.get_all()
    indices = [item.index for item in items]
    assert len(indices) == len(set(indices)), "Обнаружены дубликаты индексов в каталоге"
    assert min(indices) == 1, f"Минимальный индекс {min(indices)} != 1"
    assert max(indices) == 295, f"Максимальный индекс {max(indices)} != 295"
    assert set(indices) == set(range(1, 296)), "Присутствуют пропуски в индексах параметров"


def test_catalog_ids_unique(catalog: WindowControlPlaneCatalog):
    """Проверка уникальности всех строковых идентификаторов параметров."""
    items = catalog.get_all()
    ids = [item.id for item in items]
    assert len(ids) == len(set(ids)), "Обнаружены дубликаты строковых id параметров"
    for item in items:
        assert item.id.startswith("window."), f"Идентификатор {item.id} должен начинаться с 'window.'"
        assert len(item.name) > 0
        assert len(item.name_ru) > 0
        assert len(item.description) > 0
        assert len(item.description_ru) > 0


def test_catalog_all_15_categories_present(catalog: WindowControlPlaneCatalog):
    """Проверка наличия параметров во всех 15 системных категориях."""
    overview = catalog.get_categories_overview()
    assert len(overview) == 15, "Должно присутствовать ровно 15 системных категорий"

    for cat_info in overview:
        assert cat_info["total_items"] > 0, f"Категория {cat_info['name']} не содержит параметров"

    summary = catalog.get_summary()
    assert summary.total_settings == 295
    assert summary.categories_count == 15
    assert sum(summary.by_category.values()) == 295


def test_catalog_category_breakdown(catalog: WindowControlPlaneCatalog):
    """Проверка соответствия количества элементов конспекту по категориям."""
    cat_items = {
        SettingCategory.FOCUS_ACTIVATION: 15,
        SettingCategory.ANIMATIONS_VISUAL_EFFECTS: 20,
        SettingCategory.WINDOW_GEOMETRY_METRICS: 20,
        SettingCategory.WINDOW_ARRANGEMENT_SNAP: 20,
        SettingCategory.ALT_TAB_TASK_SWITCHING: 15,
        SettingCategory.VIRTUAL_DESKTOPS: 12,
        SettingCategory.DWM_WINDOW_COMPOSITION: 20,
        SettingCategory.TASKBAR_APP_SWITCHING: 25,
        SettingCategory.MOUSE_WINDOW_BEHAVIOUR: 21,
        SettingCategory.KEYBOARD_FOCUS_NAVIGATION: 20,
        SettingCategory.ACCESSIBILITY_PRESENTATION: 20,
        SettingCategory.DISPLAY_MULTI_MONITOR: 27,
        SettingCategory.DESKTOP_EXPLORER: 20,
        SettingCategory.THEME_WINDOW_METRICS: 20,
        SettingCategory.SHELL_POLICY_CONTROLS: 20,
    }

    total = 0
    for cat, expected_count in cat_items.items():
        actual = len(catalog.get_by_category(cat))
        assert actual == expected_count, f"Категория {cat.value}: ожидалось {expected_count}, получено {actual}"
        total += actual

    assert total == 295


# =============================================================================
# 2. Тесты поиска и фильтрации
# =============================================================================
def test_search_by_text(catalog: WindowControlPlaneCatalog):
    """Тест полнотекстового поиска по русскому и английскому названию."""
    res_en = catalog.search(query="Foreground Lock Timeout")
    assert len(res_en) >= 1
    assert res_en[0].id == "window.focus.foreground_lock_timeout"

    res_ru = catalog.search(query="Таймаут блокировки")
    assert len(res_ru) >= 1
    assert res_ru[0].id == "window.focus.foreground_lock_timeout"


def test_filter_by_category_and_risk(catalog: WindowControlPlaneCatalog):
    """Тест комбинированной фильтрации по категории и уровню риска."""
    safe_focus = catalog.search(category=SettingCategory.FOCUS_ACTIVATION, risk=RiskLevel.SAFE)
    assert len(safe_focus) > 0
    for item in safe_focus:
        assert item.category == SettingCategory.FOCUS_ACTIVATION
        assert item.risk == RiskLevel.SAFE


def test_filter_by_elevation(catalog: WindowControlPlaneCatalog):
    """Тест фильтрации настроек, требующих прав администратора."""
    admin_items = catalog.search(requires_elevation=True)
    assert len(admin_items) > 0
    for item in admin_items:
        assert item.requires_elevation is True


# =============================================================================
# 3. Тесты Backend Resolver
# =============================================================================
def test_resolver_read_value(catalog: WindowControlPlaneCatalog, resolver: WindowBackendResolver):
    """Тест чтения значения параметра через резолвер."""
    setting = catalog.get_by_id("window.focus.foreground_lock_timeout")
    assert setting is not None
    val_resp = resolver.read_value(setting)
    assert val_resp.setting_id == setting.id
    assert val_resp.value_type == "duration_ms"
    assert val_resp.unit == "ms"


def test_resolver_preview_valid_and_invalid(catalog: WindowControlPlaneCatalog, resolver: WindowBackendResolver):
    """Тест симуляции изменений с корректными и некорректными значениями."""
    setting = catalog.get_by_id("window.focus.active_window_tracking_delay")
    assert setting is not None

    # Валидное число
    prev_ok = resolver.preview_change(setting, 750)
    assert prev_ok.is_valid is True
    assert prev_ok.new_value == 750
    assert prev_ok.validation_error is None

    # Выход за диапазон (min_val=0, max_val=10000)
    prev_out = resolver.preview_change(setting, 999999)
    assert prev_out.is_valid is False
    assert "превышает допустимый максимум" in prev_out.validation_error

    # Некорректный тип
    prev_invalid = resolver.preview_change(setting, "not_a_number")
    assert prev_invalid.is_valid is False


def test_resolver_preview_enum(catalog: WindowControlPlaneCatalog, resolver: WindowBackendResolver):
    """Тест валидации параметров с типом ENUM."""
    setting = catalog.get_by_id("window.display.monitor_orientation")
    assert setting is not None

    # Допустимое значение
    prev_ok = resolver.preview_change(setting, "portrait")
    assert prev_ok.is_valid is True

    # Недопустимое значение
    prev_bad = resolver.preview_change(setting, "diagonal_360")
    assert prev_bad.is_valid is False
    assert "недопустимо" in prev_bad.validation_error


# =============================================================================
# 4. Тесты Control Plane Manager (Apply, Batch, Rollback)
# =============================================================================
def test_manager_apply_and_rollback(temp_plane: WindowManagementControlPlane):
    """Тест применения настройки с последующим откатом к старому значению."""
    setting_id = "window.focus.foreground_flash_count"
    req = SettingApplyRequest(
        value=12,
        custom_comment="Тестовое изменение количества миганий",
    )

    res = temp_plane.apply_setting(setting_id, req)
    assert res.success is True
    assert res.setting_id == setting_id
    assert res.new_value == 12
    assert res.change_id is not None

    # Проверяем запись в истории
    history = temp_plane.get_history()
    assert len(history) == 1
    assert history[0]["change_id"] == res.change_id
    assert history[0]["rolled_back"] is False

    # Выполняем откат
    rollback_res = temp_plane.rollback_change(res.change_id)
    assert rollback_res.rolled_back is True

    # Повторный откат должен вернуть отказ
    rollback_res2 = temp_plane.rollback_change(res.change_id)
    assert rollback_res2.rolled_back is False
    assert "уже было откатано" in rollback_res2.message


def test_manager_batch_apply(temp_plane: WindowManagementControlPlane):
    """Тест пакетного применения настроек."""
    batch_req = BatchApplyRequest(
        settings=[
            BatchSettingItem(setting_id="window.focus.active_window_tracking", value=True),
            BatchSettingItem(setting_id="window.taskbar.alignment", value=1),
        ],
        create_restore_point=False,
        comment="Пакетный тест",
    )

    batch_resp = temp_plane.apply_batch(batch_req)
    assert batch_resp.total_requested == 2
    assert batch_resp.successful_count == 2
    assert len(batch_resp.results) == 2


# =============================================================================
# 5. Тесты FastAPI REST API Роутера
# =============================================================================
def test_api_get_summary(test_client: TestClient):
    """Тест эндпоинта GET /api/v1/window-management/summary."""
    resp = test_client.get("/api/v1/window-management/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_settings"] == 295
    assert data["categories_count"] == 15
    assert "by_category" in data


def test_api_get_categories(test_client: TestClient):
    """Тест эндпоинта GET /api/v1/window-management/categories."""
    resp = test_client.get("/api/v1/window-management/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_categories"] == 15
    assert len(data["categories"]) == 15


def test_api_get_catalog_filtered(test_client: TestClient):
    """Тест эндпоинта GET /api/v1/window-management/catalog с параметрами поиска."""
    resp = test_client.get("/api/v1/window-management/catalog?category=dwm_window_composition")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 20
    assert len(data["settings"]) == 20


def test_api_get_setting_details(test_client: TestClient):
    """Тест эндпоинта GET /api/v1/window-management/settings/{id}."""
    resp = test_client.get("/api/v1/window-management/settings/window.focus.foreground_lock_timeout")
    assert resp.status_code == 200
    data = resp.json()
    assert data["definition"]["id"] == "window.focus.foreground_lock_timeout"
    assert "live_state" in data


def test_api_preview_endpoint(test_client: TestClient):
    """Тест эндпоинта POST /api/v1/window-management/settings/{id}/preview."""
    resp = test_client.post(
        "/api/v1/window-management/settings/window.focus.foreground_lock_timeout/preview",
        json={"value": 300000},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["new_value"] == 300000


def test_api_apply_and_history(test_client: TestClient):
    """Тест применения настройки через API и проверки истории в telemetry.db."""
    resp = test_client.post(
        "/api/v1/window-management/settings/window.anim.window_animation/apply",
        json={"value": True, "create_restore_point": False, "custom_comment": "API Test Animation"},
    )
    assert resp.status_code == 200
    apply_data = resp.json()
    assert apply_data["success"] is True
    change_id = apply_data["change_id"]

    # Проверка истории из telemetry.db
    hist_resp = test_client.get("/api/v1/window-management/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    items = hist_data if isinstance(hist_data, list) else hist_data.get("history", [])
    assert len(items) >= 1
    assert any(h.get("change_id") == change_id for h in items)

    # Откат по change_id
    rb_resp = test_client.post(f"/api/v1/window-management/rollback/{change_id}")
    assert rb_resp.status_code == 200
    assert rb_resp.json()["rolled_back"] is True


def test_telemetry_db_sqlite_persistence(tmp_path: Path):
    """Тест прямой записи и выборки из таблицы window_management_history в SQLite telemetry.db."""
    from apps.windows.sdk.modules.window_control_plane.history import WindowManagementHistoryManager

    db_file = tmp_path / "test_telemetry.db"
    mgr = WindowManagementHistoryManager(db_path=db_file)

    # 1. Запись изменения
    row_id = mgr.record_change(
        change_id="test-change-uuid-1",
        setting_id="window.focus.active_window_tracking",
        setting_name="Active Window Tracking",
        category="focus_activation",
        backend_type="spi",
        scope="user",
        risk_level="safe",
        old_value=False,
        new_value=True,
        action_type="APPLY",
        operator="TestRunner",
        reason="Unit testing SQLite logging",
    )
    assert row_id > 0

    # 2. Чтение истории
    history = mgr.get_history(limit=10)
    assert len(history) == 1
    entry = history[0]
    assert entry["change_id"] == "test-change-uuid-1"
    assert entry["setting_id"] == "window.focus.active_window_tracking"
    assert entry["old_value"] is False
    assert entry["new_value"] is True
    assert entry["is_rolled_back"] is False

    # 3. Пометка отката
    ok = mgr.mark_as_rolled_back("test-change-uuid-1", rolled_back_by="Admin")
    assert ok is True

    # 4. Проверка обновленного статуса
    updated = mgr.get_by_change_id("test-change-uuid-1")
    assert updated is not None
    assert updated["is_rolled_back"] is True
    assert updated["rolled_back_by"] == "Admin"
    assert updated["rolled_back_at"] is not None


def test_rollback_last_action(test_client: TestClient):
    """Тест быстрого отката последнего действия через API /rollback-last."""
    # Применяем изменение
    apply_resp = test_client.post(
        "/api/v1/window-management/settings/window.focus.active_window_tracking_delay/apply",
        json={"value": 500, "create_restore_point": False, "custom_comment": "Test Rollback Last"},
    )
    assert apply_resp.status_code == 200
    assert apply_resp.json()["success"] is True

    # Быстрый откат
    rb_last = test_client.post("/api/v1/window-management/rollback-last")
    assert rb_last.status_code == 200
    assert rb_last.json()["rolled_back"] is True

