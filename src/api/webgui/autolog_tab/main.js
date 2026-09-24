/**
 * ===============================================================================
 * Process Name: Auto-Logging and Telemetry Sensors Interface Controller
 * ===============================================================================
 * Description:
 *   Модульный контроллер вкладки управления автологгированием и телеметрией в /tc.
 *   Обеспечивает опрос REST API (/api/autolog), сохранение объединенной конфигурации,
 *   графическое редактирование сенсоров, метрик, JSON-редактор и выгрузку CSV-файлов.
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

  console.log('🚀 [AutoLogTab] Initializing Auto-Logging & Sensors Controller...');

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

  // Sensor metadata
  const SENSOR_META = {
    cpu: { icon: '🧠', title: 'Процессор (CPU)', allMetrics: ['temperature', 'load', 'clocks', 'voltage', 'power'] },
    gpu: { icon: '🎮', title: 'Видеокарта (GPU)', allMetrics: ['temperature', 'load', 'memory', 'power', 'fan', 'clocks'] },
    ram: { icon: '🖹', title: 'Оперативная память (RAM)', allMetrics: ['usage', 'swap', 'available', 'total'] },
    disk: { icon: '💽', title: 'Дисковая подсистема (Disk)', allMetrics: ['usage', 'io', 'read_bytes', 'write_bytes', 'queue_length'] },
    network: { icon: '🌐', title: 'Сетевой интерфейс (Network)', allMetrics: ['throughput', 'connections', 'bytes_sent', 'bytes_recv', 'errors'] },
    sensors: { icon: '🌡️', title: 'Сенсоры LHM / WMI', allMetrics: ['temperature', 'fan', 'voltage', 'power', 'control'] },
    internet: { icon: '🚀', title: 'Интернет-канал (Speed/Ping)', allMetrics: ['ping', 'download', 'upload', 'dns', 'jitter'] },
    storage: { icon: '💾', title: 'Здоровье дисков (S.M.A.R.T.)', allMetrics: ['smart_attributes', 'temperature', 'wear_level', 'health_status'] },
    device_flapping: { icon: '🔌', title: 'Дребезг устройств (Flapping)', allMetrics: ['connect_events', 'disconnect_events', 'flapping_count'] },
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
      renderSensorsCards();
      renderTelemetryOptions();
      renderJsonEditor();
    } catch (err) {
      console.error('[AutoLogTab] Ошибка загрузки статуса/конфигурации:', err);
      showToast(`Ошибка загрузки данных: ${err.message}`, 'danger');
    }
  }

  function renderHeaderStatus() {
    if (!_statusData || !_configData) return;

    const isRunning = _statusData.running || _configData.is_running;
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

    // Toggle button text
    const btnToggleText = document.getElementById('btn-autolog-toggle-text');
    const btnToggle = document.getElementById('btn-autolog-toggle-engine');
    if (btnToggleText && btnToggle) {
      if (isRunning) {
        btnToggleText.textContent = 'Остановить';
        btnToggle.className = 'btn btn-sm btn-outline-danger d-flex align-items-center gap-1 shadow-sm';
      } else {
        btnToggleText.textContent = 'Запустить';
        btnToggle.className = 'btn btn-sm btn-outline-success d-flex align-items-center gap-1 shadow-sm';
      }
    }

    // Counters
    const activeTasksEl = document.getElementById('metric-active-tasks');
    if (activeTasksEl) {
      activeTasksEl.textContent = _statusData.active_tasks_count ?? 0;
    }

    const sensorsCount = Object.keys(_configData.sensors || {}).length;
    const activeSensorsCount = Object.values(_configData.sensors || {}).filter(s => s.enabled).length;
    const metricSensorsEl = document.getElementById('metric-active-sensors');
    if (metricSensorsEl) {
      metricSensorsEl.textContent = `${activeSensorsCount} / ${sensorsCount}`;
    }
    const badgeSensorsEl = document.getElementById('badge-sensors-count');
    if (badgeSensorsEl) {
      badgeSensorsEl.textContent = `${activeSensorsCount}`;
    }

    const cfgFileEl = document.getElementById('metric-active-config-file');
    if (cfgFileEl) {
      cfgFileEl.textContent = _configData.config_file || '~autolog_sensors.json';
    }

    // Master Switch
    const masterSwitch = document.getElementById('switch-enable-autolog');
    const masterText = document.getElementById('autolog-master-status-text');
    if (masterSwitch) {
      masterSwitch.checked = Boolean(isAutologEnabled);
    }
    if (masterText) {
      masterText.textContent = isAutologEnabled ? 'Включено' : 'Выключено';
      masterText.className = isAutologEnabled ? 'fw-bold text-info' : 'fw-bold text-muted';
    }
  }

  // --- Render Loggers Table ---
  function renderLoggersTable() {
    const tbody = document.getElementById('tbody-loggers');
    if (!tbody || !_configData) return;

    const loggers = _configData.loggers || {};
    const loggerKeys = Object.keys(loggers);

    const badgeTotal = document.getElementById('badge-total-loggers');
    if (badgeTotal) badgeTotal.textContent = loggerKeys.length;

    if (loggerKeys.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-muted py-4">Логгеры не найдены в конфигурации</td>
        </tr>
      `;
      return;
    }

    let html = '';
    for (const name of loggerKeys) {
      const item = loggers[name];
      const meta = APP_META[name] || { icon: '📦', title: name };
      const isEnabled = Boolean(item.enabled);
      const intervalVal = item.interval || '1 minute';
      const pollCount = item.poll_count ?? 0;
      const lastPoll = item.last_poll
        ? new Date(item.last_poll).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        : '<span class="text-muted">—</span>';

      // Presets options HTML
      let optionsHtml = '';
      let isCustom = true;
      for (const preset of INTERVAL_PRESETS) {
        const selected = preset.value.toLowerCase() === intervalVal.toLowerCase() ? 'selected' : '';
        if (selected) isCustom = false;
        optionsHtml += `<option value="${preset.value}" ${selected}>${preset.label}</option>`;
      }
      if (isCustom) {
        optionsHtml += `<option value="${intervalVal}" selected>Пользовательский (${intervalVal})</option>`;
      }

      html += `
        <tr data-logger-name="${name}">
          <td class="text-center">
            <div class="form-check form-switch d-inline-block mb-0">
              <input class="form-check-input logger-enable-switch" type="checkbox" role="switch"
                     data-app="${name}" ${isEnabled ? 'checked' : ''}>
            </div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <span class="fs-5">${meta.icon}</span>
              <div>
                <div class="fw-semibold text-white">${meta.title}</div>
                <code class="text-secondary small">${name}</code>
              </div>
            </div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-1">
              <select class="form-select form-select-sm bg-dark text-white border-secondary select-logger-interval"
                      data-app="${name}" style="min-width: 170px;">
                ${optionsHtml}
              </select>
            </div>
          </td>
          <td class="text-center fw-mono">
            <span class="badge bg-secondary">${pollCount}</span>
          </td>
          <td>
            <small class="text-light">${lastPoll}</small>
          </td>
          <td class="text-center">
            <button class="btn btn-sm btn-outline-info btn-poll-single d-inline-flex align-items-center gap-1"
                    data-app="${name}" title="Опросить немедленно">
              <i class="bi bi-play-fill"></i>
              <span>Опросить</span>
            </button>
          </td>
        </tr>
      `;
    }

    tbody.innerHTML = html;
    bindLoggersTableEvents();
  }

  function bindLoggersTableEvents() {
    const tbody = document.getElementById('tbody-loggers');
    if (!tbody) return;

    // Single poller trigger
    tbody.querySelectorAll('.btn-poll-single').forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        const appName = btn.getAttribute('data-app');
        if (!appName) return;

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';

        try {
          await apiPost(`/api/autolog/poll/${appName}`);
          showToast(`Опрос логгера '${appName}' успешно выполнен`, 'success');
          await loadStatusAndConfig();
        } catch (err) {
          showToast(`Ошибка опроса '${appName}': ${err.message}`, 'danger');
        } finally {
          btn.disabled = false;
          btn.innerHTML = '<i class="bi bi-play-fill"></i> <span>Опросить</span>';
        }
      });
    });

    // Logger switch change
    tbody.querySelectorAll('.logger-enable-switch').forEach((sw) => {
      sw.addEventListener('change', (e) => {
        const appName = sw.getAttribute('data-app');
        if (_configData?.loggers?.[appName]) {
          _configData.loggers[appName].enabled = sw.checked;
        }
      });
    });

    // Logger interval change
    tbody.querySelectorAll('.select-logger-interval').forEach((sel) => {
      sel.addEventListener('change', (e) => {
        const appName = sel.getAttribute('data-app');
        if (_configData?.loggers?.[appName]) {
          _configData.loggers[appName].interval = sel.value;
        }
      });
    });
  }

  // --- Render Telemetry Sensors Cards ---
  function renderSensorsCards() {
    const container = document.getElementById('sensors-cards-container');
    if (!container || !_configData) return;

    const sensors = _configData.sensors || {};
    const sensorKeys = Object.keys(sensors);

    if (sensorKeys.length === 0) {
      container.innerHTML = `
        <div class="col-12 text-center text-muted py-4">Сенсоры телеметрии не найдены в конфигурации</div>
      `;
      return;
    }

    let html = '';
    for (const sensorName of sensorKeys) {
      const cfg = sensors[sensorName] || {};
      const meta = SENSOR_META[sensorName] || { icon: '📊', title: sensorName, allMetrics: cfg.metrics || [] };
      const isEnabled = Boolean(cfg.enabled);
      const intervalSec = cfg.interval_seconds ?? 5.0;
      const activeMetrics = new Set(cfg.metrics || []);

      // Combine default/known metrics with active metrics
      const allKnownMetrics = Array.from(new Set([...(meta.allMetrics || []), ...activeMetrics]));

      let metricsHtml = '';
      for (const m of allKnownMetrics) {
        const isActive = activeMetrics.has(m);
        metricsHtml += `
          <button type="button" class="btn btn-sm ${isActive ? 'btn-primary' : 'btn-outline-secondary'} py-0 px-2 rounded-pill metric-pill-btn"
                  data-sensor="${sensorName}" data-metric="${m}" style="font-size: 0.75rem;">
            ${isActive ? '✓ ' : '+ '}${m}
          </button>
        `;
      }

      html += `
        <div class="col-12 col-md-6 col-lg-4" data-sensor-card="${sensorName}">
          <div class="card bg-black border ${isEnabled ? 'border-secondary' : 'border-secondary-subtle opacity-75'} h-100 p-3 shadow-sm rounded-3">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <div class="d-flex align-items-center gap-2">
                <span class="fs-4">${meta.icon}</span>
                <div>
                  <h6 class="mb-0 text-white fw-bold">${meta.title}</h6>
                  <code class="text-secondary small">${sensorName}</code>
                </div>
              </div>
              <div class="form-check form-switch mb-0">
                <input class="form-check-input sensor-enable-switch" type="checkbox" role="switch"
                       data-sensor="${sensorName}" ${isEnabled ? 'checked' : ''}>
              </div>
            </div>

            <div class="d-flex align-items-center gap-2 my-2">
              <label class="small text-muted text-nowrap mb-0">Интервал (сек):</label>
              <input type="number" class="form-control form-control-sm bg-dark text-white border-secondary sensor-interval-input"
                     data-sensor="${sensorName}" value="${intervalSec}" min="0.1" step="0.5" style="max-width: 90px;">
            </div>

            <div class="mt-2">
              <div class="small text-muted mb-1">Собираемые метрики:</div>
              <div class="d-flex flex-wrap gap-1">
                ${metricsHtml || '<span class="text-muted small">Метрики не заданы</span>'}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    container.innerHTML = html;
    bindSensorsEvents();
  }

  function bindSensorsEvents() {
    const container = document.getElementById('sensors-cards-container');
    if (!container) return;

    // Sensor enabled switch
    container.querySelectorAll('.sensor-enable-switch').forEach((sw) => {
      sw.addEventListener('change', () => {
        const sName = sw.getAttribute('data-sensor');
        if (_configData?.sensors?.[sName]) {
          _configData.sensors[sName].enabled = sw.checked;
          const card = container.querySelector(`[data-sensor-card="${sName}"] .card`);
          if (card) {
            if (sw.checked) {
              card.classList.remove('opacity-75', 'border-secondary-subtle');
              card.classList.add('border-secondary');
            } else {
              card.classList.add('opacity-75', 'border-secondary-subtle');
              card.classList.remove('border-secondary');
            }
          }
          renderHeaderStatus();
        }
      });
    });

    // Sensor interval input
    container.querySelectorAll('.sensor-interval-input').forEach((inp) => {
      inp.addEventListener('input', () => {
        const sName = inp.getAttribute('data-sensor');
        const val = parseFloat(inp.value);
        if (_configData?.sensors?.[sName] && !isNaN(val)) {
          _configData.sensors[sName].interval_seconds = val;
        }
      });
    });

    // Metric toggle pill
    container.querySelectorAll('.metric-pill-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const sName = btn.getAttribute('data-sensor');
        const metric = btn.getAttribute('data-metric');
        if (!_configData?.sensors?.[sName]) return;

        let metrics = _configData.sensors[sName].metrics || [];
        if (metrics.includes(metric)) {
          metrics = metrics.filter(m => m !== metric);
          btn.className = 'btn btn-sm btn-outline-secondary py-0 px-2 rounded-pill metric-pill-btn';
          btn.textContent = '+ ' + metric;
        } else {
          metrics.push(metric);
          btn.className = 'btn btn-sm btn-primary py-0 px-2 rounded-pill metric-pill-btn';
          btn.textContent = '✓ ' + metric;
        }
        _configData.sensors[sName].metrics = metrics;
      });
    });
  }

  function renderTelemetryOptions() {
    if (!_configData) return;
    const opts = _configData.telemetry_options || {};

    const optInv = document.getElementById('opt-collect-inventory');
    const optSer = document.getElementById('opt-collect-serials');
    const optFiles = document.getElementById('opt-collect-file-events');
    const optMax = document.getElementById('opt-max-file-size');
    const optDirs = document.getElementById('opt-watch-dirs');

    if (optInv) optInv.checked = opts.collect_hardware_inventory ?? true;
    if (optSer) optSer.checked = opts.collect_serial_numbers ?? true;
    if (optFiles) optFiles.checked = opts.collect_file_events ?? true;
    if (optMax) optMax.value = opts.max_file_size_mb ?? 50;
    if (optDirs) optDirs.value = (opts.watch_directories || ['C:\\Users\\']).join(', ');
  }

  function collectTelemetryOptions() {
    const optInv = document.getElementById('opt-collect-inventory');
    const optSer = document.getElementById('opt-collect-serials');
    const optFiles = document.getElementById('opt-collect-file-events');
    const optMax = document.getElementById('opt-max-file-size');
    const optDirs = document.getElementById('opt-watch-dirs');

    const dirsRaw = optDirs ? optDirs.value.split(',').map(s => s.trim()).filter(Boolean) : ['C:\\Users\\'];

    return {
      collect_hardware_inventory: optInv ? optInv.checked : true,
      collect_serial_numbers: optSer ? optSer.checked : true,
      collect_file_events: optFiles ? optFiles.checked : true,
      max_file_size_mb: optMax ? parseInt(optMax.value, 10) || 50 : 50,
      watch_directories: dirsRaw,
    };
  }

  function renderJsonEditor() {
    const textarea = document.getElementById('textarea-raw-json');
    if (!textarea || !_configData) return;

    if (_configData.raw_json) {
      textarea.value = _configData.raw_json;
    } else {
      const fullObj = {
        $schema: 'https://json-schema.org/draft/2020-12/schema',
        enable_autolog: _configData.enable_autolog ?? true,
        default_interval: _configData.default_interval ?? '1 minute',
        loggers: _configData.loggers ?? {},
        sensors: _configData.sensors ?? {},
        telemetry_options: _configData.telemetry_options ?? {},
      };
      textarea.value = JSON.stringify(fullObj, null, 2);
    }
  }

  // --- Save Config via API ---
  async function saveFullConfiguration() {
    if (!_configData) return;

    const masterSwitch = document.getElementById('switch-enable-autolog');
    const enableAutolog = masterSwitch ? masterSwitch.checked : true;

    // Collect loggers
    const loggersPayload = {};
    for (const [name, item] of Object.entries(_configData.loggers || {})) {
      loggersPayload[name] = {
        interval: item.interval || '1 minute',
        enabled: Boolean(item.enabled),
      };
    }

    // Collect sensors
    const sensorsPayload = {};
    for (const [name, item] of Object.entries(_configData.sensors || {})) {
      sensorsPayload[name] = {
        enabled: Boolean(item.enabled),
        interval_seconds: item.interval_seconds ?? 5.0,
        metrics: item.metrics || [],
      };
    }

    const telemetryOptions = collectTelemetryOptions();

    const payload = {
      enable_autolog: enableAutolog,
      default_interval: _configData.default_interval || '1 minute',
      loggers: loggersPayload,
      sensors: sensorsPayload,
      telemetry_options: telemetryOptions,
    };

    try {
      showToast('Сохранение конфигурации...', 'info');
      const res = await apiPost('/api/autolog/config', payload);
      showToast(res.message || 'Конфигурация успешно сохранена!', 'success');
      await loadStatusAndConfig();
    } catch (err) {
      console.error('[AutoLogTab] Ошибка сохранения:', err);
      showToast(`Ошибка сохранения: ${err.message}`, 'danger');
    }
  }

  // --- CSV Files Manager ---
  async function loadCsvFiles() {
    const tbody = document.getElementById('tbody-files');
    if (!tbody) return;

    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-muted py-4">
          <div class="spinner-border spinner-border-sm text-info me-2" role="status"></div>
          Загрузка файлов...
        </td>
      </tr>
    `;

    try {
      const data = await apiGet('/api/autolog/files');
      _filesData = data.files || [];

      // Update counters
      const badgeFiles = document.getElementById('badge-files-count');
      if (badgeFiles) badgeFiles.textContent = _filesData.length;

      const metricFiles = document.getElementById('metric-csv-files-count');
      if (metricFiles) metricFiles.textContent = _filesData.length;

      renderFilesTable();
      populateViewerSelect();
    } catch (err) {
      console.error('[AutoLogTab] Ошибка загрузки файлов:', err);
      showToast(`Ошибка загрузки CSV файлов: ${err.message}`, 'danger');
      tbody.innerHTML = `
        <tr><td colspan="5" class="text-center text-danger py-3">Не удалось загрузить файлы: ${err.message}</td></tr>
      `;
    }
  }

  function renderFilesTable() {
    const tbody = document.getElementById('tbody-files');
    if (!tbody) return;

    if (_filesData.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center text-muted py-4">В каталоге пока нет CSV-файлов логов</td>
        </tr>
      `;
      return;
    }

    let html = '';
    for (const f of _filesData) {
      const modDate = f.modified ? new Date(f.modified).toLocaleString() : '—';
      html += `
        <tr>
          <td>
            <div class="d-flex align-items-center gap-2">
              <i class="bi bi-filetype-csv text-success fs-5"></i>
              <div>
                <span class="fw-semibold text-white">${f.filename}</span>
                <span class="text-muted small d-block">${f.app_name}</span>
              </div>
            </div>
          </td>
          <td class="text-end fw-mono text-light">${f.size_formatted || '0 B'}</td>
          <td class="text-center fw-mono">
            <span class="badge bg-secondary">${f.rows_count ?? 0}</span>
          </td>
          <td><small class="text-light">${modDate}</small></td>
          <td class="text-center">
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-info btn-view-file" data-file="${f.filename}" title="Просмотреть в инспекторе">
                <i class="bi bi-eye"></i> Просмотр
              </button>
              <a href="/api/autolog/download/${f.filename}" class="btn btn-outline-success" title="Скачать CSV">
                <i class="bi bi-download"></i>
              </a>
              <button class="btn btn-outline-danger btn-delete-file" data-file="${f.filename}" title="Удалить файл">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }

    tbody.innerHTML = html;
    bindFilesEvents();
  }

  function bindFilesEvents() {
    const tbody = document.getElementById('tbody-files');
    if (!tbody) return;

    // View file
    tbody.querySelectorAll('.btn-view-file').forEach((btn) => {
      btn.addEventListener('click', () => {
        const fn = btn.getAttribute('data-file');
        if (!fn) return;
        const viewerTabBtn = document.getElementById('subtab-viewer-btn');
        if (viewerTabBtn && window.bootstrap?.Tab) {
          const tab = new window.bootstrap.Tab(viewerTabBtn);
          tab.show();
        }
        const sel = document.getElementById('select-csv-target');
        if (sel) {
          sel.value = fn;
          loadCsvContent(fn);
        }
      });
    });

    // Delete file
    tbody.querySelectorAll('.btn-delete-file').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const fn = btn.getAttribute('data-file');
        if (!fn) return;
        if (!confirm(`Удалить файл лога '${fn}'?`)) return;

        try {
          await apiDelete(`/api/autolog/file/${fn}`);
          showToast(`Файл '${fn}' удален`, 'success');
          await loadCsvFiles();
        } catch (err) {
          showToast(`Ошибка удаления '${fn}': ${err.message}`, 'danger');
        }
      });
    });
  }

  function populateViewerSelect() {
    const sel = document.getElementById('select-csv-target');
    if (!sel) return;

    const currentVal = sel.value;
    let html = '<option value="">-- Выберите CSV-файл --</option>';
    for (const f of _filesData) {
      const selected = f.filename === currentVal ? 'selected' : '';
      html += `<option value="${f.filename}" ${selected}>${f.filename} (${f.size_formatted}, ${f.rows_count} строк)</option>`;
    }
    sel.innerHTML = html;
  }

  // --- CSV Viewer ---
  async function loadCsvContent(filename) {
    if (!filename) return;
    _currentViewingFile = filename;

    const thead = document.getElementById('thead-csv-content');
    const tbody = document.getElementById('tbody-csv-content');
    const dlBtn = document.getElementById('btn-download-current-csv');

    if (thead) thead.innerHTML = '<tr><th class="text-muted text-center">Загрузка данных...</th></tr>';
    if (tbody) tbody.innerHTML = '<tr><td class="text-center py-4"><div class="spinner-border spinner-border-sm text-info"></div></td></tr>';

    try {
      const offset = _csvPage * _csvLimit;
      const data = await apiGet(`/api/autolog/file/${filename}?limit=${_csvLimit}&offset=${offset}`);
      _currentCsvData = data;

      if (dlBtn) dlBtn.disabled = false;
      renderCsvTable(data);
    } catch (err) {
      showToast(`Ошибка чтения файла '${filename}': ${err.message}`, 'danger');
      if (thead) thead.innerHTML = '<tr><th class="text-danger text-center">Ошибка</th></tr>';
      if (tbody) tbody.innerHTML = `<tr><td class="text-danger text-center py-3">${err.message}</td></tr>`;
    }
  }

  function renderCsvTable(data) {
    const thead = document.getElementById('thead-csv-content');
    const tbody = document.getElementById('tbody-csv-content');
    const rowsCountEl = document.getElementById('viewer-rows-count');
    const pageIndicator = document.getElementById('viewer-page-indicator');
    const btnPrev = document.getElementById('btn-viewer-prev-page');
    const btnNext = document.getElementById('btn-viewer-next-page');

    const headers = data.headers || [];
    const rows = data.rows || [];
    const totalRows = data.total_rows || 0;

    if (rowsCountEl) rowsCountEl.textContent = `Строк: ${totalRows} (показано ${rows.length})`;

    const maxPages = Math.max(1, Math.ceil(totalRows / _csvLimit));
    if (pageIndicator) pageIndicator.textContent = `${_csvPage + 1} / ${maxPages}`;
    if (btnPrev) btnPrev.disabled = _csvPage <= 0;
    if (btnNext) btnNext.disabled = _csvPage >= maxPages - 1;

    if (headers.length === 0 && rows.length === 0) {
      if (thead) thead.innerHTML = '<tr><th class="text-muted text-center">Файл пуст</th></tr>';
      if (tbody) tbody.innerHTML = '<tr><td class="text-muted text-center py-4">Нет данных</td></tr>';
      return;
    }

    if (thead) {
      thead.innerHTML = '<tr>' + headers.map(h => `<th class="text-nowrap">${h}</th>`).join('') + '</tr>';
    }

    if (tbody) {
      if (rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${headers.length || 1}" class="text-center text-muted py-4">Нет строк</td></tr>`;
      } else {
        tbody.innerHTML = rows.map(r => {
          return '<tr>' + headers.map(h => `<td class="text-nowrap">${r[h] ?? ''}</td>`).join('') + '</tr>';
        }).join('');
      }
    }
  }

  // --- Setup Master Event Listeners ---
  function setupEventListeners() {
    // Save buttons
    const btnSaveHeader = document.getElementById('btn-autolog-save-config');
    const btnSaveBottom = document.getElementById('btn-autolog-save-config-bottom');
    const btnSaveSensors = document.getElementById('btn-save-sensors-config');
    if (btnSaveHeader) btnSaveHeader.addEventListener('click', saveFullConfiguration);
    if (btnSaveBottom) btnSaveBottom.addEventListener('click', saveFullConfiguration);
    if (btnSaveSensors) btnSaveSensors.addEventListener('click', saveFullConfiguration);

    // Toggle Engine button
    const btnToggle = document.getElementById('btn-autolog-toggle-engine');
    if (btnToggle) {
      btnToggle.addEventListener('click', async () => {
        btnToggle.disabled = true;
        try {
          const isRunning = _statusData?.running || _configData?.is_running;
          if (isRunning) {
            await apiPost('/api/autolog/stop');
            showToast('AutoLogEngine успешно остановлен', 'info');
          } else {
            await apiPost('/api/autolog/start');
            showToast('AutoLogEngine успешно запущен', 'success');
          }
          await loadStatusAndConfig();
        } catch (err) {
          showToast(`Ошибка: ${err.message}`, 'danger');
        } finally {
          btnToggle.disabled = false;
        }
      });
    }

    // Poll All button
    const btnPollAll = document.getElementById('btn-autolog-poll-all');
    if (btnPollAll) {
      btnPollAll.addEventListener('click', async () => {
        btnPollAll.disabled = true;
        btnPollAll.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Опрос...';
        try {
          const res = await apiPost('/api/autolog/poll-all');
          showToast(`Опрос завершен: успешно ${res.successful_count} из ${res.total_polled}`, 'success');
          await loadStatusAndConfig();
        } catch (err) {
          showToast(`Ошибка разового опроса: ${err.message}`, 'danger');
        } finally {
          btnPollAll.disabled = false;
          btnPollAll.innerHTML = '<i class="bi bi-arrow-repeat"></i> <span>Опросить все сейчас</span>';
        }
      });
    }

    // Refresh Loggers & Sensors
    const btnRefLoggers = document.getElementById('btn-refresh-loggers');
    if (btnRefLoggers) btnRefLoggers.addEventListener('click', loadStatusAndConfig);
    const btnRefSensors = document.getElementById('btn-refresh-sensors');
    if (btnRefSensors) btnRefSensors.addEventListener('click', loadStatusAndConfig);

    // Refresh Files
    const btnRefFiles = document.getElementById('btn-refresh-files');
    if (btnRefFiles) btnRefFiles.addEventListener('click', loadCsvFiles);

    // Search Loggers filter
    const inputSearch = document.getElementById('input-search-loggers');
    if (inputSearch) {
      inputSearch.addEventListener('input', () => {
        const q = inputSearch.value.toLowerCase().trim();
        const rows = document.querySelectorAll('#tbody-loggers tr[data-logger-name]');
        rows.forEach(r => {
          const name = r.getAttribute('data-logger-name') || '';
          const text = r.textContent.toLowerCase();
          r.style.display = (name.includes(q) || text.includes(q)) ? '' : 'none';
        });
      });
    }

    // Tab switch to Files
    const subtabFilesBtn = document.getElementById('subtab-files-btn');
    if (subtabFilesBtn) {
      subtabFilesBtn.addEventListener('shown.bs.tab', loadCsvFiles);
    }

    // Tab switch to JSON
    const subtabJsonBtn = document.getElementById('subtab-json-btn');
    if (subtabJsonBtn) {
      subtabJsonBtn.addEventListener('shown.bs.tab', renderJsonEditor);
    }

    // JSON Editor Actions
    const btnFormatJson = document.getElementById('btn-format-json');
    const btnReloadJson = document.getElementById('btn-reload-json');
    const btnSaveJson = document.getElementById('btn-save-raw-json');
    const txtJson = document.getElementById('textarea-raw-json');

    if (btnFormatJson && txtJson) {
      btnFormatJson.addEventListener('click', () => {
        try {
          const parsed = JSON.parse(txtJson.value);
          txtJson.value = JSON.stringify(parsed, null, 2);
          showToast('JSON отформатирован', 'info');
        } catch (e) {
          showToast(`Ошибка синтаксиса JSON: ${e.message}`, 'danger');
        }
      });
    }

    if (btnReloadJson) {
      btnReloadJson.addEventListener('click', async () => {
        await loadStatusAndConfig();
        renderJsonEditor();
        showToast('JSON перезагружен с диска', 'info');
      });
    }

    if (btnSaveJson && txtJson) {
      btnSaveJson.addEventListener('click', async () => {
        try {
          const parsed = JSON.parse(txtJson.value);
          showToast('Сохранение JSON...', 'info');
          const res = await apiPost('/api/autolog/config', { raw_json: JSON.stringify(parsed, null, 2) });
          showToast(res.message || 'JSON успешно сохранен!', 'success');
          await loadStatusAndConfig();
        } catch (err) {
          showToast(`Ошибка сохранения JSON: ${err.message}`, 'danger');
        }
      });
    }

    // CSV Viewer Controls
    const selViewer = document.getElementById('select-csv-target');
    if (selViewer) {
      selViewer.addEventListener('change', () => {
        _csvPage = 0;
        loadCsvContent(selViewer.value);
      });
    }

    const btnRefViewer = document.getElementById('btn-refresh-viewer');
    if (btnRefViewer) {
      btnRefViewer.addEventListener('click', () => {
        if (selViewer) loadCsvContent(selViewer.value);
      });
    }

    const btnPrevPage = document.getElementById('btn-viewer-prev-page');
    if (btnPrevPage) {
      btnPrevPage.addEventListener('click', () => {
        if (_csvPage > 0 && selViewer?.value) {
          _csvPage--;
          loadCsvContent(selViewer.value);
        }
      });
    }

    const btnNextPage = document.getElementById('btn-viewer-next-page');
    if (btnNextPage) {
      btnNextPage.addEventListener('click', () => {
        if (selViewer?.value) {
          _csvPage++;
          loadCsvContent(selViewer.value);
        }
      });
    }

    const inputFilterCsv = document.getElementById('input-filter-csv');
    if (inputFilterCsv) {
      inputFilterCsv.addEventListener('input', () => {
        const q = inputFilterCsv.value.toLowerCase().trim();
        const rows = document.querySelectorAll('#tbody-csv-content tr');
        rows.forEach(r => {
          const text = r.textContent.toLowerCase();
          r.style.display = text.includes(q) ? '' : 'none';
        });
      });
    }

    const btnDownload = document.getElementById('btn-download-current-csv');
    if (btnDownload) {
      btnDownload.addEventListener('click', () => {
        if (_currentViewingFile) {
          window.location.href = `/api/autolog/download/${_currentViewingFile}`;
        }
      });
    }
  }

  // --- Initialization ---
  document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadStatusAndConfig();
    loadCsvFiles();
  });

  // Also initialize immediately if DOM is already ready
  if (document.readyState === 'interactive' || document.readyState === 'complete') {
    setupEventListeners();
    loadStatusAndConfig();
    loadCsvFiles();
  }
})();
