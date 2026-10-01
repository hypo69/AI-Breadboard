/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/registry_viewer_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/registry_viewer_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

// Windows Registry Viewer Tab JavaScript Module
(function() {
  let currentHive = 'HKEY_LOCAL_MACHINE';
  let currentPath = 'SOFTWARE';
  let currentKeyData = null;
  let isInitialized = false;

  async function loadBookmarks() {
    const container = document.getElementById('reg-bookmarks-container');
    if (!container) return;

    try {
      const res = await fetch('/api/registry/bookmarks');
      if (!res.ok) throw new Error('Bookmarks API error');
      const data = await res.json();
      const bookmarks = data.bookmarks || [];

      container.innerHTML = `
        <span class="text-muted small me-2"><i class="bi bi-bookmark-star-fill text-warning me-1i18n.t('auto__i_span_bookmarks_map_b_button_class__897981')reg-bookmark-btn" data-hive="${b.hive}" data-path="${b.path}" title="${b.description || ''}">
          <span>${b.icon || '📌'}</span> ${b.title}
        </button>
      `).join('');

      container.querySelectorAll('.reg-bookmark-btn').forEach(btn => {
        btn.onclick = () => {
          const h = btn.getAttribute('data-hive');
          const p = btn.getAttribute('data-path');
          navigateTo(h, p);
        };
      });
    } catch (e) {
      console.warn('[RegistryViewerTab] Failed to load bookmarks:', e);
    }
  }

  async function navigateTo(hive, path) {
    currentHive = hive;
    currentPath = path.trim().replace(/^[\\\/]+|[\\\/]+$/g, '');

    const hiveSelect = document.getElementById('reg-hive-select');
    const pathInput = document.getElementById('reg-path-input');
    if (hiveSelect) hiveSelect.value = currentHive;
    if (pathInput) pathInput.value = currentPath;

    await loadKey(currentHive, currentPath);
  }

  async function loadKey(hive, path) {
    const subkeysList = document.getElementById('reg-subkeys-list');
    const valuesTbody = document.getElementById('reg-values-tbody');
    const badge = document.getElementById('reg-status-badge');
    const subkeysCountBadge = document.getElementById('reg-subkeys-count-badge');
    const valuesCountBadge = document.getElementById('reg-values-count-badgei18n.t('auto__if_badge_badge_innertext_hive_try_const_url_api_registry_key_hive_encodeuricomponent_hive_path_encodeuricomponent_path_const_res_await_fetch_url_if_res_ok_const_errjson_await_res_json_catch_throw_new_error_errjson_detail_http_res_status_currentkeydata_await_res_json_subkeys_const_subkeys_currentkeydata_subkeys_if_subkeyscountbadge_subkeyscountbadge_innertext_subkeys_length_if_subkeys_length_0_subkeyslist_innerhtml__eb3763')<div class="text-muted text-center py-4 small">Нет подразделов</div>';
      } else {
        subkeysList.innerHTML = subkeys.map(sk => `
          <div class="reg-tree-item" data-subkey="${sk}" title="${sk}">
            <i class="bi bi-folder-fill text-warning"></i>
            <span class="text-truncate">${sk}</span>
          </div>
        `).join('');

        subkeysList.querySelectorAll('.reg-tree-item').forEach(item => {
          item.onclick = () => {
            const subkey = item.getAttribute('data-subkeyi18n.t('auto__const_newpath_currentpath_currentpath_subkey_subkey_navigateto_currenthive_newpath_values_rendervalues_if_badge_badge_classname__24b3bd')badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2i18n.t('auto__badge_innertext_hive_catch_err_console_error__b3089a')[RegistryViewerTab] Error loading key:', err);
      if (valuesTbody) {
        valuesTbody.innerHTML = `<tr><td colspan="3" class="text-center text-danger p-4"><i class="bi bi-exclamation-triangle-fill me-1i18n.t('auto__i_err_message_td_tr_if_subkeyslist_subkeyslist_innerhtml_div_class__2d9c62')text-danger text-center py-4 small">${err.message}</div>`;
      }
      if (badge) {
        badge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
        badge.innerText = i18n.t('auto___81edb9');
      }
    }
  }

  function renderValues() {
    const valuesTbody = document.getElementById('reg-values-tbody');
    const valuesCountBadge = document.getElementById('reg-values-count-badge');
    if (!valuesTbody || !currentKeyData) return;

    const filterText = (document.getElementById('reg-filter-input')?.value || '').toLowerCase().trim();
    const values = currentKeyData.values || [];

    const filtered = values.filter(v => {
      if (!filterText) return true;
      return v.name.toLowerCase().includes(filterText) || String(v.data).toLowerCase().includes(filterText) || v.type_name.toLowerCase().includes(filterText);
    });

    if (valuesCountBadge) valuesCountBadge.innerText = `${filtered.length} / ${values.length}`;

    if (filtered.length === 0) {
      valuesTbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted p-4">Параметры отсутствуют или не соответствуют фильтру</td></tr>';
      return;
    }

    valuesTbody.innerHTML = filtered.map((v, idx) => {
      let dataDisplay = v.data;
      if (dataDisplay === null || dataDisplay === undefined) {
        dataDisplay = '<span class="text-muted">(Значение не задано)</span>';
      } else if (typeof dataDisplay === 'object') {
        dataDisplay = `<pre class="mb-0 text-info" style="font-size: 0.75rem;">${JSON.stringify(dataDisplay, null, 2)}</pre>`;
      } else {
        dataDisplay = `<span class="text-light text-break">${escapeHtml(String(dataDisplay))}</span>`;
      }

      const isDefault = v.name === i18n.t('auto__default__7d867e') || v.name === '(Default)';
      const rawNameAttr = escapeHtml(isDefault ? '' : v.name);

      return `
        <tr class="reg-val-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto__ai__7a9e89')>
          <td>
            <div class="fw-bold text-white text-truncate" style="max-width: 220px;" title="${v.name}">
              <i class="bi bi-file-earmark-binary text-secondary me-1"></i>
              ${escapeHtml(v.name)}
            </div>
          </td>
          <td>
            <span class="reg-type-badge">${v.type_name}</span>
          </td>
          <td>
            ${dataDisplay}
          </td>
          <td class="text-center">
            <button class="btn btn-xs btn-outline-info py-0 px-2 me-1 btn-edit-val" data-idx="${idx}" title=i18n.t('auto___901beb')>
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-xs btn-outline-danger py-0 px-2 btn-del-val" data-name="${rawNameAttr}" title=i18n.t('auto___86ea33')>
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('i18n.t('auto__aitablemodal_valuestbody_queryselectorall__bc152a').reg-val-row').forEach(row => {
      row.onclick = (evt) => {
        if (evt.target.closest('.btn-edit-val') || evt.target.closest('.btn-del-val')) return;
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const v = filtered[idx];
        if (!v) return;

        if (window.AITableModal) {
          window.AITableModal.show({
            icon: '🔑',
            title: v.name || '(Default)',
            subtitle: `${currentHive}\\${currentPath}`,
            tableType: 'registry',
            badges: [
              { text: v.type_name || 'REG_SZ', class: 'badge bg-info text-dark' },
              { text: currentHive, class: 'badge bg-secondary' }
            ],
            metadata: [
              { label: i18n.t('auto___0db49b'), value: v.name || i18n.t('auto___75241b') },
              { label: i18n.t('auto___3822a6'), value: v.type_name },
              { label: i18n.t('auto__hive__453091'), value: currentHive },
              { label: i18n.t('auto___6097ca'), value: currentPath, isCode: true, fullWidth: true },
              { label: i18n.t('auto___9f0b99'), value: String(v.data ?? ''), isCode: true, fullWidth: true }
            ],
            rawTitle: i18n.t('auto___a9a973'),
            rawContent: typeof v.data === 'object' ? JSON.stringify(v.data, null, 2) : String(v.data ?? 'i18n.t('auto__requestdata_hive_currenthive_path_currentpath_name_v_name_type_v_type_name_data_v_data_valuestbody_queryselectorall__08f087').btn-edit-val').forEach(btn => {
      btn.onclick = (evt) => {
        evt.stopPropagation();
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        const valObj = filtered[idx];
        if (valObj) openEditValueModal(valObj);
      };
    });

    valuesTbody.querySelectorAll('.btn-del-val').forEach(btn => {
      btn.onclick = (evt) => {
        evt.stopPropagation();
        const valName = btn.getAttribute('data-name');
        confirmDeleteValue(valName);
      };
    });
  }

  function openEditValueModal(valObj) {
    const isDefault = !valObj.name || valObj.name === i18n.t('auto__default__7d867e') || valObj.name === '(Default)';
    const nameInput = document.getElementById('regModalValueName');
    const typeSelect = document.getElementById('regModalValueType');
    const dataInput = document.getElementById('regModalValueData');
    const title = document.getElementById('regValueModalTitle');

    if (title) title.innerText = i18n.t('auto___b76c0f');
    if (nameInput) {
      nameInput.value = isDefault ? 'i18n.t('auto__valobj_name_nameinput_disabled_true_if_typeselect_typeselect_value_valobj_type_name__b01b60')REG_SZ';
    if (dataInput) {
      if (Array.isArray(valObj.data)) {
        dataInput.value = valObj.data.join('\n');
      } else {
        dataInput.value = valObj.data !== null && valObj.data !== undefined ? String(valObj.data) : '';
      }
    }

    const modalEl = document.getElementById('regValueModal');
    if (modalEl && window.bootstrap) {
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }
  }

  function openCreateValueModal() {
    const nameInput = document.getElementById('regModalValueName');
    const typeSelect = document.getElementById('regModalValueType');
    const dataInput = document.getElementById('regModalValueData');
    const title = document.getElementById('regValueModalTitle');

    if (title) title.innerText = i18n.t('auto___607c41');
    if (nameInput) {
      nameInput.value = '';
      nameInput.disabled = false;
    }
    if (typeSelect) typeSelect.value = 'REG_SZ';
    if (dataInput) dataInput.value = '';

    const modalEl = document.getElementById('regValueModal');
    if (modalEl && window.bootstrap) {
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }
  }

  async function saveModalValue() {
    const nameInput = document.getElementById('regModalValueName');
    const typeSelect = document.getElementById('regModalValueType');
    const dataInput = document.getElementById('regModalValueData');
    const backupCheck = document.getElementById('regModalBackupCheck');

    const name = nameInput ? nameInput.value.trim() : '';
    const type_name = typeSelect ? typeSelect.value : 'REG_SZ';
    const rawData = dataInput ? dataInput.value : '';
    const create_backup = backupCheck ? backupCheck.checked : true;

    try {
      const payload = {
        hive: currentHive,
        path: currentPath,
        name: name,
        type_name: type_name,
        data: rawData,
        create_backup: create_backup
      };

      const res = await fetch('/api/registry/value', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      const modalEl = document.getElementById('regValueModali18n.t('auto__if_modalel_window_bootstrap_const_modal_bootstrap_modal_getinstance_modalel_if_modal_modal_hide_await_loadkey_currenthive_currentpath_catch_e_window_showtoast_e_message__04dc24')dangeri18n.t('auto__alert_e_message_async_function_confirmdeletevalue_name_const_displayname_name__049163')${name}'` : i18n.t('auto___75241b');
    if (!confirm(`Вы действительно хотите удалить параметр ${displayName}? Перед удалением будет автоматически создан бэкап.`)) {
      return;
    }

    try {
      const res = await fetch('/api/registry/value', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_hive_currenthive_path_currentpath_name_name_create_backup_true_if_res_ok_const_errjson_await_res_json_catch_throw_new_error_errjson_detail_http_res_status_window_showtoast_displayname__b57d66')successi18n.t('auto__await_loadkey_currenthive_currentpath_catch_e_window_showtoast_e_message__02cc2e')dangeri18n.t('auto__alert_e_message_function_opencreatekeymodal_const_keynameinput_document_getelementbyid__dbae76')regModalNewKeyName');
    if (keyNameInput) keyNameInput.value = '';

    const modalEl = document.getElementById('regKeyModal');
    if (modalEl && window.bootstrap) {
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }
  }

  async function saveModalKey() {
    const keyNameInput = document.getElementById('regModalNewKeyName');
    const newKeyName = keyNameInput ? keyNameInput.value.trim() : '';
    if (!newKeyName) {
      window.showToast?.(i18n.t('auto___bff380'), 'warning') || alert(i18n.t('auto___bff380'));
      return;
    }

    const newPath = currentPath ? `${currentPath}\\${newKeyName}` : newKeyName;

    try {
      const res = await fetch('/api/registry/key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hive: currentHive,
          path: newPath
        })
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      const modalEl = document.getElementById('regKeyModali18n.t('auto__if_modalel_window_bootstrap_const_modal_bootstrap_modal_getinstance_modalel_if_modal_modal_hide_window_showtoast__84ff56')${newKeyName}i18n.t('auto___e150b1')successi18n.t('auto__await_loadkey_currenthive_currentpath_catch_e_window_showtoast_e_message__48c6a0')dangeri18n.t('auto__alert_e_message_async_function_deletecurrentkey_if_currentpath_window_showtoast__ed5641')Нельзя удалить корневой раздел', 'warning') || alert(i18n.t('auto___5a6e78'));
      return;
    }

    if (!confirm(`ВНИМАНИЕ: Вы действительно хотите удалить раздел '${currentHive}\\${currentPath}i18n.t('auto__return_try_const_res_await_fetch__4a8c1c')/api/registry/key', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hive: currentHive,
          path: currentPath,
          recursive: true,
          create_backup: true
        })
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      window.showToast?.(i18n.t('auto___8fcfbd'), 'successi18n.t('auto__goup_catch_e_window_showtoast_e_message__97c081')dangeri18n.t('auto__alert_e_message_async_function_openbackupsmodal_const_modalel_document_getelementbyid__b8b3ae')regBackupsModal');
    const tbody = document.getElementById('reg-backups-tbody');

    if (modalEl && window.bootstrap) {
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }

    if (tbody) tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Загрузка истории снимков...</td></tr>';

    try {
      const res = await fetch('/api/registry/backups');
      if (!res.ok) throw new Error(i18n.t('auto___0d9ef2'));
      const data = await res.json();
      const backups = data.backups || [];

      if (backups.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-muted">Точки восстановления отсутствуют</td></tr>';
        return;
      }

      tbody.innerHTML = backups.map(b => `
        <tr>
          <td><small class="text-light">${new Date(b.timestamp).toLocaleString()}</small></td>
          <td class="text-truncate" style="max-width: 250px;" title="${b.hive}\\${b.path}">
            <span class="text-warning">${b.hive}</span>\\${escapeHtml(b.path)}
          </td>
          <td><span class="badge bg-secondary">${escapeHtml(b.operation)}</span></td>
          <td>
            <button class="btn btn-xs btn-outline-warning py-0 px-2 btn-restore-backup" data-id="${b.backup_id}">
              <i class="bi bi-arrow-counterclockwise me-1"></i> Откатить
            </button>
          </td>
        </tr>
      `).join('');

      tbody.querySelectorAll('.btn-restore-backup').forEach(btn => {
        btn.onclick = async () => {
          const backupId = btn.getAttribute('data-idi18n.t('auto__if_confirm_backupid_return_try_const_rres_await_fetch_api_registry_restore_backup_id_encodeuricomponent_backupid_method__e5d3f8')POST'
            });
            if (!rRes.ok) {
              const err = await rRes.json().catch(() => ({}));
              throw new Error(err.detail || `HTTP ${rRes.status}`);
            }
            window.showToast?.(i18n.t('auto___2306f0'), 'successi18n.t('auto__await_loadkey_currenthive_currentpath_catch_err_window_showtoast_err_message__a705dc')danger') || alert(`Ошибка восстановления: ${err.message}`);
          }
        };
      });
    } catch (e) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-danger">${e.message}</td></tr>`;
    }
  }

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function goUp() {
    if (!currentPath) return;
    const parts = currentPath.split('\\');
    parts.pop();
    const newPath = parts.join('\\');
    navigateTo(currentHive, newPath);
  }

  function copyCurrentPath() {
    const full = `${currentHive}\\${currentPath}`.replace(/\\+$/, '');
    if (navigator.clipboard) {
      navigator.clipboard.writeText(full).then(() => {
        const btn = document.getElementById('btn-reg-copy-path');
        if (btn) {
          const orig = btn.innerHTML;
          btn.innerHTML = '<i class="bi bi-check me-1"></i> Скопировано!';
          setTimeout(() => { btn.innerHTML = orig; }, 1500);
        }
      });
    }
  }

  window.initRegistryViewerTab = async function() {
    console.log('[RegistryViewerTab] Initializing Registry Viewer & Editor tab...');

    const hiveSelect = document.getElementById('reg-hive-select');
    const pathInput = document.getElementById('reg-path-input');
    const goBtn = document.getElementById('btn-reg-go');
    const upBtn = document.getElementById('btn-reg-up');
    const filterInput = document.getElementById('reg-filter-input');
    const refreshBtn = document.getElementById('btn-reg-refresh');
    const copyBtn = document.getElementById('btn-reg-copy-path');
    const backupsBtn = document.getElementById('btn-reg-backups-modal');
    const addValBtn = document.getElementById('btn-reg-add-value');
    const addKeyBtn = document.getElementById('btn-reg-add-key');
    const delKeyBtn = document.getElementById('btn-reg-delete-current-key');
    const saveValModalBtn = document.getElementById('btn-reg-modal-save');
    const saveKeyModalBtn = document.getElementById('btn-reg-modal-create-key');

    if (hiveSelect) {
      hiveSelect.onchange = () => {
        navigateTo(hiveSelect.value, '');
      };
    }
    if (goBtn && pathInput) {
      goBtn.onclick = () => {
        navigateTo(hiveSelect.value, pathInput.value);
      };
    }
    if (pathInput) {
      pathInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
          navigateTo(hiveSelect.value, pathInput.value);
        }
      };
    }
    if (upBtn) upBtn.onclick = goUp;
    if (filterInput) filterInput.oninput = renderValues;
    if (refreshBtn) refreshBtn.onclick = () => loadKey(currentHive, currentPath);
    if (copyBtn) copyBtn.onclick = copyCurrentPath;
    if (backupsBtn) backupsBtn.onclick = openBackupsModal;
    if (addValBtn) addValBtn.onclick = openCreateValueModal;
    if (addKeyBtn) addKeyBtn.onclick = openCreateKeyModal;
    if (delKeyBtn) delKeyBtn.onclick = deleteCurrentKey;
    if (saveValModalBtn) saveValModalBtn.onclick = saveModalValue;
    if (saveKeyModalBtn) saveKeyModalBtn.onclick = saveModalKey;

    await loadBookmarks();
    await navigateTo(currentHive, currentPath);
    isInitialized = true;
  };
})();

