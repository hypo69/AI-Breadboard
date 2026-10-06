# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - System32 Models
# =============================================================================
# Description:
#   Модели данных, категории, Control Planes и Telemetry Tiers для расширенного
#   каталога системных инструментов Windows 10/11 (%SystemRoot%\System32).
#
# Usage Examples:
#   Python API:
#     from apps.windows.core.system32_models import System32Tool, TelemetryTier, ControlPlaneType
#
#     tool = System32Tool(executable="diskpart.exe", ...)
#
# File: system32_models.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 15:15:00
# =============================================================================

from __future__ import annotations
"""Модели данных, категории, Control Planes и Telemetry Tiers каталога инструментов System32."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TelemetryTier(str, Enum):
    """Градации уровней риска и назначения для AITelemetry Command Registry."""
    OBSERVE = 'OBSERVE'           # 🟢 Безопасное чтение / сбор метрик / аудит
    DIAGNOSE = 'DIAGNOSE'         # 🟡 Диагностика / трассировка / сканирование
    CONTROL = 'CONTROL'           # 🟠 Управление / запуск / остановка / изменение некритичных параметров
    ADMIN = 'ADMIN'               # 🔴 Требует повышенных привилегий (Elevation / UAC / Administrator)
    DESTRUCTIVE = 'DESTRUCTIVE'   # 🔴🔴 Потенциально деструктивно (форматирование, удаление, сброс загрузчика)
    RECOVERY = 'RECOVERY'         # 🛡️ Среда аварийного восстановления / ремонт системы / WinRE


class ControlPlaneType(str, Enum):
    """Слои плоскости управления Windows Control Plane."""
    CLI = 'CLI'                         # Консольные утилиты %SystemRoot%\System32 (*.exe, *.com)
    POWERSHELL = 'POWERSHELL'           # Командлеты PowerShell и модули
    WMI_CIM = 'WMI_CIM'                 # Пространства имен и классы WMI/CIM
    COM = 'COM'                         # OLE/COM интерфейсы и сервисы
    WIN32_API = 'WIN32_API'             # Функции Win32 API в системных DLL
    NATIVE_NT_API = 'NATIVE_NT_API'     # Низкоуровневый Native API (ntdll.dll)
    ETW = 'ETW'                         # Провайдеры и сессии трассировки Event Tracing for Windows
    EVENT_LOG = 'EVENT_LOG'             # Каналы и журнал Windows Event Log
    REGISTRY = 'REGISTRY'               # Ветки реестра (HKLM, HKCU, HKU)
    GUI_MMC_CPL = 'GUI_MMC_CPL'         # Графические оснастки MMC (.msc), апплеты (.cpl), ms-settings:


class SystemToolCategory(str, Enum):
    """Категории каталога инструментов Windows 10/11."""
    SHELLS_EXECUTION = 'shells_execution'                   # 01. SHELLS & COMMAND EXECUTION
    FILES_DIRECTORIES = 'files_directories'                 # 02. FILES & DIRECTORIES
    STORAGE_DISKS = 'storage_disks'                         # 03. STORAGE / DISKS
    VIRTUAL_DISKS_VHD = 'virtual_disks_vhd'                 # 04. VIRTUAL DISKS / VHD / VHDX
    BITLOCKER_ENCRYPTION = 'bitlocker_encryption'           # 05. BITLOCKER / ENCRYPTION
    VSS_BACKUP = 'vss_backup'                               # 06. VOLUME SHADOW COPY / BACKUP
    PROCESSES = 'processes'                                 # 07. PROCESSES
    SERVICES = 'services'                                   # 08. SERVICES
    SCHEDULED_TASKS = 'scheduled_tasks'                     # 09. SCHEDULED TASKS
    REGISTRY = 'registry'                                   # 10. REGISTRY
    ENVIRONMENT_VARS = 'environment_vars'                   # 11. ENVIRONMENT / SYSTEM VARIABLES
    USERS_GROUPS_SESSIONS = 'users_groups_sessions'         # 12. USERS / GROUPS / SESSIONS
    SECURITY_ACCESS_CONTROL = 'security_access_control'     # 13. SECURITY / ACCESS CONTROL
    GROUP_POLICY = 'group_policy'                           # 14. GROUP POLICY
    EVENT_LOG = 'event_log'                                 # 15. EVENT LOG
    ETW_PERFORMANCE_TRACING = 'etw_performance_tracing'     # 16. ETW / PERFORMANCE / TRACING
    NETWORK_BASIC = 'network_basic'                         # 17. NETWORK — BASIC
    NETWORK_NETSH = 'network_netsh'                         # 18. NETWORK — NETSH
    NETWORK_DIAGNOSTICS = 'network_diagnostics'             # 19. NETWORK DIAGNOSTICS
    FIREWALL = 'firewall'                                   # 20. FIREWALL
    DNS = 'dns'                                             # 21. DNS
    TCPIP_ROUTING = 'tcpip_routing'                         # 22. TCP/IP / ROUTING
    WIFI = 'wifi'                                           # 23. WI-FI
    SMB_FILE_SHARING = 'smb_file_sharing'                   # 24. SMB / FILE SHARING
    REMOTE_MANAGEMENT = 'remote_management'                 # 25. REMOTE MANAGEMENT
    RDP = 'rdp'                                             # 26. RDP
    WINDOWS_INSTALLER = 'windows_installer'                 # 27. WINDOWS INSTALLER
    WINDOWS_SERVICING = 'windows_servicing'                 # 28. WINDOWS COMPONENTS / SERVICING
    WINDOWS_FEATURES = 'windows_features'                   # 29. WINDOWS FEATURES
    BOOT = 'boot'                                           # 30. BOOT
    SYSTEM_RECOVERY = 'system_recovery'                     # 31. SYSTEM RECOVERY
    DRIVERS = 'drivers'                                     # 32. DRIVERS
    DEVICE_PNP = 'device_pnp'                               # 33. DEVICE / PNP
    DRIVER_VERIFIER = 'driver_verifier'                     # 34. DRIVER VERIFIER
    SYSTEM_INFORMATION = 'system_information'               # 35. SYSTEM INFORMATION
    HARDWARE_PERFORMANCE = 'hardware_performance'           # 36. HARDWARE / PERFORMANCE
    BENCHMARK_WINSAT = 'benchmark_winsat'                   # 37. WINDOWS EXPERIENCE / BENCHMARK
    TIME_LOCALE = 'time_locale'                             # 38. TIME / LOCALE
    CERTIFICATES_PKI = 'certificates_pki'                   # 39. CERTIFICATES / PKI
    CREDENTIALS = 'credentials'                             # 40. CREDENTIALS
    TPM = 'tpm'                                             # 41. TPM
    PRINTING = 'printing'                                   # 42. PRINTING
    COM_DLL_REGISTRATION = 'com_dll_registration'           # 43. COM / DLL REGISTRATION
    WINDOWS_SCRIPT_HOST = 'windows_script_host'             # 44. WINDOWS SCRIPT HOST
    CMD_BUILTINS = 'cmd_builtins'                           # 45. MS-DOS / CMD BUILTINS
    TEXT_DATA_PROCESSING = 'text_data_processing'           # 46. TEXT / DATA PROCESSING
    ARCHIVING_PACKAGING = 'archiving_packaging'             # 47. ARCHIVING / PACKAGING
    NETWORK_TRANSFER = 'network_transfer'                   # 48. NETWORK TRANSFER
    BITS = 'bits'                                           # 49. BITS
    EVENT_TRACING_DIAGNOSTICS = 'event_tracing_diagnostics' # 50. EVENT TRACING / DIAGNOSTICS
    WINDOWS_ERROR_REPORTING = 'windows_error_reporting'     # 51. WINDOWS ERROR REPORTING
    SIDE_BY_SIDE_SXSTRACE = 'side_by_side_sxstrace'         # 52. SIDE-BY-SIDE / APPLICATION DIAGNOSTICS
    WINDOWS_MANAGEMENT = 'windows_management'               # 53. WINDOWS MANAGEMENT
    WMI_CIM = 'wmi_cim'                                     # 54. WMI / CIM
    WINDOWS_UPDATE_SERVICING = 'windows_update_servicing'   # 55. WINDOWS UPDATE / SERVICING
    DEFENDER_SECURITY = 'defender_security'                 # 56. WINDOWS DEFENDER / SECURITY
    FIREWALL_WFP = 'firewall_wfp'                           # 57. WINDOWS FIREWALL / WFP
    FILE_SYSTEM_SECURITY = 'file_system_security'           # 58. FILE SYSTEM SECURITY
    FS_JOURNAL_USN = 'fs_journal_usn'                       # 59. FILE SYSTEM JOURNAL / USN
    VOLUME_MANAGEMENT = 'volume_management'                 # 60. VOLUME MANAGEMENT
    WINRE_RECOVERY = 'winre_recovery'                       # 61. WINDOWS RECOVERY ENVIRONMENT
    BACKUP_RESTORE = 'backup_restore'                       # 62. BACKUP / RESTORE
    SYSTEM_CONFIGURATION = 'system_configuration'           # 63. SYSTEM CONFIGURATION
    CONTROL_PANEL_CPL = 'control_panel_cpl'                 # 64. CONTROL PANEL
    MMC_MANAGEMENT_MSC = 'mmc_management_msc'               # 65. MMC MANAGEMENT CONSOLES
    SHUTDOWN_SESSION_CONTROL = 'shutdown_session_control'   # 66. SHUTDOWN / SESSION CONTROL


class AccessType(str, Enum):
    """Тип доступа инструмента (чтение, запись, комбинированный)."""
    READ = 'READ'
    WRITE = 'WRITE'
    READ_WRITE = 'READ_WRITE'


class ToolPrivilegeLevel(str, Enum):
    """Требуемые системные привилегии."""
    STANDARD = 'STANDARD'
    ADMINISTRATOR = 'ADMINISTRATOR'
    SYSTEM = 'SYSTEM'


class ToolDangerLevel(str, Enum):
    """Уровень опасности инструмента / операции."""
    SAFE = 'SAFE'
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


@dataclass
class System32Tool:
    """Полное описание системного инструмента, оснастки или встроенной команды Windows."""
    executable: str
    category: SystemToolCategory
    category_code: str
    purpose: str
    access_type: AccessType
    required_privileges: ToolPrivilegeLevel
    danger_level: ToolDangerLevel
    telemetry_tier: TelemetryTier = TelemetryTier.OBSERVE
    primary_control_plane: ControlPlaneType = ControlPlaneType.CLI
    native_api_equivalent: Optional[str] = None
    native_nt_api_equivalent: Optional[str] = None
    powershell_equivalent: Optional[str] = None
    wmi_cim_equivalent: Optional[str] = None
    com_equivalent: Optional[str] = None
    etw_provider_equivalent: Optional[str] = None
    event_log_channel_equivalent: Optional[str] = None
    can_run_unattended: bool = True
    can_monitor: bool = False
    can_modify_system: bool = False
    is_gui: bool = False
    is_msc_console: bool = False
    is_cpl_applet: bool = False
    is_cmd_builtin: bool = False
    etw_pipeline_enabled: bool = False
    usn_journal_enabled: bool = False
    command_templates: List[str] = field(default_factory=list)
    subcommands_info: Dict[str, str] = field(default_factory=dict)
    subcommands_tree: Dict[str, List[str]] = field(default_factory=dict)
    rest_endpoint: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование описания инструмента в словарь."""
        res = asdict(self)
        res['category'] = self.category.value
        res['access_type'] = self.access_type.value
        res['required_privileges'] = self.required_privileges.value
        res['danger_level'] = self.danger_level.value
        res['telemetry_tier'] = self.telemetry_tier.value
        res['primary_control_plane'] = self.primary_control_plane.value
        return res


class System32QueryFilter(BaseModel):
    """Фильтры для поиска и выборки системных инструментов."""
    category: Optional[SystemToolCategory] = Field(None, description='Фильтр по системной категории')
    access_type: Optional[AccessType] = Field(None, description='Тип доступа (READ, WRITE, READ_WRITE)')
    required_privileges: Optional[ToolPrivilegeLevel] = Field(None, description='Требуемые системные привилегии')
    danger_level: Optional[ToolDangerLevel] = Field(None, description='Уровень риска')
    telemetry_tier: Optional[TelemetryTier] = Field(None, description='Уровень AITelemetry Tier (OBSERVE, DIAGNOSE, etc.)')
    primary_control_plane: Optional[ControlPlaneType] = Field(None, description='Слой Control Plane (CLI, PS, WMI, COM)')
    can_run_unattended: Optional[bool] = Field(None, description='Возможность фонового выполнения')
    can_monitor: Optional[bool] = Field(None, description='Пригоден ли для мониторинга/сбора метрик')
    can_modify_system: Optional[bool] = Field(None, description='Модифицирует ли настройки или состояние ОС')
    etw_pipeline_enabled: Optional[bool] = Field(None, description='Интегрирован ли в конвейер ETW / AITelemetry')
    usn_journal_enabled: Optional[bool] = Field(None, description='Работает ли с NTFS USN Journal')
    is_cmd_builtin: Optional[bool] = Field(None, description='Встроенная команда CMD (assoc, copy, dir...)')
    search_query: Optional[str] = Field(None, description='Поисковая строка по имени, назначению, подкомандам или тегам')


class System32CatalogSummary(BaseModel):
    """Сводная статистика каталога инструментов System32."""
    total_tools: int
    categories_count: int
    control_planes_count: int
    read_tools_count: int
    write_tools_count: int
    read_write_tools_count: int
    monitoring_tools_count: int
    etw_tools_count: int
    usn_journal_tools_count: int
    gui_tools_count: int
    msc_consoles_count: int
    cpl_applets_count: int
    cmd_builtins_count: int
    by_category: Dict[str, int]
    by_danger_level: Dict[str, int]
    by_privileges: Dict[str, int]
    by_telemetry_tier: Dict[str, int]
    by_control_plane: Dict[str, int]


__all__ = [
    'TelemetryTier',
    'ControlPlaneType',
    'SystemToolCategory',
    'AccessType',
    'ToolPrivilegeLevel',
    'ToolDangerLevel',
    'System32Tool',
    'System32QueryFilter',
    'System32CatalogSummary',
]
