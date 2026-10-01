# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Win32_Ffi - Psapi
# =============================================================================
# Description:
#   psapi.dll wrapper for process memory and module enumeration.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.win32_ffi.psapi import PROCESS_MEMORY_COUNTERS
#
#     service = PROCESS_MEMORY_COUNTERS()
#
# File: psapi.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.win32_ffi
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""psapi.dll wrapper for process memory and module enumeration."""

import ctypes
import ctypes.wintypes as wintypes
from typing import List, Optional, Tuple
from dataclasses import dataclass
LIST_MODULES_DEFAULT = 0
LIST_MODULES_32BIT = 1
LIST_MODULES_64BIT = 2
LIST_MODULES_ALL = 3
SIZE_T = getattr(wintypes, 'SIZE_T', ctypes.c_size_t)

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD), ('PeakWorkingSetSize', SIZE_T), ('WorkingSetSize', SIZE_T), ('QuotaPeakPagedPoolUsage', SIZE_T), ('QuotaPagedPoolUsage', SIZE_T), ('QuotaPeakNonPagedPoolUsage', SIZE_T), ('QuotaNonPagedPoolUsage', SIZE_T), ('PagefileUsage', SIZE_T), ('PeakPagefileUsage', SIZE_T)]

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
        self.psapi.EnumProcesses.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        self.psapi.EnumProcesses.restype = wintypes.BOOL
        self.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
        self.psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        self.psapi.EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        self.psapi.EnumProcessModules.restype = wintypes.BOOL
        self.psapi.EnumProcessModulesEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
        self.psapi.EnumProcessModulesEx.restype = wintypes.BOOL
        self.psapi.GetModuleFileNameExW.argtypes = [wintypes.HANDLE, wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
        self.psapi.GetModuleFileNameExW.restype = wintypes.DWORD
        self.psapi.GetProcessImageFileNameW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD]
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
            handle = ctypes.windll.kernel32.OpenProcess(1024, False, pid)
            if not handle:
                return None
            try:
                pmc = PROCESS_MEMORY_COUNTERS()
                pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
                if self.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), ctypes.sizeof(pmc)):
                    return MemoryInfo(page_faults=pmc.PageFaultCount, peak_working_set=pmc.PeakWorkingSetSize, working_set=pmc.WorkingSetSize, paged_pool_peak=pmc.QuotaPeakPagedPoolUsage, paged_pool_usage=pmc.QuotaPagedPoolUsage, nonpaged_pool_peak=pmc.QuotaPeakNonPagedPoolUsage, nonpaged_pool_usage=pmc.QuotaNonPagedPoolUsage, pagefile_usage=pmc.PagefileUsage, pagefile_peak=pmc.PeakPagefileUsage)
                return None
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return None

    def enumerate_process_modules(self, pid: int, filter_type: int=LIST_MODULES_ALL) -> List[str]:
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
            handle = ctypes.windll.kernel32.OpenProcess(4096 | 1024, False, pid)
            if not handle:
                return modules
            try:
                max_modules = 256
                module_handles = (wintypes.HMODULE * max_modules)()
                count_ptr = wintypes.DWORD()
                if self.psapi.EnumProcessModulesEx(handle, module_handles, ctypes.sizeof(module_handles), ctypes.byref(count_ptr), filter_type):
                    count = count_ptr.value // ctypes.sizeof(wintypes.HMODULE)
                    for i in range(count):
                        filename_buffer = ctypes.create_unicode_buffer(260)
                        if self.psapi.GetModuleFileNameExW(handle, module_handles[i], filename_buffer, len(filename_buffer)):
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
            handle = ctypes.windll.kernel32.OpenProcess(1024, False, pid)
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