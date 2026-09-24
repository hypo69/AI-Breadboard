# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for User Folders & Storage Relocation Manager
# =============================================================================
# Description:
#   Тестирование обнаружения пользовательских папок, вычисления их размеров,
#   определения доступных дисков, безопасного переноса и API-эндпоинтов.
#
# File: test_user_folders_manager.py
# Package: apps.windows.backup_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модульные тесты для модуля UserFoldersManager и роутера."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from apps.windows.backup_manager.core.models import TargetDriveInfo
from apps.windows.backup_manager.core.user_folders_manager import UserFoldersManager
from apps.windows.backup_manager.router import init_router


@pytest.fixture
def temp_folders(tmp_path: Path):
    """Создает тестовую структуру пользовательской папки и целевого диска."""
    src_dir = tmp_path / "SourceDownloads"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "test1.txt").write_text("Hello World 1", encoding="utf-8")
    (src_dir / "subfolder").mkdir(exist_ok=True)
    (src_dir / "subfolder" / "test2.txt").write_text("Hello World 2", encoding="utf-8")

    dst_base = tmp_path / "TargetDrive"
    dst_base.mkdir(parents=True, exist_ok=True)

    return src_dir, dst_base


def test_user_folders_discovery_and_size(tmp_path: Path):
    """Тест сканирования пользовательских директорий и расчета их объема."""
    mock_lib_mgr = MagicMock()
    mgr = UserFoldersManager(lib_mgr=mock_lib_mgr)

    # Проверяем метод _calculate_directory_size
    test_dir = tmp_path / "FolderSizeTest"
    test_dir.mkdir()
    (test_dir / "file1.bin").write_bytes(b"0" * 1024)
    (test_dir / "file2.bin").write_bytes(b"0" * 2048)

    total_bytes, file_count = mgr._calculate_directory_size(str(test_dir))
    assert total_bytes == 3072
    assert file_count == 2

    # Проверяем получение списка папок
    folders = mgr.get_user_folders()
    assert len(folders) >= 6
    folder_ids = [f.folder_id for f in folders]
    assert "Personal" in folder_ids
    assert "Downloads" in folder_ids
    assert "Desktop" in folder_ids


def test_get_available_drives_and_overview():
    """Тест получения списка дисков и сводки overview."""
    mock_lib_mgr = MagicMock()
    mgr = UserFoldersManager(lib_mgr=mock_lib_mgr)

    drives = mgr.get_available_drives()
    assert isinstance(drives, list)
    if drives:
        assert any(d.is_system_drive for d in drives)

    overview = mgr.get_overview()
    assert len(overview.folders) >= 6
    assert isinstance(overview.total_user_size_mb, float)
    assert isinstance(overview.available_target_drives, list)


def test_relocate_folder_success(tmp_path: Path):
    """Тест успешного переноса пользовательской папки."""
    mock_lib_mgr = MagicMock()
    mgr = UserFoldersManager(lib_mgr=mock_lib_mgr)

    fake_src = tmp_path / "Downloads"
    fake_src.mkdir(exist_ok=True)
    (fake_src / "file1.txt").write_text("Data 1", encoding="utf-8")
    (fake_src / "file2.txt").write_text("Data 2", encoding="utf-8")

    dst_dir = tmp_path / "TargetD"

    with patch.object(mgr, "_read_registry_path", return_value=str(fake_src)), \
         patch.object(mgr, "_update_registry_paths", return_value=True), \
         patch("psutil.disk_usage") as mock_usage, \
         patch("pathlib.Path.home", return_value=Path("C:/Users/testuser")):

        mock_usage.return_value = MagicMock(free=100 * 1024 * 1024 * 1024, total=500 * 1024 * 1024 * 1024)

        # Мокаем shutil.copy2 и mkdir
        with patch("shutil.copy2", return_value=None), \
             patch("pathlib.Path.mkdir", return_value=None):
            res = mgr.relocate_folder("Downloads", "D:", delete_source_after=False)

        assert res.success is True
        assert res.folder_id == "Downloads"
        assert res.files_copied == 2
        mock_lib_mgr.add_folder_to_library.assert_called_once()




def test_relocate_folder_insufficient_space(temp_folders):
    """Тест отказа в переносе при нехватке свободного места."""
    src_dir, dst_base = temp_folders
    mock_lib_mgr = MagicMock()
    mgr = UserFoldersManager(lib_mgr=mock_lib_mgr)

    with patch.object(mgr, "_read_registry_path", return_value=str(src_dir)), \
         patch("psutil.disk_usage") as mock_usage:

        # 0 байт свободно
        mock_usage.return_value = MagicMock(free=100, total=500 * 1024 * 1024 * 1024)

        res = mgr.relocate_folder("Downloads", "D:", delete_source_after=False)
        assert res.success is False
        assert "Недостаточно места" in res.message


def test_user_folders_api_endpoints():
    """Тест REST API эндпоинтов для пользовательских папок."""
    app = FastAPI()
    app.include_router(init_router())
    client = TestClient(app)

    # 1. GET /api/v1/windows-backup/user-folders/overview
    resp = client.get("/api/v1/windows-backup/user-folders/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "folders" in data
    assert "drives" in data
    assert len(data["folders"]) >= 6

    # 2. POST /api/v1/windows-backup/user-folders/relocate с невалидным folder_id
    resp_invalid = client.post(
        "/api/v1/windows-backup/user-folders/relocate",
        json={"folder_id": "UnknownFolderXYZ", "target_drive_letter": "D:", "delete_source_after": False}
    )
    assert resp_invalid.status_code == 400
