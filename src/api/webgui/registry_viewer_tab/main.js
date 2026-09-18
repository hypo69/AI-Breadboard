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
        <span class="text-muted small me-2"><i class="bi bi-bookmark-star-fill text-warning me-1"></i> Закладки:</span>
      ` + bookmarks.map(b => `
        <button class="reg-bookmark-btn" data-hive="${b.hive}" data-path="${b.path}" title="${b.description || ''}">
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
    const valuesCountBadge = document.getElementById('reg-values-count-badge');

    if (badge) badge.innerText = `● Чтение ${hive}...`;

    try {
      const url = `/api/registry/key?hive=${encodeURIComponent(hive)}&path=${encodeURIComponent(path)}`;
      const res = await fetch(url);
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      currentKeyData = await res.json();

      // Рендер подразделов (subkeys)
      const subkeys = currentKeyData.subkeys || [];
      if (subkeysCountBadge) subkeysCountBadge.innerText = subkeys.length;

      if (subkeys.length === 0) {
        subkeysList.innerHTML = '<div class="text-muted text-center py-4 small">Нет подразделов</div>';
      } else {
        subkeysList.innerHTML = subkeys.map(sk => `
          <div class="reg-tree-item" data-subkey="${sk}" title="${sk}">
            <i class="bi bi-folder-fill text-warning"></i>
            <span class="text-truncate">${sk}</span>
          </div>
        `).join('');

        subkeysList.querySelectorAll('.reg-tree-item').forEach(item => {
          item.onclick = () => {
            const subkey = item.getAttribute('data-subkey');
            const newPath = currentPath ? `${currentPath}\\${subkey}` : subkey;
            navigateTo(currentHive, newPath);
          };
        });
      }

      // Рендер параметров (values)
      renderValues();

      if (badge) {
        badge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
        badge.innerText = `● Реестр: ${hive}`;
      }
    } catch (err) {
      console.error('[RegistryViewerTab] Error loading key:', err);
      if (valuesTbody) {
        valuesTbody.innerHTML = `<tr><td colspan="3" class="text-center text-danger p-4"><i class="bi bi-exclamation-triangle-fill me-1"></i> Ошибка чтения ветки: ${err.message}</td></tr>`;
      }
      if (subkeysList) {
        subkeysList.innerHTML = `<div class="text-danger text-center py-4 small">${err.message}</div>`;
      }
      if (badge) {
        badge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
        badge.innerText = '● Ошибка доступа';
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

      const isDefault = v.name === '(Default / По умолчанию)' || v.name === '(Default)';
      const rawNameAttr = escapeHtml(isDefault ? '' : v.name);

      return `
        <tr class="reg-val-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-объяснения параметра реестра">
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
            <button class="btn btn-xs btn-outline-info py-0 px-2 me-1 btn-edit-val" data-idx="${idx}" title="Редактировать">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-xs btn-outline-danger py-0 px-2 btn-del-val" data-name="${rawNameAttr}" title="Удалить">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Привязка кликабельности всей строки к AITableModal
    valuesTbody.querySelectorAll('.reg-val-row').forEach(row => {
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
              { label: 'Параметр', value: v.name || '(По умолчанию)' },
              { label: 'Тип данных', value: v.type_name },
              { label: 'Ветка реестра (Hive)', value: currentHive },
              { label: 'Путь к разделу', value: currentPath, isCode: true, fullWidth: true },
              { label: 'Значение', value: String(v.data ?? ''), isCode: true, fullWidth: true }
            ],
            rawTitle: 'Значение параметра',
            rawContent: typeof v.data === 'object' ? JSON.stringify(v.data, null, 2) : String(v.data ?? ''),
            requestData: {
              hive: currentHive,
              path: currentPath,
              name: v.name,
              type: v.type_name,
              data: v.data
            }
          });
        }
      };
    });

    // Привязка событий кнопок редактирования и удаления параметров
    valuesTbody.querySelectorAll('.btn-edit-val').forEach(btn => {
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
    const isDefault = !valObj.name || valObj.name === '(Default / По умолчанию)' || valObj.name === '(Default)';
    const nameInput = document.getElementById('regModalValueName');
    const typeSelect = document.getElementById('regModalValueType');
    const dataInput = document.getElementById('regModalValueData');
    const title = document.getElementById('regValueModalTitle');

    if (title) title.innerText = '✏️ Редактирование параметра';
    if (nameInput) {
      nameInput.value = isDefault ? '' : valObj.name;
      nameInput.disabled = true; // имя существующего параметра не меняем
    }
    if (typeSelect) typeSelect.value = valObj.type_name || 'REG_SZ';
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

    if (title) title.innerText = '➕ Создание нового параметра';
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

      const modalEl = document.getElementById('regValueModal');
      if (modalEl && window.bootstrap) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }

      await loadKey(currentHive, currentPath);
    } catch (e) {
      alert(`Ошибка сохранения параметра: ${e.message}`);
    }
  }

  async function confirmDeleteValue(name) {
    const displayName = name ? `'${name}'` : '(По умолчанию)';
    if (!confirm(`Вы действительно хотите удалить параметр ${displayName}? Перед удалением будет автоматически создан бэкап.`)) {
      return;
    }

    try {
      const res = await fetch('/api/registry/value', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hive: currentHive,
          path: currentPath,
          name: name,
          create_backup: true
        })
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      await loadKey(currentHive, currentPath);
    } catch (e) {
      alert(`Ошибка удаления параметра: ${e.message}`);
    }
  }

  function openCreateKeyModal() {
    const keyNameInput = document.getElementById('regModalNewKeyName');
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
      alert('Введите имя подраздела');
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

      const modalEl = document.getElementById('regKeyModal');
      if (modalEl && window.bootstrap) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }

      await loadKey(currentHive, currentPath);
    } catch (e) {
      alert(`Ошибка создания ключа: ${e.message}`);
    }
  }

  async function deleteCurrentKey() {
    if (!currentPath) {
      alert('Нельзя удалить корневой раздел');
      return;
    }

    if (!confirm(`ВНИМАНИЕ: Вы действительно хотите удалить раздел '${currentHive}\\${currentPath}' со всеми подразделами и значениями? Будет создан снимок резервной копии.`)) {
      return;
    }

    try {
      const res = await fetch('/api/registry/key', {
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

      goUp();
    } catch (e) {
      alert(`Ошибка удаления раздела: ${e.message}`);
    }
  }

  async function openBackupsModal() {
    const modalEl = document.getElementById('regBackupsModal');
    const tbody = document.getElementById('reg-backups-tbody');

    if (modalEl && window.bootstrap) {
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }

    if (tbody) tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Загрузка истории снимков...</td></tr>';

    try {
      const res = await fetch('/api/registry/backups');
      if (!res.ok) throw new Error('Ошибка загрузки бэкапов');
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
          const backupId = btn.getAttribute('data-id');
          if (!confirm(`Восстановить реестр из снимка ${backupId}?`)) return;

          try {
            const rRes = await fetch(`/api/registry/restore?backup_id=${encodeURIComponent(backupId)}`, {
              method: 'POST'
            });
            if (!rRes.ok) {
              const err = await rRes.json().catch(() => ({}));
              throw new Error(err.detail || `HTTP ${rRes.status}`);
            }
            alert('Реестр успешно восстановлен из резервной копии!');
            await loadKey(currentHive, currentPath);
          } catch (err) {
            alert(`Ошибка восстановления: ${err.message}`);
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

