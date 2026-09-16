"""
Event Tracing for Windows (ETW) wrapper for real-time event monitoring.

Provides access to:
- Kernel Logger session (Real-time events)
- Event tracing provider registration
- Event filtering and parsing
- Performance monitoring events
"""

import ctypes
import ctypes.wintypes as wintypes
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass
from enum import IntFlag
import threading

# ETW Constants
EVENT_TRACE_FLAG_PROCESS = 0x00000001
EVENT_TRACE_FLAG_THREAD = 0x00000002
EVENT_TRACE_FLAG_IMAGE_LOAD = 0x00000004
EVENT_TRACE_FLAG_DISK_IO = 0x00000100
EVENT_TRACE_FLAG_DISK_FILE_IO = 0x00000200
EVENT_TRACE_FLAG_MEMORY_PAGE_FAULTS = 0x00001000
EVENT_TRACE_FLAG_MEMORY_HARD_FAULTS = 0x00002000
EVENT_TRACE_FLAG_NETWORK_TCPIP = 0x00010000
EVENT_TRACE_FLAG_REGISTRY = 0x00020000
EVENT_TRACE_FLAG_FILE_IO = 0x00040000
EVENT_TRACE_FLAG_FILE_IO_INIT = 0x00080000

EVENT_TRACE_REAL_TIME_MODE = 0x00000100
EVENT_TRACE_FILE_MODE_SEQUENTIAL = 0x00000001
EVENT_TRACE_FILE_MODE_CIRCULAR = 0x00000002
EVENT_TRACE_USE_GLOBAL_SEQUENCE = 0x00004000

WNODE_FLAG_TRACED_GUID = 0x00020000
WNODE_FLAG_USE_MOF_PTR = 0x00100000

# Callback types
PEVENT_TRACE_BUFFER_CALLBACK = ctypes.CFUNCTYPE(wintypes.ULONG, wintypes.LPVOID)
PEVENT_CALLBACK = ctypes.CFUNCTYPE(None, wintypes.LPVOID)



# Structure definitions
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class WNODE_HEADER(ctypes.Structure):
    _fields_ = [
        ("BufferSize", wintypes.DWORD),
        ("ProviderId", wintypes.DWORD),
        ("ClientContext", ctypes.c_uint64),
        ("Timestamp", ctypes.c_uint64),
        ("Guid", GUID),
        ("KernelHandle", wintypes.HANDLE),
        ("Flags", wintypes.DWORD),
    ]


class EVENT_TRACE_PROPERTIES(ctypes.Structure):
    _fields_ = [
        ("Wnode", WNODE_HEADER),
        ("BufferSize", wintypes.DWORD),
        ("MinimumBuffers", wintypes.DWORD),
        ("MaximumBuffers", wintypes.DWORD),
        ("MaximumFileSize", wintypes.DWORD),
        ("LogFileMode", wintypes.DWORD),
        ("FlushTimer", wintypes.DWORD),
        ("EnableFlags", wintypes.DWORD),
        ("AgeLimit", wintypes.LONG),
        ("NumberOfBuffers", wintypes.DWORD),
        ("FreeBuffers", wintypes.DWORD),
        ("EventsLost", wintypes.DWORD),
        ("BuffersWritten", wintypes.DWORD),
        ("LogBuffersLost", wintypes.DWORD),
        ("RealTimeBuffersLost", wintypes.DWORD),
        ("LoggerThreadId", wintypes.HANDLE),
    ]


class EVENT_TRACE_HEADER(ctypes.Structure):
    _fields_ = [
        ("Size", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("Class", ctypes.c_ubyte),
        ("Type", ctypes.c_ubyte),
        ("Level", ctypes.c_ubyte),
        ("Version", ctypes.c_ubyte),
        ("Marker", wintypes.DWORD),
        ("ThreadId", wintypes.DWORD),
        ("ProcessId", wintypes.DWORD),
        ("TimeStamp", ctypes.c_uint64),
        ("ProviderId", GUID),
        ("ClientContext", wintypes.DWORD),
        ("Flags", wintypes.DWORD),
    ]


@dataclass
class EtwEvent:
    """ETW event information."""
    timestamp: int
    pid: int
    tid: int
    event_class: int
    event_type: int
    level: int
    data: bytes


class EtwAPI:
    """Wrapper for ETW event tracing functions."""

    def __init__(self):
        self.advapi32 = ctypes.windll.advapi32
        self.ntdll = ctypes.windll.ntdll
        self._setup_function_signatures()
        self._session_handle = None
        self._event_callbacks: Dict[int, List[Callable]] = {}

    def _setup_function_signatures(self):
        """Configure ctypes function signatures."""
        # StartTrace
        self.advapi32.StartTraceW.argtypes = [
            ctypes.POINTER(wintypes.HANDLE),
            wintypes.LPCWSTR,
            ctypes.POINTER(EVENT_TRACE_PROPERTIES),
        ]
        self.advapi32.StartTraceW.restype = wintypes.ULONG

        # StopTrace
        self.advapi32.StopTraceW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPCWSTR,
            ctypes.POINTER(EVENT_TRACE_PROPERTIES),
        ]
        self.advapi32.StopTraceW.restype = wintypes.ULONG

        # EnableTrace
        self.advapi32.EnableTrace.argtypes = [
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.ULONG,
            ctypes.POINTER(GUID),
            wintypes.HANDLE,
        ]
        self.advapi32.EnableTrace.restype = wintypes.ULONG

        # ControlTrace
        self.advapi32.ControlTraceW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPCWSTR,
            ctypes.POINTER(EVENT_TRACE_PROPERTIES),
            wintypes.DWORD,
        ]
        self.advapi32.ControlTraceW.restype = wintypes.ULONG

    def start_kernel_logger(self, enable_flags: int = EVENT_TRACE_FLAG_PROCESS) -> bool:
        """
        Start the Kernel Logger session for real-time event tracing.

        Args:
            enable_flags: Flags for events to capture

        Returns:
            True if successful
        """
        try:
            properties = EVENT_TRACE_PROPERTIES()
            properties.Wnode.BufferSize = ctypes.sizeof(EVENT_TRACE_PROPERTIES)
            properties.Wnode.Guid = GUID()
            properties.Wnode.ClientContext = 1
            properties.Wnode.Flags = WNODE_FLAG_TRACED_GUID
            properties.BufferSize = 128
            properties.MinimumBuffers = 4
            properties.MaximumBuffers = 64
            properties.LogFileMode = EVENT_TRACE_REAL_TIME_MODE | EVENT_TRACE_USE_GLOBAL_SEQUENCE
            properties.FlushTimer = 100
            properties.EnableFlags = enable_flags
            properties.AgeLimit = 0

            session_handle = wintypes.HANDLE()
            status = self.advapi32.StartTraceW(
                ctypes.byref(session_handle), "NT Kernel Logger", ctypes.byref(properties)
            )

            if status == 0:  # ERROR_SUCCESS
                self._session_handle = session_handle
                return True

            return False
        except Exception:
            return False

    def stop_kernel_logger(self) -> bool:
        """
        Stop the Kernel Logger session.

        Returns:
            True if successful
        """
        try:
            if not self._session_handle:
                return False

            properties = EVENT_TRACE_PROPERTIES()
            properties.Wnode.BufferSize = ctypes.sizeof(EVENT_TRACE_PROPERTIES)

            status = self.advapi32.StopTraceW(
                self._session_handle, "NT Kernel Logger", ctypes.byref(properties)
            )

            if status == 0:
                self._session_handle = None
                return True

            return False
        except Exception:
            return False

    def register_event_callback(self, event_type: int, callback: Callable) -> None:
        """
        Register a callback for a specific event type.

        Args:
            event_type: ETW event type
            callback: Callback function to invoke
        """
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(callback)

    def unregister_event_callback(self, event_type: int, callback: Callable) -> None:
        """
        Unregister a callback.

        Args:
            event_type: ETW event type
            callback: Callback function to remove
        """
        if event_type in self._event_callbacks:
            try:
                self._event_callbacks[event_type].remove(callback)
            except ValueError:
                pass

    def get_session_handle(self) -> Optional[wintypes.HANDLE]:
        """Get the current session handle."""
        return self._session_handle
