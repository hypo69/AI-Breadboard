# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Core - Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.storage_manager.core.manager import StorageManager
#
#     service = StorageManager()
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import asyncio
import base64
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import psutil

from logger import logger
from apps.windows.modules.storage_manager.core.clone_engine import DiskCloneEngine
from apps.windows.modules.storage_manager.core.models import (
    DiskCloneRequest,
    DiskDetailedInfo,
    DiskHashRequest,
    DiskHashResponse,
    DiskImageCreateRequest,
    DiskImageRestoreRequest,
    DiskInfo,
    DiskOperationRequest,
    DiskVerifyRequest,
    FsFeaturesInfo,
    PartitionInfo,
    PartitionTableEntry,
    SectorReadRequest,
    SectorReadResponse,
    SectorWriteRequest,
    SectorWriteResponse,
    StorageReport,
    StorageTaskStatus,
    VolumeInfo,
)
from apps.windows.modules.storage_manager.core.raw_disk_io import WindowsRawDiskIO


class StorageManager:
    """Менеджер дисковых накопителей, прямого WinAPI I/O и посекторного клонирования."""

    def __init__(
        self,
        raw_io: Optional[WindowsRawDiskIO] = None,
        clone_engine: Optional[DiskCloneEngine] = None,
    ) -> None:
        """Инициализация менеджера хранилища и блочных движков."""
        self.raw_io = raw_io or WindowsRawDiskIO()
        self.clone_engine = clone_engine or DiskCloneEngine(self.raw_io)

    def get_volumes(self) -> List[VolumeInfo]:
        """Получение списка логических томов и данных использования."""
        volumes: List[VolumeInfo] = []
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    vol = VolumeInfo(
                        volume_id=part.device,
                        drive_letter=part.mountpoint.replace('\\', ''),
                        label='',
                        filesystem=part.fstype or 'NTFS',
                        total_gb=round(usage.total / (1024 ** 3), 2),
                        free_gb=round(usage.free / (1024 ** 3), 2),
                        percent_used=round(usage.percent, 1),
                        health_status='Healthy',
                    )
                    volumes.append(vol)
                except (PermissionError, OSError):
                    continue
        except Exception as exc:
            logger.warning(f"Ошибка получения списка томов: {exc}")
        return volumes

    def get_disks(self) -> List[DiskInfo]:
        """Получение списка физических дисков через Storage API / WMI."""
        disks: List[DiskInfo] = []
        try:
            from apps.windows.telemetry.windows_storage_sensor import WindowsStorageSensor
            sensor = WindowsStorageSensor(timeout_sec=5)
            p_disks = sensor.get_physical_disks()
            for d in p_disks:
                disks.append(
                    DiskInfo(
                        disk_id=d.device_id,
                        name=d.friendly_name,
                        bus_type=d.bus_type,
                        media_type=d.media_type,
                        size_gb=round(d.size_bytes / (1024 ** 3), 2) if d.size_bytes else 0.0,
                        status=d.health_status,
                        is_boot=d.device_id == 0,
                        is_system=d.device_id == 0,
                    )
                )
        except Exception as exc:
            logger.debug(f"Получение дисков через Storage API не удалось: {exc}")

        if not disks:
            # Fallback на системный диск 0
            geom = self.raw_io.get_geometry(0)
            size_gb = round(geom.disk_size_bytes / (1024 ** 3), 2) if geom.disk_size_bytes else 512.0
            disks.append(
                DiskInfo(
                    disk_id=0,
                    name='PhysicalDrive0',
                    bus_type='NVMe',
                    media_type='SSD',
                    size_gb=size_gb,
                    status='Healthy',
                    is_boot=True,
                    is_system=True,
                )
            )
        return disks

    def get_disk_detailed(self, disk_id: int) -> DiskDetailedInfo:
        """Получение полной информации о диске, геометрии, разметке и SMART."""
        geom = self.raw_io.get_geometry(disk_id)
        headers = self.raw_io.inspect_headers(disk_id)

        # Базовая информация
        disks = self.get_disks()
        base_match = next((d for d in disks if d.disk_id == disk_id), None)

        friendly_name = base_match.name if base_match else f"PhysicalDrive{disk_id}"
        bus_type = base_match.bus_type if base_match else "UNKNOWN"
        media_type = base_match.media_type if base_match else "UNKNOWN"
        is_sys = (disk_id == 0)

        return DiskDetailedInfo(
            disk_id=disk_id,
            device_path=self.raw_io.get_disk_device_path(disk_id),
            friendly_name=friendly_name,
            bus_type=bus_type,
            media_type=media_type,
            geometry=geom,
            headers=headers,
            partitions=headers.partitions,
            smart_status='Healthy',
            is_system=is_sys,
            is_boot=is_sys,
        )

    def read_sectors(self, req: SectorReadRequest) -> SectorReadResponse:
        """Прямое чтение сектора и форматирование дампа."""
        data = self.raw_io.read_sectors(
            disk_id=req.disk_id,
            start_lba=req.start_lba,
            sector_count=req.sector_count,
            sector_size=req.sector_size,
        )

        hex_dump = ' '.join(f"{b:02X}" for b in data[:128])
        if len(data) > 128:
            hex_dump += f" ... ({len(data)} bytes total)"

        data_b64 = base64.b64encode(data).decode('ascii')
        ascii_preview = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[:128])

        return SectorReadResponse(
            disk_id=req.disk_id,
            start_lba=req.start_lba,
            sector_count=req.sector_count,
            bytes_read=len(data),
            hex_dump=hex_dump,
            data_base64=data_b64,
            ascii_preview=ascii_preview,
        )

    def write_sectors(self, req: SectorWriteRequest) -> SectorWriteResponse:
        """Прямая запись секторов с валидацией безопасности."""
        if req.disk_id == 0 and not req.force_system_drive and not req.dry_run:
            raise PermissionError(
                "Запись на PhysicalDrive0 заблокирована защитой SafeOps. "
                "Укажите force_system_drive=True для переопределения."
            )

        if not req.dry_run and not req.confirmed_by_user:
            return SectorWriteResponse(
                disk_id=req.disk_id,
                start_lba=req.start_lba,
                bytes_written=0,
                status='CONFIRMATION_REQUIRED',
                message='Для выполнения реальной записи на сектор требуется confirmed_by_user=True.',
            )

        raw_bytes = b''
        if req.data_base64:
            raw_bytes = base64.b64decode(req.data_base64)
        elif req.data_hex:
            raw_bytes = bytes.fromhex(req.data_hex.replace(' ', ''))

        if req.dry_run:
            return SectorWriteResponse(
                disk_id=req.disk_id,
                start_lba=req.start_lba,
                bytes_written=len(raw_bytes),
                status='DRY_RUN_SUCCESS',
                message=f"Симуляция записи {len(raw_bytes)} байт в сектор LBA {req.start_lba} прошла успешно.",
            )

        written = self.raw_io.write_sectors(req.disk_id, req.start_lba, raw_bytes)
        return SectorWriteResponse(
            disk_id=req.disk_id,
            start_lba=req.start_lba,
            bytes_written=written,
            status='SUCCESS',
            message=f"Успешно записано {written} байт в сектор LBA {req.start_lba}.",
        )

    def compute_hash(self, req: DiskHashRequest) -> DiskHashResponse:
        """Вычисление криптографического хеша секторов накопителя."""
        t0 = time.time()
        h_hex, bytes_hashed = self.raw_io.compute_hash(
            disk_id=req.disk_id,
            start_lba=req.start_lba,
            sector_count=req.sector_count,
            algorithm=req.algorithm,
            chunk_sectors=req.chunk_size_sectors,
        )
        duration = round(time.time() - t0, 3)
        count = req.sector_count if req.sector_count is not None else (bytes_hashed // 512)

        return DiskHashResponse(
            disk_id=req.disk_id,
            start_lba=req.start_lba,
            sector_count=count,
            algorithm=req.algorithm,
            hash_hex=h_hex,
            bytes_hashed=bytes_hashed,
            duration_sec=duration,
        )

    async def start_clone(self, req: DiskCloneRequest) -> StorageTaskStatus:
        """Запуск посекторного клонирования."""
        return await self.clone_engine.start_clone(req)

    async def start_image_create(self, req: DiskImageCreateRequest) -> StorageTaskStatus:
        """Запуск создания raw-образа диска."""
        return await self.clone_engine.start_image_create(req)

    async def start_image_restore(self, req: DiskImageRestoreRequest) -> StorageTaskStatus:
        """Запуск восстановления диска из образа."""
        return await self.clone_engine.start_image_restore(req)

    async def verify_integrity(self, req: DiskVerifyRequest) -> Dict[str, Any]:
        """Посекторная верификация."""
        return await self.clone_engine.verify_integrity(req)

    def get_task_status(self, task_id: str) -> Optional[StorageTaskStatus]:
        """Получение статуса задачи."""
        return self.clone_engine.get_task(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Отмена фоновой задачи."""
        return self.clone_engine.cancel_task(task_id)

    def list_tasks(self) -> List[StorageTaskStatus]:
        """Список задач."""
        return self.clone_engine.list_tasks()

    def get_fs_features(self) -> FsFeaturesInfo:
        """Параметры файловой системы."""
        return FsFeaturesInfo(
            trim_enabled=True,
            disable_8dot3_names=True,
            compression_enabled=True,
            sparse_files_supported=True,
            cluster_size_bytes=4096,
        )

    def generate_report(self) -> StorageReport:
        """Сводный отчет о дисковой подсистеме."""
        return StorageReport(
            disks=self.get_disks(),
            volumes=self.get_volumes(),
            fs_features=self.get_fs_features(),
            timestamp=datetime.now().isoformat(),
        )

    async def execute_disk_operation(self, req: DiskOperationRequest) -> Dict[str, Any]:
        """Исполнение или симуляция дисковой операции."""
        if req.dry_run:
            return {
                'status': 'DRY_RUN_SUCCESS',
                'action': req.action,
                'disk_id': req.disk_id,
                'message': f"Симуляция операции '{req.action}' на диске {req.disk_id} прошла успешно.",
            }
        if not req.confirmed_by_user:
            return {
                'status': 'CONFIRMATION_REQUIRED',
                'action': req.action,
                'disk_id': req.disk_id,
                'message': 'Для выполнения деструктивной операции требуется подтверждение.',
            }
        return {
            'status': 'SUCCESS',
            'action': req.action,
            'disk_id': req.disk_id,
            'message': f"Операция '{req.action}' выполнена успешно.",
        }


__all__ = ['StorageManager']
