/**
 * =============================================================================
 * Process Name: Windows Telemetry Config Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт редактора файла конфигурации телеметрии Windows.
 *   Обеспечивает интерактивное визуальное и raw-JSON редактирование параметров
 *   с мгновенной синхронизацией и применением на лету.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/telemetry_config_tab/main.js?v=20261006_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/telemetry_config_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 03:32:00
 * =============================================================================
 */

(function () {
  'use strict';

  const API_BASE = '/api/windows/telemetry/config';
  let currentConfig = {};
  let currentRawJson = '';
  let activeTab = 'gui'; // 'gui' | 'json'

  const SENSOR_META = {
    cpu: { name: 'Процессор (CPU)', icon: 'bi-cpu', defaultInterval: 5.0, defaultMetrics: ['temperature', 'load', 'clocks'] },
    gpu: { name: 'Видеокарта (GPU)', icon: 'bi-gpu-card', defaultInterval: 10.0, defaultMetrics: ['temperature', 'load', 'memory', 'power'] },
    ram: { name: 'Оперативная память (RAM)', icon: 'bi-memory', defaultInterval: 10.0, defaultMetrics: ['usage', 'swap'] },
    disk: { name: 'Диски и разделы (Disk)', icon: 'bi-hdd', defaultInterval: 30.0, defaultMetrics: ['usage', 'io'] },
    network: { name: 'Сетевые адаптеры (Network)', icon: 'bi-ethernet', defaultInterval: 10.0, defaultMetrics: ['throughput', 'connections'] },
    sensors: { name: 'LHM Сенсоры и вентиляторы', icon: 'bi-fan', defaultInterval: 10.0, defaultMetrics: ['temperature', 'fan', 'voltage'] },
    internet: { name: 'Скорость Fast.com / Latency', icon: 'bi-globe2', defaultInterval: 3600.0, defaultMetrics: ['ping', 'download', 'upload', 'bufferbloat', 'latency_loaded'] },
    storage: { name: 'SMART здоровье накопителей', icon: 'bi-hdd-network', defaultInterval: 32000.0, defaultMetrics: ['smart_attributes', 'temperature', 'wear_level'] },
    device_flapping: { name: 'Детектор PnP Flapping', icon: 'bi-usb-symbol', defaultInterval: 30.0, defaultMetrics: ['connect_events', 'disconnect_events', 'flapping_count'] },
  };

  /**
   * Инициализация при монтировании вкладки
   */
  async function init() {
    bindEvents();
    await loadConfig();
  }

  /**
   * Привязка обработчиков событий
   */
  function bindEvents() {
    // Кнопка сохранения
    const btnSave = document.getElementById('tc-cfg-btn-save');
    if (btnSave) {
      btnSave.addEventListener('click', saveActiveConfig);
    }

    // Кнопка перечитывания
    const btnReload = document.getElementById('tc-cfg-btn-reload');
    if (btnReload) {
      btnReload.addEventListener('click', async () => {
        showAlert('Перечитывание конфигурации с диска...', 'info');
        await loadConfig();
      });
    }

    // Кнопка сброса к значениям по умолчанию
    const btnReset = document.getElementById('tc-cfg-btn-reset');
    if (btnReset) {
      btnReset.addEventListener('click', async () => {
        if (confirm('Сбросить конфигурацию телеметрии к исходным настройкам по умолчанию?')) {
          await resetConfigToDefault();
        }
      });
    }

    // Кнопка копирования пути к файлу
    const btnCopyPath = document.getElementById('tc-cfg-copy-path-btn');
    if (btnCopyPath) {
      btnCopyPath.addEventListener('click', () => {
        const pathEl = document.getElementById('tc-cfg-file-path');
        if (pathEl) {
          navigator.clipboard.writeText(pathEl.innerText.trim()).then(() => {
            showAlert('Путь к файлу скопирован в буфер обмена', 'success', 2500);
          });
        }
      });
    }

    // Переключение вкладок GUI / JSON
    const tabGuiBtn = document.getElementById('tc-tab-gui-btn');
    const tabJsonBtn = document.getElementById('tc-tab-json-btn');
    if (tabGuiBtn && tabJsonBtn) {
      tabGuiBtn.addEventListener('shown.bs.tab', () => {
        activeTab = 'gui';
        syncJsonToGui();
      });
      tabJsonBtn.addEventListener('shown.bs.tab', () => {
        activeTab = 'json';
        syncGuiToJson();
      });
    }

    // Форматирование JSON
    const btnFormatJson = document.getElementById('tc-btn-format-json');
    if (btnFormatJson) {
      btnFormatJson.addEventListener('click', () => {
        const editor = document.getElementById('tc-raw-json-editor');
        if (!editor) return;
        try {
          const parsed = JSON.parse(editor.value);
          editor.value = JSON.stringify(parsed, null, 2);
          hideJsonError();
          showAlert('JSON отформатирован', 'info', 2000);
        } catch (e) {
          showJsonError(e.message);
        }
      });
    }

    // Копирование JSON
    const btnCopyJson = document.getElementById('tc-btn-copy-json');
    if (btnCopyJson) {
      btnCopyJson.addEventListener('click', () => {
        const editor = document.getElementById('tc-raw-json-editor');
        if (editor) {
          navigator.clipboard.writeText(editor.value).then(() => {
            showAlert('JSON скопирован в буфер обмена', 'success', 2500);
          });
        }
      });
    }

    // Live-валидация JSON при вводе
    const jsonEditor = document.getElementById('tc-raw-json-editor');
    if (jsonEditor) {
      jsonEditor.addEventListener('input', () => {
        try {
          JSON.parse(jsonEditor.value);
          hideJsonError();
        } catch (e) {
          showJsonError(e.message);
        }
      });
    }

    // Закрытие алерта
    const alertCloseBtn = document.getElementById('tc-cfg-alert-close');
    if (alertCloseBtn) {
      alertCloseBtn.addEventListener('click', () => {
        const alertBox = document.getElementById('tc-cfg-alert');
        if (alertBox) alertBox.classList.add('d-none');
      });
    }
  }

  /**
   * Загрузка конфигурации с бэкенда
   */
  async function loadConfig() {
    try {
      const response = await fetch(API_BASE, { cache: 'no-cache' });
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        currentConfig = data.config || {};
        updateMeta(data.config_path, data.last_modified, currentConfig.mode, currentConfig.telemetry_mode);
        renderGuiForm(currentConfig);
        renderRawJson(currentConfig);
        showAlert('Конфигурация успешно загружена', 'success', 2500);
      } else {
        showAlert(data.message || 'Ошибка загрузки конфигурации', 'danger');
      }
    } catch (err) {
      console.error('Ошибка загрузки конфигурации телеметрии:', err);
      showAlert(`Не удалось загрузить конфигурацию: ${err.message}`, 'danger');
    }
  }

  /**
   * Обновление метаинформации о файле
   */
  function updateMeta(path, mtime, mode, telemetryMode) {
    const pathEl = document.getElementById('tc-cfg-file-path');
    if (pathEl && path) pathEl.innerText = path;

    const mtimeEl = document.getElementById('tc-cfg-mtime');
    if (mtimeEl && mtime) {
      try {
        const d = new Date(mtime);
        mtimeEl.innerText = d.toLocaleString('ru-RU');
      } catch (_) {
        mtimeEl.innerText = mtime;
      }
    }

    const tMode = (telemetryMode || 'telemetry').toUpperCase();
    const modeBadge = document.getElementById('tc-cfg-active-mode-badge');
    if (modeBadge) {
      modeBadge.innerText = `Режим: ${tMode}`;
      modeBadge.className = `badge border fs-8 ${
        tMode === 'TC' ? 'bg-warning-subtle text-warning border-warning-subtle' :
        'bg-primary-subtle text-primary border-primary-subtle'
      }`;
    }

    const currentModeStatus = document.getElementById('tc-current-mode-status');
    if (currentModeStatus) {
      currentModeStatus.innerText = tMode === 'TC' ? 'TC (РЕАЛЬНОЕ ВРЕМЯ)' : 'СТАНДАРТНЫЙ (TELEMETRY)';
      currentModeStatus.className = `badge border ${tMode === 'TC' ? 'bg-warning-subtle text-warning border-warning-subtle' : 'bg-primary-subtle text-primary border-primary-subtle'}`;
    }
  }

  /**
   * Отрисовка значений в элементах GUI формы
   */
  function renderGuiForm(cfg) {
    setVal('tc-field-telemetry-mode', cfg.telemetry_mode || 'telemetry');
    setVal('tc-field-standard-flush-interval', cfg.standard_flush_interval_seconds ?? 30.0);
    setVal('tc-field-tc-flush-interval', cfg.tc_flush_interval_seconds ?? 5.0);
    setVal('tc-field-tc-mode-timeout', cfg.tc_mode_timeout_seconds ?? 300.0);
    setVal('tc-field-max-db-size', cfg.max_db_size_mb ?? 100.0);

    setVal('tc-field-mode', cfg.mode || 'hybrid');
    setVal('tc-field-process-mode', cfg.process_mode || 'top_n');
    setVal('tc-field-interval', cfg.interval_seconds ?? 5.0);
    setVal('tc-field-heavy-interval', cfg.heavy_interval_seconds ?? 60.0);
    setVal('tc-field-top-processes', cfg.top_processes ?? 10);
    setVal('tc-field-agg-interval', cfg.aggregation_interval_seconds ?? 3600);
    setChecked('tc-field-low-priority', cfg.low_priority !== false);
    setChecked('tc-field-heavy-auto-switch', cfg.heavy_mode_auto_switch_enabled !== false);

    setVal('tc-field-retention-days', cfg.retention_days ?? 7);
    setVal('tc-field-db-cleanup-interval', cfg.db_cleanup_interval_seconds ?? 300.0);
    setVal('tc-field-flush-interval', cfg.flush_interval_seconds ?? 5.0);
    setVal('tc-field-buffer-mode', cfg.buffer_mode || 'memory');
    setVal('tc-field-buffer-size', cfg.buffer_size ?? 50);
    setChecked('tc-field-auto-vacuum', cfg.auto_vacuum_enabled !== false);

    const hc = cfg.heavy_collectors || {};
    setChecked('tc-hc-hw-sensors', hc.hardware_sensors !== false);
    setChecked('tc-hc-smart', hc.storage_smart !== false);
    setChecked('tc-hc-ping', hc.network_ping !== false);
    setChecked('tc-hc-wmi', hc.inventory_wmi === true);

    const w64 = cfg.w64_collector || {};
    setChecked('tc-w64-enabled', w64.enabled !== false);
    setChecked('tc-w64-file', w64.enable_file_monitoring !== false);
    setChecked('tc-w64-proc', w64.enable_process_monitoring !== false);
    setChecked('tc-w64-reg', w64.enable_registry_monitoring !== false);
    setChecked('tc-w64-net', w64.enable_network_monitoring !== false);
    setChecked('tc-w64-evlog', w64.enable_event_log_monitoring !== false);
    setChecked('tc-w64-etw-proc', w64.enable_process_trace !== false);
    setChecked('tc-w64-etw-disk', w64.enable_disk_trace !== false);

    renderSensorsTable(cfg.sensors || {});
  }

  /**
   * Отрисовка таблицы сенсоров
   */
  function renderSensorsTable(sensorsConfig) {
    const tbody = document.getElementById('tc-sensors-tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    const sensorKeys = Object.keys(SENSOR_META);

    // Добавляем также сенсоры, которые есть в конфиге, но не в SENSOR_META
    Object.keys(sensorsConfig).forEach((k) => {
      if (!sensorKeys.includes(k)) sensorKeys.push(k);
    });

    const countBadge = document.getElementById('tc-sensors-count-badge');
    if (countBadge) countBadge.innerText = `${sensorKeys.length} сенсоров`;

    sensorKeys.forEach((key) => {
      const sMeta = SENSOR_META[key] || {
        name: key,
        icon: 'bi-activity',
        defaultInterval: 10.0,
        defaultMetrics: [],
      };
      const sConf = sensorsConfig[key] || {
        enabled: true,
        interval_seconds: sMeta.defaultInterval,
        metrics: sMeta.defaultMetrics,
      };

      const tr = document.createElement('tr');
      tr.className = 'border-bottom border-secondary border-opacity-10';

      const isEnabled = sConf.enabled !== false;
      const intervalSec = sConf.interval_seconds ?? sMeta.defaultInterval;
      const metricsList = Array.isArray(sConf.metrics) ? sConf.metrics.join(', ') : '';

      tr.innerHTML = `
        <td class="text-center">
          <div class="form-check form-switch mb-0">
            <input class="form-check-input tc-sensor-enabled" type="checkbox" role="switch" data-sensor="${key}" ${isEnabled ? 'checked' : ''}>
          </div>
        </td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <i class="bi ${sMeta.icon} text-info"></i>
            <div>
              <span class="fw-semibold text-white">${sMeta.name}</span>
              <span class="text-secondary d-block fs-9 font-monospace">${key}</span>
            </div>
          </div>
        </td>
        <td>
          <div class="input-group input-group-sm" style="max-width: 120px;">
            <input type="number" step="0.5" min="0.1" class="form-control form-control-sm bg-dark text-white border-secondary tc-sensor-interval" data-sensor="${key}" value="${intervalSec}">
            <span class="input-group-text bg-dark text-muted border-secondary fs-9">с</span>
          </div>
        </td>
        <td>
          <span class="text-secondary fs-9 font-monospace" title="${metricsList}">${metricsList || '—'}</span>
        </td>
      `;

      tbody.appendChild(tr);
    });
  }

  /**
   * Сбор параметров из элементов GUI формы в объект
   */
  function gatherFormConfig() {
    const cfg = JSON.parse(JSON.stringify(currentConfig));

    cfg.telemetry_mode = getVal('tc-field-telemetry-mode') || 'telemetry';
    cfg.standard_flush_interval_seconds = parseFloat(getVal('tc-field-standard-flush-interval')) || 30.0;
    cfg.tc_flush_interval_seconds = parseFloat(getVal('tc-field-tc-flush-interval')) || 5.0;
    cfg.tc_mode_timeout_seconds = parseFloat(getVal('tc-field-tc-mode-timeout')) || 300.0;
    cfg.max_db_size_mb = parseFloat(getVal('tc-field-max-db-size')) || 100.0;

    cfg.mode = getVal('tc-field-mode') || 'hybrid';
    cfg.process_mode = getVal('tc-field-process-mode') || 'top_n';
    cfg.interval_seconds = parseFloat(getVal('tc-field-interval')) || 5.0;
    cfg.heavy_interval_seconds = parseFloat(getVal('tc-field-heavy-interval')) || 60.0;
    cfg.top_processes = parseInt(getVal('tc-field-top-processes'), 10) || 10;
    cfg.aggregation_interval_seconds = parseInt(getVal('tc-field-agg-interval'), 10) || 3600;
    cfg.low_priority = getChecked('tc-field-low-priority');
    cfg.heavy_mode_auto_switch_enabled = getChecked('tc-field-heavy-auto-switch');

    cfg.retention_days = parseInt(getVal('tc-field-retention-days'), 10) || 7;
    cfg.db_cleanup_interval_seconds = parseFloat(getVal('tc-field-db-cleanup-interval')) || 300.0;
    cfg.flush_interval_seconds = parseFloat(getVal('tc-field-flush-interval')) || 5.0;
    cfg.buffer_mode = getVal('tc-field-buffer-mode') || 'memory';
    cfg.buffer_size = parseInt(getVal('tc-field-buffer-size'), 10) || 50;
    cfg.auto_vacuum_enabled = getChecked('tc-field-auto-vacuum');

    cfg.heavy_collectors = cfg.heavy_collectors || {};
    cfg.heavy_collectors.hardware_sensors = getChecked('tc-hc-hw-sensors');
    cfg.heavy_collectors.storage_smart = getChecked('tc-hc-smart');
    cfg.heavy_collectors.network_ping = getChecked('tc-hc-ping');
    cfg.heavy_collectors.inventory_wmi = getChecked('tc-hc-wmi');

    cfg.w64_collector = cfg.w64_collector || {};
    cfg.w64_collector.enabled = getChecked('tc-w64-enabled');
    cfg.w64_collector.enable_file_monitoring = getChecked('tc-w64-file');
    cfg.w64_collector.enable_process_monitoring = getChecked('tc-w64-proc');
    cfg.w64_collector.enable_registry_monitoring = getChecked('tc-w64-reg');
    cfg.w64_collector.enable_network_monitoring = getChecked('tc-w64-net');
    cfg.w64_collector.enable_event_log_monitoring = getChecked('tc-w64-evlog');
    cfg.w64_collector.enable_process_trace = getChecked('tc-w64-etw-proc');
    cfg.w64_collector.enable_disk_trace = getChecked('tc-w64-etw-disk');

    cfg.sensors = cfg.sensors || {};
    document.querySelectorAll('.tc-sensor-enabled').forEach((cb) => {
      const sKey = cb.getAttribute('data-sensor');
      if (!sKey) return;
      cfg.sensors[sKey] = cfg.sensors[sKey] || {};
      cfg.sensors[sKey].enabled = cb.checked;
    });

    document.querySelectorAll('.tc-sensor-interval').forEach((inp) => {
      const sKey = inp.getAttribute('data-sensor');
      if (!sKey) return;
      cfg.sensors[sKey] = cfg.sensors[sKey] || {};
      cfg.sensors[sKey].interval_seconds = parseFloat(inp.value) || 5.0;
    });

    return cfg;
  }

  /**
   * Отрисовка текста в редакторе сырого JSON
   */
  function renderRawJson(cfg) {
    const editor = document.getElementById('tc-raw-json-editor');
    if (editor) {
      editor.value = JSON.stringify(cfg, null, 2);
      hideJsonError();
    }
  }

  /**
   * Синхронизация формы в JSON при переходе на вкладку JSON
   */
  function syncGuiToJson() {
    try {
      const updated = gatherFormConfig();
      currentConfig = updated;
      renderRawJson(updated);
    } catch (e) {
      console.warn('Ошибка сбора формы:', e);
    }
  }

  /**
   * Синхронизация JSON в форму при переходе на вкладку GUI
   */
  function syncJsonToGui() {
    const editor = document.getElementById('tc-raw-json-editor');
    if (!editor) return;
    try {
      const parsed = JSON.parse(editor.value);
      currentConfig = parsed;
      renderGuiForm(parsed);
      hideJsonError();
    } catch (e) {
      showJsonError(`Невозможно отобразить визуальную форму: ${e.message}`);
    }
  }

  /**
   * Сохранение активной конфигурации (из GUI или JSON)
   */
  async function saveActiveConfig() {
    const btnSave = document.getElementById('tc-cfg-btn-save');
    const originalText = btnSave ? btnSave.innerHTML : '';
    if (btnSave) {
      btnSave.disabled = true;
      btnSave.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span><span>Сохранение...</span>';
    }

    try {
      if (activeTab === 'json') {
        const editor = document.getElementById('tc-raw-json-editor');
        if (!editor) throw new Error('Редактор JSON не найден');
        const rawJson = editor.value;

        // Предварительная валидация
        JSON.parse(rawJson);

        const response = await fetch(`${API_BASE}/raw`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ raw_json: rawJson }),
        });

        const resData = await response.json();
        if (!response.ok || !resData.success) {
          throw new Error(resData.detail || resData.message || `Ошибка сервера ${response.status}`);
        }

        currentConfig = resData.config;
        renderGuiForm(currentConfig);
        updateMeta(resData.config_path, new Date().toISOString(), currentConfig.mode, currentConfig.telemetry_mode);
        showAlert('✅ Конфигурация телеметрии успешно сохранена и применена на лету!', 'success');
      } else {
        const updatedConfig = gatherFormConfig();
        const response = await fetch(API_BASE, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ config: updatedConfig }),
        });

        const resData = await response.json();
        if (!response.ok || !resData.success) {
          throw new Error(resData.detail || resData.message || `Ошибка сервера ${response.status}`);
        }

        currentConfig = resData.config;
        renderRawJson(currentConfig);
        updateMeta(resData.config_path, new Date().toISOString(), currentConfig.mode, currentConfig.telemetry_mode);
        showAlert('✅ Параметры телеметрии успешно сохранены и применены на лету!', 'success');
      }
    } catch (err) {
      console.error('Ошибка сохранения конфигурации:', err);
      showAlert(`❌ Ошибка сохранения: ${err.message}`, 'danger');
      if (activeTab === 'json') {
        showJsonError(err.message);
      }
    } finally {
      if (btnSave) {
        btnSave.disabled = false;
        btnSave.innerHTML = originalText;
      }
    }
  }

  /**
   * Сброс конфигурации к значениям по умолчанию
   */
  async function resetConfigToDefault() {
    try {
      const response = await fetch(`${API_BASE}/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();
      if (data.success) {
        currentConfig = data.config || {};
        updateMeta(data.config_path, new Date().toISOString(), currentConfig.mode, currentConfig.telemetry_mode);
        renderGuiForm(currentConfig);
        renderRawJson(currentConfig);
        showAlert('↺ Конфигурация телеметрии сброшена к значениям по умолчанию!', 'warning');
      } else {
        showAlert(data.message || 'Ошибка сброса конфигурации', 'danger');
      }
    } catch (err) {
      showAlert(`Не удалось сбросить конфигурацию: ${err.message}`, 'danger');
    }
  }

  /**
   * Показать плашку ошибки валидации JSON
   */
  function showJsonError(msg) {
    const errBox = document.getElementById('tc-json-error');
    const errText = document.getElementById('tc-json-error-text');
    const statusBadge = document.getElementById('tc-json-status');
    if (errBox && errText) {
      errText.innerText = msg;
      errBox.classList.remove('d-none');
    }
    if (statusBadge) {
      statusBadge.innerText = 'Ошибка синтаксиса';
      statusBadge.className = 'badge bg-danger-subtle text-danger border border-danger-subtle fs-8';
    }
  }

  /**
   * Скрыть плашку ошибки валидации JSON
   */
  function hideJsonError() {
    const errBox = document.getElementById('tc-json-error');
    const statusBadge = document.getElementById('tc-json-status');
    if (errBox) errBox.classList.add('d-none');
    if (statusBadge) {
      statusBadge.innerText = 'Синтаксис корректен';
      statusBadge.className = 'badge bg-success-subtle text-success border border-success-subtle fs-8';
    }
  }

  /**
   * Отображение Toast / Alert сообщения
   */
  function showAlert(msg, type = 'info', autoHideMs = 4000) {
    const alertBox = document.getElementById('tc-cfg-alert');
    const alertMsg = document.getElementById('tc-cfg-alert-msg');
    const alertIcon = document.getElementById('tc-cfg-alert-icon');
    if (!alertBox || !alertMsg) return;

    alertMsg.innerText = msg;
    alertBox.className = `alert alert-${type} alert-dismissible fade show mb-3 py-2 px-3 shadow-sm border`;

    if (alertIcon) {
      alertIcon.className =
        type === 'success' ? 'bi bi-check-circle-fill text-success fs-5' :
        type === 'danger' ? 'bi bi-exclamation-triangle-fill text-danger fs-5' :
        type === 'warning' ? 'bi bi-exclamation-circle-fill text-warning fs-5' :
        'bi bi-info-circle-fill text-info fs-5';
    }

    alertBox.classList.remove('d-none');

    if (autoHideMs > 0) {
      setTimeout(() => {
        if (!alertBox.classList.contains('d-none')) {
          alertBox.classList.add('d-none');
        }
      }, autoHideMs);
    }
  }

  // Вспомогательные утилиты для работы с элементами DOM
  function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val;
  }

  function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value : '';
  }

  function setChecked(id, val) {
    const el = document.getElementById(id);
    if (el) el.checked = Boolean(val);
  }

  function getChecked(id) {
    const el = document.getElementById(id);
    return el ? Boolean(el.checked) : false;
  }

  // Запуск при загрузке DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
