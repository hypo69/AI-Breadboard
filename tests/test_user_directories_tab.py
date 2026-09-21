# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for User Directories Tab and API
# =============================================================================
# Description:
#   Тестирует REST API эндпоинты управления пользовательскими директориями,
#   статистику хранилища, получение дерева файлов, предпросмотр,
#   осиротевшие каталоги и наличие статических файлов вкладки.
#
# File: test_user_directories_tab.py
# Project: AI-Breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for user directories tab and REST API."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from header import __root__
from main import app
from src.user_manager import user_manager

client = TestClient(app)


class TestUserDirectoriesApi:
    """Набор тестов для REST API роутера user-directories."""

    @pytest.fixture(autouse=True)
    def setup_test_files(self, tmp_path, monkeypatch):
        """Создание временных тестовых файлов в хранилище пользователя."""
        user_dir = user_manager.get_user_directory(1, create=True)
        test_file = user_dir / "files" / "test_doc.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Hello AI-Breadboard User Directories!", encoding="utf-8")

        test_json = user_dir / "rag" / "sample.json"
        test_json.parent.mkdir(parents=True, exist_ok=True)
        test_json.write_text(json.dumps({"key": "value", "status": "active"}), encoding="utf-8")

        yield

    def test_get_storage_summary(self):
        """Проверка получения сводной информации о хранилище."""
        res = client.get("/api/admin/user-directories/summary")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("status") == "ok"
        summary = data.get("summary", {})
        assert "total_users" in summary
        assert "total_storage_bytes" in summary
        assert "total_files_count" in summary
        assert "top_extensions" in summary

    def test_get_users_directories_list(self):
        """Проверка получения списка пользователей со статистикой диска."""
        res = client.get("/api/admin/user-directories/users")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"
        users = data.get("users", [])
        assert len(users) > 0
        user_1 = next((u for u in users if u["id"] == 1), None)
        assert user_1 is not None
        assert "size_bytes" in user_1
        assert "files_count" in user_1
        assert "subfolders" in user_1
        assert "files" in user_1["subfolders"]

    def test_get_user_file_tree(self):
        """Проверка получения дерева файлов конкретного пользователя."""
        res = client.get("/api/admin/user-directories/users/1/tree")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"
        assert data.get("user_id") == 1
        items = data.get("items", [])
        assert len(items) > 0

        # Поиск по имени файла
        res_search = client.get("/api/admin/user-directories/users/1/tree?q=test_doc")
        assert res_search.status_code == 200
        search_items = res_search.json().get("items", [])
        assert any("test_doc.txt" in item["name"] for item in search_items)

        # Фильтр по расширению
        res_ext = client.get("/api/admin/user-directories/users/1/tree?extension=json")
        assert res_ext.status_code == 200
        ext_items = res_ext.json().get("items", [])
        assert all(item["extension"] == "json" for item in ext_items if not item["is_dir"])

    def test_preview_user_file(self):
        """Проверка безопасного предпросмотра текстового файла."""
        res = client.get("/api/admin/user-directories/users/1/file/preview?path=files/test_doc.txt")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"
        assert data.get("is_text") is True
        assert "Hello AI-Breadboard" in data.get("content", "")

    def test_download_user_file(self):
        """Проверка скачивания файла пользователя."""
        res = client.get("/api/admin/user-directories/users/1/file/download?path=files/test_doc.txt")
        assert res.status_code == 200
        assert "Hello AI-Breadboard" in res.text

    def test_orphaned_directories_api(self):
        """Проверка API поиска осиротевших директорий."""
        res = client.get("/api/admin/user-directories/orphaned")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"
        assert "total" in data
        assert "orphaned_dirs" in data


class TestUserDirectoriesStaticAndConfig:
    """Тестирование наличия статических файлов и конфигурации вкладки."""

    def test_static_files_exist(self):
        """Проверка существования файлов user_directories_tab."""
        tab_dir = __root__ / "src" / "api" / "webgui" / "user_directories_tab"
        assert tab_dir.exists(), "user_directories_tab directory must exist"
        assert (tab_dir / "index.html").exists(), "index.html must exist"
        assert (tab_dir / "main.js").exists(), "main.js must exist"
        assert (tab_dir / "README.md").exists(), "README.md must exist"

    def test_apps_tabs_config_contains_user_directories(self):
        """Проверка регистрации в tabs-config.js."""
        cfg_path = __root__ / "src" / "api" / "webgui" / "apps" / "modules" / "tabs-config.js"
        assert cfg_path.exists()
        content = cfg_path.read_text(encoding="utf-8")
        assert "user_directories" in content
        assert "user-directories" in content

    def test_locales_contain_user_directories_keys(self):
        """Проверка локализаций на наличие ключей userDirectories."""
        locales_dir = __root__ / "src" / "api" / "webgui" / "locales"
        for lang in ["ru.json", "en.json", "he.json"]:
            path = locales_dir / lang
            assert path.exists()
            data = json.loads(path.read_text(encoding="utf-8"))
            tabs = data.get("tabs", {})
            assert "userDirectories" in tabs, f"userDirectories missing in {lang}"
