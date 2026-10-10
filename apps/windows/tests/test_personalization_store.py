# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Personalization Store
# =============================================================================
# Description:
#   Тесты SQLite-хранилища персонализации (снимки + журнал изменений) и
#   Data-First эндпоинтов /state, /history, /theme.
#
# Usage Examples:
#   pytest apps/windows/tests/test_personalization_store.py -v
#
# File: test_personalization_store.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:20:00
# =============================================================================

from __future__ import annotations
"""Тесты PersonalizationStore и интеграции с PersonalizationManager."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.sdk.modules.personalization.manager import PersonalizationManager
from apps.windows.sdk.modules.personalization.models import ThemeApplyRequest
from apps.windows.sdk.modules.personalization.store import PersonalizationStore
from apps.windows.sdk.modules.window_control_plane.history import WindowManagementHistoryManager


@pytest.fixture
def store(tmp_path: Path) -> PersonalizationStore:
    return PersonalizationStore(tmp_path / 'telemetry.db')


@pytest.fixture
def manager(tmp_path: Path) -> PersonalizationManager:
    history = WindowManagementHistoryManager(db_path=tmp_path / 'telemetry.db')
    return PersonalizationManager(history_manager=history)


def test_snapshot_roundtrip(store: PersonalizationStore) -> None:
    assert store.latest_snapshot() is None
    store.add_snapshot({'cursor_size': 48, 'cursor_type': 'custom', 'cursor_color_hex': '#FFCC00'})
    snap = store.latest_snapshot()
    assert snap['cursor_size'] == 48 and snap['cursor_color_hex'] == '#FFCC00'
    assert snap['dwm_accent_color_hex'] == '#0078D4'  # значение по умолчанию схемы
    store.add_snapshot({'cursor_size': 64})
    assert store.latest_snapshot()['cursor_size'] == 64


def test_snapshot_rejects_unknown_column(store: PersonalizationStore) -> None:
    with pytest.raises(ValueError):
        store.add_snapshot({'evil; DROP TABLE x': 1})


def test_change_history(store: PersonalizationStore) -> None:
    store.record_change('CURSOR', 'cursor_size', 32, 48, 'REST_API')
    store.record_change('THEME', 'apps_use_light_theme', 1, 0)
    rows = store.history(limit=10)
    assert [r['parameter_name'] for r in rows] == ['apps_use_light_theme', 'cursor_size']
    assert rows[1]['old_value'] == '32' and rows[1]['changed_by'] == 'REST_API'
    assert rows[0]['changed_by'] == 'USER_UI'
    assert [r['parameter_name'] for r in store.history(group='CURSOR')] == ['cursor_size']


def test_apply_theme_is_audited_and_snapshotted(manager: PersonalizationManager) -> None:
    manager.apply_theme(ThemeApplyRequest(theme_name_or_path='X'))
    assert manager.store.latest_snapshot() is not None  # снимок фиксируется после изменения


def test_get_state_shape(manager: PersonalizationManager) -> None:
    state = manager.get_state()
    assert set(state) == {'cursor', 'theme', 'wallpaper', 'taskbar', 'last_updated'}
    assert 1 <= state['cursor']['size'] <= 128
    assert isinstance(state['theme']['apps_use_light_theme'], bool)
    assert state['theme']['accent_color_hex'].startswith('#')
    assert state['taskbar']['alignment'] in ('left', 'center')
    assert manager.get_state()['last_updated'] == state['last_updated']  # второй вызов из SQLite без нового снимка


def test_rest_state_history_theme(manager: PersonalizationManager) -> None:
    from apps.windows.sdk.modules.personalization import router as r_mod

    r_mod._pm = manager
    app = FastAPI()
    app.include_router(r_mod.router, prefix='/api/v1/windows/personalization')
    client = TestClient(app)
    assert client.get('/api/v1/windows/personalization/state').status_code == 200
    assert client.post('/api/v1/windows/personalization/theme', json={'theme_name_or_path': 'X'}).status_code == 200
    assert client.get('/api/v1/windows/personalization/history').status_code == 200
