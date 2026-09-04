// Gemini Models & APIs management tab logic

async function initModelsTab() {
  const modelSelect = document.getElementById('models-tab-select');
  const saveBtn = document.getElementById('btn-models-tab-save');
  const keysListBody = document.getElementById('keys-list-body');
  const refreshKeysBtn = document.getElementById('btn-refresh-keys');
  const addKeyBtn = document.getElementById('btn-add-key');
  const saveAgyBtn = document.getElementById('btn-save-agy');
  const saveFoundryBtn = document.getElementById('btn-save-foundry');
  const saveOllamaBtn = document.getElementById('btn-save-ollama');
  const saveBtnInstr = document.getElementById('btn-save-instruction');
  const reloadBtnInstr = document.getElementById('btn-reload-instruction');

  // 1. Bind event handlers immediately
  if (saveBtnInstr) saveBtnInstr.onclick = saveSystemInstruction;
  if (reloadBtnInstr) reloadBtnInstr.onclick = loadSystemInstruction;

  if (saveAgyBtn) {
    saveAgyBtn.onclick = async () => {
      const enabled = document.getElementById('agy-enabled')?.checked ?? true;
      const model = document.getElementById('agy-model')?.value || 'agy-flash';
      const key = document.getElementById('agy-key')?.value.trim() || '';

      saveAgyBtn.disabled = true;
      try {
        await window.api.fetch('/api/agy/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, model, key })
        });
        showModelsNotification('Настройки Antigravity (AGY) успешно сохранены', 'success');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка сохранения Antigravity:', err);
        showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
      } finally {
        saveAgyBtn.disabled = false;
      }
    };
  }

  if (saveFoundryBtn) {
    saveFoundryBtn.onclick = async () => {
      const enabled = document.getElementById('foundry-enabled')?.checked || false;
      const url = document.getElementById('foundry-url')?.value.trim() || '';
      const key = document.getElementById('foundry-key')?.value.trim() || '';
      
      saveFoundryBtn.disabled = true;
      try {
        await window.api.fetch('/api/foundry/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, url, key })
        });
        showModelsNotification('Настройки Microsoft Foundry успешно сохранены', 'success');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка сохранения Foundry:', err);
        showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
      } finally {
        saveFoundryBtn.disabled = false;
      }
    };
  }

  if (saveOllamaBtn) {
    saveOllamaBtn.onclick = async () => {
      const enabled = document.getElementById('ollama-enabled')?.checked || false;
      const url = document.getElementById('ollama-url')?.value.trim() || '';
      
      saveOllamaBtn.disabled = true;
      try {
        await window.api.fetch('/api/ollama/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, url })
        });
        showModelsNotification('Настройки Ollama успешно сохранены', 'success');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка сохранения Ollama:', err);
        showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
      } finally {
        saveOllamaBtn.disabled = false;
      }
    };
  }

  if (saveBtn && modelSelect) {
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
        showModelsNotification('Модель успешно обновлена на: ' + selectedModel, 'success');
        
        const otherModelSelect = document.getElementById('admin-model-select');
        if (otherModelSelect) {
          otherModelSelect.value = selectedModel;
        }
      } catch (err) {
        console.error('Ошибка сохранения модели:', err);
        showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
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
      refreshKeysBtn.textContent = '⏳ Сброс...';
      try {
        const res = await window.api.fetch('/api/keys/reset-all', { method: 'POST' });
        showModelsNotification(res.message || 'Квоты всех ключей успешно сброшены', 'success');
      } catch (err) {
        console.error('Ошибка сброса квот:', err);
        showModelsNotification('Ошибка сброса: ' + err.message, 'danger');
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
        showModelsNotification('Заполните все поля!', 'warning');
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
        console.error('Ошибка добавления ключа:', err);
        showModelsNotification('Ошибка добавления: ' + err.message, 'danger');
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
    loadSystemInstruction()
  ]);
}

// Helper to load models list
async function loadTabModels(modelSelect, saveBtn) {
  const providerSelect = document.getElementById('provider-tab-select');
  if (providerSelect) providerSelect.innerHTML = '';
  modelSelect.innerHTML = '';
  
  let modelsGrouped = {};
  
  try {
    const modelsData = await window.api.fetch('/api/chat/models');
    modelsGrouped = modelsData.models || {};
    if (Array.isArray(modelsGrouped)) {
      modelsGrouped = { 'gemini': modelsGrouped };
    }
  } catch (err) {
    console.error('Ошибка загрузки моделей:', err);
    showModelsNotification('Ошибка загрузки моделей AI: ' + err.message, 'danger');
  }

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

  const populateModels = (provider) => {
    modelSelect.innerHTML = '';
    const providerModels = modelsGrouped[provider] || [];
    if (providerModels.length === 0) {
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
    providerSelect.onchange = () => populateModels(providerSelect.value);
    populateModels(providerSelect.value);
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
        if (modelsGrouped[p].includes(settingsData.model)) {
          foundProvider = p;
          break;
        }
      }
      if (foundProvider && providerSelect) {
        providerSelect.value = foundProvider;
        populateModels(foundProvider);
      }
      modelSelect.value = settingsData.model;
    }
  } catch (err) {
    console.error('Ошибка загрузки настроек AI пользователя:', err);
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
      const statusText = isEnabled ? 'Активен' : 'Отключен';
      tdStatus.innerHTML = `<span class="badge ${statusClass}">${statusText}</span>`;
      row.appendChild(tdStatus);

      const tdQuota = document.createElement('td');
      if (key.exhausted) {
        let resetText = 'Лимит';
        if (key.reset_in_seconds) {
          const hours = Math.floor(key.reset_in_seconds / 3600);
          const mins = Math.floor((key.reset_in_seconds % 3600) / 60);
          resetText = `Сброс через ${hours}ч ${mins}м`;
        }
        tdQuota.innerHTML = `<span class="badge bg-danger d-block mb-1" title="Превышен лимит запросов в сутки">${resetText}</span>`;
      } else {
        tdQuota.innerHTML = `<span class="badge bg-success d-block mb-1">OK</span>`;
      }
      row.appendChild(tdQuota);

      const tdActions = document.createElement('td');
      tdActions.className = 'text-end';

      const btnToggle = document.createElement('button');
      btnToggle.className = `btn btn-xs btn-sm me-1 ${isEnabled ? 'btn-outline-secondary' : 'btn-outline-success'}`;
      btnToggle.textContent = isEnabled ? 'Откл' : 'Вкл';
      btnToggle.onclick = () => toggleKeyStatus(key.name, isEnabled ? 'disabled' : 'active', container);
      tdActions.appendChild(btnToggle);

      if (key.exhausted) {
        const btnReset = document.createElement('button');
        btnReset.className = 'btn btn-xs btn-outline-warning btn-sm me-1';
        btnReset.innerHTML = 'Сброс';
        btnReset.title = 'Сбросить 24-часовой бан квоты';
        btnReset.onclick = () => resetKeyQuota(key.name, container);
        tdActions.appendChild(btnReset);
      }

      const btnDelete = document.createElement('button');
      btnDelete.className = 'btn btn-xs btn-outline-danger btn-sm';
      btnDelete.textContent = 'Удалить';
      btnDelete.onclick = () => deleteKey(key.name, container);
      tdActions.appendChild(btnDelete);

      row.appendChild(tdActions);
      container.appendChild(row);
    });

  } catch (err) {
    console.error('Ошибка загрузки ключей:', err);
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
    showModelsNotification(`Статус ключа "${name}" изменен на ${newStatus === 'active' ? 'активный' : 'отключенный'}`, 'success');
    await refreshKeysList(container);
  } catch (err) {
    console.error('Ошибка переключения статуса ключа:', err);
    showModelsNotification('Ошибка изменения статуса: ' + err.message, 'danger');
  }
}

async function resetKeyQuota(name, container) {
  try {
    await window.api.fetch(`/api/keys/${name}/reset-quota`, { method: 'POST' });
    showModelsNotification(`Квота для ключа "${name}" успешно сброшена`, 'success');
    await refreshKeysList(container);
  } catch (err) {
    console.error('Ошибка сброса квоты:', err);
    showModelsNotification('Ошибка сброса квоты: ' + err.message, 'danger');
  }
}

async function deleteKey(name, container) {
  if (!confirm(`Вы уверены, что хотите удалить ключ "${name}"?`)) return;
  try {
    await window.api.fetch(`/api/keys/${name}`, { method: 'DELETE' });
    showModelsNotification(`Ключ "${name}" успешно удален`, 'success');
    await refreshKeysList(container);
  } catch (err) {
    console.error('Ошибка удаления ключа:', err);
    showModelsNotification('Ошибка удаления: ' + err.message, 'danger');
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
    console.error('Ошибка загрузки настроек Foundry:', err);
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
    console.error('Ошибка загрузки настроек Ollama:', err);
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
        console.error('Ошибка загрузки моделей AGY:', e);
      }
    }

    const config = await window.api.fetch('/api/agy/config');
    const enabledInput = document.getElementById('agy-enabled');
    const keyInput = document.getElementById('agy-key');
    
    if (enabledInput) enabledInput.checked = config.enabled ?? true;
    if (modelSelect && config.model) modelSelect.value = config.model;
    if (keyInput) keyInput.value = config.key || '';
  } catch (err) {
    console.error('Ошибка загрузки настроек Antigravity (AGY):', err);
  }
}

async function loadSystemInstruction() {
  const editor = document.getElementById('system-instruction-editor');
  const statusBadge = document.getElementById('system-instruction-status');
  if (!editor) return;
  
  editor.disabled = true;
  if (statusBadge) {
    statusBadge.className = 'badge bg-warning text-dark';
    statusBadge.textContent = 'Загрузка...';
    statusBadge.style.removeProperty('display');
  }
  
  try {
    const data = await window.api.fetch('/api/admin/system_instruction');
    editor.value = data.content || '';
    if (statusBadge) {
      statusBadge.className = 'badge bg-success';
      statusBadge.textContent = 'Загружено';
      setTimeout(() => {
        if (statusBadge) statusBadge.style.display = 'none';
      }, 2500);
    }
  } catch (err) {
    console.error('Ошибка загрузки системной инструкции:', err);
    if (statusBadge) {
      statusBadge.className = 'badge bg-danger';
      statusBadge.textContent = 'Ошибка';
      statusBadge.style.removeProperty('display');
    }
    showModelsNotification('Ошибка загрузки системной инструкции: ' + err.message, 'danger');
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
    showModelsNotification('✅ Системная инструкция успешно сохранена', 'success');
    if (statusBadge) {
      statusBadge.className = 'badge bg-success';
      statusBadge.textContent = 'Сохранено';
      statusBadge.style.removeProperty('display');
      setTimeout(() => {
        if (statusBadge) statusBadge.style.display = 'none';
      }, 3000);
    }
  } catch (err) {
    console.error('Ошибка сохранения системной инструкции:', err);
    if (statusBadge) {
      statusBadge.className = 'badge bg-danger';
      statusBadge.textContent = 'Ошибка сохранения';
      statusBadge.style.removeProperty('display');
    }
    showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = originalHtml;
  }
}

// Экспорт для загрузчика вкладок
window.initModelsTab = initModelsTab;
