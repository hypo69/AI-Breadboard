/**
 * =============================================================================
 * Process Name: Windows Js - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/js/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { switchMainTab } from '/windows/api/webgui/js/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 10:25:00
 * =============================================================================
 */

/**
 * js/main.js — оркестратор главной страницы (run.ps1, маршрут /)
 * Архитектура: UI_ARCHITECTURE.md
 */

import { initI18n, switchLang, applyTranslations } from './i18n.js';
import { initTheme } from './theme.js';
import { initUserSettings } from './userSettings.js';
import { initActivityTracker } from './activityTracker.js';
import { initCacheUI } from './cache-ui.js';
import { initModelTester, sendModelPing } from './model-tester.js';
import { switchTab, loadTab, setupTabClicks } from './tab-core.js';
import './api-cache.js'; // Подключаем универсальный API-кеш слой
import './test-api-cache.js'; // Подключаем тестовый скрипт

// Глобальный экспорт для вызова из вкладок
window.switchTab = switchTab;
window.switchToTab = switchTab;
window.sendModelPing = sendModelPing;
window.initModelTester = initModelTester;
window.applyTranslations = applyTranslations;

// Карта вкладок: имя → [htmlUrl, jsUrl]
// Пути явные — не генерируются из имени
const TABS = {
  // Базовые ИИ и коммуникации
  'chat':                     ['/html/chat/index.html',                         '/html/chat/main.js'],
  'voice':                    ['/html/voice_tab/index.html',                    '/html/voice_tab/main.js'],
  'scenarios':                ['/html/scenarios_tab/index.html',                '/html/scenarios_tab/main.js'],
  'rag':                      ['/html/rag_tab/index.html',                      '/html/rag_tab/main.js'],
  'telegram-rag':             ['/html/telegram_rag_tab/index.html',             '/html/telegram_rag_tab/main.js'],
  'news':                     ['/html/news_tab/index.html',                     '/html/news_tab/main.js'],
  'models':                   ['/html/models_tab/index.html',                   '/html/models_tab/main.js'],
  'plugins':                  ['/html/plugins_tab/index.html',                  '/html/plugins_tab/main.js'],
  'admin':                    ['/html/admin_tab/index.html',                    '/html/admin_tab/main.js'],
  'help':                     ['/html/help/index.html',                         '/html/help/main.js'],

  // Оборудование, Датчики и Телеметрия
  'about-system':             ['/html/about_system_tab/index.html',             '/html/about_system_tab/main.js'],
  'hardware-monitor':         ['/html/hardware_monitor_tab/index.html',         '/html/hardware_monitor_tab/main.js'],
  'telemetry-research':       ['/html/telemetry_research_tab/index.html',       '/html/telemetry_research_tab/main.js'],
  'ai-benchmark':             ['/html/ai_benchmark_tab/index.html',             '/html/ai_benchmark_tab/main.js'],
  'process-leaks':            ['/html/process_leaks_tab/index.html',            '/html/process_leaks_tab/main.js'],
  'forensics':                ['/html/forensics_tab/index.html',                '/html/forensics_tab/main.js'],
  'throttling':               ['/html/throttling_tab/index.html',               '/html/throttling_tab/main.js'],
  'peripherals':              ['/html/peripherals_tab/index.html',              '/html/peripherals_tab/main.js'],
  'software-transparency':    ['/html/software_transparency_tab/index.html',    '/html/software_transparency_tab/main.js'],

  // Накопители и Диски
  'storage-manager':          ['/html/storage_manager_tab/index.html',          '/html/storage_manager_tab/main.js'],
  'disk-speed':               ['/html/disk_speed_tab/index.html',               '/html/disk_speed_tab/main.js'],
  'storage-wear':             ['/html/storage_wear_tab/index.html',             '/html/storage_wear_tab/main.js'],
  'file-recovery':            ['/html/file_recovery_tab/index.html',            '/html/file_recovery_tab/main.js'],
  'file-history-search':      ['/html/file_history_ai_search_tab/index.html',   '/html/file_history_ai_search_tab/main.js'],

  // Управление Windows и Sysadmin
  'system-control':           ['/html/system_control_tab/index.html',           '/html/system_control_tab/main.js'],
  'post-install-wizard':      ['/html/post_install_wizard_tab/index.html',      '/html/post_install_wizard_tab/main.js'],
  'maintenance-recovery':     ['/html/maintenance_recovery_tab/index.html',     '/html/maintenance_recovery_tab/main.js'],
  'windows-admin':            ['/html/windows_admin_tab/index.html',            '/html/windows_admin_tab/main.js'],
  'focus-settings':           ['/html/focus_settings_tab/index.html',           '/html/focus_settings_tab/main.js'],
  'taskbar-controller':       ['/html/taskbar_tab/index.html',                  '/html/taskbar_tab/main.js'],
  'startup-auditor':          ['/html/startup_auditor_tab/index.html',          '/html/startup_auditor_tab/main.js'],
  'services-manager':         ['/html/services_manager_tab/index.html',         '/html/services_manager_tab/main.js'],
  'task-scheduler':           ['/html/task_scheduler_tab/index.html',           '/html/task_scheduler_tab/main.js'],
  'process-manager':          ['/html/process_manager_tab/index.html',          '/html/process_manager_tab/main.js'],
  'registry-viewer':          ['/html/registry_viewer_tab/index.html',          '/html/registry_viewer_tab/main.js'],
  'software-manager':         ['/html/software_manager_tab/index.html',         '/html/software_manager_tab/main.js'],
  'user-directories':         ['/html/user_directories_tab/index.html',         '/html/user_directories_tab/main.js'],
  'accounts-identity':        ['/html/accounts_identity_tab/index.html',        '/html/accounts_identity_tab/main.js'],

  // Безопасность и Целостность
  'firewall-manager':         ['/html/firewall_manager_tab/index.html',         '/html/firewall_manager_tab/main.js'],
  'defender':                 ['/html/defender_tab/index.html',                 '/html/defender_tab/main.js'],
  'security-acl':             ['/html/security_acl_tab/index.html',             '/html/security_acl_tab/main.js'],
  'servicing-integrity':      ['/html/servicing_integrity_tab/index.html',      '/html/servicing_integrity_tab/main.js'],
  'boot-recovery':            ['/html/boot_recovery_tab/index.html',            '/html/boot_recovery_tab/main.js'],
  'windows-backup':           ['/html/windows_backup_tab/index.html',           '/html/windows_backup_tab/main.js'],

  // Сеть и Системные Логи
  'network':                  ['/html/network_tab/index.html',                  '/html/network_tab/main.js'],
  'performance-tracing':      ['/html/performance_tracing_tab/index.html',      '/html/performance_tracing_tab/main.js'],
  'system-logs':              ['/html/system_logs_tab/index.html',              '/html/system_logs_tab/main.js'],
  'power-lifecycle':          ['/html/power_lifecycle_tab/index.html',          '/html/power_lifecycle_tab/main.js'],
  'app-logs':                 ['/html/app_logs_tab/index.html',                 '/html/app_logs_tab/main.js'],
};

// Lazy-загрузка: вкладка грузится при первом открытии
const loaded = new Set();

async function lazyLoad(tabName) {
  if (loaded.has(tabName) || !TABS[tabName]) return;
  loaded.add(tabName);
  const v = Date.now();
  const [html, js] = TABS[tabName];
  await loadTab(tabName, `${html}?v=${v}`, `${js}?v=${v}`);
  applyTranslations();
}

// Переопределяем switchTab с приоритетной мгновенной навигацией
const _switchTab = switchTab;
export function switchMainTab(tabId) {
  if (!tabId) return;
  // 1. Мгновенное переключение UI без задержки
  _switchTab(tabId);

  // 2. Фоновая асинхронная подгрузка разметки и скрипта вкладки (если еще не загружена)
  const name = (tabId.startsWith('tab-') ? tabId.slice(4) : tabId);
  if (!loaded.has(name) && TABS[name]) {
    lazyLoad(name).catch(err => console.warn(`[Main] Ошибка lazyLoad для ${name}:`, err));
  }
}
window.switchTab = switchMainTab;
window.switchToTab = switchMainTab;

// Открыть плагин по имени (вызывается из плагинов)
window.openPluginFromDropdown = function(pluginName) {
  if (!pluginName) return;
  const n = pluginName.toLowerCase().replace(/-/g, '_');
  if (n === 'telegram_channel_rag' || n === 'telegram_rag') {
    window.switchTab('tab-telegram-rag'); return;
  }
  if (n === 'news_feed' || n === 'news' || n === 'smart_news') {
    window.switchTab('tab-news'); return;
  }
  window.switchTab('tab-plugins');
  const sel = () => window.selectPlugin?.(pluginName);
  sel(); setTimeout(sel, 200);
};

async function init() {
  // 1. Тема
  initTheme();

  // 2. i18n (с автоматическим парсингом URL параметров: ?region=ru-ru, ?locale=ru-RU и т.д.)
  await initI18n();

  // 3. Пользователь, активность, кеш, быстрая проверка модели
  await initUserSettings();
  initActivityTracker();
  initCacheUI();
  initModelTester();

  // 4. Единый обработчик кликов
  setupTabClicks();

  // 5. Загрузить первую вкладку (чат)
  await lazyLoad('chat');
  applyTranslations();

  // 6. Синхронизация видимости плагинов
  try {
    const r = await fetch('/api/admin/plugins');
    if (r.ok) {
      const data = await r.json();
      window.syncPluginTabsVisibility?.(data.plugins);
    }
  } catch {}

  // 7. Активировать вкладку по hash или чат
  const hash = location.hash.replace('#', '');
  await switchMainTab(hash || 'tab-chat');

  // 8. Фоновый WebSocket
  initComputerStream();
}

// Фоновый WebSocket для remote transcript
function initComputerStream() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${location.host}/api/control/ws?role=computer`);
  ws.onmessage = e => {
    try {
      const msg = JSON.parse(e.data);
      if (msg.event === 'transcript') window.handleRemoteTranscript?.(msg.text);
    } catch {}
  };
  ws.onclose = () => setTimeout(initComputerStream, 3000);
}



document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', init)
  : init();
