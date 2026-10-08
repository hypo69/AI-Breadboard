# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Tools Package Root
# =============================================================================
# Description:
#   Пакет инструментов Windows для ИИ-агентов (core + native FFI).
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:18:00
# =============================================================================

from __future__ import annotations
"""Пакет инструментов Windows для ИИ-агентов (core + identity + backup + boot + defender + event_logs + firewall + focus + hardware + network + performance_tracing + personalization + process_manager + programms_history + registry + security_acl + services_manager + servicing_integrity + software_manager + startup + native FFI)."""

from src.ai.agents.windows_tools.core import (
    windows_collector_audit,
    windows_execute_atomic_op,
    windows_manage_service,
    windows_manage_process,
    windows_manage_restore_point,
    windows_manage_sys_param,
    windows_safe_probe,
    windows_execute_powershell,
    windows_manage_optional_feature,
    windows_manage_accounts_identity,
    WINDOWS_CORE_TOOLS,
)

from src.ai.agents.windows_tools.identity import (
    windows_identity_explain,
    windows_identity_explain_pid,
    windows_identity_audit_security,
    windows_identity_manage_account,
    windows_identity_audit_events,
    windows_identity_graph_build,
    WINDOWS_IDENTITY_TOOLS,
)

from src.ai.agents.windows_tools.backup import (
    windows_backup_health_check,
    windows_backup_file_history,
    windows_backup_vss_snapshots,
    windows_backup_user_folders,
    windows_backup_version_control,
    WINDOWS_BACKUP_TOOLS,
)

from src.ai.agents.windows_tools.boot import (
    windows_boot_recovery_audit,
    windows_boot_recovery_action,
    WINDOWS_BOOT_TOOLS,
)

from src.ai.agents.windows_tools.defender import (
    windows_defender_status_scan,
    windows_defender_audit_security,
    windows_defender_ai_diagnostics,
    WINDOWS_DEFENDER_TOOLS,
)

from src.ai.agents.windows_tools.event_logs import (
    windows_event_log_query,
    windows_event_log_intelligence,
    windows_event_log_action,
    WINDOWS_EVENT_LOGS_TOOLS,
)

from src.ai.agents.windows_tools.firewall import (
    windows_firewall_audit,
    windows_firewall_rule_action,
    WINDOWS_FIREWALL_TOOLS,
)

from src.ai.agents.windows_tools.focus import (
    windows_focus_status_profiles,
    windows_focus_session_action,
    windows_focus_notifications,
    WINDOWS_FOCUS_TOOLS,
)

from src.ai.agents.windows_tools.hardware import (
    windows_hardware_monitor,
    windows_hardware_inventory,
    windows_hardware_benchmark,
    WINDOWS_HARDWARE_TOOLS,
)

from src.ai.agents.windows_tools.network import (
    windows_network_scan_lan,
    windows_network_usage_stats,
    windows_network_speedtest,
    WINDOWS_NETWORK_TOOLS,
)

from src.ai.agents.windows_tools.performance_tracing import (
    windows_performance_tracing_audit,
    windows_performance_collector_action,
    WINDOWS_PERFORMANCE_TRACING_TOOLS,
)

from src.ai.agents.windows_tools.personalization import (
    windows_personalization_overview,
    windows_personalization_theme_action,
    windows_personalization_cursor_wallpaper,
    WINDOWS_PERSONALIZATION_TOOLS,
)

from src.ai.agents.windows_tools.process_manager import (
    windows_process_list,
    windows_process_action,
    WINDOWS_PROCESS_TOOLS,
)

from src.ai.agents.windows_tools.programms_history import (
    windows_programs_history_report,
    windows_programs_history_audit,
    WINDOWS_PROGRAMS_HISTORY_TOOLS,
)

from src.ai.agents.windows_tools.registry import (
    windows_registry_read,
    windows_registry_search,
    windows_registry_action,
    WINDOWS_REGISTRY_TOOLS,
)

from src.ai.agents.windows_tools.security_acl import (
    windows_security_acl_audit,
    windows_security_acl_action,
    WINDOWS_SECURITY_ACL_TOOLS,
)

from src.ai.agents.windows_tools.services_manager import (
    windows_services_list,
    windows_services_action,
    WINDOWS_SERVICES_MANAGER_TOOLS,
)

from src.ai.agents.windows_tools.servicing_integrity import (
    windows_servicing_integrity_audit,
    windows_servicing_integrity_action,
    WINDOWS_SERVICING_INTEGRITY_TOOLS,
)

from src.ai.agents.windows_tools.software_manager import (
    windows_software_list,
    windows_software_action,
    WINDOWS_SOFTWARE_MANAGER_TOOLS,
)

from src.ai.agents.windows_tools.startup import (
    windows_startup_audit,
    windows_startup_action,
    WINDOWS_STARTUP_TOOLS,
)

from src.ai.agents.windows_tools.storage_manager import (
    windows_storage_audit,
    windows_storage_action,
    WINDOWS_STORAGE_MANAGER_TOOLS,
)

from src.ai.agents.windows_tools.sysadmin import (
    windows_sysadmin_audit,
    windows_sysadmin_action,
    WINDOWS_SYSADMIN_TOOLS,
)

from src.ai.agents.windows_tools.system_checkpoints import (
    windows_checkpoints_audit,
    windows_checkpoints_action,
    WINDOWS_SYSTEM_CHECKPOINTS_TOOLS,
)

from src.ai.agents.windows_tools.system_control_center import (
    windows_system_control_audit,
    windows_system_control_action,
    WINDOWS_SYSTEM_CONTROL_CENTER_TOOLS,
)

from src.ai.agents.windows_tools.task_scheduler import (
    windows_task_scheduler_audit,
    windows_task_scheduler_action,
    WINDOWS_TASK_SCHEDULER_TOOLS,
)

from src.ai.agents.windows_tools.taskbar import (
    windows_taskbar_audit,
    windows_taskbar_action,
    WINDOWS_TASKBAR_TOOLS,
)

from src.ai.agents.windows_tools.window_control_plane import (
    windows_control_plane_audit,
    windows_control_plane_action,
    WINDOWS_WINDOW_CONTROL_PLANE_TOOLS,
)

from src.ai.agents.windows_tools.native import (
    windows_native_event_log_query,
    windows_native_network_sockets,
    windows_native_pnp_devices,
    windows_native_services_enum,
    windows_native_tasks_enum,
    windows_native_error_decode,
    windows_native_performance_counters,
    WINDOWS_NATIVE_FFI_TOOLS,
)

WINDOWS_NATIVE_TOOLS = WINDOWS_CORE_TOOLS + WINDOWS_IDENTITY_TOOLS + WINDOWS_BACKUP_TOOLS + WINDOWS_BOOT_TOOLS + WINDOWS_DEFENDER_TOOLS + WINDOWS_EVENT_LOGS_TOOLS + WINDOWS_FIREWALL_TOOLS + WINDOWS_FOCUS_TOOLS + WINDOWS_HARDWARE_TOOLS + WINDOWS_NETWORK_TOOLS + WINDOWS_PERFORMANCE_TRACING_TOOLS + WINDOWS_PERSONALIZATION_TOOLS + WINDOWS_PROCESS_TOOLS + WINDOWS_PROGRAMS_HISTORY_TOOLS + WINDOWS_REGISTRY_TOOLS + WINDOWS_SECURITY_ACL_TOOLS + WINDOWS_SERVICES_MANAGER_TOOLS + WINDOWS_SERVICING_INTEGRITY_TOOLS + WINDOWS_SOFTWARE_MANAGER_TOOLS + WINDOWS_STARTUP_TOOLS + WINDOWS_STORAGE_MANAGER_TOOLS + WINDOWS_SYSADMIN_TOOLS + WINDOWS_SYSTEM_CHECKPOINTS_TOOLS + WINDOWS_SYSTEM_CONTROL_CENTER_TOOLS + WINDOWS_TASK_SCHEDULER_TOOLS + WINDOWS_TASKBAR_TOOLS + WINDOWS_WINDOW_CONTROL_PLANE_TOOLS + WINDOWS_NATIVE_FFI_TOOLS

__all__ = [
    'windows_collector_audit',
    'windows_execute_atomic_op',
    'windows_manage_service',
    'windows_manage_process',
    'windows_manage_restore_point',
    'windows_manage_sys_param',
    'windows_safe_probe',
    'windows_execute_powershell',
    'windows_manage_optional_feature',
    'windows_manage_accounts_identity',
    'windows_identity_explain',
    'windows_identity_explain_pid',
    'windows_identity_audit_security',
    'windows_identity_manage_account',
    'windows_identity_audit_events',
    'windows_identity_graph_build',
    'windows_backup_health_check',
    'windows_backup_file_history',
    'windows_backup_vss_snapshots',
    'windows_backup_user_folders',
    'windows_backup_version_control',
    'windows_boot_recovery_audit',
    'windows_boot_recovery_action',
    'windows_defender_status_scan',
    'windows_defender_audit_security',
    'windows_defender_ai_diagnostics',
    'windows_event_log_query',
    'windows_event_log_intelligence',
    'windows_event_log_action',
    'windows_firewall_audit',
    'windows_firewall_rule_action',
    'windows_focus_status_profiles',
    'windows_focus_session_action',
    'windows_focus_notifications',
    'windows_hardware_monitor',
    'windows_hardware_inventory',
    'windows_hardware_benchmark',
    'windows_network_scan_lan',
    'windows_network_usage_stats',
    'windows_network_speedtest',
    'windows_performance_tracing_audit',
    'windows_performance_collector_action',
    'windows_personalization_overview',
    'windows_personalization_theme_action',
    'windows_personalization_cursor_wallpaper',
    'windows_process_list',
    'windows_process_action',
    'windows_programs_history_report',
    'windows_programs_history_audit',
    'windows_registry_read',
    'windows_registry_search',
    'windows_registry_action',
    'windows_security_acl_audit',
    'windows_security_acl_action',
    'windows_services_list',
    'windows_services_action',
    'windows_servicing_integrity_audit',
    'windows_servicing_integrity_action',
    'windows_software_list',
    'windows_software_action',
    'windows_startup_audit',
    'windows_startup_action',
    'windows_storage_audit',
    'windows_storage_action',
    'windows_sysadmin_audit',
    'windows_sysadmin_action',
    'windows_checkpoints_audit',
    'windows_checkpoints_action',
    'windows_system_control_audit',
    'windows_system_control_action',
    'windows_task_scheduler_audit',
    'windows_task_scheduler_action',
    'windows_taskbar_audit',
    'windows_taskbar_action',
    'windows_control_plane_audit',
    'windows_control_plane_action',
    'windows_native_event_log_query',
    'windows_native_network_sockets',
    'windows_native_pnp_devices',
    'windows_native_services_enum',
    'windows_native_tasks_enum',
    'windows_native_error_decode',
    'windows_native_performance_counters',
    'WINDOWS_CORE_TOOLS',
    'WINDOWS_IDENTITY_TOOLS',
    'WINDOWS_BACKUP_TOOLS',
    'WINDOWS_BOOT_TOOLS',
    'WINDOWS_DEFENDER_TOOLS',
    'WINDOWS_EVENT_LOGS_TOOLS',
    'WINDOWS_FIREWALL_TOOLS',
    'WINDOWS_FOCUS_TOOLS',
    'WINDOWS_HARDWARE_TOOLS',
    'WINDOWS_NETWORK_TOOLS',
    'WINDOWS_PERFORMANCE_TRACING_TOOLS',
    'WINDOWS_PERSONALIZATION_TOOLS',
    'WINDOWS_PROCESS_TOOLS',
    'WINDOWS_PROGRAMS_HISTORY_TOOLS',
    'WINDOWS_REGISTRY_TOOLS',
    'WINDOWS_SECURITY_ACL_TOOLS',
    'WINDOWS_SERVICES_MANAGER_TOOLS',
    'WINDOWS_SERVICING_INTEGRITY_TOOLS',
    'WINDOWS_SOFTWARE_MANAGER_TOOLS',
    'WINDOWS_STARTUP_TOOLS',
    'WINDOWS_STORAGE_MANAGER_TOOLS',
    'WINDOWS_SYSADMIN_TOOLS',
    'WINDOWS_SYSTEM_CHECKPOINTS_TOOLS',
    'WINDOWS_SYSTEM_CONTROL_CENTER_TOOLS',
    'WINDOWS_TASK_SCHEDULER_TOOLS',
    'WINDOWS_TASKBAR_TOOLS',
    'WINDOWS_WINDOW_CONTROL_PLANE_TOOLS',
    'WINDOWS_NATIVE_FFI_TOOLS',
    'WINDOWS_NATIVE_TOOLS',
]










