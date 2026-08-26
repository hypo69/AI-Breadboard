// ── PLUGINS TAB MAIN.JS ───────────────────────────────────────────────────────

let loadedPlugins = [];
let selectedPluginName = '';

// Notification helper
function showPluginNotification(message, type = 'info') {
  if (typeof window.showNotification === 'function') {
    window.showNotification(message, type);
    return;
  }
  console.log(`[Plugin Notification ${type}]: ${message}`);
}

// Initialize Plugins Tab
window.initPluginsTab = async function() {
  console.log('Инициализация вкладки плагинов...');
  await loadPluginsList();
};

// Загрузка списка всех плагинов
async function loadPluginsList() {
  const container = document.getElementById('plugins-list-container');
  if (!container) return;

  try {
    const data = await window.api.fetch('/api/admin/plugins');
    loadedPlugins = data.plugins || [];

    document.getElementById('plugins-count').textContent = loadedPlugins.length;
    const activeCount = loadedPlugins.filter(p => p.enabled).length;
    document.getElementById('active-plugins-badge').textContent = `${activeCount} активных`;

    renderPluginsList(loadedPlugins);
    syncPluginTabsVisibility(loadedPlugins);

    if (loadedPlugins.length > 0) {
      // Если плагин не выбран или текущий пропал, выбираем первый
      const toSelect = loadedPlugins.find(p => p.name === selectedPluginName) || loadedPlugins[0];
      selectPlugin(toSelect.name);
    } else {
      showPlaceholder();
    }
  } catch (ex) {
    console.error('Ошибка загрузки плагинов:', ex);
    container.innerHTML = `<div class="alert alert-danger m-2 small">Ошибка загрузки плагинов: ${ex.message}</div>`;
  }
}

// Отображение списка плагинов
function renderPluginsList(plugins) {
  const container = document.getElementById('plugins-list-container');
  if (!container) return;

  if (plugins.length === 0) {
    container.innerHTML = '<div class="text-center text-muted p-3 small">Плагины не найдены</div>';
    return;
  }

  let html = '<div class="list-group list-group-flush">';
  plugins.forEach(p => {
    const isSelected = p.name === selectedPluginName;
    const statusBadge = p.enabled 
      ? '<span class="badge bg-success-subtle text-success border border-success-subtle small">Вкл</span>'
      : '<span class="badge bg-secondary-subtle text-muted border small">Выкл</span>';

    html += `
      <a href="javascript:void(0)" 
         class="list-group-item list-group-item-action p-2 rounded mb-1 border-0 ${isSelected ? 'active text-white' : ''}" 
         onclick="selectPlugin('${p.name}')"
         style="cursor: pointer;">
        <div class="d-flex w-100 justify-content-between align-items-center mb-1">
          <div class="d-flex align-items-center gap-2 text-truncate">
            <span class="fs-5">${p.icon || '🧩'}</span>
            <strong class="text-truncate">${p.title || p.name}</strong>
          </div>
          <div>${statusBadge}</div>
        </div>
        <div class="small text-truncate ${isSelected ? 'text-white-50' : 'text-muted'}">
          ${p.description || p.name}
        </div>
      </a>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

// Фильтрация списка плагинов
function filterPluginsList() {
  const query = (document.getElementById('plugin-search-input')?.value || '').toLowerCase().trim();
  if (!query) {
    renderPluginsList(loadedPlugins);
    return;
  }
  const filtered = loadedPlugins.filter(p => 
    p.name.toLowerCase().includes(query) || 
    (p.title && p.title.toLowerCase().includes(query)) ||
    (p.description && p.description.toLowerCase().includes(query))
  );
  renderPluginsList(filtered);
}

// Выбор плагина для отображения органов управления
function selectPlugin(pluginName) {
  selectedPluginName = pluginName;
  const plugin = loadedPlugins.find(p => p.name === pluginName);
  if (!plugin) return;

  renderPluginsList(loadedPlugins);

  const placeholder = document.getElementById('plugin-placeholder');
  const contentPane = document.getElementById('plugin-content-pane');
  if (placeholder) placeholder.classList.add('d-none');
  if (contentPane) contentPane.classList.remove('d-none');

  // Header info
  document.getElementById('plugin-icon').textContent = plugin.icon || '🧩';
  document.getElementById('plugin-title').textContent = plugin.title || plugin.name;
  document.getElementById('plugin-version').textContent = `v${plugin.version || '1.0.0'}`;
  document.getElementById('plugin-category').textContent = plugin.category || 'tools';
  document.getElementById('plugin-id').textContent = `id: ${plugin.name}`;
  document.getElementById('plugin-description').textContent = plugin.description || 'Нет описания';
  
  const toggleSwitch = document.getElementById('plugin-toggle-switch');
  if (toggleSwitch) {
    toggleSwitch.checked = Boolean(plugin.enabled);
  }

  // Render Actions
  renderPluginActions(plugin);

  // Render Config Fields
  renderPluginFields(plugin);
}

// Отрисовка кнопок действий (Actions)
function renderPluginActions(plugin) {
  const container = document.getElementById('plugin-actions-container');
  const section = document.getElementById('plugin-actions-section');
  if (!container || !section) return;

  const actions = plugin.actions || [];
  if (actions.length === 0) {
    section.classList.add('d-none');
    return;
  }

  section.classList.remove('d-none');
  let html = '';
  actions.forEach(act => {
    const btnColor = act.color || 'primary';
    html += `
      <button class="btn btn-sm btn-outline-${btnColor} d-inline-flex align-items-center gap-1 shadow-sm"
              onclick="executePluginAction('${plugin.name}', '${act.id}', '${act.label}')"
              title="${act.description || ''}">
        <span>${act.label}</span>
      </button>
    `;
  });
  container.innerHTML = html;
}

// Отрисовка полей конфигурации
function renderPluginFields(plugin) {
  const container = document.getElementById('plugin-fields-container');
  const section = document.getElementById('plugin-config-section');
  if (!container || !section) return;

  const fields = plugin.fields || [];
  if (fields.length === 0) {
    section.classList.add('d-none');
    return;
  }

  section.classList.remove('d-none');
  const currentCfg = plugin.config || {};

  let html = '';
  fields.forEach(f => {
    const val = (currentCfg[f.id] !== undefined) ? currentCfg[f.id] : (f.default !== undefined ? f.default : '');
    const desc = f.description ? `<div class="form-text text-muted small">${f.description}</div>` : '';

    if (f.type === 'select') {
      let optionsHtml = '';
      (f.options || []).forEach(opt => {
        const isSel = String(opt.value) === String(val) ? 'selected' : '';
        optionsHtml += `<option value="${opt.value}" ${isSel}>${opt.label}</option>`;
      });
      html += `
        <div class="col-12 col-md-6">
          <label class="form-label small fw-semibold mb-1">${f.label}</label>
          <select class="form-select form-select-sm" name="${f.id}" data-field-type="select">
            ${optionsHtml}
          </select>
          ${desc}
        </div>
      `;
    } else if (f.type === 'boolean') {
      const checked = Boolean(val) ? 'checked' : '';
      html += `
        <div class="col-12 col-md-6 d-flex flex-column justify-content-center">
          <div class="form-check form-switch mt-2">
            <input class="form-check-input" type="checkbox" role="switch" name="${f.id}" id="field_${f.id}" ${checked} data-field-type="boolean">
            <label class="form-check-label small fw-semibold" for="field_${f.id}">${f.label}</label>
          </div>
          ${desc}
        </div>
      `;
    } else if (f.type === 'list_string') {
      const listVals = Array.isArray(val) ? val.join(', ') : (val || '');
      html += `
        <div class="col-12">
          <label class="form-label small fw-semibold mb-1">${f.label} (через запятую)</label>
          <input type="text" class="form-control form-control-sm font-monospace" name="${f.id}" value="${listVals}" data-field-type="list_string">
          ${desc}
        </div>
      `;
    } else if (f.type === 'readonly') {
      html += `
        <div class="col-12 col-md-6">
          <label class="form-label small fw-semibold mb-1 text-muted">${f.label}</label>
          <input type="text" class="form-control form-control-sm bg-body-tertiary text-muted" value="${val}" readonly>
          ${desc}
        </div>
      `;
    } else if (f.type === 'number') {
      html += `
        <div class="col-12 col-md-6">
          <label class="form-label small fw-semibold mb-1">${f.label}</label>
          <input type="number" class="form-control form-control-sm" name="${f.id}" value="${val}" data-field-type="number">
          ${desc}
        </div>
      `;
    } else {
      html += `
        <div class="col-12 col-md-6">
          <label class="form-label small fw-semibold mb-1">${f.label}</label>
          <input type="text" class="form-control form-control-sm" name="${f.id}" value="${val}" data-field-type="string">
          ${desc}
        </div>
      `;
    }
  });

  container.innerHTML = html;
}

// Переключение состояния плагина (Вкл / Выкл)
async function toggleCurrentPlugin(enabled) {
  if (!selectedPluginName) return;

  try {
    logToPluginConsole(`Переключение плагина '${selectedPluginName}' -> ${enabled ? 'ВКЛ' : 'ВЫКЛ'}...`);
    const res = await window.api.fetch(`/api/admin/plugins/${selectedPluginName}/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });

    const plugin = loadedPlugins.find(p => p.name === selectedPluginName);
    if (plugin) {
      plugin.enabled = enabled;
    }

    renderPluginsList(loadedPlugins);
    syncPluginTabsVisibility(loadedPlugins);
    showPluginNotification(res.message || 'Статус плагина обновлен', 'success');
    logToPluginConsole(`✓ ${res.message || 'Статус успешно обновлен'}`);
  } catch (ex) {
    console.error('Ошибка переключения плагина:', ex);
    showPluginNotification(`Ошибка: ${ex.message}`, 'danger');
    logToPluginConsole(`✗ Ошибка: ${ex.message}`);
    // Возвращаем тумблер в исходное состояние
    const toggleSwitch = document.getElementById('plugin-toggle-switch');
    if (toggleSwitch) toggleSwitch.checked = !enabled;
  }
}

// Сохранение настроек текущего плагина
async function saveCurrentPluginConfig() {
  if (!selectedPluginName) return;

  const form = document.getElementById('plugin-config-form');
  if (!form) return;

  const newConfig = {};
  const elements = form.querySelectorAll('[data-field-type]');

  elements.forEach(el => {
    const name = el.getAttribute('name');
    if (!name) return;
    const type = el.getAttribute('data-field-type');

    if (type === 'boolean') {
      newConfig[name] = el.checked;
    } else if (type === 'number') {
      newConfig[name] = Number(el.value);
    } else if (type === 'list_string') {
      newConfig[name] = el.value.split(',').map(s => s.trim()).filter(Boolean);
    } else {
      newConfig[name] = el.value;
    }
  });

  try {
    logToPluginConsole(`Сохранение параметров плагина '${selectedPluginName}'...`);
    const res = await window.api.fetch(`/api/admin/plugins/${selectedPluginName}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: newConfig })
    });

    const plugin = loadedPlugins.find(p => p.name === selectedPluginName);
    if (plugin) {
      plugin.config = res.config || newConfig;
    }

    showPluginNotification('Параметры успешно сохранены', 'success');
    logToPluginConsole(`✓ Конфигурация сохранена: ${JSON.stringify(newConfig, null, 2)}`);
  } catch (ex) {
    console.error('Ошибка сохранения конфигурации:', ex);
    showPluginNotification(`Ошибка: ${ex.message}`, 'danger');
    logToPluginConsole(`✗ Ошибка сохранения: ${ex.message}`);
  }
}

// Выполнение специфического действия (Action) плагина
async function executePluginAction(pluginName, actionId, actionLabel) {
  try {
    logToPluginConsole(`[ACTION] Запуск '${actionLabel}' для плагина '${pluginName}'...`);
    showPluginNotification(`Запуск '${actionLabel}'...`, 'info');

    // Собираем текущие поля формы как параметры действия
    const form = document.getElementById('plugin-config-form');
    const params = {};
    if (form) {
      const elements = form.querySelectorAll('[data-field-type]');
      elements.forEach(el => {
        const name = el.getAttribute('name');
        if (!name) return;
        const type = el.getAttribute('data-field-type');
        if (type === 'boolean') params[name] = el.checked;
        else if (type === 'number') params[name] = Number(el.value);
        else if (type === 'list_string') params[name] = el.value.split(',').map(s => s.trim()).filter(Boolean);
        else params[name] = el.value;
      });
    }

    const res = await window.api.fetch(`/api/admin/plugins/${pluginName}/action/${actionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ params })
    });

    if (res.success) {
      showPluginNotification(res.message || 'Действие успешно выполнено', 'success');
      logToPluginConsole(`✓ ${res.message || 'Успех'}\n${JSON.stringify(res.result || res, null, 2)}`);
    } else {
      showPluginNotification(res.message || 'Ошибка выполнения действия', 'warning');
      logToPluginConsole(`⚠ ${res.message || 'Завершено с предупреждением'}`);
    }
  } catch (ex) {
    console.error(`Ошибка выполнения действия ${actionId}:`, ex);
    showPluginNotification(`Ошибка: ${ex.message}`, 'danger');
    logToPluginConsole(`✗ Ошибка выполнения: ${ex.message}`);
  }
}

// Логирование в консоль плагина
function logToPluginConsole(text) {
  const consoleEl = document.getElementById('plugin-console-output');
  if (!consoleEl) return;
  const time = new Date().toLocaleTimeString();
  consoleEl.textContent = `[${time}] ${text}\n` + consoleEl.textContent;
}

// Очистка консоли
function clearPluginConsole() {
  const consoleEl = document.getElementById('plugin-console-output');
  if (consoleEl) consoleEl.textContent = 'Консоль очищена.\n';
}

function showPlaceholder() {
  const placeholder = document.getElementById('plugin-placeholder');
  const contentPane = document.getElementById('plugin-content-pane');
  if (placeholder) placeholder.classList.remove('d-none');
  if (contentPane) contentPane.classList.add('d-none');
}

// Синхронизация видимости вкладок в навбаре с состоянием активности плагинов
function syncPluginTabsVisibility(plugins) {
  if (!Array.isArray(plugins)) return;
  const pluginMap = {};
  plugins.forEach(p => {
    pluginMap[p.name] = Boolean(p.enabled);
  });

  // Находим все элементы навигации, привязанные к плагинам
  const pluginNavItems = document.querySelectorAll('[data-plugin-tab]');
  pluginNavItems.forEach(item => {
    const pluginName = item.getAttribute('data-plugin-tab');
    const isEnabled = (pluginMap[pluginName] !== undefined) ? pluginMap[pluginName] : false;

    if (isEnabled) {
      item.classList.remove('d-none');
    } else {
      item.classList.add('d-none');
      // Если отключенная вкладка была активна, переключаемся на вкладку чата
      const button = item.querySelector('.nav-link');
      if (button && button.classList.contains('active')) {
        const chatTab = document.querySelector('[data-bs-target="#tab-chat"]');
        if (chatTab) {
          const tab = new bootstrap.Tab(chatTab);
          tab.show();
        }
      }
    }
  });
}

// Make functions globally available for HTML inline handlers
window.loadPluginsList = loadPluginsList;
window.filterPluginsList = filterPluginsList;
window.selectPlugin = selectPlugin;
window.toggleCurrentPlugin = toggleCurrentPlugin;
window.saveCurrentPluginConfig = saveCurrentPluginConfig;
window.executePluginAction = executePluginAction;
window.clearPluginConsole = clearPluginConsole;
window.syncPluginTabsVisibility = syncPluginTabsVisibility;
