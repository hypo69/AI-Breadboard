# -*- coding: utf-8 -*-
import pytest
from pathlib import Path
from apps.windows_backup_manager.core.libraries_manager import WindowsLibrariesManager
from apps.windows_backup_manager.core.file_history_manager import FileHistoryManager
from apps.windows_backup_manager.core.health_checker import BackupHealthChecker

def test_libraries_creation_and_parse(tmp_path: Path):
    mgr = WindowsLibrariesManager(libraries_dir=tmp_path)
    
    # Создаем папку-источник
    source_dir = tmp_path / "MyProject"
    source_dir.mkdir()
    
    lib = mgr.create_library("TestLib", [str(source_dir)], is_pinned=True)
    assert lib.name == "TestLib"
    assert lib.folder_count == 1
    assert lib.folders[0].exists is True
    
    # Проверяем повторный парсинг из каталога
    all_libs = mgr.get_all_libraries()
    assert len(all_libs) == 1
    assert all_libs[0].name == "TestLib"

def test_health_checker_report():
    checker = BackupHealthChecker()
    report = checker.generate_report()
    assert report.health_score >= 0
    assert report.health_score <= 100
    assert isinstance(report.recommendations, list)