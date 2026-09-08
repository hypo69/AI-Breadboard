// User Interface Main JS
import { initI18n, switchLang, applyTranslations } from '../js/i18n.js';
import { initTheme, setTheme, getThemeMode, getResolvedTheme } from '../js/theme.js';
import { initUserSettings, refreshUserProfile } from '../js/userSettings.js';

window.switchLang = switchLang;
window.applyTranslations = applyTranslations;
window.setTheme = setTheme;
window.getThemeMode = getThemeMode;
window.getResolvedTheme = getResolvedTheme;
window.initUserSettings = initUserSettings;
window.refreshUserProfile = refreshUserProfile;

// Global API module
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
  }
};

// UI Notifications
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3 shadow`;
  notification.style.zIndex = '9999';
  notification.style.maxWidth = '400px';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 5000);
}
window.showNotification = showNotification;

// Tab Switch Handler
function onTabSwitched(targetId) {
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
  if (cleanId === 'tab-chat') {
    const msgInput = document.getElementById('message-input');
    if (msgInput) msgInput.focus();
  } else if (cleanId === 'tab-rag' && typeof window.initRagTab === 'function') {
    console.log('[UserInterface] Switching to RAG tab...');
    window.initRagTab();
  } else if (cleanId === 'tab-tts' && typeof window.initTtsTab === 'function') {
    console.log('[UserInterface] Switching to TTS tab...');
    window.initTtsTab();
  } else if (cleanId === 'tab-voice' && typeof window.initVoiceTab === 'function') {
    console.log('[UserInterface] Switching to Voice tab...');
    window.initVoiceTab();
  } else if (cleanId === 'tab-skills' && typeof window.initSkillsTab === 'function') {
    console.log('[UserInterface] Switching to Skills tab...');
    window.initSkillsTab();
  } else if (cleanId === 'tab-plugins' && typeof window.initPluginsTab === 'function') {
    console.log('[UserInterface] Switching to Plugins tab...');
    window.initPluginsTab();
  }
}

// Programmatic tab switcher
function switchTab(targetId) {
  if (!targetId) return;
  const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;

  // 1. Update active state on dropdown items & toggles
  document.querySelectorAll('#mainTabs .dropdown-item').forEach((item) => {
    const itemTarget = item.getAttribute('data-tab') || item.getAttribute('data-bs-target')?.replace('#', '');
    if (itemTarget === cleanId) {
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

  // 2. Switch tab-pane
  document.querySelectorAll('.tab-content > .tab-pane').forEach((pane) => {
    pane.classList.remove('show', 'active');
  });
  const targetPane = document.getElementById(cleanId);
  if (targetPane) {
    targetPane.classList.add('show', 'active');
  }

  // 3. Notify lifecycle callback
  onTabSwitched(cleanId);
}
window.switchTab = switchTab;

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

  // 2. Dropdown Item Buttons (Tab Switchers)
  mainTabs.querySelectorAll('.dropdown-item').forEach((item) => {
    item.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();

      const targetId = item.getAttribute('data-tab') || item.getAttribute('data-bs-target')?.replace('#', '');

      // Close dropdown menu
      item.closest('.dropdown-menu')?.classList.remove('show');
      item.closest('.dropdown')?.querySelector('.dropdown-toggle')?.classList.remove('show');

      if (targetId) {
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

async function startUserInterface() {
  console.log('User interface initializing...');
  try {
    initTheme();
    setupDropdownTabs();
    const el = document.getElementById('user-interface');
    if (el) el.style.display = 'block';
    await initInterface();
    console.log('User interface ready');
  } catch (err) {
    console.error('Error during startUserInterface initialization:', err);
    const el = document.getElementById('user-interface');
    if (el) el.style.display = 'block';
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setupDropdownTabs();
    startUserInterface();
  });
} else {
  setupDropdownTabs();
  startUserInterface();
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

  const cb = Date.now();
  // Load the requested tabs: Chat, RAG, TTS, Voice, Skills, Plugins
  await Promise.all([
    loadTabContent('chat', `/html/chat/index.html?v=${cb}`),
    loadTabContent('rag', `/html/rag_tab/index.html?v=${cb}`, `/html/rag_tab/main.js?v=${cb}`),
    loadTabContent('tts', `/html/tts_tab/index.html?v=${cb}`, `/html/tts_tab/main.js?v=${cb}`),
    loadTabContent('voice', `/html/voice_tab/index.html?v=${cb}`, `/html/voice_tab/main.js?v=${cb}`),
    loadTabContent('skills', `/html/skills_tab/index.html?v=${cb}`, `/html/skills_tab/main.js?v=${cb}`),
    loadTabContent('plugins', `/html/plugins_tab/index.html?v=${cb}`, `/html/plugins_tab/main.js?v=${cb}`),
  ]);

  // Apply translations
  applyTranslations();

  // Synchronize plugin tabs visibility
  try {
    let pluginsResp = await fetch('/api/plugins?scope=user');
    if (!pluginsResp.ok) {
      pluginsResp = await fetch('/api/admin/plugins?scope=user');
    }
    if (pluginsResp.ok) {
      const pluginsData = await pluginsResp.json();
      if (window.syncPluginTabsVisibility && pluginsData && pluginsData.plugins) {
        window.syncPluginTabsVisibility(pluginsData.plugins);
      }
    }
  } catch (err) {
    console.error('Ошибка синхронизации видимости плагинов:', err);
  }
  
  setupDropdownTabs();
}

async function loadTabContent(tabName, url, jsOverrideSrc) {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const container = document.getElementById(`tab-${tabName}`);
    if (!container) return;
    container.innerHTML = html;
    
    // Load JS for the tab if provided or present
    const cacheBuster = Date.now();
    const scriptSrc = jsOverrideSrc || `/html/${tabName}/main.js?v=${cacheBuster}`;
    
    await new Promise((resolve) => {
      const script = document.createElement('script');
      if (tabName === 'instructions' || tabName === 'rag') {
        script.type = 'module';
      }
      script.src = scriptSrc;
      script.onload = () => {
        console.log(`[User] Loaded JS for ${tabName}`);
        resolve();
      };
      script.onerror = (err) => {
        console.debug(`[User] Note: No JS loaded for ${tabName} from ${scriptSrc}`);
        resolve();
      };
      document.body.appendChild(script);
    });

    const initFuncName = 'init' + tabName.charAt(0).toUpperCase() + tabName.slice(1) + 'Tab';
    if (typeof window[initFuncName] === 'function') {
      console.log(`[User] Calling ${initFuncName} for ${tabName}`);
      try {
        await window[initFuncName]();
      } catch (err) {
        console.error(`[User] Error executing ${initFuncName}:`, err);
      }
    }
    applyTranslations();
  } catch (e) {
    console.error(`[User] Error loading tab ${tabName}:`, e);
    const container = document.getElementById(`tab-${tabName}`);
    if (container) {
      container.innerHTML = `<div class="alert alert-danger">Ошибка загрузки: ${e.message}</div>`;
    }
  }
}