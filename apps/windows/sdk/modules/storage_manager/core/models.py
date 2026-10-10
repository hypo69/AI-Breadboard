# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Core - Models
# =============================================================================
# Description:
#   Pydantic-модели данных дисковых накопителей, прямого I/O, клонирования и бенчмарка DiskSpd.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.storage_manager.core.models import BenchmarkRequest, BenchmarkSuiteResult
#
#     req = BenchmarkRequest(target_drive='C:', duration_sec=5)
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 01:34:00
# =============================================================================

from __future__ import annotations
"""Pydantic-модели данных дисковых накопителей, прямого I/O, клонирования и бенчмарка DiskSpd."""

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
    vendor: str = ''
    product: str = ''
    revision: str = ''
    bus_type: str = 'UNKNOWN'
    media_type: str = 'UNKNOWN'
    serial_number: str = ''
    firmware_revision: str = ''
    size_bytes: int = 0
    size_gb: float = 0.0
    sector_size: int = 512
    is_removable: bool = False
    is_writable: bool = True
    geometry: DiskGeometryInfo = Field(default_factory=DiskGeometryInfo)
    headers: Optional[DiskHeadersInfo] = None
    partitions: List[PartitionTableEntry] = Field(default_factory=list)
    smart_status: str = 'Healthy'
    smart_temperature_c: Optional[float] = None
    smart_wear_pct: Optional[float] = None
    tbw_written_tb: Optional[float] = None
    tbw_read_tb: Optional[float] = None
    power_on_hours: Optional[int] = None
    unsafe_shutdowns: Optional[int] = None
    media_errors: Optional[int] = None
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
    volume_id: str = ''
    drive_letter: Optional[str] = None
    mount_point: str = ''
    volume_guid: str = ''
    label: str = ''
    filesystem: str = 'NTFS'
    filesystem_flags: int = 0
    total_gb: float = 0.0
    free_gb: float = 0.0
    available_gb: float = 0.0
    percent_used: float = 0.0
    cluster_size_bytes: int = 4096
    sector_size_bytes: int = 512
    health_status: str = 'Healthy'


class DiskIOEvent(BaseModel):
    """Событие прямого ввода-вывода (ETW / Process I/O)."""
    timestamp: str = ''
    created_at: float = 0.0
    pid: int = 0
    process_name: str = ''
    disk_id: int = 0
    operation: str = 'READ'  # 'READ' или 'WRITE'
    bytes_count: int = 0
    duration_ms: Optional[float] = None
    offset: Optional[int] = None
    file_path: Optional[str] = None


class DiskPerformanceMetrics(BaseModel):
    """Счетчики производительности диска в реальном времени (Performance Counters)."""
    disk_id: int = 0
    disk_name: str = ''
    read_bytes_sec: float = 0.0
    write_bytes_sec: float = 0.0
    read_iops: float = 0.0
    write_iops: float = 0.0
    avg_read_latency_ms: float = 0.0
    avg_write_latency_ms: float = 0.0
    disk_time_percent: float = 0.0
    percent_disk_time: float = 0.0
    queue_length: float = 0.0



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


# -----------------------------------------------------------------------------
# DiskSpd Benchmark Models
# -----------------------------------------------------------------------------

class BenchmarkTargetInfo(BaseModel):
    """Информация о целевом накопителе/разделе для бенчмарка."""
    drive_letter: str
    label: str = ""
    fs_type: str = "NTFS"
    total_bytes: int = 0
    free_bytes: int = 0
    free_gb: float = 0.0
    recommended_dir: str = ""
    is_system: bool = False
    is_ssd: bool = True


class BenchmarkRequest(BaseModel):
    """Параметры запуска тестирования производительности DiskSpd."""
    target_drive: str = "C:"
    target_path: Optional[str] = None
    file_size_mb: int = 256
    duration_sec: int = 3
    warmup_sec: int = 0
    cooldown_sec: int = 0
    test_type: str = "both"  # "both", "read", "write"
    profiles: List[str] = Field(
        default_factory=lambda: ["seq1m_q8t1", "seq1m_q1t1", "rnd4k_q32t16", "rnd4k_q1t1"]
    )
    threads: int = 1
    outstanding: int = 32
    block_size: str = "4K"
    disable_cache: bool = True
    custom_args: Optional[List[str]] = None
    delete_test_file: bool = True


class BenchmarkProfileResult(BaseModel):
    """Результаты измерения отдельного профиля нагрузки (SEQ/RND)."""
    profile_name: str
    profile_label: str
    block_size: str
    access_type: str  # "Sequential" или "Random"
    queue_depth: int
    threads: int
    read_mb_s: float = 0.0
    write_mb_s: float = 0.0
    read_iops: float = 0.0
    write_iops: float = 0.0
    read_latency_ms: float = 0.0
    write_latency_ms: float = 0.0
    read_latency_us: float = 0.0
    write_latency_us: float = 0.0
    avg_latency_ms: float = 0.0
    avg_latency_us: float = 0.0
    min_latency_us: Optional[float] = None
    max_latency_us: Optional[float] = None
    cpu_usage_pct: float = 0.0
    test_time_sec: float = 0.0


class BenchmarkSuiteResult(BaseModel):
    """Сводный результат полного бенчмарка накопителя (CrystalDiskMark стиль)."""
    id: str
    target: str
    target_path: str
    file_size_mb: int
    test_duration_sec: int
    test_type: str
    created_at: str
    completed_at: Optional[str] = None
    total_duration_sec: float = 0.0
    disk_name: str = ""
    profiles: Dict[str, BenchmarkProfileResult] = Field(default_factory=dict)
    raw_output: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class BenchmarkHistoryItem(BaseModel):
    """Краткая запись в истории бенчмарков."""
    id: str
    target: str
    created_at: str
    seq1m_read_mb_s: float = 0.0
    seq1m_write_mb_s: float = 0.0
    rnd4k_read_mb_s: float = 0.0
    rnd4k_write_mb_s: float = 0.0
    rnd4k_read_iops: float = 0.0
    rnd4k_write_iops: float = 0.0
    score_summary: str = ""


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
    'BenchmarkTargetInfo',
    'BenchmarkRequest',
    'BenchmarkProfileResult',
    'BenchmarkSuiteResult',
    'BenchmarkHistoryItem',
    'DiskIOEvent',
    'DiskPerformanceMetrics',
]
