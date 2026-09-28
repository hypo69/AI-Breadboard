// Gemini Models & APIs management tab logic

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

  // 2. Load all components concurrently
  await Promise.allSettled([
    modelSelect && saveBtn ? loadTabModels(modelSelect, saveBtn) : Promise.resolve(),
    keysListBody ? refreshKeysList(keysListBody) : Promise.resolve(),
    loadFoundryConfig(),
    loadOllamaConfig(),
    loadAgyConfig(),
    loadOnnxConfig(),
    loadSystemInstruction()
  ]);
}

// Helper to load models list
async function loadTabModels(modelSelect, saveBtn, forceRefresh = false) {
  const providerSelect = document.getElementById('provider-tab-select');
  if (providerSelect) providerSelect.innerHTML = '';
  modelSelect.innerHTML = '';
  
  let modelsGrouped = {};
  
  const fetchModels = async (force = false) => {
    try {
      const url = force ? '/api/chat/models?refresh=true' : '/api/chat/models';
      const modelsData = await window.api.fetch(url);
      let grouped = modelsData.models || {};
      if (Array.isArray(grouped)) {
        grouped = { 'gemini': grouped };
      }
      return grouped;
    } catch (err) {
      console.error(i18n.t('auto___688de2'), err);
      showModelsNotification(i18n.t('auto__ai__ca8a13') + err.message, 'danger');
      return {};
    }
  };

  modelsGrouped = await fetchModels(forceRefresh);

  const providers = Object.keys(modelsGrouped).filter(p => modelsGrouped[p] && modelsGrouped[p].length > 0);

  if (providers.length === 0) {
    if (providerSelect) {
      providerSelect.innerHTML = '<option value="">Нет доступных провайдеров</option>';
    }
    modelSelect.innerHTML = '<option value="">Нет доступных моделей</option>';
    saveBtn.disabled = true;
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
        else if (cleanName.startsWith('agy-')) cleanName = cleanName.substring(4);
        option.textContent = cleanName;
        modelSelect.appendChild(option);
      });
      saveBtn.disabled = false;
    }
  };

  if (providerSelect) {
    providerSelect.onchange = async () => {
      const chosenProvider = providerSelect.value;
      modelSelect.innerHTML = '<option value="">Обновление списка моделей...</option>';
      saveBtn.disabled = true;
      try {
        const updatedGrouped = await fetchModels(true);
        if (updatedGrouped && Object.keys(updatedGrouped).length > 0) {
          modelsGrouped = updatedGrouped;
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
        option.textContent = modelName;
        modelSelect.appendChild(option);
    });
    saveBtn.disabled = allModels.length === 0;
  }

  try {
    const settingsData = await window.api.fetch('/auth/settings');
    if (settingsData && settingsData.model) {
      let foundProvider = null;
      for (const p of providers) {
        if (modelsGrouped[p] && modelsGrouped[p].includes(settingsData.model)) {
          foundProvider = p;
          break;
        }
      }
      if (foundProvider && providerSelect) {
        providerSelect.value = foundProvider;
        populateModels(foundProvider, modelsGrouped[foundProvider]);
      }
      modelSelect.value = settingsData.model;
    }
  } catch (err) {
    console.error(i18n.t('auto__ai__450d9e'), err);
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

// Экспорт для загрузчика вкладок
window.initModelsTab = initModelsTab;
