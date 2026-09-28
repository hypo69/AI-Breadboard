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
    { label: i18n.t('auto_5_5_seconds__12fa31'), value: '5 seconds' },
    { label: i18n.t('auto_10_10_seconds__b7ff71'), value: '10 seconds' },
    { label: i18n.t('auto_30_30_seconds__864959'), value: '30 seconds' },
    { label: i18n.t('auto_1_1_minute__23e767'), value: '1 minute' },
    { label: i18n.t('auto_5_5_minutes__dd04a6'), value: '5 minutes' },
    { label: i18n.t('auto_10_10_minutes__1cc423'), value: '10 minutes' },
    { label: i18n.t('auto_30_30_minutes__3de0be'), value: '30 minutes' },
    { label: i18n.t('auto_1_1_hour__11fe13'), value: '1 hour' },
    { label: i18n.t('auto_6_6_hours__adbf32'), value: '6 hours' },
    { label: i18n.t('auto_24_24_hours__112209'), value: '24 hours' },
    { label: i18n.t('auto_1_1_day__71f9fc'), value: '1 day' },
    { label: i18n.t('auto_7_7_days__152f62'), value: '7 days' },
  ];

  // App readable metadata (icons and titles)
  const APP_META = {
    system_inspector: { icon: '🖥️', title: i18n.t('auto_system_inspector__53c369') },
    hardware_monitor: { icon: '⚡', title: i18n.t('auto_hardware_sensors__e193a8') },
    librehardwaremonitor: { icon: '🌡️', title: 'LibreHardwareMonitor API' },
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
    cpu: { icon: '🧠', title: i18n.t('auto__cpu__acaa88'), allMetrics: ['temperature', 'load', 'clocks', 'voltage', 'power'] },
    gpu: { icon: '🎮', title: i18n.t('auto__gpu__19d6a3'), allMetrics: ['temperature', 'load', 'memory', 'power', 'fan', 'clocks'] },
    ram: { icon: '🖹', title: i18n.t('auto__ram__d953a0'), allMetrics: ['usage', 'swap', 'available', 'total'] },
    disk: { icon: '💽', title: i18n.t('auto__disk__d92824'), allMetrics: ['usage', 'io', 'read_bytes', 'write_bytes', 'queue_length'] },
    network: { icon: '🌐', title: i18n.t('auto__network__4e8e9f'), allMetrics: ['throughput', 'connections', 'bytes_sent', 'bytes_recv', 'errors'] },
    sensors: { icon: '🌡️', title: i18n.t('auto__lhm_wmi_52ae11'), allMetrics: ['temperature', 'fan', 'voltage', 'power', 'control'] },
    internet: { icon: '🚀', title: i18n.t('auto__speed_ping__62e3ab'), allMetrics: ['ping', 'download', 'upload', 'dns', 'jitter'] },
    storage: { icon: '💾', title: i18n.t('auto__s_m_a_r_t__c424e7'), allMetrics: ['smart_attributes', 'temperature', 'wear_level', 'health_status'] },
    device_flapping: { icon: '🔌', title: i18n.t('auto__flapping__8cb276'), allMetrics: ['connect_events', 'disconnect_events', 'flapping_count'] },
  };

  // State
  let _configData = null;
  let _statusData = null;
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
    } catch (err) {
      console.error(i18n.t('auto__autologtab__61f232'), err);
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
        badgeText.textContent = i18n.t('auto___6dedf5');
      } else {
        badge.className = 'badge bg-secondary d-flex align-items-center gap-1.5 px-3 py-2 fs-6 shadow-sm';
        badgeText.textContent = isAutologEnabled ? i18n.t('auto___870dfd') : i18n.t('auto___e0beae');
      }
    }

    // Toggle button text
    const btnToggleText = document.getElementById('btn-autolog-toggle-text');
    const btnToggle = document.getElementById('btn-autolog-toggle-engine');
    if (btnToggleText && btnToggle) {
      if (isRunning) {
        btnToggleText.textContent = i18n.t('auto___d4f447');
        btnToggle.className = 'btn btn-sm btn-outline-danger d-flex align-items-center gap-1 shadow-sm';
      } else {
        btnToggleText.textContent = i18n.t('auto___85ab1c');
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
      masterText.textContent = isAutologEnabled ? i18n.t('auto___2e304a') : i18n.t('auto___d934ae');
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
        optionsHtml += `<option value="${intervalVal}i18n.t('auto_selected_intervalval_option_html_tr_data_logger_name__a805ef')${name}">
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
                    data-app="${name}" title=i18n.t('auto___ea58d3')>
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
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>i18n.t('auto__try_await_apipost_api_autolog_poll_appname_showtoast__dac15c')${appName}i18n.t('auto___fe7962')successi18n.t('auto__await_loadstatusandconfig_catch_err_showtoast__3f2c52')${appName}': ${err.message}`, 'danger');
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
              <label class="small text-muted text-nowrap mb-0i18n.t('auto__label_input_type__79f796')number" class="form-control form-control-sm bg-dark text-white border-secondary sensor-interval-input"
                     data-sensor="${sensorName}" value="${intervalSec}" min="0.1" step="0.5" style="max-width: 90px;">
            </div>

            <div class="mt-2">
              <div class="small text-muted mb-1i18n.t('auto__div_div_class__8bf1c3')d-flex flex-wrap gap-1">
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
      showToast(i18n.t('auto___67b232'), 'info');
      const res = await apiPost('/api/autolog/config', payload);
      showToast(res.message || i18n.t('auto___db37c2'), 'success');
      await loadStatusAndConfig();
    } catch (err) {
      console.error(i18n.t('auto__autologtab__4b42a0'), err);
      showToast(`Ошибка сохранения: ${err.message}`, 'danger');
    }
  }

  // --- Telemetry Service Logic (ai-telemetry.exe) ---
  let _telemetryStatusData = null;

  async function loadTelemetryServiceStatusAndConfig() {
    try {
      const [statusRes, configRes] = await Promise.all([
        apiGet('/api/autolog/telemetry/status'),
        apiGet('/api/autolog/telemetry/configi18n.t('auto__telemetrystatusdata_statusres_const_badgenav_document_getelementbyid__4ec2cd')badge-telemetry-status');
      const badgeCard = document.getElementById('svc-status-badge');
      const pidsEl = document.getElementById('svc-info-pids');
      const memEl = document.getElementById('svc-info-memory');
      const snapEl = document.getElementById('svc-info-snapshots');
      const schedEl = document.getElementById('svc-info-scheduler');

      const isRunning = Boolean(statusRes.is_running);
      if (badgeNav) {
        badgeNav.textContent = isRunning ? 'Online' : 'Offline';
        badgeNav.className = isRunning ? 'badge bg-success ms-1' : 'badge bg-secondary ms-1';
      }
      if (badgeCard) {
        badgeCard.textContent = isRunning ? i18n.t('auto__ai_telemetry_exe__2ffa97') : i18n.t('auto___aa0d25');
        badgeCard.className = isRunning ? 'badge bg-success' : 'badge bg-secondary';
      }

      if (pidsEl) {
        if (isRunning && statusRes.processes && statusRes.processes.length > 0) {
          const list = statusRes.processes.map(p => `${p.name} (PID: ${p.pid})`).join(', ');
          pidsEl.textContent = list;
          pidsEl.title = list;
        } else {
          pidsEl.textContent = i18n.t('auto___99334f');
        }
      }

      if (memEl) {
        memEl.textContent = isRunning ? `${statusRes.total_memory_mb} МБ` : i18n.t('auto_0__2c95b9');
      }

      if (snapEl) {
        snapEl.textContent = `${statusRes.snapshots_count} снимков`;
        if (statusRes.latest_timestamp) {
          snapEl.title = `Последний: ${statusRes.latest_timestamp}`;
        }
      }

      if (schedEl) {
        const sched = statusRes.task_scheduler || {};
        if (sched.installed) {
          schedEl.innerHTML = `<span class="text-successi18n.t('auto__sched_state_span_small_class__3c04a6')text-muted" style="font-size:0.7rem;">[Wake: ${sched.wake_to_run}]</small>`;
        } else {
          schedEl.innerHTML = '<span class="text-muted">Не установлено</span>i18n.t('auto__const_mode_configres_mode_statusres_mode__d45e6c')hybrid').toLowerCase();
      const radioMode = document.querySelector(`input[name="telemetryModeRadio"][value="${mode}"]`);
      if (radioMode) radioMode.checked = true;

      const fastInt = configRes.interval_seconds || statusRes.interval_seconds || 5.0;
      const inputFast = document.getElementById('cfg-fast-interval');
      const valFast = document.getElementById('val-fast-intervali18n.t('auto__if_inputfast_inputfast_value_fastint_if_valfast_valfast_textcontent_fastint_const_heavyint_configres_heavy_interval_seconds_statusres_heavy_interval_seconds_60_0_const_inputheavy_document_getelementbyid__880fc5')cfg-heavy-interval');
      const valHeavy = document.getElementById('val-heavy-intervali18n.t('auto__if_inputheavy_inputheavy_value_heavyint_if_valheavy_valheavy_textcontent_heavyint_const_topprocs_configres_top_processes_statusres_top_processes_10_const_seltop_document_getelementbyid__9ec224')cfg-top-processes');
      if (selTop) selTop.value = String(topProcs);

      const hColls = configRes.heavy_collectors || statusRes.heavy_collectors || {};
      const swLhm = document.getElementById('h-sensor-lhm');
      if (swLhm) swLhm.checked = Boolean(hColls.hardware_sensors ?? true);
      const swSmart = document.getElementById('h-sensor-smart');
      if (swSmart) swSmart.checked = Boolean(hColls.storage_smart ?? true);
      const swPing = document.getElementById('h-sensor-ping');
      if (swPing) swPing.checked = Boolean(hColls.network_ping ?? true);
      const swInv = document.getElementById('h-sensor-inventory');
      if (swInv) swInv.checked = Boolean(hColls.inventory_wmi ?? false);

    } catch (err) {
      console.warn(i18n.t('auto__autologtab__8634e6'), err);
    }
  }

  async function saveTelemetryConfiguration() {
    try {
      const selectedMode = document.querySelector('input[name="telemetryModeRadio"]:checked')?.value || 'hybrid';
      const fastInt = parseFloat(document.getElementById('cfg-fast-interval')?.value || '5.0');
      const heavyInt = parseFloat(document.getElementById('cfg-heavy-interval')?.value || '60.0');
      const topProcs = parseInt(document.getElementById('cfg-top-processes')?.value || '10', 10);

      const hColls = {
        hardware_sensors: document.getElementById('h-sensor-lhm')?.checked ?? true,
        storage_smart: document.getElementById('h-sensor-smart')?.checked ?? true,
        network_ping: document.getElementById('h-sensor-ping')?.checked ?? true,
        inventory_wmi: document.getElementById('h-sensor-inventory')?.checked ?? false,
      };

      const payload = {
        mode: selectedMode,
        interval_seconds: fastInt,
        heavy_interval_seconds: heavyInt,
        top_processes: topProcs,
        heavy_collectors: hColls,
      };

      showToast(i18n.t('auto___6ffa28'), 'info');
      const res = await apiPost('/api/autolog/telemetry/config', payload);
      showToast(res.message || i18n.t('auto___e842db'), 'successi18n.t('auto__await_loadtelemetryservicestatusandconfig_catch_err_showtoast_err_message__c39fbd')dangeri18n.t('auto__async_function_controltelemetryservice_action_try_showtoast_action__bd4e9b')info');
      const res = await apiPost('/api/autolog/telemetry/controli18n.t('auto__action_showtoast__d730b7')${action}i18n.t('auto___7a48e8')successi18n.t('auto__settimeout_loadtelemetryservicestatusandconfig_1000_catch_err_showtoast_err_message__3b3083')danger');
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

    // Telemetry service controls & save
    const btnSaveTelemetry = document.getElementById('btn-save-telemetry-config');
    if (btnSaveTelemetry) btnSaveTelemetry.addEventListener('click', saveTelemetryConfiguration);

    const btnTelStart = document.getElementById('btn-telemetry-start');
    if (btnTelStart) btnTelStart.addEventListener('click', () => controlTelemetryService('start'));

    const btnTelStop = document.getElementById('btn-telemetry-stop');
    if (btnTelStop) btnTelStop.addEventListener('click', () => controlTelemetryService('stop'));

    const btnTelRestart = document.getElementById('btn-telemetry-restart');
    if (btnTelRestart) btnTelRestart.addEventListener('click', () => controlTelemetryService('restart'));

    const btnTelInstallTask = document.getElementById('btn-telemetry-install-task');
    if (btnTelInstallTask) btnTelInstallTask.addEventListener('click', () => controlTelemetryService('install-task'));

    const btnTelUninstallTask = document.getElementById('btn-telemetry-uninstall-task');
    if (btnTelUninstallTask) btnTelUninstallTask.addEventListener('click', () => controlTelemetryService('uninstall-task'));

    // Dynamic label sync for intervals
    const inputFast = document.getElementById('cfg-fast-interval');
    if (inputFast) {
      inputFast.addEventListener('input', () => {
        const valFast = document.getElementById('val-fast-intervali18n.t('auto__if_valfast_valfast_textcontent_inputfast_value_const_inputheavy_document_getelementbyid__62f10f')cfg-heavy-interval');
    if (inputHeavy) {
      inputHeavy.addEventListener('input', () => {
        const valHeavy = document.getElementById('val-heavy-intervali18n.t('auto__if_valheavy_valheavy_textcontent_inputheavy_value_toggle_engine_button_const_btntoggle_document_getelementbyid__178b59')btn-autolog-toggle-engine');
    if (btnToggle) {
      btnToggle.addEventListener('click', async () => {
        btnToggle.disabled = true;
        try {
          const isRunning = _statusData?.running || _configData?.is_running;
          if (isRunning) {
            await apiPost('/api/autolog/stop');
            showToast(i18n.t('auto_autologengine__1fe2cb'), 'info');
          } else {
            await apiPost('/api/autolog/start');
            showToast(i18n.t('auto_autologengine__5742cf'), 'successi18n.t('auto__await_loadstatusandconfig_catch_err_showtoast_err_message__49ea54')danger');
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
          const res = await apiPost('/api/autolog/poll-alli18n.t('auto__showtoast_res_successful_count_res_total_polled__b1b668')successi18n.t('auto__await_loadstatusandconfig_catch_err_showtoast_err_message__fb1300')danger');
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
    if (btnRefSensors) btnRefSensors.addEventListener('clicki18n.t('auto__loadstatusandconfig_const_btntabtelemetry_document_getelementbyid__5ebaaa')subtab-telemetry-service-btn');
    if (btnTabTelemetry) {
      btnTabTelemetry.addEventListener('click', loadTelemetryServiceStatusAndConfig);
    }

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
  }

  // --- Initialization ---
  function initAll() {
    setupEventListeners();
    loadStatusAndConfig();
    loadTelemetryServiceStatusAndConfig();
    setInterval(loadTelemetryServiceStatusAndConfig, 10000);
  }

  document.addEventListener('DOMContentLoaded', initAll);

  // Also initialize immediately if DOM is already ready
  if (document.readyState === 'interactive' || document.readyState === 'complete') {
    initAll();
  }
})();
