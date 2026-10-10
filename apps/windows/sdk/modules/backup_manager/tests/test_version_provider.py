# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Backup_Manager Tests - Test Version Provider
# =============================================================================
# Description:
#   Тесты подсистемы точечного версионирования файлов (VSS + SQLite blob store).
#
# Usage Examples:
#   pytest apps/windows/modules/backup_manager/tests/test_version_provider.py -v
#
# File: test_version_provider.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.backup_manager.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 21:50:00
# =============================================================================

from __future__ import annotations
"""Тесты WindowsVersionProvider и REST API /api/v1/versions."""

import hashlib
import sqlite3
from pathlib import Path
from typing import List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.sdk.modules.backup_manager.core.models import VssSnapshot
from apps.windows.sdk.modules.backup_manager.core.version_provider import WindowsVersionProvider


class FakeVss:
    """Подставной VssManager: «снимок» — это копия файла в каталоге tmp."""

    def __init__(self, snap_dir: Path, deny: bool = False) -> None:
        self.snap_dir = snap_dir
        self.deny = deny
        self.deleted: List[str] = []
        self.counter = 0

    def create_snapshot(self, volume: str) -> VssSnapshot:
        if self.deny:
            raise PermissionError('E_ACCESSDENIED')
        self.counter += 1
        return VssSnapshot(
            snapshot_id=f'{{SNAP-{self.counter}}}',
            original_volume=volume,
            shadow_volume_path=str(self.snap_dir),
        )

    def delete_snapshot(self, snapshot_id: str) -> bool:
        self.deleted.append(snapshot_id)
        return True


class SnapshotAwareProvider(WindowsVersionProvider):
    """Провайдер, читающий «снимок» из подставного каталога вместо GLOBALROOT."""

    def _read_from_snapshot(self, device_path: str, file_path: str) -> bytes:
        return (Path(device_path) / Path(file_path).name).read_bytes()


@pytest.fixture
def env(tmp_path: Path):
    """Файл, подставной VSS и провайдер с изолированной БД."""
    snap_dir = tmp_path / 'snap'
    snap_dir.mkdir()
    target = tmp_path / 'config.json'
    target.write_text('v1', encoding='utf-8')
    vss = FakeVss(snap_dir)
    provider = SnapshotAwareProvider(db_path=tmp_path / 'telemetry.db', vss=vss)
    return provider, vss, target, snap_dir


def _freeze_snapshot(snap_dir: Path, target: Path) -> None:
    """Имитация теневой копии: копируем содержимое файла в каталог «снимка»."""
    (snap_dir / target.name).write_bytes(target.read_bytes())


def test_save_creates_vss_version(env) -> None:
    provider, vss, target, _ = env
    rec = provider.save_version(str(target), 'тест')
    assert rec.storage_layer == 'VSS'
    assert rec.snapshot_id == '{SNAP-1}'
    assert rec.sha256_hash == hashlib.sha256(b'v1').hexdigest()
    assert rec.file_size_bytes == 2
    assert provider.list_versions(str(target))[0].version_id == rec.version_id


def test_save_missing_file_raises(env) -> None:
    provider, _, target, _ = env
    with pytest.raises(FileNotFoundError):
        provider.save_version(str(target.with_name('nope.txt')))


def test_fallback_to_blob_when_access_denied(tmp_path: Path) -> None:
    target = tmp_path / 'a.txt'
    target.write_text('hello', encoding='utf-8')
    provider = WindowsVersionProvider(db_path=tmp_path / 't.db', vss=FakeVss(tmp_path, deny=True))
    rec = provider.save_version(str(target))
    assert rec.storage_layer == 'PERSISTENT_BLOB'
    assert rec.blob_id
    target.write_text('changed', encoding='utf-8')
    provider.restore_version(rec.version_id)
    assert target.read_text(encoding='utf-8') == 'hello'


def test_restore_from_vss_with_backup_copy(env) -> None:
    provider, _, target, snap_dir = env
    rec = provider.save_version(str(target))
    _freeze_snapshot(snap_dir, target)
    target.write_text('v2', encoding='utf-8')
    provider.restore_version(rec.version_id)
    assert target.read_text(encoding='utf-8') == 'v1'
    assert target.with_name('config.json.bak').read_text(encoding='utf-8') == 'v2'


def test_restore_detects_hash_mismatch(env) -> None:
    provider, _, target, snap_dir = env
    rec = provider.save_version(str(target))
    (snap_dir / target.name).write_bytes(b'corrupted')
    with pytest.raises(ValueError):
        provider.restore_version(rec.version_id)
    assert target.read_text(encoding='utf-8') == 'v1'


def test_restore_unknown_version(env) -> None:
    provider, *_ = env
    with pytest.raises(KeyError):
        provider.restore_version(999)


def test_migrate_hot_to_cold_and_release_snapshot(env, tmp_path: Path) -> None:
    provider, vss, target, snap_dir = env
    rec = provider.save_version(str(target))
    _freeze_snapshot(snap_dir, target)
    with sqlite3.connect(provider.db_path) as conn:
        conn.execute("UPDATE file_versions SET created_at = datetime('now','-2 days')")
    assert provider.migrate_hot_to_cold() == 1
    moved = provider.list_versions(str(target))[0]
    assert moved.storage_layer == 'PERSISTENT_BLOB'
    assert vss.deleted == ['{SNAP-1}']
    (snap_dir / target.name).unlink()
    target.write_text('v2', encoding='utf-8')
    provider.restore_version(rec.version_id)
    assert target.read_text(encoding='utf-8') == 'v1'


def test_purge_expired_removes_old_versions(env) -> None:
    provider, _, target, snap_dir = env
    provider.vss.deny = True
    provider.save_version(str(target))
    with sqlite3.connect(provider.db_path) as conn:
        conn.execute("UPDATE file_versions SET created_at = datetime('now','-40 days')")
    assert provider.purge_expired(days=30) == 1
    assert provider.list_versions(str(target)) == []
    with sqlite3.connect(provider.db_path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM file_version_blobs').fetchone()[0] == 0


def test_rest_api_save_list_restore(env) -> None:
    from apps.windows.sdk.modules.backup_manager.versions_router import init_router

    provider, _, target, snap_dir = env
    app = FastAPI()
    app.include_router(init_router(provider))
    client = TestClient(app)

    resp = client.post('/api/v1/versions/save', json={'file_path': str(target), 'description': 'x'})
    assert resp.status_code == 200
    body = resp.json()
    assert body['status'] == 'success' and body['storage_layer'] == 'VSS'

    listed = client.get('/api/v1/versions/list', params={'file_path': str(target)}).json()
    assert len(listed) == 1

    _freeze_snapshot(snap_dir, target)
    target.write_text('v2', encoding='utf-8')
    ok = client.post('/api/v1/versions/restore', json={'version_id': body['version_id']})
    assert ok.status_code == 200
    assert target.read_text(encoding='utf-8') == 'v1'

    assert client.post('/api/v1/versions/restore', json={'version_id': 12345}).status_code == 404
    assert client.post('/api/v1/versions/save', json={'file_path': str(target) + 'x'}).status_code == 404
