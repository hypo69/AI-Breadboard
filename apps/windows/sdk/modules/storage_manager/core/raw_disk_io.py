# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Core - Raw Disk Io
# =============================================================================
# Description:
#   Прямой Win32 / IOCTL ввод-вывод для физических накопителей и томов Windows.
#   Включает опрос StorageDeviceProperty, NVMe SMART Health, разметку GPT/MBR и Win32 Volume API.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.storage_manager.core.raw_disk_io import WindowsRawDiskIO
#
#     raw_io = WindowsRawDiskIO()
#     prop = raw_io.query_storage_device_property(0)
#     health = raw_io.query_nvme_smart_health(0)
#     vols = raw_io.get_logical_volumes()
#
# File: raw_disk_io.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 01:33:00
# =============================================================================

from __future__ import annotations
"""Прямой Win32 / IOCTL ввод-вывод для физических накопителей и томов Windows."""

import ctypes
import ctypes.wintypes as wintypes
import hashlib
import struct
import sys
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple

from logger import logger
from apps.windows.sdk.modules.storage_manager.core.models import (
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
IOCTL_STORAGE_PROTOCOL_COMMAND = 0x002D1480
FSCTL_LOCK_VOLUME = 0x00090018
FSCTL_UNLOCK_VOLUME = 0x0009001C
FSCTL_DISMOUNT_VOLUME = 0x00090020

# GPT GUID типов разделов
GPT_SYSTEM_PARTITION_GUID = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"
GPT_MS_BASIC_DATA_GUID = "EBD0A0A2-B9E5-4433-87C0-68B6B72699C7"
GPT_MS_RESERVED_GUID = "E3C9E310-0B5E-4962-833B-F9A41F14E882"
GPT_MS_RECOVERY_GUID = "DE94BBA4-06D1-4D40-A16A-BFD50179D6AC"

# Карта типов шин Windows Storage
BUS_TYPE_MAP: Dict[int, str] = {
    0: 'Unknown',
    1: 'SCSI',
    2: 'ATAPI',
    3: 'ATA',
    4: '1394',
    5: 'SSA',
    6: 'Fibre Channel',
    7: 'USB',
    8: 'RAID',
    9: 'iSCSI',
    10: 'SAS',
    11: 'SATA',
    12: 'SD',
    13: 'MMC',
    14: 'MAX',
    15: 'File Backed Virtual',
    16: 'Storage Spaces',
    17: 'NVMe',
    18: 'SCM',
    19: 'UFS',
}


class DISK_GEOMETRY(ctypes.Structure):
    """Структура базовой геометрии диска."""
    _fields_ = [
        ('Cylinders', wintypes.LARGE_INTEGER),
        ('MediaType', wintypes.DWORD),
        ('TracksPerCylinder', wintypes.DWORD),
        ('SectorsPerTrack', wintypes.DWORD),
        ('BytesPerSector', wintypes.DWORD),
    ]


class DISK_GEOMETRY_EX(ctypes.Structure):
    """Структура расширенной геометрии диска с полным размером."""
    _fields_ = [
        ('Geometry', DISK_GEOMETRY),
        ('DiskSize', wintypes.LARGE_INTEGER),
        ('Data', ctypes.c_byte * 1),
    ]


class STORAGE_PROPERTY_QUERY(ctypes.Structure):
    """Структура запроса свойств хранилища StorageDeviceProperty."""
    _fields_ = [
        ('PropertyId', wintypes.DWORD),
        ('QueryType', wintypes.DWORD),
        ('AdditionalParameters', ctypes.c_byte * 1),
    ]


class STORAGE_DEVICE_DESCRIPTOR_HEADER(ctypes.Structure):
    """Фиксированный заголовок дескриптора устройства хранения."""
    _fields_ = [
        ('Version', wintypes.DWORD),
        ('Size', wintypes.DWORD),
        ('DeviceType', ctypes.c_ubyte),
        ('DeviceTypeModifier', ctypes.c_ubyte),
        ('RemovableMedia', ctypes.c_ubyte),
        ('CommandQueueing', ctypes.c_ubyte),
        ('VendorIdOffset', wintypes.DWORD),
        ('ProductIdOffset', wintypes.DWORD),
        ('ProductRevisionOffset', wintypes.DWORD),
        ('SerialNumberOffset', wintypes.DWORD),
        ('BusType', wintypes.DWORD),
        ('RawPropertiesLength', wintypes.DWORD),
    ]


class STORAGE_PROTOCOL_SPECIFIC_DATA(ctypes.Structure):
    """Запрос протокольных данных накопителя (NVMe Log Page)."""
    _fields_ = [
        ('ProtocolType', wintypes.DWORD),             # 1 = ProtocolTypeNvme
        ('DataType', wintypes.DWORD),                 # 2 = NVMeDataTypeLogPage
        ('ProtocolDataRequestValue', wintypes.DWORD), # 0x02 = NVME_LOG_PAGE_HEALTH_INFO
        ('ProtocolDataRequestSubValue', wintypes.DWORD),
        ('ProtocolDataOffset', wintypes.DWORD),
        ('ProtocolDataLength', wintypes.DWORD),
        ('FixedProtocolReturnData', wintypes.DWORD),
        ('Reserved', wintypes.DWORD * 3),
    ]


class WindowsRawDiskIO:
    """Управление прямым блочным вводом-выводом и Win32/IOCTL для накопителей Windows."""

    def __init__(self) -> None:
        """Инициализация WinAPI привязок."""
        self.is_win32 = sys.platform == 'win32'
        if self.is_win32:
            self._kernel32 = ctypes.windll.kernel32
            self._setup_win32_signatures()
        else:
            self._kernel32 = None

    def _setup_win32_signatures(self) -> None:
        """Настройка типов сигнатур ctypes для kernel32."""
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
            yield None
            return

        try:
            yield handle
        finally:
            self._kernel32.CloseHandle(handle)

    def query_storage_device_property(self, disk_id: int) -> Dict[str, Any]:
        """Запрос основных характеристик диска через IOCTL_STORAGE_QUERY_PROPERTY.

        Извлекает: Vendor, Product, Revision, SerialNumber, BusType, RemovableMedia.
        """
        result: Dict[str, Any] = {
            'vendor': '',
            'product': f'PhysicalDrive{disk_id}',
            'revision': '',
            'serial_number': '',
            'bus_type': 'Unknown',
            'removable': False,
            'command_queueing': False,
            'device_type': 0,
        }
        if not self.is_win32 or not self._kernel32:
            return result

        with self.open_disk(disk_id, write_access=False) as handle:
            if not handle:
                return result

            query = STORAGE_PROPERTY_QUERY()
            query.PropertyId = 0  # StorageDeviceProperty
            query.QueryType = 0   # PropertyStandardQuery

            desc_buf = (ctypes.c_ubyte * 4096)()
            bytes_returned = wintypes.DWORD(0)

            ok = self._kernel32.DeviceIoControl(
                handle,
                IOCTL_STORAGE_QUERY_PROPERTY,
                ctypes.byref(query),
                ctypes.sizeof(query),
                ctypes.byref(desc_buf),
                len(desc_buf),
                ctypes.byref(bytes_returned),
                None,
            )
            if ok and bytes_returned.value >= ctypes.sizeof(STORAGE_DEVICE_DESCRIPTOR_HEADER):
                raw_bytes = bytes(desc_buf[:bytes_returned.value])
                desc = STORAGE_DEVICE_DESCRIPTOR_HEADER.from_buffer_copy(raw_bytes[:ctypes.sizeof(STORAGE_DEVICE_DESCRIPTOR_HEADER)])
                result['bus_type'] = BUS_TYPE_MAP.get(desc.BusType, f'Unknown({desc.BusType})')
                result['removable'] = bool(desc.RemovableMedia)
                result['command_queueing'] = bool(desc.CommandQueueing)
                result['device_type'] = int(desc.DeviceType)

                def _extract_sz(offset: int) -> str:
                    if offset > 0 and offset < len(raw_bytes):
                        end = raw_bytes.find(b'\x00', offset)
                        if end == -1:
                            end = len(raw_bytes)
                        try:
                            return raw_bytes[offset:end].decode('ascii', errors='ignore').strip()
                        except Exception:
                            return ''
                    return ''

                result['vendor'] = _extract_sz(desc.VendorIdOffset)
                result['product'] = _extract_sz(desc.ProductIdOffset) or result['product']
                result['revision'] = _extract_sz(desc.ProductRevisionOffset)
                result['serial_number'] = _extract_sz(desc.SerialNumberOffset)

        return result

    def query_nvme_smart_health(self, disk_id: int) -> Dict[str, Any]:
        """Запрос NVMe SMART / Health данных через Storage Protocol Command.

        Извлекает: Temperature, Percentage Used (износ), Available Spare, TBW (Read/Write),
        Power On Hours, Power Cycles, Unsafe Shutdowns, Media Errors.
        """
        result: Dict[str, Any] = {
            'temperature_c': None,
            'percentage_used': None,
            'available_spare_percent': None,
            'available_spare_threshold': None,
            'data_units_read_tb': None,
            'data_units_written_tb': None,
            'power_on_hours': None,
            'power_cycles': None,
            'unsafe_shutdowns': None,
            'media_errors': None,
            'error_log_entries': None,
            'critical_warning': None,
            'raw_nvme_available': False,
        }
        if not self.is_win32 or not self._kernel32:
            return result

        with self.open_disk(disk_id, write_access=False) as handle:
            if not handle:
                return result

            # Формируем буфер запроса: STORAGE_PROPERTY_QUERY + STORAGE_PROTOCOL_SPECIFIC_DATA + 512 байт лога
            query_buf_size = ctypes.sizeof(STORAGE_PROPERTY_QUERY) + ctypes.sizeof(STORAGE_PROTOCOL_SPECIFIC_DATA) + 512
            query_buf = (ctypes.c_ubyte * query_buf_size)()

            # PropertyId = 49 (StorageDeviceProtocolSpecificProperty)
            # PropertyId = 50 (StorageAdapterProtocolSpecificProperty)
            for prop_id in (49, 50):
                ctypes.memset(query_buf, 0, query_buf_size)
                # Заполняем STORAGE_PROPERTY_QUERY
                struct.pack_into('<II', query_buf, 0, prop_id, 0)

                # Заполняем STORAGE_PROTOCOL_SPECIFIC_DATA
                proto_offset = ctypes.sizeof(STORAGE_PROPERTY_QUERY)
                proto_header_len = 40
                data_offset = proto_offset + proto_header_len
                struct.pack_into(
                    '<IIIIIIIIII',
                    query_buf,
                    proto_offset,
                    1,     # ProtocolTypeNvme
                    2,     # NVMeDataTypeLogPage
                    0x02,  # NVME_LOG_PAGE_HEALTH_INFO
                    0,     # ProtocolDataRequestSubValue
                    proto_header_len, # ProtocolDataOffset
                    512,   # ProtocolDataLength
                    0, 0, 0, 0
                )

                out_buf = (ctypes.c_ubyte * query_buf_size)()
                bytes_returned = wintypes.DWORD(0)

                ok = self._kernel32.DeviceIoControl(
                    handle,
                    IOCTL_STORAGE_QUERY_PROPERTY,
                    ctypes.byref(query_buf),
                    query_buf_size,
                    ctypes.byref(out_buf),
                    query_buf_size,
                    ctypes.byref(bytes_returned),
                    None,
                )
                if ok and bytes_returned.value >= data_offset + 192:
                    raw_out = bytes(out_buf[:bytes_returned.value])
                    log_data = raw_out[data_offset : data_offset + 512]
                    if len(log_data) >= 192:
                        crit_warn = log_data[0]
                        raw_temp_k = struct.unpack('<H', log_data[1:3])[0]
                        temp_c = round(raw_temp_k - 273.15, 1) if 200 < raw_temp_k < 400 else None
                        avail_spare = log_data[3]
                        avail_spare_thresh = log_data[4]
                        pct_used = log_data[5]

                        data_units_read = int.from_bytes(log_data[32:48], byteorder='little')
                        data_units_written = int.from_bytes(log_data[48:64], byteorder='little')
                        read_tb = round((data_units_read * 1000 * 512) / (10 ** 12), 2)
                        written_tb = round((data_units_written * 1000 * 512) / (10 ** 12), 2)

                        power_cycles = int.from_bytes(log_data[112:128], byteorder='little')
                        power_on_hours = int.from_bytes(log_data[128:144], byteorder='little')
                        unsafe_shutdowns = int.from_bytes(log_data[144:160], byteorder='little')
                        media_errors = int.from_bytes(log_data[160:176], byteorder='little')
                        error_log_entries = int.from_bytes(log_data[176:192], byteorder='little')

                        result.update({
                            'temperature_c': temp_c,
                            'percentage_used': float(pct_used),
                            'available_spare_percent': float(avail_spare),
                            'available_spare_threshold': float(avail_spare_thresh),
                            'data_units_read_tb': read_tb,
                            'data_units_written_tb': written_tb,
                            'power_on_hours': power_on_hours,
                            'power_cycles': power_cycles,
                            'unsafe_shutdowns': unsafe_shutdowns,
                            'media_errors': media_errors,
                            'error_log_entries': error_log_entries,
                            'critical_warning': crit_warn,
                            'raw_nvme_available': True,
                        })
                        return result

        return result

    def get_geometry(self, disk_id: int) -> DiskGeometryInfo:
        """Получение геометрии и точного размера диска через IOCTL_DISK_GET_DRIVE_GEOMETRY_EX."""
        info = DiskGeometryInfo(bytes_per_sector=512)
        if not self.is_win32 or not self._kernel32:
            info.disk_size_bytes = 512 * 1024 * 1024 * 1024
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
                raise OSError(f"Ошибка позиционирования на LBA {start_lba}: код {err}")

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
        """Инспекция заголовков MBR, GPT и таблицы разделов диска."""
        headers = DiskHeadersInfo(disk_id=disk_id)
        try:
            # Сектор 0: MBR (512 байт)
            mbr_raw = self.read_sectors(disk_id, start_lba=0, sector_count=1, sector_size=512)
            if len(mbr_raw) >= 512:
                sig = mbr_raw[510:512]
                if sig == b'\x55\xaa':
                    headers.has_valid_mbr = True
                    headers.mbr_signature = "0x55AA"
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

                part_entry_lba, num_parts, part_entry_size = struct.unpack('<QII', gpt_raw[72:88])
                if num_parts > 0 and 0 < part_entry_size <= 512:
                    sectors_to_read = max(1, (min(num_parts, 32) * part_entry_size + 511) // 512)
                    part_array_raw = self.read_sectors(
                        disk_id,
                        start_lba=part_entry_lba,
                        sector_count=sectors_to_read,
                        sector_size=512,
                    )
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

    def get_logical_volumes(self) -> List[Dict[str, Any]]:
        """Извлечение информации о логических дисках через нативные Win32 Volume APIs.

        Использует GetLogicalDriveStringsW, GetDriveTypeW, GetVolumeInformationW,
        GetDiskFreeSpaceExW, GetDiskFreeSpaceW и GetVolumeNameForVolumeMountPointW.
        """
        results: List[Dict[str, Any]] = []
        if not self.is_win32 or not self._kernel32:
            return results

        try:
            buf_len = 512
            buf = ctypes.create_unicode_buffer(buf_len)
            ret_len = self._kernel32.GetLogicalDriveStringsW(buf_len, buf)
            if ret_len == 0:
                return results

            raw_str = ctypes.wstring_at(ctypes.addressof(buf), ret_len)
            drives = [p for p in raw_str.split('\x00') if p]

            drive_type_map = {
                0: 'Unknown',
                1: 'NoRootDir',
                2: 'Removable',
                3: 'Fixed',
                4: 'Remote',
                5: 'CDROM',
                6: 'RAMDisk',
            }

            for drive in drives:
                drive_type_code = self._kernel32.GetDriveTypeW(drive)
                drive_type_str = drive_type_map.get(drive_type_code, 'Unknown')

                vol_name_buf = ctypes.create_unicode_buffer(260)
                fs_name_buf = ctypes.create_unicode_buffer(260)
                serial_num = wintypes.DWORD(0)
                max_comp_len = wintypes.DWORD(0)
                fs_flags = wintypes.DWORD(0)

                ok_vol = self._kernel32.GetVolumeInformationW(
                    drive,
                    vol_name_buf,
                    260,
                    ctypes.byref(serial_num),
                    ctypes.byref(max_comp_len),
                    ctypes.byref(fs_flags),
                    fs_name_buf,
                    260,
                )

                label = vol_name_buf.value if ok_vol else ''
                filesystem = fs_name_buf.value if ok_vol else 'NTFS'
                flags_val = fs_flags.value if ok_vol else 0

                free_bytes_avail = wintypes.ULARGE_INTEGER(0)
                total_bytes = wintypes.ULARGE_INTEGER(0)
                total_free_bytes = wintypes.ULARGE_INTEGER(0)

                ok_free = self._kernel32.GetDiskFreeSpaceExW(
                    drive,
                    ctypes.byref(free_bytes_avail),
                    ctypes.byref(total_bytes),
                    ctypes.byref(total_free_bytes),
                )

                tot_b = total_bytes.value if ok_free else 0
                free_b = total_free_bytes.value if ok_free else 0
                avail_b = free_bytes_avail.value if ok_free else 0

                # Опрос размера кластера
                spc = wintypes.DWORD(0)
                bps = wintypes.DWORD(0)
                nofc = wintypes.DWORD(0)
                tnoc = wintypes.DWORD(0)
                ok_cluster = self._kernel32.GetDiskFreeSpaceW(
                    drive,
                    ctypes.byref(spc),
                    ctypes.byref(bps),
                    ctypes.byref(nofc),
                    ctypes.byref(tnoc),
                )
                cluster_size = (spc.value * bps.value) if ok_cluster else 4096

                # Volume GUID
                guid_buf = ctypes.create_unicode_buffer(260)
                ok_guid = self._kernel32.GetVolumeNameForVolumeMountPointW(drive, guid_buf, 260)
                volume_guid = guid_buf.value if ok_guid else ''

                percent_used = round(((tot_b - free_b) / tot_b) * 100.0, 1) if tot_b > 0 else 0.0

                results.append({
                    'drive_letter': drive.rstrip('\\'),
                    'mount_point': drive,
                    'volume_guid': volume_guid,
                    'label': label,
                    'filesystem': filesystem,
                    'filesystem_flags': flags_val,
                    'drive_type': drive_type_str,
                    'drive_type_code': drive_type_code,
                    'total_bytes': tot_b,
                    'free_bytes': free_b,
                    'available_bytes': avail_b,
                    'total_gb': round(tot_b / (1024 ** 3), 2),
                    'free_gb': round(free_b / (1024 ** 3), 2),
                    'percent_used': percent_used,
                    'cluster_size_bytes': cluster_size,
                    'sector_size_bytes': bps.value if ok_cluster else 512,
                })
        except Exception as exc:
            logger.debug(f"Ошибка получения Win32 логических томов: {exc}")

        return results

    def list_physical_disks(self, max_disks: int = 32) -> List[Dict[str, Any]]:
        """Сканирование и обнаружение всех физических накопителей в системе через Win32 IOCTL.

        Опрашивает геометрию, StorageDeviceProperty и NVMe SMART для каждого доступного диска.
        """
        disks = []
        if not self.is_win32 or not self._kernel32:
            return disks

        for disk_id in range(max_disks):
            geom = self.get_geometry(disk_id)
            if geom.disk_size_bytes > 0:
                prop = self.query_storage_device_property(disk_id)
                smart = self.query_nvme_smart_health(disk_id)
                disks.append({
                    'disk_id': disk_id,
                    'device_path': self.get_disk_device_path(disk_id),
                    'product': prop.get('product') or f'PhysicalDrive{disk_id}',
                    'vendor': prop.get('vendor', ''),
                    'revision': prop.get('revision', ''),
                    'serial_number': prop.get('serial_number', ''),
                    'bus_type': prop.get('bus_type', 'Unknown'),
                    'size_bytes': geom.disk_size_bytes,
                    'size_gb': round(geom.disk_size_bytes / (1024 ** 3), 2),
                    'sector_size': geom.bytes_per_sector,
                    'removable': prop.get('removable', False),
                    'smart_health': smart,
                })
        return disks


__all__ = ['WindowsRawDiskIO']

