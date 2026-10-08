/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/search_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/search_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

// Search Tab Logic - Web Search MCP Providers Management

async function initSearchTab() {
  const engineSelect = document.getElementById('search-tab-engine-selector');
  const btnSaveEngine = document.getElementById('btn-save-search-tab-engine');
  const btnSaveParams = document.getElementById('btn-save-search-params');
  const geminiModelSelect = document.getElementById('search-gemini-model');
  const geminiCliModelSelect = document.getElementById('search-gemini-cli-model');
  const agyModelSelect = document.getElementById('search-agy-model');
  const engineBadge = document.getElementById('test-search-engine-badge');
  const btnRunTest = document.getElementById('btn-run-test-search');
  const testQueryInput = document.getElementById('test-search-query-input');
  const testOutputContainer = document.getElementById('test-search-output-container');

  if (!engineSelect) return;

  // --- 1. Load Dynamic Models via SDK / Tools ---
  async function loadModels() {
    try {
      const modelsData = await window.api.fetch('/api/chat/models');
      const modelsGrouped = modelsData.models || {};
      const geminiList = modelsGrouped.gemini || [];
      const geminiCliList = modelsGrouped.gemini_cli || ['gemini-3.1-flash-lite', 'gemini-3.5-flash-lite', 'gemini-2.5-pro'];
      const agyList = modelsGrouped.agy || [];

      if (geminiModelSelect && geminiList.length > 0) {
        const curVal = geminiModelSelect.value;
        geminiModelSelect.innerHTML = '';
        geminiList.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m;
          opt.textContent = m;
          geminiModelSelect.appendChild(opt);
        });
        if (curVal && geminiList.includes(curVal)) {
          geminiModelSelect.value = curVal;
        }
      }

      if (geminiCliModelSelect && geminiCliList.length > 0) {
        const curVal = geminiCliModelSelect.value;
        geminiCliModelSelect.innerHTML = '';
        geminiCliList.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m;
          opt.textContent = m;
          geminiCliModelSelect.appendChild(opt);
        });
        if (curVal && geminiCliList.includes(curVal)) {
          geminiCliModelSelect.value = curVal;
        } else if (geminiCliList.includes('gemini-3.1-flash-lite')) {
          geminiCliModelSelect.value = 'gemini-3.1-flash-lite';
        }
      }

      if (agyModelSelect && agyList.length > 0) {
        const curVal = agyModelSelect.value;
        agyModelSelect.innerHTML = '';
        agyList.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m;
          opt.textContent = m;
          agyModelSelect.appendChild(opt);
        });
        if (curVal && agyList.includes(curVal)) {
          agyModelSelect.value = curVal;
        }
      }
    } catch (err) {
      console.error(i18n.t('auto__searchtab_sdk_cli__7270c1'), err);
    }
  }

  // --- 2. Load Current Config ---
  async function loadConfig() {
    try {
      await loadModels();
      const data = await window.api.fetch('/api/admin/web-search/config');
      if (data) {
        if (data.engine && engineSelect) {
          engineSelect.value = data.engine;
          if (engineBadge) engineBadge.textContent = data.engine;
        }
        if (data.gemini_model && geminiModelSelect) {
          geminiModelSelect.value = data.gemini_model;
        }
        if (data.gemini_cli_model && geminiCliModelSelect) {
          geminiCliModelSelect.value = data.gemini_cli_model;
        }
        if (data.agy_model && agyModelSelect) {
          agyModelSelect.value = data.agy_model;
        }
      }
    } catch (e) {
      console.error(i18n.t('auto__searchtab__7da013'), e);
      notifySearch(i18n.t('auto___e42477') + e.message, 'danger');
    }
  }

  // --- 3. Save Config Helper ---
  async function saveConfig() {
    const engine = engineSelect ? engineSelect.value : 'playwright';
    const gemini_model = geminiModelSelect ? geminiModelSelect.value : 'gemini-flash-lite-latest';
    const gemini_cli_model = geminiCliModelSelect ? geminiCliModelSelect.value : 'gemini-3.1-flash-lite';
    const agy_model = agyModelSelect ? agyModelSelect.value : 'agy-flash';

    try {
      await window.api.fetch('/api/admin/web-search/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_engine_gemini_model_gemini_cli_model_agy_model_if_enginebadge_enginebadge_textcontent_engine_notifysearch_engine__b64f73')success');

      let compoundSearch = engine;
      if (engine === 'gemini') compoundSearch = `${engine}:${gemini_model}`;
      if (engine === 'gemini_cli') compoundSearch = `${engine}:${gemini_cli_model}`;
      if (engine === 'agy') compoundSearch = `${engine}:${agy_model}`;

      if (typeof window.updateChatBadges === 'function') {
        window.updateChatBadges(undefined, compoundSearch);
      }
    } catch (e) {
      console.error(i18n.t('auto__searchtab__5cc756'), e);
      notifySearch(i18n.t('auto___e764d2') + e.message, 'danger');
    }
  }

  if (btnSaveEngine) btnSaveEngine.onclick = saveConfig;
  if (btnSaveParams) btnSaveParams.onclick = saveConfig;

  if (engineSelect) {
    engineSelect.onchange = () => {
      if (engineBadge) engineBadge.textContent = engineSelect.value;
    };
  }

  // --- 3. Interactive Search Tester ---
  if (btnRunTest && testQueryInput && testOutputContainer) {
    const runTest = async () => {
      const query = testQueryInput.value.trim();
      if (!query) {
        notifySearch(i18n.t('auto___8c3c4c'), 'warning');
        testQueryInput.focus();
        return;
      }

      const engine = engineSelect ? engineSelect.value : 'playwright';
      btnRunTest.disabled = true;
      const originalText = btnRunTest.innerHTML;
      btnRunTest.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Поиск...';
      testOutputContainer.innerHTML = `<span class="text-infoi18n.t('auto__strong_engine_strong__636285')${query}"...</span>`;

      try {
        const response = await window.api.fetch('/api/admin/web-search/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, engine })
        });

        if (response.status === 'ok') {
          testOutputContainer.textContent = response.result || i18n.t('auto___70d1e8');
        } else {
          testOutputContainer.innerHTML = `<span class="text-danger">❌ Ошибка: ${response.message || i18n.t('auto___1047bb')}</span>`;
        }
      } catch (err) {
        console.error(i18n.t('auto__searchtab__facaf2'), err);
        testOutputContainer.innerHTML = `<span class="text-danger">❌ Ошибка запроса: ${err.message}</span>`;
      } finally {
        btnRunTest.disabled = false;
        btnRunTest.innerHTML = originalText;
      }
    };

    btnRunTest.onclick = runTest;
    testQueryInput.onkeydown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        runTest();
      }
    };
  }

  // Helper notification
  function notifySearch(msg, type = 'info') {
    if (typeof showNotification === 'function') {
      showNotification(msg, type);
    } else if (typeof showModelsNotification === 'function') {
      showModelsNotification(msg, type);
    } else {
      console.log(`[${type}] ${msg}`);
    }
  }

  await loadConfig();
}

window.initSearchTab = initSearchTab;
