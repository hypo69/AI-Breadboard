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
        showModelsNotification('Сначала выберите модель', 'warning');
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
        console.error('Ошибка переключения избранного:', err);
        showModelsNotification('Ошибка: ' + err.message, 'danger');
      } finally {
        favToggleBtn.disabled = false;
      }
    };
  }

  if (saveNoteBtn && modelSelect && modelNoteInput) {
    saveNoteBtn.onclick = async () => {
      const curModel = modelSelect.value;
      if (!curModel) {
        showModelsNotification('Сначала выберите модель', 'warning');
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
        console.error('Ошибка сохранения заметки:', err);
        showModelsNotification('Ошибка сохранения заметки: ' + err.message, 'danger');
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
        showModelsNotification(`Google Antigravity (AGY) ${enabled ? 'активирован' : 'деактивирован'}${remember ? ' (сохранено в config.json)' : ''}`, 'info');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка переключения Antigravity:', err);
        showModelsNotification('Ошибка переключения: ' + err.message, 'danger');
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
        showModelsNotification(`Microsoft Foundry ${enabled ? 'активирован' : 'деактивирован'}${remember ? ' (сохранено в config.json)' : ''}`, 'info');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка переключения Foundry:', err);
        showModelsNotification('Ошибка переключения: ' + err.message, 'danger');
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
        showModelsNotification(`Ollama ${enabled ? 'активирован' : 'деактивирован'}${remember ? ' (сохранено в config.json)' : ''}`, 'info');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка переключения Ollama:', err);
        showModelsNotification('Ошибка переключения: ' + err.message, 'danger');
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
        showModelsNotification(`ONNX / Olive ${enabled ? 'активирован' : 'деактивирован'}${remember ? ' (сохранено в config.json)' : ''}`, 'info');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка переключения ONNX / Olive:', err);
        showModelsNotification('Ошибка переключения: ' + err.message, 'danger');
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
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, model, key, remember })
        });
        showModelsNotification(`Настройки Antigravity (AGY) успешно сохранены${remember ? ' в config.json' : ''}`, 'success');
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
      const remember = document.getElementById('foundry-remember')?.checked ?? true;
      const url = document.getElementById('foundry-url')?.value.trim() || 'http://localhost:54837';
      const key = document.getElementById('foundry-key')?.value.trim() || '';
      const model = document.getElementById('foundry-model')?.value?.trim() || 'qwen2.5-1.5b';
      
      saveFoundryBtn.disabled = true;
      try {
        await window.api.fetch('/api/foundry/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, url, key, model, remember })
        });
        showModelsNotification(`Настройки Microsoft Foundry успешно сохранены${remember ? ' в config.json' : ''}`, 'success');
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
      const remember = document.getElementById('ollama-remember')?.checked ?? true;
      const url = document.getElementById('ollama-url')?.value.trim() || 'http://localhost:11434';
      const model = document.getElementById('ollama-model')?.value?.trim() || 'llama3.1';
      
      saveOllamaBtn.disabled = true;
      try {
        await window.api.fetch('/api/ollama/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled, url, model, remember })
        });
        showModelsNotification(`Настройки Ollama успешно сохранены${remember ? ' в config.json' : ''}`, 'success');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка сохранения Ollama:', err);
        showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
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
        showModelsNotification(`Настройки ONNX / Olive успешно сохранены${remember ? ' в config.json' : ''}`, 'success');
        if (modelSelect && saveBtn) await loadTabModels(modelSelect, saveBtn);
      } catch (err) {
        console.error('Ошибка сохранения ONNX / Olive:', err);
        showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
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
        if (typeof window.updateChatBadges === 'function') {
          window.updateChatBadges(selectedModel);
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

  if (refreshGAccountsBtn && gaccountsListBody) {
    refreshGAccountsBtn.onclick = async () => {
      refreshGAccountsBtn.disabled = true;
      const originalText = refreshGAccountsBtn.innerHTML;
      refreshGAccountsBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Обновление...';
      try {
        await refreshGoogleAccountsList(gaccountsListBody);
        showModelsNotification('Список аккаунтов Google обновлен', 'success');
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
    showModelsNotification('Выберите модель для тестирования!', 'warning');
    return;
  }

  if (!message) {
    showModelsNotification('Введите текст проверочного запроса!', 'warning');
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
        <span class="text-truncate">Отправка запроса в <strong>${escapeHtml(model)}</strong> (${escapeHtml(provider)})...</span>
      </div>
      <button class="btn btn-outline-danger btn-sm py-0 px-2 rounded ms-2 flex-shrink-0" id="btn-model-test-cancel-inner" type="button" title="Отменить проверочный запрос">
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
        <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom border-secondary">
          <div>
            <span class="badge bg-success me-2"><i class="bi bi-check-circle me-1"></i>200 OK</span>
            <span class="text-secondary small font-monospace">⚡ ${res.duration_ms || 0} ms</span>
          </div>
          <span class="badge bg-dark border border-secondary text-info font-monospace">${escapeHtml(res.model || model)}</span>
        </div>
        <div class="text-white small mt-1 font-monospace" style="white-space: pre-wrap; word-break: break-word;">${escapeHtml(res.response || 'Пустой ответ от модели')}</div>
      `;
    } else {
      const errMsg = (res && res.message) ? res.message : 'Неизвестная ошибка при запросе к модели';
      resultContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom border-secondary">
          <div>
            <span class="badge bg-danger me-2"><i class="bi bi-x-circle me-1"></i>Ошибка</span>
            <span class="text-secondary small font-monospace">⚡ ${res?.duration_ms || 0} ms</span>
          </div>
          <span class="badge bg-dark border border-secondary text-warning font-monospace">${escapeHtml(model)}</span>
        </div>
        <div class="text-danger small mt-1 font-monospace" style="white-space: pre-wrap; word-break: break-word;">${escapeHtml(errMsg)}</div>
      `;
    }
  } catch (err) {
    if (err.name === 'AbortError' || err.message?.toLowerCase().includes('abort')) {
      resultContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom border-secondary">
          <span class="badge bg-warning text-dark"><i class="bi bi-slash-circle me-1"></i>Отменено</span>
          <span class="badge bg-dark border border-secondary text-warning font-monospace">${escapeHtml(model)}</span>
        </div>
        <div class="text-warning small mt-1 font-monospace"><i class="bi bi-info-circle me-1"></i>Запрос отменен пользователем.</div>
      `;
    } else {
      console.error('Error during model test request:', err);
      resultContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom border-secondary">
          <span class="badge bg-danger"><i class="bi bi-x-circle me-1"></i>Ошибка сети/API</span>
          <span class="badge bg-dark border border-secondary text-warning font-monospace">${escapeHtml(model)}</span>
        </div>
        <div class="text-danger small mt-1 font-monospace" style="white-space: pre-wrap; word-break: break-word;">${escapeHtml(err.message || 'Ошибка соединения')}</div>
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
      favBtn.title = 'Удалить модель из избранного';
    } else {
      favBtn.classList.remove('btn-warning', 'text-dark');
      favBtn.classList.add('btn-outline-warning');
      favBtn.title = 'Добавить модель в избранное';
    }
  }
  if (statusBadge) {
    if (isFav) {
      statusBadge.textContent = 'В избранном ⭐';
      statusBadge.className = 'badge bg-warning text-dark font-monospace';
    } else {
      statusBadge.textContent = 'Не в избранном';
      statusBadge.className = 'badge bg-dark border border-secondary text-secondary';
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
  container.innerHTML = '';

  favKeys.forEach(modelName => {
    const data = window.userFavoriteModels[modelName] || {};
    const note = data.note ? `\nЗаметка: ${data.note}` : '';
    
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
    btnRemove.innerHTML = '<i class="bi bi-x"></i>';
    btnRemove.title = `Удалить ${modelName} из избранного`;
    btnRemove.onclick = async (e) => {
      e.stopPropagation();
      try {
        await window.api.fetch(`/auth/favorites/${encodeURIComponent(modelName)}`, { method: 'DELETE' });
        delete window.userFavoriteModels[modelName];
        updateModelFavoriteUI(modelSelect);
        updateModelSelectOptions(modelSelect);
        showModelsNotification(`Модель "${modelName}" удалена из избранного`, 'info');
      } catch (err) {
        showModelsNotification('Ошибка удаления: ' + err.message, 'danger');
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
      showModelsNotification('Ошибка загрузки моделей AI: ' + err.message, 'danger');
      return {};
    }
  };

  modelsGrouped = await fetchModels(forceRefresh);
  window._modelsGrouped = modelsGrouped;
  if (forceRefresh) {
    showModelsNotification('Список моделей успешно обновлен', 'success');
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
        else if (cleanName.startsWith('onnx:')) cleanName = cleanName.substring(5);
        
        const isFav = window.userFavoriteModels && Boolean(window.userFavoriteModels[modelName]);
        const isUnsupported = unsupList.includes(cleanName) || unsupList.includes(modelName);
        
        let label = cleanName;
        if (isFav) label = `⭐ ${label}`;
        if (isUnsupported) label = `${label} ⚠️ [отфильтрована]`;

        option.textContent = label;
        modelSelect.appendChild(option);
      });
      saveBtn.disabled = false;
    }
    updateModelFavoriteUI(modelSelect);
  };
  window._populateModels = populateModels;

  if (providerSelect) {
    providerSelect.onchange = async () => {
      const chosenProvider = providerSelect.value;
      // При каждом выборе провайдера актуализируем список доступных моделей
      modelSelect.innerHTML = '<option value="">Обновление списка моделей...</option>';
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
    console.error('Ошибка загрузки настроек ONNX / Olive:', err);
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
        tdStatus.innerHTML = '<span class="badge bg-danger" title="Исчерпан суточный лимит квоты">Лимит</span>';
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
        btnDefault.title = 'Сделать аккаунтом по умолчанию';
        btnDefault.innerHTML = '<i class="bi bi-star"></i>';
        btnDefault.onclick = () => setGoogleAccountDefault(acc.name, container);
        tdActions.appendChild(btnDefault);
      }

      // Reset status button
      if (acc.status === 'exhausted') {
        const btnReset = document.createElement('button');
        btnReset.className = 'btn btn-xs btn-outline-info btn-sm me-1';
        btnReset.title = 'Сбросить статус исчерпания';
        btnReset.innerHTML = '<i class="bi bi-arrow-repeat"></i>';
        btnReset.onclick = () => resetGoogleAccountStatus(acc.name, container);
        tdActions.appendChild(btnReset);
      }

      // Test button
      const btnTest = document.createElement('button');
      btnTest.className = 'btn btn-xs btn-outline-info btn-sm me-1';
      btnTest.title = 'Проверить доступ и авторизацию';
      btnTest.innerHTML = '<i class="bi bi-play-circle"></i> Тест';
      btnTest.onclick = () => testGoogleAccount(acc.name);
      tdActions.appendChild(btnTest);

      // Delete button
      const btnDelete = document.createElement('button');
      btnDelete.className = 'btn btn-xs btn-outline-danger btn-sm';
      btnDelete.title = 'Удалить аккаунт из пула';
      btnDelete.innerHTML = '<i class="bi bi-trash"></i>';
      btnDelete.onclick = () => deleteGoogleAccount(acc.name, container);
      tdActions.appendChild(btnDelete);

      row.appendChild(tdActions);
      container.appendChild(row);
    });

  } catch (err) {
    console.error('Ошибка загрузки аккаунтов Google Workspace:', err);
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
    showModelsNotification('Введите имя аккаунта (например: work, personal)', 'warning');
    nameInput.focus();
    return;
  }

  // Check if file is selected or JSON is pasted
  const file = fileInput && fileInput.files && fileInput.files[0];
  const jsonContent = jsonTextarea ? jsonTextarea.value.trim() : '';

  if (!file && !jsonContent) {
    showModelsNotification('Загрузите файл credentials.json / service_account.json или вставьте JSON', 'warning');
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
        throw new Error('Некорректный JSON в поле учетных данных');
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
    console.error('Ошибка сохранения аккаунта Google:', err);
    showModelsNotification('Ошибка сохранения: ' + err.message, 'danger');
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
    console.error('Ошибка установки аккаунта по умолчанию:', err);
    showModelsNotification('Ошибка: ' + err.message, 'danger');
  }
}

async function resetGoogleAccountStatus(name, container) {
  try {
    await window.api.googleAccounts.resetStatus(name);
    showModelsNotification(`Статус аккаунта "${name}" сброшен в активный`, 'success');
    if (container) await refreshGoogleAccountsList(container);
  } catch (err) {
    console.error('Ошибка сброса статуса аккаунта:', err);
    showModelsNotification('Ошибка сброса: ' + err.message, 'danger');
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
      testBody.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle me-1"></i>Ошибка проверки: ${escapeHtml(err.message)}</span>`;
    }
  }
}

async function deleteGoogleAccount(name, container) {
  if (!confirm(`Вы уверены, что хотите удалить аккаунт "${name}" из пула Google Workspace?`)) return;
  try {
    await window.api.googleAccounts.delete(name);
    showModelsNotification(`Аккаунт "${name}" успешно удален`, 'success');
    if (container) await refreshGoogleAccountsList(container);
  } catch (err) {
    console.error('Ошибка удаления аккаунта Google:', err);
    showModelsNotification('Ошибка удаления: ' + err.message, 'danger');
  }
}

// Export for tab loader
window.initModelsTab = initModelsTab;
window.refreshGoogleAccountsList = refreshGoogleAccountsList;
