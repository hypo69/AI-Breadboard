// ── MAIN.JS ───────────────────────────────────────────────────────────────────

import { initI18n, switchLang, applyTranslations } from './i18n.js';
import { initTheme, setTheme, getThemeMode, getResolvedTheme } from './theme.js';
import { initUserSettings, refreshUserProfile } from './userSettings.js';

// Make switchLang and theme functions available globally
window.switchLang = switchLang;
window.applyTranslations = applyTranslations;
window.setTheme = setTheme;
window.getThemeMode = getThemeMode;
window.getResolvedTheme = getResolvedTheme;
window.initUserSettings = initUserSettings;
window.refreshUserProfile = refreshUserProfile;

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

  
  await initHelpContent();
  console.log('HELP system initialized');
  
  console.log('Loading tabs...');
  const v = '20260908_chat_fixed_v9';
  await Promise.all([
    loadTabContent('chat', `/html/chat/index.html?v=${v}`, `/html/chat/main.js?v=${v}`),
    loadTabContent('rag', `/html/rag_tab/index.html?v=${v}`, `/html/rag_tab/main.js?v=${v}`),
    loadTabContent('voice', `/html/voice_tab/index.html?v=${v}`, `/html/voice_tab/main.js?v=${v}`),
    loadTabContent('plugins', `/html/plugins_tab/index.html?v=${v}`, `/html/plugins_tab/main.js?v=${v}`),
    loadTabContent('admin', `/html/admin/index.html?v=${v}`),
    loadTabContent('help', `/html/help/index.html?v=${v}`),
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
  console.log('Initialization complete');
});

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
    script.src = scriptUrl || `/html/${tabName}/main.js?v=20260908_chat_fixed_v9`;
    if (tabName === 'admin' || tabName === 'instructions' || tabName === 'rag') {
      script.type = 'module';
    }
    script.onload = () => {
      console.log(`✓ Загружен JS вкладки: ${tabName}`);
      // Call init function if exists
      if (window[`init${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`]) {
        window[`init${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`]();
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
  if (cleanId === 'tab-chat') {
    const msgInput = document.getElementById('message-input');
    if (msgInput) msgInput.focus();
  } else if (cleanId === 'tab-rag' && typeof window.initRagTab === 'function') {
    console.log('[MainInterface] Switching to RAG tab...');
    window.initRagTab();
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
// HELP content stored in JavaScript (will be populated from help tab)

window.HELP_CONTENT = {};

// Initialize HELP content when help tab is loaded
async function initHelpContent() {
  // Overview
  window.HELP_CONTENT['overview'] = `
    <h4>📋 Обзор проекта</h4>
    <p>ai-breadboard — это интегрированная платформа персонального AI-ассистента с поддержкой Google Gemini, Antigravity, Foundry, Ollama, RAG и системного управления.</p>
    <h5>Основные возможности</h5>
    <ul>
      <li><strong>Чат</strong> — диалог и выполнение команд через AI (Gemini, AGY, Foundry, Ollama)</li>
      <li><strong>Управление</strong> — мониторинг сервера, дисков, пользователей, API-ключей и логирование</li>
      <li><strong>Плагины</strong> — расширение возможностей через модульную систему</li>
      <li><strong>RAG и Агенты</strong> — семантический поиск по базам знаний и автономные ReAct-агенты</li>
    </ul>
  `;

  // Code Rules
  window.HELP_CONTENT['code_rules'] = `
    <h4>⚙️ Правила кодирования (CODE_RULES)</h4>
    <p>Проект использует Engineering Standard для поддержания качества кода.</p>
    <h5>Ключевые принципы</h5>
    <ul>
      <li><strong>Читаемость важнее краткости</strong></li>
      <li><strong>Принцип единственной ответственности</strong></li>
      <li><strong>Явное лучше неявного</strong></li>
      <li><strong>Ранний возврат и отказоустойчивость</strong></li>
    </ul>
    <h5>Запрещено использовать None</h5>
    <p>Вместо <code>None</code> использовать:</p>
    <ul>
      <li>Числа: <code>0</code> или <code>0.0</code></li>
      <li>Строки: <code>''</code> (пустая строка)</li>
      <li>Булевы: <code>false</code></li>
      <li>Коллекции: <code>[]</code> или <code>{}</code></li>
    </ul>
  `;

  // Architecture
  window.HELP_CONTENT['architecture'] = `
    <h4>🏗️ Архитектура</h4>
    <h5>Технологический стек</h5>
    <ul>
      <li><strong>FastAPI</strong> — веб-фреймворк для Python</li>
      <li><strong>UVicorn</strong> — ASGI сервер</li>
      <li><strong>Bootstrap 5</strong> — UI фреймворк</li>
      <li><strong>SQLite</strong> — база данных</li>
    </ul>
    <h5>AI интеграции</h5>
    <ul>
      <li><strong>Google Gemini / Antigravity / Foundry / Ollama</strong> — генерация контента и инференс</li>
      <li><strong>RAG</strong> — семантический поиск по документам и истории</li>
      <li><strong>LangChain Agents</strong> — автономные ReAct-агенты</li>
    </ul>
  `;

  // FastAPI
  window.HELP_CONTENT['fastapi'] = `
    <h4>🚀 FastAPI</h4>
    <h5>Роутеры</h5>
    <table class="table table-sm">
      <tr><td><code>/api/chat</code></td><td>Взаимодействие с AI моделями и WS-чат</td></tr>
      <tr><td><code>/api/admin</code></td><td>Системное администрирование, пользователи и плагины</td></tr>
      <tr><td><code>/api/control</code></td><td>Управление сессиями и накопителями (дисками)</td></tr>
      <tr><td><code>/api/keys</code></td><td>Управление API-ключами и моделями</td></tr>
      <tr><td><code>/api/logs</code></td><td>Системные логи и аналитика</td></tr>
    </table>
    <h5>Конфигурация</h5>
    <p>Файл: <code>config.json</code></p>
  `;

  // Gemini
  window.HELP_CONTENT['gemini'] = `
    <h4>🧠 Gemini AI</h4>
    <h5>Использование</h5>
    <ul>
      <li>Генерация метаданных для медиа</li>
      <li>Классификация по жанрам</li>
      <li>Генерация описаний и рецензий</li>
      <li>Поиск по RAG-индексу</li>
    </ul>
    <h5>Управление ключами</h5>
    <p>Файл: <code>src/secrets/gemini_keys.json</code></p>
  `;

  // Configuration
  window.HELP_CONTENT['configuration'] = `
    <h4>⚙️ Конфигурация</h4>
    <h5>Файлы конфигурации</h5>
    <table class="table table-sm">
      <tr><td><code>.env</code></td><td>Секреты (API ключи, пароли)</td></tr>
      <tr><td><code>src/fastapi/config.json</code></td><td>Публичные настройки</td></tr>
      <tr><td><code>plugins/media_organizer/media_paths.txt</code></td><td>Пути к медиатеке</td></tr>
    </table>
  `;

  // CLI Commands
  window.HELP_CONTENT['cli_commands'] = `
    <h4>⌨️ Командная строка</h4>
    <p>Все команды медиатеки доступны в CLI и веб-интерфейсе.</p>
    
    <h5>run_media_organizer.py</h5>
    <p>Полный функционал управления медиатекой:</p>
    <table class="table table-sm">
      <tr><td><code>--disk 1</code></td><td>Имя диска (например: 1, 2, 3)</td></tr>
      <tr><td><code>--path E: L:</code></td><td>Пути для сканирования</td></tr>
      <tr><td><code>--key имя_ключа</code></td><td>Ключ Gemini API</td></tr>
      <tr><td><code>--title</code></td><td>Генерация отчёта из БД</td></tr>
      <tr><td><code>--audit</code></td><td>Только аудит (без сканирования)</td></tr>
      <tr><td><code>--rebuild</code></td><td>Восстановление из JSON</td></tr>
      <tr><td><code>--rebuild-db</code></td><td>Консолидация дублей в БД</td></tr>
      <tr><td><code>--rebuild-rag</code></td><td>Перестройка RAG-индекса</td></tr>
    </table>
    
    <h5>series_collector.py</h5>
    <p>Сбор и анализ эпизодов:</p>
    <table class="table table-sm">
      <tr><td><code>--scan</code></td><td>Сканирование сериалов</td></tr>
      <tr><td><code>--duplicates</code></td><td>Проверка дубликатов</td></tr>
      <tr><td><code>--integrity</code></td><td>Проверка целостности</td></tr>
      <tr><td><code>--report</code></td><td>Генерация отчёта</td></tr>
      <tr><td><code>--all</code></td><td>Все проверки сразу</td></tr>
    </table>
    
    <h5>Примеры:</h5>
    <pre><code>
# Полное сканирование диска 1
py run_media_organizer.py --disk 1 --path E: L:

# Только аудит без сканирования
py run_media_organizer.py --disk 2 --audit

# Генерация отчёта из БД
py run_media_organizer.py --disk 1 --title

# Консолидация дублей
py run_media_organizer.py --rebuild-db

# Сканирование сериалов
py series_collector.py --scan

# Все проверки сразу
py series_collector.py --all
    </code></pre>
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
