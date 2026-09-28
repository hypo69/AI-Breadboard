// Gemini Models & APIs management tab logic

let modelTestAbortController = null;

function cancelModelTest() {
  if (modelTestAbortController) {
    try {
      modelTestAbortController.abort();
    } catch (e) {
      console.warn('Error aborting model test:', e);
    }
    modelTestAbortController = null;
  }
}

async function initModelsTab() {
  window.api = window.api || {};
  if (!window.api.fetch) {
    window.api.fetch = async function(url, options = {}) {
      const response = await fetch(url, options);
      if (!response.ok) {
        let msg = response.statusText;
        try {
          const data = await response.json();
          if (data && data.detail) {
            if (typeof data.detail === 'string') msg = data.detail;
            else if (Array.isArray(data.detail)) msg = data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
            else msg = JSON.stringify(data.detail);
          } else if (data && data.message) {
            msg = data.message;
          }
        } catch {}
        throw new Error(`${response.status} ${msg}`);
      }
      return response.json();
    };
  }

  const modelSelect = document.getElementById('models-tab-select');
  const saveBtn = document.getElementById('btn-models-tab-save');
  const keysListBody = document.getElementById('keys-list-body');
  const refreshKeysBtn = document.getElementById('btn-refresh-keys');
  const addKeyBtn = document.getElementById('btn-add-key');
  const saveAgyBtn = document.getElementById('btn-save-agy');
  const saveFoundryBtn = document.getElementById('btn-save-foundry');
  const saveOllamaBtn = document.getElementById('btn-save-ollama');
  const saveOnnxBtn = document.getElementById('btn-save-onnx');
  const saveBtnInstr = document.getElementById('btn-save-instruction');
  const reloadBtnInstr = document.getElementById('btn-reload-instruction');

  const gaccountsListBody = document.getElementById('gaccounts-list-body');
  const refreshGAccountsBtn = document.getElementById('btn-refresh-gaccounts');
  const addGAccountBtn = document.getElementById('btn-add-gacc');

  const refreshModelsBtn = document.getElementById('btn-refresh-models-list');
  const testModelBtn = document.getElementById('btn-model-test-send');
  const cancelModelBtn = document.getElementById('btn-model-test-cancel');
  const testModelPrompt = document.getElementById('model-test-prompt');

  // Ensure active provider pill tab pane has show active classes
  const activePill = document.querySelector('#provider-pills-tab .nav-link.active') || document.getElementById('pill-gemini-tab');
  if (activePill) {
    const targetSelector = activePill.getAttribute('data-bs-target');
    if (targetSelector) {
      const targetPane = document.querySelector(targetSelector);
      if (targetPane && !targetPane.classList.contains('active')) {
        targetPane.classList.add('show', 'active');
      }
    }
  }

  // 1. Bind event handlers immediately
  if (saveBtnInstr) saveBtnInstr.onclick = saveSystemInstruction;
  if (reloadBtnInstr) reloadBtnInstr.onclick = loadSystemInstruction;

  if (refreshModelsBtn && modelSelect && saveBtn) {
    refreshModelsBtn.onclick = async () => {
      refreshModelsBtn.disabled = true;
      const originalText = refreshModelsBtn.innerHTML;
      refreshModelsBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Обновление...';
      try {
        await loadTabModels(modelSelect, saveBtn, true);
      } finally {
        refreshModelsBtn.disabled = false;
        refreshModelsBtn.innerHTML = originalText;
      }
    };
  }

  const showAllModelsCheck = document.getElementById('show-all-models-check');
  if (showAllModelsCheck && modelSelect && saveBtn) {
    showAllModelsCheck.onchange = async () => {
      await loadTabModels(modelSelect, saveBtn, false);
    };
  }

  const favToggleBtn = document.getElementById('btn-model-toggle-favorite');
  const saveNoteBtn = document.getElementById('btn-save-model-note');
  const modelNoteInput = document.getElementById('model-user-note');

  if (favToggleBtn && modelSelect) {
    favToggleBtn.onclick = async () => {
      const curModel = modelSelect.value;
      if (!curModel) {
        showModelsNotification(i18n.t('auto___4509f6'), 'warning');
        return;
      }
      favToggleBtn.disabled = true;
      try {
        const isFav = window.userFavoriteModels && Boolean(window.userFavoriteModels[curModel]);
        if (isFav) {
          await window.api.fetch(`/auth/favorites/${encodeURIComponent(curModel)}`, { method: 'DELETE' });
          if (window.userFavoriteModels) delete window.userFavoriteModels[curModel];
          showModelsNotification(`Модель "${curModel}" удалена из избранного`, 'info');
        } else {
          const noteText = modelNoteInput ? modelNoteInput.value.trim() : '';
          const res = await window.api.fetch('/auth/favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: curModel, note: noteText })
          });
          if (res && res.favorites) window.userFavoriteModels = res.favorites;
          showModelsNotification(`Модель "${curModel}" добавлена в избранное ⭐`, 'success');
        }
        updateModelFavoriteUI(modelSelect);
        updateModelSelectOptions(modelSelect);
      } catch (err) {
        console.error(i18n.t('auto___01e549'), err);
        showModelsNotification(i18n.t('auto___8361fc') + err.message, 'danger');
      } finally {
        favToggleBtn.disabled = false;
      }
    };
  }

  if (saveNoteBtn && modelSelect && modelNoteInput) {
    saveNoteBtn.onclick = async () => {
      const curModel = modelSelect.value;
      if (!curModel) {
        showModelsNotification(i18n.t('auto___4509f6'), 'warning');
        return;
      }
      saveNoteBtn.disabled = true;
      const originalText = saveNoteBtn.innerHTML;
      saveNoteBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Сохранение...';
      try {
        const noteText = modelNoteInput.value.trim();
        const res = await window.api.fetch('/auth/favorites', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: curModel, note: noteText })
        });
        if (res && res.favorites) window.userFavoriteModels = res.favorites;
        showModelsNotification(`Заметка для модели "${curModel}" сохранена!`, 'success');
        updateModelFavoriteUI(modelSelect);
        updateModelSelectOptions(modelSelect);
      } catch (err) {
        console.error(i18n.t('auto___d0bb13'), err);
        showModelsNotification(i18n.t('auto___8561a8') + err.message, 'danger');
      } finally {
        saveNoteBtn.disabled = false;
        saveNoteBtn.innerHTML = originalText;
      }
    };
  }

  if (modelSelect) {
    modelSelect.addEventListener('change', () => {
      updateModelFavoriteUI(modelSelect);
    });
  }

  if (testModelBtn) {
    testModelBtn.onclick = executeModelTest;
  }

  if (cancelModelBtn) {
    cancelModelBtn.onclick = cancelModelTest;
  }

  if (testModelPrompt) {
    testModelPrompt.onkeydown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        executeModelTest();
      } else if (e.key === 'Escape' && modelTestAbortController) {
        e.preventDefault();
        cancelModelTest();
      }
    };
  }

  // Provider switch direct toggling
  const agyEnabledSwitch = document.getElementById('agy-enabled');
  if (agyEnabledSwitch) {
    agyEnabledSwitch.onchange = async () => {
      const enabled = agyEnabledSwitch.checked;
      const remember = document.getElementById('agy-remember')?.checked ?? true;
      const model = document.getElementById('agy-model')?.value || 'agy-flash';
      const key = document.getElementById('agy-key')?.value.trim() || '';

      try {
        await window.api.fetch('/api/agy/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, model, key, remember })
        });
        showModelsNotification(`Google Antigravity (AGY) ${enabled ? i18n.t('auto___ff0947') : i18n.t('auto___c98893')}${remember ? i18n.t('auto__config_json__246284') : ''}`, 'info');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error(i18n.t('auto__antigravity__c76fc9'), err);
        showModelsNotification(i18n.t('auto___932df8') + err.message, 'danger');
      }
    };
  }

  const foundryEnabledSwitch = document.getElementById('foundry-enabled');
  if (foundryEnabledSwitch) {
    foundryEnabledSwitch.onchange = async () => {
      const enabled = foundryEnabledSwitch.checked;
      const remember = document.getElementById('foundry-remember')?.checked ?? true;
      const url = document.getElementById('foundry-url')?.value.trim() || 'http://localhost:54837';
      const key = document.getElementById('foundry-key')?.value.trim() || '';
      const model = document.getElementById('foundry-model')?.value?.trim() || 'qwen2.5-1.5b';

      try {
        await window.api.fetch('/api/foundry/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, url, key, model, remember })
        });
        showModelsNotification(`Microsoft Foundry ${enabled ? i18n.t('auto___ff0947') : i18n.t('auto___c98893')}${remember ? i18n.t('auto__config_json__246284') : ''}`, 'info');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error(i18n.t('auto__foundry__d92256'), err);
        showModelsNotification(i18n.t('auto___932df8') + err.message, 'danger');
      }
    };
  }

  const ollamaEnabledSwitch = document.getElementById('ollama-enabled');
  if (ollamaEnabledSwitch) {
    ollamaEnabledSwitch.onchange = async () => {
      const enabled = ollamaEnabledSwitch.checked;
      const remember = document.getElementById('ollama-remember')?.checked ?? true;
      const url = document.getElementById('ollama-url')?.value.trim() || 'http://localhost:11434';
      const model = document.getElementById('ollama-model')?.value?.trim() || 'llama3.1';

      try {
        await window.api.fetch('/api/ollama/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, url, model, remember })
        });
        showModelsNotification(`Ollama ${enabled ? i18n.t('auto___ff0947') : i18n.t('auto___c98893')}${remember ? i18n.t('auto__config_json__246284') : ''}`, 'info');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error(i18n.t('auto__ollama__d3a078'), err);
        showModelsNotification(i18n.t('auto___932df8') + err.message, 'danger');
      }
    };
  }

  const onnxEnabledSwitch = document.getElementById('onnx-enabled');
  if (onnxEnabledSwitch) {
    onnxEnabledSwitch.onchange = async () => {
      const enabled = onnxEnabledSwitch.checked;
      const remember = document.getElementById('onnx-remember')?.checked ?? true;
      const execution_provider = document.getElementById('onnx-execution-provider')?.value || 'DirectMLExecutionProvider';
      const models_dir = document.getElementById('onnx-models-dir')?.value.trim() || 'models/onnx';
      const default_model = document.getElementById('onnx-default-model')?.value.trim() || 'phi-3.5-mini-instruct-onnx';
      const olive_precision = document.getElementById('onnx-olive-precision')?.value || 'int4';

      try {
        await window.api.fetch('/api/onnx/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            enabled,
            execution_provider,
            models_dir,
            default_model,
            olive_precision,
            remember
          })
        });
        showModelsNotification(`ONNX / Olive ${enabled ? i18n.t('auto___ff0947') : i18n.t('auto___c98893')}${remember ? i18n.t('auto__config_json__246284') : ''}`, 'info');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error(i18n.t('auto__onnx_olive__cc6394'), err);
        showModelsNotification(i18n.t('auto___932df8') + err.message, 'danger');
      }
    };
  }

  if (saveAgyBtn) {
    saveAgyBtn.onclick = async () => {
      const enabled = document.getElementById('agy-enabled')?.checked ?? true;
      const remember = document.getElementById('agy-remember')?.checked ?? true;
      const model = document.getElementById('agy-model')?.value || 'agy-flash';
      const key = document.getElementById('agy-key')?.value.trim() || '';

      saveAgyBtn.disabled = true;
      try {
        await window.api.fetch('/api/agy/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_enabled_model_key_remember_showmodelsnotification_antigravity_agy_remember__dc175e') в config.json' : ''}`, 'success');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error(i18n.t('auto__antigravity__3ed2ca'), err);
        showModelsNotification(i18n.t('auto___bbbabd') + err.message, 'danger');
      } finally {
        saveAgyBtn.disabled = false;
      }
    };
  }

  if (saveFoundryBtn) {
    saveFoundryBtn.onclick = async () => {
      const enabled = document.getElementById('foundry-enabled')?.checked || false;
      const remember = document.getElementById('foundry-remember')?.checked ?? true;
      const url = document.getElementById('foundry-url')?.value.trim() || 'http://localhost:54837';
      const key = document.getElementById('foundry-key')?.value.trim() || '';
      const model = document.getElementById('foundry-model')?.value?.trim() || 'qwen2.5-1.5b';
      
      saveFoundryBtn.disabled = true;
      try {
        await window.api.fetch('/api/foundry/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_enabled_url_key_model_remember_showmodelsnotification_microsoft_foundry_remember__f4e2cc') в config.json' : ''}`, 'success');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error(i18n.t('auto__foundry__301fb0'), err);
        showModelsNotification(i18n.t('auto___bbbabd') + err.message, 'danger');
      } finally {
        saveFoundryBtn.disabled = false;
      }
    };
  }

  if (saveOllamaBtn) {
    saveOllamaBtn.onclick = async () => {
      const enabled = document.getElementById('ollama-enabled')?.checked || false;
      const remember = document.getElementById('ollama-remember')?.checked ?? true;
      const url = document.getElementById('ollama-url')?.value.trim() || 'http://localhost:11434';
      const model = document.getElementById('ollama-model')?.value?.trim() || 'llama3.1';
      
      saveOllamaBtn.disabled = true;
      try {
        await window.api.fetch('/api/ollama/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_enabled_url_model_remember_showmodelsnotification_ollama_remember__5f600b') в config.json' : ''}`, 'success');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error(i18n.t('auto__ollama__9b7c48'), err);
        showModelsNotification(i18n.t('auto___bbbabd') + err.message, 'danger');
      } finally {
        saveOllamaBtn.disabled = false;
      }
    };
  }

  if (saveOnnxBtn) {
    saveOnnxBtn.onclick = async () => {
      const enabled = document.getElementById('onnx-enabled')?.checked ?? true;
      const remember = document.getElementById('onnx-remember')?.checked ?? true;
      const execution_provider = document.getElementById('onnx-execution-provider')?.value || 'DirectMLExecutionProvider';
      const models_dir = document.getElementById('onnx-models-dir')?.value.trim() || 'models/onnx';
      const default_model = document.getElementById('onnx-default-model')?.value.trim() || 'phi-3.5-mini-instruct-onnx';
      const olive_precision = document.getElementById('onnx-olive-precision')?.value || 'int4';

      saveOnnxBtn.disabled = true;
      try {
        await window.api.fetch('/api/onnx/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_enabled_execution_provider_models_dir_default_model_olive_precision_remember_showmodelsnotification_onnx_olive_remember__0c79fc') в config.json' : ''}`, 'success');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error(i18n.t('auto__onnx_olive__2a27d3'), err);
        showModelsNotification(i18n.t('auto___bbbabd') + err.message, 'danger');
      } finally {
        saveOnnxBtn.disabled = false;
      }
    };
  }

  if (saveBtn && modelSelect) {
    saveBtn.onclick = async () => {
      const selectedModel = modelSelect.value;
      saveBtn.disabled = true;
      const originalText = saveBtn.textContent;
      saveBtn.textContent = i18n.t('auto___a91a7e');
      
      try {
        await window.api.fetch('/auth/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: selectedModel })
        });
        showModelsNotification(i18n.t('auto___4d96e2') + selectedModel, 'success');
        
        const otherModelSelect = document.getElementById('admin-model-select');
        if (otherModelSelect) {
          otherModelSelect.value = selectedModel;
        }
        if (typeof window.updateChatBadges === 'function') {
          window.updateChatBadges(selectedModel);
        }
      } catch (err) {
        console.error(i18n.t('auto___a9a82f'), err);
        showModelsNotification(i18n.t('auto___bbbabd') + err.message, 'danger');
      } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
      }
    };
  }

  if (refreshKeysBtn) {
    refreshKeysBtn.onclick = async () => {
      refreshKeysBtn.disabled = true;
      const originalText = refreshKeysBtn.textContent;
      refreshKeysBtn.textContent = i18n.t('auto___e4d50e');
      try {
        const res = await window.api.fetch('/api/keys/reset-all', { method: 'POST' });
        showModelsNotification(res.message || i18n.t('auto___c173d4'), 'success');
      } catch (err) {
        console.error(i18n.t('auto___26763e'), err);
        showModelsNotification(i18n.t('auto___a413d3') + err.message, 'danger');
      } finally {
        refreshKeysBtn.disabled = false;
        refreshKeysBtn.textContent = originalText;
        if (keysListBody) await refreshKeysList(keysListBody);
      }
    };
  }

  if (addKeyBtn) {
    addKeyBtn.onclick = async () => {
      const nameInput = document.getElementById('new-key-name');
      const valueInput = document.getElementById('new-key-value');
      if (!nameInput || !valueInput) return;

      const name = nameInput.value.trim();
      const apiKey = valueInput.value.trim();

      if (!name || !apiKey) {
        showModelsNotification(i18n.t('auto___eb0a22'), 'warning');
        return;
      }

      addKeyBtn.disabled = true;
      try {
        await window.api.fetch('/api/keys', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, api_key: apiKey, status: 'active' })
        });
        showModelsNotification(`Ключ "${name}" успешно добавлен`, 'success');
        nameInput.value = '';
        valueInput.value = '';
        if (keysListBody) await refreshKeysList(keysListBody);
      } catch (err) {
        console.error(i18n.t('auto___cedd68'), err);
        showModelsNotification(i18n.t('auto___ce146e') + err.message, 'danger');
      } finally {
        addKeyBtn.disabled = false;
      }
    };
  }

  if (refreshGAccountsBtn && gaccountsListBody) {
    refreshGAccountsBtn.onclick = async () => {
      refreshGAccountsBtn.disabled = true;
      const originalText = refreshGAccountsBtn.innerHTML;
      refreshGAccountsBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Обновление...';
      try {
        await refreshGoogleAccountsList(gaccountsListBody);
        showModelsNotification(i18n.t('auto__google__69a756'), 'success');
      } finally {
        refreshGAccountsBtn.disabled = false;
        refreshGAccountsBtn.innerHTML = originalText;
      }
    };
  }

  if (addGAccountBtn) {
    addGAccountBtn.onclick = async () => {
      await handleAddGoogleAccount(gaccountsListBody);
    };
  }

  // 2. Load all components concurrently
  await Promise.allSettled([
    modelSelect && saveBtn ? loadTabModels(modelSelect, saveBtn) : Promise.resolve(),
    keysListBody ? refreshKeysList(keysListBody) : Promise.resolve(),
    gaccountsListBody ? refreshGoogleAccountsList(gaccountsListBody) : Promise.resolve(),
    loadFoundryConfig(),
    loadOllamaConfig(),
    loadAgyConfig(),
    loadOnnxConfig(),
    loadSystemInstruction()
  ]);
}

// Helper for escaping HTML strings
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Helper to execute model test request
async function executeModelTest() {
  const providerSelect = document.getElementById('provider-tab-select');
  const modelSelect = document.getElementById('models-tab-select');
  const promptInput = document.getElementById('model-test-prompt');
  const testBtn = document.getElementById('btn-model-test-send');
  const cancelBtn = document.getElementById('btn-model-test-cancel');
  const resultContainer = document.getElementById('model-test-result');

  if (!testBtn || !resultContainer) return;

  const provider = providerSelect ? providerSelect.value : '';
  const model = modelSelect ? modelSelect.value : '';
  const message = promptInput ? promptInput.value.trim() : '';

  if (!model) {
    showModelsNotification(i18n.t('auto___de79f6'), 'warning');
    return;
  }

  if (!message) {
    showModelsNotification(i18n.t('auto___50af66'), 'warning');
    if (promptInput) promptInput.focus();
    return;
  }

  // Abort any prior running test
  cancelModelTest();
  modelTestAbortController = new AbortController();

  testBtn.disabled = true;
  const originalBtnHtml = testBtn.innerHTML;
  testBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Тест...';

  if (cancelBtn) {
    cancelBtn.style.display = 'inline-block';
    cancelBtn.disabled = false;
  }

  resultContainer.style.display = 'block';
  resultContainer.innerHTML = `
    <div class="d-flex justify-content-between align-items-center text-info small">
      <div class="d-flex align-items-center text-truncate">
        <span class="spinner-border spinner-border-sm me-2 flex-shrink-0" role="status"></span>
        <span class="text-truncatei18n.t('auto__strong_escapehtml_model_strong_escapehtml_provider_span_div_button_class__766d61')btn btn-outline-danger btn-sm py-0 px-2 rounded ms-2 flex-shrink-0" id="btn-model-test-cancel-inner" type="button" title=i18n.t('auto___e54261')>
        <i class="bi bi-stop-circle me-1"></i> Отмена
      </button>
    </div>
  `;

  const cancelInnerBtn = document.getElementById('btn-model-test-cancel-inner');
  if (cancelInnerBtn) {
    cancelInnerBtn.onclick = cancelModelTest;
  }

  try {
    const res = await window.api.fetch('/api/chat/test-model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: modelTestAbortController.signal,
      body: JSON.stringify({
        provider: provider,
        model: model,
        message: message
      })
    });

    if (res && res.status === 'success') {
      resultContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom">
          <div>
            <span class="badge bg-success me-2"><i class="bi bi-check-circle me-1"></i>200 OK</span>
            <span class="text-secondary small font-monospace">⚡ ${res.duration_ms || 0} ms</span>
          </div>
          <span class="badge bg-secondary-subtle text-secondary-emphasis border font-monospace">${escapeHtml(res.model || model)}</span>
        </div>
        <div class="small mt-1 font-monospace" style="white-space: pre-wrap; word-break: break-word;">${escapeHtml(res.response || i18n.t('auto___251ba7'))}</div>
      `;
    } else {
      const errMsg = (res && res.message) ? res.message : i18n.t('auto___e503ff');
      resultContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom">
          <div>
            <span class="badge bg-danger me-2"><i class="bi bi-x-circle me-1i18n.t('auto__i_span_span_class__f18bbf')text-secondary small font-monospace">⚡ ${res?.duration_ms || 0} ms</span>
          </div>
          <span class="badge bg-secondary-subtle text-secondary-emphasis border font-monospace">${escapeHtml(model)}</span>
        </div>
        <div class="text-danger small mt-1 font-monospace" style="white-space: pre-wrap; word-break: break-word;">${escapeHtml(errMsg)}</div>
      `;
    }
  } catch (err) {
    if (err.name === 'AbortError' || err.message?.toLowerCase().includes('abort')) {
      resultContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom">
          <span class="badge bg-warning text-dark"><i class="bi bi-slash-circle me-1i18n.t('auto__i_span_span_class__4f8860')badge bg-secondary-subtle text-secondary-emphasis border font-monospace">${escapeHtml(model)}</span>
        </div>
        <div class="text-warning small mt-1 font-monospace"><i class="bi bi-info-circle me-1"></i>Запрос отменен пользователем.</div>
      `;
    } else {
      console.error('Error during model test request:', err);
      resultContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom">
          <span class="badge bg-danger"><i class="bi bi-x-circle me-1i18n.t('auto__i_api_span_span_class__8ca377')badge bg-secondary-subtle text-secondary-emphasis border font-monospace">${escapeHtml(model)}</span>
        </div>
        <div class="text-danger small mt-1 font-monospace" style="white-space: pre-wrap; word-break: break-word;">${escapeHtml(err.message || i18n.t('auto___da6765'))}</div>
      `;
    }
  } finally {
    modelTestAbortController = null;
    testBtn.disabled = false;
    testBtn.innerHTML = originalBtnHtml;
    if (cancelBtn) {
      cancelBtn.style.display = 'none';
    }
  }
}

// Favorite models storage in window state
window.userFavoriteModels = window.userFavoriteModels || {};

function updateModelFavoriteUI(modelSelect) {
  if (!modelSelect) modelSelect = document.getElementById('models-tab-select');
  const curModel = modelSelect ? modelSelect.value : '';
  const starIcon = document.getElementById('favorite-star-icon');
  const favBtn = document.getElementById('btn-model-toggle-favorite');
  const statusBadge = document.getElementById('model-fav-status-badge');
  const noteInput = document.getElementById('model-user-note');

  const favData = curModel && window.userFavoriteModels ? window.userFavoriteModels[curModel] : null;
  const isFav = Boolean(favData);

  if (starIcon) {
    starIcon.className = isFav ? 'bi bi-star-fill text-warning' : 'bi bi-star';
  }
  if (favBtn) {
    if (isFav) {
      favBtn.classList.remove('btn-outline-warning');
      favBtn.classList.add('btn-warning', 'text-dark');
      favBtn.title = i18n.t('auto___a9a267');
    } else {
      favBtn.classList.remove('btn-warning', 'text-dark');
      favBtn.classList.add('btn-outline-warning');
      favBtn.title = i18n.t('auto___0fc76f');
    }
  }
  if (statusBadge) {
    if (isFav) {
      statusBadge.textContent = i18n.t('auto___9b3b60');
      statusBadge.className = 'badge bg-warning text-dark font-monospace';
    } else {
      statusBadge.textContent = i18n.t('auto___578200');
      statusBadge.className = 'badge bg-secondary-subtle text-secondary-emphasis border font-monospace';
    }
  }
  if (noteInput && document.activeElement !== noteInput) {
    noteInput.value = favData ? (favData.note || '') : '';
  }

  renderFavoriteModelsChips(modelSelect);
}

function updateModelSelectOptions(modelSelect) {
  if (!modelSelect) return;
  const options = modelSelect.querySelectorAll('option');
  options.forEach(opt => {
    const val = opt.value;
    if (!val) return;
    const isFav = window.userFavoriteModels && Boolean(window.userFavoriteModels[val]);
    let text = opt.textContent.replace(/^⭐\s*/, '');
    if (isFav) {
      opt.textContent = `⭐ ${text}`;
    } else {
      opt.textContent = text;
    }
  });
}

function renderFavoriteModelsChips(modelSelect) {
  const container = document.getElementById('favorite-models-list');
  const section = document.getElementById('favorite-models-section');
  if (!container || !section) return;

  const favKeys = Object.keys(window.userFavoriteModels || {});
  if (favKeys.length === 0) {
    section.style.display = 'none';
    container.innerHTML = '';
    return;
  }

  section.style.display = 'block';
  container.innerHTML = 'i18n.t('auto__favkeys_foreach_modelname_const_data_window_userfavoritemodels_modelname_const_note_data_note_n_data_note__a05f57')';
    
    const chip = document.createElement('div');
    chip.className = 'btn-group btn-group-sm mb-1';
    chip.role = 'group';

    const btnSelect = document.createElement('button');
    btnSelect.type = 'button';
    btnSelect.className = modelSelect && modelSelect.value === modelName 
      ? 'btn btn-sm btn-warning text-dark py-0 px-2 font-monospace'
      : 'btn btn-sm btn-outline-warning py-0 px-2 font-monospace';
    btnSelect.innerHTML = `<i class="bi bi-star-fill me-1 text-warning"></i>${escapeHtml(modelName)}`;
    btnSelect.title = `Выбрать модель: ${modelName}${note}`;
    btnSelect.onclick = () => {
      if (modelSelect) {
        // Try finding which provider has this model
        const providerSelect = document.getElementById('provider-tab-select');
        if (providerSelect && window._modelsGrouped) {
          for (const p of Object.keys(window._modelsGrouped)) {
            if (window._modelsGrouped[p]?.includes(modelName)) {
              if (providerSelect.value !== p) {
                providerSelect.value = p;
                if (typeof window._populateModels === 'function') {
                  window._populateModels(p, window._modelsGrouped[p]);
                }
              }
              break;
            }
          }
        }
        modelSelect.value = modelName;
        updateModelFavoriteUI(modelSelect);
      }
    };

    const btnRemove = document.createElement('button');
    btnRemove.type = 'button';
    btnRemove.className = 'btn btn-sm btn-outline-danger py-0 px-1';
    btnRemove.innerHTML = '<i class="bi bi-x"></i>i18n.t('auto__btnremove_title_modelname_btnremove_onclick_async_e_e_stoppropagation_try_await_window_api_fetch_auth_favorites_encodeuricomponent_modelname_method__61dee0')DELETE' });
        delete window.userFavoriteModels[modelName];
        updateModelFavoriteUI(modelSelect);
        updateModelSelectOptions(modelSelect);
        showModelsNotification(`Модель "${modelName}" удалена из избранного`, 'info');
      } catch (err) {
        showModelsNotification(i18n.t('auto___654025') + err.message, 'danger');
      }
    };

    chip.appendChild(btnSelect);
    chip.appendChild(btnRemove);
    container.appendChild(chip);
  });
}

// Helper to load models list
async function loadTabModels(modelSelect, saveBtn, forceRefresh = false) {
  const providerSelect = document.getElementById('provider-tab-select');
  if (providerSelect) providerSelect.innerHTML = '';
  modelSelect.innerHTML = '';
  
  let modelsGrouped = {};
  let unsupportedGrouped = {};
  
  const fetchModels = async (force = false) => {
    try {
      const showAll = document.getElementById('show-all-models-check')?.checked ?? false;
      const params = new URLSearchParams();
      if (force) params.append('refresh', 'true');
      if (showAll) params.append('include_unsupported', 'true');
      const url = '/api/chat/models' + (params.toString() ? '?' + params.toString() : '');
      const modelsData = await window.api.fetch(url);
      let grouped = modelsData.models || {};
      if (Array.isArray(grouped)) {
        grouped = { 'gemini': grouped };
      }
      unsupportedGrouped = modelsData.unsupported_models || {};
      return grouped;
    } catch (err) {
      console.error('Error loading AI models:', err);
      showModelsNotification(i18n.t('auto__ai__ca8a13') + err.message, 'danger');
      return {};
    }
  };

  modelsGrouped = await fetchModels(forceRefresh);
  window._modelsGrouped = modelsGrouped;
  if (forceRefresh) {
    showModelsNotification(i18n.t('auto___f65bb1'), 'success');
  }

  // Fetch favorite models and current settings
  try {
    const settingsData = await window.api.fetch('/auth/settings');
    if (settingsData && settingsData.favorite_models) {
      window.userFavoriteModels = settingsData.favorite_models;
    } else {
      const favRes = await window.api.fetch('/auth/favorites');
      if (favRes && favRes.favorites) {
        window.userFavoriteModels = favRes.favorites;
      }
    }
  } catch (e) {
    console.warn('Failed to load favorite models:', e);
  }

  const providers = Object.keys(modelsGrouped).filter(p => modelsGrouped[p] && modelsGrouped[p].length > 0);

  if (providers.length === 0) {
    if (providerSelect) {
      providerSelect.innerHTML = '<option value="">Нет доступных провайдеров</option>';
    }
    modelSelect.innerHTML = '<option value="">Нет доступных моделей</option>';
    saveBtn.disabled = true;
    updateModelFavoriteUI(modelSelect);
    return;
  }
  
  if (providerSelect) {
    providerSelect.innerHTML = '';
    providers.forEach(p => {
      const option = document.createElement('option');
      option.value = p;
      option.textContent = p.charAt(0).toUpperCase() + p.slice(1);
      providerSelect.appendChild(option);
    });
  }

  const populateModels = (provider, providerModelsList) => {
    modelSelect.innerHTML = '';
    const providerModels = providerModelsList !== undefined ? providerModelsList : (modelsGrouped[provider] || []);
    const unsupList = unsupportedGrouped[provider] || [];
    if (!providerModels || providerModels.length === 0) {
      modelSelect.innerHTML = '<option value="">Нет моделей</option>';
      saveBtn.disabled = true;
    } else {
      providerModels.forEach(modelName => {
        const option = document.createElement('option');
        option.value = modelName;
        let cleanName = modelName;
        if (cleanName.startsWith('foundry:')) cleanName = cleanName.substring(8);
        else if (cleanName.startsWith('ollama:')) cleanName = cleanName.substring(7);
        else if (cleanName.startsWith('gemini_cli:')) cleanName = cleanName.substring(11);
        else if (cleanName.startsWith('agy-')) cleanName = cleanName.substring(4);
        else if (cleanName.startsWith('onnx:i18n.t('auto__cleanname_cleanname_substring_5_const_isfav_window_userfavoritemodels_boolean_window_userfavoritemodels_modelname_const_isunsupported_unsuplist_includes_cleanname_unsuplist_includes_modelname_let_label_cleanname_if_isfav_label_label_if_isunsupported_label_label_option_textcontent_label_modelselect_appendchild_option_savebtn_disabled_false_updatemodelfavoriteui_modelselect_window_populatemodels_populatemodels_if_providerselect_providerselect_onchange_async_const_chosenprovider_providerselect_value_modelselect_innerhtml__c7d4cc')<option value="">Обновление списка моделей...</option>';
      saveBtn.disabled = true;
      try {
        const updatedGrouped = await fetchModels(true);
        if (updatedGrouped && Object.keys(updatedGrouped).length > 0) {
          modelsGrouped = updatedGrouped;
          window._modelsGrouped = modelsGrouped;
        }
      } catch (e) {
        console.warn('Failed to refresh models on provider change:', e);
      }
      populateModels(chosenProvider, modelsGrouped[chosenProvider]);
    };
    populateModels(providerSelect.value, modelsGrouped[providerSelect.value]);
  } else {
    let allModels = [];
    providers.forEach(p => allModels = allModels.concat(modelsGrouped[p]));
    allModels.forEach(modelName => {
        const option = document.createElement('option');
        option.value = modelName;
        const isFav = window.userFavoriteModels && Boolean(window.userFavoriteModels[modelName]);
        option.textContent = isFav ? `⭐ ${modelName}` : modelName;
        modelSelect.appendChild(option);
    });
    saveBtn.disabled = allModels.length === 0;
    updateModelFavoriteUI(modelSelect);
  }

  try {
    const settingsData = await window.api.fetch('/auth/settings');
    const savedModel = settingsData && settingsData.model ? settingsData.model : '';
    if (savedModel) {
      let foundProvider = null;
      for (const p of providers) {
        if (modelsGrouped[p] && modelsGrouped[p].includes(savedModel)) {
          foundProvider = p;
          break;
        }
      }
      if (foundProvider && providerSelect) {
        providerSelect.value = foundProvider;
        populateModels(foundProvider, modelsGrouped[foundProvider]);
      }
      modelSelect.value = savedModel;
      updateModelFavoriteUI(modelSelect);
    }
    if (typeof window.updateChatBadges === 'function') {
      window.updateChatBadges(savedModel);
    }
  } catch (err) {
    console.error('Error loading user AI settings:', err);
  }
}

// Helper to refresh keys list table
async function refreshKeysList(container) {
  try {
    container.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Загрузка ключей...</td></tr>';
    const keysData = await window.api.fetch('/api/keys');
    const keys = keysData.keys || [];

    if (keys.length === 0) {
      container.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Список ключей пуст</td></tr>';
      return;
    }

    container.innerHTML = '';
    keys.forEach(key => {
      const row = document.createElement('tr');

      const tdName = document.createElement('td');
      tdName.innerHTML = `<strong>${key.name}</strong>`;
      row.appendChild(tdName);

      const tdKey = document.createElement('td');
      tdKey.className = 'font-monospace text-muted small';
      tdKey.textContent = key.api_key_masked;
      row.appendChild(tdKey);

      const tdStatus = document.createElement('td');
      const isEnabled = key.status === 'active';
      const statusClass = isEnabled ? 'bg-success' : 'bg-secondary';
      const statusText = isEnabled ? i18n.t('auto___667904') : i18n.t('auto___cadea0');
      tdStatus.innerHTML = `<span class="badge ${statusClass}">${statusText}</span>`;
      row.appendChild(tdStatus);

      const tdQuota = document.createElement('td');
      if (key.exhausted) {
        let resetText = i18n.t('auto___1397df');
        if (key.reset_in_seconds) {
          const hours = Math.floor(key.reset_in_seconds / 3600);
          const mins = Math.floor((key.reset_in_seconds % 3600) / 60);
          resetText = `Сброс через ${hours}ч ${mins}м`;
        }
        tdQuota.innerHTML = `<span class="badge bg-danger d-block mb-1" title=i18n.t('auto___47f876')>${resetText}</span>`;
      } else {
        tdQuota.innerHTML = `<span class="badge bg-success d-block mb-1">OK</span>`;
      }
      row.appendChild(tdQuota);

      const tdActions = document.createElement('td');
      tdActions.className = 'text-end';

      const btnToggle = document.createElement('button');
      btnToggle.className = `btn btn-xs btn-sm me-1 ${isEnabled ? 'btn-outline-secondary' : 'btn-outline-success'}`;
      btnToggle.textContent = isEnabled ? i18n.t('auto___23c590') : i18n.t('auto___a60b4b');
      btnToggle.onclick = () => toggleKeyStatus(key.name, isEnabled ? 'disabled' : 'active', container);
      tdActions.appendChild(btnToggle);

      if (key.exhausted) {
        const btnReset = document.createElement('button');
        btnReset.className = 'btn btn-xs btn-outline-warning btn-sm me-1';
        btnReset.innerHTML = i18n.t('auto___9322bf');
        btnReset.title = i18n.t('auto__24__1855b1');
        btnReset.onclick = () => resetKeyQuota(key.name, container);
        tdActions.appendChild(btnReset);
      }

      const btnDelete = document.createElement('button');
      btnDelete.className = 'btn btn-xs btn-outline-danger btn-sm';
      btnDelete.textContent = i18n.t('auto___86ea33');
      btnDelete.onclick = () => deleteKey(key.name, container);
      tdActions.appendChild(btnDelete);

      row.appendChild(tdActions);
      container.appendChild(row);
    });

  } catch (err) {
    console.error(i18n.t('auto___7c8c18'), err);
    container.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">Ошибка: ${err.message}</td></tr>`;
  }
}

// API action helpers
async function toggleKeyStatus(name, newStatus, container) {
  try {
    await window.api.fetch(`/api/keys/${name}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    showModelsNotification(`Статус ключа "${name}" изменен на ${newStatus === 'active' ? i18n.t('auto___27de6a') : i18n.t('auto___0c94c3')}`, 'success');
    await refreshKeysList(container);
  } catch (err) {
    console.error(i18n.t('auto___37b90b'), err);
    showModelsNotification(i18n.t('auto___75dafa') + err.message, 'danger');
  }
}

async function resetKeyQuota(name, container) {
  try {
    await window.api.fetch(`/api/keys/${name}/reset-quota`, { method: 'POST' });
    showModelsNotification(`Квота для ключа "${name}" успешно сброшена`, 'success');
    await refreshKeysList(container);
  } catch (err) {
    console.error(i18n.t('auto___02a8d0'), err);
    showModelsNotification(i18n.t('auto___1ab946') + err.message, 'danger');
  }
}

async function deleteKey(name, container) {
  if (!confirm(`Вы уверены, что хотите удалить ключ "${name}"?`)) return;
  try {
    await window.api.fetch(`/api/keys/${name}`, { method: 'DELETE' });
    showModelsNotification(`Ключ "${name}" успешно удален`, 'success');
    await refreshKeysList(container);
  } catch (err) {
    console.error(i18n.t('auto___e89e90'), err);
    showModelsNotification(i18n.t('auto___654025') + err.message, 'danger');
  }
}

function showModelsNotification(message, type = 'info') {
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

async function loadFoundryConfig() {
  try {
    const config = await window.api.fetch('/api/foundry/config');
    const enabledInput = document.getElementById('foundry-enabled');
    const urlInput = document.getElementById('foundry-url');
    const keyInput = document.getElementById('foundry-key');
    const modelInput = document.getElementById('foundry-model');
    
    if (enabledInput) enabledInput.checked = config.enabled || false;
    if (urlInput) urlInput.value = config.url || '';
    if (keyInput) keyInput.value = config.key || '';
    if (modelInput) modelInput.value = config.model || '';
  } catch (err) {
    console.error(i18n.t('auto__foundry__623fc9'), err);
  }
}

async function loadOllamaConfig() {
  try {
    const config = await window.api.fetch('/api/ollama/config');
    const enabledInput = document.getElementById('ollama-enabled');
    const urlInput = document.getElementById('ollama-url');
    const modelInput = document.getElementById('ollama-model');
    
    if (enabledInput) enabledInput.checked = config.enabled || false;
    if (urlInput) urlInput.value = config.url || '';
    if (modelInput) modelInput.value = config.model || '';
  } catch (err) {
    console.error(i18n.t('auto__ollama__db8d78'), err);
  }
}

async function loadAgyConfig() {
  try {
    const modelSelect = document.getElementById('agy-model');
    if (modelSelect) {
      try {
        const modelsData = await window.api.fetch('/api/chat/models');
        const agyList = modelsData.models?.agy || [];
        if (agyList.length > 0) {
          const curVal = modelSelect.value;
          modelSelect.innerHTML = '';
          agyList.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            modelSelect.appendChild(opt);
          });
          if (curVal && agyList.includes(curVal)) {
            modelSelect.value = curVal;
          }
        }
      } catch (e) {
        console.error(i18n.t('auto__agy__12d3f1'), e);
      }
    }

    const config = await window.api.fetch('/api/agy/config');
    const enabledInput = document.getElementById('agy-enabled');
    const keyInput = document.getElementById('agy-key');
    
    if (enabledInput) enabledInput.checked = config.enabled ?? true;
    if (modelSelect && config.model) modelSelect.value = config.model;
    if (keyInput) keyInput.value = config.key || '';
  } catch (err) {
    console.error(i18n.t('auto__antigravity_agy__ad9cec'), err);
  }
}

async function loadOnnxConfig() {
  try {
    const config = await window.api.fetch('/api/onnx/config');
    const enabledInput = document.getElementById('onnx-enabled');
    const epSelect = document.getElementById('onnx-execution-provider');
    const dirInput = document.getElementById('onnx-models-dir');
    const modelInput = document.getElementById('onnx-default-model');
    const precSelect = document.getElementById('onnx-olive-precision');

    if (enabledInput) enabledInput.checked = config.enabled ?? true;
    if (epSelect && config.execution_provider) epSelect.value = config.execution_provider;
    if (dirInput && config.models_dir) dirInput.value = config.models_dir;
    if (modelInput && config.default_model) modelInput.value = config.default_model;
    if (precSelect && config.olive_precision) precSelect.value = config.olive_precision;
  } catch (err) {
    console.error(i18n.t('auto__onnx_olive__4dcba8'), err);
  }
}

async function loadSystemInstruction() {
  const editor = document.getElementById('system-instruction-editor');
  const statusBadge = document.getElementById('system-instruction-status');
  if (!editor) return;
  
  editor.disabled = true;
  if (statusBadge) {
    statusBadge.className = 'badge bg-warning text-dark';
    statusBadge.textContent = i18n.t('auto___a90ed3');
    statusBadge.style.removeProperty('display');
  }
  
  try {
    const data = await window.api.fetch('/api/admin/system_instruction');
    editor.value = data.content || '';
    if (statusBadge) {
      statusBadge.className = 'badge bg-success';
      statusBadge.textContent = i18n.t('auto___d574e3');
      setTimeout(() => {
        if (statusBadge) statusBadge.style.display = 'none';
      }, 2500);
    }
  } catch (err) {
    console.error(i18n.t('auto___c33481'), err);
    if (statusBadge) {
      statusBadge.className = 'badge bg-danger';
      statusBadge.textContent = i18n.t('auto___72aecd');
      statusBadge.style.removeProperty('display');
    }
    showModelsNotification(i18n.t('auto___276152') + err.message, 'danger');
  } finally {
    editor.disabled = false;
  }
}

async function saveSystemInstruction() {
  const editor = document.getElementById('system-instruction-editor');
  const saveBtn = document.getElementById('btn-save-instruction');
  const statusBadge = document.getElementById('system-instruction-status');
  if (!editor || !saveBtn) return;

  const originalHtml = saveBtn.innerHTML;
  saveBtn.disabled = true;
  saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Сохранение...';

  try {
    await window.api.fetch('/api/admin/system_instruction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: editor.value })
    });
    showModelsNotification(i18n.t('auto___8d1e8d'), 'success');
    if (statusBadge) {
      statusBadge.className = 'badge bg-success';
      statusBadge.textContent = i18n.t('auto___f0dff5');
      statusBadge.style.removeProperty('display');
      setTimeout(() => {
        if (statusBadge) statusBadge.style.display = 'none';
      }, 3000);
    }
  } catch (err) {
    console.error(i18n.t('auto___bcbdfe'), err);
    if (statusBadge) {
      statusBadge.className = 'badge bg-danger';
      statusBadge.textContent = i18n.t('auto___c628b5');
      statusBadge.style.removeProperty('display');
    }
    showModelsNotification(i18n.t('auto___bbbabd') + err.message, 'danger');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = originalHtml;
  }
}

// ============================================================================
// Google Workspace Multi-Account Pool Management
// ============================================================================

async function refreshGoogleAccountsList(container) {
  if (!container) return;
  try {
    container.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Загрузка аккаунтов...</td></tr>';
    const data = await window.api.googleAccounts.list();
    const accounts = data.accounts || [];

    if (accounts.length === 0) {
      container.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Список аккаунтов пуст. Загрузите файл credentials.json или service_account.json.</td></tr>';
      return;
    }

    container.innerHTML = '';
    accounts.forEach(acc => {
      const row = document.createElement('tr');

      // 1. Account Name + Default Badge + Email
      const tdName = document.createElement('td');
      tdName.innerHTML = `
        <div class="d-flex align-items-center gap-2">
          <strong>${escapeHtml(acc.name)}</strong>
          ${acc.is_default ? '<span class="badge bg-warning text-dark"><i class="bi bi-star-fill"></i> Default</span>' : ''}
        </div>
        ${acc.email ? `<div class="small text-muted font-monospace">${escapeHtml(acc.email)}</div>` : ''}
      `;
      row.appendChild(tdName);

      // 2. Type
      const tdType = document.createElement('td');
      const isOAuth = acc.type === 'oauth2';
      tdType.innerHTML = isOAuth
        ? '<span class="badge bg-primary-subtle text-primary border border-primary-subtle"><i class="bi bi-person me-1"></i>OAuth 2.0</span>'
        : '<span class="badge bg-info-subtle text-info border border-info-subtle"><i class="bi bi-cpu me-1"></i>Service Account</span>';
      row.appendChild(tdType);

      // 3. Status / Quota
      const tdStatus = document.createElement('td');
      const isActive = acc.status === 'active';
      if (isActive) {
        tdStatus.innerHTML = '<span class="badge bg-success">Активен</span>';
      } else if (acc.status === 'exhausted') {
        tdStatus.innerHTML = '<span class="badge bg-danger" title=i18n.t('auto___54a53d')>Лимит</span>';
      } else {
        tdStatus.innerHTML = `<span class="badge bg-secondary">${escapeHtml(acc.status)}</span>`;
      }
      row.appendChild(tdStatus);

      // 4. Token / Credentials Status
      const tdToken = document.createElement('td');
      if (acc.has_token || acc.type === 'service_account') {
        tdToken.innerHTML = '<span class="badge bg-success-subtle text-success"><i class="bi bi-shield-check me-1"></i>Готов</span>';
      } else {
        tdToken.innerHTML = '<span class="badge bg-warning-subtle text-warning"><i class="bi bi-key me-1"></i>Нужен токен</span>';
      }
      row.appendChild(tdToken);

      // 5. Actions
      const tdActions = document.createElement('td');
      tdActions.className = 'text-end';

      // Set Default button
      if (!acc.is_default) {
        const btnDefault = document.createElement('button');
        btnDefault.className = 'btn btn-xs btn-outline-warning btn-sm me-1';
        btnDefault.title = i18n.t('auto___d6350d');
        btnDefault.innerHTML = '<i class="bi bi-star"></i>';
        btnDefault.onclick = () => setGoogleAccountDefault(acc.name, container);
        tdActions.appendChild(btnDefault);
      }

      // Reset status button
      if (acc.status === 'exhausted') {
        const btnReset = document.createElement('button');
        btnReset.className = 'btn btn-xs btn-outline-info btn-sm me-1';
        btnReset.title = i18n.t('auto___29d113');
        btnReset.innerHTML = '<i class="bi bi-arrow-repeat"></i>';
        btnReset.onclick = () => resetGoogleAccountStatus(acc.name, container);
        tdActions.appendChild(btnReset);
      }

      // Test button
      const btnTest = document.createElement('button');
      btnTest.className = 'btn btn-xs btn-outline-info btn-sm me-1';
      btnTest.title = i18n.t('auto___d6a136');
      btnTest.innerHTML = '<i class="bi bi-play-circle"></i> Тест';
      btnTest.onclick = () => testGoogleAccount(acc.name);
      tdActions.appendChild(btnTest);

      // Delete button
      const btnDelete = document.createElement('button');
      btnDelete.className = 'btn btn-xs btn-outline-danger btn-sm';
      btnDelete.title = i18n.t('auto___ec3b81');
      btnDelete.innerHTML = '<i class="bi bi-trash"></i>';
      btnDelete.onclick = () => deleteGoogleAccount(acc.name, container);
      tdActions.appendChild(btnDelete);

      row.appendChild(tdActions);
      container.appendChild(row);
    });

  } catch (err) {
    console.error(i18n.t('auto__google_workspace__ac8349'), err);
    container.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">Ошибка: ${escapeHtml(err.message)}</td></tr>`;
  }
}

async function handleAddGoogleAccount(container) {
  const nameInput = document.getElementById('new-gacc-name');
  const typeSelect = document.getElementById('new-gacc-type');
  const emailInput = document.getElementById('new-gacc-email');
  const fileInput = document.getElementById('new-gacc-file');
  const jsonTextarea = document.getElementById('new-gacc-json');
  const defaultCheckbox = document.getElementById('new-gacc-default');
  const addBtn = document.getElementById('btn-add-gacc');

  if (!nameInput || !addBtn) return;

  const accountName = nameInput.value.trim();
  const accountType = typeSelect ? typeSelect.value : 'oauth2';
  const email = emailInput ? emailInput.value.trim() : '';
  const setAsDefault = defaultCheckbox ? defaultCheckbox.checked : false;

  if (!accountName) {
    showModelsNotification(i18n.t('auto__work_personal__3640ed'), 'warning');
    nameInput.focus();
    return;
  }

  // Check if file is selected or JSON is pasted
  const file = fileInput && fileInput.files && fileInput.files[0];
  const jsonContent = jsonTextarea ? jsonTextarea.value.trim() : '';

  if (!file && !jsonContent) {
    showModelsNotification(i18n.t('auto__credentials_json_service_account_json_json_c9132d'), 'warning');
    return;
  }

  addBtn.disabled = true;
  const originalText = addBtn.innerHTML;
  addBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Сохранение...';

  try {
    if (file) {
      const formData = new FormData();
      formData.append('account_name', accountName);
      formData.append('account_type', accountType);
      if (email) formData.append('email', email);
      formData.append('set_as_default', setAsDefault ? 'true' : 'false');
      formData.append('file', file);

      await window.api.googleAccounts.upload(formData);
    } else {
      let parsedJson = null;
      try {
        parsedJson = JSON.parse(jsonContent);
      } catch (e) {
        throw new Error(i18n.t('auto__json__9896c0'));
      }

      await window.api.googleAccounts.create({
        account_name: accountName,
        account_type: accountType,
        email: email || undefined,
        credentials_dict: parsedJson,
        set_as_default: setAsDefault
      });
    }

    showModelsNotification(`Аккаунт Google "${accountName}" успешно сохранен в пул`, 'success');
    nameInput.value = '';
    if (emailInput) emailInput.value = '';
    if (fileInput) fileInput.value = '';
    if (jsonTextarea) jsonTextarea.value = '';
    if (defaultCheckbox) defaultCheckbox.checked = false;

    if (container) await refreshGoogleAccountsList(container);
  } catch (err) {
    console.error(i18n.t('auto__google__82151e'), err);
    showModelsNotification(i18n.t('auto___bbbabd') + err.message, 'danger');
  } finally {
    addBtn.disabled = false;
    addBtn.innerHTML = originalText;
  }
}

async function setGoogleAccountDefault(name, container) {
  try {
    await window.api.googleAccounts.setDefault(name);
    showModelsNotification(`Аккаунт "${name}" назначен по умолчанию`, 'success');
    if (container) await refreshGoogleAccountsList(container);
  } catch (err) {
    console.error(i18n.t('auto___3fcc5f'), err);
    showModelsNotification(i18n.t('auto___8361fc') + err.message, 'danger');
  }
}

async function resetGoogleAccountStatus(name, container) {
  try {
    await window.api.googleAccounts.resetStatus(name);
    showModelsNotification(`Статус аккаунта "${name}" сброшен в активный`, 'success');
    if (container) await refreshGoogleAccountsList(container);
  } catch (err) {
    console.error(i18n.t('auto___608a49'), err);
    showModelsNotification(i18n.t('auto___a413d3') + err.message, 'danger');
  }
}

async function testGoogleAccount(name) {
  const testCard = document.getElementById('gaccount-test-card');
  const testBody = document.getElementById('gaccount-test-body');

  if (testCard && testBody) {
    testCard.style.display = 'block';
    testBody.innerHTML = `<span class="spinner-border spinner-border-sm me-2 text-info"></span>Проверка аутентификации для аккаунта <strong>${escapeHtml(name)}</strong>...`;
  }

  try {
    const res = await window.api.googleAccounts.test(name);
    if (testBody) {
      const isSuccess = res.status === 'success';
      const isWarning = res.status === 'warning';
      const badgeClass = isSuccess ? 'bg-success' : isWarning ? 'bg-warning text-dark' : 'bg-danger';
      
      testBody.innerHTML = `
        <div class="mb-2 d-flex align-items-center gap-2">
          <span class="badge ${badgeClass}">${res.status.toUpperCase()}</span>
          <strong>${escapeHtml(name)}</strong>
        </div>
        <div class="mb-1">${escapeHtml(res.message || '')}</div>
        ${res.scopes && res.scopes.length > 0 ? `<div class="text-muted mt-2"><strong>Доступные Scopes:</strong><br>${res.scopes.map(s => '• ' + escapeHtml(s)).join('<br>')}</div>` : ''}
      `;
    }
  } catch (err) {
    if (testBody) {
      testBody.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle me-1i18n.t('auto__i_escapehtml_err_message_span_async_function_deletegoogleaccount_name_container_if_confirm__3d5d10')${name}i18n.t('auto__google_workspace_return_try_await_window_api_googleaccounts_delete_name_showmodelsnotification__219d28')${name}" успешно удален`, 'success');
    if (container) await refreshGoogleAccountsList(container);
  } catch (err) {
    console.error(i18n.t('auto__google__fea33a'), err);
    showModelsNotification(i18n.t('auto___654025') + err.message, 'danger');
  }
}

// Export for tab loader
window.initModelsTab = initModelsTab;
window.refreshGoogleAccountsList = refreshGoogleAccountsList;
