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

// Helper to check if current view is user interface
function isRunningInUserInterface() {
  if (document.getElementById('user-interface')) return true;
  if (window.location.pathname.includes('/user')) return true;
  if (!document.getElementById('admin-interface')) {
    if (typeof window.isUserAdmin === 'function') {
      return !window.isUserAdmin();
    }
    return true;
  }
  return false;
}

// Initialize Plugins Tab
window.initPluginsTab = async function() {
  console.log(i18n.t('auto___eb75b0'));
  await loadPluginsList();
};

// Загрузка списка всех плагинов
async function loadPluginsList() {
  const container = document.getElementById('plugins-list-container');
  if (!container) return;

  try {
    const isUserUI = isRunningInUserInterface();
    const endpoint = isUserUI ? '/api/plugins?scope=user' : '/api/admin/plugins';

    let data;
    if (window.api && typeof window.api.fetch === 'function') {
      try {
        data = await window.api.fetch(endpoint);
      } catch {
        data = await window.api.fetch('/api/admin/plugins');
      }
    } else {
      let resp = await fetch(endpoint);
      if (!resp.ok && isUserUI) {
        resp = await fetch('/api/admin/plugins?scope=user');
      }
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      data = await resp.json();
    }
    let plugins = data.plugins || [];
    if (isUserUI) {
      plugins = plugins.filter(p => !p.is_system && p.scope !== 'system');
    }
    loadedPlugins = plugins;

    const countEl = document.getElementById('plugins-count');
    if (countEl) countEl.textContent = loadedPlugins.length;
    const activeCount = loadedPlugins.filter(p => p.enabled).length;
    const badgeEl = document.getElementById('active-plugins-badgei18n.t('auto__if_badgeel_badgeel_textcontent_activecount_renderpluginslist_loadedplugins_syncplugintabsvisibility_loadedplugins_if_loadedplugins_length_0_const_toselect_loadedplugins_find_p_p_name_selectedpluginname_loadedplugins_0_selectplugin_toselect_name_else_showplaceholder_catch_ex_console_error__6e46e6')Ошибка загрузки плагинов:', ex);
    container.innerHTML = `<div class="alert alert-danger m-2 small">Ошибка загрузки плагинов: ${ex.message}</div>`;
  }
}

// Отображение списка плагинов
function renderPluginsList(plugins) {
  const container = document.getElementById('plugins-list-container');
  if (!container) return;

  if (plugins.length === 0) {
    const isUserUI = isRunningInUserInterface();
    const emptyMsg = isUserUI ? i18n.t('auto___605fd0') : i18n.t('auto___a0a8da');
    container.innerHTML = `<div class="text-center text-muted p-3 small">${emptyMsg}</div>`;
    return;
  }

  let html = '<div class="list-group list-group-flush">';
  plugins.forEach(p => {
    const isSelected = p.name === selectedPluginName;
    const statusBadge = p.enabled 
      ? '<span class="badge bg-success-subtle text-success border border-success-subtle small">Вкл</span>'
      : '<span class="badge bg-danger-subtle text-danger border border-danger-subtle small">Выкл</span>';
    const typeBadge = p.is_system
      ? '<span class="badge bg-secondary-subtle text-body-secondary border small">Системный</span>'
      : '<span class="badge bg-info-subtle text-info-emphasis border small">Пользовательский</span>';

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
          <div class="d-flex align-items-center gap-1">${typeBadge}${statusBadge}</div>
        </div>
        <div class="small text-truncate ${isSelected ? 'text-white-50' : 'text-muted'}">
          ${p.description || p.name}
        </div>
      </a>
    `;
  });
  html += '</div>i18n.t('auto__container_innerhtml_html_function_filterpluginslist_const_query_document_getelementbyid__ff0e09')plugin-search-input')?.value || 'i18n.t('auto__tolowercase_trim_if_query_renderpluginslist_loadedplugins_return_const_filtered_loadedplugins_filter_p_p_name_tolowercase_includes_query_p_title_p_title_tolowercase_includes_query_p_description_p_description_tolowercase_includes_query_renderpluginslist_filtered_function_selectplugin_pluginname_if_pluginname_return_selectedpluginname_pluginname_const_normalized_pluginname_tolowercase_replace_g__04c335')_');
  const plugin = loadedPlugins.find(p => {
    const pName = (p.name || '').toLowerCase().replace(/-/g, '_');
    const pId = (p.id || '').toLowerCase().replace(/-/g, '_');
    const pTitle = (p.title || '').toLowerCase();
    return pName === normalized || pId === normalized || pTitle === pluginName.toLowerCase();
  });
  if (!plugin) {
    if (!loadedPlugins || loadedPlugins.length === 0) {
      loadPluginsList().then(() => {
        if (loadedPlugins && loadedPlugins.length > 0) {
          const pFound = loadedPlugins.find(p => {
            const pName = (p.name || '').toLowerCase().replace(/-/g, '_');
            const pId = (p.id || '').toLowerCase().replace(/-/g, '_');
            const pTitle = (p.title || '').toLowerCase();
            return pName === normalized || pId === normalized || pTitle === pluginName.toLowerCase();
          });
          if (pFound) selectPlugin(pFound.name);
        }
      });
    }
    return;
  }

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
  document.getElementById('plugin-description').textContent = plugin.description || i18n.t('auto___f09160');
  
  const scopeBadgeEl = document.getElementById('plugin-scope-badge');
  if (scopeBadgeEl) {
    if (plugin.is_system) {
      scopeBadgeEl.textContent = i18n.t('auto___eca171');
      scopeBadgeEl.className = 'badge bg-secondary-subtle text-body-secondary border';
    } else {
      scopeBadgeEl.textContent = i18n.t('auto___dfbb74');
      scopeBadgeEl.className = 'badge bg-info-subtle text-info-emphasis border';
    }
  }

  const isAdmin = (typeof window.isUserAdmin === 'function') ? window.isUserAdmin() : false;
  const isLocked = Boolean(plugin.is_system && !isAdmin);

  const toggleSwitch = document.getElementById('plugin-toggle-switch');
  if (toggleSwitch) {
    toggleSwitch.checked = Boolean(plugin.enabled);
    toggleSwitch.disabled = isLocked;
    toggleSwitch.title = isLocked 
      ? i18n.t('auto___0f3b3a') 
      : i18n.t('auto___0535e1');
  }

  const saveBtn = document.getElementById('btn-save-plugin-config');
  if (saveBtn) {
    saveBtn.disabled = isLocked;
    saveBtn.title = isLocked ? i18n.t('auto___035aaf') : 'i18n.t('auto__render_actions_renderpluginactions_plugin_render_config_fields_renderpluginfields_plugin_actions_function_renderpluginactions_plugin_const_container_document_getelementbyid__251d60')plugin-actions-container');
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
    const label = act.label || act.name || act.id;
    const icon = act.icon ? `<span class="me-1">${act.icon}</span>` : '';
    const safeLabel = label.replace(/'/g, "\\'");
    html += `
      <button class="btn btn-sm btn-outline-${btnColor} d-inline-flex align-items-center gap-1 shadow-sm"
              onclick="executePluginAction('${plugin.name}', '${act.id}', '${safeLabel}')"
              title="${act.description || ''}">
        ${icon}<span>${label}</span>
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
          <label class="form-label small fw-semibold mb-1i18n.t('auto__f_label_label_input_type__17b3ea')text" class="form-control form-control-sm font-monospace" name="${f.id}" value="${listVals}" data-field-type="list_string">
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
    logToPluginConsole(`Переключение плагина '${selectedPluginName}' -> ${enabled ? i18n.t('auto___593689') : i18n.t('auto___919af8')}...`);
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
    showPluginNotification(res.message || i18n.t('auto___73044b'), 'success');
    logToPluginConsole(`✓ ${res.message || i18n.t('auto___60064f')}`);
  } catch (ex) {
    console.error(i18n.t('auto___3deefa'), ex);
    showPluginNotification(`Ошибка: ${ex.message}`, 'dangeri18n.t('auto__logtopluginconsole_ex_message_const_toggleswitch_document_getelementbyid__39f96a')plugin-toggle-switchi18n.t('auto__if_toggleswitch_toggleswitch_checked_enabled_async_function_savecurrentpluginconfig_if_selectedpluginname_return_const_form_document_getelementbyid__8db223')plugin-config-form');
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
      newConfig[name] = el.value.split(',i18n.t('auto__map_s_s_trim_filter_boolean_else_newconfig_name_el_value_try_logtopluginconsole__11265f')${selectedPluginName}'...`);
    const res = await window.api.fetch(`/api/admin/plugins/${selectedPluginName}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: newConfig })
    });

    const plugin = loadedPlugins.find(p => p.name === selectedPluginName);
    if (plugin) {
      plugin.config = res.config || newConfig;
    }

    showPluginNotification(i18n.t('auto___b6f9d2'), 'successi18n.t('auto__logtopluginconsole_json_stringify_newconfig_null_2_catch_ex_console_error__7e715f')Ошибка сохранения конфигурации:i18n.t('auto__ex_showpluginnotification_ex_message__26cf67')dangeri18n.t('auto__logtopluginconsole_ex_message_action_async_function_executepluginaction_pluginname_actionid_actionlabel_try_logtopluginconsole_action__9b1c40')${actionLabel}i18n.t('auto___cdde58')${pluginName}i18n.t('auto__showpluginnotification__10dca9')${actionLabel}'...`, 'infoi18n.t('auto__const_form_document_getelementbyid__0a0370')plugin-config-form');
    const params = {};
    if (form) {
      const elements = form.querySelectorAll('[data-field-type]');
      elements.forEach(el => {
        const name = el.getAttribute('name');
        if (!name) return;
        const type = el.getAttribute('data-field-type');
        if (type === 'boolean') params[name] = el.checked;
        else if (type === 'number') params[name] = Number(el.value);
        else if (type === 'list_string') params[name] = el.value.split(',i18n.t('auto__map_s_s_trim_filter_boolean_else_params_name_el_value_const_plugin_typeof_loadedplugins__c415f0')undefined') ? loadedPlugins.find(p => p.name === pluginName) : null;
    const actDef = plugin?.actions?.find(a => a.id === actionId);
    if (actDef && Array.isArray(actDef.parameters)) {
      for (const param of actDef.parameters) {
        if (param.required && (params[param.name] === undefined || params[param.name] === 'i18n.t('auto__const_userval_prompt_param_description_param_name_if_userval_null_logtopluginconsole_action_return_params_param_name_userval_const_res_await_window_api_fetch_api_admin_plugins_pluginname_action_actionid_method__296025')POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ params })
    });

    if (res.success || res.status === 'success') {
      showPluginNotification(res.message || i18n.t('auto___5e263d'), 'success');
      logToPluginConsole(`✓ ${res.message || i18n.t('auto___053399')}\n${JSON.stringify(res.result || res.results || res, null, 2)}`);
    } else {
      showPluginNotification(res.message || i18n.t('auto___bb27b8'), 'warning');
      logToPluginConsole(`⚠ ${res.message || i18n.t('auto___ced8df')}`);
    }
  } catch (ex) {
    console.error(`Ошибка выполнения действия ${actionId}:`, ex);
    showPluginNotification(`Ошибка: ${ex.message}`, 'dangeri18n.t('auto__logtopluginconsole_ex_message_function_logtopluginconsole_text_const_consoleel_document_getelementbyid__b10cb5')plugin-console-outputi18n.t('auto__if_consoleel_return_const_time_new_date_tolocaletimestring_consoleel_textcontent_time_text_n_consoleel_textcontent_function_clearpluginconsole_const_consoleel_document_getelementbyid__6140c0')plugin-console-output');
  if (consoleEl) consoleEl.textContent = i18n.t('auto__n_01d8e9');
}

function showPlaceholder() {
  const placeholder = document.getElementById('plugin-placeholder');
  const contentPane = document.getElementById('plugin-content-pane');
  if (placeholder) placeholder.classList.remove('d-none');
  if (contentPane) contentPane.classList.add('d-nonei18n.t('auto__function_openpluginfromdropdown_pluginname_if_pluginname_return_1_document_queryselectorall__eaa73b')#mainTabs .dropdown-menu.show').forEach((m) => {
    m.classList.remove('show');
    m.closest('.dropdown')?.querySelector('.dropdown-toggle')?.classList.remove('show');
  });

  const normalized = pluginName.toLowerCase().replace(/-/g, '_i18n.t('auto__2_dom_if_normalized__25d29a')telegram_channel_rag' || normalized === 'telegram_rag') {
    const pane = document.getElementById('tab-telegram-rag') || document.getElementById('tab-telegram_rag');
    if (pane && typeof window.switchTab === 'function') {
      window.switchTab('tab-telegram-rag');
      return;
    }
  }
  if (normalized === 'news_feed' || normalized === 'news' || normalized === 'smart_news' || normalized === 'smart_feed_news') {
    const pane = document.getElementById('tab-news');
    if (pane && typeof window.switchTab === 'function') {
      window.switchTab('tab-newsi18n.t('auto__return_3_if_typeof_window_switchtab__fcdce2')function') {
    window.switchTab('tab-plugins');
  }

  const select = () => {
    if (typeof window.selectPlugin === 'functioni18n.t('auto__window_selectplugin_pluginname_select_settimeout_select_150_settimeout_select_400_function_syncplugintabsvisibility_plugins_if_array_isarray_plugins_return_const_pluginmap_plugins_foreach_p_pluginmap_p_name_boolean_p_enabled_1_const_enabledcontainers_document_queryselectorall__a7a68c')#nav-enabled-plugins-list, .nav-enabled-plugins-list');
  const enabledPlugins = plugins.filter(p => p.enabled);

  enabledContainers.forEach(container => {
    if (enabledPlugins.length === 0) {
      container.innerHTML = `
        <div class="list-group-item dropdown-item text-muted small py-2 px-3 fst-italic">
          Нет активных плагинов
        </div>
      `;
    } else {
      let html = '';
      enabledPlugins.forEach(p => {
        const icon = p.icon || '🧩';
        const title = p.title || p.name;
        const desc = p.description || title;
        html += `
          <button class="list-group-item list-group-item-action dropdown-item d-flex align-items-center gap-2 py-2 px-3 text-truncate" 
                  type="button" 
                  data-plugin="${p.name}"
                  title="${desc}"
                  onclick="openPluginFromDropdown('${p.name}')">
            <span>${icon}</span>
            <span class="text-truncate">${title}</span>
          </button>
        `;
      });
      container.innerHTML = html;
    }
  });

  // 2. Находим все элементы навигации, привязанные к отдельным плагинам
  const pluginNavItems = document.querySelectorAll('[data-plugin-tab]');
  pluginNavItems.forEach(item => {
    const pluginName = item.getAttribute('data-plugin-tab');
    const isEnabled = (pluginMap[pluginName] !== undefined) ? pluginMap[pluginName] : false;

    if (isEnabled) {
      item.classList.remove('d-none');
    } else {
      item.classList.add('d-nonei18n.t('auto__const_button_item_queryselector__aa6df0').nav-link, .dropdown-item');
      if (button && button.classList.contains('active')) {
        if (typeof window.switchTab === 'function') {
          window.switchTab('tab-chat');
        } else {
          const chatTab = document.querySelector('[data-bs-target="#tab-chat"]');
          if (chatTab) {
            const tab = new bootstrap.Tab(chatTab);
            tab.show();
          }
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
window.openPluginFromDropdown = openPluginFromDropdown;

// Auto-run initialization
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.initPluginsTab === 'function') window.initPluginsTab();
  });
} else {
  if (typeof window.initPluginsTab === 'function') window.initPluginsTab();
}
