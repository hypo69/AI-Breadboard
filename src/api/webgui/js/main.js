// ── MAIN.JS ───────────────────────────────────────────────────────────────────

import { initI18n, switchLang, applyTranslations } from './i18n.js';
import { initTheme, setTheme, getThemeMode, getResolvedTheme } from './theme.js';
import { initUserSettings, refreshUserProfile } from './userSettings.js';
import { initActivityTracker, trackTabSwitch } from './activityTracker.js';

// Make switchLang and theme functions available globally
window.switchLang = switchLang;
window.applyTranslations = applyTranslations;
window.setTheme = setTheme;
window.getThemeMode = getThemeMode;
window.getResolvedTheme = getResolvedTheme;
window.initUserSettings = initUserSettings;
window.refreshUserProfile = refreshUserProfile;
window.trackTabSwitch = trackTabSwitch;

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

// Initialize HELP content when help tab is loaded
document.addEventListener('DOMContentLoaded', async () => {
  console.log('Starting initialization...');
  
  // Initialize dropdown navigation immediately
  setupDropdownTabs();

  // Initialize theme first
  initTheme();
  console.log('Theme initialized');
  
  // Initialize i18n first
  const savedLang = localStorage.getItem('app_language') || 'ru';
  await initI18n(savedLang);
  console.log('i18n initialized');
  
  // Setup language selector
  document.querySelectorAll('.lang-selector').forEach((sel) => {
    sel.value = savedLang;
    sel.addEventListener('change', (e) => {
      switchLang(e.target.value);
    });
  });

  // Initialize User Settings & Google OAuth
  await initUserSettings();
  console.log('User settings initialized');

  // Initialize Activity Tracker for authenticated users
  initActivityTracker();

  await initHelpContent();
  console.log('HELP system initialized');
  
  console.log('Loading tabs...');
  const v = Date.now();
  await Promise.all([
    loadTabContent('chat', `/html/chat/index.html?v=${v}`, `/html/chat/main.js?v=${v}`),
    loadTabContent('rag', `/html/rag_tab/index.html?v=${v}`, `/html/rag_tab/main.js?v=${v}`),
    loadTabContent('telegram-rag', `/html/telegram_rag_tab/index.html?v=${v}`, `/html/telegram_rag_tab/main.js?v=${v}`),
    loadTabContent('news', `/html/news_tab/index.html?v=${v}`, `/html/news_tab/main.js?v=${v}`),
    loadTabContent('voice', `/html/voice_tab/index.html?v=${v}`, `/html/voice_tab/main.js?v=${v}`),
    loadTabContent('plugins', `/html/plugins_tab/index.html?v=${v}`, `/html/plugins_tab/main.js?v=${v}`),
    loadTabContent('admin', `/html/admin_tab/index.html?v=${v}`, `/html/admin_tab/main.js?v=${v}`),
    loadTabContent('help', `/html/help/index.html?v=${v}`, `/html/help/main.js?v=${v}`),
  ]);
  console.log('All tabs loaded');
  
  // Apply translations after all tabs are loaded
  applyTranslations();
  
  // Синхронизация видимости вкладок плагинов
  try {
    const pluginsResp = await fetch('/api/admin/plugins');
    if (pluginsResp.ok) {
      const pluginsData = await pluginsResp.json();
      if (window.syncPluginTabsVisibility && pluginsData && pluginsData.plugins) {
        window.syncPluginTabsVisibility(pluginsData.plugins);
      }
    }
  } catch (err) {
    console.error('Ошибка синхронизации видимости плагинов:', err);
  }
  
  // Инициализация первой вкладки
  const chatTab = document.querySelector('[data-bs-target="#tab-chat"]');
  if (chatTab) {
    chatTab.classList.add('active');
    document.getElementById('tab-chat').classList.add('show', 'active');
  }
  setupDropdownTabs();

  // Инициализация постоянного фонового WebSocket соединения компьютера
  initBackgroundComputerStream();

  console.log('Initialization complete');
});

// ── BACKGROUND COMPUTER WS STREAM ──────────────────────────────────────────
let backgroundComputerWs = null;

function initBackgroundComputerStream() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/control/ws?role=computer`;
  
  try {
    backgroundComputerWs = new WebSocket(wsUrl);

    backgroundComputerWs.onopen = () => {
      console.log('✓ Background computer WebSocket stream connected');
    };

    backgroundComputerWs.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event === 'transcript' && msg.text) {
          console.log('Received remote transcript:', msg.text);
          if (typeof window.handleRemoteTranscript === 'function') {
            window.handleRemoteTranscript(msg.text);
          }
        }
      } catch (err) {
        console.error('Error handling background WS message:', err);
      }
    };

    backgroundComputerWs.onclose = () => {
      console.warn('Background computer WebSocket stream closed. Reconnecting in 3s...');
      setTimeout(() => {
        initBackgroundComputerStream();
      }, 3000);
    };

    backgroundComputerWs.onerror = (err) => {
      console.debug('Background computer WS stream error:', err);
    };
  } catch (e) {
    console.debug('Failed to initialize background computer WS stream:', e);
  }
}

// Загрузка контента вкладки
async function loadTabContent(tabName, url, scriptUrl = null) {
  try {
    console.log(`Loading tab ${tabName} from ${url}...`);
    const response = await fetch(url);
    console.log(`Response status: ${response.status} for ${tabName}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const container = document.getElementById(`tab-${tabName}`);
    container.innerHTML = html;
    console.log(`Content set for tab ${tabName}, length: ${html.length}`);
    
    // Загрузка JS файла вкладки
    const script = document.createElement('script');
    script.src = scriptUrl || `/html/${tabName}/main.js?v=${Date.now()}`;
    if (tabName === 'admin' || tabName === 'instructions' || tabName === 'rag') {
      script.type = 'module';
    }
    script.onload = () => {
      console.log(`✓ Загружен JS вкладки: ${tabName}`);
    const camelName = tabName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const initFuncName = 'init' + camelName.charAt(0).toUpperCase() + camelName.slice(1) + 'Tab';
    if (typeof window[initFuncName] === 'function') {
      try {
        window[initFuncName]();
      } catch (err) {
        console.error(`Error executing ${initFuncName}:`, err);
      }
    }
    // Apply translations to newly loaded tab content
    window.applyTranslations?.();
  };
  script.onerror = () => console.error(`✗ Ошибка загрузки JS вкладки ${tabName}`);
  container.appendChild(script);
  
  console.log(`✓ Загружена вкладка: ${tabName}`);
} catch (e) {
  console.error(`✗ Ошибка загрузки вкладки ${tabName}:`, e);
  document.getElementById(`tab-${tabName}`).innerHTML = 
    `<div class="alert alert-danger">Ошибка загрузки вкладки: ${e.message}</div>`;
}
}

// Tab Switch Handler
function onTabSwitched(targetId) {
const cleanId = targetId.startsWith('#') ? targetId.slice(1) : targetId;
try {
  trackTabSwitch(cleanId);
} catch (e) {
  console.debug('Failed to track tab switch:', e);
}
if (cleanId === 'tab-chat') {
  const msgInput = document.getElementById('message-input');
  if (msgInput) msgInput.focus();
} else if (cleanId === 'tab-rag' && typeof window.initRagTab === 'function') {
  console.log('[MainInterface] Switching to RAG tab...');
  window.initRagTab();
} else if ((cleanId === 'tab-telegram-rag' || cleanId === 'tab-telegram_rag') && typeof window.initTelegramRagTab === 'function') {
  console.log('[MainInterface] Switching to Telegram RAG tab...');
  window.initTelegramRagTab();
} else if (cleanId === 'tab-news' && typeof window.initNewsTab === 'function') {
  console.log('[MainInterface] Switching to News tab...');
  window.initNewsTab();
} else if (cleanId === 'tab-voice' && typeof window.initVoiceTab === 'function') {
  console.log('[MainInterface] Switching to Voice tab...');
  window.initVoiceTab();
} else if (cleanId === 'tab-plugins' && typeof window.initPluginsTab === 'function') {
  console.log('[MainInterface] Switching to Plugins tab...');
  window.initPluginsTab();
} else if (cleanId === 'tab-admin' && typeof window.initAdminTab === 'function') {
  console.log('[MainInterface] Switching to Admin tab...');
  window.initAdminTab();
} else if (cleanId === 'tab-help' && typeof window.initHelpTab === 'function') {
  console.log('[MainInterface] Switching to Help tab...');
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

// Модуль для работы с API
window.api = {
  async fetch(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
      let msg = response.statusText;
      try {
        const data = await response.json();
        msg = data.detail || msg;
      } catch {}
      throw new Error(`${response.status} ${msg}`);
    }
    return response.json();
  }
};

// ── HELP SYSTEM ───────────────────────────────────────────────────────────────
// Comprehensive User-Friendly Knowledge Base and Guides

window.HELP_CONTENT = {};

// Initialize HELP content with interactive guides and quick actions
async function initHelpContent() {
  // 1. Overview & Quick Start
  window.HELP_CONTENT['overview'] = `
    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
      <div>
        <h4 class="fw-bold mb-1 text-primary">🚀 Быстрый старт и обзор AI Breadboard</h4>
        <p class="text-muted small mb-0">Интерактивный персональный AI-ассистент, объединяющий облачные и локальные модели, базу знаний и автоматизацию.</p>
      </div>
      <button class="btn btn-outline-primary btn-sm rounded-pill d-flex align-items-center gap-1" data-jump-tab="tab-chat">
        <i class="bi bi-chat-dots-fill"></i> Открыть чат
      </button>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-md-6">
        <div class="card h-100 border-primary-subtle bg-body-tertiary shadow-sm">
          <div class="card-body p-3">
            <h6 class="fw-bold text-primary d-flex align-items-center gap-2">
              <i class="bi bi-chat-square-text-fill"></i> 1. Умный чат и Модели
            </h6>
            <p class="small text-secondary mb-2">Общайтесь с передовыми облачными моделями (Google Gemini, OpenAI, Groq) или запускайте полностью приватные локальные нейросети (Ollama, Microsoft Foundry, DirectML).</p>
            <span class="badge bg-primary-subtle text-primary">Мульти-провайдеры</span>
            <span class="badge bg-info-subtle text-info">Веб-поиск</span>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card h-100 border-danger-subtle bg-body-tertiary shadow-sm">
          <div class="card-body p-3">
            <h6 class="fw-bold text-danger d-flex align-items-center gap-2">
              <i class="bi bi-google"></i> 2. Google Workspace
            </h6>
            <p class="small text-secondary mb-2">Автономные агенты для работы с Gmail, Google Drive, Google Таблицами и Документами. Поддерживаются персональный вход через OAuth 2.0 и серверные Service Accounts.</p>
            <span class="badge bg-danger-subtle text-danger">Gmail & Drive</span>
            <span class="badge bg-warning-subtle text-warning">Docs & Sheets</span>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card h-100 border-warning-subtle bg-body-tertiary shadow-sm">
          <div class="card-body p-3">
            <h6 class="fw-bold text-warning d-flex align-items-center gap-2">
              <i class="bi bi-journal-bookmark-fill"></i> 3. База знаний (RAG)
            </h6>
            <p class="small text-secondary mb-2">Загружайте ваши PDF, Word, TXT, CSV файлы. Ассистент находит точные ответы на основе ваших документов с цитированием первоисточников.</p>
            <span class="badge bg-warning-subtle text-warning">Векторный поиск</span>
            <span class="badge bg-secondary-subtle text-secondary">RAG Cleaner</span>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card h-100 border-success-subtle bg-body-tertiary shadow-sm">
          <div class="card-body p-3">
            <h6 class="fw-bold text-success d-flex align-items-center gap-2">
              <i class="bi bi-mic-fill"></i> 4. Голос, Звук и Плагины
            </h6>
            <p class="small text-secondary mb-2">Диктовка голосом (Whisper), естественная озвучка ответов (Edge TTS), Telegram-бот, управление умным домом через IFTTT и расширение возможностей через MCP.</p>
            <span class="badge bg-success-subtle text-success">Edge TTS</span>
            <span class="badge bg-info-subtle text-info">Telegram Bot</span>
          </div>
        </div>
      </div>
    </div>

    <h5 class="fw-bold mb-2">📌 Быстрая навигация по разделам</h5>
    <div class="d-flex flex-wrap gap-2 mb-3">
      <button class="btn btn-outline-secondary btn-sm rounded-pill" onclick="loadHelpSection('google_oauth')">🔑 Как подключить Google OAuth</button>
      <button class="btn btn-outline-secondary btn-sm rounded-pill" onclick="loadHelpSection('ai_models')">🤖 Выбор и настройка моделей ИИ</button>
      <button class="btn btn-outline-secondary btn-sm rounded-pill" onclick="loadHelpSection('gdrive_sync')">☁️ Синхронизация с Google Drive</button>
      <button class="btn btn-outline-secondary btn-sm rounded-pill" onclick="loadHelpSection('rag_knowledge')">📚 Как загрузить документы в RAG</button>
      <button class="btn btn-outline-secondary btn-sm rounded-pill" onclick="loadHelpSection('troubleshooting')">❓ Решение частых проблем</button>
    </div>
  `;

  // 2. Google OAuth & Accounts Guide
  window.HELP_CONTENT['google_oauth'] = `
    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
      <div>
        <h4 class="fw-bold mb-1 text-danger d-flex align-items-center gap-2">
          <i class="bi bi-google"></i> Руководство по Google OAuth 2.0 и аккаунтам
        </h4>
        <p class="text-muted small mb-0">Пошаговая инструкция по привязке аккаунтов Google для работы с почтой, документами и диском.</p>
      </div>
      <button class="btn btn-danger btn-sm rounded-pill d-flex align-items-center gap-1" data-jump-tab="tab-admin">
        <i class="bi bi-person-plus-fill"></i> Управление аккаунтами
      </button>
    </div>

    <div class="alert alert-primary border-0 shadow-sm rounded-3 mb-4">
      <h6 class="fw-bold mb-1"><i class="bi bi-info-circle-fill me-1"></i> Два способа интеграции с Google:</h6>
      <ul class="mb-0 small ps-3">
        <li><strong>OAuth 2.0 Client (Desktop App)</strong> — позволяет ассистенту читать и отправлять письма от вашего имени, редактировать ваши файлы Google Docs и Google Таблицы.</li>
        <li><strong>Service Account (Сервисный ключ JSON)</strong> — используется для автономных фоновых серверов, автоматической синхронизации данных и бэкапов.</li>
      </ul>
    </div>

    <h5 class="fw-bold mb-3">🛠️ Пошаговая настройка OAuth 2.0 (5 шагов):</h5>

    <div class="card mb-3 border shadow-sm">
      <div class="card-header bg-body-tertiary fw-bold small">Шаг 1: Создание проекта в Google Cloud Console</div>
      <div class="card-body p-3 small">
        <p class="mb-2">Перейдите в консоль управления Google и создайте новый проект (или выберите существующий):</p>
        <a href="https://console.cloud.google.com/projectcreate" target="_blank" rel="noopener noreferrer" class="btn btn-outline-primary btn-sm">
          <i class="bi bi-box-arrow-up-right me-1"></i> Открыть Google Cloud Console ➜ Создать проект
        </a>
      </div>
    </div>

    <div class="card mb-3 border shadow-sm">
      <div class="card-header bg-body-tertiary fw-bold small">Шаг 2: Включение необходимых Google API</div>
      <div class="card-body p-3 small">
        <p class="mb-2">В разделе <strong>APIs & Services ➜ Library</strong> найдите и нажмите <strong>«Enable» (Включить)</strong> для следующих сервисов:</p>
        <div class="d-flex flex-wrap gap-2">
          <span class="badge bg-secondary p-2">Gmail API</span>
          <span class="badge bg-secondary p-2">Google Drive API</span>
          <span class="badge bg-secondary p-2">Google Sheets API</span>
          <span class="badge bg-secondary p-2">Google Docs API</span>
        </div>
      </div>
    </div>

    <div class="card mb-3 border shadow-sm">
      <div class="card-header bg-body-tertiary fw-bold small">Шаг 3: Настройка экрана согласия (OAuth Consent Screen)</div>
      <div class="card-body p-3 small">
        <ol class="ps-3 mb-0">
          <li class="mb-1">В боковом меню выберите <strong>OAuth consent screen</strong>.</li>
          <li class="mb-1">Выберите тип: <code>External</code> (Внешний) и нажмите <em>Create</em>.</li>
          <li class="mb-1">Укажите имя приложения (например, <code>AI Breadboard</code>) и ваш контактный email.</li>
          <li class="mb-1">В разделе <strong>Test Users (Тестовые пользователи)</strong> обязательно добавьте ваш Google Email!</li>
        </ol>
      </div>
    </div>

    <div class="card mb-3 border shadow-sm">
      <div class="card-header bg-body-tertiary fw-bold small">Шаг 4: Создание учетных данных OAuth Client ID</div>
      <div class="card-body p-3 small">
        <ol class="ps-3 mb-2">
          <li class="mb-1">Перейдите в <strong>Credentials ➜ + CREATE CREDENTIALS ➜ OAuth client ID</strong>.</li>
          <li class="mb-1">В выпадающем списке <em>Application type</em> выберите: <strong>Desktop app (Приложение для ПК)</strong>.</li>
          <li class="mb-1">Нажмите <strong>Create</strong>, затем нажмите <strong>DOWNLOAD JSON</strong>.</li>
        </ol>
        <div class="text-muted">Файл скачается с именем вида <code>client_secret_XXXXX.json</code>.</div>
      </div>
    </div>

    <div class="card mb-3 border shadow-sm">
      <div class="card-header bg-body-tertiary fw-bold small">Шаг 5: Загрузка в AI Breadboard</div>
      <div class="card-body p-3 small">
        <p class="mb-2">Перейдите во вкладку <strong>«Управление» ➜ «Google Workspace»</strong>, выберите скачанный JSON-файл и сохраните аккаунт.</p>
        <button class="btn btn-outline-danger btn-sm rounded-pill" data-jump-tab="tab-admin">
          <i class="bi bi-arrow-right-circle-fill me-1"></i> Перейти к добавлению аккаунта
        </button>
      </div>
    </div>
  `;

  // 3. AI Providers & Models Guide
  window.HELP_CONTENT['ai_models'] = `
    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
      <div>
        <h4 class="fw-bold mb-1 text-info d-flex align-items-center gap-2">
          <i class="bi bi-cpu-fill"></i> ИИ Провайдеры, Модели и Ключи
        </h4>
        <p class="text-muted small mb-0">Как подключать и переключать облачные и локальные модели машинного обучения.</p>
      </div>
      <button class="btn btn-outline-info btn-sm rounded-pill d-flex align-items-center gap-1" data-jump-tab="tab-admin">
        <i class="bi bi-key-fill"></i> Управление ключами
      </button>
    </div>

    <div class="row g-3 mb-4">
      <!-- Gemini -->
      <div class="col-md-6">
        <div class="card h-100 border shadow-sm">
          <div class="card-header bg-primary text-white py-2 fw-bold d-flex justify-content-between align-items-center">
            <span>✨ Google Gemini</span>
            <span class="badge bg-light text-primary">Облако</span>
          </div>
          <div class="card-body p-3 small">
            <p class="mb-2">Быстрые мультимодальные модели (текст, код, изображения, RAG). Поддерживаются <code>gemini-2.5-flash</code> и <code>gemini-2.5-pro</code>.</p>
            <p class="mb-1 text-muted"><strong>Ключ API:</strong> Получите бесплатно в <a href="https://aistudio.google.com/app/apikey" target="_blank" class="text-primary text-decoration-none">Google AI Studio <i class="bi bi-box-arrow-up-right"></i></a>.</p>
            <p class="mb-0 text-muted">Укажите в файле <code>.env</code> параметр <code>GEMINI_API_KEY_1=AIzaSy...</code></p>
          </div>
        </div>
      </div>

      <!-- Ollama -->
      <div class="col-md-6">
        <div class="card h-100 border shadow-sm">
          <div class="card-header bg-dark text-white py-2 fw-bold d-flex justify-content-between align-items-center">
            <span>🦙 Ollama</span>
            <span class="badge bg-success">100% Локально</span>
          </div>
          <div class="card-body p-3 small">
            <p class="mb-2">Локальный сервер нейросетей (Llama 3.2, Mistral, Qwen 2.5, DeepSeek). Работает без интернета и подписок.</p>
            <p class="mb-1 text-muted"><strong>Адрес:</strong> <code>http://localhost:11434</code></p>
            <div class="bg-body-secondary p-2 rounded font-monospace small mb-1 code-box d-flex justify-content-between align-items-center">
              <code>ollama run llama3.2</code>
              <button class="btn btn-sm btn-outline-secondary py-0 px-1 btn-copy-snippet" data-copy-text="ollama run llama3.2"><i class="bi bi-clipboard"></i></button>
            </div>
          </div>
        </div>
      </div>

      <!-- Foundry Local -->
      <div class="col-md-6">
        <div class="card h-100 border shadow-sm">
          <div class="card-header bg-info text-dark py-2 fw-bold d-flex justify-content-between align-items-center">
            <span>🔷 Microsoft Foundry Local</span>
            <span class="badge bg-primary text-white">DirectML / NPU</span>
          </div>
          <div class="card-body p-3 small">
            <p class="mb-2">Оптимизированные для Windows и DirectML модели семейства Phi (Phi-3.5, Phi-4). Аппаратное ускорение на GPU и NPU.</p>
            <p class="mb-0 text-muted"><strong>Адрес:</strong> <code>http://localhost:54837</code></p>
          </div>
        </div>
      </div>

      <!-- OpenAI & Groq -->
      <div class="col-md-6">
        <div class="card h-100 border shadow-sm">
          <div class="card-header bg-secondary text-white py-2 fw-bold d-flex justify-content-between align-items-center">
            <span>🌐 OpenAI / Groq / HuggingFace</span>
            <span class="badge bg-light text-secondary">Совместимые</span>
          </div>
          <div class="card-body p-3 small">
            <p class="mb-2">Подключение любых сторонних провайдеров через OpenAI-совместимый API протокол.</p>
            <p class="mb-0 text-muted">Настраивается в <code>config.json</code> и через вкладку «Управление ключами».</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card border-info-subtle bg-body-tertiary shadow-sm p-3">
      <h6 class="fw-bold text-info mb-1"><i class="bi bi-magic me-1"></i> Как быстро переключить модель в диалоге?</h6>
      <p class="small text-secondary mb-0">В верхней панели чата нажмите на бейдж активной модели <code>🤖 Модель: ...</code> и выберите нужный провайдер из списка. Переключение происходит мгновенно без перезагрузки сервера.</p>
    </div>
  `;

  // 4. Google Drive Sync Guide
  window.HELP_CONTENT['gdrive_sync'] = `
    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
      <div>
        <h4 class="fw-bold mb-1 text-success d-flex align-items-center gap-2">
          <i class="bi bi-cloud-arrow-up-fill"></i> Синхронизация и Бэкап на Google Drive
        </h4>
        <p class="text-muted small mb-0">Автоматическое сохранение баз данных, RAG индексов, логов и настроек в облако.</p>
      </div>
    </div>

    <p class="small text-secondary">
      Модуль Google Drive Sync обеспечивает полную сохранность вашего рабочего пространства. Все данные шифруются и загружаются в изолированную папку <code>AI-Breadboard-Sync</code> на вашем Google Drive.
    </p>

    <h5 class="fw-bold mb-2">📦 Что входит в резервную копию:</h5>
    <ul class="small text-secondary mb-3">
      <li>📁 <strong>data/</strong> — базы данных SQLite, пользовательские RAG-индексы и история сессий.</li>
      <li>🔑 <strong>src/secrets/</strong> — защищенные токены доступа и конфигурации ключей.</li>
      <li>⚙️ <strong>config.json, .env</strong> — настройки сервера и переменные окружения.</li>
      <li>📝 <strong>logs/</strong> — журнал работы и аналитика системных событий.</li>
    </ul>

    <h5 class="fw-bold mb-2">🚀 Команды управления синхронизацией:</h5>
    <div class="table-responsive small mb-3">
      <table class="table table-bordered table-sm align-middle">
        <thead class="table-light">
          <tr><th>Команда</th><th>Описание</th><th>Действие</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><code>.\\sync.ps1 init</code></td>
            <td>Первичная инициализация папки и проверка связи с Google Drive API</td>
            <td><button class="btn btn-outline-secondary btn-sm py-0 px-2 btn-copy-snippet" data-copy-text=".\\sync.ps1 init">Копировать</button></td>
          </tr>
          <tr>
            <td><code>.\\sync.ps1 sync</code></td>
            <td>Запуск мгновенной синхронизации (разовый бэкап)</td>
            <td><button class="btn btn-outline-secondary btn-sm py-0 px-2 btn-copy-snippet" data-copy-text=".\\sync.ps1 sync">Копировать</button></td>
          </tr>
          <tr>
            <td><code>.\\sync.ps1 start</code></td>
            <td>Запуск автоматического фонового мониторинга с периодической синхронизацией</td>
            <td><button class="btn btn-outline-secondary btn-sm py-0 px-2 btn-copy-snippet" data-copy-text=".\\sync.ps1 start">Копировать</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  `;

  // 5. RAG & Knowledge Base Guide
  window.HELP_CONTENT['rag_knowledge'] = `
    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
      <div>
        <h4 class="fw-bold mb-1 text-warning d-flex align-items-center gap-2">
          <i class="bi bi-journal-bookmark-fill"></i> База знаний и RAG (Поиск по документам)
        </h4>
        <p class="text-muted small mb-0">Как наполнять базу знаний и общаться с вашими документами с точностью до цитаты.</p>
      </div>
      <button class="btn btn-warning btn-sm rounded-pill d-flex align-items-center gap-1" data-jump-tab="tab-rag">
        <i class="bi bi-folder2-open"></i> Открыть RAG
      </button>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div class="card h-100 border p-3 shadow-sm text-center">
          <div class="fs-2 text-warning mb-1"><i class="bi bi-file-earmark-arrow-up-fill"></i></div>
          <h6 class="fw-bold mb-1">1. Загрузка</h6>
          <p class="small text-muted mb-0">Поддерживаются форматы: PDF, DOCX, TXT, Markdown, CSV, JSON, ZIP.</p>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card h-100 border p-3 shadow-sm text-center">
          <div class="fs-2 text-primary mb-1"><i class="bi bi-funnel-fill"></i></div>
          <h6 class="fw-bold mb-1">2. Очистка (Cleaner)</h6>
          <p class="small text-muted mb-0">Автоматическая нормализация кодировок, удаление шума и разбиение на смысловые фрагменты.</p>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card h-100 border p-3 shadow-sm text-center">
          <div class="fs-2 text-success mb-1"><i class="bi bi-search-heart-fill"></i></div>
          <h6 class="fw-bold mb-1">3. Семантический поиск</h6>
          <p class="small text-muted mb-0">Векторный поиск находит ответы даже при несовпадении точных формулировок.</p>
        </div>
      </div>
    </div>

    <h5 class="fw-bold mb-2">💡 Как использовать в диалоге:</h5>
    <ol class="small text-secondary ps-3 mb-3">
      <li class="mb-1">Перейдите во вкладку <strong>«RAG»</strong> и загрузите ваши файлы через кнопку <em>«➕ Загрузить файл»</em>.</li>
      <li class="mb-1">В окне чата убедитесь, что включен тумблер <strong>«Использовать базу знаний (RAG)»</strong> под полем ввода.</li>
      <li class="mb-1">Задайте вопрос своими словами (например: <em>«Что говорится в договоре о сроках поставки?»</em>). Ассистент приведет точный ответ и сошлется на документ.</li>
    </ol>
  `;

  // 6. Voice & TTS Guide
  window.HELP_CONTENT['voice_tts'] = `
    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
      <div>
        <h4 class="fw-bold mb-1 text-primary d-flex align-items-center gap-2">
          <i class="bi bi-mic-fill"></i> Голосовое управление, Диаризация и Озвучка
        </h4>
        <p class="text-muted small mb-0">Распознавание речи, разделение спикеров и синтез ответов естественным голосом.</p>
      </div>
      <button class="btn btn-outline-primary btn-sm rounded-pill d-flex align-items-center gap-1" data-jump-tab="tab-voice">
        <i class="bi bi-soundwave"></i> Голосовой модуль
      </button>
    </div>

    <div class="card mb-3 border shadow-sm">
      <div class="card-header bg-body-tertiary fw-bold small"><i class="bi bi-mic text-primary me-1"></i> Распознавание речи (STT)</div>
      <div class="card-body p-3 small">
        <p class="mb-2">Вы можете надиктовывать сообщения прямо в микрофон. Поддерживаются два режима:</p>
        <ul class="mb-0 ps-3">
          <li><strong>Web Speech API</strong> — быстрое распознавание средствами браузера без нагрузки на процессор.</li>
          <li><strong>OpenAI Whisper / Диаризация</strong> — студийная точность локального распознавания с автоматическим разделением реплик разных собеседников (Спикер 1, Спикер 2).</li>
        </ul>
      </div>
    </div>

    <div class="card mb-3 border shadow-sm">
      <div class="card-header bg-body-tertiary fw-bold small"><i class="bi bi-volume-up text-success me-1"></i> Синтез речи (TTS)</div>
      <div class="card-body p-3 small">
        <p class="mb-2">Озвучивание ответов AI естественными нейросетевыми голосами Microsoft Edge TTS (русский, английский, иврит) без необходимости платных подписок.</p>
        <div class="d-flex gap-2">
          <span class="badge bg-secondary">ru-RU-SvetlanaNeural</span>
          <span class="badge bg-secondary">ru-RU-DmitryNeural</span>
          <span class="badge bg-secondary">en-US-JennyNeural</span>
        </div>
      </div>
    </div>

    <div class="card border shadow-sm">
      <div class="card-header bg-body-tertiary fw-bold small"><i class="bi bi-phone text-info me-1"></i> Удаленный микрофон (Remote Mic)</div>
      <div class="card-body p-3 small">
        <p class="mb-0">Откройте страницу <code>/remote_mic</code> на вашем смартфоне в домашней Wi-Fi сети для использования телефона в качестве беспроводного микрофона для AI Breadboard.</p>
      </div>
    </div>
  `;

  // 7. Plugins, Skills & MCP Guide
  window.HELP_CONTENT['plugins_skills'] = `
    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
      <div>
        <h4 class="fw-bold mb-1 text-secondary d-flex align-items-center gap-2">
          <i class="bi bi-plugin"></i> Плагины, Навыки (Skills) и MCP-серверы
        </h4>
        <p class="text-muted small mb-0">Расширение возможностей ассистента внешними инструментами и сервисами.</p>
      </div>
      <button class="btn btn-outline-secondary btn-sm rounded-pill d-flex align-items-center gap-1" data-jump-tab="tab-plugins">
        <i class="bi bi-grid-3x3-gap-fill"></i> Управление плагинами
      </button>
    </div>

    <div class="row g-3 mb-3">
      <div class="col-md-6">
        <div class="card h-100 border shadow-sm p-3">
          <h6 class="fw-bold d-flex align-items-center gap-2 text-primary">
            <i class="bi bi-telegram"></i> Telegram Bot
          </h6>
          <p class="small text-secondary mb-2">Управляйте ассистентом через Telegram. Укажите токен <code>TELEGRAM_BOT_TOKEN</code> в файле <code>.env</code>.</p>
          <div class="text-muted small">Пользователи связывают Telegram с личным аккаунтом через быструю ссылку в боте.</div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card h-100 border shadow-sm p-3">
          <h6 class="fw-bold d-flex align-items-center gap-2 text-warning">
            <i class="bi bi-house-gear-fill"></i> IFTTT (Умный дом)
          </h6>
          <p class="small text-secondary mb-2">Интеграция с умными розетками, освещением и бытовой техникой через вебхуки IFTTT Maker.</p>
          <div class="text-muted small">Параметр: <code>IFTTT_WEBHOOK_KEY</code> в файле <code>.env</code>.</div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card h-100 border shadow-sm p-3">
          <h6 class="fw-bold d-flex align-items-center gap-2 text-success">
            <i class="bi bi-receipt"></i> Invoice Extractor
          </h6>
          <p class="small text-secondary mb-0">Автоматическое распознавание реквизитов, сумм и позиций со счетов и квитанций с экспортом в Google Sheets.</p>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card h-100 border shadow-sm p-3">
          <h6 class="fw-bold d-flex align-items-center gap-2 text-info">
            <i class="bi bi-diagram-3-fill"></i> MCP (Model Context Protocol)
          </h6>
          <p class="small text-secondary mb-0">Подключение внешних серверов инструментов по открытому стандарту MCP для прямого доступа к базам данных и API.</p>
        </div>
      </div>
    </div>
  `;

  // 8. Storage & Disks Guide
  window.HELP_CONTENT['storage_disks'] = `
    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
      <div>
        <h4 class="fw-bold mb-1 text-dark d-flex align-items-center gap-2">
          <i class="bi bi-hdd-network-fill"></i> Диски, Хранилище и Медиатека
        </h4>
        <p class="text-muted small mb-0">Управление накопителями, проверка целостности и консолидация дубликатов.</p>
      </div>
      <button class="btn btn-outline-dark btn-sm rounded-pill d-flex align-items-center gap-1" data-jump-tab="tab-admin">
        <i class="bi bi-hdd-stack"></i> Панель хранилища
      </button>
    </div>

    <div class="card mb-3 border shadow-sm">
      <div class="card-body p-3 small">
        <h6 class="fw-bold mb-2">🔍 Автоматический аудит накопителей:</h6>
        <p class="text-secondary mb-2">Система автоматически сканирует подключенные физические и сетевые диски по их меткам и серийным номерам.</p>
        <ul class="mb-0 ps-3">
          <li><strong>Проверка целостности (Integrity Check):</strong> выявление поврежденных или перемещенных файлов.</li>
          <li><strong>Дедупликация (Duplicate Consolidation):</strong> объединение дублирующихся метаданных и записей в SQLite.</li>
        </ul>
      </div>
    </div>
  `;

  // 9. Troubleshooting & FAQ
  window.HELP_CONTENT['troubleshooting'] = `
    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
      <div>
        <h4 class="fw-bold mb-1 text-danger d-flex align-items-center gap-2">
          <i class="bi bi-question-diamond-fill"></i> Частые вопросы и Решение проблем (FAQ)
        </h4>
        <p class="text-muted small mb-0">Ответы на типичные вопросы и способы устранения ошибок.</p>
      </div>
    </div>

    <div class="accordion mb-3 shadow-sm" id="faqAccordion">
      <!-- Q1 -->
      <div class="accordion-item">
        <h2 class="accordion-header">
          <button class="accordion-button collapsed fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#faq1">
            ❓ Ошибка «Redirect URI mismatch» при входе через Google OAuth
          </button>
        </h2>
        <div id="faq1" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
          <div class="accordion-body small text-secondary">
            Убедитесь, что в Google Cloud Console для вашего OAuth Client ID в разделе <strong>Authorized redirect URIs</strong> указан точный адрес вашего сервера (например, <code>http://localhost:8000/auth/google/callback</code> или <code>https://your-domain/auth/google/callback</code>).
          </div>
        </div>
      </div>

      <!-- Q2 -->
      <div class="accordion-item">
        <h2 class="accordion-header">
          <button class="accordion-button collapsed fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#faq2">
            ❓ Локальная модель Ollama или Foundry не отвечает
          </button>
        </h2>
        <div id="faq2" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
          <div class="accordion-body small text-secondary">
            Проверьте, запущен ли демон локальной модели:
            <ul class="mb-2 mt-1">
              <li>Для Ollama: выполните команду <code>ollama list</code> в терминале и убедитесь, что порт <code>11434</code> доступен.</li>
              <li>Для Foundry: проверьте статус службы на порту <code>54837</code>.</li>
            </ul>
            Если модель не скачана, выполните в терминале <code>ollama pull llama3.2</code>.
          </div>
        </div>
      </div>

      <!-- Q3 -->
      <div class="accordion-item">
        <h2 class="accordion-header">
          <button class="accordion-button collapsed fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#faq3">
            ❓ Предупреждение о сертификате SSL при локальном запуске по HTTPS
          </button>
        </h2>
        <div id="faq3" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
          <div class="accordion-body small text-secondary">
            Запустите встроенный генератор доверенных локальных сертификатов через команду <code>py manage_tools.py cert-installer install</code> или используйте скрипт <code>.\install.ps1</code>.
          </div>
        </div>
      </div>

      <!-- Q4 -->
      <div class="accordion-item">
        <h2 class="accordion-header">
          <button class="accordion-button collapsed fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#faq4">
            ❓ Как проверить подробные системные логи при сбоях?
          </button>
        </h2>
        <div id="faq4" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
          <div class="accordion-body small text-secondary">
            Перейдите во вкладку <strong>«Управление» ➜ «Логи»</strong> или запустите анализатор логов: <code>py manage_tools.py log-analyzer check</code>.
          </div>
        </div>
      </div>
    </div>
  `;

  console.log('HELP content initialized');
}

// Show help modal
function showHelpModal(key) {
  const content = window.HELP_CONTENT[key] || '<p>Информация не найдена</p>';
  document.getElementById('help-modal-content').innerHTML = content;
  
  const modal = new bootstrap.Modal(document.getElementById('help-modal'));
  modal.show();
}

// Show help tooltip/popover for element
function showHelpTooltip(element, content) {
  const options = {
    title: 'Помощь',
    content: content,
    html: true,
    placement: 'top',
    trigger: 'hover focus'
  };
  
  const popover = new bootstrap.Popover(element, options);
  popover.show();
}
