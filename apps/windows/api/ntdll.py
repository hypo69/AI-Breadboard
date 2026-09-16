"""
ntdll.dll wrapper for native NT API functions.

Provides access to:
- NtQuerySystemInformation: Query system information structures
- NtQueryObject: Query object information
- NtQueryInformationProcess: Query process information
- RtlGetVersion: Get Windows version
- RtlGetNtVersionNumbers: Get NT version details
"""

import ctypes
import ctypes.wintypes as wintypes
from typing import Optional, Any
from dataclasses import dataclass

# Status codes
STATUS_SUCCESS = 0x00000000
STATUS_BUFFER_TOO_SMALL = 0xC0000023

# System information classes
SystemBasicInformation = 0
SystemProcessorInformation = 1
SystemPerformanceInformation = 2
SystemTimeOfDayInformation = 3
SystemPathInformation = 4
SystemProcessInformation = 5
SystemCallCountInformation = 6
SystemDeviceInformation = 7
SystemProcessorPerformanceInformation = 8
SystemFlagsInformation = 9
SystemCallTimeInformation = 10
SystemModuleInformation = 11
SystemLocksInformation = 12
SystemStackTraceInformation = 13
SystemPagedPoolInformation = 14
SystemNonPagedPoolInformation = 15
SystemHandleInformation = 16
SystemObjectInformation = 17
SystemPageFileInformation = 18
SystemVdmInstemulInformation = 19
SystemVdmBopInformation = 20
SystemFileCacheInformation = 21
SystemPoolTagInformation = 22
SystemInterruptInformation = 23
SystemDpcBehaviorInformation = 24
SystemFullMemoryInformation = 25
SystemLoadGdiDriverInformation = 26
SystemUnloadGdiDriverInformation = 27
SystemTimeAdjustmentInformation = 28
SystemSummaryMemoryInformation = 29
SystemMirrorInformation = 30
SystemPerformanceTraceInformation = 31
SystemCrashDumpInformation = 32
SystemExceptionInformation = 33
SystemCrashDumpStateInformation = 34
SystemDebuggerInformation = 35
SystemProcessorSpeedInformation = 36
SystemNUMAProximityNodeInformation = 37
SystemDpcWatchdogInformation = 38
SystemDpcWatchdogInformation2 = 39
SystemInvalidProcessorSpeedInformation = 40


# Structure definitions
class SYSTEM_INFO(ctypes.Structure):
    _fields_ = [
        ("dwOemId", wintypes.DWORD),
        ("dwPageSize", wintypes.DWORD),
        ("lpMinimumApplicationAddress", wintypes.LPVOID),
        ("lpMaximumApplicationAddress", wintypes.LPVOID),
        ("dwActiveProcessorMask", wintypes.DWORD),
        ("dwNumberOfProcessors", wintypes.DWORD),
        ("dwProcessorType", wintypes.DWORD),
        ("dwAllocationGranularity", wintypes.DWORD),
        ("wProcessorLevel", wintypes.WORD),
        ("wProcessorRevision", wintypes.WORD),
    ]


class UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    ]


class OBJECT_NAME_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("Name", UNICODE_STRING),
    ]


class PROCESS_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("Reserved1", wintypes.LPVOID),
        ("PebBaseAddress", wintypes.LPVOID),
        ("Reserved2_0", wintypes.LPVOID),
        ("Reserved2_1", wintypes.LPVOID),
        ("UniqueProcessId", wintypes.LPVOID),
        ("Reserved3", wintypes.LPVOID),
    ]


class RTL_OSVERSIONINFOEXW(ctypes.Structure):
    _fields_ = [
        ("dwOSVersionInfoSize", wintypes.DWORD),
        ("dwMajorVersion", wintypes.DWORD),
        ("dwMinorVersion", wintypes.DWORD),
        ("dwBuildNumber", wintypes.DWORD),
        ("dwPlatformId", wintypes.DWORD),
        ("szCSDVersion", ctypes.c_wchar * 128),
        ("wServicePackMajor", wintypes.WORD),
        ("wServicePackMinor", wintypes.WORD),
        ("wSuiteMask", wintypes.WORD),
        ("wProductType", wintypes.BYTE),
        ("wReserved", wintypes.BYTE),
    ]


@dataclass
class VersionInfo:
    """Windows version information."""
    major: int
    minor: int
    build: int
    platform: str


class NtdllAPI:
    """Wrapper for ntdll native API functions."""

    def __init__(self):
        self.ntdll = ctypes.windll.ntdll
        self._setup_function_signatures()

    def _setup_function_signatures(self):
        """Configure ctypes function signatures."""
        # NtQuerySystemInformation
        self.ntdll.NtQuerySystemInformation.argtypes = [
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG),
        ]
        self.ntdll.NtQuerySystemInformation.restype = wintypes.LONG

        # NtQueryObject
        self.ntdll.NtQueryObject.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG),
        ]
        self.ntdll.NtQueryObject.restype = wintypes.LONG

        # NtQueryInformationProcess
        self.ntdll.NtQueryInformationProcess.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG),
        ]
        self.ntdll.NtQueryInformationProcess.restype = wintypes.LONG

        # RtlGetVersion
        self.ntdll.RtlGetVersion.argtypes = [ctypes.POINTER(RTL_OSVERSIONINFOEXW)]
        self.ntdll.RtlGetVersion.restype = wintypes.LONG

    def get_windows_version(self) -> Optional[VersionInfo]:
        """
        Get Windows version information.

        Returns:
            VersionInfo object or None
        """
        try:
            version_info = RTL_OSVERSIONINFOEXW()
            version_info.dwOSVersionInfoSize = ctypes.sizeof(RTL_OSVERSIONINFOEXW)

            status = self.ntdll.RtlGetVersion(ctypes.byref(version_info))
            if status == STATUS_SUCCESS:
                platform_map = {
                    0: "Win32s",
                    1: "Windows 9x",
                    2: "Windows NT/2000/XP/Vista/7/8/10/11",
                }
                return VersionInfo(
                    major=version_info.dwMajorVersion,
                    minor=version_info.dwMinorVersion,
                    build=version_info.dwBuildNumber,
                    platform=platform_map.get(version_info.dwPlatformId, "Unknown"),
                )
            return None
        except Exception:
            return None

    def query_system_information(self, info_class: int) -> Optional[bytes]:
        """
        Query system information.

        Args:
            info_class: System information class

        Returns:
            System information bytes or None
        """
        try:
            buffer_size = 8192
            buffer = ctypes.create_string_buffer(buffer_size)
            return_length = wintypes.ULONG()

            status = self.ntdll.NtQuerySystemInformation(
                info_class, buffer, buffer_size, ctypes.byref(return_length)
            )

            if status == STATUS_SUCCESS:
                return buffer.raw[: return_length.value]

            return None
        except Exception:
            return None

    def query_object_name(self, handle: int) -> Optional[str]:
        """
        Query the name of a kernel object.

        Args:
            handle: Object handle

        Returns:
            Object name or None
        """
        try:
            buffer_size = 1024
            buffer = ctypes.create_string_buffer(buffer_size)
            return_length = wintypes.ULONG()

            status = self.ntdll.NtQueryObject(
                handle, 1, buffer, buffer_size, ctypes.byref(return_length)  # ObjectNameInformation = 1
            )

            if status == STATUS_SUCCESS:
                obj_name_info = ctypes.cast(buffer, ctypes.POINTER(OBJECT_NAME_INFORMATION))
                if obj_name_info.contents.Name.Buffer:
                    return obj_name_info.contents.Name.Buffer

            return None
        except Exception:
            return None

    def query_process_basic_info(self, pid: int) -> Optional[PROCESS_BASIC_INFORMATION]:
        """
        Query basic process information.

        Args:
            pid: Process ID

        Returns:
            PROCESS_BASIC_INFORMATION structure or None
        """
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not handle:
                return None

            try:
                pbi = PROCESS_BASIC_INFORMATION()
                return_length = wintypes.ULONG()

                status = self.ntdll.NtQueryInformationProcess(
                    handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(return_length)  # ProcessBasicInformation = 0
                )

                if status == STATUS_SUCCESS:
                    return pbi

                return None
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return None
