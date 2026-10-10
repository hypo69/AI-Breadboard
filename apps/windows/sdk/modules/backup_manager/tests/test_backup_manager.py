# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Backup_Manager Tests - Test Backup Manager
# =============================================================================
# Description:
#   Модуль реализации компонентов подсистемы Windows AI-Breadboard (test_backup_manager).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.backup_manager.tests.test_backup_manager import test_libraries_creation_and_parse
#
#     res = test_libraries_creation_and_parse()
#
# File: test_backup_manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.backup_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Модуль реализации компонентов подсистемы Windows AI-Breadboard (test_backup_manager)."""

import pytest
from pathlib import Path
from apps.windows.sdk.modules.backup_manager.core.libraries_manager import WindowsLibrariesManager
from apps.windows.sdk.modules.backup_manager.core.file_history_manager import FileHistoryManager
from apps.windows.sdk.modules.backup_manager.core.health_checker import BackupHealthChecker

def test_libraries_creation_and_parse(tmp_path: Path):
    mgr = WindowsLibrariesManager(libraries_dir=tmp_path)
    source_dir = tmp_path / 'MyProject'
    source_dir.mkdir()
    lib = mgr.create_library('TestLib', [str(source_dir)], is_pinned=True)
    assert lib.name == 'TestLib'
    assert lib.folder_count == 1
    assert lib.folders[0].exists is True
    all_libs = mgr.get_all_libraries()
    assert len(all_libs) == 1
    assert all_libs[0].name == 'TestLib'

def test_health_checker_report():
    checker = BackupHealthChecker()
    report = checker.generate_report()
    assert report.health_score >= 0
    assert report.health_score <= 100
    assert isinstance(report.recommendations, list)

def test_backup_health_api_endpoint():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from apps.windows.sdk.modules.backup_manager.router import init_router
    app = FastAPI()
    app.include_router(init_router())
    client = TestClient(app)
    response = client.get('/api/v1/windows-backup/health')
    assert response.status_code == 200
    data = response.json()
    assert 'health_score' in data
    assert 'file_history' in data
    assert 'libraries' in data