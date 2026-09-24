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
            alert('Архивация File History успешно запущена: ' + (data.message || 'OK'));
          } else {
            alert('Ошибка запуска: ' + (data.detail || JSON.stringify(data)));
          }
        } catch (e) {
          alert('Сетевая ошибка при запуске архивации: ' + e.message);
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
          alert('Укажите название библиотеки');
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
            alert('Ошибка: ' + (data.detail || JSON.stringify(data)));
          }
        } catch (e) {
          alert('Ошибка сети: ' + e.message);
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
          alert('Выберите библиотеку и укажите путь к папке');
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
            alert('Ошибка: ' + (data.detail || JSON.stringify(data)));
          }
        } catch (e) {
          alert('Ошибка сети: ' + e.message);
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
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force_rebuild: false })
          });
          const data = await res.json();
          if (res.ok) {
            alert(`Синхронизация RAG завершена!\nПроиндексировано: ${data.total_indexed || 0} версий файлов.`);
          } else {
            alert('Ошибка синхронизации: ' + (data.detail || JSON.stringify(data)));
          }
        } catch (e) {
          alert('Ошибка сети: ' + e.message);
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
        if (confirm('Включить системный аудит файловой системы (auditpol /set /subcategory:File System)?')) {
          try {
            const res = await fetch('/api/sysadmin/file-audit/policy', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ enable_success: true, enable_failure: true })
            });
            const data = await res.json();
            alert(data.success ? 'Аудит файловой системы успешно активирован!' : `Ошибка: ${data.error || 'Сбой'}`);
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
        const targetPath = prompt('Укажите путь к папке для настройки SACL аудита удаления:', 'c:\\Users\\onela\\AppData\\Local\\AI-Breadboard');
        if (targetPath) {
          try {
            const res = await fetch('/api/sysadmin/file-audit/folder-sacl', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ path: targetPath, principal: 'Everyone', enable: true })
            });
            const data = await res.json();
            alert(data.Success ? `SACL успешно настроен для ${targetPath}!` : `Ошибка: ${data.Error || 'Сбой'}`);
            await loadFileDeletions();
          } catch (err) {
            alert(`Ошибка: ${err.message}`);
          }
        }
      };
    }

    const btnRefreshFolders = document.getElementById('wb-btn-refresh-user-folders');
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
            const inputPath = document.getElementById('wb-relocate-target-path');
            if (inputPath) inputPath.value = chosenPath;

            // Синхронизируем выпадающий список дисков
            const driveLetter = chosenPath.match(/^[a-zA-Z]:/)?.[0]?.toUpperCase();
            if (driveLetter && selectRelocateDrive) {
              for (let opt of selectRelocateDrive.options) {
                if (opt.value && opt.value.toUpperCase().startsWith(driveLetter)) {
                  selectRelocateDrive.value = opt.value;
                  break;
                }
              }
            }
          }
        } catch (err) {
          console.error('[WindowsBackup] Browse folder error:', err);
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
          alert('Пожалуйста, выберите целевой диск или укажите целевую папку для переноса.');
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
            alert(data.message || 'Перенос успешно завершен!');
            const modalEl = document.getElementById('wb-relocate-modal');
            if (modalEl && window.bootstrap?.Modal) {
              const modalInstance = window.bootstrap.Modal.getInstance(modalEl);
              if (modalInstance) modalInstance.hide();
            }
            await loadBackupData();
          } else {
            alert('Ошибка переноса: ' + (data.detail || data.message || JSON.stringify(data)));
          }
        } catch (e) {
          alert('Сетевая ошибка при переносе: ' + e.message);
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
        elBadge.textContent = score >= 80 ? 'Готов' : score >= 50 ? 'Внимание' : 'Критично';
        elBadge.className = `badge bg-${score >= 80 ? 'success' : score >= 50 ? 'warning' : 'danger'}`;
      }
      if (elSub) {
        elSub.textContent = data.service_running ? 'Служба активна' : 'Служба остановлена';
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
      const res = await fetch('/api/v1/windows-backup/libraries');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const libs = await res.json();
      _librariesData = libs || [];

      if (countBadge) countBadge.textContent = `${libs.length} шт.`;
      if (valLibs) valLibs.textContent = `${libs.length}`;

      if (!tbody) return;
      if (!libs || libs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Библиотеки не найдены</td></tr>';
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
              <span class="badge ${lib.is_pinned ? 'bg-primary' : 'bg-secondary'}">${lib.is_pinned ? 'Да' : 'Нет'}</span>
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
        elService.textContent = isRunning ? 'Работает' : 'Остановлена';
        elService.className = `wb-card-value ${isRunning ? 'text-success' : 'text-danger'}`;
      }
      if (elSubService) {
        elSubService.textContent = `Запуск: ${data.service_start_type || 'Manual'}`;
      }

      const cfg = data.config;
      if (cfg) {
        if (elTarget) elTarget.textContent = cfg.target_path || cfg.target_url || 'Не настроено';
        if (elConfig) elConfig.textContent = cfg.config_file_path || 'Стандартный профиль';
        if (elInterval) elInterval.textContent = cfg.backup_interval_minutes ? `${cfg.backup_interval_minutes} мин.` : 'По умолчанию (1 ч)';
        if (elRetention) elRetention.textContent = cfg.retention_policy || 'Всегда';
        if (elLast) elLast.textContent = cfg.last_backup_time || 'Нет записей';
      } else {
        if (elTarget) elTarget.textContent = 'Конфигурация отсутствует';
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
      const res = await fetch('/api/v1/windows-backup/vss/snapshots');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const snapshots = await res.json();

      if (countBadge) countBadge.textContent = `${snapshots.length} шт.`;

      if (!tbody) return;
      if (!snapshots || snapshots.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Теневые копии (VSS) не найдены</td></tr>';
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
      const valDeletions = document.getElementById('wb-val-deletions');

      if (badge) badge.innerText = `${events.length} удалений`;
      if (valDeletions) valDeletions.innerText = events.length;

      if (tbody) {
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted p-3">События удаления (4663/4660) не зафиксированы или аудит не включен</td></tr>';
          return;
        }
        tbody.innerHTML = events.slice(0, 30).map((e, idx) => `
          <tr class="wb-deletion-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детального анализа удаления">
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
                icon: '🗑️',
                title: `Удаление: ${e.object_name.split('\\').pop() || e.object_name}`,
                subtitle: `Event ID: ${e.event_id} | ${e.timestamp}`,
                tableType: 'security_event',
                badges: [
                  { text: `Event ${e.event_id}`, class: e.event_id === 4660 ? 'badge bg-danger' : 'badge bg-warning text-dark' },
                  { text: e.status || 'Success', class: 'badge bg-success' }
                ],
                metadata: [
                  { label: 'Целевой объект', value: e.object_name },
                  { label: 'Тип объекта', value: e.object_type || 'File' },
                  { label: 'Процесс-инициатор', value: e.process_name || 'Не указан' },
                  { label: 'PID процесса', value: e.process_id ? String(e.process_id) : 'N/A' },
                  { label: 'Пользователь', value: `${e.subject_domain_name}\\${e.subject_user_name}` },
                  { label: 'Дескриптор HandleId', value: e.handle_id || 'N/A' },
                  { label: 'Маска доступа', value: e.access_mask || 'DELETE (0x10000)' }
                ],
                rawTitle: 'Полное сообщение Security Log',
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
      const res = await fetch('/api/v1/windows-backup/user-folders/overview');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      _userFoldersData = data;

      if (totalSizeBadge) {
        totalSizeBadge.textContent = `Общий объем: ${data.total_user_size_gb} ГБ (${data.total_user_size_mb} МБ)`;
      }

      if (drivesList) {
        if (!data.drives || data.drives.length === 0) {
          drivesList.innerHTML = '<span class="text-muted">Диски не обнаружены</span>';
        } else {
          drivesList.innerHTML = data.drives.map(d => `
            <div class="px-2 py-1 rounded border ${d.is_system_drive ? 'border-info bg-dark' : 'border-secondary bg-dark'} d-flex align-items-center gap-1.5">
              <i class="bi ${d.is_system_drive ? 'bi-hdd-fill text-info' : 'bi-hdd text-success'}"></i>
              <span class="fw-bold">${escapeHtml(d.drive_letter)}</span>
              <span class="text-muted">(${escapeHtml(d.fstype)})</span>:
              <span class="text-success fw-semibold">${d.free_space_gb} ГБ своб.</span>
              <span class="text-muted small">из ${d.total_space_gb} ГБ</span>
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
            <td class="fw-semibold font-monospace ${f.size_gb > 1.0 ? 'text-warning' : 'text-info'}">
              ${f.size_gb >= 0.01 ? `${f.size_gb} ГБ` : `${f.size_mb} МБ`}
            </td>
            <td class="small text-muted font-monospace">${f.file_count}</td>
            <td class="text-end">
              <button class="btn btn-xs ${canRelocate ? 'btn-outline-warning' : 'btn-outline-secondary'} py-0 px-2 wb-btn-relocate-modal" 
                      data-folder-id="${escapeHtml(f.folder_id)}"
                      ${!canRelocate ? 'title="Нет подходящих дисков с достаточным местом"' : 'title="Перенести на другой диск"'}
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
    const elHint = document.getElementById('wb-relocate-drive-hint');

    if (elId) elId.value = folder.folder_id;
    if (elName) elName.textContent = folder.name;
    if (elPath) elPath.textContent = folder.current_path;
    if (elSize) elSize.textContent = `${folder.size_gb >= 0.01 ? `${folder.size_gb} ГБ` : `${folder.size_mb} МБ`} (${folder.file_count} файлов)`;

    const inputPath = document.getElementById('wb-relocate-target-path');
    if (inputPath) inputPath.value = '';

    if (selectDrive) {
      selectDrive.innerHTML = '<option value="">-- Выберите диск --</option>';
      const folderDrive = folder.drive_letter.replace('\\', '').toUpperCase();
      let firstSuitableDrive = null;

      (_userFoldersData.drives || []).forEach(d => {
        const dLetter = d.drive_letter.replace('\\', '').toUpperCase();
        if (dLetter === folderDrive) return;

        const isEnough = d.free_space_gb >= (folder.size_gb + 1.0);
        const opt = document.createElement('option');
        opt.value = d.drive_letter;
        opt.textContent = `${d.drive_letter} (${d.fstype}) — Свободно: ${d.free_space_gb} ГБ из ${d.total_space_gb} ГБ ${isEnough ? '✅ Достаточно места' : '⚠️ Мало места'}`;
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
      elHint.textContent = 'Требуется свободного места: минимум ' + (folder.size_gb + 1.0).toFixed(2) + ' ГБ (размер + 1 ГБ резерва).';
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
