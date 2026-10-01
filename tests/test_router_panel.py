# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Router Panel
# =============================================================================
# Description:
#   Тесты эндпоинтов сводных KPI-карточек /api/v1/panel/*.
#
# Usage Examples:
#   Python API:
#     from tests.test_router_panel import test_storage
#
#     res = test_storage()
#
# File: test_router_panel.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Тесты эндпоинтов сводных KPI-карточек /api/v1/panel/*."""

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_panel import init_router
from apps.windows.telemetry.models import (
    CpuMetrics,
    DiskPartitionMetrics,
    MemoryMetrics,
    SystemSnapshot,
)
from apps.windows.telemetry.sqlite import TelemetryStorage


@pytest.fixture
def test_storage(tmp_path):
    """Создает временное хранилище TelemetryStorage для тестов."""
    db_file = tmp_path / "telemetry_test.db"
    storage = TelemetryStorage(db_path=db_file, buffer_mode="direct")
    return storage


@pytest.fixture
def client(test_storage, monkeypatch):
    """Инициализирует тестовый клиент FastAPI с внедренным тестовым TelemetryStorage."""
    monkeypatch.setattr(
        "apps.windows.api.routers.router_panel.TelemetryStorage.get_instance",
        lambda: test_storage,
    )
    app = FastAPI()
    router = init_router()
    app.include_router(router)
    return TestClient(app)


def test_panel_os_empty_fallback(client):
    """Проверка работы GET /api/v1/panel/os при пустой базе данных (fallback-режим)."""
    response = client.get("/api/v1/panel/os")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "os_name" in data
    assert "display_title" in data
    assert "display_host" in data
    assert "uptime_human" in data


def test_panel_os_with_saved_snapshot(client, test_storage):
    """Проверка чтения данных ОС из зафиксированного снимка в базе данных."""
    snap = SystemSnapshot(
        hostname="TEST-WORKSTATION",
        os_name="Windows 11 Pro",
        os_build="22631",
        uptime_seconds=7320.0,
        cpu=CpuMetrics(architecture="AMD64", total_percent=15.5),
        memory=MemoryMetrics(total_gb=32.0, used_gb=16.0, percent=50.0),
    )
    test_storage.save_snapshot(snap)
    test_storage.flush()

    response = client.get("/api/v1/panel/os")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["hostname"] == "TEST-WORKSTATION"
    assert data["os_name"] == "Windows 11 Pro"
    assert data["os_build"] == "22631"
    assert data["architecture"] == "AMD64"
    assert data["uptime_seconds"] == 7320.0
    assert data["uptime_human"] == "2h 2m"
    assert data["display_title"] == "Windows 11 Pro (AMD64)"
    assert data["display_host"] == "Host: TEST-WORKSTATION"


def test_panel_security(client, test_storage):
    """Проверка чтения статуса безопасности, Брандмауэра и UAC."""
    with test_storage._lock, test_storage._get_connection() as conn:
        cursor = conn.cursor()
        audit_payload = {
            "security": {
                "firewall": {"domain": True, "private": True, "public": True},
                "defender": {"enabled": True, "realtime_protection": True},
                "uac": {"enabled": True},
            }
        }
        cursor.execute(
            """
            INSERT INTO system_extended_audits (timestamp, created_at, hostname, raw_json)
            VALUES (?, ?, ?, ?)
        """,
            (
                "2026-10-01T05:00:00Z",
                1790830800.0,
                "TEST-HOST",
                json.dumps(audit_payload),
            ),
        )
        conn.commit()

    response = client.get("/api/v1/panel/security")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Active & Protected"
    assert data["firewall_status"] == "ON"
    assert data["defender_enabled"] is True
    assert data["realtime_protection"] is True
    assert data["uac_enabled"] is True
    assert data["display_title"] == "Active & Protected"
    assert data["display_subtitle"] == "Firewall: ON | UAC: ON"


def test_panel_restore_points(client, test_storage):
    """Проверка чтения информации о точках восстановления Windows."""
    with test_storage._lock, test_storage._get_connection() as conn:
        cursor = conn.cursor()
        vss_payload = {
            "vss": {
                "protection_enabled": True,
                "status": "Active",
                "latest_name": "Pre-Update Checkpoint",
                "latest_time": "2026-10-01 04:00:00",
            }
        }
        cursor.execute(
            """
            INSERT INTO system_extended_audits (
                timestamp, created_at, hostname, vss_snapshots_count, raw_json
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (
                "2026-10-01T05:00:00Z",
                1790830800.0,
                "TEST-HOST",
                3,
                json.dumps(vss_payload),
            ),
        )
        conn.commit()

    response = client.get("/api/v1/panel/restore-points")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["checkpoints_count"] == 3
    assert data["protection_enabled"] is True
    assert data["protection_status"] == "Active"
    assert data["display_title"] == "3 Checkpoints"
    assert data["display_subtitle"] == "Protection: Active"
    assert data["latest_checkpoint_name"] == "Pre-Update Checkpoint"


def test_panel_storage(client, test_storage):
    """Проверка чтения данных о системном накопителе C: и очищаемых файлах."""
    snap = SystemSnapshot(
        hostname="TEST-STORAGE-HOST",
        disks=[
            DiskPartitionMetrics(
                device="C:",
                mountpoint="C:\\",
                fstype="NTFS",
                total_gb=1024.0,
                used_gb=9.2,
                free_gb=1014.8,
                percent=0.9,
            )
        ],
    )
    test_storage.save_snapshot(snap)

    test_storage.save_app_poll(
        app="clean_collector",
        poll_type="clean_audit",
        metric_name="cleanable_mb",
        value=190.0,
    )
    test_storage.flush()

    response = client.get("/api/v1/panel/storage")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["drive"] == "C:"
    assert data["total_gb"] == 1024.0
    assert data["free_gb"] == 1014.8
    assert data["cleanable_mb"] == 190.0
    assert data["display_title"] == "1014.8 GB Free"
    assert data["display_subtitle"] == "Cleanable: ~190 MB"
