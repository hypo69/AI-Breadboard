/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Tab-Registry Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля tab-registry.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/core/tab-registry.js?v=20261006_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { TAB_DEFINITIONS, TabRegistry } from '/src/api/webgui/core/tab-registry.js';
 *
 * File: tab-registry.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/core
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 06:35:00
 * =============================================================================
 */

/**
 * TabRegistry – единый источник правды (SSOT) для всех вкладок WebGUI.
 * Экспортирует методы getAll(), getById(id), getFiltered(appsStatusMap, role).
 */
export const TAB_DEFINITIONS = [
  { id: 'about_system', label: 'О системе', i18nKey: 'auto___d32ca0', icon: 'ℹ️', tab: 'about-system', tabId: 'tab-about-system', html: '/html/about_system_tab/index.html?v=20261006_v4', js: '/html/about_system_tab/main.js?v=20261006_v4' },
  { id: 'scenarios', label: 'Сценарии', i18nKey: 'auto___ddaf0e', icon: '💬', tab: 'scenarios', tabId: 'tab-scenarios', html: '/html/scenarios_tab/index.html?v=20260925_v2', js: '/html/scenarios_tab/main.js?v=20260925_v2' },
  { id: 'chat', label: 'Чат', i18nKey: 'auto___8c77e4', icon: '💬', tab: 'chat', tabId: 'tab-chat', html: '/html/chat/index.html?v=20260923_v5', js: '/html/chat/main.js?v=20260923_v5' },
  { id: 'network_terminal', label: 'Сеть', i18nKey: 'auto___f6df40', icon: '🌐', tab: 'network', tabId: 'tab-network', html: '/html/network_tab/index.html', js: '/html/network_tab/main.js' },
  { id: 'system_inspector', label: 'Инспектор системы', i18nKey: 'auto___4324be', icon: 'bi-graph-up-arrow', tab: 'hardware-load-inspector', tabId: 'tab-hardware-load-inspector', html: '/html/system_inspector_tab/index.html?v=20261006_v1', js: '/html/system_inspector_tab/main.js?v=20261006_v1' },
  { id: 'windows_sysadmin', label: 'Windows Sysadmin', icon: 'bi-server', tab: 'windows-admin', tabId: 'tab-windows-admin', html: '/html/windows_admin_tab/index.html', js: '/html/windows_admin_tab/main.js' },
  { id: 'system_control_center', label: 'System Logs & Activity', icon: 'bi-journal-text', tab: 'system-control', tabId: 'tab-system-control', html: '/html/system_control_tab/index.html?v=20261006_v2', js: '/html/system_control_tab/main.js?v=20261006_v2' },
  { id: 'post_install_wizard', label: 'Post-Install Wizard', icon: '⚡', tab: 'post-install-wizard', tabId: 'tab-post-install-wizard', html: '/html/post_install_wizard_tab/index.html?v=20261006_v1', js: '/html/post_install_wizard_tab/main.js?v=20261006_v1' },
  { id: 'maintenance_recovery', label: 'Maintenance & Recovery', icon: '🛠️', tab: 'maintenance-recovery', tabId: 'tab-maintenance-recovery', html: '/html/maintenance_recovery_tab/index.html?v=20261006_v1', js: '/html/maintenance_recovery_tab/main.js?v=20261006_v1' },
  { id: 'system_log_viewer', label: 'Логи системы', i18nKey: 'auto___6e28ee', icon: '📋', tab: 'system-logs', tabId: 'tab-system-logs', html: '/html/system_logs_tab/index.html', js: '/html/system_logs_tab/main.js' },
  { id: 'software_audit', label: 'Аудит ПО', i18nKey: 'auto___128e2e', icon: '📦', tab: 'software-audit', tabId: 'tab-software-audit', html: '/html/software_audit_tab/index.html', js: '/html/software_audit_tab/main.js' },
  { id: 'registry_viewer', label: 'Registry Viewer', icon: '🗝️', tab: 'registry-viewer', tabId: 'tab-registry-viewer', html: '/html/registry_viewer_tab/index.html', js: '/html/registry_viewer_tab/main.js' },
  { id: 'windows_defender', label: 'Defender Security', icon: 'bi-shield-lock', tab: 'defender', tabId: 'tab-defender', html: '/html/defender_tab/index.html?v=20261004_v1', js: '/html/defender_tab/main.js?v=20261004_v1' },
  { id: 'windows_startup_auditor', label: 'Автозагрузка', i18nKey: 'auto___007983', icon: '🚀', tab: 'startup-auditor', tabId: 'tab-startup-auditor', html: '/html/startup_auditor_tab/index.html', js: '/html/startup_auditor_tab/main.js' },
  { id: 'windows_backup_manager', label: 'Windows Backup', icon: '💾', tab: 'windows-backup', tabId: 'tab-windows-backup', html: '/html/windows_backup_tab/index.html?v=20261004_v1', js: '/html/windows_backup_tab/main.js?v=20261004_v1' },
  { id: 'hardware_monitor', label: 'Мониторинг оборудования', i18nKey: 'auto___8a1c35', icon: 'bi-cpu', tab: 'hardware-monitor', tabId: 'tab-hardware-monitor', html: '/html/hardware_monitor_tab/index.html', js: '/html/hardware_monitor_tab/main.js' },
  { id: 'cloudflared_monitor', label: 'Cloudflared', icon: '☁️', tab: 'cloudflared', tabId: 'tab-cloudflared', html: '/html/cloudflared_tab/index.html', js: '/html/cloudflared_tab/main.js' },
  { id: 'google_user_desktop', label: 'Google User Desktop', icon: '🌐', tab: 'google-desktop', tabId: 'tab-google-desktop', html: '/html/google_desktop_tab/index.html?v=20260928_v2', js: '/html/google_desktop_tab/main.js?v=20260928_v2' },
  { id: 'gcloud_monitor', label: 'Google Cloud', icon: '☁️', tab: 'gcloud', tabId: 'tab-gcloud', html: '/html/gcloud_tab/index.html', js: '/html/gcloud_tab/main.js' },
  { id: 'website_monitor', label: 'Website Intelligence', icon: '📊', tab: 'website-monitor', tabId: 'tab-website-monitor', html: '/html/website_monitor_tab/index.html', js: '/html/website_monitor_tab/main.js' },
  { id: 'trading_terminal', label: 'Trading Terminal', icon: '📈', tab: 'trading', tabId: 'tab-trading', html: '/html/trading_tab/index.html', js: '/html/trading_tab/main.js' },
  { id: 'user_assistant', label: 'User Assistant', icon: '🗓️', tab: 'user-assistant', tabId: 'tab-user-assistant', html: '/html/user_assistant_tab/index.html', js: '/html/user_assistant_tab/main.js' },
  { id: 'helpdesk', label: 'Helpdesk', icon: '🎫', tab: 'helpdesk', tabId: 'tab-helpdesk', html: '/html/helpdesk_tab/index.html', js: '/html/helpdesk_tab/main.js' },
  { id: 'wikipedia_research', label: 'Wikipedia Research', icon: '📖', tab: 'wikipedia-research', tabId: 'tab-wikipedia-research', html: '/html/wikipedia_research_tab/index.html', js: '/html/wikipedia_research_tab/main.js' },
  { id: 'autolog_manager', label: 'Автологи', i18nKey: 'auto___17b9d1', icon: '📝', tab: 'autolog', tabId: 'tab-autolog', html: '/html/autolog_tab/index.html?v=20260925_v2', js: '/html/autolog_tab/main.js?v=20260925_v2' },
  { id: 'software_transparency_scanner', label: 'Transparency Scanner', icon: '🔍', tab: 'software-transparency', tabId: 'tab-software-transparency', html: '/html/software_transparency_tab/index.html?v=20260926_v2', js: '/html/software_transparency_tab/main.js?v=20260926_v2' },
  { id: 'user_directories', label: 'Каталоги пользователя', i18nKey: 'auto___1ddade', icon: '📁', tab: 'user-directories', tabId: 'tab-user-directories', html: '/html/user_directories_tab/index.html', js: '/html/user_directories_tab/main.js' },
  { id: 'ninite_updater', label: 'Ninite Updater', icon: '🔄', tab: 'ninite-updater', tabId: 'tab-ninite-updater', html: '/html/ninite_updater_tab/index.html?v=20260924_v2', js: '/html/ninite_updater_tab/main.js?v=20260924_v2' },
  { id: 'file_recovery', label: 'Восстановление файлов', i18nKey: 'auto___8f9984', icon: '🩹', tab: 'file-recovery', tabId: 'tab-file-recovery', html: '/html/file_recovery_tab/index.html', js: '/html/file_recovery_tab/main.js' },
  { id: 'file_history_ai_search', label: 'Поиск файлов AI', i18nKey: 'auto__ai_2d3bf7', icon: '🔍', tab: 'file-history-search', tabId: 'tab-file-history-search', html: '/html/file_history_ai_search_tab/index.html?v=20260928_v1', js: '/html/file_history_ai_search_tab/main.js?v=20260928_v1' },
  { id: 'telemetry_history', label: 'История телеметрии', i18nKey: 'auto___adb56b', icon: 'bi-graph-up', tab: 'telemetry-history', tabId: 'tab-telemetry-history', html: '/html/telemetry_history_tab/index.html?v=20260924_v1', js: '/html/telemetry_history_tab/main.js?v=20260924_v1' },
  { id: 'telemetry_research', label: 'Исследование телеметрии', i18nKey: 'auto___025fa1', icon: '🔬', tab: 'telemetry-research', tabId: 'tab-telemetry-research', html: '/html/telemetry_research_tab/index.html?v=20260924_v1', js: '/html/telemetry_research_tab/main.js?v=20260924_v1' },
  { id: 'process_leaks', label: 'Утечки процессов', i18nKey: 'auto___6e10ab', icon: '⚠️', tab: 'process-leaks', tabId: 'tab-process-leaks', html: '/html/process_leaks_tab/index.html?v=20260924_v1', js: '/html/process_leaks_tab/main.js?v=20260924_v1' },
  { id: 'forensics', label: 'Форензика', i18nKey: 'auto___82e8f9', icon: '🛡️', tab: 'forensics', tabId: 'tab-forensics', html: '/html/forensics_tab/index.html?v=20260924_v1', js: '/html/forensics_tab/main.js?v=20260924_v1' },
  { id: 'throttling', label: 'Троттлинг', i18nKey: 'auto___23403a', icon: '🌡️', tab: 'throttling', tabId: 'tab-throttling', html: '/html/throttling_tab/index.html?v=20260924_v1', js: '/html/throttling_tab/main.js?v=20260924_v1' },
  { id: 'storage_wear', label: 'Износ дисков', i18nKey: 'auto___5c3dfb', icon: '💽', tab: 'storage-wear', tabId: 'tab-storage-wear', html: '/html/storage_wear_tab/index.html?v=20260924_v1', js: '/html/storage_wear_tab/main.js?v=20260924_v1' },
  { id: 'peripherals', label: 'Периферия', i18nKey: 'auto___b62c2e', icon: '🔌', tab: 'peripherals', tabId: 'tab-peripherals', html: '/html/peripherals_tab/index.html?v=20260924_v1', js: '/html/peripherals_tab/main.js?v=20260924_v1' },
  { id: 'rag', label: 'RAG База знаний', i18nKey: 'auto_rag__829445', icon: '🧠', tab: 'rag', tabId: 'tab-rag', html: '/html/rag_tab/index.html', js: '/html/rag_tab/main.js' },
  { id: 'pixelrag', label: 'PixelRAG', icon: '🖼️', tab: 'pixelrag', tabId: 'tab-pixelrag', html: '/html/pixelrag_tab/index.html', js: '/html/pixelrag_tab/main.js' },
  { id: 'models', label: 'Модели', i18nKey: 'auto___44bfc5', icon: '🤖', tab: 'models', tabId: 'tab-models', html: '/html/models_tab/index.html', js: '/html/models_tab/main.js' },
  { id: 'agents', label: 'Агенты', i18nKey: 'auto___af1850', icon: '🧩', tab: 'agents', tabId: 'tab-agents', html: '/html/agents_tab/index.html', js: '/html/agents_tab/main.js' },
  { id: 'skills', label: 'Навыки', i18nKey: 'auto___56221b', icon: '⚡', tab: 'skills', tabId: 'tab-skills', html: '/html/skills_tab/index.html', js: '/html/skills_tab/main.js' },
  { id: 'mcp', label: 'MCP Серверы', i18nKey: 'auto_mcp__8f43dd', icon: '🔌', tab: 'mcp', tabId: 'tab-mcp', html: '/html/mcp_tab/index.html', js: '/html/mcp_tab/main.js' },
  { id: 'ai_benchmark', label: 'AI Benchmark', icon: '⏱️', tab: 'ai-benchmark', tabId: 'tab-ai-benchmark', html: '/html/ai_benchmark_tab/index.html?v=20260926_v1', js: '/html/ai_benchmark_tab/main.js?v=20260926_v1' }
];

export class TabRegistry {
  static getAll() { return TAB_DEFINITIONS; }
  static getById(tabId) {
    if (!tabId) return null;
    const clean = tabId.replace(/^tab-/, '');
    return TAB_DEFINITIONS.find(t =>
      t.id === clean ||
      t.tab === clean ||
      t.tabId === tabId ||
      t.tabId === `tab-${clean}` ||
      t.appId === clean
    ) || null;
  }
  static getLabel(tab) {
    if (!tab) return '';
    if (tab.i18nKey && typeof window !== 'undefined' && window.i18next?.t) {
      const translated = window.i18next.t(tab.i18nKey);
      if (translated && translated !== tab.i18nKey) return translated;
    }
    return tab.label || '';
  }
  static getFiltered(appsStatusMap = null, targetRole = 'admin') {
    return TAB_DEFINITIONS.filter(tab => {
      if (tab.roles && !tab.roles.includes(targetRole)) return false;
      if (tab.appId && appsStatusMap && appsStatusMap[tab.appId]) {
        return appsStatusMap[tab.appId].enabled !== false;
      }
      return true;
    });
  }
}
