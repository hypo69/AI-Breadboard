// Windows Backup & Libraries Manager Frontend Logic
(function () {
  let _userFoldersData = null;
  let _librariesData = [];

  async function initWindowsBackupTab() {
    console.log('[WindowsBackup] Initializing tab...');
    bindEvents();
    await loadBackupData();
  }
  window.initWindowsBackupTab = initWindowsBackupTab;

  function bindEvents() {
    const btnRefresh = document.getElementById('wb-btn-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => loadBackupData();
    }

    const btnTrigger = document.getElementById('wb-btn-trigger-backup');
    if (btnTrigger) {
      btnTrigger.onclick = async () => {
        btnTrigger.disabled = true;
        btnTrigger.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Запуск...';
        try {
          const res = await fetch('/api/v1/windows-backup/file-history/trigger', { method: 'POST' });
          const data = await res.json();
          if (res.ok) {
            alert(i18n.t('auto__file_history__e03fa7') + (data.message || 'OK'));
          } else {
            alert(i18n.t('auto___4c1c20') + (data.detail || JSON.stringify(data)));
          }
        } catch (e) {
          alert(i18n.t('auto___c4809d') + e.message);
        } finally {
          btnTrigger.disabled = false;
          btnTrigger.innerHTML = '<i class="bi bi-play-fill"></i> <span>Запустить бэкап</span>';
          await loadBackupData();
        }
      };
    }

    // Modal Create Library
    const btnOpenCreateLib = document.getElementById('wb-btn-open-create-lib');
    if (btnOpenCreateLib) {
      btnOpenCreateLib.onclick = () => {
        const modalEl = document.getElementById('wb-create-lib-modal');
        if (modalEl) {
          if (window.bootstrap?.Modal) {
            new window.bootstrap.Modal(modalEl).show();
          } else {
            modalEl.classList.add('show');
            modalEl.style.display = 'block';
          }
        }
      };
    }

    const btnExecCreateLib = document.getElementById('wb-btn-execute-create-lib');
    if (btnExecCreateLib) {
      btnExecCreateLib.onclick = async () => {
        const name = document.getElementById('wb-create-lib-name')?.value?.trim();
        const foldersRaw = document.getElementById('wb-create-lib-folders')?.value || '';
        const isPinned = document.getElementById('wb-create-lib-pinned')?.checked ?? true;

        if (!name) {
          alert(i18n.t('auto___6b272c'));
          return;
        }

        const folders = foldersRaw
          .split('\n')
          .map(f => f.trim())
          .filter(f => f.length > 0);

        btnExecCreateLib.disabled = true;
        btnExecCreateLib.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Создание...';

        try {
          const res = await fetch('/api/v1/windows-backup/libraries', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, folders, is_pinned: isPinned })
          });
          const data = await res.json();
          if (res.ok) {
            alert(`Библиотека "${name}" успешно создана!`);
            const modalEl = document.getElementById('wb-create-lib-modal');
            if (modalEl && window.bootstrap?.Modal) {
              const modalInst = window.bootstrap.Modal.getInstance(modalEl);
              if (modalInst) modalInst.hide();
            }
            await loadLibraries();
          } else {
            alert(i18n.t('auto___8361fc') + (data.detail || JSON.stringify(data)));
          }
        } catch (e) {
          alert(i18n.t('auto___c12601') + e.message);
        } finally {
          btnExecCreateLib.disabled = false;
          btnExecCreateLib.innerHTML = '<i class="bi bi-check-lg"></i> <span>Создать</span>';
        }
      };
    }

    // Modal Add Folder to Library
    const btnQuickAddFolder = document.getElementById('wb-btn-quick-add-folder');
    if (btnQuickAddFolder) {
      btnQuickAddFolder.onclick = () => {
        const select = document.getElementById('wb-add-folder-lib-select');
        if (select) {
          select.innerHTML = _librariesData.length > 0
            ? _librariesData.map(l => `<option value="${escapeHtml(l.name)}">${escapeHtml(l.name)} (${l.folder_count || 0} папок)</option>`).join('')
            : '<option value="">Нет доступных библиотек</option>';
        }
        const modalEl = document.getElementById('wb-add-folder-modal');
        if (modalEl) {
          if (window.bootstrap?.Modal) {
            new window.bootstrap.Modal(modalEl).show();
          } else {
            modalEl.classList.add('show');
            modalEl.style.display = 'block';
          }
        }
      };
    }

    const btnExecAddFolder = document.getElementById('wb-btn-execute-add-folder');
    if (btnExecAddFolder) {
      btnExecAddFolder.onclick = async () => {
        const libName = document.getElementById('wb-add-folder-lib-select')?.value;
        const folderPath = document.getElementById('wb-add-folder-path')?.value?.trim();
        const isDefault = document.getElementById('wb-add-folder-default-save')?.checked ?? false;

        if (!libName || !folderPath) {
          alert(i18n.t('auto___f66e5c'));
          return;
        }

        btnExecAddFolder.disabled = true;
        btnExecAddFolder.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Добавление...';

        try {
          const res = await fetch(`/api/v1/windows-backup/libraries/${encodeURIComponent(libName)}/folders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: folderPath, is_default_save: isDefault })
          });
          const data = await res.json();
          if (res.ok) {
            alert(`Папка успешно добавлена в библиотеку "${libName}"!`);
            const modalEl = document.getElementById('wb-add-folder-modal');
            if (modalEl && window.bootstrap?.Modal) {
              const modalInst = window.bootstrap.Modal.getInstance(modalEl);
              if (modalInst) modalInst.hide();
            }
            await loadLibraries();
          } else {
            alert(i18n.t('auto___8361fc') + (data.detail || JSON.stringify(data)));
          }
        } catch (e) {
          alert(i18n.t('auto___c12601') + e.message);
        } finally {
          btnExecAddFolder.disabled = false;
          btnExecAddFolder.innerHTML = '<i class="bi bi-check-lg"></i> <span>Добавить</span>';
        }
      };
    }

    // RAG Search & Sync
    const btnRagSync = document.getElementById('wb-btn-rag-sync');
    if (btnRagSync) {
      btnRagSync.onclick = async () => {
        btnRagSync.disabled = true;
        btnRagSync.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Синхр...';
        try {
          const res = await fetch('/api/v1/windows-backup/file-history/rag/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_force_rebuild_false_const_data_await_res_json_if_res_ok_alert_rag_n_data_total_indexed_0_else_alert__36d4ac')Ошибка синхронизации: ' + (data.detail || JSON.stringify(data)));
          }
        } catch (e) {
          alert(i18n.t('auto___c12601') + e.message);
        } finally {
          btnRagSync.disabled = false;
          btnRagSync.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i>Синхронизация';
        }
      };
    }

    const btnRagSearch = document.getElementById('wb-btn-rag-search');
    const inputRagQuery = document.getElementById('wb-rag-query');
    const performRagSearch = async () => {
      const query = inputRagQuery?.value?.trim();
      if (!query) return;

      const resultsContainer = document.getElementById('wb-rag-results');
      if (resultsContainer) {
        resultsContainer.innerHTML = '<div class="text-center text-muted py-2"><span class="spinner-border spinner-border-sm me-1"></span>Поиск в архиве...</div>';
      }

      try {
        const res = await fetch('/api/v1/windows-backup/file-history/rag/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, top_k: 5 })
        });
        const items = await res.json();
        if (resultsContainer) {
          if (!items || items.length === 0) {
            resultsContainer.innerHTML = '<div class="text-muted text-center py-2 small">Ничего не найдено по запросу</div>';
            return;
          }
          resultsContainer.innerHTML = items.map(item => `
            <div class="p-1.5 mb-1 rounded bg-dark border border-secondary" style="font-size: 0.75rem;">
              <div class="d-flex justify-content-between align-items-center mb-0.5">
                <span class="fw-bold text-info text-truncate" title="${escapeHtml(item.file_name)}">${escapeHtml(item.file_name)}</span>
                <span class="badge bg-primary-subtle text-primary">${(item.score * 100).toFixed(0)}%</span>
              </div>
              <div class="text-muted font-monospace small text-truncate" title="${escapeHtml(item.original_path)}">${escapeHtml(item.original_path)}</div>
              ${item.snippet ? `<div class="text-white-50 mt-1 small text-truncate">${escapeHtml(item.snippet)}</div>` : ''}
            </div>
          `).join('');
        }
      } catch (e) {
        if (resultsContainer) {
          resultsContainer.innerHTML = `<div class="text-danger small py-1">Ошибка поиска: ${escapeHtml(e.message)}</div>`;
        }
      }
    };

    if (btnRagSearch) btnRagSearch.onclick = performRagSearch;
    if (inputRagQuery) {
      inputRagQuery.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          performRagSearch();
        }
      };
    }

    // Audit buttons
    const btnEnableAudit = document.getElementById('wb-btn-enable-auditpol');
    if (btnEnableAudit) {
      btnEnableAudit.onclick = async () => {
        if (confirm(i18n.t('auto__auditpol_set_subcategory_file_system__f508c2'))) {
          try {
            const res = await fetch('/api/sysadmin/file-audit/policy', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ enable_success: true, enable_failure: true })
            });
            const data = await res.json();
            alert(data.success ? i18n.t('auto___98f406') : `Ошибка: ${data.error || i18n.t('auto___cd4325')}`);
            await loadBackupData();
          } catch (err) {
            alert(`Ошибка выполнения: ${err.message}`);
          }
        }
      };
    }

    const btnConfigureSacl = document.getElementById('wb-btn-configure-sacl');
    if (btnConfigureSacl) {
      btnConfigureSacl.onclick = async () => {
        const targetPath = prompt(i18n.t('auto__sacl__85d35f'), 'c:\\Users\\onela\\AppData\\Local\\AI-Breadboard');
        if (targetPath) {
          try {
            const res = await fetch('/api/sysadmin/file-audit/folder-sacl', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ path: targetPath, principal: 'Everyonei18n.t('auto__enable_true_const_data_await_res_json_alert_data_success_sacl_targetpath_data_error__64c459')Сбойi18n.t('auto__await_loadfiledeletions_catch_err_alert_err_message_const_btnrefreshfolders_document_getelementbyid__5bab3e')wb-btn-refresh-user-folders');
    if (btnRefreshFolders) {
      btnRefreshFolders.onclick = () => loadUserFoldersOverview();
    }

    // Modal Relocate Target Drive Change
    const selectRelocateDrive = document.getElementById('wb-relocate-target-drive');
    if (selectRelocateDrive) {
      selectRelocateDrive.onchange = () => {
        const driveVal = selectRelocateDrive.value;
        const folderId = document.getElementById('wb-relocate-folder-id')?.value;
        const folder = (_userFoldersData?.folders || []).find(f => f.folder_id === folderId);
        const inputPath = document.getElementById('wb-relocate-target-path');
        if (driveVal && folder && inputPath) {
          const d = driveVal.replace('/', '\\').replace(/\\+$/, '');
          const parts = folder.current_path.split('\\');
          const folderSubname = parts[parts.length - 1] || folder.name;
          const userMatch = folder.current_path.match(/Users\\([^\\]+)/i);
          const username = userMatch ? userMatch[1] : 'User';
          inputPath.value = `${d}\\Users\\${username}\\${folderSubname}`;
        }
      };
    }

    // Modal Relocate Browse Folder Button
    const btnBrowseFolder = document.getElementById('wb-btn-browse-folder');
    if (btnBrowseFolder) {
      btnBrowseFolder.onclick = async () => {
        const currentPathVal = document.getElementById('wb-relocate-target-path')?.value || '';
        const currentDriveVal = document.getElementById('wb-relocate-target-drive')?.value || '';
        const initialPath = currentPathVal || (currentDriveVal ? currentDriveVal + '\\' : '');

        btnBrowseFolder.disabled = true;
        btnBrowseFolder.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Выбор...';

        try {
          const res = await fetch(`/api/v1/windows-backup/browse-folder?initial_path=${encodeURIComponent(initialPath)}`, {
            method: 'POST'
          });
          const data = await res.json();
          if (res.ok && data.selected_path) {
            const chosenPath = data.selected_path;
            const inputPath = document.getElementById('wb-relocate-target-pathi18n.t('auto__if_inputpath_inputpath_value_chosenpath_const_driveletter_chosenpath_match_a_za_z_0_touppercase_if_driveletter_selectrelocatedrive_for_let_opt_of_selectrelocatedrive_options_if_opt_value_opt_value_touppercase_startswith_driveletter_selectrelocatedrive_value_opt_value_break_catch_err_console_error__e59400')[WindowsBackup] Browse folder error:', err);
        } finally {
          btnBrowseFolder.disabled = false;
          btnBrowseFolder.innerHTML = '<i class="bi bi-folder2-open"></i> <span>Обзор...</span>';
        }
      };
    }

    // Modal Relocate Execution
    const btnExecRelocate = document.getElementById('wb-btn-execute-relocate');
    if (btnExecRelocate) {
      btnExecRelocate.onclick = async () => {
        const folderId = document.getElementById('wb-relocate-folder-id')?.value;
        const targetDrive = document.getElementById('wb-relocate-target-drive')?.value;
        const targetPath = document.getElementById('wb-relocate-target-path')?.value?.trim();
        const deleteSource = document.getElementById('wb-relocate-delete-source')?.checked || false;

        if (!folderId || (!targetDrive && !targetPath)) {
          alert(i18n.t('auto___dbb091'));
          return;
        }

        const destDisplay = targetPath || targetDrive;
        if (!confirm(`Подтвердите перенос папки в "${destDisplay}".\nВсе файлы будут скопированы, а системные пути и библиотеки перенастроены.`)) {
          return;
        }

        btnExecRelocate.disabled = true;
        btnExecRelocate.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Перенос...';

        try {
          const res = await fetch('/api/v1/windows-backup/user-folders/relocate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              folder_id: folderId,
              target_drive_letter: targetDrive || null,
              target_path: targetPath || null,
              delete_source_after: deleteSource
            })
          });

          const data = await res.json();
          if (res.ok && data.success) {
            alert(data.message || i18n.t('auto___6d6dc0'));
            const modalEl = document.getElementById('wb-relocate-modal');
            if (modalEl && window.bootstrap?.Modal) {
              const modalInstance = window.bootstrap.Modal.getInstance(modalEl);
              if (modalInstance) modalInstance.hide();
            }
            await loadBackupData();
          } else {
            alert(i18n.t('auto___268b58') + (data.detail || data.message || JSON.stringify(data)));
          }
        } catch (e) {
          alert(i18n.t('auto___f9eada') + e.message);
        } finally {
          btnExecRelocate.disabled = false;
          btnExecRelocate.innerHTML = '<i class="bi bi-check-circle"></i> <span>Выполнить перенос</span>';
        }
      };
    }
  }

  async function loadBackupData() {
    await Promise.allSettled([
      loadHealthReport(),
      loadLibraries(),
      loadFileHistoryStatus(),
      loadUserFoldersOverview(),
      loadVssSnapshots(),
      loadFileDeletions()
    ]);
  }

  async function loadHealthReport() {
    try {
      const res = await fetch('/api/v1/windows-backup/health');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const elHealth = document.getElementById('wb-val-health');
      const elBadge = document.getElementById('wb-badge-status');
      const elSub = document.getElementById('wb-sub-health');

      const score = data.health_score ?? 0;
      if (elHealth) elHealth.textContent = `${score} / 100`;
      if (elBadge) {
        elBadge.textContent = score >= 80 ? i18n.t('auto___97b864') : score >= 50 ? i18n.t('auto___5f5f86') : i18n.t('auto___238b17');
        elBadge.className = `badge bg-${score >= 80 ? 'success' : score >= 50 ? 'warning' : 'danger'}`;
      }
      if (elSub) {
        elSub.textContent = data.service_running ? i18n.t('auto___b3fcb0') : i18n.t('auto___c4e687');
      }

      const recList = document.getElementById('wb-recommendations-list');
      if (recList && Array.isArray(data.recommendations)) {
        if (data.recommendations.length === 0) {
          recList.innerHTML = '<li class="text-success small"><i class="bi bi-check-circle me-1"></i>Все проверки безопасности данных пройдены успешно.</li>';
        } else {
          recList.innerHTML = data.recommendations.map(r => `
            <li class="mb-1.5 text-warning d-flex align-items-start gap-1">
              <i class="bi bi-exclamation-triangle-fill text-warning flex-shrink-0 mt-0.5"></i>
              <span>${escapeHtml(r)}</span>
            </li>
          `).join('');
        }
      }
    } catch (e) {
      console.warn('[WindowsBackup] Error loading health:', e);
    }
  }

  async function loadLibraries() {
    const tbody = document.getElementById('wb-libraries-body');
    const countBadge = document.getElementById('wb-lib-count');
    const valLibs = document.getElementById('wb-val-libraries');

    try {
      const res = await fetch('/api/v1/windows-backup/librariesi18n.t('auto__if_res_ok_throw_new_error_http_res_status_const_libs_await_res_json_librariesdata_libs_if_countbadge_countbadge_textcontent_libs_length_if_vallibs_vallibs_textcontent_libs_length_if_tbody_return_if_libs_libs_length_0_tbody_innerhtml__80a1e4')<tr><td colspan="4" class="text-center py-3 text-muted">Библиотеки не найдены</td></tr>';
        return;
      }

      tbody.innerHTML = libs.map(lib => {
        const foldersHtml = (lib.folders || []).map(f => {
          const path = typeof f === 'string' ? f : f.folder_path;
          const exists = typeof f === 'object' ? f.exists : true;
          return `
            <div class="text-break font-monospace small d-flex align-items-center gap-1 ${exists ? 'text-white' : 'text-danger'}">
              <i class="bi ${exists ? 'bi-folder-check text-info' : 'bi-folder-x text-danger'}"></i>
              <span>${escapeHtml(path)}</span>
              ${!exists ? '<span class="badge bg-danger-subtle text-danger py-0 px-1" style="font-size:0.6rem;">Недоступна</span>' : ''}
            </div>
          `;
        }).join('') || '<span class="text-muted small">Нет папок</span>';

        return `
          <tr>
            <td class="fw-bold text-white">
              <i class="bi bi-collection me-1 text-primary"></i>${escapeHtml(lib.name)}
            </td>
            <td>${foldersHtml}</td>
            <td class="text-break font-monospace small text-info">
              ${lib.default_save_folder ? escapeHtml(lib.default_save_folder) : '<span class="text-muted">—</span>'}
            </td>
            <td>
              <span class="badge ${lib.is_pinned ? 'bg-primary' : 'bg-secondary'}">${lib.is_pinned ? i18n.t('auto___8d2fab') : i18n.t('auto___f82a82')}</span>
            </td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-danger">Ошибка: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  async function loadFileHistoryStatus() {
    try {
      const res = await fetch('/api/v1/windows-backup/file-history/status');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const elService = document.getElementById('wb-val-service');
      const elSubService = document.getElementById('wb-sub-service');
      const elTarget = document.getElementById('wb-fh-target');
      const elConfig = document.getElementById('wb-fh-config');
      const elInterval = document.getElementById('wb-fh-interval');
      const elRetention = document.getElementById('wb-fh-retention');
      const elLast = document.getElementById('wb-fh-last-backup');

      const isRunning = data.is_service_running;
      if (elService) {
        elService.textContent = isRunning ? i18n.t('auto___e6156d') : i18n.t('auto___6af536');
        elService.className = `wb-card-value ${isRunning ? 'text-success' : 'text-dangeri18n.t('auto__if_elsubservice_elsubservice_textcontent_data_service_start_type__afacbc')Manual'}`;
      }

      const cfg = data.config;
      if (cfg) {
        if (elTarget) elTarget.textContent = cfg.target_path || cfg.target_url || i18n.t('auto___1411ab');
        if (elConfig) elConfig.textContent = cfg.config_file_path || i18n.t('auto___12995c');
        if (elInterval) elInterval.textContent = cfg.backup_interval_minutes ? `${cfg.backup_interval_minutes} мин.` : i18n.t('auto__1__a7e3d1');
        if (elRetention) elRetention.textContent = cfg.retention_policy || i18n.t('auto___deb9e5');
        if (elLast) elLast.textContent = cfg.last_backup_time || i18n.t('auto___096309');
      } else {
        if (elTarget) elTarget.textContent = i18n.t('auto___20bf4c');
        if (elConfig) elConfig.textContent = '—';
        if (elInterval) elInterval.textContent = '—';
        if (elRetention) elRetention.textContent = '—';
        if (elLast) elLast.textContent = '—';
      }
    } catch (e) {
      console.warn('[WindowsBackup] Error loading File History status:', e);
    }
  }

  async function loadVssSnapshots() {
    const tbody = document.getElementById('wb-vss-body');
    const countBadge = document.getElementById('wb-vss-count');

    try {
      const res = await fetch('/api/v1/windows-backup/vss/snapshotsi18n.t('auto__if_res_ok_throw_new_error_http_res_status_const_snapshots_await_res_json_if_countbadge_countbadge_textcontent_snapshots_length_if_tbody_return_if_snapshots_snapshots_length_0_tbody_innerhtml__b2bfac')<tr><td colspan="4" class="text-center py-3 text-muted">Теневые копии (VSS) не найдены</td></tr>';
        return;
      }

      tbody.innerHTML = snapshots.map(s => `
        <tr>
          <td class="font-monospace small text-truncate" style="max-width: 150px;" title="${escapeHtml(s.snapshot_id || '')}">
            ${escapeHtml(s.snapshot_id || '—')}
          </td>
          <td class="fw-semibold text-info">${escapeHtml(s.original_volume || '—')}</td>
          <td class="small text-muted">${escapeHtml(s.creation_time || '—')}</td>
          <td><span class="badge bg-success">${escapeHtml(s.status || 'OK')}</span></td>
        </tr>
      `).join('');
    } catch (e) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-danger">Ошибка: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  async function loadFileDeletions() {
    try {
      const res = await fetch('/api/sysadmin/file-audit/deletions?hours=24&limit=100&deletions_only=true');
      if (!res.ok) return;
      const data = await res.json();
      const events = data.events || [];

      const tbody = document.getElementById('wb-deletions-tbody');
      const badge = document.getElementById('wb-deletions-badge');
      const valDeletions = document.getElementById('wb-val-deletionsi18n.t('auto__if_badge_badge_innertext_events_length_if_valdeletions_valdeletions_innertext_events_length_if_tbody_if_events_length_0_tbody_innerhtml__d7ec51')<tr><td colspan="5" class="text-center text-muted p-3">События удаления (4663/4660) не зафиксированы или аудит не включен</td></tr>';
          return;
        }
        tbody.innerHTML = events.slice(0, 30).map((e, idx) => `
          <tr class="wb-deletion-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto___5b69eb')>
            <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
            <td class="font-monospace fw-semibold ${e.event_id === 4660 ? 'text-danger' : 'text-warning'}">${e.event_id}</td>
            <td class="font-monospace text-truncate text-white" style="max-width: 260px;" title="${escapeHtml(e.object_name)}">${escapeHtml(e.object_name.split('\\').pop() || e.object_name)}</td>
            <td class="small text-info text-truncate" style="max-width: 140px;" title="${escapeHtml(e.process_name)}">${escapeHtml(e.process_name ? e.process_name.split('\\').pop() : 'N/A')}</td>
            <td class="small text-muted">${escapeHtml(e.subject_user_name || 'SYSTEM')}</td>
          </tr>
        `).join('');

        tbody.querySelectorAll('.wb-deletion-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const e = events[idx];
            if (!e) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '🗑️i18n.t('auto__title_e_object_name_split__d97fad')\\').pop() || e.object_name}`,
                subtitle: `Event ID: ${e.event_id} | ${e.timestamp}`,
                tableType: 'security_event',
                badges: [
                  { text: `Event ${e.event_id}`, class: e.event_id === 4660 ? 'badge bg-danger' : 'badge bg-warning text-dark' },
                  { text: e.status || 'Success', class: 'badge bg-success' }
                ],
                metadata: [
                  { label: i18n.t('auto___6ebcae'), value: e.object_name },
                  { label: i18n.t('auto___9748fe'), value: e.object_type || 'File' },
                  { label: i18n.t('auto___2b3e8f'), value: e.process_name || i18n.t('auto___3b3c4f') },
                  { label: i18n.t('auto_pid__763699'), value: e.process_id ? String(e.process_id) : 'N/A' },
                  { label: i18n.t('auto___51aff1'), value: `${e.subject_domain_name}\\${e.subject_user_name}` },
                  { label: i18n.t('auto__handleid_9d5304'), value: e.handle_id || 'N/A' },
                  { label: i18n.t('auto___cec473'), value: e.access_mask || 'DELETE (0x10000)' }
                ],
                rawTitle: i18n.t('auto__security_log_384465'),
                rawContent: e.raw_message || JSON.stringify(e, null, 2),
                requestData: e
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[WindowsBackup] Failed to fetch deletion events:', e);
    }
  }

  async function loadUserFoldersOverview() {
    const tbody = document.getElementById('wb-user-folders-tbody');
    const totalSizeBadge = document.getElementById('wb-total-user-size');
    const drivesList = document.getElementById('wb-drives-list');

    try {
      const res = await fetch('/api/v1/windows-backup/user-folders/overviewi18n.t('auto__if_res_ok_throw_new_error_http_res_status_const_data_await_res_json_userfoldersdata_data_if_totalsizebadge_totalsizebadge_textcontent_data_total_user_size_gb_data_total_user_size_mb_if_driveslist_if_data_drives_data_drives_length_0_driveslist_innerhtml__2de266')<span class="text-muted">Диски не обнаружены</span>';
        } else {
          drivesList.innerHTML = data.drives.map(d => `
            <div class="px-2 py-1 rounded border ${d.is_system_drive ? 'border-info bg-dark' : 'border-secondary bg-dark'} d-flex align-items-center gap-1.5">
              <i class="bi ${d.is_system_drive ? 'bi-hdd-fill text-info' : 'bi-hdd text-success'}"></i>
              <span class="fw-bold">${escapeHtml(d.drive_letter)}</span>
              <span class="text-muted">(${escapeHtml(d.fstype)})</span>:
              <span class="text-success fw-semiboldi18n.t('auto__d_free_space_gb_span_span_class__f43e88')text-muted small">из ${d.total_space_gb} ГБ</span>
              ${d.is_system_drive ? '<span class="badge bg-info-subtle text-info py-0 px-1" style="font-size: 0.65rem;">System</span>' : ''}
            </div>
          `).join('');
        }
      }

      if (!tbody) return;
      if (!data.folders || data.folders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-3 text-muted">Пользовательские папки не найдены</td></tr>';
        return;
      }

      tbody.innerHTML = data.folders.map(f => {
        const suitableDrives = (data.available_target_drives || []).filter(d => {
          const folderDrive = f.drive_letter.replace('\\', '');
          const targetDrive = d.drive_letter.replace('\\', '');
          return folderDrive !== targetDrive && d.free_space_gb >= (f.size_gb + 1.0);
        });

        const canRelocate = suitableDrives.length > 0;

        return `
          <tr>
            <td class="fw-bold text-white">
              <i class="bi bi-folder2-open me-1 text-primary"></i>${escapeHtml(f.name)}
            </td>
            <td class="font-monospace text-muted small text-truncate" style="max-width: 250px;" title="${escapeHtml(f.current_path)}">
              ${escapeHtml(f.current_path)}
            </td>
            <td>
              <span class="badge ${f.drive_letter.startsWith('C') ? 'bg-secondary' : 'bg-primary'}">${escapeHtml(f.drive_letter)}</span>
            </td>
            <td class="fw-semibold font-monospace ${f.size_gb > 1.0 ? 'text-warning' : 'text-info'}i18n.t('auto__f_size_gb_0_01_f_size_gb_f_size_mb_td_td_class__0f7dc2')small text-muted font-monospace">${f.file_count}</td>
            <td class="text-end">
              <button class="btn btn-xs ${canRelocate ? 'btn-outline-warning' : 'btn-outline-secondary'} py-0 px-2 wb-btn-relocate-modal" 
                      data-folder-id="${escapeHtml(f.folder_id)}"
                      ${!canRelocate ? 'title=i18n.t('auto___8f78e3')' : 'title=i18n.t('auto___f340a5')'}
                      style="font-size: 0.72rem;">
                <i class="bi bi-box-arrow-right me-1"></i>Перенести
              </button>
            </td>
          </tr>
        `;
      }).join('');

      tbody.querySelectorAll('.wb-btn-relocate-modal').forEach(btn => {
        btn.onclick = () => {
          const fid = btn.getAttribute('data-folder-id');
          openRelocateModal(fid);
        };
      });

    } catch (e) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-danger">Ошибка загрузки: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  function openRelocateModal(folderId) {
    if (!_userFoldersData) return;
    const folder = (_userFoldersData.folders || []).find(f => f.folder_id === folderId);
    if (!folder) return;

    const elId = document.getElementById('wb-relocate-folder-id');
    const elName = document.getElementById('wb-relocate-folder-name');
    const elPath = document.getElementById('wb-relocate-folder-path');
    const elSize = document.getElementById('wb-relocate-folder-size');
    const selectDrive = document.getElementById('wb-relocate-target-drive');
    const elHint = document.getElementById('wb-relocate-drive-hinti18n.t('auto__if_elid_elid_value_folder_folder_id_if_elname_elname_textcontent_folder_name_if_elpath_elpath_textcontent_folder_current_path_if_elsize_elsize_textcontent_folder_size_gb_0_01_folder_size_gb_folder_size_mb_folder_file_count_const_inputpath_document_getelementbyid__987ad5')wb-relocate-target-path');
    if (inputPath) inputPath.value = '';

    if (selectDrive) {
      selectDrive.innerHTML = '<option value="">-- Выберите диск --</option>';
      const folderDrive = folder.drive_letter.replace('\\', '').toUpperCase();
      let firstSuitableDrive = null;

      (_userFoldersData.drives || []).forEach(d => {
        const dLetter = d.drive_letter.replace('\\', '').toUpperCase();
        if (dLetter === folderDrive) return;

        const isEnough = d.free_space_gb >= (folder.size_gb + 1.0);
        const opt = document.createElement('optioni18n.t('auto__opt_value_d_drive_letter_opt_textcontent_d_drive_letter_d_fstype_d_free_space_gb_d_total_space_gb_isenough__28ec5b')✅ Достаточно места' : i18n.t('auto___db6a47')}`;
        if (!isEnough) {
          opt.disabled = true;
        } else if (!firstSuitableDrive) {
          firstSuitableDrive = d.drive_letter;
        }
        selectDrive.appendChild(opt);
      });

      if (firstSuitableDrive) {
        selectDrive.value = firstSuitableDrive;
        if (inputPath) {
          const d = firstSuitableDrive.replace('/', '\\').replace(/\\+$/, '');
          const parts = folder.current_path.split('\\');
          const folderSubname = parts[parts.length - 1] || folder.name;
          const userMatch = folder.current_path.match(/Users\\([^\\]+)/i);
          const username = userMatch ? userMatch[1] : 'User';
          inputPath.value = `${d}\\Users\\${username}\\${folderSubname}`;
        }
      }
    }

    if (elHint) {
      elHint.textContent = i18n.t('auto___3416bd') + (folder.size_gb + 1.0).toFixed(2) + i18n.t('auto__1__aa3cbb');
    }

    const modalEl = document.getElementById('wb-relocate-modal');
    if (modalEl) {
      if (window.bootstrap?.Modal) {
        new window.bootstrap.Modal(modalEl).show();
      } else {
        modalEl.classList.add('show');
        modalEl.style.display = 'block';
      }
    }
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
})();
