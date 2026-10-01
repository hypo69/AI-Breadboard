# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Core - Raw Disk Io
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.storage_manager.core.raw_disk_io import DISK_GEOMETRY
#
#     service = DISK_GEOMETRY()
#
# File: raw_disk_io.py
# Project: ai-breadboard
# Package: apps.windows.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import ctypes
import ctypes.wintypes as wintypes
import hashlib
import struct
import sys
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple

from logger import logger
from apps.windows.modules.storage_manager.core.models import (
    DiskGeometryInfo,
    DiskHeadersInfo,
    PartitionTableEntry,
)

# Win32 Константы блочного доступа
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
FILE_FLAG_NO_BUFFERING = 0x20000000
FILE_FLAG_WRITE_THROUGH = 0x80000000

INVALID_HANDLE_VALUE = -1

# IOCTL Коды управления дисками
IOCTL_DISK_GET_DRIVE_GEOMETRY_EX = 0x000700A0
IOCTL_DISK_GET_DRIVE_LAYOUT_EX = 0x00070050
IOCTL_STORAGE_QUERY_PROPERTY = 0x002D1400
FSCTL_LOCK_VOLUME = 0x00090018
FSCTL_UNLOCK_VOLUME = 0x0009001C
FSCTL_DISMOUNT_VOLUME = 0x00090020

# GPT GUID типов разделов
GPT_SYSTEM_PARTITION_GUID = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"
GPT_MS_BASIC_DATA_GUID = "EBD0A0A2-B9E5-4433-87C0-68B6B72699C7"
GPT_MS_RESERVED_GUID = "E3C9E310-0B5E-4962-833B-F9A41F14E882"
GPT_MS_RECOVERY_GUID = "DE94BBA4-06D1-4D40-A16A-BFD50179D6AC"


class DISK_GEOMETRY(ctypes.Structure):
    _fields_ = [
        ('Cylinders', wintypes.LARGE_INTEGER),
        ('MediaType', wintypes.DWORD),
        ('TracksPerCylinder', wintypes.DWORD),
        ('SectorsPerTrack', wintypes.DWORD),
        ('BytesPerSector', wintypes.DWORD),
    ]


class DISK_GEOMETRY_EX(ctypes.Structure):
    _fields_ = [
        ('Geometry', DISK_GEOMETRY),
        ('DiskSize', wintypes.LARGE_INTEGER),
        ('Data', ctypes.c_byte * 1),
    ]


class WindowsRawDiskIO:
    """Управление прямым блочным вводом-выводом для физических дисков Windows."""

    def __init__(self) -> None:
        """Инициализация WinAPI привязок."""
        self.is_win32 = sys.platform == 'win32'
        if self.is_win32:
            self._kernel32 = ctypes.windll.kernel32
            self._setup_win32_signatures()
        else:
            self._kernel32 = None

    def _setup_win32_signatures(self) -> None:
        """Настройка типов сигнатур ctypes."""
        if not self._kernel32:
            return
        self._kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        self._kernel32.CreateFileW.restype = wintypes.HANDLE

        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL

        self._kernel32.ReadFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        self._kernel32.ReadFile.restype = wintypes.BOOL

        self._kernel32.WriteFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPCVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        self._kernel32.WriteFile.restype = wintypes.BOOL

        self._kernel32.SetFilePointerEx.argtypes = [
            wintypes.HANDLE,
            wintypes.LARGE_INTEGER,
            ctypes.POINTER(wintypes.LARGE_INTEGER),
            wintypes.DWORD,
        ]
        self._kernel32.SetFilePointerEx.restype = wintypes.BOOL

        self._kernel32.DeviceIoControl.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        self._kernel32.DeviceIoControl.restype = wintypes.BOOL

    def get_disk_device_path(self, disk_id: int) -> str:
        """Формирование пути прямого устройства PhysicalDrive."""
        return rf"\\.\PhysicalDrive{disk_id}"

    @contextmanager
    def open_disk(
        self,
        disk_id: int,
        write_access: bool = False,
        no_buffering: bool = False,
    ) -> Generator[Optional[int], None, None]:
        """Контекстный менеджер для открытия дескриптора физического диска."""
        if not self.is_win32 or not self._kernel32:
            logger.debug("WinAPI недоступен на данной платформе, дескриптор None")
            yield None
            return

        device_path = self.get_disk_device_path(disk_id)
        access = GENERIC_READ
        if write_access:
            access |= GENERIC_WRITE

        share_mode = FILE_SHARE_READ | FILE_SHARE_WRITE
        flags = FILE_ATTRIBUTE_NORMAL
        if no_buffering:
            flags |= FILE_FLAG_NO_BUFFERING | FILE_FLAG_WRITE_THROUGH

        handle = self._kernel32.CreateFileW(
            device_path,
            access,
            share_mode,
            None,
            OPEN_EXISTING,
            flags,
            None,
        )

        if handle == INVALID_HANDLE_VALUE or handle == 0:
            err = self._kernel32.GetLastError()
            logger.warning(
                f"Не удалось открыть {device_path} (write={write_access}): код ошибки {err}"
            )
            yield None
            return

        try:
            yield handle
        finally:
            self._kernel32.CloseHandle(handle)

    def get_geometry(self, disk_id: int) -> DiskGeometryInfo:
        """Получение геометрии и точного размера диска через IOCTL."""
        info = DiskGeometryInfo(bytes_per_sector=512)
        if not self.is_win32 or not self._kernel32:
            info.disk_size_bytes = 512 * 1024 * 1024 * 1024  # 512 GB Mock
            info.total_sectors = info.disk_size_bytes // 512
            return info

        with self.open_disk(disk_id, write_access=False) as handle:
            if not handle:
                return info

            geom_ex = DISK_GEOMETRY_EX()
            bytes_returned = wintypes.DWORD(0)
            res = self._kernel32.DeviceIoControl(
                handle,
                IOCTL_DISK_GET_DRIVE_GEOMETRY_EX,
                None,
                0,
                ctypes.byref(geom_ex),
                ctypes.sizeof(DISK_GEOMETRY_EX),
                ctypes.byref(bytes_returned),
                None,
            )

            if res:
                info.cylinders = geom_ex.Geometry.Cylinders
                info.tracks_per_cylinder = geom_ex.Geometry.TracksPerCylinder
                info.sectors_per_track = geom_ex.Geometry.SectorsPerTrack
                info.bytes_per_sector = max(512, geom_ex.Geometry.BytesPerSector)
                info.disk_size_bytes = geom_ex.DiskSize
                info.total_sectors = (
                    info.disk_size_bytes // info.bytes_per_sector
                    if info.bytes_per_sector > 0
                    else 0
                )
            else:
                err = self._kernel32.GetLastError()
                logger.debug(f"DeviceIoControl GEOMETRY_EX завершился ошибкой: {err}")

        return info

    def read_sectors(
        self,
        disk_id: int,
        start_lba: int,
        sector_count: int,
        sector_size: int = 512,
    ) -> bytes:
        """Прямое посекторное чтение из блочного устройства."""
        total_bytes = sector_count * sector_size
        if not self.is_win32 or not self._kernel32:
            # Fallback генерация фиктивных данных сектора для тестов/симуляции
            pattern = f"PhysicalDrive{disk_id}_LBA_{start_lba}_TO_{start_lba + sector_count}".encode('utf-8')
            return (pattern * ((total_bytes // len(pattern)) + 1))[:total_bytes]

        with self.open_disk(disk_id, write_access=False) as handle:
            if not handle:
                raise OSError(f"Не удалось открыть PhysicalDrive{disk_id} для чтения")

            byte_offset = start_lba * sector_size
            offset_large = wintypes.LARGE_INTEGER(byte_offset)
            new_pos = wintypes.LARGE_INTEGER(0)

            seek_ok = self._kernel32.SetFilePointerEx(
                handle,
                offset_large,
                ctypes.byref(new_pos),
                0,  # FILE_BEGIN
            )
            if not seek_ok:
                err = self._kernel32.GetLastError()
                raise OSError(f"Ошибка позиционирования на LBA {start_lba} (смещение {byte_offset}): код {err}")

            buf = ctypes.create_string_buffer(total_bytes)
            bytes_read = wintypes.DWORD(0)

            read_ok = self._kernel32.ReadFile(
                handle,
                buf,
                total_bytes,
                ctypes.byref(bytes_read),
                None,
            )
            if not read_ok:
                err = self._kernel32.GetLastError()
                raise OSError(f"Ошибка прямого чтения {total_bytes} байт на LBA {start_lba}: код {err}")

            return buf.raw[: bytes_read.value]

    def write_sectors(
        self,
        disk_id: int,
        start_lba: int,
        data: bytes,
        sector_size: int = 512,
    ) -> int:
        """Прямая посекторная запись в блочное устройство."""
        if not data:
            return 0

        if not self.is_win32 or not self._kernel32:
            return len(data)

        with self.open_disk(disk_id, write_access=True) as handle:
            if not handle:
                raise OSError(f"Не удалось открыть PhysicalDrive{disk_id} для записи")

            byte_offset = start_lba * sector_size
            offset_large = wintypes.LARGE_INTEGER(byte_offset)
            new_pos = wintypes.LARGE_INTEGER(0)

            seek_ok = self._kernel32.SetFilePointerEx(
                handle,
                offset_large,
                ctypes.byref(new_pos),
                0,
            )
            if not seek_ok:
                err = self._kernel32.GetLastError()
                raise OSError(f"Ошибка позиционирования на LBA {start_lba}: код {err}")

            bytes_to_write = len(data)
            bytes_written = wintypes.DWORD(0)

            write_ok = self._kernel32.WriteFile(
                handle,
                data,
                bytes_to_write,
                ctypes.byref(bytes_written),
                None,
            )
            if not write_ok:
                err = self._kernel32.GetLastError()
                raise OSError(f"Ошибка прямой записи {bytes_to_write} байт на LBA {start_lba}: код {err}")

            return bytes_written.value

    def inspect_headers(self, disk_id: int) -> DiskHeadersInfo:
        """Инспекция заголовков MBR, GPT и разделов диска."""
        headers = DiskHeadersInfo(disk_id=disk_id)
        try:
            # Сектор 0: MBR (512 байт)
            mbr_raw = self.read_sectors(disk_id, start_lba=0, sector_count=1, sector_size=512)
            if len(mbr_raw) >= 512:
                sig = mbr_raw[510:512]
                if sig == b'\x55\xaa':
                    headers.has_valid_mbr = True
                    headers.mbr_signature = "0x55AA"
                    # Парсинг 4 записей таблицы MBR (смещение 446 / 0x1BE)
                    for i in range(4):
                        offset = 446 + i * 16
                        entry_bytes = mbr_raw[offset : offset + 16]
                        if len(entry_bytes) == 16:
                            status, chs_start, part_type, chs_end, start_lba, sec_count = struct.unpack(
                                '<B3sB3sII', entry_bytes
                            )
                            if part_type != 0 and sec_count > 0:
                                p_entry = PartitionTableEntry(
                                    partition_number=i + 1,
                                    partition_style='MBR',
                                    starting_offset=start_lba * 512,
                                    partition_length=sec_count * 512,
                                    start_lba=start_lba,
                                    end_lba=start_lba + sec_count - 1,
                                    partition_type=f"0x{part_type:02X}",
                                    is_bootable=(status == 0x80),
                                )
                                headers.partitions.append(p_entry)

            # Сектор 1: GPT Header (LBA 1, 512 байт)
            gpt_raw = self.read_sectors(disk_id, start_lba=1, sector_count=1, sector_size=512)
            if len(gpt_raw) >= 92 and gpt_raw[:8] == b'EFI PART':
                headers.has_valid_gpt = True
                headers.gpt_header_lba = 1
                guid_bytes = gpt_raw[56:72]
                if len(guid_bytes) == 16:
                    headers.gpt_guid = str(uuid.UUID(bytes_le=guid_bytes))

                # GPT Partition Array: LBA партиций (обычно LBA 2)
                part_entry_lba, num_parts, part_entry_size = struct.unpack('<QII', gpt_raw[72:88])
                if num_parts > 0 and 0 < part_entry_size <= 512:
                    # Читаем массив записей (первые 8 разделов для скорости инспекции)
                    sectors_to_read = max(1, (min(num_parts, 32) * part_entry_size + 511) // 512)
                    part_array_raw = self.read_sectors(
                        disk_id,
                        start_lba=part_entry_lba,
                        sector_count=sectors_to_read,
                        sector_size=512,
                    )

                    # Сбрасываем MBR разделы если найден полноценный GPT
                    headers.partitions = []
                    for idx in range(min(num_parts, 32)):
                        p_off = idx * part_entry_size
                        p_buf = part_array_raw[p_off : p_off + part_entry_size]
                        if len(p_buf) >= 128:
                            type_guid_bytes = p_buf[0:16]
                            if type_guid_bytes != b'\x00' * 16:
                                type_guid = str(uuid.UUID(bytes_le=type_guid_bytes)).upper()
                                unique_guid = str(uuid.UUID(bytes_le=p_buf[16:32])).upper()
                                s_lba, e_lba, flags = struct.unpack('<QQQ', p_buf[32:56])
                                name = p_buf[56:128].decode('utf-16le', errors='ignore').rstrip('\x00')

                                type_label = "Basic Data (NTFS/FAT)"
                                if type_guid == GPT_SYSTEM_PARTITION_GUID:
                                    type_label = "EFI System Partition (ESP)"
                                elif type_guid == GPT_MS_RECOVERY_GUID:
                                    type_label = "Windows Recovery"
                                elif type_guid == GPT_MS_RESERVED_GUID:
                                    type_label = "Microsoft Reserved (MSR)"

                                headers.partitions.append(
                                    PartitionTableEntry(
                                        partition_number=idx + 1,
                                        partition_style='GPT',
                                        starting_offset=s_lba * 512,
                                        partition_length=(e_lba - s_lba + 1) * 512,
                                        start_lba=s_lba,
                                        end_lba=e_lba,
                                        partition_type=f"{type_label} ({name})" if name else type_label,
                                        partition_id_guid=unique_guid,
                                        is_bootable=(type_guid == GPT_SYSTEM_PARTITION_GUID),
                                    )
                                )

            headers.partition_count = len(headers.partitions)
        except Exception as exc:
            logger.debug(f"Ошибка инспекции заголовков PhysicalDrive{disk_id}: {exc}")

        return headers

    def compute_hash(
        self,
        disk_id: int,
        start_lba: int = 0,
        sector_count: Optional[int] = None,
        algorithm: str = 'sha256',
        chunk_sectors: int = 2048,
        sector_size: int = 512,
    ) -> Tuple[str, int]:
        """Потоковое вычисление хеша диапазона секторов диска."""
        geom = self.get_geometry(disk_id)
        max_sectors = geom.total_sectors if geom.total_sectors > 0 else 1024 * 1024
        count = sector_count if sector_count is not None else (max_sectors - start_lba)
        count = max(1, count)

        h = hashlib.new(algorithm)
        curr_lba = start_lba
        remaining = count
        bytes_hashed = 0

        while remaining > 0:
            batch = min(remaining, chunk_sectors)
            data = self.read_sectors(disk_id, curr_lba, batch, sector_size)
            if not data:
                break
            h.update(data)
            bytes_hashed += len(data)
            curr_lba += batch
            remaining -= batch

        return h.hexdigest(), bytes_hashed


__all__ = ['WindowsRawDiskIO']
