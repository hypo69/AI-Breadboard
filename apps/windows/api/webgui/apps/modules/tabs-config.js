/**
 * =============================================================================
 * Process Name: Windows Modules - Tabs-Config Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля tabs-config.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/apps/modules/tabs-config.js?v=20261008_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { APP_TAB_DEFS, TC_EXCLUDES } from '/windows/api/webgui/apps/modules/tabs-config.js';
 *
 * File: tabs-config.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/apps/modules
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-10 11:49:00
 * =============================================================================
 */

export const APP_TAB_DEFS = [
  { id: 'about_system', tab: 'about-system', tabId: 'tab-about-system', html: '/html/about_system_tab/index.html?v=20261008_v2', js: '/html/about_system_tab/main.js?v=20261008_v2' },
  { id: 'scenarios', tab: 'scenarios', tabId: 'tab-scenarios', html: '/html/scenarios_tab/index.html?v=20261006_v8', js: '/html/scenarios_tab/main.js?v=20261006_v8' },
  { id: 'chat', tab: 'chat', tabId: 'tab-chat', html: '/html/chat/index.html?v=20260923_v5', js: '/html/chat/main.js?v=20260923_v5' },
  { id: 'network_terminal', tab: 'network', tabId: 'tab-network', html: '/html/network_tab/index.html', js: '/html/network_tab/main.js' },
  { id: 'system_inspector', tab: 'hardware-load-inspector', tabId: 'tab-hardware-load-inspector', html: '/html/system_inspector_tab/index.html?v=20261008_v1', js: '/html/system_inspector_tab/main.js?v=20261008_v1' },
  { id: 'processes_load_inspector', tab: 'processes-load-inspector', tabId: 'tab-processes-load-inspector', html: '/html/processes_load_inspector_tab/index.html?v=20261008_v1', js: '/html/processes_load_inspector_tab/main.js?v=20261008_v1' },
  { id: 'windows_sysadmin', tab: 'windows-admin', tabId: 'tab-windows-admin', html: '/html/windows_admin_tab/index.html?v=20261010_v2', js: '/html/windows_admin_tab/main.js?v=20261010_v2' },
  { id: 'focus_settings', tab: 'focus-settings', tabId: 'tab-focus-settings', html: '/html/focus_settings_tab/index.html?v=20261006_v1', js: '/html/focus_settings_tab/main.js?v=20261006_v1' },
  { id: 'system32_commands', tab: 'system32-commands', tabId: 'tab-system32-commands', html: '/html/system32_commands_tab/index.html?v=20261006_v1', js: '/html/system32_commands_tab/main.js?v=20261006_v1' },
  { id: 'system_control_center', tab: 'system-control', tabId: 'tab-system-control', html: '/html/system_control_tab/index.html?v=20261008_v1', js: '/html/system_control_tab/main.js?v=20261008_v1' },
  { id: 'post_install_wizard', tab: 'post-install-wizard', tabId: 'tab-post-install-wizard', html: '/html/post_install_wizard_tab/index.html?v=20261006_v1', js: '/html/post_install_wizard_tab/main.js?v=20261006_v1' },
  { id: 'maintenance_recovery', tab: 'maintenance-recovery', tabId: 'tab-maintenance-recovery', html: '/html/maintenance_recovery_tab/index.html?v=20261006_v1', js: '/html/maintenance_recovery_tab/main.js?v=20261006_v1' },
  { id: 'system_log_viewer', tab: 'system-logs', tabId: 'tab-system-logs', html: '/html/system_logs_tab/index.html', js: '/html/system_logs_tab/main.js' },
  { id: 'software_audit', tab: 'software-audit', tabId: 'tab-software-audit', html: '/html/software_audit_tab/index.html', js: '/html/software_audit_tab/main.js' },
  { id: 'registry_viewer', tab: 'registry-viewer', tabId: 'tab-registry-viewer', html: '/html/registry_viewer_tab/index.html', js: '/html/registry_viewer_tab/main.js' },
  { id: 'windows_defender', tab: 'defender', tabId: 'tab-defender', html: '/html/defender_tab/index.html?v=20261006_v2', js: '/html/defender_tab/main.js?v=20261006_v2' },
  { id: 'windows_startup_auditor', tab: 'startup-auditor', tabId: 'tab-startup-auditor', html: '/html/startup_auditor_tab/index.html?v=20261006_v15', js: '/html/startup_auditor_tab/main.js?v=20261006_v15' },
  { id: 'windows_backup_manager', tab: 'windows-backup', tabId: 'tab-windows-backup', html: '/html/windows_backup_tab/index.html?v=20261004_v1', js: '/html/windows_backup_tab/main.js?v=20261004_v1' },
  { id: 'hardware_monitor', tab: 'hardware-monitor', tabId: 'tab-hardware-monitor', html: '/html/hardware_monitor_tab/index.html', js: '/html/hardware_monitor_tab/main.js' },
  { id: 'cloudflared_monitor', tab: 'cloudflared', tabId: 'tab-cloudflared', html: '/html/cloudflared_tab/index.html', js: '/html/cloudflared_tab/main.js' },
  { id: 'google_user_desktop', tab: 'google-desktop', tabId: 'tab-google-desktop', html: '/html/google_desktop_tab/index.html', js: '/html/google_desktop_tab/main.js' },
  { id: 'gcloud_monitor', tab: 'gcloud', tabId: 'tab-gcloud', html: '/html/gcloud_tab/index.html', js: '/html/gcloud_tab/main.js' },
  { id: 'website_monitor', tab: 'website-monitor', tabId: 'tab-website-monitor', html: '/html/website_monitor_tab/index.html', js: '/html/website_monitor_tab/main.js' },
  { id: 'trading_terminal', tab: 'trading', tabId: 'tab-trading', html: '/html/trading_tab/index.html', js: '/html/trading_tab/main.js' },
  { id: 'user_assistant', tab: 'user-assistant', tabId: 'tab-user-assistant', html: '/html/user_assistant_tab/index.html', js: '/html/user_assistant_tab/main.js' },
  { id: 'helpdesk', tab: 'helpdesk', tabId: 'tab-helpdesk', html: '/html/helpdesk_tab/index.html', js: '/html/helpdesk_tab/main.js' },
  { id: 'wikipedia_research', tab: 'wikipedia-research', tabId: 'tab-wikipedia-research', html: '/html/wikipedia_research_tab/index.html', js: '/html/wikipedia_research_tab/main.js' },
  { id: 'software_transparency_scanner', tab: 'software-transparency', tabId: 'tab-software-transparency', html: '/html/software_transparency_tab/index.html', js: '/html/software_transparency_tab/main.js' },
  { id: 'user_directories', tab: 'user-directories', tabId: 'tab-user-directories', html: '/html/user_directories_tab/index.html', js: '/html/user_directories_tab/main.js' },
  { id: 'ninite_updater', tab: 'ninite-updater', tabId: 'tab-ninite-updater', html: '/html/ninite_updater_tab/index.html?v=20260924_v2', js: '/html/ninite_updater_tab/main.js?v=20260924_v2' },
  { id: 'file_recovery', tab: 'file-recovery', tabId: 'tab-file-recovery', html: '/html/file_recovery_tab/index.html', js: '/html/file_recovery_tab/main.js' },
  { id: 'file_history_ai_search', tab: 'file-history-search', tabId: 'tab-file-history-search', html: '/html/file_history_ai_search_tab/index.html?v=20260928_v1', js: '/html/file_history_ai_search_tab/main.js?v=20260928_v1' },
  { id: 'telemetry_research', tab: 'telemetry-research', tabId: 'tab-telemetry-research', html: '/html/telemetry_research_tab/index.html?v=20260924_v1', js: '/html/telemetry_research_tab/main.js?v=20260924_v1' },
  { id: 'telemetry_config', tab: 'telemetry-config', tabId: 'tab-telemetry-config', html: '/html/telemetry_config_tab/index.html?v=20261006_v1', js: '/html/telemetry_config_tab/main.js?v=20261006_v1' },
  { id: 'process_leaks', tab: 'process-leaks', tabId: 'tab-process-leaks', html: '/html/process_leaks_tab/index.html?v=20260924_v1', js: '/html/process_leaks_tab/main.js?v=20260924_v1' },
  { id: 'forensics', tab: 'forensics', tabId: 'tab-forensics', html: '/html/forensics_tab/index.html?v=20261006_v2', js: '/html/forensics_tab/main.js?v=20261006_v2' },

  { id: 'throttling', tab: 'throttling', tabId: 'tab-throttling', html: '/html/throttling_tab/index.html?v=20260924_v1', js: '/html/throttling_tab/main.js?v=20260924_v1' },
  { id: 'storage_wear', tab: 'storage-wear', tabId: 'tab-storage-wear', html: '/html/storage_wear_tab/index.html?v=20260924_v1', js: '/html/storage_wear_tab/main.js?v=20260924_v1' },
  { id: 'peripherals', tab: 'peripherals', tabId: 'tab-peripherals', html: '/html/peripherals_tab/index.html?v=20260924_v1', js: '/html/peripherals_tab/main.js?v=20260924_v1' },
  { id: 'rag', tab: 'rag', tabId: 'tab-rag', html: '/html/rag_tab/index.html', js: '/html/rag_tab/main.js' },
  { id: 'pixelrag', tab: 'pixelrag', tabId: 'tab-pixelrag', html: '/html/pixelrag_tab/index.html', js: '/html/pixelrag_tab/main.js' },
  { id: 'models', tab: 'models', tabId: 'tab-models', html: '/html/models_tab/index.html?v=20261010_v1', js: '/html/models_tab/main.js?v=20261010_v1' },
  { id: 'agents', tab: 'agents', tabId: 'tab-agents', html: '/html/agents_tab/index.html', js: '/html/agents_tab/main.js' },
  { id: 'skills', tab: 'skills', tabId: 'tab-skills', html: '/html/skills_tab/index.html', js: '/html/skills_tab/main.js' },
  { id: 'mcp', tab: 'mcp', tabId: 'tab-mcp', html: '/html/mcp_tab/index.html', js: '/html/mcp_tab/main.js' },
  { id: 'ai_benchmark', tab: 'ai-benchmark', tabId: 'tab-ai-benchmark', html: '/html/ai_benchmark_tab/index.html?v=20260926_v1', js: '/html/ai_benchmark_tab/main.js?v=20260926_v1' },

  // Новые модули управления Windows CLI
  { id: 'storage_manager', tab: 'storage-manager', tabId: 'tab-storage-manager', html: '/html/storage_manager_tab/index.html?v=20261001_v1', js: '/html/storage_manager_tab/main.js?v=20261001_v1' },
  { id: 'disk_speed', tab: 'disk-speed', tabId: 'tab-disk-speed', html: '/html/disk_speed_tab/index.html?v=20261004_v1', js: '/html/disk_speed_tab/main.js?v=20261004_v1' },
  { id: 'boot_recovery', tab: 'boot-recovery', tabId: 'tab-boot-recovery', html: '/html/boot_recovery_tab/index.html?v=20261001_v1', js: '/html/boot_recovery_tab/main.js?v=20261001_v1' },
  { id: 'servicing_integrity', tab: 'servicing-integrity', tabId: 'tab-servicing-integrity', html: '/html/servicing_integrity_tab/index.html?v=20261001_v1', js: '/html/servicing_integrity_tab/main.js?v=20261001_v1' },
  { id: 'services_manager', tab: 'services-manager', tabId: 'tab-services-manager', html: '/html/services_manager_tab/index.html?v=20261006_v1', js: '/html/services_manager_tab/main.js?v=20261006_v1' },
  { id: 'task_scheduler', tab: 'task-scheduler', tabId: 'tab-task-scheduler', html: '/html/task_scheduler_tab/index.html?v=20261006_v2', js: '/html/task_scheduler_tab/main.js?v=20261006_v2' },
  { id: 'process_manager', tab: 'process-manager', tabId: 'tab-process-manager', html: '/html/process_manager_tab/index.html?v=20261004_v2', js: '/html/process_manager_tab/main.js?v=20261004_v2' },
  { id: 'firewall_manager', tab: 'firewall-manager', tabId: 'tab-firewall-manager', html: '/html/firewall_manager_tab/index.html?v=20261001_v1', js: '/html/firewall_manager_tab/main.js?v=20261001_v1' },
  { id: 'security_acl', tab: 'security-acl', tabId: 'tab-security-acl', html: '/html/security_acl_tab/index.html?v=20261001_v1', js: '/html/security_acl_tab/main.js?v=20261001_v1' },
  { id: 'performance_tracing', tab: 'performance-tracing', tabId: 'tab-performance-tracing', html: '/html/performance_tracing_tab/index.html?v=20261001_v1', js: '/html/performance_tracing_tab/main.js?v=20261001_v1' },
  { id: 'log_settings', tab: 'log-settings', tabId: 'tab-log-settings', html: '/html/log_settings_tab/index.html?v=20261008_v1', js: '/html/log_settings_tab/main.js?v=20261008_v1' },
  { id: 'software_manager', tab: 'software-manager', tabId: 'tab-software-manager', html: '/html/software_manager_tab/index.html?v=20261004_v2', js: '/html/software_manager_tab/main.js?v=20261004_v2' },
  { id: 'taskbar_controller', tab: 'taskbar-controller', tabId: 'tab-taskbar-controller', html: '/html/taskbar_tab/index.html?v=20261006_v1', js: '/html/taskbar_tab/main.js?v=20261006_v1' },
  { id: 'accounts_identity', tab: 'accounts-identity', tabId: 'tab-accounts-identity', html: '/html/accounts_identity_tab/index.html?v=20261008_v1', js: '/html/accounts_identity_tab/main.js?v=20261008_v1' },
  { id: 'power_lifecycle', tab: 'power-lifecycle', tabId: 'tab-power-lifecycle', html: '/html/power_lifecycle_tab/index.html?v=20261008_v2', js: '/html/power_lifecycle_tab/main.js?v=20261008_v2' },
  { id: 'app_logs', tab: 'app-logs', tabId: 'tab-app-logs', html: '/html/app_logs_tab/index.html?v=20261010_v3', js: '/html/app_logs_tab/main.js?v=20261010_v3' },
];

export const TC_EXCLUDES = new Set([
  'cloudflared_monitor',
  'gcloud_monitor',
  'website_monitor',
  'user_assistant',
  'wikipedia_research',
  'trading_terminal',
  'helpdesk'
]);
