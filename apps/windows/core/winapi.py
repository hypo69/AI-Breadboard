"""
Main WinAPI wrapper with capability levels
"""

import ctypes
import os
import sys
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


class CapabilityLevel(IntEnum):
    """API capability levels"""
    LEVEL_1_DOCUMENTED = 1  # Documented Win32 API
    LEVEL_2_WMI_PERF = 2    # WMI / Performance Counters
    LEVEL_3_ETW = 3          # Event Tracing for Windows
    LEVEL_4_NATIVE_NT = 4    # Native NT API
    LEVEL_5_UNDOCUMENTED = 5 # Undocumented structures
    LEVEL_6_KERNEL_DRIVER = 6 # Optional kernel driver


@dataclass
class WinAPICapabilities:
    """Detected WinAPI capabilities"""
    level: CapabilityLevel
    os_version: str
    is_admin: bool
    architecture: str  # x86, x64, ARM64
    available_dlls: Dict[str, bool]
    supported_apis: Dict[str, bool]


class WinAPI:
    """
    Main Windows API interface with multi-level capability detection
    
    Automatically detects available APIs and falls back gracefully
    """

    def __init__(self):
        """Initialize WinAPI with capability detection"""
        self.logger = logging.getLogger(__name__)
        self.capabilities = self._detect_capabilities()
        self._init_dlls()
        self._init_functions()

    def _detect_capabilities(self) -> WinAPICapabilities:
        """Detect available Windows API capabilities"""
        # Detect OS version
        os_version = sys.platform
        
        # Check admin
        is_admin = self._check_admin()
        
        # Detect architecture
        arch = "x64" if sys.maxsize > 2**32 else "x86"
        
        # Check available DLLs
        available_dlls = {
            "kernel32": self._check_dll("kernel32.dll"),
            "psapi": self._check_dll("psapi.dll"),
            "advapi32": self._check_dll("advapi32.dll"),
            "ntdll": self._check_dll("ntdll.dll"),
            "iphlpapi": self._check_dll("iphlpapi.dll"),
            "setupapi": self._check_dll("setupapi.dll"),
            "wevtapi": self._check_dll("wevtapi.dll"),
            "pdh": self._check_dll("pdh.dll"),
        }
        
        # Determine capability level
        level = CapabilityLevel.LEVEL_1_DOCUMENTED
        if available_dlls["ntdll"]:
            level = CapabilityLevel.LEVEL_4_NATIVE_NT
        elif available_dlls["advapi32"]:
            level = CapabilityLevel.LEVEL_2_WMI_PERF
        
        supported_apis = {
            "process_enumeration": available_dlls["kernel32"],
            "memory_info": available_dlls["psapi"],
            "registry": available_dlls["advapi32"],
            "native_nt": available_dlls["ntdll"],
            "network": available_dlls["iphlpapi"],
            "devices": available_dlls["setupapi"],
            "events": available_dlls["wevtapi"],
            "performance": available_dlls["pdh"],
        }
        
        return WinAPICapabilities(
            level=level,
            os_version=os_version,
            is_admin=is_admin,
            architecture=arch,
            available_dlls=available_dlls,
            supported_apis=supported_apis,
        )

    @staticmethod
    def _check_admin() -> bool:
        """Check if running as admin"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    @staticmethod
    def _check_dll(dll_name: str) -> bool:
        """Check if DLL is available"""
        try:
            ctypes.windll.LoadLibrary(dll_name)
            return True
        except (OSError, AttributeError):
            return False

    def _init_dlls(self):
        """Initialize DLL handles"""
        self.kernel32 = self._load_dll("kernel32.dll")
        self.psapi = self._load_dll("psapi.dll")
        self.advapi32 = self._load_dll("advapi32.dll")
        self.ntdll = self._load_dll("ntdll.dll")
        self.iphlpapi = self._load_dll("iphlpapi.dll")
        self.setupapi = self._load_dll("setupapi.dll")
        self.wevtapi = self._load_dll("wevtapi.dll")
        self.pdh = self._load_dll("pdh.dll")

    @staticmethod
    def _load_dll(dll_name: str) -> Optional[Any]:
        """Load DLL if available"""
        try:
            return ctypes.windll.LoadLibrary(dll_name)
        except (OSError, AttributeError):
            return None

    def _init_functions(self):
        """Initialize function pointers"""
        # Level 1 - Documented Win32 API
        if self.kernel32:
            try:
                self.CreateToolhelp32Snapshot = self.kernel32.CreateToolhelp32Snapshot
                self.Process32FirstW = self.kernel32.Process32FirstW
                self.Process32NextW = self.kernel32.Process32NextW
                self.GetProcessMemoryInfo = self.psapi.GetProcessMemoryInfo if self.psapi else None
                self.EnumProcesses = self.psapi.EnumProcesses if self.psapi else None
            except AttributeError as e:
                logger.warning(f"Failed to initialize function: {e}")

    def get_capability_level(self) -> CapabilityLevel:
        """Get detected capability level"""
        return self.capabilities.level

    def is_admin(self) -> bool:
        """Check if running as admin"""
        return self.capabilities.is_admin

    def get_supported_features(self) -> Dict[str, bool]:
        """Get dictionary of supported features"""
        return self.capabilities.supported_apis

    def get_architecture(self) -> str:
        """Get system architecture"""
        return self.capabilities.architecture

    def __repr__(self) -> str:
        return (
            f"WinAPI(level={self.capabilities.level.name}, "
            f"admin={self.is_admin()}, "
            f"arch={self.get_architecture()})"
        )


# Singleton instance
_winapi_instance = None


def get_winapi() -> WinAPI:
    """Get or create WinAPI singleton"""
    global _winapi_instance
    if _winapi_instance is None:
        _winapi_instance = WinAPI()
    return _winapi_instance
