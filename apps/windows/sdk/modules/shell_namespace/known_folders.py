# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows SDK Modules Shell - Known Folders
# =============================================================================
# Description:
#   Инвентаризация и разрешение Known Folders Windows через Win32 API и реестр.
#   Модуль использует функции SHGetKnownFolderPath / ctypes с освобождением памяти
#   через CoTaskMemFree, а также резервный поиск в реестре User Shell Folders.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.shell_namespace.known_folders import KnownFoldersManager
#
#     manager = KnownFoldersManager()
#     folders = manager.list_known_folders()
#
# File: known_folders.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.shell_namespace
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 06:15:00
# =============================================================================

from __future__ import annotations
"""Инвентаризация и разрешение Known Folders Windows через Win32 API и реестр."""

import ctypes
from ctypes import wintypes
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import winreg

logger = logging.getLogger(__name__)


class GUID(ctypes.Structure):
    """Структура GUID для ctypes."""
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_string(cls, guid_str: str) -> "GUID":
        clean = guid_str.strip("{}")
        parts = clean.split("-")
        data1 = int(parts[0], 16)
        data2 = int(parts[1], 16)
        data3 = int(parts[2], 16)
        d4 = [int(parts[3][:2], 16), int(parts[3][2:], 16)]
        for i in range(0, 12, 2):
            d4.append(int(parts[4][i:i+2], 16))

        g = cls()
        g.Data1 = data1
        g.Data2 = data2
        g.Data3 = data3
        for i, b in enumerate(d4):
            g.Data4[i] = b
        return g


KNOWN_FOLDERS_CATALOG: Dict[str, Dict[str, Any]] = {
    'Desktop': {
        'id': '{B4BF2709-9732-45C2-9C14-92F2D5122BA7}',
        'category': 'peruser',
        'reg_key': 'Desktop',
    },
    'Documents': {
        'id': '{FDD39FA0-2371-497B-A841-10294FD740B0}',
        'category': 'peruser',
        'reg_key': 'Personal',
    },
    'Downloads': {
        'id': '{374DE290-123F-4565-9164-39C4925E467B}',
        'category': 'peruser',
        'reg_key': '{374DE290-123F-4565-9164-39C4925E467B}',
    },
    'Music': {
        'id': '{4BD8D571-6D19-48D3-BE97-422220080E43}',
        'category': 'peruser',
        'reg_key': 'My Music',
    },
    'Pictures': {
        'id': '{33E28610-88C3-4E80-9958-B260E365B043}',
        'category': 'peruser',
        'reg_key': 'My Pictures',
    },
    'Videos': {
        'id': '{18926901-2100-429B-A042-2A41F1A72A28}',
        'category': 'peruser',
        'reg_key': 'My Video',
    },
    'ProgramFiles': {
        'id': '{90570670-BFA2-4EAE-BA44-1E6336A40064}',
        'category': 'fixed',
        'reg_key': 'ProgramFilesDir',
    },
    'System': {
        'id': '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}',
        'category': 'fixed',
        'reg_key': None,
    },
    'Windows': {
        'id': '{F38BF404-1D43-42F2-9305-67DE0B28FC23}',
        'category': 'fixed',
        'reg_key': None,
    },
}


def get_known_folder_path_win32(folder_guid_str: str) -> Optional[str]:
    """Получить физический путь Known Folder через SHGetKnownFolderPath (Win32 API).

    Args:
        folder_guid_str: GUID папки (например '{FDD39FA0-2371-497B-A841-10294FD740B0}').

    Returns:
        str | None: Абсолютный путь к папке или None при неудаче.
    """
    try:
        shell32 = ctypes.windll.shell32
        ole32 = ctypes.windll.ole32

        guid = GUID.from_string(folder_guid_str)
        p_path = ctypes.c_wchar_p()

        res = shell32.SHGetKnownFolderPath(
            ctypes.byref(guid),
            0,
            None,
            ctypes.byref(p_path),
        )

        if res == 0 and p_path.value:
            path_val = p_path.value
            ole32.CoTaskMemFree(p_path)
            return path_val
    except Exception as err:
        logger.debug("SHGetKnownFolderPath не удалось разрешить %s: %s", folder_guid_str, err)

    return None


def get_known_folder_path_registry(reg_key: Optional[str]) -> Optional[str]:
    """Резервное получение пути папки пользователя из реестра User Shell Folders.

    Args:
        reg_key: Имя ключа в реестре User Shell Folders.

    Returns:
        str | None: Развернутый физический путь.
    """
    if not reg_key:
        return None

    try:
        reg_path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            reg_path,
            0,
            winreg.KEY_READ,
        ) as key:
            val, _ = winreg.QueryValueEx(key, reg_key)
            if val:
                return os.path.expandvars(str(val))
    except FileNotFoundError:
        pass
    except Exception as err:
        logger.debug("Ошибка чтения реестра User Shell Folders для %s: %s", reg_key, err)

    return None


def list_known_folders() -> List[Dict[str, Any]]:
    """Инвентаризация всех основных Known Folders системы.

    Returns:
        list[dict]: Данные по каждой известной папке (имя, GUID, категория, путь, существование).
    """
    folders: List[Dict[str, Any]] = []

    for name, meta in KNOWN_FOLDERS_CATALOG.items():
        guid_str = meta['id']
        path = get_known_folder_path_win32(guid_str)
        source = 'Win32_SHGetKnownFolderPath'

        if not path and meta.get('reg_key'):
            path = get_known_folder_path_registry(meta['reg_key'])
            source = 'Registry_UserShellFolders'

        exists = bool(path and Path(path).exists())

        folders.append({
            'canonical_name': name,
            'guid': guid_str,
            'category': meta['category'],
            'path': path,
            'exists': exists,
            'source': source if path else 'none',
        })

    return folders


class KnownFoldersManager:
    """Менеджер Known Folders Windows."""

    def list_known_folders(self) -> List[Dict[str, Any]]:
        return list_known_folders()

    def get_path_by_guid(self, guid_str: str) -> Optional[str]:
        return get_known_folder_path_win32(guid_str)


__all__ = [
    'KnownFoldersManager',
    'list_known_folders',
    'get_known_folder_path_win32',
    'get_known_folder_path_registry',
    'KNOWN_FOLDERS_CATALOG',
    'GUID',
]
