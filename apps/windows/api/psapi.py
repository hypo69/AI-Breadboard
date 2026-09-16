"""
psapi.dll wrapper for process memory and module enumeration.

Provides access to:
- EnumProcesses: Get all process IDs
- GetProcessMemoryInfo: Get memory statistics
- EnumProcessModules: Get loaded modules
- GetModuleFilename: Get module path
- EnumProcessModulesEx: Get modules with filter
- GetProcessImageFilename: Get process executable path
"""

import ctypes
import ctypes.wintypes as wintypes
from typing import List, Optional, Tuple
from dataclasses import dataclass

# Constants
LIST_MODULES_DEFAULT = 0x00
LIST_MODULES_32BIT = 0x01
LIST_MODULES_64BIT = 0x02
LIST_MODULES_ALL = 0x03

# Structure definitions
SIZE_T = getattr(wintypes, "SIZE_T", ctypes.c_size_t)

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", SIZE_T),
        ("WorkingSetSize", SIZE_T),
        ("QuotaPeakPagedPoolUsage", SIZE_T),
        ("QuotaPagedPoolUsage", SIZE_T),
        ("QuotaPeakNonPagedPoolUsage", SIZE_T),
        ("QuotaNonPagedPoolUsage", SIZE_T),
        ("PagefileUsage", SIZE_T),
        ("PeakPagefileUsage", SIZE_T),
    ]



@dataclass
class MemoryInfo:
    """Process memory statistics from psapi."""
    page_faults: int
    peak_working_set: int
    working_set: int
    paged_pool_peak: int
    paged_pool_usage: int
    nonpaged_pool_peak: int
    nonpaged_pool_usage: int
    pagefile_usage: int
    pagefile_peak: int


class PsapiAPI:
    """Wrapper for psapi process memory and module functions."""

    def __init__(self):
        self.psapi = ctypes.windll.psapi
        self._setup_function_signatures()

    def _setup_function_signatures(self):
        """Configure ctypes function signatures."""
        # EnumProcesses
        self.psapi.EnumProcesses.argtypes = [
            ctypes.POINTER(wintypes.DWORD),
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.psapi.EnumProcesses.restype = wintypes.BOOL

        # GetProcessMemoryInfo
        self.psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
            wintypes.DWORD,
        ]
        self.psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

        # EnumProcessModules
        self.psapi.EnumProcessModules.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.HMODULE),
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.psapi.EnumProcessModules.restype = wintypes.BOOL

        # EnumProcessModulesEx
        self.psapi.EnumProcessModulesEx.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.HMODULE),
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.DWORD,
        ]
        self.psapi.EnumProcessModulesEx.restype = wintypes.BOOL

        # GetModuleFileNameExW
        self.psapi.GetModuleFileNameExW.argtypes = [
            wintypes.HANDLE,
            wintypes.HMODULE,
            wintypes.LPWSTR,
            wintypes.DWORD,
        ]
        self.psapi.GetModuleFileNameExW.restype = wintypes.DWORD

        # GetProcessImageFileNameW
        self.psapi.GetProcessImageFileNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
        ]
        self.psapi.GetProcessImageFileNameW.restype = wintypes.DWORD

    def enumerate_processes(self) -> List[int]:
        """
        Get all process IDs.

        Returns:
            List of process IDs
        """
        max_pids = 1024
        pids = (wintypes.DWORD * max_pids)()
        count_ptr = wintypes.DWORD()

        if self.psapi.EnumProcesses(pids, ctypes.sizeof(pids), ctypes.byref(count_ptr)):
            count = count_ptr.value // ctypes.sizeof(wintypes.DWORD)
            return list(pids[:count])

        return []

    def get_process_memory_info(self, pid: int) -> Optional[MemoryInfo]:
        """
        Get memory statistics for a process.

        Args:
            pid: Process ID

        Returns:
            MemoryInfo object or None
        """
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
            if not handle:
                return None

            try:
                pmc = PROCESS_MEMORY_COUNTERS()
                pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)

                if self.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), ctypes.sizeof(pmc)):
                    return MemoryInfo(
                        page_faults=pmc.PageFaultCount,
                        peak_working_set=pmc.PeakWorkingSetSize,
                        working_set=pmc.WorkingSetSize,
                        paged_pool_peak=pmc.QuotaPeakPagedPoolUsage,
                        paged_pool_usage=pmc.QuotaPagedPoolUsage,
                        nonpaged_pool_peak=pmc.QuotaPeakNonPagedPoolUsage,
                        nonpaged_pool_usage=pmc.QuotaNonPagedPoolUsage,
                        pagefile_usage=pmc.PagefileUsage,
                        pagefile_peak=pmc.PeakPagefileUsage,
                    )
                return None
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return None

    def enumerate_process_modules(self, pid: int, filter_type: int = LIST_MODULES_ALL) -> List[str]:
        """
        Get loaded modules for a process.

        Args:
            pid: Process ID
            filter_type: Module filter (32-bit, 64-bit, or all)

        Returns:
            List of module paths
        """
        modules = []
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x1000 | 0x0400, False, pid)  # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
            if not handle:
                return modules

            try:
                max_modules = 256
                module_handles = (wintypes.HMODULE * max_modules)()
                count_ptr = wintypes.DWORD()

                if self.psapi.EnumProcessModulesEx(
                    handle, module_handles, ctypes.sizeof(module_handles), ctypes.byref(count_ptr), filter_type
                ):
                    count = count_ptr.value // ctypes.sizeof(wintypes.HMODULE)
                    for i in range(count):
                        filename_buffer = ctypes.create_unicode_buffer(260)
                        if self.psapi.GetModuleFileNameExW(
                            handle, module_handles[i], filename_buffer, len(filename_buffer)
                        ):
                            modules.append(filename_buffer.value)
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass

        return modules

    def get_process_image_filename(self, pid: int) -> Optional[str]:
        """
        Get the executable path of a process.

        Args:
            pid: Process ID

        Returns:
            Process image filename or None
        """
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
            if not handle:
                return None

            try:
                filename_buffer = ctypes.create_unicode_buffer(260)
                if self.psapi.GetProcessImageFileNameW(handle, filename_buffer, len(filename_buffer)):
                    return filename_buffer.value
                return None
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return None
