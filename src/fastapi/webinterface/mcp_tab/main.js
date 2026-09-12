// MCP Servers Tab Management Logic for AI Breadboard Admin Interface

class McpTabManager {
  constructor() {
    this.servers = [];
    this.filteredServers = [];
    this.viewMode = 'cards'; // 'cards' | 'table'
    this.searchQuery = '';
    this.activeFilter = 'all'; // 'all' | 'enabled' | 'disabled' | 'stdio' | 'sse'
    this.isInitialized = false;
  }

  async init() {
    if (this.isInitialized) {
      await this.refresh();
      return;
    }
    this.bindEvents();
    this.isInitialized = true;
    await this.refresh();
  }

  bindEvents() {
    const searchInput = document.getElementById('mcp-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.trim().toLowerCase();
        this.applyFilters();
      });
    }

    const idInput = document.getElementById('mcp-server-id');
    if (idInput) {
      idInput.addEventListener('input', (e) => {
        const val = e.target.value;
        const normalized = val.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
        if (val !== normalized) {
          e.target.value = normalized;
        }
      });
    }
  }

  async apiFetch(endpoint, options = {}) {
    let url = endpoint;
    let res = await fetch(url, options);
    if (!res.ok && url.startsWith('/api/admin/mcp')) {
      const fallbackUrl = url.replace('/api/admin/mcp', '/api/mcp');
      const fallbackRes = await fetch(fallbackUrl, options);
      if (fallbackRes.ok) {
        return fallbackRes;
      }
    }
    return res;
  }

  async refresh() {
    this.showLoading(true);
    try {
      const res = await this.apiFetch('/api/admin/mcp/servers');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();
      this.servers = data.servers || [];
      this.updateStats();
      this.applyFilters();
    } catch (err) {
      console.error('[McpTab] Error fetching MCP servers:', err);
      this.renderError(err.message);
    } finally {
      this.showLoading(false);
    }
  }

  updateStats() {
    const total = this.servers.length;
    const active = this.servers.filter(s => s.enabled !== false).length;
    const stdio = this.servers.filter(s => (s.transport || 'stdio') === 'stdio').length;
    const network = this.servers.filter(s => ['sse', 'streamable_http', 'http'].includes(s.transport)).length;

    const badge = document.getElementById('mcp-total-badge');
    if (badge) badge.textContent = total;

    const elTotal = document.getElementById('stat-total-mcp');
    if (elTotal) elTotal.textContent = total;

    const elActive = document.getElementById('stat-active-mcp');
    if (elActive) elActive.textContent = active;

    const elStdio = document.getElementById('stat-stdio-mcp');
    if (elStdio) elStdio.textContent = stdio;

    const elNetwork = document.getElementById('stat-network-mcp');
    if (elNetwork) elNetwork.textContent = network;
  }

  applyFilters() {
    const filterSelect = document.getElementById('mcp-filter-select');
    this.activeFilter = filterSelect ? filterSelect.value : 'all';

    this.filteredServers = this.servers.filter(s => {
      // Search filter
      if (this.searchQuery) {
        const idMatch = (s.id || '').toLowerCase().includes(this.searchQuery);
        const nameMatch = (s.name || '').toLowerCase().includes(this.searchQuery);
        const descMatch = (s.description || '').toLowerCase().includes(this.searchQuery);
        const cmdMatch = (s.command || '').toLowerCase().includes(this.searchQuery);
        const urlMatch = (s.url || '').toLowerCase().includes(this.searchQuery);
        if (!idMatch && !nameMatch && !descMatch && !cmdMatch && !urlMatch) {
          return false;
        }
      }

      // Category filter
      if (this.activeFilter === 'enabled') {
        return s.enabled !== false;
      } else if (this.activeFilter === 'disabled') {
        return s.enabled === false;
      } else if (this.activeFilter === 'stdio') {
        return (s.transport || 'stdio') === 'stdio';
      } else if (this.activeFilter === 'sse') {
        return ['sse', 'streamable_http', 'http'].includes(s.transport);
      }

      return true;
    });

    this.render();
  }

  clearSearch() {
    const searchInput = document.getElementById('mcp-search-input');
    if (searchInput) searchInput.value = '';
    this.searchQuery = '';
    this.applyFilters();
  }

  setViewMode(mode) {
    this.viewMode = mode;
    const btnCards = document.getElementById('btn-mcp-view-cards');
    const btnTable = document.getElementById('btn-mcp-view-table');
    const cardsContainer = document.getElementById('mcp-cards-container');
    const tableContainer = document.getElementById('mcp-table-container');

    if (mode === 'cards') {
      btnCards?.classList.add('active');
      btnTable?.classList.remove('active');
      cardsContainer?.classList.remove('d-none');
      tableContainer?.classList.add('d-none');
    } else {
      btnCards?.classList.remove('active');
      btnTable?.classList.add('active');
      cardsContainer?.classList.add('d-none');
      tableContainer?.classList.remove('d-none');
    }
  }

  showLoading(show) {
    const loadingEl = document.getElementById('mcp-loading');
    const cardsEl = document.getElementById('mcp-cards-container');
    const tableEl = document.getElementById('mcp-table-container');
    const emptyEl = document.getElementById('mcp-empty');

    if (show) {
      loadingEl?.classList.remove('d-none');
      cardsEl?.classList.add('d-none');
      tableEl?.classList.add('d-none');
      emptyEl?.classList.add('d-none');
    } else {
      loadingEl?.classList.add('d-none');
      this.setViewMode(this.viewMode);
    }
  }

  render() {
    const emptyEl = document.getElementById('mcp-empty');
    const cardsContainer = document.getElementById('mcp-cards-container');
    const tableBody = document.getElementById('mcp-table-body');

    if (this.filteredServers.length === 0) {
      if (emptyEl) emptyEl.classList.remove('d-none');
      if (cardsContainer) cardsContainer.innerHTML = '';
      if (tableBody) tableBody.innerHTML = '';
      return;
    }

    if (emptyEl) emptyEl.classList.add('d-none');

    if (cardsContainer) {
      cardsContainer.innerHTML = this.filteredServers.map(s => this.renderServerCard(s)).join('');
    }

    if (tableBody) {
      tableBody.innerHTML = this.filteredServers.map(s => this.renderServerTableRow(s)).join('');
    }
  }

  renderServerCard(server) {
    const isEnabled = server.enabled !== false;
    const isStdio = (server.transport || 'stdio') === 'stdio';
    const statusBadge = isEnabled
      ? '<span class="badge bg-success-subtle text-success border border-success-subtle"><i class="bi bi-check-circle-fill"></i> Активен</span>'
      : '<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle"><i class="bi bi-dash-circle"></i> Отключен</span>';

    const transportBadge = isStdio
      ? '<span class="badge bg-info-subtle text-info border border-info-subtle"><i class="bi bi-terminal"></i> stdio</span>'
      : `<span class="badge bg-warning-subtle text-warning border border-warning-subtle"><i class="bi bi-broadcast"></i> ${this.escapeHtml(server.transport)}</span>`;

    const commandOrUrl = isStdio
      ? `<code>${this.escapeHtml(server.command || '')} ${(server.args || []).join(' ')}</code>`
      : `<a href="${this.escapeHtml(server.url || '#')}" target="_blank" class="text-info text-truncate d-inline-block" style="max-width: 250px;">${this.escapeHtml(server.url || '')}</a>`;

    return `
      <div class="col-12 col-md-6 col-xl-4">
        <div class="card bg-dark border-secondary h-100 shadow-sm d-flex flex-column">
          <div class="card-header border-secondary d-flex align-items-center justify-content-between p-3">
            <div class="d-flex align-items-center gap-2 text-truncate">
              <div class="p-2 bg-black rounded border border-secondary text-primary">
                <i class="bi ${isStdio ? 'bi-cpu' : 'bi-globe2'}"></i>
              </div>
              <div class="text-truncate">
                <h6 class="mb-0 text-white text-truncate fw-bold">${this.escapeHtml(server.name || server.id)}</h6>
                <small class="text-muted font-monospace">${this.escapeHtml(server.id)}</small>
              </div>
            </div>
            <div class="d-flex align-items-center gap-1">
              ${transportBadge}
              ${statusBadge}
            </div>
          </div>
          <div class="card-body p-3 flex-grow-1">
            <p class="card-text small text-secondary mb-3" style="min-height: 38px;">
              ${this.escapeHtml(server.description || 'Описание отсутствует.')}
            </p>
            <div class="p-2 bg-black rounded border border-secondary mb-2 small">
              <div class="text-muted small mb-1">${isStdio ? 'Исполняемая команда:' : 'Сетевой эндпоинт:'}</div>
              <div class="text-truncate">${commandOrUrl}</div>
            </div>
          </div>
          <div class="card-footer border-secondary p-2 d-flex align-items-center justify-content-between gap-1 bg-black bg-opacity-25">
            <button class="btn btn-sm btn-outline-info d-flex align-items-center gap-1" onclick="window.mcpTab?.testServer('${this.escapeHtml(server.id)}')">
              <i class="bi bi-play-circle"></i> Тест & Tools
            </button>
            <div class="d-flex align-items-center gap-1">
              <button class="btn btn-sm ${isEnabled ? 'btn-outline-warning' : 'btn-outline-success'}" title="${isEnabled ? 'Отключить' : 'Включить'}" onclick="window.mcpTab?.toggleServer('${this.escapeHtml(server.id)}')">
                <i class="bi ${isEnabled ? 'bi-pause-fill' : 'bi-play-fill'}"></i>
              </button>
              <button class="btn btn-sm btn-outline-primary" title="Редактировать" onclick="window.mcpTab?.openEditModal('${this.escapeHtml(server.id)}')">
                <i class="bi bi-pencil-fill"></i>
              </button>
              <button class="btn btn-sm btn-outline-danger" title="Удалить" onclick="window.mcpTab?.deleteServer('${this.escapeHtml(server.id)}')">
                <i class="bi bi-trash-fill"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  renderServerTableRow(server) {
    const isEnabled = server.enabled !== false;
    const isStdio = (server.transport || 'stdio') === 'stdio';
    const statusDot = isEnabled
      ? '<span class="badge bg-success rounded-pill" title="Активен">ON</span>'
      : '<span class="badge bg-secondary rounded-pill" title="Отключен">OFF</span>';

    const transportBadge = isStdio
      ? '<span class="badge bg-info-subtle text-info border border-info-subtle">stdio</span>'
      : `<span class="badge bg-warning-subtle text-warning border border-warning-subtle">${this.escapeHtml(server.transport)}</span>`;

    const cmdOrUrl = isStdio
      ? `<code>${this.escapeHtml(server.command || '')} ${(server.args || []).join(' ')}</code>`
      : `<a href="${this.escapeHtml(server.url || '#')}" target="_blank" class="text-info">${this.escapeHtml(server.url || '')}</a>`;

    return `
      <tr>
        <td class="text-center">${statusDot}</td>
        <td>
          <div class="fw-bold text-white">${this.escapeHtml(server.name || server.id)}</div>
          <div class="small font-monospace text-muted">${this.escapeHtml(server.id)}</div>
        </td>
        <td>${transportBadge}</td>
        <td class="small text-truncate" style="max-width: 250px;">${cmdOrUrl}</td>
        <td class="small text-muted text-truncate" style="max-width: 200px;">${this.escapeHtml(server.description || '—')}</td>
        <td class="text-end">
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-info" title="Тест соединения" onclick="window.mcpTab?.testServer('${this.escapeHtml(server.id)}')">
              <i class="bi bi-play-circle"></i>
            </button>
            <button class="btn ${isEnabled ? 'btn-outline-warning' : 'btn-outline-success'}" title="${isEnabled ? 'Отключить' : 'Включить'}" onclick="window.mcpTab?.toggleServer('${this.escapeHtml(server.id)}')">
              <i class="bi ${isEnabled ? 'bi-pause-fill' : 'bi-play-fill'}"></i>
            </button>
            <button class="btn btn-outline-primary" title="Редактировать" onclick="window.mcpTab?.openEditModal('${this.escapeHtml(server.id)}')">
              <i class="bi bi-pencil-fill"></i>
            </button>
            <button class="btn btn-outline-danger" title="Удалить" onclick="window.mcpTab?.deleteServer('${this.escapeHtml(server.id)}')">
              <i class="bi bi-trash-fill"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }

  onTransportChange() {
    const transport = document.getElementById('mcp-server-transport')?.value || 'stdio';
    const stdioContainer = document.getElementById('mcp-stdio-container');
    const networkContainer = document.getElementById('mcp-network-container');

    if (transport === 'stdio') {
      stdioContainer?.classList.remove('d-none');
      networkContainer?.classList.add('d-none');
    } else {
      stdioContainer?.classList.add('d-none');
      networkContainer?.classList.remove('d-none');
    }
  }

  applyPreset(presetKey) {
    const presets = {
      playwright: {
        id: 'playwright',
        name: 'Playwright Browser MCP',
        description: 'Управление веб-браузером, навигация, клики, скриншоты и парсинг страниц через Playwright.',
        transport: 'stdio',
        command: 'npx',
        args: '@playwright/mcp@latest',
        env: ''
      },
      filesystem: {
        id: 'filesystem',
        name: 'Filesystem MCP',
        description: 'Безопасное чтение, запись и навигация по каталогам и файлам на диске.',
        transport: 'stdio',
        command: 'npx',
        args: '-y @modelcontextprotocol/server-filesystem ./data',
        env: ''
      },
      memory: {
        id: 'memory',
        name: 'Knowledge Graph Memory MCP',
        description: 'Хранилище графа знаний и ассоциативная память для ИИ-агентов.',
        transport: 'stdio',
        command: 'npx',
        args: '-y @modelcontextprotocol/server-memory',
        env: ''
      },
      sqlite: {
        id: 'sqlite',
        name: 'SQLite Database MCP',
        description: 'Выполнение запросов, исследование схемы и инспекция таблиц SQLite базы данных.',
        transport: 'stdio',
        command: 'uvx',
        args: 'mcp-server-sqlite --db-path ./data/database.sqlite',
        env: ''
      },
      fetch: {
        id: 'fetch',
        name: 'Fetch / Web Request MCP',
        description: 'Преобразование HTML веб-страниц в Markdown и выполнение HTTP-запросов.',
        transport: 'stdio',
        command: 'uvx',
        args: 'mcp-server-fetch',
        env: ''
      },
      sse: {
        id: 'remote_mcp',
        name: 'Remote SSE MCP Server',
        description: 'Удаленный MCP-сервер, доступный по протоколу Server-Sent Events (SSE).',
        transport: 'sse',
        url: 'http://localhost:8080/sse'
      }
    };

    const p = presets[presetKey];
    if (!p) return;

    const idEl = document.getElementById('mcp-server-id');
    const nameEl = document.getElementById('mcp-server-name');
    const descEl = document.getElementById('mcp-server-desc');
    const transportEl = document.getElementById('mcp-server-transport');
    const cmdEl = document.getElementById('mcp-server-command');
    const argsEl = document.getElementById('mcp-server-args');
    const urlEl = document.getElementById('mcp-server-url');
    const envEl = document.getElementById('mcp-server-env');

    if (idEl && document.getElementById('mcp-form-mode')?.value === 'create') idEl.value = p.id;
    if (nameEl) nameEl.value = p.name || '';
    if (descEl) descEl.value = p.description || '';
    if (transportEl) transportEl.value = p.transport || 'stdio';
    if (cmdEl) cmdEl.value = p.command || '';
    if (argsEl) argsEl.value = p.args || '';
    if (urlEl) urlEl.value = p.url || '';
    if (envEl) envEl.value = p.env || '';

    this.onTransportChange();
  }

  openCreateModal() {
    const form = document.getElementById('mcp-server-form');
    if (form) form.reset();

    const titleText = document.getElementById('mcp-modal-title-text');
    if (titleText) titleText.textContent = 'Добавление нового MCP сервера';

    const modeInput = document.getElementById('mcp-form-mode');
    if (modeInput) modeInput.value = 'create';

    const idInput = document.getElementById('mcp-server-id');
    if (idInput) {
      idInput.removeAttribute('readonly');
      idInput.classList.remove('bg-secondary');
    }

    const presetContainer = document.getElementById('mcp-preset-container');
    if (presetContainer) presetContainer.classList.remove('d-none');

    const enabledCheckbox = document.getElementById('mcp-server-enabled');
    if (enabledCheckbox) enabledCheckbox.checked = true;

    this.applyPreset('playwright');
  }

  openEditModal(serverId) {
    const server = this.servers.find(s => s.id === serverId);
    if (!server) return;

    const titleText = document.getElementById('mcp-modal-title-text');
    if (titleText) titleText.textContent = `Редактирование: ${server.name || server.id}`;

    const modeInput = document.getElementById('mcp-form-mode');
    if (modeInput) modeInput.value = 'edit';

    const presetContainer = document.getElementById('mcp-preset-container');
    if (presetContainer) presetContainer.classList.add('d-none');

    const idInput = document.getElementById('mcp-server-id');
    if (idInput) {
      idInput.value = server.id;
      idInput.setAttribute('readonly', 'true');
      idInput.classList.add('bg-secondary');
    }

    const nameInput = document.getElementById('mcp-server-name');
    if (nameInput) nameInput.value = server.name || '';

    const descInput = document.getElementById('mcp-server-desc');
    if (descInput) descInput.value = server.description || '';

    const transportInput = document.getElementById('mcp-server-transport');
    if (transportInput) transportInput.value = server.transport || 'stdio';

    const cmdInput = document.getElementById('mcp-server-command');
    if (cmdInput) cmdInput.value = server.command || '';

    const argsInput = document.getElementById('mcp-server-args');
    if (argsInput) {
      argsInput.value = Array.isArray(server.args) ? server.args.join(' ') : (server.args || '');
    }

    const urlInput = document.getElementById('mcp-server-url');
    if (urlInput) urlInput.value = server.url || '';

    const envInput = document.getElementById('mcp-server-env');
    if (envInput) {
      envInput.value = server.env ? JSON.stringify(server.env, null, 2) : '';
    }

    const enabledCheckbox = document.getElementById('mcp-server-enabled');
    if (enabledCheckbox) enabledCheckbox.checked = server.enabled !== false;

    this.onTransportChange();

    const modalEl = document.getElementById('mcpServerModal');
    if (modalEl && window.bootstrap) {
      const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
      modal.show();
    }
  }

  async saveServer(event) {
    if (event) event.preventDefault();

    const mode = document.getElementById('mcp-form-mode')?.value || 'create';
    const serverId = document.getElementById('mcp-server-id')?.value.trim();
    const name = document.getElementById('mcp-server-name')?.value.trim();
    const description = document.getElementById('mcp-server-desc')?.value.trim();
    const transport = document.getElementById('mcp-server-transport')?.value || 'stdio';
    const enabled = document.getElementById('mcp-server-enabled')?.checked ?? true;
    const command = document.getElementById('mcp-server-command')?.value.trim();
    const argsRaw = document.getElementById('mcp-server-args')?.value.trim();
    const url = document.getElementById('mcp-server-url')?.value.trim();
    const envRaw = document.getElementById('mcp-server-env')?.value.trim();

    if (!serverId) {
      alert('Укажите ID сервера');
      return;
    }

    // Parse args
    let args = [];
    if (argsRaw) {
      if (argsRaw.startsWith('[') && argsRaw.endsWith(']')) {
        try {
          args = JSON.parse(argsRaw);
        } catch {
          args = argsRaw.split(/\s+/).filter(Boolean);
        }
      } else {
        args = argsRaw.split(/\s+/).filter(Boolean);
      }
    }

    // Parse env
    let env = {};
    if (envRaw) {
      try {
        env = JSON.parse(envRaw);
      } catch (err) {
        alert('Ошибка формата JSON в переменных окружения: ' + err.message);
        return;
      }
    }

    const payload = {
      id: serverId,
      name: name || serverId,
      description: description,
      transport: transport,
      enabled: enabled,
      command: command,
      args: args,
      url: url,
      env: env
    };

    const saveBtn = document.getElementById('mcp-btn-save-server');
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Сохранение...';
    }

    try {
      const endpoint = mode === 'create'
        ? '/api/admin/mcp/servers'
        : `/api/admin/mcp/servers/${encodeURIComponent(serverId)}`;

      const method = mode === 'create' ? 'POST' : 'PUT';

      const res = await this.apiFetch(endpoint, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      // Close modal
      const modalEl = document.getElementById('mcpServerModal');
      if (modalEl && window.bootstrap) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal?.hide();
      }

      await this.refresh();
    } catch (err) {
      alert(`Ошибка сохранения MCP сервера: ${err.message}`);
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = 'Сохранить';
      }
    }
  }

  async toggleServer(serverId) {
    try {
      const res = await this.apiFetch(`/api/admin/mcp/servers/${encodeURIComponent(serverId)}/toggle`, {
        method: 'POST'
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      await this.refresh();
    } catch (err) {
      alert(`Ошибка переключения статуса сервера: ${err.message}`);
    }
  }

  async deleteServer(serverId) {
    if (!confirm(`Вы уверены, что хотите удалить MCP сервер "${serverId}"?`)) {
      return;
    }

    try {
      const res = await this.apiFetch(`/api/admin/mcp/servers/${encodeURIComponent(serverId)}`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      await this.refresh();
    } catch (err) {
      alert(`Ошибка удаления сервера: ${err.message}`);
    }
  }

  async testServer(serverId) {
    const server = this.servers.find(s => s.id === serverId);
    const serverName = server?.name || serverId;

    const nameEl = document.getElementById('mcp-test-server-name');
    if (nameEl) nameEl.textContent = serverName;

    const statusBox = document.getElementById('mcp-test-status-box');
    const statusText = document.getElementById('mcp-test-status-text');
    const spinner = document.getElementById('mcp-test-spinner');
    const latencyBadge = document.getElementById('mcp-test-latency-badge');
    const countBadge = document.getElementById('mcp-test-tools-count');
    const toolsList = document.getElementById('mcp-test-tools-list');

    if (spinner) spinner.classList.remove('d-none');
    if (statusBox) {
      statusBox.className = 'p-3 mb-3 rounded border border-info bg-black text-info d-flex align-items-center justify-content-between';
    }
    if (statusText) statusText.textContent = 'Подключение к процессу / эндпоинту и опрос инструментов...';
    if (latencyBadge) latencyBadge.textContent = '...';
    if (countBadge) countBadge.textContent = '0';
    if (toolsList) toolsList.innerHTML = '<div class="text-muted text-center py-3">Опрос инструментов...</div>';

    const modalEl = document.getElementById('mcpTestModal');
    if (modalEl && window.bootstrap) {
      const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
      modal.show();
    }

    try {
      const res = await this.apiFetch(`/api/admin/mcp/servers/${encodeURIComponent(serverId)}/test`, {
        method: 'POST'
      });
      const data = await res.json();

      if (spinner) spinner.classList.add('d-none');
      if (latencyBadge) latencyBadge.textContent = `${data.latency_ms || 0} ms`;

      if (data.status === 'ok') {
        if (statusBox) {
          statusBox.className = 'p-3 mb-3 rounded border border-success bg-black text-success d-flex align-items-center justify-content-between';
        }
        if (statusText) statusText.innerHTML = `✅ <strong>Успешно:</strong> ${this.escapeHtml(data.message)}`;
        if (countBadge) countBadge.textContent = data.tools_count || (data.tools || []).length;
        this.renderDiscoveredTools(data.tools || [], toolsList);
      } else {
        if (statusBox) {
          statusBox.className = 'p-3 mb-3 rounded border border-danger bg-black text-danger d-flex align-items-center justify-content-between';
        }
        if (statusText) statusText.innerHTML = `❌ <strong>Ошибка:</strong> ${this.escapeHtml(data.message || 'Не удалось подключиться к серверу')}`;
        if (toolsList) {
          toolsList.innerHTML = `<div class="alert alert-danger bg-dark border-danger text-light small mb-0">${this.escapeHtml(data.message || 'Ошибка соединения')}</div>`;
        }
      }
    } catch (err) {
      if (spinner) spinner.classList.add('d-none');
      if (statusBox) {
        statusBox.className = 'p-3 mb-3 rounded border border-danger bg-black text-danger d-flex align-items-center justify-content-between';
      }
      if (statusText) statusText.innerHTML = `❌ <strong>Сетевая ошибка:</strong> ${this.escapeHtml(err.message)}`;
    }
  }

  async testCurrentForm() {
    const serverId = document.getElementById('mcp-server-id')?.value.trim() || 'test_server';
    const transport = document.getElementById('mcp-server-transport')?.value || 'stdio';
    const command = document.getElementById('mcp-server-command')?.value.trim();
    const argsRaw = document.getElementById('mcp-server-args')?.value.trim();
    const url = document.getElementById('mcp-server-url')?.value.trim();
    const envRaw = document.getElementById('mcp-server-env')?.value.trim();

    let args = [];
    if (argsRaw) {
      if (argsRaw.startsWith('[') && argsRaw.endsWith(']')) {
        try { args = JSON.parse(argsRaw); } catch { args = argsRaw.split(/\s+/).filter(Boolean); }
      } else {
        args = argsRaw.split(/\s+/).filter(Boolean);
      }
    }

    let env = {};
    if (envRaw) {
      try { env = JSON.parse(envRaw); } catch (e) { alert('Неверный формат JSON в env'); return; }
    }

    const testBtn = document.getElementById('btn-test-modal-server');
    if (testBtn) {
      testBtn.disabled = true;
      testBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Тест...';
    }

    try {
      const res = await this.apiFetch('/api/admin/mcp/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: serverId,
          transport: transport,
          command: command,
          args: args,
          url: url,
          env: env
        })
      });
      const data = await res.json();
      if (data.status === 'ok') {
        alert(`✅ Подключение успешно! (${data.latency_ms} ms)\nНайдено инструментов: ${data.tools_count}`);
      } else {
        alert(`❌ Ошибка проверки подключения:\n${data.message}`);
      }
    } catch (err) {
      alert(`❌ Ошибка запроса: ${err.message}`);
    } finally {
      if (testBtn) {
        testBtn.disabled = false;
        testBtn.innerHTML = '<i class="bi bi-play-circle"></i> Проверить подключение';
      }
    }
  }

  async openAllToolsModal() {
    const modalEl = document.getElementById('mcpAllToolsModal');
    if (modalEl && window.bootstrap) {
      const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
      modal.show();
    }

    const loadingEl = document.getElementById('mcp-all-tools-loading');
    const emptyEl = document.getElementById('mcp-all-tools-empty');
    const container = document.getElementById('mcp-all-tools-container');

    loadingEl?.classList.remove('d-none');
    emptyEl?.classList.add('d-none');
    container?.classList.add('d-none');

    try {
      const res = await this.apiFetch('/api/admin/mcp/tools');
      const data = await res.json();
      loadingEl?.classList.add('d-none');

      const tools = data.tools || [];
      if (tools.length === 0) {
        emptyEl?.classList.remove('d-none');
        return;
      }

      container?.classList.remove('d-none');
      if (container) {
        container.innerHTML = tools.map(t => `
          <div class="col-12 col-lg-6">
            <div class="p-3 bg-black rounded border border-secondary h-100 d-flex flex-column">
              <div class="d-flex align-items-center justify-content-between mb-2">
                <strong class="text-info font-monospace d-flex align-items-center gap-1">
                  <i class="bi bi-wrench"></i> ${this.escapeHtml(t.name)}
                </strong>
                <span class="badge bg-primary-subtle text-primary border border-primary-subtle small">Tool</span>
              </div>
              <p class="small text-muted mb-2 flex-grow-1">${this.escapeHtml(t.description || 'Нет описания.')}</p>
              ${t.args_schema ? `
                <div class="mt-auto">
                  <details class="small">
                    <summary class="text-secondary cursor-pointer">Схема аргументов</summary>
                    <pre class="bg-dark text-light p-2 rounded mt-1 mb-0 font-monospace small" style="max-height: 150px; overflow-y: auto;">${this.escapeHtml(typeof t.args_schema === 'object' ? JSON.stringify(t.args_schema, null, 2) : String(t.args_schema))}</pre>
                  </details>
                </div>
              ` : ''}
            </div>
          </div>
        `).join('');
      }
    } catch (err) {
      loadingEl?.classList.add('d-none');
      if (container) {
        container.classList.remove('d-none');
        container.innerHTML = `<div class="col-12"><div class="alert alert-danger">${this.escapeHtml(err.message)}</div></div>`;
      }
    }
  }

  renderDiscoveredTools(tools, container) {
    if (!tools || tools.length === 0) {
      container.innerHTML = '<div class="text-muted text-center py-3">Сервер не вернул доступных инструментов.</div>';
      return;
    }

    container.innerHTML = tools.map((t, idx) => `
      <div class="p-3 bg-dark rounded border border-secondary">
        <div class="d-flex align-items-center justify-content-between mb-1">
          <strong class="text-warning font-monospace d-flex align-items-center gap-1">
            <i class="bi bi-wrench-adjustable"></i> ${this.escapeHtml(t.name)}
          </strong>
          <span class="badge bg-dark border border-secondary text-muted">#${idx + 1}</span>
        </div>
        <div class="small text-muted mb-2">${this.escapeHtml(t.description || 'Описание не указано')}</div>
        ${t.args_schema ? `
          <details class="small">
            <summary class="text-info cursor-pointer">Параметры и схема вызова</summary>
            <pre class="bg-black text-white p-2 rounded mt-1 mb-0 font-monospace small" style="max-height: 180px; overflow-y: auto;">${this.escapeHtml(typeof t.args_schema === 'object' ? JSON.stringify(t.args_schema, null, 2) : String(t.args_schema))}</pre>
          </details>
        ` : ''}
      </div>
    `).join('');
  }

  renderError(msg) {
    const container = document.getElementById('mcp-cards-container');
    if (container) {
      container.innerHTML = `
        <div class="col-12">
          <div class="alert alert-danger bg-dark border-danger text-light d-flex align-items-center justify-content-between">
            <div><i class="bi bi-exclamation-triangle-fill text-danger me-2"></i> ${this.escapeHtml(msg)}</div>
            <button class="btn btn-sm btn-outline-light" onclick="window.mcpTab?.refresh()">Повторить</button>
          </div>
        </div>
      `;
    }
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

// Global initialization hooks
window.McpTabManager = McpTabManager;
if (!window.mcpTab) {
  window.mcpTab = new McpTabManager();
}
window.initMcpTab = function() {
  if (window.mcpTab) {
    window.mcpTab.init();
  }
};

if (document.getElementById('mcp-tab-root')) {
  window.mcpTab.init();
}
