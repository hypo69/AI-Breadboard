# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Standalone Registry Viewer App
# =============================================================================
# Description:
#   Тесты для автономного приложения Windows Registry Viewer (apps.windows.registry).
#
# File: test_app_registry_viewer.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для приложения Windows Registry Viewer."""

import json
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.registry import (
    BookmarkItem,
    RegistryKeyDetailsDTO,
    RegistryValueDTO,
    RegistryViewer,
    RegistryViewerTUI,
    SearchResponseDTO,
    init_router,
)


@pytest.fixture
def viewer():
    """Фикстура экземпляра RegistryViewer."""
    return RegistryViewer()


@pytest.fixture
def client(viewer):
    """Фикстура TestClient для автономного роутера RegistryViewer."""
    app = FastAPI()
    app.include_router(init_router(viewer))
    return TestClient(app)


def test_registry_viewer_bookmarks(viewer):
    """Проверка получения списка закладок через ядро RegistryViewer."""
    bookmarks = viewer.get_bookmarks()
    assert len(bookmarks) >= 6
    assert isinstance(bookmarks[0], BookmarkItem)

    startup_bm = viewer.get_bookmark_by_id("startup_run")
    assert startup_bm is not None
    assert startup_bm.hive == "HKEY_CURRENT_USER"
    assert "Run" in startup_bm.path

    non_existent = viewer.get_bookmark_by_id("non_existent_bookmark_id")
    assert non_existent is None


def test_registry_viewer_read_key(viewer):
    """Проверка чтения раздела реестра через ядро RegistryViewer."""
    details = viewer.read_key(hive="HKEY_LOCAL_MACHINE", path="SOFTWARE")
    assert isinstance(details, RegistryKeyDetailsDTO)
    assert details.hive == "HKEY_LOCAL_MACHINE"
    assert isinstance(details.subkeys, list)
    assert isinstance(details.values, list)
    assert details.subkeys_count == len(details.subkeys)
    assert details.values_count == len(details.values)


def test_registry_viewer_search(viewer):
    """Проверка поиска по реестру через ядро RegistryViewer."""
    response = viewer.search(
        query="Windows",
        hive="HKEY_LOCAL_MACHINE",
        path="SOFTWARE",
        max_results=5,
    )
    assert isinstance(response, SearchResponseDTO)
    assert response.status == "ok"
    assert isinstance(response.results, list)
    assert len(response.results) <= 5


def test_registry_viewer_exports(viewer, tmp_path):
    """Проверка экспорта ключа реестра в форматы JSON и CSV."""
    details = viewer.read_key(hive="HKEY_LOCAL_MACHINE", path="SOFTWARE")

    # JSON экспорт
    json_str = viewer.export_key_to_json(details)
    parsed = json.loads(json_str)
    assert parsed["hive"] == "HKEY_LOCAL_MACHINE"

    json_file = tmp_path / "export.json"
    viewer.export_key_to_json(details, json_file)
    assert json_file.exists()
    assert "HKEY_LOCAL_MACHINE" in json_file.read_text(encoding="utf-8")

    # CSV экспорт
    csv_str = viewer.export_key_to_csv(details)
    assert "KeyPath,ValueName,Type,Data,SizeBytes" in csv_str

    csv_file = tmp_path / "export.csv"
    viewer.export_key_to_csv(details, csv_file)
    assert csv_file.exists()


def test_registry_viewer_tui(viewer):
    """Проверка генерации представлений TUI без ошибок."""
    tui = RegistryViewerTUI(viewer=viewer)

    # Рендеринг закладок
    tui.render_bookmarks()

    # Рендеринг деталей раздела
    details = viewer.read_key(hive="HKLM", path="SOFTWARE")
    tui.render_key_details(details)

    # Рендеринг поиска
    search_res = viewer.search("Windows", hive="HKLM", path="SOFTWARE", max_results=2)
    tui.render_search_results(search_res)


def test_api_endpoints_standalone(client):
    """Проверка эндпоинтов автономного FastAPI роутера."""
    # Bookmarks
    r_bm = client.get("/api/registry/bookmarks")
    assert r_bm.status_code == 200
    assert r_bm.json()["status"] == "ok"

    # Key
    r_key = client.get("/api/registry/key?hive=HKCU&path=Software")
    assert r_key.status_code == 200
    assert r_key.json()["hive"] == "HKEY_CURRENT_USER"

    # Search
    r_srch = client.get("/api/registry/search?hive=HKLM&path=SOFTWARE&query=Windows&max_results=3")
    assert r_srch.status_code == 200
    assert r_srch.json()["status"] == "ok"

    # Export JSON
    r_exp_json = client.get("/api/registry/export?hive=HKLM&path=SOFTWARE&format=json")
    assert r_exp_json.status_code == 200
    assert r_exp_json.headers["content-type"] == "application/json"

    # Export CSV
    r_exp_csv = client.get("/api/registry/export?hive=HKLM&path=SOFTWARE&format=csv")
    assert r_exp_csv.status_code == 200
    assert "text/csv" in r_exp_csv.headers["content-type"]


def test_registry_editor_operations_and_backups(tmp_path):
    """Проверка полного цикла создания, редактирования, бэкапа и отката параметров реестра."""
    from apps.windows.registry import (
        RegistryViewer,
        SetValueRequestDTO,
        DeleteValueRequestDTO,
        CreateKeyRequestDTO,
        DeleteKeyRequestDTO,
    )

    viewer = RegistryViewer(backup_dir=tmp_path / "backups")

    # 1. Создание подраздела
    key_res = viewer.create_key(
        CreateKeyRequestDTO(
            hive="HKCU",
            path="Software\\AIBreadboardTestKey",
        )
    )
    assert key_res.status == "ok"

    # 2. Создание параметра с авто-бэкапом
    set_res = viewer.set_value(
        SetValueRequestDTO(
            hive="HKCU",
            path="Software\\AIBreadboardTestKey",
            name="TestParam",
            type_name="REG_SZ",
            data="Hello Breadboard",
            create_backup=True,
        )
    )
    assert set_res.status == "ok"
    assert set_res.backup is not None
    backup_id = set_res.backup.backup_id

    # Проверяем, что бэкап зарегистрирован в списке
    backups = viewer.list_backups()
    assert any(b.backup_id == backup_id for b in backups)

    # 3. Изменение параметра на новое значение
    set_res_2 = viewer.set_value(
        SetValueRequestDTO(
            hive="HKCU",
            path="Software\\AIBreadboardTestKey",
            name="TestParam",
            type_name="REG_SZ",
            data="Modified Value",
            create_backup=True,
        )
    )
    assert set_res_2.status == "ok"

    # 4. Восстановление исходного состояния из бэкапа
    restore_res = viewer.restore_backup(backup_id)
    assert restore_res.status == "ok"
    assert restore_res.backup_id == backup_id

    # 5. Удаление параметра с бэкапом
    del_val_res = viewer.delete_value(
        DeleteValueRequestDTO(
            hive="HKCU",
            path="Software\\AIBreadboardTestKey",
            name="TestParam",
            create_backup=True,
        )
    )
    assert del_val_res.status == "ok"

    # 6. Удаление ключа
    del_key_res = viewer.delete_key(
        DeleteKeyRequestDTO(
            hive="HKCU",
            path="Software\\AIBreadboardTestKey",
            recursive=True,
            create_backup=False,
        )
    )
    assert del_key_res.status == "ok"


def test_api_editor_endpoints(client):
    """Проверка REST API эндпоинтов редактирования и бэкапов."""
    # Создание/изменение параметра
    payload = {
        "hive": "HKCU",
        "path": "Software\\AIBreadboardAPITest",
        "name": "ApiVal",
        "type_name": "REG_SZ",
        "data": "123",
        "create_backup": True,
    }
    r_post = client.post("/api/registry/value", json=payload)
    assert r_post.status_code == 200
    res_data = r_post.json()
    assert res_data["status"] == "ok"

    # Список бэкапов
    r_bks = client.get("/api/registry/backups")
    assert r_bks.status_code == 200
    assert "backups" in r_bks.json()

    # Удаление параметра
    r_del = client.request(
        "DELETE",
        "/api/registry/value",
        json={
            "hive": "HKCU",
            "path": "Software\\AIBreadboardAPITest",
            "name": "ApiVal",
            "create_backup": False,
        },
    )
    assert r_del.status_code == 200
    assert r_del.json()["status"] == "ok"

    # Удаление ключа
    r_del_key = client.request(
        "DELETE",
        "/api/registry/key",
        json={
            "hive": "HKCU",
            "path": "Software\\AIBreadboardAPITest",
            "recursive": True,
            "create_backup": False,
        },
    )
    assert r_del_key.status_code == 200

