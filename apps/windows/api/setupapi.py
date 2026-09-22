# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: SetupAPI & Configuration Manager Wrapper (setupapi.dll / cfgmgr32.dll)
# =============================================================================
# Description:
#   Direct low-level Ctypes wrapper for SetupAPI and Configuration Manager (PnP).
#   Enumerates hardware devices, checks device status flags (DN_HAS_PROBLEM),
#   and retrieves PnP problem codes (Code 10, 43, 28) natively without PowerShell.
#
# Examples:
#   >>> from apps.windows.api.setupapi import SetupAPI
#   >>> pnp = SetupAPI()
#   >>> problem_devs = pnp.get_problem_devices()
#
# File: setupapi.py
# Project: AI-Breadboard
# Package: apps.windows.api
# Class: SetupAPI
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Низкоуровневый интерфейс к SetupAPI и Configuration Manager PnP."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from logger import logger

# SetupAPI константы
DIGCF_DEFAULT = 0x00000001
DIGCF_PRESENT = 0x00000002
DIGCF_ALLCLASSES = 0x00000004
DIGCF_PROFILE = 0x00000008
DIGCF_DEVICEINTERFACE = 0x00000010

SPDRP_DEVICEDESC = 0x00000000
SPDRP_HARDWAREID = 0x00000001
SPDRP_CLASS = 0x00000007
SPDRP_CLASSGUID = 0x00000008
SPDRP_DRIVER = 0x00000009
SPDRP_FRIENDLYNAME = 0x0000000C
SPDRP_LOCATION_INFORMATION = 0x0000000D
SPDRP_MFG = 0x0000000B

# Configuration Manager флаги статуса
DN_ROOT_ENUMERATED = 0x00000001
DN_DRIVER_LOADED = 0x00000002
DN_ENUM_LOADED = 0x00000004
DN_STARTED = 0x00000008
DN_MANUAL = 0x00000010
DN_NEED_TO_ENUM = 0x00000020
DN_NOT_FIRST_TIME = 0x00000040
DN_HARDWARE_ENUM = 0x00000080
DN_LIBCONFIG = 0x00000100
DN_FILTERED = 0x00000200
DN_MOVED = 0x00000400
DN_DISABLEABLE = 0x00000800
DN_REMOVABLE = 0x00001000
DN_HAS_PROBLEM = 0x00000400  # Флаг наличия проблемы
DN_PRIVATE_PROBLEM = 0x00008000

CR_SUCCESS = 0x00000000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class GUID(ctypes.Structure):
    """Структура Windows GUID."""
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


class SP_DEVINFO_DATA(ctypes.Structure):
    """Структура информации об устройстве SetupAPI."""
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("ClassGuid", GUID),
        ("DevInst", wintypes.DWORD),
        ("Reserved", ctypes.c_void_p),
    ]


@dataclass
class PnPDeviceInfo:
    """Нормализованные данные об аппаратном устройстве PnP."""
    device_instance_id: str
    friendly_name: str
    hardware_id: str
    device_class: str
    manufacturer: str
    has_problem: bool
    status_code: int
    problem_code: int

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "device_instance_id": self.device_instance_id,
            "friendly_name": self.friendly_name,
            "hardware_id": self.hardware_id,
            "device_class": self.device_class,
            "manufacturer": self.manufacturer,
            "has_problem": self.has_problem,
            "status_code": self.status_code,
            "problem_code": self.problem_code,
        }


class SetupAPI:
    """Низкоуровневый клиент к SetupAPI и CfgMgr32."""

    def __init__(self) -> None:
        """Инициализация библиотек setupapi.dll и cfgmgr32.dll."""
        self._setupapi = ctypes.windll.setupapi
        self._cfgmgr32 = ctypes.windll.cfgmgr32

        self._SetupDiGetClassDevsW = self._setupapi.SetupDiGetClassDevsW
        self._SetupDiGetClassDevsW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD]
        self._SetupDiGetClassDevsW.restype = ctypes.c_void_p

        self._SetupDiEnumDeviceInfo = self._setupapi.SetupDiEnumDeviceInfo
        self._SetupDiEnumDeviceInfo.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(SP_DEVINFO_DATA)]
        self._SetupDiEnumDeviceInfo.restype = wintypes.BOOL

        self._SetupDiGetDeviceRegistryPropertyW = self._setupapi.SetupDiGetDeviceRegistryPropertyW
        self._SetupDiGetDeviceRegistryPropertyW.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(SP_DEVINFO_DATA),
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPBYTE,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._SetupDiGetDeviceRegistryPropertyW.restype = wintypes.BOOL

        self._SetupDiDestroyDeviceInfoList = self._setupapi.SetupDiDestroyDeviceInfoList
        self._SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]
        self._SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

        self._CM_Get_DevNode_Status = self._cfgmgr32.CM_Get_DevNode_Status
        self._CM_Get_DevNode_Status.argtypes = [
            ctypes.POINTER(wintypes.ULONG),
            ctypes.POINTER(wintypes.ULONG),
            wintypes.DWORD,
            wintypes.ULONG,
        ]
        self._CM_Get_DevNode_Status.restype = wintypes.DWORD

        self._CM_Get_Device_IDW = self._cfgmgr32.CM_Get_Device_IDW
        self._CM_Get_Device_IDW.argtypes = [
            wintypes.DWORD,
            wintypes.LPWSTR,
            wintypes.ULONG,
            wintypes.ULONG,
        ]
        self._CM_Get_Device_IDW.restype = wintypes.DWORD

    def _get_property_string(self, h_dev_info: ctypes.c_void_p, dev_data: SP_DEVINFO_DATA, prop: int) -> str:
        """Получение строкового свойства устройства из реестра SetupAPI."""
        reg_type = wintypes.DWORD(0)
        req_size = wintypes.DWORD(0)

        self._SetupDiGetDeviceRegistryPropertyW(
            h_dev_info,
            ctypes.byref(dev_data),
            prop,
            ctypes.byref(reg_type),
            None,
            0,
            ctypes.byref(req_size),
        )

        if req_size.value == 0:
            return ""

        buf = (ctypes.c_byte * req_size.value)()
        if not self._SetupDiGetDeviceRegistryPropertyW(
            h_dev_info,
            ctypes.byref(dev_data),
            prop,
            ctypes.byref(reg_type),
            ctypes.cast(buf, wintypes.LPBYTE),
            req_size.value,
            ctypes.byref(req_size),
        ):
            return ""

        try:
            return ctypes.wstring_at(buf)
        except Exception:
            return ""

    def get_all_devices(self, only_present: bool = True) -> List[PnPDeviceInfo]:
        """Получение списка всех устройств PnP с их статусом и кодами проблем.

        Args:
            only_present: Фильтровать только подключенные устройства.

        Returns:
            List[PnPDeviceInfo]: Список PnP устройств.
        """
        flags = DIGCF_ALLCLASSES
        if only_present:
            flags |= DIGCF_PRESENT

        h_dev_info = self._SetupDiGetClassDevsW(None, None, None, flags)
        if not h_dev_info or h_dev_info == INVALID_HANDLE_VALUE:
            logger.debug("Не удалось получить дескриптор SetupDiGetClassDevsW")
            return []

        devices: List[PnPDeviceInfo] = []
        try:
            dev_data = SP_DEVINFO_DATA()
            dev_data.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)
            idx = 0

            while self._SetupDiEnumDeviceInfo(h_dev_info, idx, ctypes.byref(dev_data)):
                idx += 1
                try:
                    friendly_name = self._get_property_string(h_dev_info, dev_data, SPDRP_FRIENDLYNAME)
                    if not friendly_name:
                        friendly_name = self._get_property_string(h_dev_info, dev_data, SPDRP_DEVICEDESC)

                    hw_id = self._get_property_string(h_dev_info, dev_data, SPDRP_HARDWAREID)
                    cls_name = self._get_property_string(h_dev_info, dev_data, SPDRP_CLASS)
                    mfg = self._get_property_string(h_dev_info, dev_data, SPDRP_MFG)

                    # Получение ID инстанса устройства
                    id_buf = (ctypes.c_wchar * 512)()
                    cm_res = self._CM_Get_Device_IDW(dev_data.DevInst, id_buf, 512, 0)
                    device_instance_id = id_buf.value if cm_res == CR_SUCCESS else ""

                    # Опрос статуса узла через CfgMgr32
                    status = wintypes.ULONG(0)
                    prob_code = wintypes.ULONG(0)
                    cm_status = self._CM_Get_DevNode_Status(ctypes.byref(status), ctypes.byref(prob_code), dev_data.DevInst, 0)

                    has_problem = False
                    problem_num = 0
                    if cm_status == CR_SUCCESS:
                        problem_num = prob_code.value
                        has_problem = (status.value & DN_HAS_PROBLEM) != 0 or problem_num != 0

                    devices.append(
                        PnPDeviceInfo(
                            device_instance_id=device_instance_id,
                            friendly_name=friendly_name or device_instance_id or "Устройство без имени",
                            hardware_id=hw_id,
                            device_class=cls_name,
                            manufacturer=mfg,
                            has_problem=has_problem,
                            status_code=status.value if cm_status == CR_SUCCESS else 0,
                            problem_code=problem_num,
                        )
                    )
                except Exception:
                    continue
        finally:
            self._SetupDiDestroyDeviceInfoList(h_dev_info)

        return devices

    def get_problem_devices(self) -> List[PnPDeviceInfo]:
        """Быстрый поиск только устройств с аппаратными сбоями (Code 10/43/28).

        Returns:
            List[PnPDeviceInfo]: Список проблемных устройств.
        """
        all_devs = self.get_all_devices(only_present=True)
        return [d for d in all_devs if d.has_problem and d.problem_code > 0]
