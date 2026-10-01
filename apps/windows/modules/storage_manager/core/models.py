# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.storage_manager.core.models import DiskGeometryInfo
#
#     service = DiskGeometryInfo()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DiskGeometryInfo(BaseModel):
    """Геометрия и физические параметры диска."""
    cylinders: int = 0
    tracks_per_cylinder: int = 0
    sectors_per_track: int = 0
    bytes_per_sector: int = 512
    total_sectors: int = 0
    disk_size_bytes: int = 0


class PartitionTableEntry(BaseModel):
    """Информация о записи таблицы разделов (MBR или GPT)."""
    partition_number: int
    partition_style: str = 'GPT'  # MBR или GPT
    starting_offset: int = 0
    partition_length: int = 0
    start_lba: int = 0
    end_lba: int = 0
    partition_type: str = ''
    partition_id_guid: Optional[str] = None
    is_bootable: bool = False
    is_hidden: bool = False
    drive_letter: Optional[str] = None


class DiskHeadersInfo(BaseModel):
    """Информация о заголовках и разметке накопителя."""
    disk_id: int
    has_valid_mbr: bool = False
    mbr_signature: str = ''
    has_valid_gpt: bool = False
    gpt_header_lba: int = 1
    gpt_guid: str = ''
    partition_count: int = 0
    partitions: List[PartitionTableEntry] = Field(default_factory=list)


class DiskInfo(BaseModel):
    """Информация о физическом накопителе."""
    disk_id: int
    name: str = ''
    bus_type: str = 'UNKNOWN'
    media_type: str = 'UNKNOWN'
    size_gb: float = 0.0
    status: str = 'Online'
    partition_style: str = 'GPT'
    is_boot: bool = False
    is_system: bool = False


class DiskDetailedInfo(BaseModel):
    """Полная детальная информация о накопителе (геометрия, SMART, заголовки)."""
    disk_id: int
    device_path: str = ''
    friendly_name: str = ''
    bus_type: str = 'UNKNOWN'
    media_type: str = 'UNKNOWN'
    serial_number: str = ''
    firmware_revision: str = ''
    geometry: DiskGeometryInfo = Field(default_factory=DiskGeometryInfo)
    headers: Optional[DiskHeadersInfo] = None
    partitions: List[PartitionTableEntry] = Field(default_factory=list)
    smart_status: str = 'Healthy'
    smart_temperature_c: Optional[float] = None
    is_system: bool = False
    is_boot: bool = False
    is_read_only: bool = False


class PartitionInfo(BaseModel):
    """Информация о разделе диска."""
    disk_id: int
    partition_id: int
    size_mb: float = 0.0
    partition_type: str = 'Primary'
    drive_letter: Optional[str] = None
    is_active: bool = False
    is_hidden: bool = False


class VolumeInfo(BaseModel):
    """Информация о логическом томе."""
    volume_id: str
    drive_letter: Optional[str] = None
    label: str = ''
    filesystem: str = 'NTFS'
    total_gb: float = 0.0
    free_gb: float = 0.0
    percent_used: float = 0.0
    health_status: str = 'Healthy'


class FsFeaturesInfo(BaseModel):
    """Состояние расширенных возможностей файловой системы."""
    trim_enabled: bool = True
    disable_8dot3_names: bool = True
    compression_enabled: bool = True
    sparse_files_supported: bool = True
    cluster_size_bytes: int = 4096


class StorageReport(BaseModel):
    """Сводный отчет о состоянии дисковой подсистемы."""
    disks: List[DiskInfo] = Field(default_factory=list)
    volumes: List[VolumeInfo] = Field(default_factory=list)
    fs_features: Optional[FsFeaturesInfo] = None
    timestamp: str = ''


# -----------------------------------------------------------------------------
# Модели для прямых блочных операций (WinAPI / Raw I/O)
# -----------------------------------------------------------------------------

class SectorReadRequest(BaseModel):
    """Запрос на прямое чтение диапазона секторов."""
    disk_id: int
    start_lba: int = 0
    sector_count: int = 1
    sector_size: int = 512


class SectorReadResponse(BaseModel):
    """Результат прямого чтения секторов."""
    disk_id: int
    start_lba: int
    sector_count: int
    bytes_read: int
    hex_dump: str = ''
    data_base64: str = ''
    ascii_preview: str = ''


class SectorWriteRequest(BaseModel):
    """Запрос на прямую запись в сектор."""
    disk_id: int
    start_lba: int
    data_base64: Optional[str] = None
    data_hex: Optional[str] = None
    dry_run: bool = True
    force_system_drive: bool = False
    confirmed_by_user: bool = False


class SectorWriteResponse(BaseModel):
    """Результат прямой записи секторов."""
    disk_id: int
    start_lba: int
    bytes_written: int
    status: str
    message: str


class DiskCloneRequest(BaseModel):
    """Запрос на посекторное клонирование физического диска в другой диск."""
    source_disk_id: int
    target_disk_id: int
    clone_mode: str = 'raw'  # 'raw' (посекторно всё) или 'smart' (только активные разделы)
    chunk_size_sectors: int = 2048  # 1MB при секторе 512 байт
    dry_run: bool = True
    force_system_drive: bool = False
    confirmed_by_user: bool = False


class DiskImageCreateRequest(BaseModel):
    """Запрос на создание raw-образа физического накопителя."""
    disk_id: int
    image_path: str
    start_lba: int = 0
    sector_count: Optional[int] = None
    chunk_size_sectors: int = 2048
    dry_run: bool = True


class DiskImageRestoreRequest(BaseModel):
    """Запрос на восстановление физического накопителя из raw-образа."""
    disk_id: int
    image_path: str
    start_lba: int = 0
    chunk_size_sectors: int = 2048
    dry_run: bool = True
    force_system_drive: bool = False
    confirmed_by_user: bool = False


class DiskVerifyRequest(BaseModel):
    """Запрос на посекторную верификацию накопителя."""
    source_disk_id: int
    target_disk_id: Optional[int] = None
    image_path: Optional[str] = None
    start_lba: int = 0
    sector_count: Optional[int] = None
    chunk_size_sectors: int = 2048


class DiskHashRequest(BaseModel):
    """Запрос на вычисление криптографического хеша секторов диска."""
    disk_id: int
    start_lba: int = 0
    sector_count: Optional[int] = None
    algorithm: str = 'sha256'
    chunk_size_sectors: int = 2048


class DiskHashResponse(BaseModel):
    """Результат вычисления хеша диска."""
    disk_id: int
    start_lba: int
    sector_count: int
    algorithm: str
    hash_hex: str
    bytes_hashed: int
    duration_sec: float


class StorageTaskStatus(BaseModel):
    """Статус фоновой задачи клонирования / создания образа / верификации."""
    task_id: str
    task_type: str  # clone, image_create, image_restore, verify, hash
    status: str  # pending, running, completed, failed, cancelled
    source: str
    destination: str
    clone_mode: str = 'raw'
    dry_run: bool = False
    total_bytes: int = 0
    processed_bytes: int = 0
    progress_percent: float = 0.0
    current_lba: int = 0
    speed_mb_s: float = 0.0
    eta_seconds: Optional[int] = None
    error_message: Optional[str] = None
    started_at: str = ''
    finished_at: Optional[str] = None


class DiskOperationRequest(BaseModel):
    """Запрос на выполнение общей дисковой операции."""
    disk_id: int
    action: str
    partition_id: Optional[int] = None
    size_mb: Optional[int] = None
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'DiskGeometryInfo',
    'PartitionTableEntry',
    'DiskHeadersInfo',
    'DiskInfo',
    'DiskDetailedInfo',
    'PartitionInfo',
    'VolumeInfo',
    'FsFeaturesInfo',
    'StorageReport',
    'SectorReadRequest',
    'SectorReadResponse',
    'SectorWriteRequest',
    'SectorWriteResponse',
    'DiskCloneRequest',
    'DiskImageCreateRequest',
    'DiskImageRestoreRequest',
    'DiskVerifyRequest',
    'DiskHashRequest',
    'DiskHashResponse',
    'StorageTaskStatus',
    'DiskOperationRequest',
]
