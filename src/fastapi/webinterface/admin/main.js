// Admin Interface Main JS
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

// Admin password (hardcoded for security)
const ADMIN_PASSWORD = 'onela';

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
  } else if (cleanId === 'tab-help' && typeof window.initHelpTab === 'function') {
    console.log('[AdminInterface] Switching to help tab...');
    window.initHelpTab();
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
  // Load all tabs
  await Promise.all([
    loadTabContent('chat', `/html/chat/index.html?v=${cb}`),
    loadTabContent('plugins', `/html/plugins_tab/index.html?v=${cb}`, `/html/plugins_tab/main.js?v=${cb}`),
    loadTabContent('admin', `/html/admin_tab/index.html?v=${cb}`, `/html/admin_tab/main.js?v=${cb}`),
    loadTabContent('users', `/html/users_tab/index.html?v=${cb}`, `/html/users_tab/main.js?v=${cb}`),
    loadTabContent('instructions', `/html/instructions_tab/index.html?v=${cb}`, `/html/instructions_tab/main.js?v=${cb}`),
    loadTabContent('rag', `/html/rag_tab/index.html?v=${cb}`, `/html/rag_tab/main.js?v=${cb}`),
    loadTabContent('voice', `/html/voice_tab/index.html?v=${cb}`, `/html/voice_tab/main.js?v=${cb}`),
    loadTabContent('models', `/html/models_tab/index.html?v=${cb}`, `/html/models_tab/main.js?v=${cb}`),
    loadTabContent('agents', `/html/agents_tab/index.html?v=${cb}`, `/html/agents_tab/main.js?v=${cb}`),
    loadTabContent('search', `/html/search_tab/index.html?v=${cb}`, `/html/search_tab/main.js?v=${cb}`),
    loadTabContent('tts', `/html/tts_tab/index.html?v=${cb}`, `/html/tts_tab/main.js?v=${cb}`),
    loadTabContent('sources', `/html/sources_tab/index.html?v=${cb}`, `/html/sources_tab/main.js?v=${cb}`),
    loadTabContent('skills', `/html/skills_tab/index.html?v=${cb}`, `/html/skills_tab/main.js?v=${cb}`),
    loadTabContent('mcp', `/html/mcp_tab/index.html?v=${cb}`, `/html/mcp_tab/main.js?v=${cb}`),
    loadTabContent('logs', `/html/logs/index.html?v=${cb}`),
    loadTabContent('help', `/html/help/index.html?v=${cb}`),
  ]);
  
  // Apply translations
  applyTranslations();
  
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
  
  if (password === ADMIN_PASSWORD) {
    // Password correct
    hasEnteredPassword = true;
    
    // Hide error
    passwordError?.classList.add('d-none');
    
    // Close modal
    const modalElement = document.getElementById('passwordModal');
    const modal = bootstrap.Modal.getInstance(modalElement);
    modal?.hide();
    
    // Show interface
    document.getElementById('admin-interface').style.display = 'block';
    
    // Initialize interface
    await initInterface();
  } else {
    // Password incorrect
    passwordError?.classList.remove('d-none');
    if (passwordError) {
      passwordError.textContent = 'Неверный пароль';
    }
    
    // Clear input
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

    const initFuncName = 'init' + tabName.charAt(0).toUpperCase() + tabName.slice(1) + 'Tab';
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
  window.HELP_CONTENT = {
    'overview': `<h4>📋 Обзор проекта</h4><p>ai-breadboard — интегрированная среда для работы с AI, RAG и системным управлением.</p>`,
    'rag': `<h4>🧠 RAG-индекс (Векторный поиск)</h4>
<p><strong>1. База RAG:</strong> Индексирует системные базы знаний, системные инструкции и документы.</p>
<p><strong>2. Загрузка документов («➕ JSON»):</strong> Позволяет загрузить внешние <code>.json</code>, <code>.txt</code>, <code>.md</code> файлы или сканировать директории напрямую в RAG-индекс.</p>
<p><strong>3. Чат-RAG:</strong> Индексирует историю сохраненных диалогов и ответов ассистента.</p>`,
    'code_rules': `<h4>⚙️ CODE_RULES</h4><p>Правила кодирования проекта.</p>`,
    'architecture': `<h4>🏗️ Архитектура</h4><p>Технологический стек проекта.</p>`,
    'fastapi': `<h4>🚀 FastAPI</h4><p>API роутеры и эндпоинты.</p>`,
    'gemini': `<h4>🧠 Gemini AI</h4><p>Интеграция с Gemini, AGY, Foundry и Ollama.</p>`,
    'configuration': `<h4>⚙️ Конфигурация</h4><p>Настройки проекта (config.json).</p>`,
    'cli_commands': `<h4>⌨️ CLI команды</h4><p>Командная строка и лончеры.</p>`,
  };
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