// =============================================================================
// Process Name: App Configuration Editor UI Module
// =============================================================================
// Description:
//   Reusable client-side controller for inspecting and modifying config.json
//   across /apps microservices in the AI-Breadboard web administrative panel.
//
// File: appConfigEditor.js
// Project: ai-breadboard
// Package: src.api.webinterface.js
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function() {
  let activeConfig = null;
  let activeAppName = '';

  /**
   * Fetch app config from server
   * @param {string} appName
   * @returns {Promise<Object>}
   */
  async function fetchAppConfig(appName) {
    let res;
    if (window.api && typeof window.api.fetch === 'function') {
      try {
        return await window.api.fetch(`/api/admin/apps/${appName}/config`);
      } catch (e) {
        // fallback
      }
    }
    res = await fetch(`/api/admin/apps/${appName}/config`);
    if (!res.ok) {
      throw new Error(`Failed to load config: HTTP ${res.status}`);
    }
    return await res.json();
  }

  /**
   * Save app config to server
   * @param {string} appName
   * @param {Object} configObj
   * @returns {Promise<Object>}
   */
  async function saveAppConfig(appName, configObj) {
    const payload = { config: configObj };
    const res = await fetch(`/api/admin/apps/${appName}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  }

  /**
   * Render or update modal HTML
   */
  function ensureModalExists() {
    let modalEl = document.getElementById('app-config-modal');
    if (!modalEl) {
      modalEl = document.createElement('div');
      modalEl.id = 'app-config-modal';
      modalEl.className = 'modal fade';
      modalEl.tabIndex = -1;
      modalEl.setAttribute('aria-hidden', 'true');
      modalEl.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
          <div class="modal-content border-secondary shadow-lg" style="background: #0f172a; color: #f8fafc;">
            <div class="modal-header border-secondary" style="background: #1e293b;">
              <h5 class="modal-title d-flex align-items-center gap-2 fw-bold text-info" id="app-config-modal-title">
                <i class="bi bi-sliders"></i> Настройка конфигурации (config.json)
              </h5>
              <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-3">
              <div id="app-config-alert" class="alert d-none py-2 px-3 small"></div>
              
              <!-- Tabs: Visual Form vs Raw JSON -->
              <ul class="nav nav-pills nav-fill mb-3" id="app-config-tabs" role="tablist">
                <li class="nav-item">
                  <button class="nav-link active py-1 small fw-semibold" id="app-config-tab-visual-btn" data-bs-toggle="pill" data-bs-target="#app-config-tab-visual" type="button">
                    <i class="bi bi-ui-checks me-1"></i> Визуальная форма
                  </button>
                </li>
                <li class="nav-item">
                  <button class="nav-link py-1 small fw-semibold" id="app-config-tab-raw-btn" data-bs-toggle="pill" data-bs-target="#app-config-tab-raw" type="button">
                    <i class="bi bi-code-square me-1"></i> Исходный JSON
                  </button>
                </li>
              </ul>

              <div class="tab-content">
                <!-- Visual Form Pane -->
                <div class="tab-pane fade show active" id="app-config-tab-visual">
                  <div class="card border-secondary mb-3" style="background: #1e293b;">
                    <div class="card-header border-secondary py-2 small fw-bold text-primary d-flex align-items-center gap-2">
                      <i class="bi bi-hdd-network"></i> Режим сервера (Server Mode)
                    </div>
                    <div class="card-body p-3">
                      <div class="row g-3">
                        <div class="col-md-6">
                          <label class="form-label small fw-semibold text-light mb-1">Режим работы сервера:</label>
                          <select class="form-select form-select-sm bg-dark text-white border-secondary" id="app-cfg-server-mode">
                            <option value="dedicated">Dedicated (Отдельный процесс / порт)</option>
                            <option value="shared">Shared (Маршрутизация через главный сервер :8000)</option>
                          </select>
                          <div class="form-text small text-muted" id="app-cfg-server-mode-hint">
                            В режиме dedicated run.ps1 запускает отдельный процесс микросервиса.
                          </div>
                        </div>
                        <div class="col-md-6">
                          <label class="form-label small fw-semibold text-light mb-1">Порт (Port):</label>
                          <input type="number" class="form-control form-control-sm bg-dark text-white border-secondary font-monospace" id="app-cfg-server-port" placeholder="8100">
                        </div>
                        <div class="col-md-6">
                          <label class="form-label small fw-semibold text-light mb-1">Хост (Host):</label>
                          <input type="text" class="form-control form-control-sm bg-dark text-white border-secondary font-monospace" id="app-cfg-server-host" placeholder="127.0.0.1">
                        </div>
                        <div class="col-md-6">
                          <label class="form-label small fw-semibold text-light mb-1">Воркеры (Workers):</label>
                          <input type="number" class="form-control form-control-sm bg-dark text-white border-secondary font-monospace" id="app-cfg-server-workers" placeholder="1" min="1" max="16">
                        </div>
                        <div class="col-12">
                          <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="app-cfg-server-ssl">
                            <label class="form-check-label small text-light" for="app-cfg-server-ssl">Использовать SSL (HTTPS)</label>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Dynamic App Extra Params Card -->
                  <div class="card border-secondary" style="background: #1e293b;" id="app-cfg-extra-card">
                    <div class="card-header border-secondary py-2 small fw-bold text-info d-flex align-items-center gap-2">
                      <i class="bi bi-gear-wide-connected"></i> Параметры приложения
                    </div>
                    <div class="card-body p-3" id="app-cfg-extra-body">
                      <!-- Populated dynamically based on app properties -->
                    </div>
                  </div>
                </div>

                <!-- Raw JSON Pane -->
                <div class="tab-pane fade" id="app-config-tab-raw">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="small text-muted font-monospace" id="app-cfg-file-path">config.json</span>
                    <button class="btn btn-sm btn-outline-secondary py-0 px-2" id="app-cfg-btn-format">
                      <i class="bi bi-magic"></i> Форматировать
                    </button>
                  </div>
                  <textarea class="form-control font-monospace bg-dark text-white border-secondary" id="app-cfg-raw-json" rows="14" style="font-size: 0.82rem; line-height: 1.4; tab-size: 2;"></textarea>
                </div>
              </div>
            </div>
            <div class="modal-footer border-secondary justify-content-between" style="background: #1e293b;">
              <button type="button" class="btn btn-sm btn-outline-secondary rounded-pill px-3" id="app-cfg-btn-reload">
                <i class="bi bi-arrow-clockwise me-1"></i> Сбросить
              </button>
              <div class="d-flex gap-2">
                <button type="button" class="btn btn-sm btn-secondary rounded-pill px-3" data-bs-dismiss="modal">Отмена</button>
                <button type="button" class="btn btn-sm btn-primary rounded-pill px-4 fw-semibold" id="app-cfg-btn-save">
                  <i class="bi bi-save me-1"></i> Сохранить
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modalEl);

      // Event handlers
      document.getElementById('app-cfg-btn-save')?.addEventListener('click', onSaveConfig);
      document.getElementById('app-cfg-btn-reload')?.addEventListener('click', onReloadConfig);
      document.getElementById('app-cfg-btn-format')?.addEventListener('click', () => {
        const rawEl = document.getElementById('app-cfg-raw-json');
        try {
          const parsed = JSON.parse(rawEl.value);
          rawEl.value = JSON.stringify(parsed, null, 2);
        } catch (e) {
          showModalAlert(`Ошибка JSON: ${e.message}`, 'danger');
        }
      });

      // Synchronize visual form to raw JSON on tab switch
      document.getElementById('app-config-tab-raw-btn')?.addEventListener('click', () => {
        syncFormToRawJson();
      });
      document.getElementById('app-config-tab-visual-btn')?.addEventListener('click', () => {
        syncRawJsonToForm();
      });
    }
  }

  function showModalAlert(message, type = 'info') {
    const el = document.getElementById('app-config-alert');
    if (!el) return;
    el.className = `alert alert-${type} py-2 px-3 small`;
    el.innerHTML = message;
    el.classList.remove('d-none');
    if (type === 'success') {
      setTimeout(() => el.classList.add('d-none'), 3500);
    }
  }

  function populateVisualForm(config) {
    if (!config) return;
    
    // Server section
    let serverMode = 'dedicated';
    let host = '127.0.0.1';
    let port = 8100;
    let workers = 1;
    let ssl = false;

    if (typeof config.server === 'string') {
      serverMode = config.server.toLowerCase();
    } else if (config.server && typeof config.server === 'object') {
      if (typeof config.server.dedicated === 'boolean') {
        serverMode = config.server.dedicated ? 'dedicated' : 'shared';
      } else if (config.server.dedicated !== undefined) {
        serverMode = String(config.server.dedicated).toLowerCase() === 'true' ? 'dedicated' : 'shared';
      } else {
        serverMode = config.server.mode || config.server.type || 'dedicated';
      }
      host = config.server.host || '127.0.0.1';
      port = config.server.port || port;
      workers = config.server.workers || 1;
      ssl = !!config.server.use_ssl;
    }

    const modeSelect = document.getElementById('app-cfg-server-mode');
    if (modeSelect) modeSelect.value = serverMode;
    const portInput = document.getElementById('app-cfg-server-port');
    if (portInput) portInput.value = port;
    const hostInput = document.getElementById('app-cfg-server-host');
    if (hostInput) hostInput.value = host;
    const workersInput = document.getElementById('app-cfg-server-workers');
    if (workersInput) workersInput.value = workers;
    const sslCheck = document.getElementById('app-cfg-server-ssl');
    if (sslCheck) sslCheck.checked = ssl;

    // Extra properties
    const extraBody = document.getElementById('app-cfg-extra-body');
    if (extraBody) {
      let fieldsHtml = '<div class="row g-2">';
      let hasExtra = false;

      for (const [key, val] of Object.entries(config)) {
        if (key === 'server' || key === 'cors' || key === 'server_cors_origins' || key === 'server_cors_allow_credentials') {
          continue;
        }
        hasExtra = true;
        if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
          fieldsHtml += `<div class="col-12"><h6 class="text-warning small fw-bold mt-2 mb-1">${key}:</h6></div>`;
          for (const [subK, subV] of Object.entries(val)) {
            fieldsHtml += `
              <div class="col-md-6">
                <label class="form-label small text-muted mb-0">${key}.${subK}:</label>
                <input type="text" class="form-control form-control-sm bg-dark text-white border-secondary font-monospace app-cfg-extra-input" data-path="${key}.${subK}" value="${subV !== undefined ? String(subV) : ''}">
              </div>
            `;
          }
        } else {
          fieldsHtml += `
            <div class="col-md-6">
              <label class="form-label small text-muted mb-0">${key}:</label>
              <input type="text" class="form-control form-control-sm bg-dark text-white border-secondary font-monospace app-cfg-extra-input" data-path="${key}" value="${val !== undefined ? String(val) : ''}">
            </div>
          `;
        }
      }

      fieldsHtml += '</div>';
      extraBody.innerHTML = hasExtra ? fieldsHtml : '<div class="text-muted small">Дополнительные параметры отсутствуют.</div>';
    }

    // Raw JSON
    const rawEl = document.getElementById('app-cfg-raw-json');
    if (rawEl) {
      rawEl.value = JSON.stringify(config, null, 2);
    }
  }

  function syncFormToRawJson() {
    try {
      const rawEl = document.getElementById('app-cfg-raw-json');
      let currentObj = {};
      try {
        currentObj = JSON.parse(rawEl.value || '{}');
      } catch {}

      const serverMode = document.getElementById('app-cfg-server-mode')?.value || 'dedicated';
      const isDedicated = serverMode === 'dedicated';
      const port = parseInt(document.getElementById('app-cfg-server-port')?.value || '8100', 10);
      const host = document.getElementById('app-cfg-server-host')?.value || '127.0.0.1';
      const workers = parseInt(document.getElementById('app-cfg-server-workers')?.value || '1', 10);
      const ssl = !!document.getElementById('app-cfg-server-ssl')?.checked;

      if (!currentObj.server || typeof currentObj.server !== 'object') {
        currentObj.server = {};
      }
      currentObj.server.dedicated = isDedicated;
      if (currentObj.server.mode !== undefined) {
        delete currentObj.server.mode;
      }
      currentObj.server.host = host;
      currentObj.server.port = port;
      currentObj.server.use_ssl = ssl;
      currentObj.server.workers = workers;

      // Sync extra inputs
      document.querySelectorAll('.app-cfg-extra-input').forEach((input) => {
        const path = input.getAttribute('data-path');
        const val = input.value;
        if (!path) return;
        
        let parsedVal = val;
        if (val === 'true') parsedVal = true;
        else if (val === 'false') parsedVal = false;
        else if (/^\d+$/.test(val)) parsedVal = parseInt(val, 10);
        else if (/^\d+\.\d+$/.test(val)) parsedVal = parseFloat(val);

        const parts = path.split('.');
        if (parts.length === 1) {
          currentObj[parts[0]] = parsedVal;
        } else if (parts.length === 2) {
          if (!currentObj[parts[0]] || typeof currentObj[parts[0]] !== 'object') {
            currentObj[parts[0]] = {};
          }
          currentObj[parts[0]][parts[1]] = parsedVal;
        }
      });

      rawEl.value = JSON.stringify(currentObj, null, 2);
      activeConfig = currentObj;
    } catch (e) {
      console.error('[AppConfigEditor] Form sync error:', e);
    }
  }

  function syncRawJsonToForm() {
    try {
      const rawEl = document.getElementById('app-cfg-raw-json');
      const parsed = JSON.parse(rawEl.value || '{}');
      activeConfig = parsed;
      populateVisualForm(parsed);
    } catch (e) {
      showModalAlert(`Ошибка парсинга JSON: ${e.message}`, 'danger');
    }
  }

  async function onSaveConfig() {
    try {
      syncFormToRawJson();
      const rawEl = document.getElementById('app-cfg-raw-json');
      const parsed = JSON.parse(rawEl.value);
      
      const res = await saveAppConfig(activeAppName, parsed);
      showModalAlert(`✓ ${res.message || 'Конфигурация успешно сохранена!'}`, 'success');
      activeConfig = parsed;
      
      if (typeof window.showNotification === 'function') {
        window.showNotification(`Конфигурация ${activeAppName} сохранена`, 'success');
      }
    } catch (e) {
      showModalAlert(`Ошибка при сохранении: ${e.message}`, 'danger');
    }
  }

  async function onReloadConfig() {
    try {
      const data = await fetchAppConfig(activeAppName);
      activeConfig = data.config;
      populateVisualForm(activeConfig);
      showModalAlert('Конфигурация перезагружена с диска', 'info');
    } catch (e) {
      showModalAlert(`Ошибка загрузки: ${e.message}`, 'danger');
    }
  }

  /**
   * Open the configuration modal for an app
   * @param {string} appName e.g. 'trading_terminal', 'network_terminal', etc.
   * @param {string} displayName e.g. 'Exchange Trading Terminal'
   */
  window.openAppConfigModal = async function(appName, displayName = '') {
    ensureModalExists();
    activeAppName = appName;

    const titleEl = document.getElementById('app-config-modal-title');
    if (titleEl) {
      titleEl.innerHTML = `<i class="bi bi-sliders"></i> ${displayName || appName} — config.json`;
    }

    const pathEl = document.getElementById('app-cfg-file-path');
    if (pathEl) {
      pathEl.textContent = `apps/${appName}/config.json`;
    }

    const alertEl = document.getElementById('app-config-alert');
    if (alertEl) alertEl.classList.add('d-none');

    // Show modal
    const modalEl = document.getElementById('app-config-modal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();

    try {
      const data = await fetchAppConfig(appName);
      activeConfig = data.config;
      populateVisualForm(activeConfig);
    } catch (e) {
      showModalAlert(`Не удалось загрузить конфигурацию: ${e.message}`, 'danger');
    }
  };
})();
