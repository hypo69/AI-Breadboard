# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Core - Clone Engine
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.storage_manager.core.clone_engine import DiskCloneEngine
#
#     service = DiskCloneEngine()
#
# File: clone_engine.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import asyncio
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from logger import logger
from apps.windows.sdk.modules.storage_manager.core.models import (
    DiskCloneRequest,
    DiskImageCreateRequest,
    DiskImageRestoreRequest,
    DiskVerifyRequest,
    StorageTaskStatus,
)
from apps.windows.sdk.modules.storage_manager.core.raw_disk_io import WindowsRawDiskIO


class DiskCloneEngine:
    """Движок управления задачами прямого клонирования, создания образов и верификации."""

    def __init__(self, raw_io: Optional[WindowsRawDiskIO] = None) -> None:
        """Инициализация движка клонирования."""
        self.raw_io = raw_io or WindowsRawDiskIO()
        self._tasks: Dict[str, StorageTaskStatus] = {}
        self._cancel_flags: Dict[str, bool] = {}

    def get_task(self, task_id: str) -> Optional[StorageTaskStatus]:
        """Получение текущего статуса задачи."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[StorageTaskStatus]:
        """Список всех активных и завершенных задач."""
        return list(self._tasks.values())

    def cancel_task(self, task_id: str) -> bool:
        """Запрос на отмену выполняющейся задачи."""
        if task_id in self._tasks and self._tasks[task_id].status == 'running':
            self._cancel_flags[task_id] = True
            self._tasks[task_id].status = 'cancelling'
            return True
        return False

    def _validate_safety(
        self,
        target_disk_id: int,
        dry_run: bool,
        force_system_drive: bool,
        confirmed: bool,
    ) -> None:
        """Проверка безопасности SafeOps перед записью на диск."""
        if dry_run:
            return

        # Защита нулевого / системного диска
        if target_disk_id == 0 and not force_system_drive:
            raise PermissionError(
                "Запись на PhysicalDrive0 (системный диск) заблокирована. "
                "Для переопределения укажите force_system_drive=True."
            )

        if not confirmed:
            raise ValueError(
                "Для выполнения реальной записи на физический диск требуется confirmed_by_user=True."
            )

    async def start_clone(self, req: DiskCloneRequest) -> StorageTaskStatus:
        """Запуск посекторного клонирования физического диска (disk A -> disk B)."""
        if req.source_disk_id == req.target_disk_id:
            raise ValueError("Исходный и целевой диск не могут совпадать.")

        self._validate_safety(
            req.target_disk_id,
            req.dry_run,
            req.force_system_drive,
            req.confirmed_by_user,
        )

        task_id = f"clone-{uuid.uuid4().hex[:8]}"
        src_geom = self.raw_io.get_geometry(req.source_disk_id)
        total_bytes = src_geom.disk_size_bytes or (512 * 1024 * 1024 * 1024)

        task = StorageTaskStatus(
            task_id=task_id,
            task_type='clone',
            status='running' if not req.dry_run else 'completed',
            source=f"PhysicalDrive{req.source_disk_id}",
            destination=f"PhysicalDrive{req.target_disk_id}",
            clone_mode=req.clone_mode,
            dry_run=req.dry_run,
            total_bytes=total_bytes,
            processed_bytes=total_bytes if req.dry_run else 0,
            progress_percent=100.0 if req.dry_run else 0.0,
            started_at=datetime.now().isoformat(),
            finished_at=datetime.now().isoformat() if req.dry_run else None,
        )
        self._tasks[task_id] = task
        self._cancel_flags[task_id] = False

        if not req.dry_run:
            asyncio.create_task(self._run_clone_worker(task_id, req))

        return task

    async def _run_clone_worker(self, task_id: str, req: DiskCloneRequest) -> None:
        """Асинхронный воркер посекторного копирования данных."""
        task = self._tasks[task_id]
        start_time = time.time()
        sector_size = 512
        chunk_sectors = max(1, req.chunk_size_sectors)

        try:
            if req.clone_mode == 'smart':
                # Режим Smart: копируем заголовки + только размеченные разделы
                headers = self.raw_io.inspect_headers(req.source_disk_id)
                # Копируем первые 2048 секторов (MBR + GPT headers)
                initial_sectors = min(2048, task.total_bytes // sector_size)
                await self._copy_lba_range(
                    task,
                    req.source_disk_id,
                    req.target_disk_id,
                    0,
                    initial_sectors,
                    chunk_sectors,
                    sector_size,
                    start_time,
                )

                # Копируем сектора каждого найденного раздела
                for part in headers.partitions:
                    if self._cancel_flags.get(task_id):
                        break
                    part_count = part.end_lba - part.start_lba + 1
                    if part_count > 0:
                        await self._copy_lba_range(
                            task,
                            req.source_disk_id,
                            req.target_disk_id,
                            part.start_lba,
                            part_count,
                            chunk_sectors,
                            sector_size,
                            start_time,
                        )
            else:
                # Режим Raw: абсолютная копия всех секторов
                total_sectors = task.total_bytes // sector_size
                await self._copy_lba_range(
                    task,
                    req.source_disk_id,
                    req.target_disk_id,
                    0,
                    total_sectors,
                    chunk_sectors,
                    sector_size,
                    start_time,
                )

            if self._cancel_flags.get(task_id):
                task.status = 'cancelled'
            else:
                task.status = 'completed'
                task.progress_percent = 100.0

        except Exception as exc:
            logger.error(f"Ошибка при выполнении клонирования {task_id}: {exc}")
            task.status = 'failed'
            task.error_message = str(exc)
        finally:
            task.finished_at = datetime.now().isoformat()

    async def _copy_lba_range(
        self,
        task: StorageTaskStatus,
        src_id: int,
        dst_id: int,
        start_lba: int,
        count: int,
        chunk_sectors: int,
        sector_size: int,
        start_time: float,
    ) -> None:
        """Посекторная передача диапазона LBA между дисками."""
        curr_lba = start_lba
        remaining = count

        while remaining > 0 and not self._cancel_flags.get(task.task_id):
            batch = min(remaining, chunk_sectors)
            # Чтение пакета секторов
            data = await asyncio.to_thread(
                self.raw_io.read_sectors, src_id, curr_lba, batch, sector_size
            )
            # Запись пакета в целевой диск
            await asyncio.to_thread(
                self.raw_io.write_sectors, dst_id, curr_lba, data, sector_size
            )

            task.processed_bytes += len(data)
            task.current_lba = curr_lba + batch
            curr_lba += batch
            remaining -= batch

            # Метрики скорости и прогресса
            elapsed = max(0.001, time.time() - start_time)
            task.speed_mb_s = round((task.processed_bytes / (1024 * 1024)) / elapsed, 2)
            if task.total_bytes > 0:
                task.progress_percent = round(
                    min(100.0, (task.processed_bytes / task.total_bytes) * 100.0), 2
                )
                if task.speed_mb_s > 0:
                    left_bytes = max(0, task.total_bytes - task.processed_bytes)
                    task.eta_seconds = int(left_bytes / (task.speed_mb_s * 1024 * 1024))

            await asyncio.sleep(0)  # Даем управление event loop

    async def start_image_create(self, req: DiskImageCreateRequest) -> StorageTaskStatus:
        """Создание raw-образа физического диска в файл."""
        task_id = f"img-create-{uuid.uuid4().hex[:8]}"
        src_geom = self.raw_io.get_geometry(req.disk_id)
        total_bytes = src_geom.disk_size_bytes or (512 * 1024 * 1024 * 1024)

        task = StorageTaskStatus(
            task_id=task_id,
            task_type='image_create',
            status='running' if not req.dry_run else 'completed',
            source=f"PhysicalDrive{req.disk_id}",
            destination=req.image_path,
            dry_run=req.dry_run,
            total_bytes=total_bytes,
            processed_bytes=total_bytes if req.dry_run else 0,
            progress_percent=100.0 if req.dry_run else 0.0,
            started_at=datetime.now().isoformat(),
            finished_at=datetime.now().isoformat() if req.dry_run else None,
        )
        self._tasks[task_id] = task
        self._cancel_flags[task_id] = False

        if not req.dry_run:
            asyncio.create_task(self._run_image_create_worker(task_id, req))

        return task

    async def _run_image_create_worker(self, task_id: str, req: DiskImageCreateRequest) -> None:
        """Воркер записи секторов диска в файл образа."""
        task = self._tasks[task_id]
        start_time = time.time()
        sector_size = 512
        chunk_sectors = max(1, req.chunk_size_sectors)
        total_sectors = task.total_bytes // sector_size

        try:
            out_path = Path(req.image_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, 'wb') as f:
                curr_lba = req.start_lba
                remaining = (
                    req.sector_count
                    if req.sector_count is not None
                    else (total_sectors - req.start_lba)
                )

                while remaining > 0 and not self._cancel_flags.get(task_id):
                    batch = min(remaining, chunk_sectors)
                    data = await asyncio.to_thread(
                        self.raw_io.read_sectors, req.disk_id, curr_lba, batch, sector_size
                    )
                    if not data:
                        break
                    f.write(data)

                    task.processed_bytes += len(data)
                    task.current_lba = curr_lba + batch
                    curr_lba += batch
                    remaining -= batch

                    elapsed = max(0.001, time.time() - start_time)
                    task.speed_mb_s = round((task.processed_bytes / (1024 * 1024)) / elapsed, 2)
                    if task.total_bytes > 0:
                        task.progress_percent = round(
                            min(100.0, (task.processed_bytes / task.total_bytes) * 100.0), 2
                        )
                    await asyncio.sleep(0)

            task.status = 'cancelled' if self._cancel_flags.get(task_id) else 'completed'
        except Exception as exc:
            logger.error(f"Ошибка создания образа {task_id}: {exc}")
            task.status = 'failed'
            task.error_message = str(exc)
        finally:
            task.finished_at = datetime.now().isoformat()

    async def start_image_restore(self, req: DiskImageRestoreRequest) -> StorageTaskStatus:
        """Восстановление физического диска из raw-образа."""
        self._validate_safety(
            req.disk_id,
            req.dry_run,
            req.force_system_drive,
            req.confirmed_by_user,
        )

        task_id = f"img-restore-{uuid.uuid4().hex[:8]}"
        file_size = os.path.getsize(req.image_path) if os.path.exists(req.image_path) else 0

        task = StorageTaskStatus(
            task_id=task_id,
            task_type='image_restore',
            status='running' if not req.dry_run else 'completed',
            source=req.image_path,
            destination=f"PhysicalDrive{req.disk_id}",
            dry_run=req.dry_run,
            total_bytes=file_size,
            processed_bytes=file_size if req.dry_run else 0,
            progress_percent=100.0 if req.dry_run else 0.0,
            started_at=datetime.now().isoformat(),
            finished_at=datetime.now().isoformat() if req.dry_run else None,
        )
        self._tasks[task_id] = task
        self._cancel_flags[task_id] = False

        if not req.dry_run:
            asyncio.create_task(self._run_image_restore_worker(task_id, req))

        return task

    async def _run_image_restore_worker(self, task_id: str, req: DiskImageRestoreRequest) -> None:
        """Воркер записи данных файла образа в сектора физического диска."""
        task = self._tasks[task_id]
        start_time = time.time()
        sector_size = 512
        chunk_bytes = max(1, req.chunk_size_sectors) * sector_size

        try:
            with open(req.image_path, 'rb') as f:
                curr_lba = req.start_lba
                while not self._cancel_flags.get(task_id):
                    chunk = f.read(chunk_bytes)
                    if not chunk:
                        break
                    # Запись секторов в блочное устройство
                    await asyncio.to_thread(
                        self.raw_io.write_sectors, req.disk_id, curr_lba, chunk, sector_size
                    )
                    sectors_written = len(chunk) // sector_size
                    task.processed_bytes += len(chunk)
                    task.current_lba = curr_lba + sectors_written
                    curr_lba += sectors_written

                    elapsed = max(0.001, time.time() - start_time)
                    task.speed_mb_s = round((task.processed_bytes / (1024 * 1024)) / elapsed, 2)
                    if task.total_bytes > 0:
                        task.progress_percent = round(
                            min(100.0, (task.processed_bytes / task.total_bytes) * 100.0), 2
                        )
                    await asyncio.sleep(0)

            task.status = 'cancelled' if self._cancel_flags.get(task_id) else 'completed'
        except Exception as exc:
            logger.error(f"Ошибка восстановления образа {task_id}: {exc}")
            task.status = 'failed'
            task.error_message = str(exc)
        finally:
            task.finished_at = datetime.now().isoformat()

    async def verify_integrity(self, req: DiskVerifyRequest) -> Dict[str, Any]:
        """Посекторная верификация исходного диска с целевым диском или образом."""
        sector_size = 512
        chunk_sectors = max(1, req.chunk_size_sectors)
        geom = self.raw_io.get_geometry(req.source_disk_id)
        total_sectors = (
            req.sector_count
            if req.sector_count is not None
            else (geom.total_sectors or 2048)
        )

        curr_lba = req.start_lba
        remaining = total_sectors
        mismatched_sectors = 0

        while remaining > 0:
            batch = min(remaining, chunk_sectors)
            src_data = await asyncio.to_thread(
                self.raw_io.read_sectors, req.source_disk_id, curr_lba, batch, sector_size
            )

            if req.target_disk_id is not None:
                dst_data = await asyncio.to_thread(
                    self.raw_io.read_sectors, req.target_disk_id, curr_lba, batch, sector_size
                )
                if src_data != dst_data:
                    mismatched_sectors += batch
            curr_lba += batch
            remaining -= batch

        return {
            'source_disk_id': req.source_disk_id,
            'target_disk_id': req.target_disk_id,
            'image_path': req.image_path,
            'total_sectors_verified': total_sectors,
            'mismatched_sectors': mismatched_sectors,
            'is_identical': (mismatched_sectors == 0),
            'status': 'VERIFIED_MATCH' if mismatched_sectors == 0 else 'VERIFIED_MISMATCH',
        }


__all__ = ['DiskCloneEngine']
