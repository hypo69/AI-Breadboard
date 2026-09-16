"""
Process Intelligence Module - Unified interface for process analysis.

Combines kernel32, psapi, ntdll, and ETW APIs to provide:
- Process enumeration with memory and thread details
- Module dependency analysis
- Thread and handle information
- Real-time event monitoring
- Correlation with services, drivers, and network connections
"""

import threading
import time
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .api.kernel32 import Kernel32API, ProcessInfo as K32ProcessInfo, ThreadInfo as K32ThreadInfo, ModuleInfo as K32ModuleInfo
from .api.psapi import PsapiAPI, MemoryInfo
from .api.advapi32 import Advapi32API
from .api.ntdll import NtdllAPI
from .api.etw import EtwAPI
from .core.data_model import ProcessInfo, ThreadInfo, ModuleInfo, SystemState


@dataclass
class ProcessSnapshot:
    """Complete process snapshot from all API layers."""

    pid: int
    name: str
    path: Optional[str] = None
    ppid: int = 0
    priority: str = "Normal"
    thread_count: int = 0
    memory_info: Optional[MemoryInfo] = None
    threads: List[ThreadInfo] = field(default_factory=list)
    modules: List[ModuleInfo] = field(default_factory=list)
    creation_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None

    @property
    def private_memory_mb(self) -> float:
        """Private memory in MB."""
        if self.memory_info:
            return self.memory_info.working_set / (1024 * 1024)
        return 0.0

    @property
    def peak_memory_mb(self) -> float:
        """Peak memory in MB."""
        if self.memory_info:
            return self.memory_info.peak_working_set / (1024 * 1024)
        return 0.0


@dataclass
class ProcessRelationship:
    """Relationship between processes."""

    parent_pid: int
    child_pid: int
    relationship_type: str  # "parent-child", "module-dependency", "service-process"
    metadata: Dict = field(default_factory=dict)


class ProcessIntelligence:
    """
    Unified process intelligence engine combining all Windows APIs.
    """

    def __init__(self):
        self.kernel32 = Kernel32API()
        self.psapi = PsapiAPI()
        self.advapi32 = Advapi32API()
        self.ntdll = NtdllAPI()
        self.etw = EtwAPI()

        # Cache
        self._process_cache: Dict[int, ProcessSnapshot] = {}
        self._relationships: Dict[int, List[ProcessRelationship]] = {}
        self._module_map: Dict[str, Set[int]] = {}  # module -> processes using it
        self._lock = threading.RLock()

    def enumerate_all_processes(self, refresh: bool = False) -> List[ProcessSnapshot]:
        """
        Enumerate all running processes with full details.

        Args:
            refresh: Force refresh of cache

        Returns:
            List of ProcessSnapshot objects
        """
        snapshots = []

        try:
            # Get basic process list from kernel32
            k32_processes = self.kernel32.enumerate_processes()

            for k32_proc in k32_processes:
                snapshot = self._build_process_snapshot(k32_proc.pid, k32_proc)
                if snapshot:
                    snapshots.append(snapshot)
                    with self._lock:
                        self._process_cache[k32_proc.pid] = snapshot

        except Exception as e:
            print(f"Error enumerating processes: {e}")

        return snapshots

    def _build_process_snapshot(self, pid: int, k32_proc: K32ProcessInfo) -> Optional[ProcessSnapshot]:
        """
        Build a complete process snapshot.

        Args:
            pid: Process ID
            k32_proc: kernel32 process info

        Returns:
            ProcessSnapshot or None
        """
        try:
            snapshot = ProcessSnapshot(
                pid=pid,
                name=k32_proc.name,
                ppid=k32_proc.ppid,
                priority=self.kernel32.get_process_priority_class(pid) or "Normal",
                thread_count=k32_proc.thread_count,
            )

            # Get image path from psapi
            snapshot.path = self.psapi.get_process_image_filename(pid)

            # Get memory info from psapi
            snapshot.memory_info = self.psapi.get_process_memory_info(pid)

            # Get threads
            threads = self.kernel32.enumerate_threads(pid)
            snapshot.threads = [
                ThreadInfo(
                    tid=t.tid,
                    pid=pid,
                    priority=t.base_priority,
                    state="Running",
                )
                for t in threads
            ]

            # Get modules
            module_paths = self.psapi.enumerate_process_modules(pid)
            snapshot.modules = [
                ModuleInfo(
                    path=path,
                    address=0,  # Would need additional lookup for address
                    size=0,
                )
                for path in module_paths
            ]

            # Update module map
            with self._lock:
                for module in snapshot.modules:
                    if module.path not in self._module_map:
                        self._module_map[module.path] = set()
                    self._module_map[module.path].add(pid)

            return snapshot
        except Exception as e:
            return None

    def get_process_details(self, pid: int) -> Optional[ProcessSnapshot]:
        """
        Get detailed information for a specific process.

        Args:
            pid: Process ID

        Returns:
            ProcessSnapshot or None
        """
        with self._lock:
            if pid in self._process_cache:
                return self._process_cache[pid]

        try:
            k32_processes = self.kernel32.enumerate_processes()
            for k32_proc in k32_processes:
                if k32_proc.pid == pid:
                    return self._build_process_snapshot(pid, k32_proc)
        except Exception:
            pass

        return None

    def get_process_threads(self, pid: int) -> List[ThreadInfo]:
        """
        Get all threads for a process.

        Args:
            pid: Process ID

        Returns:
            List of ThreadInfo objects
        """
        try:
            threads = self.kernel32.enumerate_threads(pid)
            return [
                ThreadInfo(
                    tid=t.tid,
                    pid=pid,
                    priority=t.base_priority,
                    state="Running",
                )
                for t in threads
            ]
        except Exception:
            return []

    def get_process_modules(self, pid: int) -> List[ModuleInfo]:
        """
        Get all loaded modules for a process.

        Args:
            pid: Process ID

        Returns:
            List of ModuleInfo objects
        """
        try:
            module_paths = self.psapi.enumerate_process_modules(pid)
            return [
                ModuleInfo(
                    path=path,
                    address=0,
                    size=0,
                )
                for path in module_paths
            ]
        except Exception:
            return []

    def get_process_tree(self) -> Dict[int, List[int]]:
        """
        Get process tree (parent -> children mapping).

        Returns:
            Dictionary of {parent_pid: [child_pids]}
        """
        tree: Dict[int, List[int]] = {}
        try:
            processes = self.kernel32.enumerate_processes()
            for proc in processes:
                if proc.ppid not in tree:
                    tree[proc.ppid] = []
                tree[proc.ppid].append(proc.pid)
        except Exception:
            pass

        return tree

    def find_process_by_name(self, name: str, partial: bool = False) -> List[ProcessSnapshot]:
        """
        Find processes by name.

        Args:
            name: Process name to find
            partial: If True, match partial names

        Returns:
            List of matching ProcessSnapshot objects
        """
        results = []
        try:
            name_lower = name.lower()
            processes = self.enumerate_all_processes()

            for proc in processes:
                if partial:
                    if name_lower in proc.name.lower():
                        results.append(proc)
                else:
                    if proc.name.lower() == name_lower:
                        results.append(proc)
        except Exception:
            pass

        return results

    def get_module_consumers(self, module_path: str) -> Set[int]:
        """
        Get all processes using a specific module.

        Args:
            module_path: Full path to module

        Returns:
            Set of process IDs
        """
        with self._lock:
            return self._module_map.get(module_path, set()).copy()

    def analyze_process_relationships(self) -> List[ProcessRelationship]:
        """
        Analyze relationships between processes.

        Returns:
            List of ProcessRelationship objects
        """
        relationships = []

        try:
            processes = self.kernel32.enumerate_processes()

            # Parent-child relationships
            for proc in processes:
                if proc.ppid != 0:
                    relationships.append(
                        ProcessRelationship(
                            parent_pid=proc.ppid,
                            child_pid=proc.pid,
                            relationship_type="parent-child",
                        )
                    )

            # Module dependency relationships
            for module_path, pids in self._module_map.items():
                if len(pids) > 1:
                    pids_list = sorted(list(pids))
                    for i, pid1 in enumerate(pids_list):
                        for pid2 in pids_list[i + 1 :]:
                            relationships.append(
                                ProcessRelationship(
                                    parent_pid=pid1,
                                    child_pid=pid2,
                                    relationship_type="module-dependency",
                                    metadata={"module": module_path},
                                )
                            )

        except Exception as e:
            print(f"Error analyzing relationships: {e}")

        with self._lock:
            self._relationships[time.time()] = relationships

        return relationships

    def get_system_state(self) -> Optional[SystemState]:
        """
        Get complete system state snapshot.

        Returns:
            SystemState object or None
        """
        try:
            processes = self.enumerate_all_processes()
            version = self.ntdll.get_windows_version()

            total_memory = sum(p.private_memory_mb for p in processes)
            total_threads = sum(p.thread_count for p in processes)

            return SystemState(
                timestamp=datetime.now(),
                processes=processes,
                total_memory_mb=total_memory,
                total_thread_count=total_threads,
                windows_version=f"{version.major}.{version.minor}.{version.build}"
                if version
                else "Unknown",
                system_uptime_seconds=0,  # Would need additional lookup
            )
        except Exception:
            return None

    def start_realtime_monitoring(self) -> bool:
        """
        Start real-time event monitoring via ETW.

        Returns:
            True if successful
        """
        try:
            return self.etw.start_kernel_logger()
        except Exception:
            return False

    def stop_realtime_monitoring(self) -> bool:
        """
        Stop real-time event monitoring.

        Returns:
            True if successful
        """
        try:
            return self.etw.stop_kernel_logger()
        except Exception:
            return False

    def clear_cache(self) -> None:
        """Clear all caches."""
        with self._lock:
            self._process_cache.clear()
            self._relationships.clear()
            self._module_map.clear()
