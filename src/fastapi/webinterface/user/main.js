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

async function startUserInterface() {
  console.log('User interface initializing...');
  try {
    initTheme();
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
  document.addEventListener('DOMContentLoaded', startUserInterface);
} else {
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
  
  // Setup dropdowns and wire click handlers
  function setupDropdownTabs() {
    document.querySelectorAll('#mainTabs [data-bs-toggle="dropdown"]').forEach((toggleBtn) => {
      if (window.bootstrap?.Dropdown) {
        bootstrap.Dropdown.getOrCreateInstance(toggleBtn, {
          autoClose: true
        });
      }

      if (!toggleBtn.dataset.boundDropdownClick) {
        toggleBtn.dataset.boundDropdownClick = 'true';
        toggleBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const menu = toggleBtn.nextElementSibling;
          const isShown = toggleBtn.classList.contains('show') || (menu && menu.classList.contains('show'));

          // Close other open dropdowns first
          document.querySelectorAll('#mainTabs .dropdown-menu.show').forEach((otherMenu) => {
            if (otherMenu !== menu) {
              otherMenu.classList.remove('show');
              const otherToggle = otherMenu.previousElementSibling;
              otherToggle?.classList.remove('show');
              otherToggle?.setAttribute('aria-expanded', 'false');
              if (otherToggle && window.bootstrap?.Dropdown) {
                const dd = bootstrap.Dropdown.getInstance(otherToggle);
                dd?.hide();
              }
            }
          });

          if (isShown) {
            if (window.bootstrap?.Dropdown) {
              const dd = bootstrap.Dropdown.getInstance(toggleBtn);
              dd?.hide();
            }
            menu?.classList.remove('show');
            toggleBtn.classList.remove('show');
            toggleBtn.setAttribute('aria-expanded', 'false');
          } else {
            if (window.bootstrap?.Dropdown) {
              const dd = bootstrap.Dropdown.getOrCreateInstance(toggleBtn);
              dd.show();
            }
            menu?.classList.add('show');
            toggleBtn.classList.add('show');
            toggleBtn.setAttribute('aria-expanded', 'true');
          }
        });
      }
    });

    document.querySelectorAll('#mainTabs .dropdown-item[data-bs-toggle="tab"]').forEach((itemBtn) => {
      // Avoid duplicate click listeners
      if (itemBtn.dataset.boundTabClick) return;
      itemBtn.dataset.boundTabClick = 'true';

      itemBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (window.bootstrap?.Tab) {
          const tabInstance = bootstrap.Tab.getOrCreateInstance(itemBtn);
          tabInstance.show();
        }
        const dropdown = itemBtn.closest('.dropdown');
        const dropdownToggle = dropdown?.querySelector('[data-bs-toggle="dropdown"]');
        if (dropdownToggle) {
          if (window.bootstrap?.Dropdown) {
            const dd = bootstrap.Dropdown.getInstance(dropdownToggle);
            dd?.hide();
          }
          const menu = itemBtn.closest('.dropdown-menu');
          if (menu) {
            menu.classList.remove('show');
            dropdownToggle.classList.remove('show');
            dropdownToggle.setAttribute('aria-expanded', 'false');
          }
        }
      });
    });
  }

  // Close dropdowns on outside click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('#mainTabs .dropdown')) {
      document.querySelectorAll('#mainTabs .dropdown-menu.show').forEach((menu) => {
        menu.classList.remove('show');
        const toggle = menu.previousElementSibling;
        if (toggle) {
          toggle.classList.remove('show');
          toggle.setAttribute('aria-expanded', 'false');
          if (window.bootstrap?.Dropdown) {
            const dd = bootstrap.Dropdown.getInstance(toggle);
            dd?.hide();
          }
        }
      });
    }
  });

  setupDropdownTabs();

  // Tab switch handlers
  document.addEventListener('shown.bs.tab', (e) => {
    const target = e.target.getAttribute('data-bs-target');

    // Sync active state for dropdown items and toggles
    document.querySelectorAll('#mainTabs .dropdown-item').forEach((item) => {
      if (item.getAttribute('data-bs-target') === target) {
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

    setupDropdownTabs();

    if (target === '#tab-chat') {
      const msgInput = document.getElementById('message-input');
      if (msgInput) {
        msgInput.focus();
      }
    } else if (target === '#tab-rag') {
      console.log('[UserInterface] Switching to RAG tab...');
      if (window.initRagTab) {
        window.initRagTab();
      }
    } else if (target === '#tab-tts') {
      console.log('[UserInterface] Switching to TTS tab...');
      if (window.initTtsTab) {
        window.initTtsTab();
      }
    } else if (target === '#tab-voice') {
      console.log('[UserInterface] Switching to Voice tab...');
      if (window.initVoiceTab) {
        window.initVoiceTab();
      }
    } else if (target === '#tab-skills') {
      console.log('[UserInterface] Switching to Skills tab...');
      if (window.initSkillsTab) {
        window.initSkillsTab();
      }
    } else if (target === '#tab-plugins') {
      console.log('[UserInterface] Switching to Plugins tab...');
      if (window.initPluginsTab) {
        window.initPluginsTab();
      }
    }
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