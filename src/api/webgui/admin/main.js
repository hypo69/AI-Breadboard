// Admin Interface Main JS
import { initI18n, switchLang, applyTranslations } from '../js/i18n.js';
import { initTheme, setTheme, getThemeMode, getResolvedTheme } from '../js/theme.js';
import { initUserSettings, refreshUserProfile } from '../js/userSettings.js';

// Make switchLang and theme functions available globally
window.switchLang = switchLang;
window.applyTranslations = applyTranslations;
window.setTheme = setTheme;
window.getThemeMode = getThemeMode;
window.getResolvedTheme = getResolvedTheme;
window.initUserSettings = initUserSettings;
window.refreshUserProfile = refreshUserProfile;

// Helper to open plugin from top navbar dropdown
window.openPluginFromDropdown = function(pluginName) {
  if (!pluginName) return;
  document.querySelectorAll('#mainTabs .dropdown-menu.show').forEach((m) => {
    m.classList.remove('show');
    m.closest('.dropdown')?.querySelector('.dropdown-toggle')?.classList.remove('show');
  });

  const normalized = pluginName.toLowerCase().replace(/-/g, '_');

  if (normalized === 'telegram_channel_rag' || normalized === 'telegram_rag') {
    const pane = document.getElementById('tab-telegram-rag') || document.getElementById('tab-telegram_rag');
    if (pane && typeof window.switchTab === 'function') {
      window.switchTab('tab-telegram-rag');
      return;
    }
  }

  if (normalized === 'news_feed' || normalized === 'news' || normalized === 'smart_news' || normalized === 'smart_feed_news') {
    const pane = document.getElementById('tab-news');
    if (pane && typeof window.switchTab === 'function') {
      window.switchTab('tab-news');
      return;
    }
  }

  if (typeof window.switchTab === 'function') {
    window.switchTab('tab-plugins');
  }

  const select = () => {
    if (typeof window.selectPlugin === 'function') {
      window.selectPlugin(pluginName);
    }
  };

  select();
  setTimeout(select, 150);
  setTimeout(select, 400);
};

// API module
window.api = {
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
  },
  
  // User management API
  users: {
    async list(params = {}) {
      const q = new URLSearchParams(params).toString();
      return window.api.fetch(`/api/admin/users${q ? '?' + q : ''}`);
    },
    
    async get(userId) {
      return window.api.fetch(`/api/admin/users/${userId}`);
    },

    async create(data) {
      return window.api.fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },
    
    async update(userId, data) {
      return window.api.fetch(`/api/admin/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },

    async setPassword(userId, password) {
      return window.api.fetch(`/api/admin/users/${userId}/password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
    },

    async toggleActive(userId) {
      return window.api.fetch(`/api/admin/users/${userId}/toggle-active`, {
        method: 'POST'
      });
    },

    async toggleRole(userId) {
      return window.api.fetch(`/api/admin/users/${userId}/toggle-role`, {
        method: 'POST'
      });
    },
    
    async delete(userId) {
      return window.api.fetch(`/api/admin/users/${userId}`, {
        method: 'DELETE'
      });
    }
  },

  // Skills management API
  skills: {
    async list(params = {}) {
      const q = new URLSearchParams(params).toString();
      return window.api.fetch(`/api/admin/skills${q ? '?' + q : ''}`);
    },
    async get(name) {
      return window.api.fetch(`/api/admin/skills/${encodeURIComponent(name)}`);
    },
    async create(data) {
      return window.api.fetch('/api/admin/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },
    async update(name, data) {
      return window.api.fetch(`/api/admin/skills/${encodeURIComponent(name)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },
    async delete(name) {
      return window.api.fetch(`/api/admin/skills/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
    },
    async package(name) {
      return window.api.fetch(`/api/admin/skills/${encodeURIComponent(name)}/package`, {
        method: 'POST'
      });
    }
  },

  // MCP Servers management API
  mcp: {
    async list() {
      return window.api.fetch('/api/admin/mcp/servers');
    },
    async get(id) {
      return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}`);
    },
    async create(data) {
      return window.api.fetch('/api/admin/mcp/servers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },
    async update(id, data) {
      return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },
    async delete(id) {
      return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}`, {
        method: 'DELETE'
      });
    },
    async toggle(id) {
      return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}/toggle`, {
        method: 'POST'
      });
    },
    async test(id) {
      return window.api.fetch(`/api/admin/mcp/servers/${encodeURIComponent(id)}/test`, {
        method: 'POST'
      });
    },
    async testAdhoc(data) {
      return window.api.fetch('/api/admin/mcp/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },
    async getTools() {
      return window.api.fetch('/api/admin/mcp/tools');
    }
  },

  // Google Workspace Accounts Pool API
  googleAccounts: {
    async list() {
      return window.api.fetch('/api/admin/google-accounts');
    },
    async get(name) {
      return window.api.fetch(`/api/admin/google-accounts/${encodeURIComponent(name)}`);
    },
    async create(data) {
      return window.api.fetch('/api/admin/google-accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },
    async upload(formData) {
      const response = await fetch('/api/admin/google-accounts/upload', {
        method: 'POST',
        body: formData
      });
      if (!response.ok) {
        let msg = response.statusText;
        try {
          const data = await response.json();
          if (data && data.detail) msg = data.detail;
        } catch {}
        throw new Error(`${response.status} ${msg}`);
      }
      return response.json();
    },
    async setDefault(name) {
      return window.api.fetch(`/api/admin/google-accounts/${encodeURIComponent(name)}/default`, {
        method: 'POST'
      });
    },
    async resetStatus(name) {
      return window.api.fetch(`/api/admin/google-accounts/${encodeURIComponent(name)}/reset-status`, {
        method: 'POST'
      });
    },
    async test(name) {
      return window.api.fetch(`/api/admin/google-accounts/${encodeURIComponent(name)}/test`, {
        method: 'POST'
      });
    },
    async delete(name) {
      return window.api.fetch(`/api/admin/google-accounts/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
    }
  }
};

// HELP content
// Password protection state
let isPasswordProtected = false;
let hasEnteredPassword = false;

// Tab Switch Handler
function onTabSwitched(targetId) {
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  if (cleanId === 'tab-chat') {
    const msgInput = document.getElementById('message-input');
    if (msgInput) msgInput.focus();
  } else if (cleanId === 'tab-voice' && typeof window.initVoiceTab === 'function') {
    console.log('[AdminInterface] Switching to voice tab...');
    window.initVoiceTab();
  } else if (cleanId === 'tab-tts' && typeof window.initTtsTab === 'function') {
    console.log('[AdminInterface] Switching to tts tab...');
    window.initTtsTab();
  } else if (cleanId === 'tab-plugins' && typeof window.initPluginsTab === 'function') {
    console.log('[AdminInterface] Switching to plugins tab...');
    window.initPluginsTab();
  } else if (cleanId === 'tab-admin' && typeof window.initAdminTab === 'function') {
    console.log('[AdminInterface] Switching to admin tab...');
    window.initAdminTab();
  } else if (cleanId === 'tab-users' && typeof window.initUsersTab === 'function') {
    console.log('[AdminInterface] Switching to users tab...');
    window.initUsersTab();
  } else if (cleanId === 'tab-windows-users' && typeof window.initWindowsUsersTab === 'function') {
    console.log('[AdminInterface] Switching to Windows users tab...');
    window.initWindowsUsersTab();
  } else if (cleanId === 'tab-user-directories' && typeof window.initUserDirectoriesTab === 'function') {
    console.log('[AdminInterface] Switching to user directories tab...');
    window.initUserDirectoriesTab();
  } else if (cleanId === 'tab-google-accounts' && typeof window.initGoogleAccountsTab === 'function') {
    console.log('[AdminInterface] Switching to google accounts tab...');
    window.initGoogleAccountsTab();
  } else if (cleanId === 'tab-instructions' && typeof window.initInstructionsTab === 'function') {
    console.log('[AdminInterface] Switching to instructions tab...');
    window.initInstructionsTab();
  } else if (cleanId === 'tab-skills' && typeof window.initSkillsTab === 'function') {
    console.log('[AdminInterface] Switching to skills tab...');
    window.initSkillsTab();
  } else if (cleanId === 'tab-mcp' && typeof window.initMcpTab === 'function') {
    console.log('[AdminInterface] Switching to MCP tab...');
    window.initMcpTab();
  } else if (cleanId === 'tab-rag' && typeof window.initRagTab === 'function') {
    console.log('[AdminInterface] Switching to RAG tab...');
    window.initRagTab();
  } else if (cleanId === 'tab-pixelrag' && typeof window.initPixelRagTab === 'function') {
    console.log('[AdminInterface] Switching to PixelRAG tab...');
    window.initPixelRagTab();
  } else if ((cleanId === 'tab-telegram-rag' || cleanId === 'tab-telegram_rag') && typeof window.initTelegramRagTab === 'function') {
    console.log('[AdminInterface] Switching to Telegram RAG tab...');
    window.initTelegramRagTab();
  } else if (cleanId === 'tab-search' && typeof window.initSearchTab === 'function') {
    console.log('[AdminInterface] Switching to search tab...');
    window.initSearchTab();
  } else if (cleanId === 'tab-models' && typeof window.initModelsTab === 'function') {
    console.log('[AdminInterface] Switching to models tab...');
    window.initModelsTab();
  } else if (cleanId === 'tab-agents' && typeof window.initAgentsTab === 'function') {
    console.log('[AdminInterface] Switching to agents tab...');
    window.initAgentsTab();
  } else if (cleanId === 'tab-sources' && typeof window.initSourcesTab === 'function') {
    console.log('[AdminInterface] Switching to sources tab...');
    window.initSourcesTab();
  } else if (cleanId === 'tab-logs' && typeof window.initLogsTab === 'function') {
    console.log('[AdminInterface] Switching to logs tab...');
    window.initLogsTab();
  } else if (cleanId === 'tab-trading' && typeof window.initTradingTab === 'function') {
    console.log('[AdminInterface] Switching to trading tab...');
    window.initTradingTab();
  } else if (cleanId === 'tab-network' && typeof window.initNetworkTab === 'function') {
    console.log('[AdminInterface] Switching to network tab...');
    window.initNetworkTab();
  } else if (cleanId === 'tab-system-inspector' && typeof window.initSystemInspectorTab === 'function') {
    console.log('[AdminInterface] Switching to system inspector tab...');
    window.initSystemInspectorTab();
  } else if (cleanId === 'tab-about-system' && typeof window.initAboutSystemTab === 'function') {
    console.log('[AdminInterface] Switching to about system tab...');
    window.initAboutSystemTab();
  } else if (cleanId === 'tab-windows-admin' && typeof window.initWindowsAdminTab === 'function') {
    console.log('[AdminInterface] Switching to windows admin tab...');
    window.initWindowsAdminTab();
  } else if (cleanId === 'tab-cloudflared' && typeof window.initCloudflaredTab === 'function') {
    console.log('[AdminInterface] Switching to cloudflared tab...');
    window.initCloudflaredTab();
  } else if (cleanId === 'tab-user-assistant' && typeof window.initUserAssistantTab === 'function') {
    console.log('[AdminInterface] Switching to user assistant tab...');
    window.initUserAssistantTab();
  } else if (cleanId === 'tab-gcloud' && typeof window.initGCloudTab === 'function') {
    console.log('[AdminInterface] Switching to gcloud tab...');
    window.initGCloudTab();
  } else if (cleanId === 'tab-website-monitor' && typeof window.initWebsiteMonitorTab === 'function') {
    console.log('[AdminInterface] Switching to website monitor tab...');
    window.initWebsiteMonitorTab();
  } else if (cleanId === 'tab-system-control' && typeof window.initSystemControlTab === 'function') {
    console.log('[AdminInterface] Switching to system control tab...');
    window.initSystemControlTab();
  } else if (cleanId === 'tab-news' && typeof window.initNewsTab === 'function') {
    console.log('[AdminInterface] Switching to news tab...');
    window.initNewsTab();
  } else if (cleanId === 'tab-windows-backup' && typeof window.initWindowsBackupTab === 'function') {
    console.log('[AdminInterface] Switching to windows backup tab...');
    window.initWindowsBackupTab();
  } else if (cleanId === 'tab-help' && typeof window.initHelpTab === 'function') {
    console.log('[AdminInterface] Switching to help tab...');
    window.initHelpTab();
  }
}

// Programmatic tab switcher
function switchTab(targetId) {
  if (!targetId) return;
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  const tabId = cleanId.startsWith('tab-') ? cleanId : `tab-${cleanId}`;

  // 1. Update active state on dropdown items & toggles
  document.querySelectorAll('#mainTabs .dropdown-item').forEach((item) => {
    const itemTarget = item.getAttribute('data-tab') || item.getAttribute('data-bs-target')?.replace('#', '');
    if (itemTarget === tabId || itemTarget === cleanId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  document.querySelectorAll('#mainTabs .dropdown').forEach((dropdown) => {
    const toggle = dropdown.querySelector('.dropdown-toggle');
    const hasActiveChild = dropdown.querySelector('.dropdown-item.active');
    if (toggle) {
      if (hasActiveChild) {
        toggle.classList.add('active');
      } else {
        toggle.classList.remove('active');
      }
    }
  });

  // 2. Switch tab-pane (scoped to top-level container to preserve nested subtabs)
  const mainTabContent = document.getElementById('mainTabContent');
  if (mainTabContent) {
    Array.from(mainTabContent.children).forEach((pane) => {
      if (pane.classList.contains('tab-pane')) {
        pane.classList.remove('show', 'active');
      }
    });
  } else {
    document.querySelectorAll('#mainTabContent > .tab-pane, body > .container-fluid > .tab-content > .tab-pane').forEach((pane) => {
      pane.classList.remove('show', 'active');
    });
  }
  const targetPane = document.getElementById(tabId) || document.getElementById(cleanId);
  if (targetPane) {
    targetPane.classList.add('show', 'active');
  }

  // 3. Notify lifecycle callback
  onTabSwitched(tabId);
}
window.switchTab = switchTab;
window.switchToTab = switchTab;

// Setup dropdowns navigation
function setupDropdownTabs() {
  const mainTabs = document.getElementById('mainTabs');
  if (!mainTabs) return;

  // 1. Dropdown Toggle Buttons
  mainTabs.querySelectorAll('.dropdown-toggle').forEach((btn) => {
    btn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();

      const dropdown = btn.closest('.dropdown');
      const menu = dropdown?.querySelector('.dropdown-menu');
      const isAlreadyOpen = menu?.classList.contains('show');

      // Close all dropdowns
      document.querySelectorAll('#mainTabs .dropdown-menu.show').forEach((m) => {
        m.classList.remove('show');
        m.closest('.dropdown')?.querySelector('.dropdown-toggle')?.classList.remove('show');
      });

      // Toggle clicked dropdown
      if (!isAlreadyOpen && menu) {
        menu.classList.add('show');
        btn.classList.add('show');
      }
    };
  });

  // 2. Dropdown Item Buttons (Tab Switchers & Action Buttons)
  mainTabs.querySelectorAll('.dropdown-item').forEach((item) => {
    item.onclick = (e) => {
      const targetId = item.getAttribute('data-tab') || item.getAttribute('data-bs-target')?.replace('#', '');
      const pluginName = item.getAttribute('data-plugin');

      // Close dropdown menu
      item.closest('.dropdown-menu')?.classList.remove('show');
      item.closest('.dropdown')?.querySelector('.dropdown-toggle')?.classList.remove('show');

      if (pluginName && typeof window.openPluginFromDropdown === 'function') {
        e.preventDefault();
        e.stopPropagation();
        window.openPluginFromDropdown(pluginName);
      } else if (targetId) {
        e.preventDefault();
        e.stopPropagation();
        switchTab(targetId);
      }
    };
  });

  // 3. Document Click to Close Dropdowns
  if (!document.body.dataset.dropdownOutsideBound) {
    document.body.dataset.dropdownOutsideBound = 'true';
    document.addEventListener('click', (e) => {
      if (!e.target.closest('#mainTabs .dropdown')) {
        document.querySelectorAll('#mainTabs .dropdown-menu.show').forEach((menu) => {
          menu.classList.remove('show');
          menu.closest('.dropdown')?.querySelector('.dropdown-toggle')?.classList.remove('show');
        });
      }
    });
  }
}

async function startAdmin() {
  console.log('Admin interface initializing...');
  try {
    initTheme();
    setupDropdownTabs();
    const el = document.getElementById('admin-interface');
    if (el) el.style.display = 'block';
    
    if (isPasswordProtected) {
      showPasswordModal();
    } else {
      await initInterface();
    }
    console.log('Admin interface ready');
  } catch (err) {
    console.error('Error during startAdmin initialization:', err);
    const el = document.getElementById('admin-interface');
    if (el) el.style.display = 'block';
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setupDropdownTabs();
    startAdmin();
  });
} else {
  setupDropdownTabs();
  startAdmin();
}

async function initInterface() {
  // Initialize theme
  initTheme();

  // Initialize i18n
  const savedLang = localStorage.getItem('app_language') || 'ru';
  await initI18n(savedLang);
  
  // Setup language selector
  document.querySelectorAll('.lang-selector').forEach((sel) => {
    sel.value = savedLang;
    sel.addEventListener('change', (e) => {
      switchLang(e.target.value);
    });
  });

  // Initialize User Settings & Google OAuth
  await initUserSettings();

  
  // Initialize HELP content
  initHelpContent();
  
  const cb = Date.now();
  
  // Синхронизация видимости приложений (/apps) перед загрузкой вкладок
  let appsMap = {};
  try {
    let appsData = null;
    try {
      appsData = await window.api.fetch('/api/apps/status');
    } catch {
      appsData = await window.api.fetch('/api/admin/apps/status');
    }
    if (appsData && appsData.apps) {
      appsMap = appsData.apps;
      window.appsStatusMap = appsData.apps;
      syncAppsTabsVisibility(appsData.apps);
    }
  } catch (err) {
    console.warn('Ошибка синхронизации видимости приложений (/apps):', err);
  }

  // Загрузка базовых вкладок администратора
  const coreTabLoads = [
    loadTabContent('chat', `/html/chat/index.html?v=${cb}`, `/html/chat/main.js?v=${cb}`),
    loadTabContent('plugins', `/html/plugins_tab/index.html?v=${cb}`, `/html/plugins_tab/main.js?v=${cb}`),
    loadTabContent('admin', `/html/admin_tab/index.html?v=${cb}`, `/html/admin_tab/main.js?v=${cb}`),
    loadTabContent('users', `/html/users_tab/index.html?v=${cb}`, `/html/users_tab/main.js?v=${cb}`),
    loadTabContent('windows-users', `/html/windows_users_tab/index.html?v=${cb}`, `/html/windows_users_tab/main.js?v=${cb}`),
    loadTabContent('user-directories', `/html/user_directories_tab/index.html?v=${cb}`, `/html/user_directories_tab/main.js?v=${cb}`),
    loadTabContent('google-accounts', `/html/google_accounts_tab/index.html?v=${cb}`, `/html/google_accounts_tab/main.js?v=${cb}`),
    loadTabContent('instructions', `/html/instructions_tab/index.html?v=${cb}`, `/html/instructions_tab/main.js?v=${cb}`),
    loadTabContent('rag', `/html/rag_tab/index.html?v=${cb}`, `/html/rag_tab/main.js?v=${cb}`),
    loadTabContent('pixelrag', `/html/pixelrag_tab/index.html?v=${cb}`, `/html/pixelrag_tab/main.js?v=${cb}`),
    loadTabContent('telegram-rag', `/html/telegram_rag_tab/index.html?v=${cb}`, `/html/telegram_rag_tab/main.js?v=${cb}`),
    loadTabContent('voice', `/html/voice_tab/index.html?v=${cb}`, `/html/voice_tab/main.js?v=${cb}`),
    loadTabContent('models', `/html/models_tab/index.html?v=${cb}`, `/html/models_tab/main.js?v=${cb}`),
    loadTabContent('agents', `/html/agents_tab/index.html?v=${cb}`, `/html/agents_tab/main.js?v=${cb}`),
    loadTabContent('search', `/html/search_tab/index.html?v=${cb}`, `/html/search_tab/main.js?v=${cb}`),
    loadTabContent('tts', `/html/tts_tab/index.html?v=${cb}`, `/html/tts_tab/main.js?v=${cb}`),
    loadTabContent('sources', `/html/sources_tab/index.html?v=${cb}`, `/html/sources_tab/main.js?v=${cb}`),
    loadTabContent('skills', `/html/skills_tab/index.html?v=${cb}`, `/html/skills_tab/main.js?v=${cb}`),
    loadTabContent('mcp', `/html/mcp_tab/index.html?v=${cb}`, `/html/mcp_tab/main.js?v=${cb}`),
    loadTabContent('observability', `/html/system_inspector_tab/index.html?v=${cb}`, `/html/system_inspector_tab/main.js?v=${cb}`),
    loadTabContent('news', `/html/news_tab/index.html?v=${cb}`, `/html/news_tab/main.js?v=${cb}`),
    loadTabContent('logs', `/html/logs/index.html?v=${cb}`, `/html/logs/main.js?v=${cb}`),
    loadTabContent('help', `/html/help/index.html?v=${cb}`, `/html/help/main.js?v=${cb}`),
  ];

  // Определение и фильтрация вкладок микроприложений (/apps)
  const appTabDefs = [
    { id: 'about_system', tab: 'about-system', html: '/html/about_system_tab/index.html?v=20260925_v2', js: '/html/about_system_tab/main.js?v=20260925_v2' },
    { id: 'trading_terminal', tab: 'trading', html: '/html/trading_tab/index.html', js: '/html/trading_tab/main.js' },
    { id: 'network_terminal', tab: 'network', html: '/html/network_tab/index.html', js: '/html/network_tab/main.js' },
    { id: 'system_inspector', tab: 'system-inspector', html: '/html/system_inspector_tab/index.html', js: '/html/system_inspector_tab/main.js' },
    { id: 'chat', tab: 'chat', html: '/html/chat/index.html', js: '/html/chat/main.js' },
    { id: 'scenarios', tab: 'scenarios', html: '/html/scenarios_tab/index.html', js: '/html/scenarios_tab/main.js' },
    { id: 'user_assistant', tab: 'user-assistant', html: '/html/user_assistant_tab/index.html', js: '/html/user_assistant_tab/main.js' },
    { id: 'gcloud_monitor', tab: 'gcloud', html: '/html/gcloud_tab/index.html', js: '/html/gcloud_tab/main.js' },
    { id: 'website_monitor', tab: 'website-monitor', html: '/html/website_monitor_tab/index.html', js: '/html/website_monitor_tab/main.js' },
    { id: 'cloudflared_monitor', tab: 'cloudflared', html: '/html/cloudflared_tab/index.html', js: '/html/cloudflared_tab/main.js' },
    { id: 'process_leaks', tab: 'process-leaks', html: '/html/process_leaks_tab/index.html?v=20260924_v1', js: '/html/process_leaks_tab/main.js?v=20260924_v1' },
    { id: 'forensics', tab: 'forensics', html: '/html/forensics_tab/index.html?v=20260924_v1', js: '/html/forensics_tab/main.js?v=20260924_v1' },
    { id: 'throttling', tab: 'throttling', html: '/html/throttling_tab/index.html?v=20260924_v1', js: '/html/throttling_tab/main.js?v=20260924_v1' },
    { id: 'storage_wear', tab: 'storage-wear', html: '/html/storage_wear_tab/index.html?v=20260924_v1', js: '/html/storage_wear_tab/main.js?v=20260924_v1' },
    { id: 'peripherals', tab: 'peripherals', html: '/html/peripherals_tab/index.html?v=20260924_v1', js: '/html/peripherals_tab/main.js?v=20260924_v1' },
  ];

  const appTabLoads = appTabDefs
    .filter(def => {
      const appInfo = appsMap[def.id] || Object.values(appsMap).find(a => a.tab === `tab-${def.tab}` || a.id === def.id || a.folder === def.id);
      return appInfo ? appInfo.enabled : true;
    })
    .map(def => loadTabContent(def.tab, `${def.html}?v=${cb}`, `${def.js}?v=${cb}`));

  await Promise.all([...coreTabLoads, ...appTabLoads]);
  
  // Синхронизация видимости вкладок плагинов
  try {
    const pluginsData = await window.api.fetch('/api/admin/plugins');
    if (window.syncPluginTabsVisibility && pluginsData && pluginsData.plugins) {
      window.syncPluginTabsVisibility(pluginsData.plugins);
    }
  } catch (err) {
    console.error('Ошибка синхронизации видимости плагинов:', err);
  }
  
  setupDropdownTabs();
}

function syncAppsTabsVisibility(appsMap) {
  if (!appsMap || typeof appsMap !== 'object') return;
  const dropdown = document.getElementById('appsTabsDropdown');
  if (!dropdown) return;
  const dropdownMenu = dropdown.nextElementSibling || dropdown.closest('.dropdown')?.querySelector('.dropdown-menu');
  if (!dropdownMenu) return;

  const appButtons = dropdownMenu.querySelectorAll('button[data-tab]');
  let visibleCount = 0;

  appButtons.forEach((btn) => {
    const dataTab = btn.getAttribute('data-tab') || btn.getAttribute('data-bs-target')?.replace('#', '');
    const cleanId = dataTab ? dataTab.replace(/^tab-/, '') : '';
    const appInfo = Object.values(appsMap).find(a => a.tab === dataTab || a.id === cleanId || a.folder === cleanId);
    const isEnabled = appInfo ? appInfo.enabled : true;

    if (isEnabled) {
      btn.style.display = '';
      btn.classList.remove('d-none');
      visibleCount++;
    } else {
      btn.style.display = 'none';
      btn.classList.add('d-none');
      const pane = document.getElementById(dataTab);
      if (pane) {
        pane.style.display = 'none';
        pane.classList.remove('show', 'active');
      }
      if (btn.classList.contains('active')) {
        btn.classList.remove('active');
        if (typeof window.switchTab === 'function') {
          window.switchTab('tab-chat');
        }
      }
    }
  });

  const dropdownWrapper = dropdown.closest('li.nav-item');
  if (dropdownWrapper) {
    const prevDivider = dropdownWrapper.previousElementSibling;
    if (visibleCount === 0) {
      dropdownWrapper.style.display = 'none';
      dropdownWrapper.classList.add('d-none');
      if (prevDivider && prevDivider.querySelector('.nav-group-divider')) {
        prevDivider.style.display = 'none';
        prevDivider.classList.add('d-none');
      }
    } else {
      dropdownWrapper.style.display = '';
      dropdownWrapper.classList.remove('d-none');
      if (prevDivider && prevDivider.querySelector('.nav-group-divider')) {
        prevDivider.style.display = '';
        prevDivider.classList.remove('d-none');
      }
    }
  }
}
window.syncAppsTabsVisibility = syncAppsTabsVisibility;

function showPasswordModal() {
  const modal = new bootstrap.Modal(document.getElementById('passwordModal'));
  modal.show();
  
  const loginBtn = document.getElementById('login-btn');
  const passwordInput = document.getElementById('admin-password');
  const passwordError = document.getElementById('password-error');
  
  passwordInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') verifyPassword();
  });
  
  loginBtn?.addEventListener('click', verifyPassword);
}

async function verifyPassword() {
  const passwordInput = document.getElementById('admin-password');
  const passwordError = document.getElementById('password-error');
  const password = passwordInput?.value;
  if (!password) return;

  const formData = new FormData();
  formData.append('password', password);

  try {
    const res = await fetch('/admin', {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      hasEnteredPassword = true;
      passwordError?.classList.add('d-none');
      const modalElement = document.getElementById('passwordModal');
      const modal = bootstrap.Modal.getInstance(modalElement);
      modal?.hide();
      document.getElementById('admin-interface').style.display = 'block';
      await initInterface();
    } else {
      throw new Error('Invalid password');
    }
  } catch {
    passwordError?.classList.remove('d-none');
    if (passwordError) {
      passwordError.textContent = 'Неверный пароль';
    }
    if (passwordInput) {
      passwordInput.value = '';
      passwordInput.focus();
    }
  }
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
    const scriptSrc = jsOverrideSrc || `/html/${tabName}/main.js?v=${cacheBuster}`;
    
    await new Promise((resolve) => {
      const script = document.createElement('script');
      if (tabName === 'instructions' || tabName === 'rag') {
        script.type = 'module';
      }
      script.src = scriptSrc;
      script.onload = () => {
        console.log(`[Admin] Loaded JS for ${tabName}`);
        resolve();
      };
      script.onerror = (err) => {
        console.warn(`[Admin] Note: No JS loaded for ${tabName} from ${scriptSrc}`);
        resolve();
      };
      document.body.appendChild(script);
    });

    const camelName = tabName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const initFuncName = 'init' + camelName.charAt(0).toUpperCase() + camelName.slice(1) + 'Tab';
    if (typeof window[initFuncName] === 'function') {
      console.log(`[Admin] Calling ${initFuncName} for ${tabName}`);
      try {
        await window[initFuncName]();
      } catch (err) {
        console.error(`[Admin] Error executing ${initFuncName}:`, err);
      }
    }
    applyTranslations();
  } catch (e) {
    console.error(`[Admin] Error loading tab ${tabName}:`, e);
    const container = document.getElementById(`tab-${tabName}`);
    if (container) {
      container.innerHTML = `<div class="alert alert-danger">Ошибка загрузки: ${e.message}</div>`;
    }
  }
}

// Initialize HELP content
function initHelpContent() {
  window.HELP_CONTENT = window.HELP_CONTENT || {};
  const defaults = {
    'overview': `<h4>🚀 Обзор проекта</h4><p>ai-breadboard — интегрированная среда для работы с AI, RAG и системным управлением.</p>`,
    'google_oauth': `<h4>🔑 Google OAuth и аккаунты</h4><p>Интеграция с Gmail, Drive, Sheets и Docs через OAuth 2.0 и Service Accounts.</p>`,
    'ai_models': `<h4>🤖 ИИ Провайдеры и Модели</h4><p>Облачные (Gemini, OpenAI, Groq) и локальные (Ollama, Foundry, DirectML) модели.</p>`,
    'gdrive_sync': `<h4>☁️ Google Drive Sync</h4><p>Автоматическая синхронизация баз данных и файлов с Google Drive.</p>`,
    'rag_knowledge': `<h4>📚 База знаний и RAG</h4><p>Загрузка и поиск по вашим документам (PDF, Word, TXT, CSV, JSON).</p>`,
    'rag': `<h4>🧠 RAG-индекс (Векторный поиск)</h4>
<p><strong>1. База RAG:</strong> Индексирует системные базы знаний, системные инструкции и документы.</p>
<p><strong>2. Загрузка документов:</strong> Позволяет загрузить внешние <code>.json</code>, <code>.txt</code>, <code>.md</code>, <code>.pdf</code> файлы или сканировать директории напрямую в RAG-индекс.</p>
<p><strong>3. Чат-RAG:</strong> Индексирует историю сохраненных диалогов и ответов ассистента.</p>`,
    'voice_tts': `<h4>🎙️ Голос и Озвучка</h4><p>Голосовой ввод (Whisper/WebSpeech) и синтез речи (Edge TTS).</p>`,
    'plugins_skills': `<h4>🔌 Плагины, Навыки и MCP</h4><p>Telegram-бот, IFTTT, распознавание счетов и расширение через MCP.</p>`,
    'storage_disks': `<h4>💾 Диски и Хранилище</h4><p>Сканирование накопителей, проверка целостности и консолидация дублей.</p>`,
    'troubleshooting': `<h4>❓ Решение проблем (FAQ)</h4><p>Ответы на частые вопросы и устранение ошибок подключения.</p>`
  };
  window.HELP_CONTENT = Object.assign(defaults, window.HELP_CONTENT);
}

function showHelpModal(key) {
  const content = window.HELP_CONTENT[key] || '<p>Информация не найдена</p>';
  document.getElementById('help-modal-content').innerHTML = content;
  const modal = new bootstrap.Modal(document.getElementById('help-modal'));
  modal.show();
}

function showChatLogicModal() {
  const modalEl = document.getElementById('chat-logic-modal');
  if (modalEl) {
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }
}
window.showChatLogicModal = showChatLogicModal;
window.showHelpModal = showHelpModal;

// Уведомления
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
  notification.style.zIndex = '9999';
  notification.style.maxWidth = '400px';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

async function initAdminTab() {
  const modelSelect = document.getElementById('admin-model-select');
  const saveBtn = document.getElementById('btn-admin-save-model');
  
  if (!modelSelect || !saveBtn) return;
  
  // 1. Очищаем селект
  modelSelect.innerHTML = '';
  
  let modelsGrouped = {};
  // 2. Загружаем доступные модели
  try {
    const modelsData = await window.api.fetch('/api/chat/models');
    modelsGrouped = modelsData.models || {};
    if (Array.isArray(modelsGrouped)) {
      modelsGrouped = { 'gemini': modelsGrouped };
    }
  } catch (err) {
    console.error('Ошибка загрузки моделей:', err);
    showNotification('Ошибка загрузки моделей AI: ' + err.message, 'danger');
  }
  
  // 3. Заполняем селект моделями с иерархией optgroup
  const providerMeta = {
    'gemini': { label: '✨ Google Gemini', order: 1 },
    'agy': { label: '🚀 Google Antigravity (AGY)', order: 2 },
    'foundry': { label: '⚙️ Microsoft Foundry', order: 3 },
    'ollama': { label: '🦙 Ollama (Local)', order: 4 },
    'onnx': { label: '🧠 Microsoft ONNX / Olive', order: 5 }
  };

  const providers = Object.keys(modelsGrouped).sort((a, b) => {
    const oA = providerMeta[a]?.order ?? 99;
    const oB = providerMeta[b]?.order ?? 99;
    return oA - oB;
  });

  let totalModels = 0;
  providers.forEach(p => {
    const list = modelsGrouped[p] || [];
    if (!Array.isArray(list) || list.length === 0) return;

    const optgroup = document.createElement('optgroup');
    optgroup.label = providerMeta[p]?.label || `🤖 ${p.toUpperCase()}`;

    list.forEach(m => {
      totalModels++;
      const option = document.createElement('option');
      option.value = m;
      option.textContent = m;
      optgroup.appendChild(option);
    });

    modelSelect.appendChild(optgroup);
  });

  if (totalModels === 0) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'Нет доступных моделей';
    modelSelect.appendChild(option);
    saveBtn.disabled = true;
  } else {
    saveBtn.disabled = false;
  }
  
  // 4. Загружаем текущие настройки пользователя (выбранную модель)
  try {
    const settingsData = await window.api.fetch('/auth/settings');
    const savedModel = settingsData && settingsData.model ? settingsData.model : '';
    if (savedModel) {
      modelSelect.value = savedModel;
    }
    if (typeof window.updateChatBadges === 'function') {
      window.updateChatBadges(savedModel);
    }
  } catch (err) {
    console.error('Ошибка загрузки настроек AI пользователя:', err);
  }
  
  // 5. Навешиваем обработчик сохранения
  saveBtn.onclick = async () => {
    const selectedModel = modelSelect.value;
    saveBtn.disabled = true;
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Сохранение...';
    
    try {
      await window.api.fetch('/auth/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      });
      showNotification('Модель успешно обновлена на: ' + selectedModel, 'success');
      
      // Обновляем бейджи модели в реальном времени на странице
      window.activeModelName = selectedModel;
      if (typeof window.updateChatBadges === 'function') {
        window.updateChatBadges(selectedModel);
      } else {
        const badges = document.querySelectorAll('#chat-model-badge, #chat-popup-model-badge');
        badges.forEach(badge => {
          badge.textContent = selectedModel;
          badge.style.display = 'inline-block';
        });
      }
    } catch (err) {
      console.error('Ошибка сохранения модели:', err);
      showNotification('Ошибка сохранения: ' + err.message, 'danger');
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
    }
  };
}

window.initAdminTab = initAdminTab;