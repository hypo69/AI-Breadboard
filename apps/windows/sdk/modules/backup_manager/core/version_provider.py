# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Backup_Manager Core - Version Provider
# =============================================================================
# Description:
#   Точечное версионирование файлов: горячий слой (Windows VSS) и холодный слой
#   (сжатые блобы в SQLite telemetry.db). Нулевое копирование при сохранении версии.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.backup_manager.core.version_provider import WindowsVersionProvider
#
#     provider = WindowsVersionProvider()
#     rec = provider.save_version('C:/Data/config.json', 'перед правкой')
#     provider.restore_version(rec.version_id)
#
# File: version_provider.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 21:50:00
# =============================================================================

from __future__ import annotations
"""Провайдер двухуровневого хранилища версий файлов (VSS + SQLite)."""

import hashlib
import os
import sqlite3
import uuid
import zlib
from pathlib import Path
from typing import Any, List, Optional, Union

from logger import logger
from apps.windows.sdk.modules.backup_manager.core.models import FileVersionEntry
from apps.windows.sdk.modules.backup_manager.core.vss_manager import VssManager
from apps.windows.sdk.modules.window_control_plane.history import get_default_telemetry_db_path

try:  # Python 3.14+: Zstandard в стандартной библиотеке
    from compression import zstd as _zstd
except ImportError:  # Откат на zlib, алгоритм фиксируется в БД
    _zstd = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS file_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    volume_letter TEXT NOT NULL,
    snapshot_id TEXT,
    snapshot_device_path TEXT,
    storage_layer TEXT NOT NULL DEFAULT 'VSS',
    blob_id TEXT,
    file_size_bytes INTEGER NOT NULL,
    sha256_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT
);
CREATE TABLE IF NOT EXISTS file_version_blobs (
    blob_id TEXT PRIMARY KEY,
    compressed_payload BLOB NOT NULL,
    original_size_bytes INTEGER NOT NULL,
    compressed_size_bytes INTEGER NOT NULL,
    compression_algorithm TEXT NOT NULL DEFAULT 'zstd',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_file_versions_path ON file_versions(file_path);
CREATE INDEX IF NOT EXISTS idx_file_versions_hash ON file_versions(sha256_hash);
"""


def _compress(data: bytes) -> tuple[bytes, str]:
    """Сжимает данные: zstd при наличии, иначе zlib."""
    if _zstd is not None:
        return _zstd.compress(data), 'zstd'
    return zlib.compress(data), 'zlib'


def _decompress(payload: bytes, algorithm: str) -> bytes:
    """Распаковывает блоб согласно сохраненному алгоритму."""
    if algorithm == 'zstd':
        if _zstd is None:
            raise RuntimeError('Блоб сжат zstd, но модуль compression.zstd недоступен')
        return _zstd.decompress(payload)
    return zlib.decompress(payload)


class WindowsVersionProvider:
    """Сохранение, просмотр, восстановление и ротация версий файлов."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        vss: Optional[VssManager] = None,
        hot_hours: int = 24,
    ) -> None:
        """Инициализация провайдера.

        Args:
            db_path: Путь к telemetry.db (по умолчанию — стандартный).
            vss: Менеджер VSS (внедряется для тестов).
            hot_hours: Срок жизни версии в горячем слое VSS.
        """
        self.db_path = Path(db_path) if db_path else get_default_telemetry_db_path()
        self.vss = vss or VssManager()
        self.hot_hours = hot_hours
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row(row: sqlite3.Row) -> FileVersionEntry:
        return FileVersionEntry(**dict(row))

    @staticmethod
    def _read_from_snapshot(device_path: str, file_path: str) -> bytes:
        """Читает файл из теневой копии по пути ``<device>\\<относительный путь>``."""
        rel = os.path.splitdrive(file_path)[1].lstrip('\\/')
        return Path(device_path.rstrip('\\') + '\\' + rel).read_bytes()

    def save_version(self, file_path: str, description: Optional[str] = None) -> FileVersionEntry:
        """Фиксирует версию файла: мгновенный VSS-снимок либо fallback в холодный слой.

        Raises:
            FileNotFoundError: Файл не существует.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(file_path)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        volume = os.path.splitdrive(str(path.resolve()))[0] + '\\'
        snapshot_id = device = blob_id = None
        layer = 'VSS'
        try:
            snap = self.vss.create_snapshot(volume)
            snapshot_id, device = snap.snapshot_id, snap.shadow_volume_path
        except (PermissionError, RuntimeError, OSError) as exc:
            logger.warning(f'[VersionProvider] VSS недоступен ({exc}), fallback в холодный слой')
            layer = 'PERSISTENT_BLOB'
        with self._connect() as conn:
            if layer == 'PERSISTENT_BLOB':
                blob_id = self._store_blob(conn, data)
            cur = conn.execute(
                'INSERT INTO file_versions (file_path, volume_letter, snapshot_id, snapshot_device_path, '
                'storage_layer, blob_id, file_size_bytes, sha256_hash, description) VALUES (?,?,?,?,?,?,?,?,?)',
                (str(path), volume, snapshot_id, device, layer, blob_id, len(data), digest, description),
            )
            row = conn.execute('SELECT * FROM file_versions WHERE version_id = ?', (cur.lastrowid,)).fetchone()
        return self._row(row)

    @staticmethod
    def _store_blob(conn: sqlite3.Connection, data: bytes) -> str:
        payload, algo = _compress(data)
        blob_id = uuid.uuid4().hex
        conn.execute(
            'INSERT INTO file_version_blobs (blob_id, compressed_payload, original_size_bytes, '
            'compressed_size_bytes, compression_algorithm) VALUES (?,?,?,?,?)',
            (blob_id, payload, len(data), len(payload), algo),
        )
        return blob_id

    def list_versions(self, file_path: str) -> List[FileVersionEntry]:
        """Возвращает версии файла от новых к старым."""
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT * FROM file_versions WHERE file_path = ? ORDER BY version_id DESC', (str(Path(file_path)),)
            ).fetchall()
        return [self._row(r) for r in rows]

    def _load_content(self, conn: sqlite3.Connection, row: sqlite3.Row) -> bytes:
        if row['storage_layer'] == 'VSS':
            return self._read_from_snapshot(row['snapshot_device_path'], row['file_path'])
        blob = conn.execute('SELECT * FROM file_version_blobs WHERE blob_id = ?', (row['blob_id'],)).fetchone()
        if blob is None:
            raise KeyError(f"Блоб {row['blob_id']} не найден")
        return _decompress(blob['compressed_payload'], blob['compression_algorithm'])

    def restore_version(self, version_id: int) -> FileVersionEntry:
        """Восстанавливает файл: проверка SHA-256, страховая копия ``.bak``, атомарная замена.

        Raises:
            KeyError: Версия не найдена.
            ValueError: Контрольная сумма не совпала (файл не изменяется).
        """
        with self._connect() as conn:
            row = conn.execute('SELECT * FROM file_versions WHERE version_id = ?', (version_id,)).fetchone()
            if row is None:
                raise KeyError(f'Версия {version_id} не найдена')
            data = self._load_content(conn, row)
        if hashlib.sha256(data).hexdigest() != row['sha256_hash']:
            raise ValueError(f'Нарушена целостность версии {version_id}: SHA-256 не совпадает')
        target = Path(row['file_path'])
        if target.exists():
            target.with_name(target.name + '.bak').write_bytes(target.read_bytes())
        tmp = target.with_name(target.name + '.restore.tmp')
        tmp.write_bytes(data)
        os.replace(tmp, target)
        logger.info(f'[VersionProvider] Версия {version_id} восстановлена в {target}')
        return self._row(row)

    def migrate_hot_to_cold(self) -> int:
        """Переносит версии старше ``hot_hours`` из VSS в SQLite-блобы и освобождает снимки.

        Returns:
            int: Число перенесенных версий.
        """
        moved = 0
        released: set = set()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM file_versions WHERE storage_layer = 'VSS' AND created_at <= datetime('now', ?)",
                (f'-{self.hot_hours} hours',),
            ).fetchall()
            for row in rows:
                try:
                    data = self._load_content(conn, row)
                except OSError as exc:
                    logger.warning(f"[VersionProvider] Версия {row['version_id']} недоступна в VSS: {exc}")
                    continue
                if hashlib.sha256(data).hexdigest() != row['sha256_hash']:
                    logger.warning(f"[VersionProvider] Версия {row['version_id']}: хеш не совпал, перенос пропущен")
                    continue
                blob_id = self._store_blob(conn, data)
                conn.execute(
                    "UPDATE file_versions SET storage_layer='PERSISTENT_BLOB', blob_id=?, snapshot_id=NULL, "
                    "snapshot_device_path=NULL WHERE version_id=?",
                    (blob_id, row['version_id']),
                )
                released.add(row['snapshot_id'])
                moved += 1
            for snap_id in released:
                left = conn.execute('SELECT 1 FROM file_versions WHERE snapshot_id = ?', (snap_id,)).fetchone()
                if left is None:
                    self.vss.delete_snapshot(snap_id)
        return moved

    def purge_expired(self, days: int = 30) -> int:
        """Удаляет версии холодного слоя старше ``days`` суток вместе с блобами.

        Returns:
            int: Число удаленных версий.
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT version_id, blob_id FROM file_versions WHERE storage_layer = 'PERSISTENT_BLOB' "
                "AND created_at <= datetime('now', ?)",
                (f'-{days} days',),
            ).fetchall()
            for row in rows:
                conn.execute('DELETE FROM file_versions WHERE version_id = ?', (row['version_id'],))
                conn.execute('DELETE FROM file_version_blobs WHERE blob_id = ?', (row['blob_id'],))
        return len(rows)
