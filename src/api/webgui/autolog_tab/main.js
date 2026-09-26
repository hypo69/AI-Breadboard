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

  // --- Telemetry Service Logic (ai-telemetry.exe) ---
  let _telemetryStatusData = null;

  async function loadTelemetryServiceStatusAndConfig() {
    try {
      const [statusRes, configRes] = await Promise.all([
        apiGet('/api/autolog/telemetry/status'),
        apiGet('/api/autolog/telemetry/config'),
      ]);
      _telemetryStatusData = statusRes;

      // Обновление карточки живого статуса
      const badgeNav = document.getElementById('badge-telemetry-status');
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
        badgeCard.textContent = isRunning ? 'Активен (ai-telemetry.exe)' : 'Остановлен';
        badgeCard.className = isRunning ? 'badge bg-success' : 'badge bg-secondary';
      }

      if (pidsEl) {
        if (isRunning && statusRes.processes && statusRes.processes.length > 0) {
          const list = statusRes.processes.map(p => `${p.name} (PID: ${p.pid})`).join(', ');
          pidsEl.textContent = list;
          pidsEl.title = list;
        } else {
          pidsEl.textContent = 'Не запущен';
        }
      }

      if (memEl) {
        memEl.textContent = isRunning ? `${statusRes.total_memory_mb} МБ` : '0 МБ';
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
          schedEl.innerHTML = `<span class="text-success">Установлено (${sched.state})</span> <small class="text-muted" style="font-size:0.7rem;">[Wake: ${sched.wake_to_run}]</small>`;
        } else {
          schedEl.innerHTML = '<span class="text-muted">Не установлено</span>';
        }
      }

      // Заполнение полей формы конфигурации
      const mode = (configRes.mode || statusRes.mode || 'hybrid').toLowerCase();
      const radioMode = document.querySelector(`input[name="telemetryModeRadio"][value="${mode}"]`);
      if (radioMode) radioMode.checked = true;

      const fastInt = configRes.interval_seconds || statusRes.interval_seconds || 5.0;
      const inputFast = document.getElementById('cfg-fast-interval');
      const valFast = document.getElementById('val-fast-interval');
      if (inputFast) inputFast.value = fastInt;
      if (valFast) valFast.textContent = `${fastInt}с`;

      const heavyInt = configRes.heavy_interval_seconds || statusRes.heavy_interval_seconds || 60.0;
      const inputHeavy = document.getElementById('cfg-heavy-interval');
      const valHeavy = document.getElementById('val-heavy-interval');
      if (inputHeavy) inputHeavy.value = heavyInt;
      if (valHeavy) valHeavy.textContent = `${heavyInt}с`;

      const topProcs = configRes.top_processes || statusRes.top_processes || 10;
      const selTop = document.getElementById('cfg-top-processes');
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
      console.warn('[AutoLogTab] Ошибка загрузки статуса службы телеметрии:', err);
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

      showToast('Сохранение параметров телеметрии...', 'info');
      const res = await apiPost('/api/autolog/telemetry/config', payload);
      showToast(res.message || 'Параметры телеметрии успешно сохранены!', 'success');
      await loadTelemetryServiceStatusAndConfig();
    } catch (err) {
      showToast(`Ошибка сохранения телеметрии: ${err.message}`, 'danger');
    }
  }

  async function controlTelemetryService(action) {
    try {
      showToast(`Выполняется: ${action}...`, 'info');
      const res = await apiPost('/api/autolog/telemetry/control', { action });
      showToast(`Действие '${action}' успешно выполнено!`, 'success');
      setTimeout(loadTelemetryServiceStatusAndConfig, 1000);
    } catch (err) {
      showToast(`Ошибка: ${err.message}`, 'danger');
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
        const valFast = document.getElementById('val-fast-interval');
        if (valFast) valFast.textContent = `${inputFast.value}с`;
      });
    }
    const inputHeavy = document.getElementById('cfg-heavy-interval');
    if (inputHeavy) {
      inputHeavy.addEventListener('input', () => {
        const valHeavy = document.getElementById('val-heavy-interval');
        if (valHeavy) valHeavy.textContent = `${inputHeavy.value}с`;
      });
    }

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

    // Вкладка службы телеметрии
    const btnTabTelemetry = document.getElementById('subtab-telemetry-service-btn');
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
