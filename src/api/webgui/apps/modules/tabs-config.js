/**
 * apps/modules/tabs-config.js — Реестр определений вкладок для интерфейса /apps
 */

export const APP_TAB_DEFS = [
  { id: 'about_system', tab: 'about-system', tabId: 'tab-about-system', html: '/html/about_system_tab/index.html', js: '/html/about_system_tab/main.js' },
  { id: 'scenarios', tab: 'scenarios', tabId: 'tab-scenarios', html: '/html/scenarios_tab/index.html', js: '/html/scenarios_tab/main.js' },
  { id: 'chat', tab: 'chat', tabId: 'tab-chat', html: '/html/chat/index.html', js: '/html/chat/main.js' },
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
];

export const TC_EXCLUDES = new Set([
  'network_terminal',
  'cloudflared_monitor',
  'gcloud_monitor',
  'website_monitor',
  'user_assistant',
  'wikipedia_research',
  'trading_terminal',
  'helpdesk'
]);
