"""Низкоуровневый интерфейс к SetupAPI и Configuration Manager PnP."""
from __future__ import annotations
import ctypes
import ctypes.wintypes as wintypes
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from logger import logger
DIGCF_DEFAULT = 1
DIGCF_PRESENT = 2
DIGCF_ALLCLASSES = 4
DIGCF_PROFILE = 8
DIGCF_DEVICEINTERFACE = 16
SPDRP_DEVICEDESC = 0
SPDRP_HARDWAREID = 1
SPDRP_CLASS = 7
SPDRP_CLASSGUID = 8
SPDRP_DRIVER = 9
SPDRP_FRIENDLYNAME = 12
SPDRP_LOCATION_INFORMATION = 13
SPDRP_MFG = 11
DN_ROOT_ENUMERATED = 1
DN_DRIVER_LOADED = 2
DN_ENUM_LOADED = 4
DN_STARTED = 8
DN_MANUAL = 16
DN_NEED_TO_ENUM = 32
DN_NOT_FIRST_TIME = 64
DN_HARDWARE_ENUM = 128
DN_LIBCONFIG = 256
DN_FILTERED = 512
DN_MOVED = 1024
DN_DISABLEABLE = 2048
DN_REMOVABLE = 4096
DN_HAS_PROBLEM = 1024
DN_PRIVATE_PROBLEM = 32768
CR_SUCCESS = 0
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

class GUID(ctypes.Structure):
    """Структура Windows GUID."""
    _fields_ = [('Data1', wintypes.DWORD), ('Data2', wintypes.WORD), ('Data3', wintypes.WORD), ('Data4', wintypes.BYTE * 8)]

class SP_DEVINFO_DATA(ctypes.Structure):
    """Структура информации об устройстве SetupAPI."""
    _fields_ = [('cbSize', wintypes.DWORD), ('ClassGuid', GUID), ('DevInst', wintypes.DWORD), ('Reserved', ctypes.c_void_p)]

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
        return {'device_instance_id': self.device_instance_id, 'friendly_name': self.friendly_name, 'hardware_id': self.hardware_id, 'device_class': self.device_class, 'manufacturer': self.manufacturer, 'has_problem': self.has_problem, 'status_code': self.status_code, 'problem_code': self.problem_code}

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
        self._SetupDiGetDeviceRegistryPropertyW.argtypes = [ctypes.c_void_p, ctypes.POINTER(SP_DEVINFO_DATA), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPBYTE, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        self._SetupDiGetDeviceRegistryPropertyW.restype = wintypes.BOOL
        self._SetupDiDestroyDeviceInfoList = self._setupapi.SetupDiDestroyDeviceInfoList
        self._SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]
        self._SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL
        self._CM_Get_DevNode_Status = self._cfgmgr32.CM_Get_DevNode_Status
        self._CM_Get_DevNode_Status.argtypes = [ctypes.POINTER(wintypes.ULONG), ctypes.POINTER(wintypes.ULONG), wintypes.DWORD, wintypes.ULONG]
        self._CM_Get_DevNode_Status.restype = wintypes.DWORD
        self._CM_Get_Device_IDW = self._cfgmgr32.CM_Get_Device_IDW
        self._CM_Get_Device_IDW.argtypes = [wintypes.DWORD, wintypes.LPWSTR, wintypes.ULONG, wintypes.ULONG]
        self._CM_Get_Device_IDW.restype = wintypes.DWORD

    def _get_property_string(self, h_dev_info: ctypes.c_void_p, dev_data: SP_DEVINFO_DATA, prop: int) -> str:
        """Получение строкового свойства устройства из реестра SetupAPI."""
        reg_type = wintypes.DWORD(0)
        req_size = wintypes.DWORD(0)
        self._SetupDiGetDeviceRegistryPropertyW(h_dev_info, ctypes.byref(dev_data), prop, ctypes.byref(reg_type), None, 0, ctypes.byref(req_size))
        if req_size.value == 0:
            return ''
        buf = (ctypes.c_byte * req_size.value)()
        if not self._SetupDiGetDeviceRegistryPropertyW(h_dev_info, ctypes.byref(dev_data), prop, ctypes.byref(reg_type), ctypes.cast(buf, wintypes.LPBYTE), req_size.value, ctypes.byref(req_size)):
            return ''
        try:
            return ctypes.wstring_at(buf)
        except Exception:
            return ''

    def get_all_devices(self, only_present: bool=True) -> List[PnPDeviceInfo]:
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
            logger.debug('Не удалось получить дескриптор SetupDiGetClassDevsW')
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
                    id_buf = (ctypes.c_wchar * 512)()
                    cm_res = self._CM_Get_Device_IDW(dev_data.DevInst, id_buf, 512, 0)
                    device_instance_id = id_buf.value if cm_res == CR_SUCCESS else ''
                    status = wintypes.ULONG(0)
                    prob_code = wintypes.ULONG(0)
                    cm_status = self._CM_Get_DevNode_Status(ctypes.byref(status), ctypes.byref(prob_code), dev_data.DevInst, 0)
                    has_problem = False
                    problem_num = 0
                    if cm_status == CR_SUCCESS:
                        problem_num = prob_code.value
                        has_problem = status.value & DN_HAS_PROBLEM != 0 or problem_num != 0
                    devices.append(PnPDeviceInfo(device_instance_id=device_instance_id, friendly_name=friendly_name or device_instance_id or 'Устройство без имени', hardware_id=hw_id, device_class=cls_name, manufacturer=mfg, has_problem=has_problem, status_code=status.value if cm_status == CR_SUCCESS else 0, problem_code=problem_num))
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