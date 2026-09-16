"""
kernel32.dll wrapper for process enumeration and snapshot operations.

Provides access to:
- CreateToolhelp32Snapshot: Snapshot processes, threads, modules
- Process32First/Process32Next: Enumerate processes
- Thread32First/Thread32Next: Enumerate threads
- Module32First/Module32Next: Enumerate modules
- GetCurrentProcess: Get current process handle
- GetProcessTimes: Get process creation/exit times
- GetProcessPriorityClass: Get process priority
"""

import ctypes
import ctypes.wintypes as wintypes
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import IntFlag

# Constants
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPTHREAD = 0x00000004
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

# Process priority classes
ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
HIGH_PRIORITY_CLASS = 0x00000080
IDLE_PRIORITY_CLASS = 0x00000040
NORMAL_PRIORITY_CLASS = 0x00000020
REALTIME_PRIORITY_CLASS = 0x00000100

# Structure definitions
class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("dwPriority", wintypes.LONG),
        ("dwThreadCount", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("pcbUsage", wintypes.DWORD),
        ("th32AccessKey", wintypes.LPVOID),
        ("szExeFile", ctypes.c_char * 260),
    ]


class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]


class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlpvBase", wintypes.LPVOID),
        ("dwSize_", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", ctypes.c_char * 256),
        ("szExePath", ctypes.c_char * 260),
    ]


class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


@dataclass
class ProcessInfo:
    """Process snapshot information from Toolhelp32."""
    pid: int
    ppid: int
    name: str
    priority: int
    thread_count: int


@dataclass
class ThreadInfo:
    """Thread snapshot information from Toolhelp32."""
    tid: int
    pid: int
    base_priority: int
    delta_priority: int


@dataclass
class ModuleInfo:
    """Module snapshot information from Toolhelp32."""
    name: str
    path: str
    base_address: int
    size: int


class Kernel32API:
    """Wrapper for kernel32 process and thread enumeration functions."""

    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self._setup_function_signatures()

    def _setup_function_signatures(self):
        """Configure ctypes function signatures for proper type checking."""
        # CreateToolhelp32Snapshot
        self.kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE

        # Process32First / Process32Next
        self.kernel32.Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
        self.kernel32.Process32First.restype = wintypes.BOOL

        self.kernel32.Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
        self.kernel32.Process32Next.restype = wintypes.BOOL

        # Thread32First / Thread32Next
        self.kernel32.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
        self.kernel32.Thread32First.restype = wintypes.BOOL

        self.kernel32.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
        self.kernel32.Thread32Next.restype = wintypes.BOOL

        # Module32First / Module32Next
        self.kernel32.Module32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
        self.kernel32.Module32First.restype = wintypes.BOOL

        self.kernel32.Module32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
        self.kernel32.Module32Next.restype = wintypes.BOOL

        # CloseHandle
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL

        # GetCurrentProcess
        self.kernel32.GetCurrentProcess.restype = wintypes.HANDLE

        # GetProcessTimes
        self.kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(FILETIME),
            ctypes.POINTER(FILETIME),
            ctypes.POINTER(FILETIME),
            ctypes.POINTER(FILETIME),
        ]
        self.kernel32.GetProcessTimes.restype = wintypes.BOOL

        # GetPriorityClass
        self.kernel32.GetPriorityClass.argtypes = [wintypes.HANDLE]
        self.kernel32.GetPriorityClass.restype = wintypes.DWORD


    def enumerate_processes(self) -> List[ProcessInfo]:
        """
        Enumerate all running processes using Toolhelp32.

        Returns:
            List of ProcessInfo objects
        """
        processes = []
        snapshot = self.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)

        if snapshot == -1:
            return processes

        try:
            pe = PROCESSENTRY32()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32)

            if self.kernel32.Process32First(snapshot, ctypes.byref(pe)):
                while True:
                    try:
                        process = ProcessInfo(
                            pid=pe.th32ProcessID,
                            ppid=pe.th32ParentProcessID,
                            name=pe.szExeFile.decode('utf-8', errors='ignore'),
                            priority=pe.dwPriority,
                            thread_count=pe.dwThreadCount,
                        )
                        processes.append(process)
                    except Exception:
                        pass

                    if not self.kernel32.Process32Next(snapshot, ctypes.byref(pe)):
                        break

        finally:
            self.kernel32.CloseHandle(snapshot)

        return processes

    def enumerate_threads(self, pid: Optional[int] = None) -> List[ThreadInfo]:
        """
        Enumerate threads for a process or all threads if pid is None.

        Args:
            pid: Process ID to filter threads, or None for all threads

        Returns:
            List of ThreadInfo objects
        """
        threads = []
        snapshot = self.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, pid or 0)

        if snapshot == -1:
            return threads

        try:
            te = THREADENTRY32()
            te.dwSize = ctypes.sizeof(THREADENTRY32)

            if self.kernel32.Thread32First(snapshot, ctypes.byref(te)):
                while True:
                    try:
                        if pid is None or te.th32OwnerProcessID == pid:
                            thread = ThreadInfo(
                                tid=te.th32ThreadID,
                                pid=te.th32OwnerProcessID,
                                base_priority=te.tpBasePri,
                                delta_priority=te.tpDeltaPri,
                            )
                            threads.append(thread)
                    except Exception:
                        pass

                    if not self.kernel32.Thread32Next(snapshot, ctypes.byref(te)):
                        break

        finally:
            self.kernel32.CloseHandle(snapshot)

        return threads

    def enumerate_modules(self, pid: int) -> List[ModuleInfo]:
        """
        Enumerate modules (DLLs) loaded in a process.

        Args:
            pid: Process ID

        Returns:
            List of ModuleInfo objects
        """
        modules = []
        snapshot = self.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)

        if snapshot == -1:
            return modules

        try:
            me = MODULEENTRY32()
            me.dwSize = ctypes.sizeof(MODULEENTRY32)

            if self.kernel32.Module32First(snapshot, ctypes.byref(me)):
                while True:
                    try:
                        module = ModuleInfo(
                            name=me.szModule.decode('utf-8', errors='ignore'),
                            path=me.szExePath.decode('utf-8', errors='ignore'),
                            base_address=int(me.GlpvBase),
                            size=me.dwSize_,
                        )
                        modules.append(module)
                    except Exception:
                        pass

                    if not self.kernel32.Module32Next(snapshot, ctypes.byref(me)):
                        break

        finally:
            self.kernel32.CloseHandle(snapshot)

        return modules

    def get_process_priority_class(self, pid: int) -> Optional[str]:
        """
        Get the priority class of a process.

        Args:
            pid: Process ID

        Returns:
            Priority class name or None if error
        """
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not handle:
                return None

            try:
                priority = self.kernel32.GetPriorityClass(handle)
                priority_map = {

                    ABOVE_NORMAL_PRIORITY_CLASS: "Above Normal",
                    BELOW_NORMAL_PRIORITY_CLASS: "Below Normal",
                    HIGH_PRIORITY_CLASS: "High",
                    IDLE_PRIORITY_CLASS: "Idle",
                    NORMAL_PRIORITY_CLASS: "Normal",
                    REALTIME_PRIORITY_CLASS: "Realtime",
                }
                return priority_map.get(priority, f"Unknown ({priority})")
            finally:
                self.kernel32.CloseHandle(handle)
        except Exception:
            return None

    def get_process_times(self, pid: int) -> Optional[Tuple[int, int]]:
        """
        Get process creation and exit times.

        Args:
            pid: Process ID

        Returns:
            Tuple of (creation_time_filetime, exit_time_filetime) or None
        """
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
            if not handle:
                return None

            try:
                creation_time = FILETIME()
                exit_time = FILETIME()
                kernel_time = FILETIME()
                user_time = FILETIME()

                if self.kernel32.GetProcessTimes(
                    handle,
                    ctypes.byref(creation_time),
                    ctypes.byref(exit_time),
                    ctypes.byref(kernel_time),
                    ctypes.byref(user_time),
                ):
                    return (creation_time.dwLowDateTime, exit_time.dwLowDateTime)
                return None
            finally:
                self.kernel32.CloseHandle(handle)
        except Exception:
            return None
