"""
Normalized data models for Windows system information
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum, IntEnum


class ProcessState(Enum):
    """Process state enumeration"""
    RUNNING = "Running"
    SUSPENDED = "Suspended"
    UNKNOWN = "Unknown"


class ThreadState(IntEnum):
    """Thread state enumeration"""
    INITIALIZED = 0
    READY = 1
    RUNNING = 2
    STANDBY = 3
    TERMINATED = 4
    WAIT = 5
    TRANSITION = 6


class ServiceState(Enum):
    """Service state enumeration"""
    STOPPED = "Stopped"
    START_PENDING = "Start Pending"
    STOP_PENDING = "Stop Pending"
    RUNNING = "Running"
    CONTINUE_PENDING = "Continue Pending"
    PAUSE_PENDING = "Pause Pending"
    PAUSED = "Paused"
    UNKNOWN = "Unknown"


@dataclass
class MemoryInfo:
    """Memory information"""
    working_set: int = 0
    working_set_peak: int = 0
    private_bytes: int = 0
    pagefile_usage: int = 0
    pagefile_peak: int = 0
    paged_pool: int = 0
    nonpaged_pool: int = 0
    page_faults: int = 0
    hard_page_faults: int = 0

    @property
    def working_set_mb(self) -> float:
        return self.working_set / (1024 * 1024)

    @property
    def private_bytes_mb(self) -> float:
        return self.private_bytes / (1024 * 1024)


@dataclass
class ThreadInfo:
    """Thread information"""
    tid: int
    pid: int
    state: ThreadState = ThreadState.RUNNING
    wait_reason: str = "Unknown"
    base_priority: int = 0
    current_priority: int = 0
    cpu_time: int = 0
    kernel_time: int = 0
    user_time: int = 0
    start_time: Optional[datetime] = None
    start_address: int = 0
    suspended: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tid": self.tid,
            "pid": self.pid,
            "state": self.state.name,
            "wait_reason": self.wait_reason,
            "base_priority": self.base_priority,
            "cpu_time_ms": self.cpu_time // 10000,
        }


@dataclass
class ModuleInfo:
    """DLL/Module information"""
    name: str
    path: str
    base_address: int = 0
    size: int = 0
    entry_point: int = 0
    version: str = ""
    company: str = ""
    description: str = ""
    product: str = ""
    is_signed: bool = False
    signer: str = ""
    load_time: Optional[datetime] = None
    architecture: str = ""  # x86, x64, ARM64

    @property
    def size_mb(self) -> float:
        return self.size / (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "version": self.version,
            "company": self.company,
            "signed": self.is_signed,
            "signer": self.signer,
        }


@dataclass
class HandleInfo:
    """Handle/Descriptor information"""
    handle_value: int
    pid: int
    object_type: str  # File, Key, Event, Mutex, etc.
    object_name: str
    access_mask: int = 0
    attributes: int = 0
    inheritance: bool = False
    duplicated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handle": hex(self.handle_value),
            "type": self.object_type,
            "name": self.object_name,
            "access": hex(self.access_mask),
        }


@dataclass
class ProcessInfo:
    """Process information"""
    pid: int
    ppid: int
    name: str
    executable: Optional[str] = None
    command_line: str = ""
    working_directory: str = ""
    username: str = ""
    user_sid: str = ""
    session_id: int = 0
    
    # Performance metrics
    cpu_percent: float = 0.0
    cpu_time: int = 0
    kernel_time: int = 0
    user_time: int = 0
    
    # Memory
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    
    # State
    state: ProcessState = ProcessState.UNKNOWN
    priority: int = 0
    base_priority: int = 0
    affinity: int = 0
    architecture: str = ""  # x86, x64, ARM64
    is_wow64: bool = False
    
    # Lifecycle
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Resources
    thread_count: int = 0
    handle_count: int = 0
    
    # Collections
    threads: List[ThreadInfo] = field(default_factory=list)
    modules: List[ModuleInfo] = field(default_factory=list)
    handles: List[HandleInfo] = field(default_factory=list)
    
    # Security
    integrity_level: str = "Medium"
    elevation: str = "Limited"
    token_user: str = ""
    
    # File info
    company: str = ""
    product: str = ""
    file_version: str = ""
    is_signed: bool = False
    signer: str = ""

    @property
    def memory_mb(self) -> float:
        return self.memory.working_set_mb

    @property
    def private_bytes_mb(self) -> float:
        return self.memory.private_bytes_mb

    @property
    def uptime_seconds(self) -> Optional[float]:
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "ppid": self.ppid,
            "name": self.name,
            "executable": self.executable,
            "memory_mb": self.memory_mb,
            "threads": self.thread_count,
            "handles": self.handle_count,
            "cpu_percent": self.cpu_percent,
            "state": self.state.value,
            "user": self.username,
            "signed": self.is_signed,
        }


@dataclass
class ServiceInfo:
    """Service information"""
    name: str
    display_name: str
    description: str = ""
    executable: str = ""
    command_line: str = ""
    service_type: str = ""
    start_type: str = ""
    current_state: ServiceState = ServiceState.UNKNOWN
    pid: Optional[int] = None
    account: str = ""
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    is_signed: bool = False
    signer: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "state": self.current_state.value,
            "pid": self.pid,
            "executable": self.executable,
            "account": self.account,
        }


@dataclass
class DriverInfo:
    """Driver information"""
    name: str
    display_name: str
    path: str = ""
    service_name: str = ""
    start_type: str = ""
    state: str = ""
    signer: str = ""
    is_signed: bool = False
    version: str = ""
    company: str = ""
    is_test_signed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "signer": self.signer,
            "signed": self.is_signed,
            "test_signed": self.is_test_signed,
        }


@dataclass
class DeviceInfo:
    """Device information"""
    device_id: str
    name: str
    description: str = ""
    driver_path: str = ""
    driver_version: str = ""
    manufacturer: str = ""
    status: str = "Unknown"
    problem_code: int = 0
    location: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
        }


class AppCategory(str, Enum):
    """Категории установленного программного обеспечения."""
    SYSTEM = "Системное ПО"
    DEVELOPMENT = "Разработка и программирование"
    BROWSER = "Веб-браузер"
    COMMUNICATION = "Связь и мессенджеры"
    OFFICE = "Офис и документы"
    MULTIMEDIA = "Мультимедиа и графика"
    UTILITIES = "Утилиты и инструменты"
    SECURITY = "Безопасность и антивирусы"
    GAMES = "Игры и развлечения"
    DRIVERS = "Драйверы и аппаратное ПО"
    OTHER = "Прочее"


@dataclass
class AppExecutionInfo:
    """Информация об истории запусков программы."""
    last_run_time: Optional[datetime] = None
    run_count: int = 0
    focus_time_seconds: int = 0
    source_artifact: str = "UserAssist"  # UserAssist, Prefetch, AppCompatCache, etc.
    raw_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "run_count": self.run_count,
            "focus_time_seconds": self.focus_time_seconds,
            "source_artifact": self.source_artifact,
            "raw_path": self.raw_path,
        }


@dataclass
class InstalledAppInfo:
    """Информация об установленном приложении Windows."""
    name: str
    display_name: str
    version: str = ""
    publisher: str = ""
    install_date: Optional[str] = None
    install_location: str = ""
    uninstall_string: str = ""
    size_bytes: int = 0
    architecture: str = "x64"  # x86, x64, ARM64
    registry_key: str = ""
    is_system_component: bool = False
    
    # Классификация и назначение
    category: AppCategory = AppCategory.OTHER
    purpose_description: str = ""
    
    # История запусков
    execution_info: Optional[AppExecutionInfo] = None

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024) if self.size_bytes else 0.0

    @property
    def was_launched(self) -> bool:
        return self.execution_info is not None and self.execution_info.run_count > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "version": self.version,
            "publisher": self.publisher,
            "install_date": self.install_date,
            "install_location": self.install_location,
            "uninstall_string": self.uninstall_string,
            "size_mb": round(self.size_mb, 2),
            "architecture": self.architecture,
            "category": self.category.value if isinstance(self.category, AppCategory) else str(self.category),
            "purpose_description": self.purpose_description,
            "is_system_component": self.is_system_component,
            "execution_info": self.execution_info.to_dict() if self.execution_info else None,
        }


@dataclass
class SoftwareAuditReport:
    """Сводный отчет по аудиту программного обеспечения."""
    timestamp: datetime = field(default_factory=datetime.now)
    total_apps: int = 0
    active_apps_count: int = 0
    unused_apps_count: int = 0
    categories_breakdown: Dict[str, int] = field(default_factory=dict)
    recently_launched: List[InstalledAppInfo] = field(default_factory=list)
    top_launched: List[InstalledAppInfo] = field(default_factory=list)
    never_launched_or_dormant: List[InstalledAppInfo] = field(default_factory=list)
    apps: List[InstalledAppInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_apps": self.total_apps,
            "active_apps_count": self.active_apps_count,
            "unused_apps_count": self.unused_apps_count,
            "categories_breakdown": self.categories_breakdown,
            "recently_launched": [a.to_dict() for a in self.recently_launched[:10]],
            "top_launched": [a.to_dict() for a in self.top_launched[:10]],
            "never_launched_or_dormant_count": len(self.never_launched_or_dormant),
        }


@dataclass
class SystemState:
    """Complete system state snapshot"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # System info
    hostname: str = ""
    os_version: str = ""
    os_build: str = ""
    architecture: str = ""
    
    # Resources
    total_processes: int = 0
    total_threads: int = 0
    total_handles: int = 0
    
    # Collections
    processes: List[ProcessInfo] = field(default_factory=list)
    services: List[ServiceInfo] = field(default_factory=list)
    drivers: List[DriverInfo] = field(default_factory=list)
    devices: List[DeviceInfo] = field(default_factory=list)
    installed_apps: List[InstalledAppInfo] = field(default_factory=list)
    
    # System memory
    system_memory: MemoryInfo = field(default_factory=MemoryInfo)
    
    # Diagnostics
    anomalies: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def get_process_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """Get process by PID"""
        for proc in self.processes:
            if proc.pid == pid:
                return proc
        return None

    def get_process_by_name(self, name: str) -> List[ProcessInfo]:
        """Get processes by name"""
        return [p for p in self.processes if p.name.lower() == name.lower()]

    def get_service_by_name(self, name: str) -> Optional[ServiceInfo]:
        """Get service by name"""
        for svc in self.services:
            if svc.name.lower() == name.lower():
                return svc
        return None

    def get_installed_app_by_name(self, name: str) -> Optional[InstalledAppInfo]:
        """Получить установленное приложение по имени."""
        name_lower = name.lower()
        for app in self.installed_apps:
            if app.name.lower() == name_lower or app.display_name.lower() == name_lower:
                return app
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "hostname": self.hostname,
            "os_version": self.os_version,
            "total_processes": self.total_processes,
            "total_threads": self.total_threads,
            "total_handles": self.total_handles,
            "total_installed_apps": len(self.installed_apps),
            "anomalies": len(self.anomalies),
            "warnings": len(self.warnings),
        }


@dataclass
class SoftwareRowViewModel:
    """Модель представления строки установленного ПО."""
    name: str
    version: str
    category: str
    run_count: int
    last_launched: str
    install_date: str
    publisher: str

    @classmethod
    def from_app_info(cls, app: InstalledAppInfo) -> "SoftwareRowViewModel":
        """Создать ViewModel из InstalledAppInfo."""
        last_str = "-"
        run_count = 0
        if app.execution_info:
            run_count = app.execution_info.run_count
            if app.execution_info.last_run_time:
                last_str = app.execution_info.last_run_time.strftime("%Y-%m-%d %H:%M")

        return cls(
            name=app.display_name or app.name,
            version=app.version or "-",
            category=app.category.value if isinstance(app.category, AppCategory) else str(app.category),
            run_count=run_count,
            last_launched=last_str,
            install_date=app.install_date or "-",
            publisher=app.publisher or "-",
        )


