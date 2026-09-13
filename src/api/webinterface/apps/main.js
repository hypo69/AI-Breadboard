// Applications Hub Interface Main JS (/apps)
import { initI18n, switchLang, applyTranslations } from '../js/i18n.js';
import { initTheme, setTheme, getThemeMode, getResolvedTheme } from '../js/theme.js';

// Make switchLang and theme functions available globally
window.switchLang = switchLang;
window.applyTranslations = applyTranslations;
window.setTheme = setTheme;
window.getThemeMode = getThemeMode;
window.getResolvedTheme = getResolvedTheme;

// Minimal global API module for tabs
window.api = window.api || {
  async fetch(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
      let msg = response.statusText;
      try {
        const data = await response.json();
        if (data && data.detail) {
          if (typeof data.detail === 'string') {
            msg = data.detail;
          } else if (Array.isArray(data.detail)) {
            msg = data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
          } else {
            msg = JSON.stringify(data.detail);
          }
        }
      } catch {}
      throw new Error(`${response.status} ${msg}`);
    }
    return response.json();
  }
};

// Tab Switch Handler
function onTabSwitched(targetId) {
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  if (cleanId === 'tab-trading' && typeof window.initTradingTab === 'function') {
    console.log('[AppsHub] Switching to trading tab...');
    window.initTradingTab();
  } else if (cleanId === 'tab-network' && typeof window.initNetworkTab === 'function') {
    console.log('[AppsHub] Switching to network tab...');
    window.initNetworkTab();
  } else if (cleanId === 'tab-system-inspector' && typeof window.initSystemInspectorTab === 'function') {
    console.log('[AppsHub] Switching to system inspector tab...');
    window.initSystemInspectorTab();
  } else if (cleanId === 'tab-windows-admin' && typeof window.initWindowsAdminTab === 'function') {
    console.log('[AppsHub] Switching to windows admin tab...');
    window.initWindowsAdminTab();
  } else if (cleanId === 'tab-cloudflared' && typeof window.initCloudflaredTab === 'function') {
    console.log('[AppsHub] Switching to cloudflared tab...');
    window.initCloudflaredTab();
  } else if (cleanId === 'tab-user-assistant' && typeof window.initUserAssistantTab === 'function') {
    console.log('[AppsHub] Switching to user assistant tab...');
    window.initUserAssistantTab();
  } else if (cleanId === 'tab-gcloud' && typeof window.initGCloudTab === 'function') {
    console.log('[AppsHub] Switching to gcloud tab...');
    window.initGCloudTab();
  } else if (cleanId === 'tab-website-monitor' && typeof window.initWebsiteMonitorTab === 'function') {
    console.log('[AppsHub] Switching to website monitor tab...');
    window.initWebsiteMonitorTab();
  }
}

// Programmatic tab switcher
function switchTab(targetId) {
  if (!targetId) return;
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  const tabId = cleanId.startsWith('tab-') ? cleanId : `tab-${cleanId}`;

  // 1. Update active state on nav buttons
  document.querySelectorAll('#appsNavTabs .nav-link').forEach((item) => {
    const itemTarget = item.getAttribute('data-tab') || item.getAttribute('data-bs-target')?.replace('#', '');
    if (itemTarget === tabId || itemTarget === cleanId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // 2. Switch tab-pane
  const mainTabContent = document.getElementById('mainTabContent');
  if (mainTabContent) {
    Array.from(mainTabContent.children).forEach((pane) => {
      if (pane.classList.contains('tab-pane')) {
        pane.classList.remove('show', 'active');
      }
    });
  }
  const targetPane = document.getElementById(tabId) || document.getElementById(cleanId);
  if (targetPane) {
    targetPane.classList.add('show', 'active');
  }

  // 3. Update hash in URL
  if (history.replaceState) {
    history.replaceState(null, null, `#${tabId}`);
  }

  // 4. Notify lifecycle callback
  onTabSwitched(tabId);
}
window.switchTab = switchTab;
window.switchToTab = switchTab;

// Setup navigation clicks
function setupNavTabs() {
  const navTabs = document.getElementById('appsNavTabs');
  if (!navTabs) return;

  navTabs.querySelectorAll('.nav-link').forEach((btn) => {
    btn.onclick = (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-tab') || btn.getAttribute('data-bs-target')?.replace('#', '');
      if (targetId) {
        switchTab(targetId);
      }
    };
  });
}

async function loadTabContent(tabName, url, jsOverrideSrc) {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const container = document.getElementById(`tab-${tabName}`);
    if (!container) return;
    container.innerHTML = html;

    // Load JS for the tab
    const cacheBuster = Date.now();
    const scriptSrc = jsOverrideSrc || `/html/${tabName}_tab/main.js?v=${cacheBuster}`;

    await new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = scriptSrc;
      script.onload = () => {
        console.log(`[AppsHub] Loaded JS for ${tabName}`);
        resolve();
      };
      script.onerror = (err) => {
        console.warn(`[AppsHub] Note: No JS loaded for ${tabName} from ${scriptSrc}`);
        resolve();
      };
      document.body.appendChild(script);
    });

    const camelName = tabName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const initFuncName = 'init' + camelName.charAt(0).toUpperCase() + camelName.slice(1) + 'Tab';
    if (typeof window[initFuncName] === 'function') {
      console.log(`[AppsHub] Calling ${initFuncName} for ${tabName}`);
      try {
        await window[initFuncName]();
      } catch (err) {
        console.error(`[AppsHub] Error executing ${initFuncName}:`, err);
      }
    }
  } catch (e) {
    console.error(`[AppsHub] Error loading tab ${tabName}:`, e);
    const container = document.getElementById(`tab-${tabName}`);
    if (container) {
      container.innerHTML = `<div class="alert alert-danger">Ошибка загрузки ${tabName}: ${e.message}</div>`;
    }
  }
}

async function initAppsHub() {
  console.log('Apps Hub interface initializing...');
  initTheme();

  // Setup language
  const savedLang = localStorage.getItem('app_language') || 'ru';
  await initI18n(savedLang);

  const langSel = document.getElementById('apps-lang-selector');
  if (langSel) {
    langSel.value = savedLang;
    langSel.addEventListener('change', (e) => {
      switchLang(e.target.value);
    });
  }

  const themeSel = document.getElementById('apps-theme-selector');
  if (themeSel) {
    themeSel.value = getThemeMode();
    themeSel.addEventListener('change', (e) => {
      setTheme(e.target.value);
    });
  }

  setupNavTabs();

  const cb = Date.now();
  // Load all 8 application tabs in parallel
  await Promise.all([
    loadTabContent('trading', `/html/trading_tab/index.html?v=${cb}`, `/html/trading_tab/main.js?v=${cb}`),
    loadTabContent('network', `/html/network_tab/index.html?v=${cb}`, `/html/network_tab/main.js?v=${cb}`),
    loadTabContent('system-inspector', `/html/system_inspector_tab/index.html?v=${cb}`, `/html/system_inspector_tab/main.js?v=${cb}`),
    loadTabContent('windows-admin', `/html/windows_admin_tab/index.html?v=${cb}`, `/html/windows_admin_tab/main.js?v=${cb}`),
    loadTabContent('user-assistant', `/html/user_assistant_tab/index.html?v=${cb}`, `/html/user_assistant_tab/main.js?v=${cb}`),
    loadTabContent('gcloud', `/html/gcloud_tab/index.html?v=${cb}`, `/html/gcloud_tab/main.js?v=${cb}`),
    loadTabContent('website-monitor', `/html/website_monitor_tab/index.html?v=${cb}`, `/html/website_monitor_tab/main.js?v=${cb}`),
    loadTabContent('cloudflared', `/html/cloudflared_tab/index.html?v=${cb}`, `/html/cloudflared_tab/main.js?v=${cb}`)
  ]);

  applyTranslations();

  // Check initial hash in URL
  const hash = window.location.hash;
  if (hash) {
    switchTab(hash);
  } else {
    onTabSwitched('tab-trading');
  }

  console.log('Apps Hub interface ready');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAppsHub);
} else {
  initAppsHub();
}
