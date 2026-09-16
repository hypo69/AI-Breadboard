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

// Global map of app status
window.appsStatusMap = {};

// Tab Switch Handler
function onTabSwitched(targetId) {
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  if (cleanId === 'tab-chat' && typeof window.initChatTab === 'function') {
    console.log('[AppsHub] Switching to chat tab...');
    window.initChatTab();
    const msgInput = document.getElementById('message-input');
    if (msgInput) msgInput.focus();
  } else if (cleanId === 'tab-network' && typeof window.initNetworkTab === 'function') {
    console.log('[AppsHub] Switching to network tab...');
    window.initNetworkTab();
  } else if (cleanId === 'tab-system-inspector' && typeof window.initSystemInspectorTab === 'function') {
    console.log('[AppsHub] Switching to system inspector tab...');
    window.initSystemInspectorTab();
  } else if (cleanId === 'tab-windows-admin' && typeof window.initWindowsAdminTab === 'function') {
    console.log('[AppsHub] Switching to windows admin tab...');
    window.initWindowsAdminTab();
  } else if (cleanId === 'tab-system-control' && typeof window.initSystemControlTab === 'function') {
    console.log('[AppsHub] Switching to system control tab...');
    window.initSystemControlTab();
  } else if (cleanId === 'tab-system-logs' && typeof window.initSystemLogsTab === 'function') {
    console.log('[AppsHub] Switching to system logs tab...');
    window.initSystemLogsTab();
  } else if (cleanId === 'tab-cloudflared' && typeof window.initCloudflaredTab === 'function') {
    console.log('[AppsHub] Switching to cloudflared tab...');
    window.initCloudflaredTab();
  } else if (cleanId === 'tab-gcloud' && typeof window.initGcloudTab === 'function') {
    console.log('[AppsHub] Switching to gcloud tab...');
    window.initGcloudTab();
  } else if (cleanId === 'tab-website-monitor' && typeof window.initWebsiteMonitorTab === 'function') {
    console.log('[AppsHub] Switching to website monitor tab...');
    window.initWebsiteMonitorTab();
  } else if (cleanId === 'tab-trading' && typeof window.initTradingTab === 'function') {
    console.log('[AppsHub] Switching to trading tab...');
    window.initTradingTab();
  } else if (cleanId === 'tab-user-assistant' && typeof window.initUserAssistantTab === 'function') {
    console.log('[AppsHub] Switching to user assistant tab...');
    window.initUserAssistantTab();
  } else if (cleanId === 'tab-helpdesk' && typeof window.initHelpdeskTab === 'function') {
    console.log('[AppsHub] Switching to helpdesk tab...');
    window.initHelpdeskTab();
  } else if (cleanId === 'tab-wikipedia-research' && typeof window.initWikipediaResearchTab === 'function') {
    console.log('[AppsHub] Switching to wikipedia research tab...');
    window.initWikipediaResearchTab();
  }
}

// Programmatic tab switcher
function switchTab(targetId) {
  if (!targetId) return;
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  const tabId = cleanId.startsWith('tab-') ? cleanId : `tab-${cleanId}`;

  // Check if target is disabled
  const statusEntry = Object.values(window.appsStatusMap || {}).find(a => a.tab === tabId || a.id === cleanId);
  if (statusEntry && statusEntry.enabled === false) {
    console.warn(`[AppsHub] Tab ${tabId} is disabled in configuration, skipping switch.`);
    return;
  }

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

async function fetchAppsStatus() {
  try {
    let data = null;
    try {
      data = await window.api.fetch('/api/apps/status');
    } catch {
      data = await window.api.fetch('/api/admin/apps/status');
    }
    if (data && data.apps) {
      window.appsStatusMap = data.apps;
      return data;
    }
  } catch (err) {
    console.warn('[AppsHub] Could not retrieve /api/apps/status, defaulting to all enabled:', err);
  }
  return null;
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

  // Fetch enabled / disabled status from active config (config.json / config_tc.json)
  const statusData = await fetchAppsStatus();
  const appsMap = statusData?.apps || {};

  // Tab definitions with URL and script routes
  const tabDefs = [
    { id: 'chat', tab: 'chat', tabId: 'tab-chat', html: '/html/chat/index.html', js: '/html/chat/main.js' },
    { id: 'network_terminal', tab: 'network', tabId: 'tab-network', html: '/html/network_tab/index.html', js: '/html/network_tab/main.js' },
    { id: 'system_inspector', tab: 'system-inspector', tabId: 'tab-system-inspector', html: '/html/system_inspector_tab/index.html', js: '/html/system_inspector_tab/main.js' },
    { id: 'windows_sysadmin', tab: 'windows-admin', tabId: 'tab-windows-admin', html: '/html/windows_admin_tab/index.html', js: '/html/windows_admin_tab/main.js' },
    { id: 'system_control_center', tab: 'system-control', tabId: 'tab-system-control', html: '/html/system_control_tab/index.html', js: '/html/system_control_tab/main.js' },
    { id: 'system_log_viewer', tab: 'system-logs', tabId: 'tab-system-logs', html: '/html/system_logs_tab/index.html', js: '/html/system_logs_tab/main.js' },
    { id: 'cloudflared_monitor', tab: 'cloudflared', tabId: 'tab-cloudflared', html: '/html/cloudflared_tab/index.html', js: '/html/cloudflared_tab/main.js' },
    { id: 'gcloud_monitor', tab: 'gcloud', tabId: 'tab-gcloud', html: '/html/gcloud_tab/index.html', js: '/html/gcloud_tab/main.js' },
    { id: 'website_monitor', tab: 'website-monitor', tabId: 'tab-website-monitor', html: '/html/website_monitor_tab/index.html', js: '/html/website_monitor_tab/main.js' },
    { id: 'trading_terminal', tab: 'trading', tabId: 'tab-trading', html: '/html/trading_tab/index.html', js: '/html/trading_tab/main.js' },
    { id: 'user_assistant', tab: 'user-assistant', tabId: 'tab-user-assistant', html: '/html/user_assistant_tab/index.html', js: '/html/user_assistant_tab/main.js' },
    { id: 'helpdesk', tab: 'helpdesk', tabId: 'tab-helpdesk', html: '/html/helpdesk_tab/index.html', js: '/html/helpdesk_tab/main.js' },
    { id: 'wikipedia_research', tab: 'wikipedia-research', tabId: 'tab-wikipedia-research', html: '/html/wikipedia_research_tab/index.html', js: '/html/wikipedia_research_tab/main.js' },
  ];

  const enabledTabs = [];
  const cb = Date.now();

  // Hide disabled application tabs and show enabled ones
  tabDefs.forEach(def => {
    const appInfo = appsMap[def.id] || Object.values(appsMap).find(a => a.tab === def.tabId);
    const isEnabled = appInfo ? appInfo.enabled : true;

    const navBtn = document.querySelector(`#appsNavTabs [data-tab="${def.tabId}"], #appsNavTabs [data-bs-target="#${def.tabId}"]`);
    const navItem = navBtn ? navBtn.closest('.nav-item') : null;
    const pane = document.getElementById(def.tabId);

    if (isEnabled) {
      if (navItem) {
        navItem.style.display = '';
        navItem.classList.remove('d-none');
      }
      if (pane) {
        pane.style.display = '';
      }
      enabledTabs.push(def);
    } else {
      if (navItem) {
        navItem.style.display = 'none';
        navItem.classList.add('d-none');
      }
      if (pane) {
        pane.style.display = 'none';
        pane.classList.remove('show', 'active');
      }
    }
  });

  // Load content only for enabled tabs in parallel
  if (enabledTabs.length > 0) {
    const loadPromises = enabledTabs.map(def =>
      loadTabContent(def.tab, `${def.html}?v=${cb}`, `${def.js}?v=${cb}`)
    );
    await Promise.all(loadPromises);
  } else {
    // If all apps are disabled
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
          <div class="small text-secondary">
            Чтобы включить приложения, установите <code>"enable_all": true</code> или активируйте конкретные приложения в секции <code>"apps"</code> файла <code>${cfgFile}</code>.
          </div>
        </div>
      `;
    }
  }

  applyTranslations();

  // Check initial hash in URL and activate first valid enabled tab
  const hash = window.location.hash ? window.location.hash.replace('#', '') : '';
  const hashTabId = hash.startsWith('tab-') ? hash : `tab-${hash}`;
  const isHashEnabled = enabledTabs.some(d => d.tabId === hashTabId || d.tab === hash);

  if (hash && isHashEnabled) {
    switchTab(hashTabId);
  } else if (enabledTabs.length > 0) {
    switchTab(enabledTabs[0].tabId);
  }

  console.log('Apps Hub interface ready');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAppsHub);
} else {
  initAppsHub();
}
