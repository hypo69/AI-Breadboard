# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Tests - Test Raw Cloner
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.storage_manager.tests.test_raw_cloner import raw_io
#
#     res = raw_io()
#
# File: test_raw_cloner.py
# Project: ai-breadboard
# Package: apps.windows.modules.storage_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import base64
import os
import tempfile
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.modules.storage_manager.core.clone_engine import DiskCloneEngine
from apps.windows.modules.storage_manager.core.manager import StorageManager
from apps.windows.modules.storage_manager.core.models import (
    DiskCloneRequest,
    DiskHashRequest,
    DiskImageCreateRequest,
    DiskImageRestoreRequest,
    DiskVerifyRequest,
    SectorReadRequest,
    SectorWriteRequest,
)
from apps.windows.modules.storage_manager.core.raw_disk_io import WindowsRawDiskIO
from apps.windows.modules.storage_manager.router import init_router


@pytest.fixture
def raw_io() -> WindowsRawDiskIO:
    """Фикстура блочного ввода-вывода."""
    return WindowsRawDiskIO()


@pytest.fixture
def manager(raw_io: WindowsRawDiskIO) -> StorageManager:
    """Фикстура менеджера дисков."""
    return StorageManager(raw_io=raw_io)


@pytest.fixture
def client() -> TestClient:
    """Фикстура тестового клиента FastAPI."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


# -----------------------------------------------------------------------------
# Тесты блочного ввода-вывода и структур
# -----------------------------------------------------------------------------

def test_raw_io_geometry(raw_io: WindowsRawDiskIO):
    """Проверка получения геометрии диска."""
    geom = raw_io.get_geometry(0)
    assert geom is not None
    assert geom.bytes_per_sector >= 512
    assert geom.disk_size_bytes > 0 or geom.total_sectors >= 0


def test_raw_io_read_sectors(raw_io: WindowsRawDiskIO):
    """Проверка посекторного чтения."""
    data = raw_io.read_sectors(disk_id=0, start_lba=0, sector_count=2, sector_size=512)
    assert isinstance(data, bytes)
    assert len(data) == 1024


def test_inspect_headers(raw_io: WindowsRawDiskIO):
    """Проверка инспекции заголовков разметки."""
    headers = raw_io.inspect_headers(0)
    assert headers.disk_id == 0
    assert isinstance(headers.partitions, list)


def test_compute_hash(raw_io: WindowsRawDiskIO):
    """Проверка потокового расчета SHA-256 хеша секторов."""
    h_hex, count = raw_io.compute_hash(disk_id=0, start_lba=0, sector_count=10)
    assert len(h_hex) == 64
    assert count == 10 * 512


# -----------------------------------------------------------------------------
# Тесты StorageManager и бизнес-логики
# -----------------------------------------------------------------------------

def test_manager_read_sectors_dump(manager: StorageManager):
    """Проверка форматирования HEX дампа и base64 при чтении сектора."""
    req = SectorReadRequest(disk_id=0, start_lba=0, sector_count=1)
    res = manager.read_sectors(req)
    assert res.disk_id == 0
    assert res.bytes_read == 512
    assert len(res.hex_dump) > 0
    assert len(res.data_base64) > 0


def test_manager_write_sectors_dry_run(manager: StorageManager):
    """Проверка безопасной симуляции записи секторов (Dry-Run)."""
    data_b64 = base64.b64encode(b"TEST_SECTOR_DATA" * 32).decode('ascii')
    req = SectorWriteRequest(
        disk_id=0,
        start_lba=100,
        data_base64=data_b64,
        dry_run=True,
    )
    res = manager.write_sectors(req)
    assert res.status == 'DRY_RUN_SUCCESS'
    assert res.bytes_written == 512


def test_manager_write_safety_guards(manager: StorageManager):
    """Проверка защиты от случайной записи в системный диск."""
    req = SectorWriteRequest(
        disk_id=0,
        start_lba=0,
        data_base64="AAAA",
        dry_run=False,
        force_system_drive=False,
        confirmed_by_user=True,
    )
    with pytest.raises(PermissionError):
        manager.write_sectors(req)


@pytest.mark.asyncio
async def test_manager_clone_simulation(manager: StorageManager):
    """Проверка симуляции клонирования диск-в-диск."""
    req = DiskCloneRequest(
        source_disk_id=0,
        target_disk_id=1,
        clone_mode='raw',
        dry_run=True,
    )
    task = await manager.start_clone(req)
    assert task.status == 'completed'
    assert task.dry_run is True
    assert task.source == 'PhysicalDrive0'
    assert task.destination == 'PhysicalDrive1'


@pytest.mark.asyncio
async def test_manager_clone_safety_validation(manager: StorageManager):
    """Проверка валидации безопасности клонирования (одинаковый диск)."""
    req = DiskCloneRequest(
        source_disk_id=0,
        target_disk_id=0,
        dry_run=True,
    )
    with pytest.raises(ValueError):
        await manager.start_clone(req)


@pytest.mark.asyncio
async def test_manager_image_create_and_restore_simulation(manager: StorageManager):
    """Проверка симуляции создания и восстановления образа диска."""
    with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Создание
        create_req = DiskImageCreateRequest(
            disk_id=0,
            image_path=tmp_path,
            dry_run=True,
        )
        t_create = await manager.start_image_create(create_req)
        assert t_create.status == 'completed'

        # Восстановление
        restore_req = DiskImageRestoreRequest(
            disk_id=1,
            image_path=tmp_path,
            dry_run=True,
        )
        t_restore = await manager.start_image_restore(restore_req)
        assert t_restore.status == 'completed'
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_manager_verify_integrity(manager: StorageManager):
    """Проверка верификации диска."""
    req = DiskVerifyRequest(
        source_disk_id=0,
        target_disk_id=0,  # Сравнение с самим собой должно совпадать
        start_lba=0,
        sector_count=10,
    )
    res = await manager.verify_integrity(req)
    assert res['is_identical'] is True
    assert res['status'] == 'VERIFIED_MATCH'
    assert res['mismatched_sectors'] == 0


# -----------------------------------------------------------------------------
# Тесты REST API Эндпоинтов
# -----------------------------------------------------------------------------

def test_api_list_disks(client: TestClient):
    """GET /api/v1/storage/disks"""
    resp = client.get('/api/v1/storage/disks')
    assert resp.status_code == 200
    disks = resp.json()
    assert isinstance(disks, list)
    assert len(disks) > 0


def test_api_get_disk_info(client: TestClient):
    """GET /api/v1/storage/disks/0"""
    resp = client.get('/api/v1/storage/disks/0')
    assert resp.status_code == 200
    data = resp.json()
    assert data['disk_id'] == 0
    assert 'geometry' in data
    assert 'partitions' in data


def test_api_read_sector(client: TestClient):
    """POST /api/v1/storage/disks/0/read"""
    resp = client.post(
        '/api/v1/storage/disks/0/read',
        json={'disk_id': 0, 'start_lba': 0, 'sector_count': 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['bytes_read'] == 512
    assert 'hex_dump' in data


def test_api_write_sector_dry_run(client: TestClient):
    """POST /api/v1/storage/disks/0/write"""
    resp = client.post(
        '/api/v1/storage/disks/0/write',
        json={
            'disk_id': 0,
            'start_lba': 10,
            'data_base64': 'AAAA',
            'dry_run': True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'DRY_RUN_SUCCESS'


def test_api_clone_disk_dry_run(client: TestClient):
    """POST /api/v1/storage/disks/0/clone"""
    resp = client.post(
        '/api/v1/storage/disks/0/clone',
        json={
            'source_disk_id': 0,
            'target_disk_id': 1,
            'clone_mode': 'raw',
            'dry_run': True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'completed'
    assert 'task_id' in data


def test_api_disk_hash(client: TestClient):
    """POST /api/v1/storage/disks/0/hash"""
    resp = client.post(
        '/api/v1/storage/disks/0/hash',
        json={'disk_id': 0, 'start_lba': 0, 'sector_count': 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert 'hash_hex' in data
    assert len(data['hash_hex']) == 64


def test_api_tasks_lifecycle(client: TestClient):
    """GET /api/v1/storage/tasks и DELETE /api/v1/storage/tasks/{task_id}"""
    # Создаем задачу
    clone_resp = client.post(
        '/api/v1/storage/disks/0/clone',
        json={
            'source_disk_id': 0,
            'target_disk_id': 1,
            'dry_run': True,
        },
    )
    task_id = clone_resp.json()['task_id']

    # Читаем статус
    get_resp = client.get(f'/api/v1/storage/tasks/{task_id}')
    assert get_resp.status_code == 200
    assert get_resp.json()['task_id'] == task_id

    # Читаем список
    list_resp = client.get('/api/v1/storage/tasks')
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
