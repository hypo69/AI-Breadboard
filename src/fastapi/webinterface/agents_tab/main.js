/**
 * =============================================================================
 * Process Name: AI Agents Management and Builder Interface
 * =============================================================================
 * Description:
 *   Client-side controller for managing AI agent registry, model pool binding,
 *   automated specification generation, and execution sandbox testing.
 *
 * File: main.js
 * Project: Mediteka
 * Module: AgentsTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

'use strict';

/**
 * Global reactive state for the AI Agents tab.
 */
const _state = {
  agents: [],
  tools: [],
  providers: {},
  currentFilter: 'all',
  activeSandboxAgent: null,
  lastGeneratedSpec: null,
  isEventsBound: false
};

/**
 * Initializes the AI Agents management tab.
 * Called on tab switch from the main admin interface.
 *
 * @returns {Promise<void>}
 */
async function initAgentsTab() {
  _bindStaticEvents();
  await _loadAllData();
}

window.initAgentsTab = initAgentsTab;

/**
 * Executes an HTTP JSON request using window.api or standard fetch.
 *
 * @param {string} endpoint - Target API endpoint path.
 * @param {RequestInit} [options={}] - Optional fetch configuration options.
 * @returns {Promise<any>} Parsed JSON response.
 * @throws {Error} Thrown if response status is not OK.
 */
async function _fetchJson(endpoint, options = {}) {
  if (window.api && typeof window.api.fetch === 'function') {
    return await window.api.fetch(endpoint, options);
  }
  const response = await fetch(endpoint, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Loads agents, capabilities catalog, and model providers from the backend API.
 *
 * @returns {Promise<void>}
 */
async function _loadAllData() {
  try {
    const [agentsRes, toolsRes, providersRes] = await Promise.all([
      _fetchJson('/api/agents'),
      _fetchJson('/api/agents/tools'),
      _fetchJson('/api/agents/providers')
    ]);

    _state.agents = Array.isArray(agentsRes) ? agentsRes : [];
    _state.tools = Array.isArray(toolsRes) ? toolsRes : [];
    _state.providers = providersRes ?? {};

    _renderCounters();
    _renderGrid();
    _populateToolsMatrix();
    _updateModelDropdown('agent-provider', 'agent-model');
    _updateModelDropdown('ai-builder-provider', 'ai-builder-model');
  } catch (err) {
    console.error('[AgentsTab] Failed to load data:', err);
    _showToast(`Failed to load data: ${err.message}`, 'danger');
    const grid = document.getElementById('agents-grid');
    if (grid) {
      grid.innerHTML = `
        <div class="col-12 text-center py-5 text-danger">
          <i class="bi bi-exclamation-triangle fs-1 d-block mb-2"></i>
          <h5>Не удалось загрузить данные агентов</h5>
          <p class="small text-secondary">${err.message}</p>
          <button class="btn btn-sm btn-outline-primary rounded-pill px-3" onclick="window.initAgentsTab()">Повторить попытку</button>
        </div>
      `;
    }
  }
}

/**
 * Binds static DOM event listeners for buttons, filters, and modal templates.
 *
 * @returns {void}
 */
function _bindStaticEvents() {
  if (_state.isEventsBound) return;
  _state.isEventsBound = true;

  // Refresh agents list
  const refreshBtn = document.getElementById('btn-refresh-agents');
  if (refreshBtn) {
    refreshBtn.onclick = async () => {
      refreshBtn.disabled = true;
      await _loadAllData();
      refreshBtn.disabled = false;
      _showToast('Список агентов обновлен', 'success');
    };
  }

  // Filter toolbar buttons
  const filterGroup = document.getElementById('agents-filter-group');
  if (filterGroup) {
    filterGroup.querySelectorAll('button').forEach((btn) => {
      btn.onclick = () => {
        filterGroup.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        _state.currentFilter = btn.getAttribute('data-filter') ?? 'all';
        _renderGrid();
      };
    });
  }

  // Modal trigger buttons
  document.getElementById('btn-open-create-agent')?.addEventListener('click', () => _openEditor(null));
  document.getElementById('btn-open-ai-builder')?.addEventListener('click', _openAiBuilder);

  // Provider change handlers
  document.getElementById('agent-provider')?.addEventListener('change', () => {
    _updateModelDropdown('agent-provider', 'agent-model');
  });
  document.getElementById('ai-builder-provider')?.addEventListener('change', () => {
    _updateModelDropdown('ai-builder-provider', 'ai-builder-model');
  });

  // Temperature slider synchronization
  const tempSlider = document.getElementById('agent-temperature');
  const tempVal = document.getElementById('agent-temp-val');
  if (tempSlider && tempVal) {
    tempSlider.oninput = () => {
      tempVal.textContent = tempSlider.value;
    };
  }

  // Action buttons
  document.getElementById('btn-save-agent')?.addEventListener('click', _handleSaveAgent);
  document.getElementById('btn-run-ai-generate')?.addEventListener('click', _handleRunAiGenerate);

  // Apply AI Generated specification to editor
  document.getElementById('btn-apply-ai-generated')?.addEventListener('click', () => {
    if (!_state.lastGeneratedSpec) return;
    const builderModalEl = document.getElementById('modal-ai-builder');
    bootstrap.Modal.getInstance(builderModalEl)?.hide();
    _openEditor(null, _state.lastGeneratedSpec);
  });

  // System Prompt templates
  document.getElementById('btn-insert-react-template')?.addEventListener('click', () => {
    const promptInput = document.getElementById('agent-system-prompt');
    if (promptInput) {
      promptInput.value =
        'Ты автономный ReAct-агент Mediteka.\n\n' +
        'ПРИНЦИП РАБОТЫ (Thought -> Action -> Observation):\n' +
        '1. Тщательно анализируй вопрос пользователя (Thought).\n' +
        '2. Выбирай необходимый инструмент из доступных (Action) с корректными параметрами.\n' +
        '3. Анализируй результат выполнения инструмента (Observation).\n' +
        '4. Сформируй итоговый структурированный ответ пользователю.\n\n' +
        'ФОРМАТ ОТВЕТА:\n' +
        '- Используй Markdown с красивым форматированием (списки, жирный шрифт, эмодзи).\n' +
        '- Не выводи технические ошибки напрямую, объясняй суть решения.';
    }
  });

  document.getElementById('btn-insert-json-template')?.addEventListener('click', () => {
    const promptInput = document.getElementById('agent-system-prompt');
    if (promptInput) {
      promptInput.value =
        'Ты специализированный аналитический агент Mediteka.\n\n' +
        'Твоя задача: структурировать полученные данные и всегда отвечать строго валидным JSON-объектом без лишнего обрамления и markdown-блоков.\n\n' +
        'Пример структуры:\n{\n  "status": "success",\n  "items": [],\n  "summary": "краткое резюме"\n}';
    }
  });

  // Sandbox inputs
  const sandboxSendBtn = document.getElementById('btn-sandbox-send');
  const sandboxInput = document.getElementById('sandbox-input-msg');
  if (sandboxSendBtn && sandboxInput) {
    sandboxSendBtn.onclick = _handleRunSandboxTest;
    sandboxInput.onkeypress = (e) => {
      if (e.key === 'Enter') _handleRunSandboxTest();
    };
  }
}

/**
 * Updates filter counter badges on top toolbar buttons.
 *
 * @returns {void}
 */
function _renderCounters() {
  const allCount = _state.agents.length;
  const activeCount = _state.agents.filter((a) => a.enabled).length;
  const systemCount = _state.agents.filter((a) => a.is_system).length;
  const customCount = _state.agents.filter((a) => !a.is_system).length;

  document.getElementById('count-all')?.replaceChildren(document.createTextNode(String(allCount)));
  document.getElementById('count-active')?.replaceChildren(document.createTextNode(String(activeCount)));
  document.getElementById('count-system')?.replaceChildren(document.createTextNode(String(systemCount)));
  document.getElementById('count-custom')?.replaceChildren(document.createTextNode(String(customCount)));
}

/**
 * Renders the responsive agent cards grid based on current filter state.
 *
 * @returns {void}
 */
function _renderGrid() {
  const grid = document.getElementById('agents-grid');
  if (!grid) return;

  const filter = _state.currentFilter;
  let items = _state.agents;

  if (filter === 'active') items = items.filter((a) => a.enabled);
  else if (filter === 'system') items = items.filter((a) => a.is_system);
  else if (filter === 'custom') items = items.filter((a) => !a.is_system);

  if (items.length === 0) {
    grid.innerHTML = `
      <div class="col-12 text-center py-5" style="color: #cbd5e1;">
        <i class="bi bi-robot fs-1 d-block mb-2" style="color: #38bdf8;"></i>
        <h5 class="text-white">Агенты не найдены</h5>
        <p class="small" style="color: #94a3b8;">Создайте нового агента с помощью AI или вручную</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = items
    .map((agent) => {
      const isSystem = Boolean(agent.is_system);
      const isEnabled = Boolean(agent.enabled);
      const providerName = _getProviderDisplayName(agent.provider);

      const toolsBadges = (agent.tools ?? [])
        .map((toolId) => {
          const tool = _state.tools.find((t) => t.id === toolId);
          const icon = tool?.icon ?? '🔧';
          const name = tool?.name ?? toolId;
          return `<span class="badge tool-badge me-1 mb-1 font-monospace">${icon} <span>${name}</span></span>`;
        })
        .join('');

      return `
        <div class="col-xl-4 col-lg-6">
          <div class="card h-100 agent-card shadow-sm" style="${!isEnabled ? 'opacity: 0.65;' : ''}">
            <div class="card-header d-flex justify-content-between align-items-center py-2 px-3">
              <div class="d-flex align-items-center gap-2">
                <span class="fs-5">${isSystem ? '⚙️' : '🧩'}</span>
                <strong class="text-white fs-6 fw-bold">${agent.name}</strong>
                ${
                  isSystem
                    ? '<span class="badge fw-bold" style="font-size: 0.7rem; background-color: #0284c7 !important; color: #ffffff !important;">SYSTEM</span>'
                    : '<span class="badge fw-bold" style="font-size: 0.7rem; background-color: #d97706 !important; color: #ffffff !important;">CUSTOM</span>'
                }
              </div>
              <div class="form-check form-switch m-0" title="Включить / Выключить">
                <input class="form-check-input agent-toggle-switch" type="checkbox" data-agent-id="${agent.id}" ${isEnabled ? 'checked' : ''}>
              </div>
            </div>
            <div class="card-body p-3 d-flex flex-column">
              <p class="small mb-3 flex-grow-1 agent-desc" style="min-height: 40px; color: #cbd5e1; line-height: 1.45;">${agent.description || 'Описание отсутствует'}</p>
              
              <div class="agent-spec-box mb-3 small">
                <div class="d-flex justify-content-between align-items-center mb-1 pb-1" style="border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                  <span class="spec-label">Провайдер &amp; Модель:</span>
                  <span class="badge spec-value-badge text-truncate" style="max-width: 190px;">${providerName}: ${agent.model}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                  <span class="spec-label">Температура / Шаги:</span>
                  <span class="spec-tech-val font-monospace">T: ${agent.temperature} <span style="color: #64748b;">|</span> Max: ${agent.max_steps}</span>
                </div>
              </div>

              <div class="mb-3">
                <div class="small fw-semibold mb-2" style="color: #f1f5f9;">Инструменты (${(agent.tools ?? []).length}):</div>
                <div class="d-flex flex-wrap">${toolsBadges || '<span class="small" style="color: #94a3b8;">Без внешних инструментов</span>'}</div>
              </div>

              <div class="mt-auto d-flex justify-content-between gap-2 pt-2" style="border-top: 1px solid #334155;">
                <button class="btn btn-sm rounded-pill px-3 btn-test-sandbox" data-agent-id="${agent.id}">
                  <i class="bi bi-play-fill"></i> Тест в Sandbox
                </button>
                <div class="d-flex gap-1">
                  <button class="btn btn-sm rounded-pill px-2 btn-edit-agent" data-agent-id="${agent.id}" title="Редактировать">
                    <i class="bi bi-pencil-fill"></i>
                  </button>
                  ${
                    !isSystem
                      ? `
                    <button class="btn btn-sm rounded-pill px-2 btn-delete-agent" data-agent-id="${agent.id}" title="Удалить">
                      <i class="bi bi-trash-fill"></i>
                    </button>
                  `
                      : ''
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    })
    .join('');

  // Attach card event listeners
  grid.querySelectorAll('.agent-toggle-switch').forEach((sw) => {
    sw.onchange = async () => {
      const agentId = sw.getAttribute('data-agent-id');
      if (agentId) await _toggleAgentState(agentId, sw.checked);
    };
  });

  grid.querySelectorAll('.btn-test-sandbox').forEach((btn) => {
    btn.onclick = () => {
      const agentId = btn.getAttribute('data-agent-id');
      if (agentId) _openSandbox(agentId);
    };
  });

  grid.querySelectorAll('.btn-edit-agent').forEach((btn) => {
    btn.onclick = () => {
      const agentId = btn.getAttribute('data-agent-id');
      if (agentId) _openEditor(agentId);
    };
  });

  grid.querySelectorAll('.btn-delete-agent').forEach((btn) => {
    btn.onclick = () => {
      const agentId = btn.getAttribute('data-agent-id');
      if (agentId) _deleteAgent(agentId);
    };
  });
}

/**
 * Toggles an agent's enabled state and persists it to the server.
 *
 * @param {string} agentId - Target agent unique identifier.
 * @param {boolean} enabled - New enabled state.
 * @returns {Promise<void>}
 */
async function _toggleAgentState(agentId, enabled) {
  const agent = _state.agents.find((a) => a.id === agentId);
  if (!agent) return;

  agent.enabled = enabled;
  try {
    await _fetchJson(`/api/agents/${agentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(agent)
    });
    _renderCounters();
    _renderGrid();
    _showToast(`Агент "${agent.name}" ${enabled ? 'включен' : 'отключен'}`, 'success');
  } catch (err) {
    console.error('[AgentsTab] Error toggling agent:', err);
    _showToast(`Ошибка: ${err.message}`, 'danger');
    await _loadAllData();
  }
}

/**
 * Populates capability checkboxes inside the editor modal.
 *
 * @returns {void}
 */
function _populateToolsMatrix() {
  const container = document.getElementById('agent-tools-matrix');
  if (!container) return;

  container.innerHTML = _state.tools
    .map(
      (tool) => `
      <div class="col-md-6">
        <div class="p-3 rounded h-100" style="background: #1e293b; border: 1px solid #334155;">
          <div class="form-check form-switch m-0">
            <input class="form-check-input tool-checkbox" type="checkbox" value="${tool.id}" id="tool-chk-${tool.id}">
            <label class="form-check-label small text-white fw-bold" for="tool-chk-${tool.id}">
              ${tool.icon} ${tool.name}
            </label>
          </div>
          <div class="small mt-1" style="color: #cbd5e1; font-size: 0.8rem; line-height: 1.4;">${tool.description}</div>
        </div>
      </div>
    `
    )
    .join('');

  container.querySelectorAll('.tool-checkbox').forEach((chk) => {
    chk.onchange = _updateSelectedToolsCounter;
  });
}

/**
 * Updates selected capabilities counter badge in the editor modal.
 *
 * @returns {void}
 */
function _updateSelectedToolsCounter() {
  const count = document.querySelectorAll('#agent-tools-matrix .tool-checkbox:checked').length;
  const badge = document.getElementById('agent-tools-count');
  if (badge) badge.textContent = `${count} выбрано`;
}

/**
 * Updates model selection dropdown options when provider selection changes.
 *
 * @param {string} providerSelectId - ID of provider select element.
 * @param {string} modelSelectId - ID of model select element.
 * @param {string} [selectedModel=''] - Model ID to select by default.
 * @returns {void}
 */
function _updateModelDropdown(providerSelectId, modelSelectId, selectedModel = '') {
  const pSel = document.getElementById(providerSelectId);
  const mSel = document.getElementById(modelSelectId);
  if (!pSel || !mSel) return;

  const prov = _state.providers[pSel.value];
  const models = prov?.models ?? [];

  mSel.innerHTML = models.map((m) => `<option value="${m.id}">${m.name || m.id}</option>`).join('');

  if (selectedModel && models.some((m) => m.id === selectedModel)) {
    mSel.value = selectedModel;
  } else if (prov?.default_model) {
    mSel.value = prov.default_model;
  }
}

/**
 * Opens agent editor modal for creating or updating an agent.
 *
 * @param {string|null} [agentId=null] - Agent ID to edit, or null for create.
 * @param {object|null} [prefillData=null] - Pre-filled data from AI builder.
 * @returns {void}
 */
function _openEditor(agentId = null, prefillData = null) {
  const modalEl = document.getElementById('modal-agent-editor');
  if (!modalEl) return;

  const modeInput = document.getElementById('agent-edit-mode');
  const idInput = document.getElementById('agent-id');
  const nameInput = document.getElementById('agent-name');
  const descInput = document.getElementById('agent-desc');
  const enabledChk = document.getElementById('agent-enabled');
  const providerSel = document.getElementById('agent-provider');
  const tempSlider = document.getElementById('agent-temperature');
  const tempVal = document.getElementById('agent-temp-val');
  const maxStepsInput = document.getElementById('agent-max-steps');
  const timeoutInput = document.getElementById('agent-timeout');
  const promptTa = document.getElementById('agent-system-prompt');

  // Reset tools checkboxes
  document.querySelectorAll('#agent-tools-matrix .tool-checkbox').forEach((chk) => {
    chk.checked = false;
  });

  if (agentId) {
    const agent = _state.agents.find((a) => a.id === agentId);
    if (!agent) return;

    if (modeInput) modeInput.value = 'edit';
    if (idInput) {
      idInput.value = agent.id;
      idInput.disabled = true;
    }
    if (nameInput) nameInput.value = agent.name;
    if (descInput) descInput.value = agent.description ?? '';
    if (enabledChk) enabledChk.checked = Boolean(agent.enabled);
    if (providerSel) providerSel.value = agent.provider ?? 'gemini';

    _updateModelDropdown('agent-provider', 'agent-model', agent.model);

    if (tempSlider) {
      tempSlider.value = agent.temperature ?? 0.3;
      if (tempVal) tempVal.textContent = tempSlider.value;
    }
    if (maxStepsInput) maxStepsInput.value = agent.max_steps ?? 15;
    if (timeoutInput) timeoutInput.value = agent.timeout_seconds ?? 60;
    if (promptTa) promptTa.value = agent.system_prompt ?? '';

    (agent.tools ?? []).forEach((tId) => {
      const chk = document.getElementById(`tool-chk-${tId}`);
      if (chk) chk.checked = true;
    });
  } else if (prefillData) {
    if (modeInput) modeInput.value = 'create';
    if (idInput) {
      idInput.value = (prefillData.name || 'agent').toLowerCase().replace(/[^a-z0-9_]/g, '_').slice(0, 25);
      idInput.disabled = false;
    }
    if (nameInput) nameInput.value = prefillData.name ?? 'Новый ИИ-Агент';
    if (descInput) descInput.value = prefillData.description ?? '';
    if (enabledChk) enabledChk.checked = true;
    if (providerSel) providerSel.value = prefillData.provider ?? 'gemini';

    _updateModelDropdown('agent-provider', 'agent-model', prefillData.model);

    if (tempSlider) {
      tempSlider.value = prefillData.temperature ?? 0.3;
      if (tempVal) tempVal.textContent = tempSlider.value;
    }
    if (maxStepsInput) maxStepsInput.value = prefillData.max_steps ?? 15;
    if (timeoutInput) timeoutInput.value = 60;
    if (promptTa) promptTa.value = prefillData.system_prompt ?? '';

    (prefillData.recommended_tools ?? []).forEach((tId) => {
      const chk = document.getElementById(`tool-chk-${tId}`);
      if (chk) chk.checked = true;
    });
  } else {
    if (modeInput) modeInput.value = 'create';
    if (idInput) {
      idInput.value = '';
      idInput.disabled = false;
    }
    if (nameInput) nameInput.value = '';
    if (descInput) descInput.value = '';
    if (enabledChk) enabledChk.checked = true;
    if (providerSel) providerSel.value = 'gemini';

    _updateModelDropdown('agent-provider', 'agent-model');

    if (tempSlider) {
      tempSlider.value = 0.3;
      if (tempVal) tempVal.textContent = '0.3';
    }
    if (maxStepsInput) maxStepsInput.value = 15;
    if (timeoutInput) timeoutInput.value = 60;
    if (promptTa) promptTa.value = '';
  }

  _updateSelectedToolsCounter();
  new bootstrap.Modal(modalEl).show();
}

/**
 * Saves agent configuration (POST create or PUT update).
 *
 * @returns {Promise<void>}
 */
async function _handleSaveAgent() {
  const mode = document.getElementById('agent-edit-mode')?.value ?? 'create';
  const id = document.getElementById('agent-id')?.value.trim();
  const name = document.getElementById('agent-name')?.value.trim();
  const desc = document.getElementById('agent-desc')?.value.trim();
  const enabled = document.getElementById('agent-enabled')?.checked ?? true;
  const provider = document.getElementById('agent-provider')?.value ?? 'gemini';
  const model = document.getElementById('agent-model')?.value ?? 'gemini-2.5-flash';
  const temperature = parseFloat(document.getElementById('agent-temperature')?.value ?? '0.3');
  const max_steps = parseInt(document.getElementById('agent-max-steps')?.value ?? '15', 10);
  const timeout_seconds = parseInt(document.getElementById('agent-timeout')?.value ?? '60', 10);
  const system_prompt = document.getElementById('agent-system-prompt')?.value.trim() ?? '';

  if (!id || !name) {
    _showToast('ID и Название агента обязательны для заполнения', 'warning');
    return;
  }

  const selectedTools = [];
  document.querySelectorAll('#agent-tools-matrix .tool-checkbox:checked').forEach((chk) => {
    selectedTools.push(chk.value);
  });

  const payload = {
    id,
    name,
    description: desc,
    enabled,
    provider,
    model,
    temperature,
    max_steps,
    timeout_seconds,
    tools: selectedTools,
    system_prompt
  };

  const saveBtn = document.getElementById('btn-save-agent');
  if (saveBtn) saveBtn.disabled = true;

  try {
    if (mode === 'create') {
      await _fetchJson('/api/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      _showToast(`Агент "${name}" успешно создан!`, 'success');
    } else {
      await _fetchJson(`/api/agents/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      _showToast(`Агент "${name}" успешно обновлен!`, 'success');
    }

    const modalEl = document.getElementById('modal-agent-editor');
    bootstrap.Modal.getInstance(modalEl)?.hide();
    await _loadAllData();
  } catch (err) {
    console.error('[AgentsTab] Error saving agent:', err);
    _showToast(`Ошибка сохранения: ${err.message}`, 'danger');
  } finally {
    if (saveBtn) saveBtn.disabled = false;
  }
}

/**
 * Deletes an existing custom agent after confirmation.
 *
 * @param {string} agentId - Target agent unique identifier.
 * @returns {Promise<void>}
 */
async function _deleteAgent(agentId) {
  const agent = _state.agents.find((a) => a.id === agentId);
  if (!agent) return;

  if (!confirm(`Вы действительно хотите удалить агента "${agent.name}" (${agent.id})?`)) {
    return;
  }

  try {
    await _fetchJson(`/api/agents/${agentId}`, { method: 'DELETE' });
    _showToast(`Агент "${agent.name}" удален`, 'success');
    await _loadAllData();
  } catch (err) {
    console.error('[AgentsTab] Error deleting agent:', err);
    _showToast(`Ошибка удаления: ${err.message}`, 'danger');
  }
}

/**
 * Opens AI prompt architect builder modal.
 *
 * @returns {void}
 */
function _openAiBuilder() {
  const modalEl = document.getElementById('modal-ai-builder');
  if (!modalEl) return;

  const promptInput = document.getElementById('ai-builder-prompt');
  const resultBox = document.getElementById('ai-builder-result');
  if (promptInput) promptInput.value = '';
  if (resultBox) resultBox.classList.add('d-none');
  _state.lastGeneratedSpec = null;

  new bootstrap.Modal(modalEl).show();
}

/**
 * Generates an agent specification using selected LLM architect model.
 *
 * @returns {Promise<void>}
 */
async function _handleRunAiGenerate() {
  const taskDesc = document.getElementById('ai-builder-prompt')?.value.trim();
  const provider = document.getElementById('ai-builder-provider')?.value ?? 'gemini';
  const model = document.getElementById('ai-builder-model')?.value ?? 'gemini-2.5-flash';

  if (!taskDesc) {
    _showToast('Пожалуйста, опишите задачу агента', 'warning');
    return;
  }

  const runBtn = document.getElementById('btn-run-ai-generate');
  if (runBtn) {
    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Анализ задачи и генерация...';
  }

  try {
    const res = await _fetchJson('/api/agents/generate-prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_description: taskDesc, provider, model })
    });

    if (res?.data) {
      _state.lastGeneratedSpec = { ...res.data, provider, model };
      const resultBox = document.getElementById('ai-builder-result');
      const previewBox = document.getElementById('ai-builder-preview-box');
      if (resultBox && previewBox) {
        resultBox.classList.remove('d-none');
        previewBox.innerHTML = `
          <div><strong style="color: #38bdf8;">Название:</strong> <span class="text-white fw-bold">${res.data.name}</span></div>
          <div class="mt-1"><strong style="color: #cbd5e1;">Описание:</strong> <span style="color: #f1f5f9;">${res.data.description}</span></div>
          <div class="mt-1"><strong style="color: #4ade80;">Инструменты:</strong> <span style="color: #f8fafc;">${(res.data.recommended_tools ?? []).join(', ') || 'нет'}</span></div>
          <div class="mt-2 p-2 rounded" style="background: #0f172a; border: 1px solid #334155; color: #f8fafc; white-space: pre-wrap; font-size: 0.85rem; line-height: 1.45;">${res.data.system_prompt}</div>
        `;
      }
      _showToast('Спецификация агента успешно сгенерирована!', 'success');
    }
  } catch (err) {
    console.error('[AgentsTab] AI Generator error:', err);
    _showToast(`Ошибка генерации: ${err.message}`, 'danger');
  } finally {
    if (runBtn) {
      runBtn.disabled = false;
      runBtn.innerHTML = '<i class="bi bi-stars me-1"></i> Сгенерировать спецификацию';
    }
  }
}

/**
 * Opens sandbox modal for interactive agent testing.
 *
 * @param {string} agentId - Target agent unique identifier.
 * @returns {void}
 */
function _openSandbox(agentId) {
  const agent = _state.agents.find((a) => a.id === agentId);
  if (!agent) return;

  _state.activeSandboxAgent = agent;
  const modalEl = document.getElementById('modal-agent-sandbox');
  if (!modalEl) return;

  document.getElementById('sandbox-agent-name')?.replaceChildren(document.createTextNode(agent.name));
  const modelBadge = document.getElementById('sandbox-agent-model');
  if (modelBadge) modelBadge.textContent = `${_getProviderDisplayName(agent.provider)}: ${agent.model}`;

  const toolsSummary = document.getElementById('sandbox-agent-tools-summary');
  if (toolsSummary) toolsSummary.textContent = `Инструментов: ${(agent.tools ?? []).length}`;

  const msgsList = document.getElementById('sandbox-messages-list');
  const placeholder = document.getElementById('sandbox-placeholder');
  if (msgsList) msgsList.innerHTML = '';
  if (placeholder) placeholder.style.display = 'block';

  new bootstrap.Modal(modalEl).show();
}

/**
 * Executes a test query against the active sandbox agent and renders execution trace.
 *
 * @returns {Promise<void>}
 */
async function _handleRunSandboxTest() {
  const agent = _state.activeSandboxAgent;
  const input = document.getElementById('sandbox-input-msg');
  const sendBtn = document.getElementById('btn-sandbox-send');
  const msgsList = document.getElementById('sandbox-messages-list');
  const placeholder = document.getElementById('sandbox-placeholder');

  if (!agent || !input || !msgsList) return;
  const query = input.value.trim();
  if (!query) return;

  if (placeholder) placeholder.style.display = 'none';

  // Append user message
  const userMsgEl = document.createElement('div');
  userMsgEl.className = 'd-flex justify-content-end mb-3';
  userMsgEl.innerHTML = `
    <div class="p-2 px-3 rounded shadow-sm text-white small" style="background-color: #2563eb; max-width: 80%; font-weight: 500;">
      <strong>Вы:</strong> ${query}
    </div>
  `;
  msgsList.appendChild(userMsgEl);

  input.value = '';
  if (sendBtn) sendBtn.disabled = true;

  // Append response placeholder with loader
  const botMsgEl = document.createElement('div');
  botMsgEl.className = 'd-flex flex-column mb-3';
  botMsgEl.innerHTML = `
    <div class="p-3 rounded small" style="background: #0f172a; border: 1px solid #334155; color: #f8fafc;">
      <div class="d-flex align-items-center gap-2 mb-2" style="color: #fbbf24; font-weight: 600;">
        <span class="spinner-border spinner-border-sm"></span>
        <span>Агент выполняет рассуждение и вызовы инструментов...</span>
      </div>
      <div class="steps-trace small font-monospace" style="color: #cbd5e1;"></div>
    </div>
  `;
  msgsList.appendChild(botMsgEl);
  msgsList.scrollTop = msgsList.scrollHeight;

  try {
    const res = await _fetchJson('/api/agents/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: agent.id, test_message: query })
    });

    const stepsHtml = (res.steps ?? [])
      .map((s) => {
        let icon = '🔹';
        if (s.type === 'tool_init') icon = '🛠️';
        else if (s.type === 'action') icon = '⚡';
        else if (s.type === 'finish') icon = '✅';
        else if (s.type === 'error') icon = '❌';

        return `<div class="mb-1">${icon} <span style="color: #38bdf8; font-weight: bold;">[Шаг ${s.step}]</span> <span style="color: #e2e8f0;">${s.content}</span></div>`;
      })
      .join('');

    botMsgEl.innerHTML = `
      <div class="p-3 rounded small" style="background: #0f172a; border: 1px solid #334155; color: #f8fafc;">
        <div class="d-flex justify-content-between align-items-center mb-2 pb-1" style="border-bottom: 1px solid #334155;">
          <strong style="color: #38bdf8; font-size: 0.95rem;">🤖 ${agent.name}</strong>
          <span class="badge" style="background: #334155; color: #f8fafc; font-weight: 600;">${res.duration_ms ?? 0} мс</span>
        </div>
        
        <div class="mb-2" style="white-space: pre-wrap; color: #f8fafc; line-height: 1.5;">${res.response || 'Пустой ответ'}</div>
        
        <div class="p-2 rounded mt-2 small font-monospace" style="background: #020617; border: 1px solid #334155; font-size: 0.8rem; line-height: 1.45;">
          <div class="fw-bold mb-1" style="color: #cbd5e1;">Трассировка выполнения (ReAct Trace):</div>
          ${stepsHtml}
        </div>
      </div>
    `;
  } catch (err) {
    botMsgEl.innerHTML = `
      <div class="p-3 rounded small" style="background: #450a0a; border: 1px solid #dc2626; color: #fecaca;">
        <strong style="color: #ef4444;">Ошибка выполнения:</strong> ${err.message}
      </div>
    `;
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    const chatWin = document.getElementById('sandbox-chat-window');
    if (chatWin) chatWin.scrollTop = chatWin.scrollHeight;
  }
}

/**
 * Returns human-readable display name for provider identifier.
 *
 * @param {string} provKey - Provider key (e.g. 'gemini', 'agy', 'foundry', 'ollama').
 * @returns {string} Provider display label.
 */
function _getProviderDisplayName(provKey) {
  return _state.providers[provKey]?.name ?? provKey;
}

/**
 * Displays floating feedback notification toast.
 *
 * @param {string} message - Notification text message.
 * @param {string} [type='info'] - Bootstrap color variant ('info', 'success', 'warning', 'danger').
 * @returns {void}
 */
function _showToast(message, type = 'info') {
  if (typeof window.showModelsNotification === 'function') {
    window.showModelsNotification(message, type);
    return;
  }
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} position-fixed bottom-0 end-0 m-3 shadow`;
  alertDiv.style.zIndex = '9999';
  alertDiv.textContent = message;
  document.body.appendChild(alertDiv);
  setTimeout(() => alertDiv.remove(), 3500);
}
