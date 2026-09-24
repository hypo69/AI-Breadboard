/**
 * js/main.js — оркестратор главной страницы (run.ps1, маршрут /)
 * Архитектура: UI_ARCHITECTURE.md
 */

import { initI18n, switchLang, applyTranslations } from './i18n.js';
import { initTheme } from './theme.js';
import { initUserSettings } from './userSettings.js';
import { initActivityTracker } from './activityTracker.js';
import { initCacheUI } from './cache-ui.js';
import { switchTab, loadTab, setupTabClicks } from './tab-core.js';
import './api-cache.js'; // Подключаем универсальный API-кеш слой
import './test-api-cache.js'; // Подключаем тестовый скрипт

// Глобальный экспорт для вызова из вкладок
window.switchTab = switchTab;
window.switchToTab = switchTab;
window.applyTranslations = applyTranslations;

// Карта вкладок: имя → [htmlUrl, jsUrl]
// Пути явные — не генерируются из имени
const TABS = {
  'chat':         ['/html/chat/index.html',             '/html/chat/main.js'],
  'rag':          ['/html/rag_tab/index.html',          '/html/rag_tab/main.js'],
  'telegram-rag': ['/html/telegram_rag_tab/index.html', '/html/telegram_rag_tab/main.js'],
  'news':         ['/html/news_tab/index.html',         '/html/news_tab/main.js'],
  'voice':        ['/html/voice_tab/index.html',        '/html/voice_tab/main.js'],
  'plugins':      ['/html/plugins_tab/index.html',      '/html/plugins_tab/main.js'],
  'admin':        ['/html/admin_tab/index.html',        '/html/admin_tab/main.js'],
  'help':         ['/html/help/index.html',             '/html/help/main.js'],
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

// Переопределяем switchTab с lazy-загрузкой
const _switchTab = switchTab;
export async function switchMainTab(tabId) {
  const name = (tabId.startsWith('tab-') ? tabId.slice(4) : tabId);
  await lazyLoad(name);
  _switchTab(tabId);
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

  // 2. i18n
  const lang = localStorage.getItem('app_language') || 'ru';
  await initI18n(lang);
  document.querySelectorAll('.lang-selector').forEach(sel => {
    sel.value = lang;
    sel.addEventListener('change', e => switchLang(e.target.value));
  });

  // 3. Пользователь, активность, кеш
  await initUserSettings();
  initActivityTracker();
  initCacheUI();

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
