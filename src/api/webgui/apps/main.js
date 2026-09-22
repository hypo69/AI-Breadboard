/**
 * Applications Hub Interface Main JS (/apps) — Модульный Оркестратор
 */

import { setupGlobalApi, setupThemeAndLang } from './modules/init-interface.js';
import { setupNavTabs, switchTab, loadTabContent } from './modules/tab-manager.js';
import { fetchAppsStatus, updateModelBadge } from './modules/status-manager.js';
import { APP_TAB_DEFS, TC_EXCLUDES } from './modules/tabs-config.js';
import { applyTranslations } from '../js/i18n.js';

// Экспорт глобальных функций переключения для HTML и плагинов
window.switchTab = switchTab;
window.switchToTab = switchTab;

// Обработчики кнопок верхнего меню (Quick Access)
function setupTopMenuButtons() {
  const topMenuButtons = document.querySelectorAll('.main-nav-container button[data-tab]');
  topMenuButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const tabId = btn.getAttribute('data-tab');
      if (tabId) {
        switchTab(tabId);
      }
    });
  });
}

// Обработчики элементов бокового меню
function setupSidebarButtons() {
  const sidebarButtons = document.querySelectorAll('#appsNavTabs .list-group-item');
  sidebarButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const tabId = btn.getAttribute('data-tab');
      if (tabId) {
        switchTab(tabId);
      }
    });
  });
}

async function initAppsHub() {
  console.log('🚀 [AppsHub] Initializing modular interface...');

  // 1. Инициализация глобального API и темы/языка
  setupGlobalApi();
  await setupThemeAndLang();
  setupNavTabs();
  setupTopMenuButtons();
  setupSidebarButtons();

  const isTcRoute = window.location.pathname.startsWith('/tc');
  if (isTcRoute) {
    document.title = 'AI Breadboard — Test Computer (/tc)';
  }

  // 2. Получение статуса приложений и обновление бейджа модели
  const statusData = await fetchAppsStatus();
  const appsMap = statusData?.apps || {};
  await updateModelBadge(statusData);

  // 3. Загрузка содержимого включенных вкладок (только для тех, что есть в DOM)
  const enabledTabs = [];
  const cb = Date.now();

  // Получаем список вкладок, которые actually отображаются в DOM
  const visibleTabButtons = document.querySelectorAll('#appsNavTabs .list-group-item');
  const visibleTabIds = Array.from(visibleTabButtons).map(btn => btn.dataset.tab);

  APP_TAB_DEFS.forEach((def) => {
    // Пропускаем вкладки, которых нет в DOM (они уже отфильтрованы)
    if (!visibleTabIds.includes(def.tabId)) return;

    const appInfo = appsMap[def.id] || Object.values(appsMap).find(a => a.tab === def.tabId);
    let isEnabled = appInfo ? appInfo.enabled : (!isTcRoute || !TC_EXCLUDES.has(def.id));
    
    if (isTcRoute && appInfo && appInfo.enabled && TC_EXCLUDES.has(def.id) && (!statusData?.config_file || statusData.config_file === 'config.json')) {
      isEnabled = false;
    }

    if (isEnabled) {
      enabledTabs.push(def);
    }
  });

  // 4. Параллельная загрузка содержимого включенных вкладок
  if (enabledTabs.length > 0) {
    const loadPromises = enabledTabs.map(def =>
      loadTabContent(def.tab, `${def.html}?v=${cb}`, `${def.js}?v=${cb}`)
    );
    await Promise.all(loadPromises);
  } else {
    const mainContent = document.getElementById('mainTabContent');
    if (mainContent) {
      const cfgFile = statusData?.config_file || 'config.json';
      mainContent.innerHTML = `
        <div class="card shadow-sm border-secondary-subtle p-4 text-center my-4">
          <div class="mb-2 fs-1 text-warning">🚫</div>
          <h5 class="fw-bold text-white mb-2">Все приложения отключены</h5>
          <p class="text-muted mb-3 small">
            Все приложения в блоке <code>/apps</code> отключены в текущем конфигурационном файле (<code>${cfgFile}</code>).
          </p>
        </div>
      `;
    }
  }

  applyTranslations();

  // 5. Активация начальной вкладки по URL hash или первой активной
  const hash = window.location.hash ? window.location.hash.replace('#', '') : '';
  const hashTabId = hash.startsWith('tab-') ? hash : `tab-${hash}`;
  const isHashEnabled = enabledTabs.some(d => d.tabId === hashTabId || d.tab === hash);

  if (hash && isHashEnabled) {
    switchTab(hashTabId);
  } else if (enabledTabs.length > 0) {
    switchTab(enabledTabs[0].tabId);
  }

  console.log('✅ [AppsHub] Modular interface ready');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAppsHub);
} else {
  initAppsHub();
}
