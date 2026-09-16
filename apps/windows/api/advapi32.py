"""
advapi32.dll wrapper for registry, services, and security functions.

Provides access to:
- Registry operations: RegOpenKeyEx, RegQueryValueEx, RegEnumKeyEx
- Service operations: OpenSCManager, OpenService, EnumServicesStatus
- Security: GetTokenInformation, GetSecurityDescriptorOwner
"""

import ctypes
import ctypes.wintypes as wintypes
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import IntFlag

# Registry constants
HKEY_CLASSES_ROOT = 0x80000000
HKEY_CURRENT_USER = 0x80000001
HKEY_LOCAL_MACHINE = 0x80000002
HKEY_USERS = 0x80000003
HKEY_PERFORMANCE_DATA = 0x80000004
HKEY_CURRENT_CONFIG = 0x80000005

KEY_READ = 0x20019
KEY_WRITE = 0x20006
KEY_QUERY_VALUE = 0x0001
KEY_ENUMERATE_SUB_KEYS = 0x0008

# Service constants
SERVICE_QUERY_STATUS = 0x0004
SERVICE_QUERY_CONFIG = 0x0001
SERVICE_AUTO_START = 0x00000002
SERVICE_DEMAND_START = 0x00000003
SERVICE_DISABLED = 0x00000004

SERVICE_RUNNING = 0x00000004
SERVICE_STOPPED = 0x00000001

# Structure definitions
class SYSTEMTIME(ctypes.Structure):
    _fields_ = [
        ("wYear", wintypes.WORD),
        ("wMonth", wintypes.WORD),
        ("wDayOfWeek", wintypes.WORD),
        ("wDay", wintypes.WORD),
        ("wHour", wintypes.WORD),
        ("wMinute", wintypes.WORD),
        ("wSecond", wintypes.WORD),
        ("wMilliseconds", wintypes.WORD),
    ]


class SERVICE_STATUS(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", wintypes.DWORD),
        ("dwCurrentState", wintypes.DWORD),
        ("dwControlsAccepted", wintypes.DWORD),
        ("dwWin32ExitCode", wintypes.DWORD),
        ("dwServiceSpecificExitCode", wintypes.DWORD),
        ("dwCheckPoint", wintypes.DWORD),
        ("dwWaitHint", wintypes.DWORD),
    ]


class ENUM_SERVICE_STATUS(ctypes.Structure):
    _fields_ = [
        ("lpServiceName", wintypes.LPWSTR),
        ("lpDisplayName", wintypes.LPWSTR),
        ("ServiceStatus", SERVICE_STATUS),
    ]


@dataclass
class RegistryValue:
    """Registry value information."""
    name: str
    value_type: int
    data: Any


@dataclass
class ServiceInfo:
    """Service information."""
    name: str
    display_name: str
    state: str
    service_type: str
    start_type: str


class Advapi32API:
    """Wrapper for advapi32 registry and service functions."""

    def __init__(self):
        self.advapi32 = ctypes.windll.advapi32
        self._setup_function_signatures()

    def _setup_function_signatures(self):
        """Configure ctypes function signatures."""
        # Registry functions
        self.advapi32.RegOpenKeyExW.argtypes = [
            wintypes.HKEY,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.HKEY),
        ]

        self.advapi32.RegOpenKeyExW.restype = wintypes.LONG

        self.advapi32.RegQueryValueExW.argtypes = [
            wintypes.HKEY,
            wintypes.LPCWSTR,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.advapi32.RegQueryValueExW.restype = wintypes.LONG

        self.advapi32.RegEnumKeyExW.argtypes = [
            wintypes.HKEY,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(SYSTEMTIME),
        ]
        self.advapi32.RegEnumKeyExW.restype = wintypes.LONG

        self.advapi32.RegCloseKey.argtypes = [wintypes.HKEY]
        self.advapi32.RegCloseKey.restype = wintypes.LONG

        # Service functions
        self.advapi32.OpenSCManagerW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
        ]
        self.advapi32.OpenSCManagerW.restype = wintypes.SC_HANDLE

        self.advapi32.OpenServiceW.argtypes = [
            wintypes.SC_HANDLE,
            wintypes.LPCWSTR,
            wintypes.DWORD,
        ]
        self.advapi32.OpenServiceW.restype = wintypes.SC_HANDLE

        self.advapi32.QueryServiceStatus.argtypes = [
            wintypes.SC_HANDLE,
            ctypes.POINTER(SERVICE_STATUS),
        ]
        self.advapi32.QueryServiceStatus.restype = wintypes.BOOL

        self.advapi32.EnumServicesStatusW.argtypes = [
            wintypes.SC_HANDLE,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ENUM_SERVICE_STATUS),
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        self.advapi32.EnumServicesStatusW.restype = wintypes.BOOL

        self.advapi32.CloseServiceHandle.argtypes = [wintypes.SC_HANDLE]
        self.advapi32.CloseServiceHandle.restype = wintypes.BOOL

    def read_registry_value(self, hive: int, path: str, value_name: str) -> Optional[Any]:
        """
        Read a registry value.

        Args:
            hive: Registry hive (HKEY_*)
            path: Registry path
            value_name: Value name

        Returns:
            Registry value or None
        """
        try:
            key = wintypes.HKEY()
            result = self.advapi32.RegOpenKeyExW(hive, path, 0, KEY_READ, ctypes.byref(key))

            if result != 0:  # ERROR_SUCCESS
                return None

            try:
                value_type = wintypes.DWORD()
                data_size = wintypes.DWORD(4096)
                data = ctypes.create_unicode_buffer(4096)

                result = self.advapi32.RegQueryValueExW(
                    key, value_name, None, ctypes.byref(value_type), data, ctypes.byref(data_size)
                )

                if result == 0:
                    return RegistryValue(name=value_name, value_type=value_type.value, data=data.value)

                return None
            finally:
                self.advapi32.RegCloseKey(key)
        except Exception:
            return None

    def enumerate_registry_values(self, hive: int, path: str) -> List[RegistryValue]:
        """
        Enumerate all values in a registry key.

        Args:
            hive: Registry hive
            path: Registry path

        Returns:
            List of RegistryValue objects
        """
        values = []
        try:
            key = wintypes.HKEY()
            result = self.advapi32.RegOpenKeyExW(hive, path, 0, KEY_READ, ctypes.byref(key))

            if result != 0:
                return values

            try:
                index = 0
                while True:
                    value_name_buffer = ctypes.create_unicode_buffer(256)
                    value_name_size = wintypes.DWORD(len(value_name_buffer))
                    value_type = wintypes.DWORD()
                    data_size = wintypes.DWORD(4096)
                    data = ctypes.create_unicode_buffer(4096)

                    result = self.advapi32.RegEnumKeyExW(
                        key,
                        index,
                        value_name_buffer,
                        ctypes.byref(value_name_size),
                        None,
                        None,
                        None,
                        None,
                    )

                    if result != 0:  # Not found
                        break

                    values.append(
                        RegistryValue(
                            name=value_name_buffer.value, value_type=value_type.value, data=data.value
                        )
                    )
                    index += 1
            finally:
                self.advapi32.RegCloseKey(key)
        except Exception:
            pass

        return values

    def enumerate_services(self) -> List[ServiceInfo]:
        """
        Enumerate all services.

        Returns:
            List of ServiceInfo objects
        """
        services = []
        try:
            scm_handle = self.advapi32.OpenSCManagerW(None, None, 0x0001)  # SC_MANAGER_ENUMERATE_SERVICE

            if not scm_handle:
                return services

            try:
                max_services = 256
                services_buffer = (ENUM_SERVICE_STATUS * max_services)()
                bytes_needed = wintypes.DWORD()
                services_returned = wintypes.DWORD()

                result = self.advapi32.EnumServicesStatusW(
                    scm_handle,
                    0x00000030,  # SERVICE_WIN32 | SERVICE_DRIVER
                    0x00000004,  # SERVICE_ACTIVE
                    services_buffer,
                    ctypes.sizeof(services_buffer),
                    ctypes.byref(bytes_needed),
                    ctypes.byref(services_returned),
                    None,
                )

                if result:
                    for i in range(services_returned.value):
                        svc = services_buffer[i]
                        service_info = ServiceInfo(
                            name=svc.lpServiceName if svc.lpServiceName else "Unknown",
                            display_name=svc.lpDisplayName if svc.lpDisplayName else "Unknown",
                            state="Running" if svc.ServiceStatus.dwCurrentState == SERVICE_RUNNING else "Stopped",
                            service_type="Service" if svc.ServiceStatus.dwServiceType == 0x00000010 else "Driver",
                            start_type="Auto Start"
                            if svc.ServiceStatus.dwCurrentState == SERVICE_AUTO_START
                            else "Manual",
                        )
                        services.append(service_info)
            finally:
                self.advapi32.CloseServiceHandle(scm_handle)
        except Exception:
            pass

        return services
