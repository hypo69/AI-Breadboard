/**
 * ===============================================================================
 * Process Name: Auto-Logging Manager Interface Controller
 * ===============================================================================
 * Description:
 *   Модульный контроллер вкладки управления автологгированием и CSV-логами в /tc.
 *   Обеспечивает опрос REST API (/api/autolog), сохранение конфигурации,
 *   управление воркерами, интерактивную визуализацию и выгрузку CSV-файлов.
 *
 * File: main.js
 * Project: AI-Breadboard
 * Module: WebInterface.AutoLogTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * ===============================================================================
 */

(function () {
  'use strict';

  console.log('🚀 [AutoLogTab] Initializing Auto-Logging Management Controller...');

  // Preset intervals for quick selection
  const INTERVAL_PRESETS = [
    { label: '5 сек (5 seconds)', value: '5 seconds' },
    { label: '10 сек (10 seconds)', value: '10 seconds' },
    { label: '30 сек (30 seconds)', value: '30 seconds' },
    { label: '1 мин (1 minute)', value: '1 minute' },
    { label: '5 мин (5 minutes)', value: '5 minutes' },
    { label: '10 мин (10 minutes)', value: '10 minutes' },
    { label: '30 мин (30 minutes)', value: '30 minutes' },
    { label: '1 час (1 hour)', value: '1 hour' },
    { label: '6 часов (6 hours)', value: '6 hours' },
    { label: '24 часа (24 hours)', value: '24 hours' },
    { label: '1 день (1 day)', value: '1 day' },
    { label: '7 дней (7 days)', value: '7 days' },
  ];

  // App readable metadata (icons and titles)
  const APP_META = {
    system_inspector: { icon: '🖥️', title: 'System Inspector (Потребление ресурсов)' },
    hardware_monitor: { icon: '⚡', title: 'Hardware Sensors (Датчики оборудования)' },
    librehardwaremonitor: { icon: '🌡️', title: 'LibreHardwareMonitor API' },
    smartmontools: { icon: '💾', title: 'Smartmontools (SMART дисков)' },
    website_monitor: { icon: '🌐', title: 'Website Intelligence & Heartbeat' },
    gcloud_monitor: { icon: '☁️', title: 'Google Cloud Observability' },
    cloudflared_monitor: { icon: '🛡️', title: 'Cloudflared Tunnel Supervisor' },
    windows_sysadmin: { icon: '⚙️', title: 'Windows Sysadmin Services' },
    windows_defender: { icon: '🛡️', title: 'Windows Defender Security' },
    windows_startup_auditor: { icon: '🚀', title: 'Windows Startup Auditor' },
    windows_backup_manager: { icon: '💾', title: 'Windows Backup & Restore Points' },
    trading_terminal: { icon: '📈', title: 'Trading Terminal Connection' },
    user_assistant: { icon: '🗓️', title: 'Personal User Assistant' },
    helpdesk: { icon: '🎧', title: 'Helpdesk Tickets Queue' },
    registry_viewer: { icon: '🗝️', title: 'Windows Registry Hives' },
    software_audit: { icon: '📊', title: 'Software Transparency Audit' },
    autolog_manager: { icon: '📝', title: 'Auto-Logging Manager' },
  };

  // State
  let _configData = null;
  let _statusData = null;
  let _filesData = [];
  let _currentViewingFile = '';
  let _currentCsvData = null;
  let _csvPage = 0;
  const _csvLimit = 100;
  let _toastInstance = null;

  function showToast(message, type = 'info') {
    const toastEl = document.getElementById('autolog-toast');
    if (!toastEl) return;
    const msgEl = document.getElementById('autolog-toast-msg');
    const iconEl = document.getElementById('autolog-toast-icon');

    if (msgEl) msgEl.textContent = message;

    if (iconEl) {
      iconEl.className = 'bi me-1 ';
      if (type === 'success') {
        iconEl.className += 'bi-check-circle-fill text-success';
      } else if (type === 'error' || type === 'danger') {
        iconEl.className += 'bi-exclamation-octagon-fill text-danger';
      } else if (type === 'warning') {
        iconEl.className += 'bi-exclamation-triangle-fill text-warning';
      } else {
        iconEl.className += 'bi-info-circle-fill text-info';
      }
    }

    if (!_toastInstance && window.bootstrap?.Toast) {
      _toastInstance = new window.bootstrap.Toast(toastEl, { delay: 4000 });
    }
    if (_toastInstance) {
      _toastInstance.show();
    }
  }

  // --- API Fetch Helpers ---
  async function apiGet(endpoint) {
    const res = await fetch(endpoint);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  }

  async function apiPost(endpoint, body = {}) {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  }

  async function apiDelete(endpoint) {
    const res = await fetch(endpoint, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  }

  // --- Load and Render Status & Config ---
  async function loadStatusAndConfig() {
    try {
      const [status, config] = await Promise.all([
        apiGet('/api/autolog/status'),
        apiGet('/api/autolog/config'),
      ]);

      _statusData = status;
      _configData = config;

      renderHeaderStatus();
      renderLoggersTable();
    } catch (err) {
      console.error('[AutoLogTab] Ошибка загрузки статуса/конфигурации:', err);
      showToast(`Ошибка загрузки данных: ${err.message}`, 'danger');
    }
  }

  function renderHeaderStatus() {
    if (!_statusData || !_configData) return;

    const isRunning = _statusData.running;
    const isAutologEnabled = _configData.enable_autolog;

    // Badge
    const badge = document.getElementById('autolog-engine-badge');
    const badgeText = document.getElementById('autolog-engine-badge-text');
    if (badge && badgeText) {
      if (isRunning) {
        badge.className = 'badge bg-success d-flex align-items-center gap-1.5 px-3 py-2 fs-6 shadow-sm';
        badgeText.textContent = 'Движок активен';
      } else {
        badge.className = 'badge bg-secondary d-flex align-items-center gap-1.5 px-3 py-2 fs-6 shadow-sm';
        badgeText.textContent = isAutologEnabled ? 'Движок остановлен' : 'Автологгирование выключено';
      }
    }

    // Toggle button
    const toggleBtn = document.getElementById('btn-autolog-toggle-engine');
    const toggleText = document.getElementById('btn-autolog-toggle-text');
    if (toggleBtn && toggleText) {
      if (isRunning) {
        toggleBtn.className = 'btn btn-sm btn-outline-danger d-flex align-items-center gap-1 shadow-sm';
        toggleText.textContent = 'Остановить';
      } else {
        toggleBtn.className = 'btn btn-sm btn-outline-success d-flex align-items-center gap-1 shadow-sm';
        toggleText.textContent = 'Запустить';
      }
    }

    // Master Switch
    const masterSwitch = document.getElementById('switch-enable-autolog');
    const masterText = document.getElementById('autolog-master-status-text');
    if (masterSwitch) {
      masterSwitch.checked = isAutologEnabled;
    }
    if (masterText) {
      masterText.textContent = isAutologEnabled ? 'Включено' : 'Выключено';
      masterText.className = isAutologEnabled ? 'fw-bold text-info' : 'fw-bold text-muted';
    }

    // Metrics Counters
    const activeTasksEl = document.getElementById('metric-active-tasks');
    if (activeTasksEl) {
      activeTasksEl.textContent = _statusData.active_tasks_count || 0;
    }

    const cfgFileEl = document.getElementById('metric-active-config-file');
    if (cfgFileEl) {
      cfgFileEl.textContent = _configData.config_file || 'config_tc.json';
    }
  }

  function renderLoggersTable() {
    const tbody = document.getElementById('tbody-loggers');
    if (!tbody || !_configData) return;

    const loggers = _configData.loggers || {};
    const keys = Object.keys(loggers);
    const badgeTotal = document.getElementById('badge-total-loggers');
    if (badgeTotal) badgeTotal.textContent = keys.length;

    const searchInput = document.getElementById('input-search-loggers');
    const filter = (searchInput?.value || '').toLowerCase().trim();

    const filteredKeys = keys.filter(k => {
      if (!filter) return true;
      const meta = APP_META[k] || {};
      return k.toLowerCase().includes(filter) || (meta.title && meta.title.toLowerCase().includes(filter));
    });

    if (filteredKeys.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-muted py-4">
            ${filter ? 'Ничего не найдено по фильтру "' + filter + '"' : 'Нет доступных логгеров'}
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = filteredKeys.map(name => {
      const item = loggers[name];
      const meta = APP_META[name] || { icon: '📦', title: name };
      const isEnabled = item.enabled !== false;
      const interval = item.interval || '1 minute';
      const pollCount = item.poll_count || 0;
      const lastPoll = item.last_poll ? formatDateTime(item.last_poll) : '<span class="text-muted">Не опрашивался</span>';

      // Build options for select
      const hasCustom = !INTERVAL_PRESETS.some(p => p.value === interval);
      const optionsHtml = INTERVAL_PRESETS.map(p => `
        <option value="${p.value}" ${p.value === interval ? 'selected' : ''}>${p.label}</option>
      `).join('') + (hasCustom ? `<option value="${interval}" selected>${interval} (пользовательский)</option>` : '');

      return `
        <tr data-logger="${name}">
          <td class="text-center">
            <div class="form-check form-switch d-inline-block mb-0">
              <input class="form-check-input logger-enable-switch" type="checkbox" role="switch" 
                     data-logger="${name}" ${isEnabled ? 'checked' : ''} title="Включить / выключить логгер">
            </div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <span class="fs-5">${meta.icon}</span>
              <div>
                <div class="fw-bold text-white">${name}</div>
                <div class="text-muted" style="font-size: 0.75rem;">${meta.title}</div>
              </div>
            </div>
          </td>
          <td>
            <div class="input-group input-group-sm">
              <select class="form-select form-select-sm bg-dark text-white border-secondary logger-interval-select" data-logger="${name}">
                ${optionsHtml}
              </select>
              <button class="btn btn-outline-secondary btn-custom-interval" type="button" data-logger="${name}" title="Ввести свой интервал">
                <i class="bi bi-pencil"></i>
              </button>
            </div>
          </td>
          <td class="text-center font-monospace text-info fw-bold">
            ${pollCount}
          </td>
          <td class="small font-monospace">
            ${lastPoll}
          </td>
          <td class="text-center">
            <div class="btn-group btn-group-sm" role="group">
              <button class="btn btn-outline-info btn-poll-single d-flex align-items-center gap-1" data-logger="${name}" title="Опросить немедленно">
                <i class="bi bi-play-circle"></i>
                <span class="d-none d-lg-inline">Опрос</span>
              </button>
              <button class="btn btn-outline-light btn-view-csv d-flex align-items-center gap-1" data-logger="${name}" title="Посмотреть CSV-лог">
                <i class="bi bi-eye"></i>
                <span class="d-none d-lg-inline">Лог</span>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    attachLoggersTableEvents();
  }

  function formatDateTime(isoStr) {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' +
             d.toLocaleDateString([], { day: '2-digit', month: '2-digit' });
    } catch {
      return isoStr;
    }
  }

  function attachLoggersTableEvents() {
    // 1. Enable switch change
    document.querySelectorAll('.logger-enable-switch').forEach(sw => {
      sw.addEventListener('change', (e) => {
        const loggerName = e.target.getAttribute('data-logger');
        if (_configData?.loggers?.[loggerName]) {
          _configData.loggers[loggerName].enabled = e.target.checked;
        }
      });
    });

    // 2. Interval select change
    document.querySelectorAll('.logger-interval-select').forEach(sel => {
      sel.addEventListener('change', (e) => {
        const loggerName = e.target.getAttribute('data-logger');
        if (_configData?.loggers?.[loggerName]) {
          _configData.loggers[loggerName].interval = e.target.value;
        }
      });
    });

    // 3. Custom interval prompt
    document.querySelectorAll('.btn-custom-interval').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const loggerName = btn.getAttribute('data-logger');
        const currentVal = _configData?.loggers?.[loggerName]?.interval || '1 minute';
        const newVal = prompt(`Введите интервал опроса для '${loggerName}' (например: '10 seconds', '5 minutes', '2 hours'):`, currentVal);
        if (newVal && newVal.trim()) {
          const trimmed = newVal.trim();
          if (_configData?.loggers?.[loggerName]) {
            _configData.loggers[loggerName].interval = trimmed;
          }
          renderLoggersTable();
        }
      });
    });

    // 4. Poll single logger button
    document.querySelectorAll('.btn-poll-single').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const loggerName = btn.getAttribute('data-logger');
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span>`;
        try {
          await apiPost(`/api/autolog/poll/${loggerName}`);
          showToast(`Опрос приложения '${loggerName}' успешно выполнен!`, 'success');
          await loadStatusAndConfig();
          await loadLogFiles();
        } catch (err) {
          showToast(`Ошибка опроса '${loggerName}': ${err.message}`, 'danger');
        } finally {
          btn.disabled = false;
          btn.innerHTML = `<i class="bi bi-play-circle"></i> <span class="d-none d-lg-inline">Опрос</span>`;
        }
      });
    });

    // 5. View CSV button
    document.querySelectorAll('.btn-view-csv').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const loggerName = btn.getAttribute('data-logger');
        await openLoggerCsvFile(loggerName);
      });
    });
  }

  async function openLoggerCsvFile(loggerName) {
    // Guess file name
    await loadLogFiles();
    const candidateName = _filesData.find(f => f.filename.toLowerCase().includes(loggerName.toLowerCase()))?.filename
      || `${loggerName}_polls.csv`;

    const viewerTabBtn = document.getElementById('subtab-viewer-btn');
    if (viewerTabBtn) {
      viewerTabBtn.click();
    }

    const select = document.getElementById('select-csv-target');
    if (select) {
      select.value = candidateName;
      await loadCsvContent(candidateName);
    }
  }

  // --- Save Configuration ---
  async function saveConfig() {
    const saveBtns = [
      document.getElementById('btn-autolog-save-config'),
      document.getElementById('btn-autolog-save-config-bottom'),
    ];

    saveBtns.forEach(b => {
      if (b) {
        b.disabled = true;
        b.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status"></span> Сохранение...`;
      }
    });

    try {
      const masterSwitch = document.getElementById('switch-enable-autolog');
      const isAutologEnabled = masterSwitch ? masterSwitch.checked : true;

      const loggersPayload = {};
      if (_configData?.loggers) {
        Object.entries(_configData.loggers).forEach(([k, v]) => {
          loggersPayload[k] = {
            interval: v.interval || '1 minute',
            enabled: v.enabled !== false,
          };
        });
      }

      const payload = {
        enable_autolog: isAutologEnabled,
        loggers: loggersPayload,
      };

      const res = await apiPost('/api/autolog/config', payload);
      showToast(res.message || 'Конфигурация успешно сохранена!', 'success');
      await loadStatusAndConfig();
    } catch (err) {
      console.error('[AutoLogTab] Ошибка сохранения конфигурации:', err);
      showToast(`Ошибка сохранения: ${err.message}`, 'danger');
    } finally {
      saveBtns.forEach(b => {
        if (b) {
          b.disabled = false;
          b.innerHTML = `<i class="bi bi-floppy-fill me-1"></i> Сохранить настройки`;
        }
      });
    }
  }

  // --- Files Manager ---
  async function loadLogFiles() {
    try {
      const data = await apiGet('/api/autolog/files');
      _filesData = data.files || [];

      // Update counters
      const badgeFiles = document.getElementById('badge-files-count');
      if (badgeFiles) badgeFiles.textContent = _filesData.length;

      const metricFiles = document.getElementById('metric-csv-files-count');
      if (metricFiles) metricFiles.textContent = _filesData.length;

      renderFilesTable();
      updateCsvSelectDropdown();
    } catch (err) {
      console.error('[AutoLogTab] Ошибка загрузки списка файлов логов:', err);
    }
  }

  function renderFilesTable() {
    const tbody = document.getElementById('tbody-files');
    if (!tbody) return;

    if (_filesData.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center text-muted py-4">
            В каталоге <code>%APPDATA%/AI-Breadboard/apps/logs</code> пока нет созданных CSV-файлов.
            Запустите движок автологгирования или выполните разовый опрос.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = _filesData.map(file => {
      const dateStr = formatDateTime(file.modified_at);
      return `
        <tr data-file="${file.filename}">
          <td>
            <div class="d-flex align-items-center gap-2">
              <i class="bi bi-file-earmark-spreadsheet text-success fs-5"></i>
              <span class="font-monospace fw-semibold text-white">${file.filename}</span>
            </div>
          </td>
          <td class="text-end font-monospace text-muted">
            ${file.size_human}
          </td>
          <td class="text-center font-monospace text-info fw-bold">
            ${file.row_count}
          </td>
          <td class="small font-monospace">
            ${dateStr}
          </td>
          <td class="text-center">
            <div class="btn-group btn-group-sm" role="group">
              <button class="btn btn-outline-light btn-view-file d-flex align-items-center gap-1" data-file="${file.filename}" title="Открыть в инспекторе">
                <i class="bi bi-eye"></i>
                <span>Просмотр</span>
              </button>
              <a href="/api/autolog/download/${file.filename}" class="btn btn-outline-success d-flex align-items-center gap-1" download title="Скачать CSV">
                <i class="bi bi-download"></i>
              </a>
              <button class="btn btn-outline-danger btn-delete-file d-flex align-items-center gap-1" data-file="${file.filename}" title="Удалить файл лога">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    // Attach row events
    document.querySelectorAll('.btn-view-file').forEach(btn => {
      btn.addEventListener('click', () => {
        const fn = btn.getAttribute('data-file');
        const viewerTabBtn = document.getElementById('subtab-viewer-btn');
        if (viewerTabBtn) viewerTabBtn.click();
        const select = document.getElementById('select-csv-target');
        if (select) {
          select.value = fn;
          loadCsvContent(fn);
        }
      });
    });

    document.querySelectorAll('.btn-delete-file').forEach(btn => {
      btn.addEventListener('click', async () => {
        const fn = btn.getAttribute('data-file');
        if (confirm(`Вы уверены, что хотите удалить файл лога '${fn}'?`)) {
          try {
            await apiDelete(`/api/autolog/file/${fn}`);
            showToast(`Файл '${fn}' успешно удален`, 'success');
            await loadLogFiles();
          } catch (err) {
            showToast(`Ошибка удаления файла: ${err.message}`, 'danger');
          }
        }
      });
    });
  }

  function updateCsvSelectDropdown() {
    const select = document.getElementById('select-csv-target');
    if (!select) return;

    const currentVal = select.value;
    select.innerHTML = '<option value="">-- Выберите CSV-файл --</option>' +
      _filesData.map(f => `<option value="${f.filename}" ${f.filename === currentVal ? 'selected' : ''}>${f.filename} (${f.row_count} записей, ${f.size_human})</option>`).join('');
  }

  // --- CSV Content Viewer ---
  async function loadCsvContent(filename) {
    if (!filename) {
      renderCsvTable([], []);
      return;
    }

    _currentViewingFile = filename;
    const downloadBtn = document.getElementById('btn-download-current-csv');
    if (downloadBtn) {
      downloadBtn.disabled = false;
      downloadBtn.onclick = () => {
        window.location.href = `/api/autolog/download/${filename}`;
      };
    }

    const thead = document.getElementById('thead-csv-content');
    const tbody = document.getElementById('tbody-csv-content');
    if (tbody) {
      tbody.innerHTML = `<tr><td class="text-center text-muted py-4"><div class="spinner-border spinner-border-sm text-info me-2"></div> Загрузка строк лога...</td></tr>`;
    }

    try {
      const filterInput = document.getElementById('input-filter-csv');
      const search = filterInput ? filterInput.value.trim() : '';
      const query = `?limit=${_csvLimit}&offset=${_csvPage * _csvLimit}${search ? '&search=' + encodeURIComponent(search) : ''}`;
      const res = await apiGet(`/api/autolog/file/${filename}${query}`);

      _currentCsvData = res;
      renderCsvTable(res.headers, res.rows, res.total_rows);
    } catch (err) {
      console.error('[AutoLogTab] Ошибка чтения CSV файла:', err);
      if (tbody) {
        tbody.innerHTML = `<tr><td class="text-center text-danger py-4">Ошибка чтения файла: ${err.message}</td></tr>`;
      }
    }
  }

  function renderCsvTable(headers, rows, totalRows = 0) {
    const thead = document.getElementById('thead-csv-content');
    const tbody = document.getElementById('tbody-csv-content');
    const counter = document.getElementById('viewer-rows-count');
    const pageIndicator = document.getElementById('viewer-page-indicator');
    const prevBtn = document.getElementById('btn-viewer-prev-page');
    const nextBtn = document.getElementById('btn-viewer-next-page');

    if (!headers || headers.length === 0) {
      if (thead) thead.innerHTML = `<tr><th class="text-muted text-center">Нет данных</th></tr>`;
      if (tbody) tbody.innerHTML = `<tr><td class="text-center text-muted py-5">Выберите файл лога из списка выше</td></tr>`;
      if (counter) counter.textContent = 'Строк: 0';
      return;
    }

    // Render headers
    if (thead) {
      thead.innerHTML = `
        <tr>
          <th style="width: 45px;" class="text-center">#</th>
          ${headers.map(h => `<th class="text-nowrap">${escapeHtml(h)}</th>`).join('')}
        </tr>
      `;
    }

    // Render rows
    if (tbody) {
      if (!rows || rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${headers.length + 1}" class="text-center text-muted py-4">Нет записей, соответствующих критериям фильтра</td></tr>`;
      } else {
        const startIdx = _csvPage * _csvLimit;
        tbody.innerHTML = rows.map((row, idx) => `
          <tr>
            <td class="text-center font-monospace text-muted">${startIdx + idx + 1}</td>
            ${row.map(cell => `<td class="font-monospace text-nowrap" style="max-width: 320px; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(cell)}">${escapeHtml(cell)}</td>`).join('')}
          </tr>
        `).join('');
      }
    }

    // Update pagination
    const totalPages = Math.max(1, Math.ceil(totalRows / _csvLimit));
    if (counter) counter.textContent = `Отображено: ${rows.length} из ${totalRows} записей`;
    if (pageIndicator) pageIndicator.textContent = `${_csvPage + 1} / ${totalPages}`;
    if (prevBtn) prevBtn.disabled = _csvPage <= 0;
    if (nextBtn) nextBtn.disabled = (_csvPage + 1) >= totalPages;
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // --- Main Initialization ---
  function initAutoLogTab() {
    // 1. Search in loggers
    const searchLoggers = document.getElementById('input-search-loggers');
    if (searchLoggers) {
      searchLoggers.addEventListener('input', renderLoggersTable);
    }

    // 2. Refresh buttons
    const btnRefreshLoggers = document.getElementById('btn-refresh-loggers');
    if (btnRefreshLoggers) {
      btnRefreshLoggers.addEventListener('click', loadStatusAndConfig);
    }

    const btnRefreshFiles = document.getElementById('btn-refresh-files');
    if (btnRefreshFiles) {
      btnRefreshFiles.addEventListener('click', loadLogFiles);
    }

    const btnRefreshViewer = document.getElementById('btn-refresh-viewer');
    if (btnRefreshViewer) {
      btnRefreshViewer.addEventListener('click', () => {
        if (_currentViewingFile) loadCsvContent(_currentViewingFile);
      });
    }

    // 3. Master Poll All Button
    const btnPollAll = document.getElementById('btn-autolog-poll-all');
    if (btnPollAll) {
      btnPollAll.addEventListener('click', async () => {
        btnPollAll.disabled = true;
        btnPollAll.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Опрос всех...`;
        try {
          const res = await apiPost('/api/autolog/poll-all');
          showToast(`Опрос завершен: ${res.successful_count} из ${res.total_polled} логгеров успешно опрошено`, 'success');
          await loadStatusAndConfig();
          await loadLogFiles();
        } catch (err) {
          showToast(`Ошибка опроса всех логгеров: ${err.message}`, 'danger');
        } finally {
          btnPollAll.disabled = false;
          btnPollAll.innerHTML = `<i class="bi bi-arrow-repeat me-1"></i> Опросить все сейчас`;
        }
      });
    }

    // 4. Toggle Engine Run/Stop Button
    const btnToggle = document.getElementById('btn-autolog-toggle-engine');
    if (btnToggle) {
      btnToggle.addEventListener('click', async () => {
        const isRunning = _statusData?.running;
        btnToggle.disabled = true;
        try {
          if (isRunning) {
            await apiPost('/api/autolog/stop');
            showToast('AutoLogEngine успешно остановлен', 'info');
          } else {
            await apiPost('/api/autolog/start');
            showToast('AutoLogEngine успешно запущен', 'success');
          }
          await loadStatusAndConfig();
        } catch (err) {
          showToast(`Ошибка переключения движка: ${err.message}`, 'danger');
        } finally {
          btnToggle.disabled = false;
        }
      });
    }

    // 5. Save buttons
    const btnSaveTop = document.getElementById('btn-autolog-save-config');
    if (btnSaveTop) btnSaveTop.addEventListener('click', saveConfig);

    const btnSaveBottom = document.getElementById('btn-autolog-save-config-bottom');
    if (btnSaveBottom) btnSaveBottom.addEventListener('click', saveConfig);

    // 6. CSV file select dropdown
    const selectCsv = document.getElementById('select-csv-target');
    if (selectCsv) {
      selectCsv.addEventListener('change', (e) => {
        _csvPage = 0;
        loadCsvContent(e.target.value);
      });
    }

    // 7. Filter in viewer
    const filterCsv = document.getElementById('input-filter-csv');
    if (filterCsv) {
      let filterTimeout = null;
      filterCsv.addEventListener('input', () => {
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(() => {
          _csvPage = 0;
          if (_currentViewingFile) loadCsvContent(_currentViewingFile);
        }, 300);
      });
    }

    // 8. Pagination buttons
    const prevBtn = document.getElementById('btn-viewer-prev-page');
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (_csvPage > 0) {
          _csvPage--;
          if (_currentViewingFile) loadCsvContent(_currentViewingFile);
        }
      });
    }

    const nextBtn = document.getElementById('btn-viewer-next-page');
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        _csvPage++;
        if (_currentViewingFile) loadCsvContent(_currentViewingFile);
      });
    }

    // Initial data fetch
    loadStatusAndConfig();
    loadLogFiles();
  }

  // Self-execute on load or tab switch
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAutoLogTab);
  } else {
    initAutoLogTab();
  }

})();
