/**
 * apps/modules/tabs-config.js — Реестр определений вкладок для интерфейса /apps
 */

export const APP_TAB_DEFS = [
  { id: 'about_system', tab: 'about-system', tabId: 'tab-about-system', html: '/html/about_system_tab/index.html?v=20260924_v4', js: '/html/about_system_tab/main.js?v=20260924_v4' },
  { id: 'scenarios', tab: 'scenarios', tabId: 'tab-scenarios', html: '/html/scenarios_tab/index.html?v=20260924_v2', js: '/html/scenarios_tab/main.js?v=20260924_v2' },
  { id: 'chat', tab: 'chat', tabId: 'tab-chat', html: '/html/chat/index.html?v=20260923_v5', js: '/html/chat/main.js?v=20260923_v5' },
  { id: 'network_terminal', tab: 'network', tabId: 'tab-network', html: '/html/network_tab/index.html', js: '/html/network_tab/main.js' },
  { id: 'system_inspector', tab: 'system-inspector', tabId: 'tab-system-inspector', html: '/html/system_inspector_tab/index.html', js: '/html/system_inspector_tab/main.js' },
  { id: 'windows_sysadmin', tab: 'windows-admin', tabId: 'tab-windows-admin', html: '/html/windows_admin_tab/index.html', js: '/html/windows_admin_tab/main.js' },
  { id: 'system_control_center', tab: 'system-control', tabId: 'tab-system-control', html: '/html/system_control_tab/index.html', js: '/html/system_control_tab/main.js' },
  { id: 'system_log_viewer', tab: 'system-logs', tabId: 'tab-system-logs', html: '/html/system_logs_tab/index.html', js: '/html/system_logs_tab/main.js' },
  { id: 'software_audit', tab: 'software-audit', tabId: 'tab-software-audit', html: '/html/software_audit_tab/index.html', js: '/html/software_audit_tab/main.js' },
  { id: 'registry_viewer', tab: 'registry-viewer', tabId: 'tab-registry-viewer', html: '/html/registry_viewer_tab/index.html', js: '/html/registry_viewer_tab/main.js' },
  { id: 'windows_defender', tab: 'defender', tabId: 'tab-defender', html: '/html/defender_tab/index.html', js: '/html/defender_tab/main.js' },
  { id: 'windows_startup_auditor', tab: 'startup-auditor', tabId: 'tab-startup-auditor', html: '/html/startup_auditor_tab/index.html', js: '/html/startup_auditor_tab/main.js' },
  { id: 'windows_backup_manager', tab: 'windows-backup', tabId: 'tab-windows-backup', html: '/html/windows_backup_tab/index.html', js: '/html/windows_backup_tab/main.js' },
  { id: 'hardware_monitor', tab: 'hardware-monitor', tabId: 'tab-hardware-monitor', html: '/html/hardware_monitor_tab/index.html', js: '/html/hardware_monitor_tab/main.js' },
  { id: 'cloudflared_monitor', tab: 'cloudflared', tabId: 'tab-cloudflared', html: '/html/cloudflared_tab/index.html', js: '/html/cloudflared_tab/main.js' },
  { id: 'gcloud_monitor', tab: 'gcloud', tabId: 'tab-gcloud', html: '/html/gcloud_tab/index.html', js: '/html/gcloud_tab/main.js' },
  { id: 'website_monitor', tab: 'website-monitor', tabId: 'tab-website-monitor', html: '/html/website_monitor_tab/index.html', js: '/html/website_monitor_tab/main.js' },
  { id: 'trading_terminal', tab: 'trading', tabId: 'tab-trading', html: '/html/trading_tab/index.html', js: '/html/trading_tab/main.js' },
  { id: 'user_assistant', tab: 'user-assistant', tabId: 'tab-user-assistant', html: '/html/user_assistant_tab/index.html', js: '/html/user_assistant_tab/main.js' },
  { id: 'helpdesk', tab: 'helpdesk', tabId: 'tab-helpdesk', html: '/html/helpdesk_tab/index.html', js: '/html/helpdesk_tab/main.js' },
  { id: 'wikipedia_research', tab: 'wikipedia-research', tabId: 'tab-wikipedia-research', html: '/html/wikipedia_research_tab/index.html', js: '/html/wikipedia_research_tab/main.js' },
  { id: 'autolog_manager', tab: 'autolog', tabId: 'tab-autolog', html: '/html/autolog_tab/index.html', js: '/html/autolog_tab/main.js' },
  { id: 'software_transparency_scanner', tab: 'software-transparency', tabId: 'tab-software-transparency', html: '/html/software_transparency_tab/index.html', js: '/html/software_transparency_tab/main.js' },
  { id: 'user_directories', tab: 'user-directories', tabId: 'tab-user-directories', html: '/html/user_directories_tab/index.html', js: '/html/user_directories_tab/main.js' },
  { id: 'ninite_updater', tab: 'ninite-updater', tabId: 'tab-ninite-updater', html: '/html/ninite_updater_tab/index.html?v=20260924_v2', js: '/html/ninite_updater_tab/main.js?v=20260924_v2' },
  { id: 'file_recovery', tab: 'file-recovery', tabId: 'tab-file-recovery', html: '/html/file_recovery_tab/index.html', js: '/html/file_recovery_tab/main.js' },
  { id: 'telemetry_history', tab: 'telemetry-history', tabId: 'tab-telemetry-history', html: '/html/telemetry_history_tab/index.html?v=20260924_v1', js: '/html/telemetry_history_tab/main.js?v=20260924_v1' },
  { id: 'rag', tab: 'rag', tabId: 'tab-rag', html: '/html/rag_tab/index.html', js: '/html/rag_tab/main.js' },
  { id: 'pixelrag', tab: 'pixelrag', tabId: 'tab-pixelrag', html: '/html/pixelrag_tab/index.html', js: '/html/pixelrag_tab/main.js' },
  { id: 'models', tab: 'models', tabId: 'tab-models', html: '/html/models_tab/index.html', js: '/html/models_tab/main.js' },
  { id: 'agents', tab: 'agents', tabId: 'tab-agents', html: '/html/agents_tab/index.html', js: '/html/agents_tab/main.js' },
  { id: 'skills', tab: 'skills', tabId: 'tab-skills', html: '/html/skills_tab/index.html', js: '/html/skills_tab/main.js' },
  { id: 'mcp', tab: 'mcp', tabId: 'tab-mcp', html: '/html/mcp_tab/index.html', js: '/html/mcp_tab/main.js' },
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
