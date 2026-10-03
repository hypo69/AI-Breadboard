# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Router About System
# =============================================================================
# Description:
#   Тесты REST эндпоинтов панели 'О Системе' (/api/v1/about-system/*).
#
# Usage Examples:
#   Python API:
#     from tests.test_router_about_system import test_storage
#
#     res = test_storage()
#
# File: test_router_about_system.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-03 22:31:00
# =============================================================================

from __future__ import annotations
"""Тесты REST эндпоинтов панели 'О Системе' /api/v1/about-system/*."""

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_about_system import init_router
from apps.windows.telemetry.models import (
    CpuMetrics,
    DiskIoMetrics,
    DiskPartitionMetrics,
    GpuMetrics,
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
        "apps.windows.api.routers.router_about_system.TelemetryStorage.get_instance",
        lambda: test_storage,
    )
    app = FastAPI()
    router = init_router()
    app.include_router(router)
    return TestClient(app)


def test_about_system_os_empty_fallback(client):
    """Проверка работы GET /api/v1/about-system/os при пустой базе данных (fallback-режим)."""
    response = client.get("/api/v1/about-system/os")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "os_name" in data
    assert "display_title" in data
    assert "display_host" in data
    assert "uptime_human" in data


def test_about_system_os_with_saved_snapshot(client, test_storage):
    """Проверка чтения данных ОС из зафиксированного снимка в базе данных."""
    snap = SystemSnapshot(
        hostname="TEST-WORKSTATION",
        os_name="Windows 11 Pro",
        os_build="22631",
        os_install_date="02.02.2026 08:30",
        uptime_seconds=7320.0,
        cpu=CpuMetrics(architecture="AMD64", total_percent=15.5),
        memory=MemoryMetrics(total_gb=32.0, used_gb=16.0, percent=50.0),
    )
    test_storage.save_snapshot(snap)
    test_storage.flush()

    response = client.get("/api/v1/about-system/os")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["hostname"] == "TEST-WORKSTATION"
    assert data["os_name"] == "Windows 11 Pro"
    assert data["os_build"] == "22631"
    assert data["os_install_date"] == "02.02.2026 08:30"
    assert data["architecture"] == "AMD64"
    assert data["uptime_seconds"] == 7320.0
    assert data["uptime_human"] == "2h 2m"
    assert data["display_title"] == "Windows 11 Pro (AMD64)"
    assert data["display_host"] == "Host: TEST-WORKSTATION"


def test_about_system_security(client, test_storage):
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

    response = client.get("/api/v1/about-system/security")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Active & Protected"
    assert data["firewall_status"] == "ON"
    assert data["defender_enabled"] is True
    assert data["realtime_protection"] is True
    assert data["uac_enabled"] is True
    assert data["display_title"] == "Active & Protected"
    assert data["display_subtitle"] == "Firewall: ON | UAC: ON"


def test_about_system_restore_points(client, test_storage):
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

    response = client.get("/api/v1/about-system/restore-points")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["checkpoints_count"] == 3
    assert data["protection_enabled"] is True
    assert data["protection_status"] == "Active"
    assert data["display_title"] == "3 Checkpoints"
    assert data["display_subtitle"] == "Protection: Active"
    assert data["latest_checkpoint_name"] == "Pre-Update Checkpoint"


def test_about_system_storage(client, test_storage):
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

    response = client.get("/api/v1/about-system/storage")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["drive"] == "C:"
    assert data["total_gb"] == 1024.0
    assert data["free_gb"] == 1014.8
    assert data["cleanable_mb"] == 190.0
    assert data["display_title"] == "1014.8 GB Free"
    assert data["display_subtitle"] == "Cleanable: ~190 MB"


def test_about_system_panel_overview(client, test_storage):
    """Проверка работы сводного GET эндпоинта /api/v1/about-system/summary со всеми 8 карточками."""
    # 1. Сохраняем системный снимок в telemetry.db
    snap = SystemSnapshot(
        hostname="DELL-VOSTRO",
        os_name="Windows 11",
        os_build="22631",
        uptime_seconds=3600.0,
        cpu=CpuMetrics(
            architecture="AMD64",
            model="Intel(R) Core(TM) i5-10400 CPU @ 2.90GHz",
            physical_cores=6,
            logical_cores=12,
            total_percent=22.2,
            frequency_mhz=2900.0,
        ),
        memory=MemoryMetrics(
            total_gb=31.8,
            used_gb=18.7,
            available_gb=13.1,
            percent=58.9,
        ),
        gpus=[
            GpuMetrics(
                name="GeForce GT 710",
                memory_total_gb=2.0,
                load_percent=0.0,
                has_cuda=True,
                has_directml=True,
            )
        ],
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
        disk_io=DiskIoMetrics(
            read_bytes_per_sec=0.0,
            write_bytes_per_sec=0.0,
        ),
    )
    test_storage.save_snapshot(snap)

    # 2. Сохраняем аудит безопасности и VSS
    with test_storage._lock, test_storage._get_connection() as conn:
        cursor = conn.cursor()
        audit_payload = {
            "security": {
                "firewall": {"domain": True, "private": True, "public": True},
                "defender": {"enabled": True, "realtime_protection": True},
                "uac": {"enabled": True},
            },
            "vss": {
                "protection_enabled": True,
                "status": "Active",
            },
        }
        cursor.execute(
            """
            INSERT INTO system_extended_audits (
                timestamp, created_at, hostname, vss_snapshots_count, raw_json
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (
                "2026-10-03T19:00:00Z",
                1791054000.0,
                "DELL-VOSTRO",
                0,
                json.dumps(audit_payload),
            ),
        )
        conn.commit()

    test_storage.save_app_poll(
        app="clean_collector",
        poll_type="clean_audit",
        metric_name="cleanable_mb",
        value=0.0,
    )
    test_storage.flush()

    # 3. Выполняем GET запрос к API эндпоинту панели
    response = client.get("/api/v1/about-system/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

    # Карточки 1-4
    assert data["os"]["display_title"] == "Windows 11 (AMD64)"
    assert data["os"]["display_host"] == "Host: DELL-VOSTRO"
    assert data["os"]["uptime_human"] == "1h 0m"

    assert data["security"]["display_title"] == "Active & Protected"
    assert data["security"]["display_subtitle"] == "Firewall: ON | UAC: ON"

    assert data["restore_points"]["display_title"] == "0 Checkpoints"
    assert data["restore_points"]["display_subtitle"] == "Protection: Active"

    assert data["storage"]["display_title"] == "1014.8 GB Free"
    assert data["storage"]["display_subtitle"] == "Cleanable: ~0 MB"

    # Карточки 5-8
    assert data["cpu"]["display_val"] == "22.2%"
    assert data["cpu"]["display_cores"] == "6 физ. / 12 Потоков"
    assert data["cpu"]["display_freq"] == "2900 MHz"

    assert data["memory"]["display_val"] == "18.7 / 31.8 GB"
    assert "58.9% занято" in data["memory"]["display_sub"]

    assert data["gpu"]["display_name"] == "GeForce GT 710"
    assert data["gpu"]["badge"] == "CUDA + DirectML"
    assert "VRAM: 2.0 GB" in data["gpu"]["display_vram"]

    assert data["disk_io"]["display_val"] == "0.00 MB/s"
    assert "Чтение: 0 КБ/с" in data["disk_io"]["display_rates"]

    # Метаданные SQL-запроса
    assert data["meta"]["source"] == "telemetry.db"
    assert len(data["meta"]["sql_queries"]) >= 3

    # Проверка вызова через /api/v1/about-system
    res_direct = client.get("/api/v1/about-system")
    assert res_direct.status_code == 200
    assert res_direct.json()["status"] == "ok"


def test_about_system_history(client, test_storage):
    """Проверка работы GET /api/v1/about-system/history и извлечения списка предыдущих срезов."""
    # Сохраняем 3 снимка
    for i in range(1, 4):
        snap = SystemSnapshot(
            hostname=f"HOST-{i}",
            os_install_date=f"0{i}.02.2026 08:30",
            uptime_seconds=float(i * 1000),
            cpu=CpuMetrics(total_percent=float(10 * i), frequency_mhz=2000.0 + i * 100),
            memory=MemoryMetrics(total_gb=32.0, used_gb=float(10 + i), percent=float(30 + i * 5)),
            disks=[
                DiskPartitionMetrics(
                    device="C:",
                    mountpoint="C:\\",
                    total_gb=1000.0,
                    free_gb=float(800 - i * 50),
                    used_gb=float(200 + i * 50),
                    percent=float(20 + i * 5),
                )
            ],
            disk_io=DiskIoMetrics(read_bytes_per_sec=1024.0 * i, write_bytes_per_sec=2048.0 * i),
        )
        test_storage.save_snapshot(snap)
    test_storage.flush()

    response = client.get("/api/v1/about-system/history?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["count"] == 2
    assert len(data["history"]) == 2

    # Проверка порядка DESC (первый - последний добавленный HOST-3)
    first_item = data["history"][0]
    assert first_item["hostname"] == "HOST-3"
    assert first_item["os_install_date"] == "03.02.2026 08:30"
    assert first_item["cpu_total_percent"] == 30.0
    assert first_item["memory_used_gb"] == 13.0
    assert first_item["storage_c_free_gb"] == 650.0

    second_item = data["history"][1]
    assert second_item["hostname"] == "HOST-2"
    assert second_item["os_install_date"] == "02.02.2026 08:30"
    assert second_item["cpu_total_percent"] == 20.0


def test_dashboard_card_endpoints(client, test_storage):
    """Проверка работы всех индивидуальных GET эндпоинтов для карточек /api/v1/dashboard/*."""
    endpoints = [
        "/api/v1/dashboard/os",
        "/api/v1/dashboard/security",
        "/api/v1/dashboard/checkpoints",
        "/api/v1/dashboard/storage",
        "/api/v1/dashboard/cpu",
        "/api/v1/dashboard/ram",
        "/api/v1/dashboard/panel_ram",
        "/api/v1/dashboard/gpu",
        "/api/v1/dashboard/disk_io",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Endpoint {ep} failed with status {res.status_code}"
        data = res.json()
        assert data is not None
