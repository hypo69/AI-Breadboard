# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Windows File Auditor
# =============================================================================
# Description:
#   Тесты для Windows File Deletion & System Auditing Engine:
#   - Парсинг и корреляция событий 4663/4660
#   - Проверка моделей AuditPolicyStatus и FolderSaclStatus
#   - Проверка REST API эндпоинтов /api/sysadmin/file-audit/*
#
# File: test_file_auditor.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты модуля аудита файловой системы и регистрации удаления файлов."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from apps.windows_sysadmin.src.file_auditor import (
    AuditPolicyStatus,
    FileAuditEvent,
    FolderSaclStatus,
    WindowsFileAuditor,
)
from apps.windows_sysadmin.src.directory_watcher import (
    DirectoryWatcher,
    LiveFileEvent,
)
from apps.windows_sysadmin.router import init_router
from fastapi import FastAPI


@pytest.fixture
def auditor():
    """Фикстура экземпляра WindowsFileAuditor."""
    return WindowsFileAuditor()


@pytest.fixture
def client():
    """Фикстура TestClient для FastAPI роутера sysadmin."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_parse_and_correlate_events(auditor):
    """Тест парсинга и корреляции событий 4663 и 4660 по HandleId."""
    raw_events = [
        {
            "Id": 4663,
            "TimeCreated": "2026-09-18 20:00:00",
            "Message": "An attempt was made to access an object.",
            "EventData": {
                "ObjectName": "C:\\AI-Breadboard\\secret_file.txt",
                "ObjectType": "File",
                "ProcessName": "C:\\Windows\\System32\\cmd.exe",
                "ProcessId": "0x1a2b",
                "SubjectUserName": "onela",
                "SubjectDomainName": "WORKSTATION",
                "SubjectLogonId": "0x12345",
                "HandleId": "0x9999",
                "AccessMask": "0x10000",
                "AccessList": "DELETE\n",
            },
        },
        {
            "Id": 4660,
            "TimeCreated": "2026-09-18 20:00:01",
            "Message": "An object was deleted.",
            "EventData": {
                "HandleId": "0x9999",
                "SubjectUserName": "onela",
            },
        },
    ]

    events = auditor._parse_and_correlate_events(raw_events)
    assert len(events) == 2

    ev_4663 = events[0]
    assert ev_4663.event_id == 4663
    assert ev_4663.object_name == "C:\\AI-Breadboard\\secret_file.txt"
    assert ev_4663.is_deletion is True
    assert ev_4663.process_id == 0x1a2b

    ev_4660 = events[1]
    assert ev_4660.event_id == 4660
    assert ev_4660.is_deletion is True
    # Проверяем, что имя файла успешно скоррелировано по HandleId
    assert ev_4660.object_name == "C:\\AI-Breadboard\\secret_file.txt"
    assert ev_4660.process_name == "C:\\Windows\\System32\\cmd.exe"


def test_audit_policy_status_mock(auditor):
    """Тест разбора статуса политики auditpol."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="WORKSTATION,System,File System,{0CCE921D-69AE-11D9-BED3-505054503030},Success and Failure,",
            stderr="",
        )
        status = auditor.get_audit_policy_status()
        assert status.subcategory == "File System"
        assert status.success_enabled is True
        assert status.failure_enabled is True
        assert status.is_configured is True


def test_router_status_endpoint(client):
    """Тест эндпоинта /api/sysadmin/status."""
    response = client.get("/api/sysadmin/status")
    assert response.status_code == 200
    data = response.json()
    assert "hostname" in data
    assert "file_audit" in data


def test_router_file_audit_deletions(client):
    """Тест эндпоинта /api/sysadmin/file-audit/deletions."""
    response = client.get("/api/sysadmin/file-audit/deletions?hours=1")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "deletions_count" in data


def test_router_file_audit_live_events(client):
    """Тест эндпоинта /api/sysadmin/file-audit/live-events."""
    response = client.get("/api/sysadmin/file-audit/live-events?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "watch_dir" in data
