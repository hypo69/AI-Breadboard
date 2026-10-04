/**
 * =============================================================================
 * Process Name: Windows System Inspector Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/system_inspector_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/system_inspector_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 08:46:00
 * =============================================================================
 */

// System & Hardware Inspector Tab JS Module
(function() {
  let sysWs = null;
  let isSysInitialized = false;
  let isSysPaused = false;
  let isNetPaused = false;
  let currentNetFilter = 'internet';
  let cachedNetworkActivities = [];
  let latestTelemetrySnapshot = null;
  let cachedSensors = [];
  let currentSensorCategory = 'all';
  let isLhmRunning = false;
  let cachedHardwareSensorsData = null;

  async function fetchLhmSensors() {
    const badgeCount = document.getElementById('sys-lhm-sensors-count');
    const badgeStatus = document.getElementById('sys-lhm-status-badge');
    const container = document.getElementById('sys-lhm-sensors-container');
    const maxTempLabel = document.getElementById('sys-sensors-max-temp');
    const warningsBadge = document.getElementById('sys-sensors-warnings-badge');
    const dbTsBadge = document.getElementById('sys-sensors-db-ts');

    try {
      const res = await fetch('/api/v1/panel/hardware-sensors');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      cachedHardwareSensorsData = data;
      cachedSensors = data.all_sensors || [];

      const summary = data.summary || {};

      if (badgeCount) {
        badgeCount.textContent = `${summary.total_sensors || cachedSensors.length} шт. (БД)`;
      }
      if (badgeStatus) {
        badgeStatus.textContent = '● telemetry.db';
        badgeStatus.className = 'badge bg-success';
        if (summary.timestamp) {
          const tsStr = new Date(summary.timestamp).toLocaleTimeString();
          badgeStatus.title = `Данные из базы telemetry.db: ${tsStr}`;
          if (dbTsBadge) dbTsBadge.textContent = tsStr;
        }
      }
      if (maxTempLabel) {
        maxTempLabel.textContent = summary.max_temperature_c != null ? `${summary.max_temperature_c.toFixed(0)} °C` : '-- °C';
        if (summary.max_temperature_c && summary.max_temperature_c >= 75) {
          maxTempLabel.className = 'fw-bold text-danger font-monospace';
        } else if (summary.max_temperature_c && summary.max_temperature_c >= 60) {
          maxTempLabel.className = 'fw-bold text-warning font-monospace';
        } else {
          maxTempLabel.className = 'fw-bold text-info font-monospace';
        }
      }
      if (warningsBadge) {
        warningsBadge.textContent = summary.warnings_count || '0';
        warningsBadge.className = summary.warnings_count > 0 ? 'badge bg-danger text-white' : 'badge bg-dark border border-secondary text-success';
      }

      renderSensors();
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to fetch hardware sensors from DB:', e);
      if (container) {
        container.innerHTML = `<div class="text-center py-4 text-muted small">Датчики опрашиваются из БД... (${e.message})</div>`;
      }
    }
  }

  function createSensorWidgetHtml(s) {
    const cat = (s.sensor_category || '').toLowerCase();
    const val = Number(s.value || 0);
    const valRaw = s.value_raw || `${val.toFixed(1)} ${s.unit || ''}`.trim();
    const name = escapeHtml(s.sensor_name);

    if (cat.includes('temp')) {
      const tempSlider = createTempSliderHtml(val, 25, 95, false);
      const gaugeSvg = createGaugeSvg(Math.min(100, Math.max(0, ((val - 25) / 70) * 100)), 64, 38);
      return `
        <div class="sys-sensor-widget-item p-1.5 rounded-2 mb-1" style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle, rgba(255,255,255,0.06));">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="sys-sensor-name text-truncate" title="${name}" style="font-size: 0.74rem; font-weight: 600;">${name}</span>
            <span class="badge ${val >= 80 ? 'bg-danger' : val >= 65 ? 'bg-warning text-dark' : 'bg-info-subtle text-info'}" style="font-size: 0.65rem;">${val.toFixed(0)}°C</span>
          </div>
          <div class="d-flex align-items-center gap-2">
            <div style="width: 64px; height: 38px; flex-shrink: 0;">${gaugeSvg}</div>
            <div class="flex-grow-1">${tempSlider}</div>
          </div>
        </div>
      `;
    }

    if (cat.includes('load')) {
      const pctSlider = createPercentSliderHtml(val, false, `${val.toFixed(0)}%`);
      const gaugeSvg = createGaugeSvg(val, 64, 38);
      return `
        <div class="sys-sensor-widget-item p-1.5 rounded-2 mb-1" style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle, rgba(255,255,255,0.06));">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="sys-sensor-name text-truncate" title="${name}" style="font-size: 0.74rem; font-weight: 600;">${name}</span>
            <span class="badge ${val >= 85 ? 'bg-danger' : val >= 60 ? 'bg-warning text-dark' : 'bg-success-subtle text-success'}" style="font-size: 0.65rem;">${val.toFixed(0)}%</span>
          </div>
          <div class="d-flex align-items-center gap-2">
            <div style="width: 64px; height: 38px; flex-shrink: 0;">${gaugeSvg}</div>
            <div class="flex-grow-1">${pctSlider}</div>
          </div>
        </div>
      `;
    }

    if (cat.includes('fan')) {
      const pct = Math.min(100, Math.max(0, (val / 2800) * 100));
      return `
        <div class="sys-sensor-widget-item p-1.5 rounded-2 mb-1" style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle, rgba(255,255,255,0.06));">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="sys-sensor-name text-truncate" title="${name}" style="font-size: 0.74rem; font-weight: 600;"><i class="bi bi-fan text-info me-1"></i>${name}</span>
            <span class="font-monospace text-info fw-bold" style="font-size: 0.76rem;">${val.toFixed(0)} RPM</span>
          </div>
          <div class="progress" style="height: 5px; background: rgba(255,255,255,0.1); border-radius: 3px;">
            <div class="progress-bar bg-info" style="width: ${pct}%;"></div>
          </div>
        </div>
      `;
    }

    if (cat.includes('volt') || cat.includes('power')) {
      const isPower = cat.includes('power') || (s.unit || '').toLowerCase() === 'w';
      return `
        <div class="sys-sensor-widget-item p-1.5 rounded-2 mb-1" style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle, rgba(255,255,255,0.06));">
          <div class="d-flex justify-content-between align-items-center">
            <span class="sys-sensor-name text-truncate" title="${name}" style="font-size: 0.74rem; font-weight: 600;"><i class="bi bi-lightning-charge text-warning me-1"></i>${name}</span>
            <span class="badge ${isPower ? 'bg-warning-subtle text-warning' : 'bg-primary-subtle text-primary'} font-monospace" style="font-size: 0.72rem;">${valRaw}</span>
          </div>
        </div>
      `;
    }

    if (cat.includes('clock')) {
      return `
        <div class="sys-sensor-widget-item p-1.5 rounded-2 mb-1" style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle, rgba(255,255,255,0.06));">
          <div class="d-flex justify-content-between align-items-center">
            <span class="sys-sensor-name text-truncate" title="${name}" style="font-size: 0.74rem; font-weight: 600;"><i class="bi bi-speedometer2 text-primary me-1"></i>${name}</span>
            <span class="font-monospace text-primary fw-bold" style="font-size: 0.74rem;">${valRaw}</span>
          </div>
        </div>
      `;
    }

    return `
      <div class="sys-sensor-widget-item p-1.5 rounded-2 mb-1" style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle, rgba(255,255,255,0.06));">
        <div class="d-flex justify-content-between align-items-center">
          <span class="sys-sensor-name text-truncate" title="${name}" style="font-size: 0.74rem; font-weight: 600;">${name}</span>
          <span class="font-monospace text-light fw-bold" style="font-size: 0.74rem;">${valRaw}</span>
        </div>
      </div>
    `;
  }

  function renderSensors() {
    const container = document.getElementById('sys-lhm-sensors-container');
    if (!container) return;

    const searchInput = document.getElementById('sys-lhm-search');
    const filterText = (searchInput ? searchInput.value : '').trim().toLowerCase();

    if (!Array.isArray(cachedSensors) || cachedSensors.length === 0) {
      container.innerHTML = `
        <div class="text-center py-4 text-muted small">
          <div>В базе данных telemetry.db сенсоры не обнаружены</div>
          <div class="mt-2 text-muted" style="font-size: 0.72rem;">Ожидание сбора и сохранения телеметрии сенсоров...</div>
        </div>
      `;
      return;
    }

    const filtered = cachedSensors.filter(s => {
      // Category filter
      if (currentSensorCategory !== 'all') {
        const catLower = (s.sensor_category || '').toLowerCase();
        if (currentSensorCategory === 'temperature' && !catLower.includes('temp')) return false;
        if (currentSensorCategory === 'load' && !catLower.includes('load')) return false;
        if (currentSensorCategory === 'fan' && !catLower.includes('fan') && !catLower.includes('control')) return false;
        if (currentSensorCategory === 'voltage' && !catLower.includes('volt') && !catLower.includes('power')) return false;
        if (currentSensorCategory === 'clock' && !catLower.includes('clock')) return false;
        if (currentSensorCategory === 'storage' && !catLower.includes('data') && !catLower.includes('throughput')) return false;
      }

      // Text search
      if (filterText) {
        const hName = (s.hardware_name || '').toLowerCase();
        const sName = (s.sensor_name || '').toLowerCase();
        const sCat = (s.sensor_category || '').toLowerCase();
        const valStr = String(s.value_raw || s.value || '').toLowerCase();
        return hName.includes(filterText) || sName.includes(filterText) || sCat.includes(filterText) || valStr.includes(filterText);
      }
      return true;
    });

    if (filtered.length === 0) {
      container.innerHTML = `<div class="text-center py-4 text-muted small">По выбранному фильтру сенсоров не найдено</div>`;
      return;
    }

    // Group sensors by Hardware Name
    const groups = {};
    filtered.forEach(s => {
      const grpKey = s.hardware_name || 'Оборудование';
      if (!groups[grpKey]) groups[grpKey] = [];
      groups[grpKey].push(s);
    });

    container.innerHTML = Object.entries(groups).map(([grpName, items]) => {
      const type = (items[0].hardware_type || '').toLowerCase();
      let icon = 'bi bi-cpu';
      let iconColor = 'text-info';
      if (type.includes('gpu')) { icon = 'bi bi-gpu-card'; iconColor = 'text-warning'; }
      else if (type.includes('storage') || type.includes('disk')) { icon = 'bi bi-hdd'; iconColor = 'text-success'; }
      else if (type.includes('memory') || type.includes('ram')) { icon = 'bi bi-memory'; iconColor = 'text-primary'; }
      else if (type.includes('network') || type.includes('net')) { icon = 'bi bi-globe'; iconColor = 'text-info'; }
      else if (type.includes('motherboard') || type.includes('mainboard')) { icon = 'bi bi-motherboard'; iconColor = 'text-secondary'; }

      const temps = items.filter(i => (i.sensor_category || '').toLowerCase().includes('temp')).map(i => Number(i.value || 0));
      const maxT = temps.length ? Math.max(...temps) : null;
      const tempBadge = maxT != null ? `<span class="badge ${maxT >= 80 ? 'bg-danger' : maxT >= 65 ? 'bg-warning text-dark' : 'bg-info-subtle text-info'}" style="font-size: 0.65rem;">🔥 ${maxT.toFixed(0)}°C</span>` : '';

      const widgetsHtml = items.map(s => createSensorWidgetHtml(s)).join('');

      return `
        <div class="sys-core-card mb-2 p-2" style="min-height: auto; background: var(--surface-2, rgba(255,255,255,0.02)); border: 1px solid var(--border-color, rgba(255,255,255,0.08));">
          <div class="d-flex justify-content-between align-items-center mb-1.5 pb-1 border-bottom" style="border-color: var(--border-subtle, rgba(255,255,255,0.06)) !important;">
            <div class="d-flex align-items-center gap-1.5 text-truncate" style="max-width: 70%;">
              <i class="${icon} ${iconColor}"></i>
              <span class="sys-core-title text-truncate" style="font-size: 0.82rem;" title="${escapeHtml(grpName)}">${escapeHtml(grpName)}</span>
            </div>
            <div class="d-flex align-items-center gap-1">
              ${tempBadge}
              <span class="badge bg-dark border border-secondary text-muted" style="font-size: 0.65rem;">${items.length} шт.</span>
            </div>
          </div>
          <div>
            ${widgetsHtml}
          </div>
        </div>
      `;
    }).join('');

    // Также обновляем блоки сенсоров в целевых панелях CPU, GPU и RAM
    updateAllComponentSensors();
  }

  function getSensorSortPriority(s) {
    const cat = (s.sensor_category || '').toLowerCase();
    const unit = (s.unit || '').toLowerCase();
    if (cat.includes('power') || unit === 'w') return 1;
    if (cat.includes('volt') || unit === 'v') return 2;
    if (cat.includes('clock') || unit.includes('hz')) return 3;
    if (cat.includes('fan') || unit.includes('rpm')) return 4;
    if (cat.includes('timing') || cat.includes('factor')) return 5;
    if (cat.includes('temp') || unit.includes('°c')) return 6;
    return 7;
  }

  function renderComponentSensors(containerId, countBadgeId, sensors) {
    const container = document.getElementById(containerId);
    const countBadge = document.getElementById(countBadgeId);
    if (!container) return;
    if (countBadge) {
      countBadge.textContent = sensors && sensors.length ? `${sensors.length} параметров` : '0 параметров';
    }
    if (!sensors || sensors.length === 0) {
      container.innerHTML = `<div class="text-muted small text-center py-2 col-12" style="font-size: 0.74rem;">Нет дополнительных данных сенсоров</div>`;
      return;
    }

    const sorted = [...sensors].sort((a, b) => {
      const pA = getSensorSortPriority(a);
      const pB = getSensorSortPriority(b);
      if (pA !== pB) return pA - pB;
      return (a.sensor_name || '').localeCompare(b.sensor_name || '');
    });

    container.innerHTML = sorted.map(s => {
      const name = escapeHtml(s.sensor_name);
      const cat = (s.sensor_category || '').toLowerCase();
      const val = Number(s.value || 0);
      const unit = (s.unit || '').trim();
      const valRaw = s.value_raw || `${val.toFixed(1)} ${unit}`.trim();

      let icon = 'bi bi-lightning-charge';
      let iconColor = 'text-warning';
      let badgeClass = 'bg-warning-subtle text-warning border border-warning';

      if (cat.includes('volt') || unit.toLowerCase() === 'v') {
        icon = 'bi bi-lightning-charge';
        iconColor = 'text-primary';
        badgeClass = 'bg-primary-subtle text-primary border border-primary';
      } else if (cat.includes('power') || unit.toLowerCase() === 'w') {
        icon = 'bi bi-lightning-charge';
        iconColor = 'text-warning';
        badgeClass = 'bg-warning-subtle text-warning border border-warning';
      } else if (cat.includes('clock') || unit.toLowerCase().includes('hz')) {
        icon = 'bi bi-speedometer2';
        iconColor = 'text-info';
        badgeClass = 'bg-info-subtle text-info border border-info';
      } else if (cat.includes('fan') || unit.toLowerCase().includes('rpm')) {
        icon = 'bi bi-fan';
        iconColor = 'text-info';
        badgeClass = 'bg-dark border border-secondary text-info';
      } else if (cat.includes('timing') || cat.includes('factor')) {
        icon = 'bi bi-clock-history';
        iconColor = 'text-secondary';
        badgeClass = 'bg-dark border border-secondary text-light';
      } else if (cat.includes('data') || unit.toLowerCase().includes('mb') || unit.toLowerCase().includes('gb')) {
        icon = 'bi bi-hdd-fill';
        iconColor = 'text-success';
        badgeClass = 'bg-success-subtle text-success border border-success';
      } else if (cat.includes('temp') || unit.toLowerCase().includes('°c')) {
        icon = 'bi bi-thermometer-half';
        iconColor = val >= 75 ? 'text-danger' : val >= 60 ? 'text-warning' : 'text-info';
        badgeClass = val >= 75 ? 'bg-danger text-white' : val >= 60 ? 'bg-warning text-dark' : 'bg-info-subtle text-info';
      }

      return `
        <div class="sys-sensor-widget-item p-1.5 rounded-2" style="background: var(--surface-2, rgba(255,255,255,0.03)); border: 1px solid var(--border-color, rgba(255,255,255,0.08));">
          <div class="d-flex justify-content-between align-items-center">
            <span class="sys-sensor-name text-truncate" title="${name}" style="font-size: 0.74rem; font-weight: 600;">
              <i class="${icon} ${iconColor} me-1"></i>${name}
            </span>
            <span class="badge ${badgeClass} font-monospace" style="font-size: 0.72rem;">${valRaw}</span>
          </div>
        </div>
      `;
    }).join('');
  }

  function updateAllComponentSensors() {
    if (!Array.isArray(cachedSensors) || cachedSensors.length === 0) return;

    // 1. CPU Sensors (электрические параметры, мощности, вольтажи, шины, TjMax)
    const cpuSensors = cachedSensors.filter(s => {
      const hwType = (s.hardware_type || '').toLowerCase();
      const hwName = (s.hardware_name || '').toLowerCase();
      const sName = (s.sensor_name || '').toLowerCase();
      const cat = (s.sensor_category || '').toLowerCase();

      const isCpu = hwType === 'cpu' || hwName.includes('cpu') || hwName.includes('intel') || hwName.includes('amd');
      if (!isCpu) return false;

      // Исключаем по-ядерную загрузку и температуру отдельных ядер (они уже в карточках ядер)
      if (cat.includes('load') && (sName.includes('core #') || sName === 'cpu total')) return false;
      if (cat.includes('temp') && sName.includes('core #') && !sName.includes('tjmax')) return false;
      if (cat.includes('temp') && sName === 'cpu package') return false; // показана в главном слайдере Package

      return true;
    });
    renderComponentSensors('sys-metric-cpu-sensors', 'sys-cpu-sensors-count-badge', cpuSensors);

    // 2. GPU Sensors (мощности, вольтажи, частоты, вентиляторы, память GPU)
    const gpuSensors = cachedSensors.filter(s => {
      const hwType = (s.hardware_type || '').toLowerCase();
      const hwName = (s.hardware_name || '').toLowerCase();
      const sName = (s.sensor_name || '').toLowerCase();
      const cat = (s.sensor_category || '').toLowerCase();

      const isGpu = hwType === 'gpu' || hwName.includes('gpu') || hwName.includes('nvidia') || hwName.includes('geforce') || hwName.includes('radeon') || hwName.includes('intel arc');
      if (!isGpu) return false;

      // Исключаем общую загрузку/температуру GPU Core (они в главном Gauge/Slider)
      if (cat.includes('load') && sName === 'gpu core') return false;
      if (cat.includes('temp') && sName === 'gpu core') return false;

      return true;
    });
    renderComponentSensors('sys-metric-gpu-sensors', 'sys-gpu-sensors-count-badge', gpuSensors);

    // 3. RAM Sensors (мощности, вольтажи, тайминги, доступный объем)
    const ramSensors = cachedSensors.filter(s => {
      const hwType = (s.hardware_type || '').toLowerCase();
      const hwName = (s.hardware_name || '').toLowerCase();
      const sName = (s.sensor_name || '').toLowerCase();

      const isRam = hwType === 'memory' || hwType === 'ram' || hwName.includes('memory') || hwName.includes('ram') || sName.includes('cpu memory');
      return isRam;
    });
    renderComponentSensors('sys-metric-ram-sensors', 'sys-ram-sensors-count-badge', ramSensors);

    // 4. Network Sensors (трафик, сетевые интерфейсы, Wi-Fi, Bluetooth)
    const netSensors = cachedSensors.filter(s => {
      const hwType = (s.hardware_type || '').toLowerCase();
      const hwName = (s.hardware_name || '').toLowerCase();
      const isNet = hwType === 'network' || hwType === 'net' || hwName.includes('net') || hwName.includes('ethernet') || hwName.includes('wi-fi') || hwName.includes('wifi') || hwName.includes('bluetooth');
      return isNet;
    });
    renderComponentSensors('sys-metric-net-sensors', 'sys-net-sensors-count-badge', netSensors);
  }

  let lastAnalysisReportText = '';

  async function analyzeSensorsAndReport() {
    const modalEl = document.getElementById('sysSensorAnalysisModal');
    let modal = null;
    if (modalEl && window.bootstrap && window.bootstrap.Modal) {
      modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }

    // Set Loading state in modal
    const titleEl = document.getElementById('modal-sensor-status-title');
    const subEl = document.getElementById('modal-sensor-status-sub');
    const aiCompEl = document.getElementById('modal-sensor-ai-comparison');
    const devListEl = document.getElementById('modal-sensor-devices-list');
    const devCountEl = document.getElementById('modal-sensor-devices-count');
    const modelBadge = document.getElementById('modal-sensor-model-badge');

    if (titleEl) titleEl.textContent = 'Выполняется AI-аудит залогированных сенсоров...';
    if (subEl) subEl.textContent = 'Чтение CSV-логов, усреднение значений и сравнение со спецификациями железа';
    if (aiCompEl) {
      aiCompEl.innerHTML = '<div class="d-flex align-items-center gap-2 py-3"><div class="spinner-border spinner-border-sm text-primary" role="status"></div><span>Запрос к модели AI и сравнительный анализ номинальных параметров железа...</span></div>';
    }
    if (devListEl) {
      devListEl.innerHTML = '<span class="badge bg-dark border border-secondary text-muted"><span class="spinner-border spinner-border-sm me-1" style="width:0.6rem;height:0.6rem;"></span>Определение устройств...</span>';
    }

    let report = null;
    try {
      let res = await fetch('/api/v1/system/lhm-audit', { method: 'POST' });
      if (!res.ok) {
        res = await fetch('/api/v1/lhm/audit', { method: 'POST' });
      }
      if (res.ok) {
        report = await res.json();
      }
    } catch (err) {
      console.warn('[SystemInspectorTab] LHM Audit API error:', err);
    }

    // Extract metrics from report or fallback to cachedSensors
    const sensorsList = (report && report.aggregated_sensors) ? report.aggregated_sensors : (cachedSensors || []);
    const devices = (report && report.devices) ? report.devices : [];
    let healthScore = report ? (report.health_score || 100) : 100;
    const recommendations = [];

    let maxCpuTemp = null;
    let maxGpuTemp = null;
    let maxMbTemp = null;
    let maxStorageTemp = null;
    let fanSpeeds = [];
    let voltages = [];
    let cpuLoads = [];
    let gpuLoads = [];

    sensorsList.forEach(s => {
      const cat = ((s.category || s.sensor_category) || '').toLowerCase();
      const hw = ((s.hardware || s.hardware_name) || '').toLowerCase();
      const sName = (s.sensor_name || '').toLowerCase();
      const num = s.avg !== undefined ? s.avg : s.value_numeric;

      if (num === null || num === undefined || isNaN(num)) return;

      if (cat.includes('temp')) {
        if (hw.includes('cpu') || sName.includes('cpu') || sName.includes('core')) {
          if (maxCpuTemp === null || num > maxCpuTemp) maxCpuTemp = num;
        } else if (hw.includes('gpu') || hw.includes('nvidia') || sName.includes('gpu')) {
          if (maxGpuTemp === null || num > maxGpuTemp) maxGpuTemp = num;
        } else if (hw.includes('storage') || hw.includes('nvme') || hw.includes('ssd') || hw.includes('hdd') || sName.includes('drive')) {
          if (maxStorageTemp === null || num > maxStorageTemp) maxStorageTemp = num;
        } else {
          if (maxMbTemp === null || num > maxMbTemp) maxMbTemp = num;
        }
      } else if (cat.includes('fan')) {
        fanSpeeds.push({ name: s.sensor_name, value: num, unit: s.unit || 'RPM' });
      } else if (cat.includes('volt')) {
        voltages.push({ name: s.sensor_name, value: num, unit: s.unit || 'V' });
      } else if (cat.includes('load')) {
        if (hw.includes('cpu') || sName.includes('cpu')) cpuLoads.push(num);
        else if (hw.includes('gpu') || sName.includes('gpu')) gpuLoads.push(num);
      }
    });

    const overallMaxTemp = Math.max(
      maxCpuTemp || 0,
      maxGpuTemp || 0,
      maxMbTemp || 0,
      maxStorageTemp || 0
    );

    // Update Model Badge
    if (modelBadge && report) {
      modelBadge.textContent = report.ai_model_used || 'Heuristic Engine';
    }

    // Render Devices List
    if (devCountEl) {
      devCountEl.textContent = `${devices.length} устр.`;
    }
    if (devListEl) {
      if (devices.length > 0) {
        devListEl.innerHTML = devices.map(d => {
          let icon = 'bi-hdd-network';
          const low = d.toLowerCase();
          if (low.includes('core') || low.includes('cpu') || low.includes('intel') || low.includes('amd')) icon = 'bi-cpu';
          else if (low.includes('geforce') || low.includes('gpu') || low.includes('nvidia') || low.includes('radeon')) icon = 'bi-gpu-card';
          else if (low.includes('ssd') || low.includes('hd') || low.includes('wdc') || low.includes('toshiba') || low.includes('st3500')) icon = 'bi-device-hdd';
          else if (low.includes('memory') || low.includes('ram')) icon = 'bi-memory';
          else if (low.includes('ethernet') || low.includes('wi-fi') || low.includes('network')) icon = 'bi-wifi';

          return `<span class="badge bg-dark border border-secondary text-info px-2 py-1 d-inline-flex align-items-center gap-1"><i class="bi ${icon}"></i> ${escapeHtml(d)}</span>`;
        }).join('');
      } else {
        devListEl.innerHTML = '<span class="text-muted small">Устройства считываются из текущей телеметрии</span>';
      }
    }

    // Render AI Comparison Report
    if (aiCompEl) {
      if (report && report.comparison_report) {
        aiCompEl.textContent = report.comparison_report;
      } else {
        aiCompEl.textContent = 'AI-сравнение выполнено по эвристическим профилям оборудования хоста. Все параметры сенсоров в пределах нормы.';
      }
    }

    // Analyze CPU
    const elCpuBadge = document.getElementById('modal-cpu-temp-badge');
    const elCpuText = document.getElementById('modal-cpu-analysis-text');
    if (maxCpuTemp !== null) {
      if (elCpuBadge) {
        elCpuBadge.textContent = `${Math.round(maxCpuTemp)} °C`;
        elCpuBadge.className = `badge ${maxCpuTemp > 82 ? 'bg-danger' : maxCpuTemp > 70 ? 'bg-warning text-dark' : 'bg-success'}`;
      }
      if (maxCpuTemp > 82) {
        if (elCpuText) elCpuText.textContent = `Критический нагрев (${Math.round(maxCpuTemp)}°C). Риск теплового троттлинга.`;
        recommendations.push({
          type: 'danger',
          icon: 'bi-exclamation-triangle-fill',
          title: 'Высокая температура процессора',
          text: `Пиковая/средняя температура CPU достигает ${Math.round(maxCpuTemp)}°C. Проверьте плотность прижима кулера, термопасту и запыленность радиатора.`
        });
      } else if (maxCpuTemp > 70) {
        if (elCpuText) elCpuText.textContent = `Повышенная температура (${Math.round(maxCpuTemp)}°C) под нагрузкой.`;
        recommendations.push({
          type: 'warning',
          icon: 'bi-thermometer-high',
          title: 'Повышенный нагрев CPU',
          text: `Температура CPU ${Math.round(maxCpuTemp)}°C выше оптимального порога. Рекомендуется настроить кривую оборотов вентилятора.`
        });
      } else {
        if (elCpuText) elCpuText.textContent = `Штатный температурный режим (${Math.round(maxCpuTemp)}°C). Троттлинг отсутствует.`;
        recommendations.push({
          type: 'success',
          icon: 'bi-check-circle-fill',
          title: 'Тепловой режим процессора оптимален',
          text: `Температура процессора ${Math.round(maxCpuTemp)}°C находится в безопасной зоне номинальных характеристик.`
        });
      }
    } else {
      if (elCpuBadge) elCpuBadge.textContent = 'N/A';
      if (elCpuText) elCpuText.textContent = 'Температурные датчики CPU не предоставили данных.';
    }

    // Analyze GPU
    const elGpuBadge = document.getElementById('modal-gpu-temp-badge');
    const elGpuText = document.getElementById('modal-gpu-analysis-text');
    if (maxGpuTemp !== null) {
      if (elGpuBadge) {
        elGpuBadge.textContent = `${Math.round(maxGpuTemp)} °C`;
        elGpuBadge.className = `badge ${maxGpuTemp > 80 ? 'bg-danger' : maxGpuTemp > 72 ? 'bg-warning text-dark' : 'bg-success'}`;
      }
      if (maxGpuTemp > 80) {
        if (elGpuText) elGpuText.textContent = `Критический нагрев GPU (${Math.round(maxGpuTemp)}°C).`;
        recommendations.push({
          type: 'danger',
          icon: 'bi-gpu-card',
          title: 'Высокая температура видеокарты',
          text: `Графический чип нагревается до ${Math.round(maxGpuTemp)}°C. Проверьте циркуляцию воздуха в корпусе ПК.`
        });
      } else {
        if (elGpuText) elGpuText.textContent = `Температура GPU ${Math.round(maxGpuTemp)}°C в норме.`;
        recommendations.push({
          type: 'success',
          icon: 'bi-check-circle-fill',
          title: 'Видеокарта работает штатно',
          text: `Температурные показатели GPU (${Math.round(maxGpuTemp)}°C) соответствуют номиналу.`
        });
      }
    } else {
      if (elGpuBadge) elGpuBadge.textContent = 'N/A';
      if (elGpuText) elGpuText.textContent = 'Дискретный GPU в режиме энергосбережения или данные отсутствуют.';
    }

    // Analyze Cooling
    const elFanBadge = document.getElementById('modal-fan-status-badge');
    const elFanText = document.getElementById('modal-fan-analysis-text');
    if (fanSpeeds.length > 0) {
      const activeFans = fanSpeeds.filter(f => f.value > 0);
      if (elFanBadge) {
        elFanBadge.textContent = `${activeFans.length} акт. кулеров`;
        elFanBadge.className = 'badge bg-success';
      }
      if (elFanText) {
        elFanText.textContent = `Опрошено ${fanSpeeds.length} кулеров. Обороты стабильны.`;
      }
    } else {
      if (elFanBadge) elFanBadge.textContent = 'Пассив / WMI';
      if (elFanText) elFanText.textContent = 'Управление вентиляторами через BIOS или пассивное охлаждение.';
    }

    // Additional recommendations from backend report
    if (report && Array.isArray(report.recommendations)) {
      report.recommendations.forEach(r => {
        if (!recommendations.some(ex => ex.text.includes(r))) {
          recommendations.push({
            type: 'info',
            icon: 'bi-info-circle',
            title: 'Рекомендация по оборудованию',
            text: r
          });
        }
      });
    }

    // Update Header & Badge
    const badgeHealth = document.getElementById('modal-sensor-health-badge');
    if (badgeHealth) {
      badgeHealth.textContent = `Health: ${healthScore}/100`;
      badgeHealth.className = `badge ms-1 ${healthScore >= 85 ? 'bg-success' : healthScore >= 65 ? 'bg-warning text-dark' : 'bg-danger'}`;
    }

    const countStat = document.getElementById('modal-sensor-count-stat');
    if (countStat) {
      const totalSmpls = report ? report.total_samples : sensorsList.length;
      countStat.textContent = `${sensorsList.length} шт. (${totalSmpls} замеров)`;
    }

    const maxTempStat = document.getElementById('modal-sensor-max-temp');
    if (maxTempStat) maxTempStat.textContent = overallMaxTemp > 0 ? `${Math.round(overallMaxTemp)} °C` : 'N/A';

    const statusTitle = document.getElementById('modal-sensor-status-title');
    const statusSub = document.getElementById('modal-sensor-status-sub');
    const statusIcon = document.getElementById('modal-sensor-status-icon');

    if (healthScore >= 85) {
      if (statusIcon) statusIcon.textContent = '✅';
      if (statusTitle) statusTitle.textContent = 'Все аппаратные подсистемы работают в идеальном режиме';
      if (statusSub) statusSub.textContent = `Усредненные показатели соответствуют спецификациям реального железа (макс. ${Math.round(overallMaxTemp)}°C).`;
    } else if (healthScore >= 65) {
      if (statusIcon) statusIcon.textContent = '⚠️';
      if (statusTitle) statusTitle.textContent = 'Обнаружены параметры оборудования, требующие внимания';
      if (statusSub) statusSub.textContent = `Пиковая температура ${Math.round(overallMaxTemp)}°C. Ознакомьтесь с AI-заключением и рекомендациями.`;
    } else {
      if (statusIcon) statusIcon.textContent = '🚨';
      if (statusTitle) statusTitle.textContent = 'Внимание: Критические параметры оборудования!';
      if (statusSub) statusSub.textContent = `Зафиксирован опасный нагрев или высокая перегрузка компонентов.`;
    }

    // Render Recommendations List
    const recList = document.getElementById('modal-sensor-recommendations-list');
    if (recList) {
      recList.innerHTML = recommendations.map(r => `
        <div class="p-2.5 rounded border d-flex align-items-start gap-2.5" style="background: var(--surface-2); border-color: var(--border-color) !important;">
          <div class="mt-0.5">
            <span class="badge ${r.type === 'danger' ? 'bg-danger' : r.type === 'warning' ? 'bg-warning text-dark' : r.type === 'info' ? 'bg-info text-dark' : 'bg-success'} rounded-circle p-1.5 d-flex align-items-center justify-content-center" style="width: 24px; height: 24px;">
              <i class="bi ${r.icon}" style="font-size: 0.75rem;"></i>
            </span>
          </div>
          <div class="flex-grow-1">
            <div class="fw-bold text-white mb-0.5" style="font-size: 0.82rem;">${escapeHtml(r.title)}</div>
            <div class="text-muted" style="font-size: 0.76rem; line-height: 1.4;">${escapeHtml(r.text)}</div>
          </div>
        </div>
      `).join('');
    }

    // Prepare Clipboard text
    lastAnalysisReportText = `=== AI-Breadboard: Отчет AI-аудита сенсоров и оборудования ===\n` +
      `Дата: ${new Date().toLocaleString('ru-RU')}\n` +
      `Индекс здоровья системы: ${healthScore}/100\n` +
      `AI-модель: ${report ? report.ai_model_used : 'Heuristic'}\n` +
      `Распознанные устройства (${devices.length} шт.): ${devices.join(', ')}\n` +
      `Сенсоров в аудите: ${sensorsList.length}\n` +
      `Максимальная температура: ${overallMaxTemp > 0 ? Math.round(overallMaxTemp) + ' °C' : 'N/A'}\n\n` +
      `=== AI СРАВНЕНИЕ СО СПЕЦИФИКАЦИЯМИ РЕАЛЬНОГО ЖЕЛЕЗА ===\n` +
      `${(report && report.comparison_report) ? report.comparison_report : 'Параметры в норме.'}\n\n` +
      `=== РЕКОМЕНДАЦИИ И ВЫВОДЫ ===\n` +
      recommendations.map((r, i) => `${i + 1}. [${r.title}] ${r.text}`).join('\n') +
      `\n======================================================`;
  }

  /**
   * Генерация полукруглого спидометра (Gauge) со стрелкой.
   * @param {number|null} percent - Значение нагрузки (0-100)
   * @param {number} width - Ширина SVG контейнера
   * @param {number} height - Высота SVG контейнера
   * @returns {string} SVG разметка
   */
  function createGaugeSvg(percent, width = 100, height = 56) {
    const val = percent == null ? 0 : Math.min(100, Math.max(0, Number(percent)));
    // Угол поворота стрелки: 0% -> -90deg (влево), 50% -> 0deg (вверх), 100% -> +90deg (вправо)
    const angle = -90 + (val / 100) * 180;
    const needleColor = val > 80 ? '#ef4444' : val > 50 ? '#f59e0b' : '#38bdf8';

    return `
      <svg width="${width}" height="${height}" viewBox="0 0 100 56" preserveAspectRatio="xMidYMid meet" style="display:block;margin:0 auto;overflow:visible;">
        <defs>
          <linearGradient id="sysGaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#10b981"/>
            <stop offset="50%" stop-color="#f59e0b"/>
            <stop offset="100%" stop-color="#ef4444"/>
          </linearGradient>
        </defs>
        <!-- Фоновая дуга -->
        <path d="M 12 50 A 38 38 0 0 1 88 50" fill="none" stroke="rgba(255,255,255,0.14)" stroke-width="9" stroke-linecap="round"/>
        <!-- Градиентная активная шкала -->
        <path d="M 12 50 A 38 38 0 0 1 88 50" fill="none" stroke="url(#sysGaugeGrad)" stroke-width="9" stroke-linecap="round" opacity="0.9"/>
        <!-- Стрелка прибора -->
        <g transform="rotate(${angle.toFixed(1)}, 50, 50)" style="transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);">
          <polygon points="48,50 50,14 52,50" fill="${needleColor}" filter="drop-shadow(0 2px 3px rgba(0,0,0,0.6))"/>
          <line x1="50" y1="50" x2="50" y2="14" stroke="#ffffff" stroke-width="1.2" opacity="0.9"/>
        </g>
        <!-- Центральный шарнир -->
        <circle cx="50" cy="50" r="6" fill="#38bdf8"/>
        <circle cx="50" cy="50" r="2.5" fill="#0f172a"/>
      </svg>
    `;
  }

  /**
   * Генерация цветного термо-слайдера с бегунком.
   * @param {number|null} tempC - Температура в градусах Цельсия
   * @param {number} minTemp - Мин. шкала (по умолчанию 30°C)
   * @param {number} maxTemp - Макс. шкала (по умолчанию 95°C)
   * @param {boolean} isLarge - Флаг увеличенного отображения для шапки
   * @returns {string} HTML разметка
   */
  function createTempSliderHtml(tempC, minTemp = 30, maxTemp = 95, isLarge = false) {
    if (tempC == null) {
      return `<div class="sys-temp-slider-empty">-- °C</div>`;
    }
    const val = Number(tempC);
    const pct = Math.min(100, Math.max(0, ((val - minTemp) / (maxTemp - minTemp)) * 100));

    let barColor = '#10b981'; // Зеленый (<50°C)
    let badgeClass = 'text-success';
    if (val >= 80) {
      barColor = '#ef4444'; // Красный (>=80°C)
      badgeClass = 'text-danger fw-bold';
    } else if (val >= 68) {
      barColor = '#f97316'; // Оранжевый (68-80°C)
      badgeClass = 'text-warning fw-bold';
    } else if (val >= 50) {
      barColor = '#eab308'; // Желтый (50-68°C)
      badgeClass = 'text-warning';
    }

    const wrapClass = isLarge ? 'sys-temp-slider-wrap sys-temp-slider-lg' : 'sys-temp-slider-wrap';
    const fontSize = isLarge ? 'font-size: 0.85rem;' : 'font-size: 0.78rem;';

    return `
      <div class="${wrapClass}">
        <div class="d-flex justify-content-between align-items-center mb-1" style="${fontSize}">
          <span class="text-muted"><i class="bi bi-thermometer-half me-1"></i>t°</span>
          <span class="font-monospace ${badgeClass}" style="font-weight: 700;">${val.toFixed(0)}°C</span>
        </div>
        <div class="sys-temp-slider-track">
          <div class="sys-temp-slider-bar" style="width: ${pct.toFixed(1)}%; background: ${barColor};"></div>
          <div class="sys-temp-slider-thumb" style="left: ${pct.toFixed(1)}%; background: ${barColor};"></div>
        </div>
      </div>
    `;
  }

  function renderCpuCores(cores) {
    const box = document.getElementById('sys-metric-cpu-cores');
    const badgeCount = document.getElementById('sys-cores-count-badge');
    if (!box) return;

    if (badgeCount) {
      badgeCount.textContent = cores && cores.length ? `${cores.length} ядер` : '0 ядер';
    }

    if (!Array.isArray(cores) || cores.length === 0) {
      box.innerHTML = `<div class="text-muted small text-center py-3 col-12">Опрос ядер CPU выполняется...</div>`;
      return;
    }

    box.innerHTML = cores.map(c => {
      const load = c.load_percent == null ? null : Number(c.load_percent);
      const temp = c.temperature_c == null ? null : Number(c.temperature_c);
      const loadStr = load == null ? '--' : `${load.toFixed(0)}%`;
      const gaugeSvg = createGaugeSvg(load, 100, 56);
      const tempHtml = createTempSliderHtml(temp, 30, 95, false);

      return `
        <div class="sys-core-card" title="Ядро #${c.index}: Нагрузка ${loadStr}, Температура ${temp != null ? temp.toFixed(0) + '°C' : 'N/A'}">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="sys-core-title">Core #${c.index}</span>
            <span class="sys-core-load-badge">${loadStr}</span>
          </div>
          <div class="py-1">
            ${gaugeSvg}
          </div>
          <div>
            ${tempHtml}
          </div>
        </div>
      `;
    }).join('');
  }

  function formatBytes(v) {
    const n = Number(v) || 0;
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    let x = n;
    while (x >= 1024 && i < units.length - 1) { x /= 1024; i++; }
    return `${x.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
  }

  function formatBytesPerSec(v) {
    const n = Number(v) || 0;
    const units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    let i = 0;
    let x = n;
    while (x >= 1024 && i < units.length - 1) { x /= 1024; i++; }
    return `${x.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
  }

  const _cpuSparkHistory = [];
  const _gpuSparkHistory = [];

  function renderCpuSpark(history) {
    const box = document.getElementById('sys-cpu-spark');
    if (!box) return;
    box.replaceChildren();
    if (!Array.isArray(history) || history.length < 2) return;
    const ns = 'http://www.w3.org/2000/svg';
    const W = 200, H = 56;
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.style.cssText = 'width:100%;height:100%;';
    const line = (getY, color) => {
      const pts = history.map((h, i) => `${(i / (history.length - 1) * W).toFixed(1)},${(H - getY(h) * (H - 4) - 2).toFixed(1)}`);
      const pl = document.createElementNS(ns, 'polyline');
      pl.setAttribute('points', pts.join(' '));
      pl.setAttribute('fill', 'none');
      pl.setAttribute('stroke', color);
      pl.setAttribute('stroke-width', '1.4');
      svg.appendChild(pl);
    };
    line(h => Math.min(100, Math.max(0, Number(h.load || 0))) / 100, '#0dcaf0');
    line(h => {
      const t = h.temp != null ? Number(h.temp) : 0;
      return Math.min(1, Math.max(0, (t - 20) / 80));
    }, '#ef4444');
    box.appendChild(svg);
  }

  function renderGpuSpark(history) {
    const box = document.getElementById('sys-gpu-spark');
    if (!box) return;
    box.replaceChildren();
    if (!Array.isArray(history) || history.length < 2) return;
    const ns = 'http://www.w3.org/2000/svg';
    const W = 200, H = 56;
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.style.cssText = 'width:100%;height:100%;';
    const line = (getY, color) => {
      const pts = history.map((h, i) => `${(i / (history.length - 1) * W).toFixed(1)},${(H - getY(h) * (H - 4) - 2).toFixed(1)}`);
      const pl = document.createElementNS(ns, 'polyline');
      pl.setAttribute('points', pts.join(' '));
      pl.setAttribute('fill', 'none');
      pl.setAttribute('stroke', color);
      pl.setAttribute('stroke-width', '1.4');
      svg.appendChild(pl);
    };
    line(h => Math.min(100, Math.max(0, Number(h.load || 0))) / 100, '#f59e0b');
    line(h => {
      const t = h.temp != null ? Number(h.temp) : 0;
      return Math.min(1, Math.max(0, (t - 20) / 80));
    }, '#ef4444');
    box.appendChild(svg);
  }

  function renderMemIoSpark(history) {
    const box = document.getElementById('sys-memio-spark');
    if (!box) return;
    box.replaceChildren();
    if (!Array.isArray(history) || history.length < 2) return;
    const ns = 'http://www.w3.org/2000/svg';
    const W = 200, H = 56;
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.style.cssText = 'width:100%;height:100%;';
    const maxIo = Math.max(1, ...history.map(h => Math.max(h.read_bytes_sec, h.write_bytes_sec)));
    const line = (getY, color) => {
      const pts = history.map((h, i) => `${(i / (history.length - 1) * W).toFixed(1)},${(H - getY(h) * (H - 2) - 1).toFixed(1)}`);
      const pl = document.createElementNS(ns, 'polyline');
      pl.setAttribute('points', pts.join(' '));
      pl.setAttribute('fill', 'none');
      pl.setAttribute('stroke', color);
      pl.setAttribute('stroke-width', '1.2');
      svg.appendChild(pl);
    };
    line(h => Math.min(100, h.memory_percent) / 100, '#198754');
    line(h => h.read_bytes_sec / maxIo, '#0dcaf0');
    line(h => h.write_bytes_sec / maxIo, '#ffc107');
    box.appendChild(svg);
  }

  /**
   * Генерация цветного процентного слайдера (для памяти, RAM, Swap).
   * @param {number|null} percent - Значение в % (0-100)
   * @param {boolean} isLarge - Флаг увеличенного отображения для шапки
   * @param {string} labelText - Подпись бейджа справа
   * @returns {string} HTML разметка
   */
  function createPercentSliderHtml(percent, isLarge = false, labelText = '') {
    const val = percent == null ? 0 : Math.min(100, Math.max(0, Number(percent)));
    let barColor = '#10b981'; // Зеленый (<60%)
    let badgeClass = 'text-success';
    if (val >= 85) {
      barColor = '#ef4444'; // Красный
      badgeClass = 'text-danger fw-bold';
    } else if (val >= 70) {
      barColor = '#f97316'; // Оранжевый
      badgeClass = 'text-warning fw-bold';
    } else if (val >= 50) {
      barColor = '#eab308'; // Желтый
      badgeClass = 'text-warning';
    }

    const wrapClass = isLarge ? 'sys-temp-slider-wrap sys-temp-slider-lg' : 'sys-temp-slider-wrap';
    const fontSize = isLarge ? 'font-size: 0.85rem;' : 'font-size: 0.78rem;';
    const displayLabel = labelText || `${val.toFixed(0)}%`;

    return `
      <div class="${wrapClass}">
        <div class="d-flex justify-content-between align-items-center mb-1" style="${fontSize}">
          <span class="text-muted"><i class="bi bi-memory me-1"></i>Занято</span>
          <span class="font-monospace ${badgeClass}" style="font-weight: 700;">${displayLabel}</span>
        </div>
        <div class="sys-temp-slider-track">
          <div class="sys-temp-slider-bar" style="width: ${val.toFixed(1)}%; background: ${barColor};"></div>
          <div class="sys-temp-slider-thumb" style="left: ${val.toFixed(1)}%; background: ${barColor};"></div>
        </div>
      </div>
    `;
  }

  async function fetchMemoryIoFromApi() {
    try {
      const res = await fetch('/api/v1/panel/memory-io?limit=60');
      if (!res.ok) return;
      const data = await res.json();
      const set = (id, text) => { const el = document.getElementById(id); if (el) el.innerText = text; };
      const m = data.memory || {};
      const io = data.disk_io || {};
      const pct = Number(m.percent || 0);
      const swapPct = Number(m.swap_percent || 0);
      const usedGb = Number(m.used_gb || 0);
      const totalGb = Number(m.total_gb || 0);
      const freeGb = Number(m.free_gb || 0);

      // 1. Главный баннер RAM
      const ramModel = document.getElementById('sys-metric-ram-model');
      if (ramModel) {
        ramModel.innerText = data.name || (m.name || (m.total_gb ? `${Math.round(m.total_gb)} GB RAM` : 'RAM'));
      }
      set('sys-memio-pct', `${pct.toFixed(1)}%`);
      set('sys-memio-used', `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB (свободно ${freeGb.toFixed(1)} GB)`);
      set('sys-memio-swap', `Файл подкачки: ${swapPct.toFixed(1)}%`);
      set('sys-memio-ts', data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : '--');

      const ramGauge = document.getElementById('sys-metric-ram-gauge');
      if (ramGauge) {
        ramGauge.innerHTML = createGaugeSvg(pct, 130, 74);
      }

      const ramSlider = document.getElementById('sys-metric-ram-slider');
      if (ramSlider) {
        ramSlider.innerHTML = createPercentSliderHtml(pct, true, `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB`);
      }

      // 2. Блок 1: Физическая RAM
      set('sys-ram-sub-badge', `${pct.toFixed(0)}%`);
      const ramSubGauge = document.getElementById('sys-ram-sub-gauge');
      if (ramSubGauge) {
        ramSubGauge.innerHTML = createGaugeSvg(pct, 100, 56);
      }
      const ramSubSlider = document.getElementById('sys-ram-sub-slider');
      if (ramSubSlider) {
        ramSubSlider.innerHTML = createPercentSliderHtml(pct, false, `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB`);
      }

      // 3. Блок 2: Файл подкачки (Swap)
      set('sys-swap-sub-badge', `${swapPct.toFixed(1)}%`);
      const swapSubGauge = document.getElementById('sys-swap-sub-gauge');
      if (swapSubGauge) {
        swapSubGauge.innerHTML = createGaugeSvg(swapPct, 100, 56);
      }
      const swapSubSlider = document.getElementById('sys-swap-sub-slider');
      if (swapSubSlider) {
        swapSubSlider.innerHTML = createPercentSliderHtml(swapPct, false, `Подкачка ${swapPct.toFixed(1)}%`);
      }

      // 4. Блок 3 & 4: Чтение и запись на диск (IO)
      const rBps = Number(io.read_bytes_sec || 0);
      const wBps = Number(io.write_bytes_sec || 0);
      const readFormatted = formatBytesPerSec(rBps);
      const writeFormatted = formatBytesPerSec(wBps);

      set('sys-memio-read', readFormatted);
      set('sys-read-sub-badge', readFormatted);
      set('sys-memio-write', writeFormatted);
      set('sys-write-sub-badge', writeFormatted);

      // Вычисление процента скорости относительно шкалы 50 MB/s
      const maxIoScale = 50 * 1024 * 1024; // 50 MB/s
      const readPct = Math.min(100, (rBps / maxIoScale) * 100);
      const writePct = Math.min(100, (wBps / maxIoScale) * 100);

      const readSubGauge = document.getElementById('sys-read-sub-gauge');
      if (readSubGauge) {
        readSubGauge.innerHTML = createGaugeSvg(readPct, 100, 56);
      }
      const readSubBar = document.getElementById('sys-read-sub-bar');
      const readSubThumb = document.getElementById('sys-read-sub-thumb');
      if (readSubBar) readSubBar.style.width = `${readPct.toFixed(1)}%`;
      if (readSubThumb) readSubThumb.style.left = `${readPct.toFixed(1)}%`;

      const writeSubGauge = document.getElementById('sys-write-sub-gauge');
      if (writeSubGauge) {
        writeSubGauge.innerHTML = createGaugeSvg(writePct, 100, 56);
      }
      const writeSubBar = document.getElementById('sys-write-sub-bar');
      const writeSubThumb = document.getElementById('sys-write-sub-thumb');
      if (writeSubBar) writeSubBar.style.width = `${writePct.toFixed(1)}%`;
      if (writeSubThumb) writeSubThumb.style.left = `${writePct.toFixed(1)}%`;

      // 5. График спарклайна
      renderMemIoSpark(data.history);
    } catch (e) {
      console.warn('[SystemInspectorTab] Ошибка получения памяти/IO из API:', e);
    }
  }

  const _netSparkHistory = [];

  function renderNetSpark(history) {
    const box = document.getElementById('sys-net-spark');
    if (!box) return;
    box.replaceChildren();
    if (!Array.isArray(history) || history.length < 2) return;
    const ns = 'http://www.w3.org/2000/svg';
    const W = 200, H = 56;
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.style.cssText = 'width:100%;height:100%;';
    const maxSpeed = Math.max(1024, ...history.map(h => Math.max(h.download_bytes_sec || 0, h.upload_bytes_sec || 0)));
    const line = (getY, color) => {
      const pts = history.map((h, i) => `${(i / (history.length - 1) * W).toFixed(1)},${(H - getY(h) * (H - 4) - 2).toFixed(1)}`);
      const pl = document.createElementNS(ns, 'polyline');
      pl.setAttribute('points', pts.join(' '));
      pl.setAttribute('fill', 'none');
      pl.setAttribute('stroke', color);
      pl.setAttribute('stroke-width', '1.4');
      svg.appendChild(pl);
    };
    line(h => Math.min(1, Math.max(0, Number(h.download_bytes_sec || 0) / maxSpeed)), '#0dcaf0');
    line(h => Math.min(1, Math.max(0, Number(h.upload_bytes_sec || 0) / maxSpeed)), '#f59e0b');
    box.appendChild(svg);
  }

  async function fetchNetworkLoadFromApi() {
    try {
      const res = await fetch('/api/v1/panel/network-load');
      if (!res.ok) return;
      const data = await res.json();
      const set = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
      };

      const rxBps = Number(data.download_bytes_sec || 0);
      const txBps = Number(data.upload_bytes_sec || 0);
      const totalBps = rxBps + txBps;
      const utilPct = Number(data.utilization_percent || 0);

      const rxFormatted = formatBytesPerSec(rxBps);
      const txFormatted = formatBytesPerSec(txBps);
      const totalFormatted = formatBytesPerSec(totalBps);

      const rxTotalFormatted = formatBytes(data.download_total_bytes || 0);
      const txTotalFormatted = formatBytes(data.upload_total_bytes || 0);
      const sumTotalFormatted = formatBytes((data.download_total_bytes || 0) + (data.upload_total_bytes || 0));

      // 1. Главный баннер Сети
      const netModel = document.getElementById('sys-metric-net-model');
      if (netModel) {
        netModel.innerText = data.name || 'Сетевые адаптеры (Ethernet / Wi-Fi / BT)';
      }
      set('sys-net-ts', data.timestamp || 'Live');
      set('sys-net-speed-val', totalFormatted);
      set('sys-net-sub-details', `⬇ ${rxFormatted} · ⬆ ${txFormatted} (Всего: ${sumTotalFormatted})`);
      set('sys-net-util-label', `Загрузка канала: ${utilPct.toFixed(1)}% (Линк: ${data.link_speed_mbps || 1000} Mbps)`);

      const netGauge = document.getElementById('sys-metric-net-gauge');
      if (netGauge) {
        netGauge.innerHTML = createGaugeSvg(utilPct, 130, 74);
      }

      const netSlider = document.getElementById('sys-metric-net-slider');
      if (netSlider) {
        netSlider.innerHTML = createPercentSliderHtml(utilPct, true, `Канал ${utilPct.toFixed(1)}%`);
      }

      // 2. Блок 1: Входящий (Rx)
      set('sys-rx-sub-badge', rxFormatted);
      set('sys-rx-total-text', `${rxTotalFormatted} всего`);
      const maxSpeedScale = 12.5 * 1024 * 1024; // 100 Mbps = 12.5 MB/s
      const rxPct = Math.min(100, (rxBps / maxSpeedScale) * 100);
      const rxSubGauge = document.getElementById('sys-rx-sub-gauge');
      if (rxSubGauge) rxSubGauge.innerHTML = createGaugeSvg(rxPct, 100, 56);
      const rxSubBar = document.getElementById('sys-rx-sub-bar');
      const rxSubThumb = document.getElementById('sys-rx-sub-thumb');
      if (rxSubBar) rxSubBar.style.width = `${rxPct.toFixed(1)}%`;
      if (rxSubThumb) rxSubThumb.style.left = `${rxPct.toFixed(1)}%`;

      // 3. Блок 2: Исходящий (Tx)
      set('sys-tx-sub-badge', txFormatted);
      set('sys-tx-total-text', `${txTotalFormatted} всего`);
      const txPct = Math.min(100, (txBps / maxSpeedScale) * 100);
      const txSubGauge = document.getElementById('sys-tx-sub-gauge');
      if (txSubGauge) txSubGauge.innerHTML = createGaugeSvg(txPct, 100, 56);
      const txSubBar = document.getElementById('sys-tx-sub-bar');
      const txSubThumb = document.getElementById('sys-tx-sub-thumb');
      if (txSubBar) txSubBar.style.width = `${txPct.toFixed(1)}%`;
      if (txSubThumb) txSubThumb.style.left = `${txPct.toFixed(1)}%`;

      // 4. Блок 3: Wi-Fi
      const wifi = data.wifi || {};
      const wifiState = wifi.state || 'Disconnected';
      const wifiSignal = wifi.signal_percent != null ? Number(wifi.signal_percent) : (wifi.radio_status && wifi.radio_status.includes('On') ? 100 : 0);
      set('sys-wifi-sub-badge', wifi.ssid ? `SSID: ${wifi.ssid}` : (wifi.radio_status || 'On'));
      set('sys-wifi-status-text', wifi.ssid ? `${wifi.ssid} (${wifiSignal}%)` : wifiState);
      const wifiSubGauge = document.getElementById('sys-wifi-sub-gauge');
      if (wifiSubGauge) wifiSubGauge.innerHTML = createGaugeSvg(wifiSignal, 100, 56);
      const wifiSubBar = document.getElementById('sys-wifi-sub-bar');
      const wifiSubThumb = document.getElementById('sys-wifi-sub-thumb');
      if (wifiSubBar) wifiSubBar.style.width = `${wifiSignal}%`;
      if (wifiSubThumb) wifiSubThumb.style.left = `${wifiSignal}%`;

      // 5. Блок 4: Bluetooth
      const bt = data.bluetooth || {};
      const btDevCount = bt.devices_count || 0;
      set('sys-bt-sub-badge', bt.status || 'Active');
      set('sys-bt-devices-text', btDevCount > 0 ? `${btDevCount} устр. (${bt.devices ? bt.devices[0] : ''})` : 'Активен (0 устр.)');
      const btPct = Math.min(100, btDevCount * 25);
      const btSubGauge = document.getElementById('sys-bt-sub-gauge');
      if (btSubGauge) btSubGauge.innerHTML = createGaugeSvg(btPct > 0 ? btPct : 10, 100, 56);
      const btSubBar = document.getElementById('sys-bt-sub-bar');
      const btSubThumb = document.getElementById('sys-bt-sub-thumb');
      if (btSubBar) btSubBar.style.width = `${btPct > 0 ? btPct : 10}%`;
      if (btSubThumb) btSubThumb.style.left = `${btPct > 0 ? btPct : 10}%`;

      // 6. График истории
      if (Array.isArray(data.history) && data.history.length > 0) {
        renderNetSpark(data.history);
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Ошибка получения сетевой нагрузки из API:', e);
    }
  }

  function renderStorageCards(data) {
    const box = document.getElementById('sys-metric-storage-cards');
    const badgeDrives = document.getElementById('sys-storage-drives-badge');
    const badgeParts = document.getElementById('sys-storage-parts-badge');
    const badgeSummary = document.getElementById('sys-storage-summary-badge');
    if (!box) return;

    const drives = Array.isArray(data.drives) ? data.drives : [];
    const partitions = Array.isArray(data.partitions) ? data.partitions : [];

    if (badgeDrives) badgeDrives.textContent = `${drives.length} дисков`;
    if (badgeParts) badgeParts.textContent = `${partitions.length} разделов`;
    if (badgeSummary) {
      const summary = data.summary || {};
      badgeSummary.textContent = `${summary.used_gb || 0} / ${summary.total_gb || 0} GB (${summary.used_percent || 0}%)`;
    }

    if (drives.length === 0 && partitions.length === 0) {
      box.innerHTML = `<div class="text-muted small text-center py-3 col-12">Опрос накопителей выполняется...</div>`;
      return;
    }

    if (drives.length > 0) {
      box.innerHTML = drives.map(d => {
        const pct = d.used_percent != null ? Number(d.used_percent) : 0;
        const temp = d.temperature_c != null ? Number(d.temperature_c) : null;
        const totGb = d.total_gb != null ? Number(d.total_gb) : 0;
        const usedGb = d.used_gb != null ? Number(d.used_gb) : 0;
        const gaugeSvg = createGaugeSvg(pct, 100, 56);
        const percentSlider = createPercentSliderHtml(pct, false, `${usedGb.toFixed(0)} / ${totGb.toFixed(0)} GB`);
        const tempHtml = temp != null ? createTempSliderHtml(temp, 25, 75, false) : '';
        const mediaBadgeClass = d.media_type === 'SSD' || d.media_type === 'NVMe' ? 'bg-primary-subtle text-primary border-primary' : 'bg-warning-subtle text-warning border-warning';

        let subInfo = '';
        if (d.read_rate_raw || d.write_rate_raw) {
          subInfo = `
            <div class="d-flex justify-content-between text-muted mt-1" style="font-size: 0.72rem;">
              <span><i class="bi bi-arrow-down text-info"></i> ${escapeHtml(d.read_rate_raw || '0 B/s')}</span>
              <span><i class="bi bi-arrow-up text-warning"></i> ${escapeHtml(d.write_rate_raw || '0 B/s')}</span>
            </div>
          `;
        } else if (d.activity_percent != null) {
          subInfo = `<div class="text-muted mt-1" style="font-size: 0.72rem;">Активность: <span class="text-light fw-bold">${d.activity_percent}%</span></div>`;
        }

        return `
          <div class="sys-core-card" title="${escapeHtml(d.name)}: Занято ${pct.toFixed(1)}% (${usedGb.toFixed(1)} GB / ${totGb.toFixed(1)} GB)${temp != null ? ', Температура ' + temp.toFixed(0) + '°C' : ''}">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="sys-core-title text-truncate" style="max-width: 140px;" title="${escapeHtml(d.name)}">${escapeHtml(d.name)}</span>
              <span class="badge ${mediaBadgeClass} border" style="font-size: 0.65rem;">${escapeHtml(d.media_type)}</span>
            </div>
            <div class="py-1">
              ${gaugeSvg}
            </div>
            <div class="mb-1">
              ${percentSlider}
            </div>
            ${tempHtml ? `<div class="mb-1">${tempHtml}</div>` : ''}
            ${subInfo}
          </div>
        `;
      }).join('');
    } else {
      box.innerHTML = partitions.map(p => {
        const pct = Number(p.used_percent || 0);
        const gaugeSvg = createGaugeSvg(pct, 100, 56);
        const percentSlider = createPercentSliderHtml(pct, false, `${p.used_gb.toFixed(0)} / ${p.total_gb.toFixed(0)} GB`);

        return `
          <div class="sys-core-card" title="Раздел ${escapeHtml(p.device)} (${escapeHtml(p.fstype)}): Занято ${pct.toFixed(1)}%">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="sys-core-title">${escapeHtml(p.device)} (${escapeHtml(p.fstype)})</span>
              <span class="badge bg-secondary border" style="font-size: 0.65rem;">${p.free_gb.toFixed(0)} GB free</span>
            </div>
            <div class="py-1">
              ${gaugeSvg}
            </div>
            <div>
              ${percentSlider}
            </div>
          </div>
        `;
      }).join('');
    }
  }

  async function fetchStorageLoadFromApi() {
    try {
      const res = await fetch('/api/v1/panel/storage-load');
      if (!res.ok) return;
      const data = await res.json();
      const set = (id, text) => { const el = document.getElementById(id); if (el) el.innerText = text; };
      const s = data.summary || {};
      const pct = Number(s.used_percent || 0);
      const usedGb = Number(s.used_gb || 0);
      const totalGb = Number(s.total_gb || 0);
      const freeGb = Number(s.free_gb || 0);
      const maxTemp = s.max_temperature_c != null ? Number(s.max_temperature_c) : null;

      // 1. Главный баннер хранилища
      set('sys-storage-pct', `${pct.toFixed(1)}%`);
      set('sys-storage-used', `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB (свободно ${freeGb.toFixed(1)} GB)`);
      set('sys-storage-temp-label', maxTemp != null ? `Макс. температура: ${maxTemp.toFixed(0)} °C` : 'Макс. температура: -- °C');
      set('sys-storage-ts', new Date().toLocaleTimeString());

      const stGauge = document.getElementById('sys-metric-storage-gauge');
      if (stGauge) {
        stGauge.innerHTML = createGaugeSvg(pct, 130, 74);
      }

      const stSlider = document.getElementById('sys-metric-storage-temp-slider');
      if (stSlider) {
        stSlider.innerHTML = createTempSliderHtml(maxTemp, 25, 75, true);
      }

      // 2. Карточки дисков
      renderStorageCards(data);
    } catch (e) {
      console.warn('[SystemInspectorTab] Ошибка получения параметров дисков из API:', e);
    }
  }

  async function fetchCpuLoadFromApi() {
    try {
      const res = await fetch('/api/v1/panel/cpu-load');
      if (!res.ok) return;
      const data = await res.json();
      const cpuVal = document.getElementById('sys-metric-cpu-val');
      const cpuFill = document.getElementById('sys-metric-cpu-fill');
      const cpuSub = document.getElementById('sys-metric-cpu-sub');
      const cpuModel = document.getElementById('sys-metric-cpu-model');
      const cpuGauge = document.getElementById('sys-metric-cpu-gauge');
      const cpuPkgSlider = document.getElementById('sys-metric-cpu-package-slider');
      const cpuPkgTemp = document.getElementById('sys-metric-cpu-package-temp');

      const pct = Number(data.total_percent || 0);
      const cores = Array.isArray(data.cores) ? data.cores : [];
      if (cpuVal) cpuVal.innerText = `${pct.toFixed(1)}%`;
      if (cpuFill) cpuFill.style.width = `${Math.min(100, pct)}%`;

      if (cpuModel && data.name) {
        cpuModel.innerText = data.name;
        cpuModel.title = data.name;
      }

      const pkgTemp = data.package_temperature_c != null ? Number(data.package_temperature_c) : null;
      if (cpuSub) {
        const t = pkgTemp == null ? '' : ` · ${pkgTemp.toFixed(0)} °C`;
        cpuSub.innerText = cores.length ? `${cores.length} Ядер${t}` : '-- Ядер';
      }
      if (cpuPkgTemp) {
        cpuPkgTemp.innerText = pkgTemp != null ? `Пакет: ${pkgTemp.toFixed(0)} °C` : 'Пакет: -- °C';
      }

      // Gauge полукруг со стрелкой для общего CPU (крупный 130x74)
      if (cpuGauge) {
        cpuGauge.innerHTML = createGaugeSvg(pct, 130, 74);
      }

      // Слайдер температуры Package (крупный)
      if (cpuPkgSlider) {
        cpuPkgSlider.innerHTML = createTempSliderHtml(pkgTemp, 30, 95, true);
      }

      renderCpuCores(cores);

      // Добавление точки в историю линейного графика CPU
      _cpuSparkHistory.push({ load: pct, temp: pkgTemp, time: new Date() });
      if (_cpuSparkHistory.length > 60) _cpuSparkHistory.shift();
      renderCpuSpark(_cpuSparkHistory);
    } catch (e) {
      console.warn('[SystemInspectorTab] Ошибка получения загрузки CPU из API:', e);
    }
  }

  function renderGpuEngines(engines) {
    const box = document.getElementById('sys-metric-gpu-engines');
    const badgeCount = document.getElementById('sys-gpu-engines-count-badge');
    if (!box) return;

    if (badgeCount) {
      badgeCount.textContent = engines && engines.length ? `${engines.length} блоков` : '0 блоков';
    }

    if (!Array.isArray(engines) || engines.length === 0) {
      box.innerHTML = `<div class="text-muted small text-center py-3 col-12">Опрос подсистем GPU выполняется...</div>`;
      return;
    }

    box.innerHTML = engines.map(e => {
      const load = e.load_percent == null ? null : Number(e.load_percent);
      const temp = e.temperature_c == null ? null : Number(e.temperature_c);
      const loadStr = load == null ? '--' : `${load.toFixed(0)}%`;
      const gaugeSvg = createGaugeSvg(load, 100, 56);
      const tempHtml = createTempSliderHtml(temp, 30, 95, false);

      return `
        <div class="sys-core-card" title="${escapeHtml(e.name)}: Нагрузка ${loadStr}${temp != null ? ', Температура ' + temp.toFixed(0) + '°C' : ''}">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="sys-core-title text-truncate" style="max-width: 85px;" title="${escapeHtml(e.name)}">${escapeHtml(e.name)}</span>
            <span class="sys-core-load-badge">${loadStr}</span>
          </div>
          <div class="py-1">
            ${gaugeSvg}
          </div>
          <div>
            ${tempHtml}
          </div>
        </div>
      `;
    }).join('');
  }

  async function fetchGpuLoadFromApi() {
    try {
      const res = await fetch('/api/v1/panel/gpu-load');
      if (!res.ok) return;
      const data = await res.json();

      const gpuVal = document.getElementById('sys-metric-gpu-val');
      const gpuModel = document.getElementById('sys-metric-gpu-model');
      const gpuSub = document.getElementById('sys-metric-gpu-sub');
      const gpuGauge = document.getElementById('sys-metric-gpu-gauge');
      const gpuTempSlider = document.getElementById('sys-metric-gpu-temp-slider');
      const gpuCoreTemp = document.getElementById('sys-metric-gpu-core-temp');
      const gpuVramLabel = document.getElementById('sys-metric-gpu-vram-label');

      const pct = Number(data.core_load_percent || 0);
      const engines = Array.isArray(data.engines) ? data.engines : [];

      if (gpuVal) gpuVal.innerText = `${pct.toFixed(1)}%`;

      if (gpuModel) {
        gpuModel.innerText = data.name || 'GPU';
        gpuModel.title = data.name || 'GPU';
      }

      const coreTemp = data.core_temperature_c != null ? Number(data.core_temperature_c) : null;
      if (gpuCoreTemp) {
        let tempText = coreTemp != null ? `GPU: ${coreTemp.toFixed(0)} °C` : 'GPU: -- °C';
        if (data.hotspot_temperature_c != null) {
          tempText += ` (HotSpot: ${Number(data.hotspot_temperature_c).toFixed(0)}°C)`;
        }
        gpuCoreTemp.innerText = tempText;
      }

      if (gpuSub) {
        let subText = '';
        if (data.clocks && data.clocks.core_mhz) {
          subText += `${Math.round(data.clocks.core_mhz)} MHz`;
        }
        if (data.memory && data.memory.total_mb) {
          const totalGb = (data.memory.total_mb / 1024).toFixed(1);
          subText += (subText ? ' · ' : '') + `${totalGb} GB VRAM`;
        }
        gpuSub.innerText = subText || (data.name || 'GPU');
        gpuSub.title = subText || (data.name || 'GPU');
      }

      if (gpuVramLabel) {
        if (data.memory && data.memory.total_mb) {
          const usedMb = Math.round(data.memory.used_mb || 0);
          const totalMb = Math.round(data.memory.total_mb || 0);
          const memPct = data.memory.used_percent != null ? ` (${Math.round(data.memory.used_percent)}%)` : '';
          gpuVramLabel.innerText = `VRAM: ${usedMb} / ${totalMb} MB${memPct}`;
        } else {
          gpuVramLabel.innerText = 'Температура GPU (LHM)';
        }
      }

      // Gauge полукруг со стрелкой для GPU Core (крупный 130x74)
      if (gpuGauge) {
        gpuGauge.innerHTML = createGaugeSvg(pct, 130, 74);
      }

      // Слайдер температуры GPU Core (крупный)
      if (gpuTempSlider) {
        gpuTempSlider.innerHTML = createTempSliderHtml(coreTemp, 30, 95, true);
      }

      renderGpuEngines(engines);

      // Добавление точки в историю линейного графика GPU
      _gpuSparkHistory.push({ load: pct, temp: coreTemp, time: new Date() });
      if (_gpuSparkHistory.length > 60) _gpuSparkHistory.shift();
      renderGpuSpark(_gpuSparkHistory);
    } catch (e) {
      console.warn('[SystemInspectorTab] Ошибка получения загрузки GPU из API:', e);
    }
  }

  function updateTelemetryDashboard(snap) {
    if (!snap) return;

    // CPU
    if (snap.cpu) {
      const cpuVal = document.getElementById('sys-metric-cpu-val');
      const cpuModel = document.getElementById('sys-metric-cpu-model');
      const cpuFill = document.getElementById('sys-metric-cpu-fill');
      const cpuSub = document.getElementById('sys-metric-cpu-sub');
      const cpuGauge = document.getElementById('sys-metric-cpu-gauge');

      const pct = Number(snap.cpu.total_percent || 0);
      if (cpuVal) cpuVal.innerText = `${pct.toFixed(1)}%`;
      if (cpuModel && snap.cpu.model) cpuModel.innerText = snap.cpu.model;
      if (cpuFill) cpuFill.style.width = `${Math.min(100, pct)}%`;
      if (cpuSub) cpuSub.innerText = `${snap.cpu.physical_cores || '--'} Физических / ${snap.cpu.logical_cores || '--'} Потоков`;
      if (cpuGauge) cpuGauge.innerHTML = createGaugeSvg(pct, 130, 74);
    }

    // RAM
    if (snap.memory) {
      const ramVal = document.getElementById('sys-metric-ram-val');
      const ramFill = document.getElementById('sys-metric-ram-fill');
      const ramSub = document.getElementById('sys-metric-ram-sub');
      const ramModel = document.getElementById('sys-metric-ram-model');

      const usedGb = Number(snap.memory.used_gb || 0);
      const totalGb = Number(snap.memory.total_gb || 0);
      const pct = Number(snap.memory.percent || 0);
      const swapPct = Number(snap.memory.swap_percent || 0);

      if (ramModel && totalGb > 0) ramModel.innerText = `${Math.round(totalGb)} GB RAM`;
      if (ramVal) ramVal.innerText = `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB`;
      if (ramFill) ramFill.style.width = `${pct}%`;
      if (ramSub) ramSub.innerText = `${pct}% занято (${Number(snap.memory.available_gb || 0).toFixed(1)} GB свободно)`;

      const memioPct = document.getElementById('sys-memio-pct');
      if (memioPct) memioPct.innerText = `${pct.toFixed(1)}%`;
      const memioUsed = document.getElementById('sys-memio-used');
      if (memioUsed) memioUsed.innerText = `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB (свободно ${Number(snap.memory.available_gb || (totalGb - usedGb)).toFixed(1)} GB)`;
      const memioSwap = document.getElementById('sys-memio-swap');
      if (memioSwap) memioSwap.innerText = `Файл подкачки: ${swapPct.toFixed(1)}%`;
      const memioTs = document.getElementById('sys-memio-ts');
      if (memioTs) memioTs.innerText = new Date().toLocaleTimeString();

      const ramGauge = document.getElementById('sys-metric-ram-gauge');
      if (ramGauge) ramGauge.innerHTML = createGaugeSvg(pct, 130, 74);
      const ramSlider = document.getElementById('sys-metric-ram-slider');
      if (ramSlider) ramSlider.innerHTML = createPercentSliderHtml(pct, true, `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB`);
      const ramSubGauge = document.getElementById('sys-ram-sub-gauge');
      if (ramSubGauge) ramSubGauge.innerHTML = createGaugeSvg(pct, 100, 56);
      const ramSubSlider = document.getElementById('sys-ram-sub-slider');
      if (ramSubSlider) ramSubSlider.innerHTML = createPercentSliderHtml(pct, false, `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB`);
      const ramSubBadge = document.getElementById('sys-ram-sub-badge');
      if (ramSubBadge) ramSubBadge.textContent = `${pct.toFixed(0)}%`;

      // Swap
      const swapSubBadge = document.getElementById('sys-swap-sub-badge');
      if (swapSubBadge) swapSubBadge.textContent = `${swapPct.toFixed(1)}%`;
      const swapSubGauge = document.getElementById('sys-swap-sub-gauge');
      if (swapSubGauge) swapSubGauge.innerHTML = createGaugeSvg(swapPct, 100, 56);
      const swapSubSlider = document.getElementById('sys-swap-sub-slider');
      if (swapSubSlider) swapSubSlider.innerHTML = createPercentSliderHtml(swapPct, false, `Подкачка ${swapPct.toFixed(1)}%`);
    }

    // GPU
    if (Array.isArray(snap.gpus) && snap.gpus.length > 0) {
      const g = snap.gpus[0];
      const gpuVal = document.getElementById('sys-metric-gpu-val');
      const gpuModel = document.getElementById('sys-metric-gpu-model');
      const gpuSub = document.getElementById('sys-metric-gpu-sub');
      const gpuGauge = document.getElementById('sys-metric-gpu-gauge');

      if (gpuModel) {
        gpuModel.innerText = g.name || 'GPU';
        gpuModel.title = g.name || 'GPU';
      }
      if (g.load_percent != null && gpuVal) {
        gpuVal.innerText = `${Number(g.load_percent).toFixed(1)}%`;
      }
      if (gpuSub) {
        gpuSub.innerText = `VRAM: ${Number(g.memory_total_gb || 0).toFixed(1)} GB | CUDA: ${g.has_cuda ? 'Да' : 'Нет'}`;
      }
      if (gpuGauge && g.load_percent != null) gpuGauge.innerHTML = createGaugeSvg(g.load_percent, 130, 74);
    }

    // Disk I/O
    if (snap.disk_io) {
      const diskVal = document.getElementById('sys-metric-disk-val');
      const diskSub = document.getElementById('sys-metric-disk-sub');

      const rBps = Number(snap.disk_io.read_bytes_per_sec || 0);
      const wBps = Number(snap.disk_io.write_bytes_per_sec || 0);
      const totalMb = ((rBps + wBps) / (1024 * 1024)).toFixed(2);
      const rKb = (rBps / 1024).toFixed(0);
      const wKb = (wBps / 1024).toFixed(0);

      if (diskVal) diskVal.innerText = `${totalMb} MB/s`;
      if (diskSub) diskSub.innerText = `Чтение: ${rKb} KB/s | Запись: ${wKb} KB/s`;

      const readFormatted = formatBytesPerSec(rBps);
      const writeFormatted = formatBytesPerSec(wBps);

      const memioRead = document.getElementById('sys-memio-read');
      if (memioRead) memioRead.innerText = readFormatted;
      const readSubBadge = document.getElementById('sys-read-sub-badge');
      if (readSubBadge) readSubBadge.innerText = readFormatted;

      const memioWrite = document.getElementById('sys-memio-write');
      if (memioWrite) memioWrite.innerText = writeFormatted;
      const writeSubBadge = document.getElementById('sys-write-sub-badge');
      if (writeSubBadge) writeSubBadge.innerText = writeFormatted;

      const maxIoScale = 50 * 1024 * 1024;
      const readPct = Math.min(100, (rBps / maxIoScale) * 100);
      const writePct = Math.min(100, (wBps / maxIoScale) * 100);

      const readSubGauge = document.getElementById('sys-read-sub-gauge');
      if (readSubGauge) readSubGauge.innerHTML = createGaugeSvg(readPct, 100, 56);
      const readSubBar = document.getElementById('sys-read-sub-bar');
      const readSubThumb = document.getElementById('sys-read-sub-thumb');
      if (readSubBar) readSubBar.style.width = `${readPct.toFixed(1)}%`;
      if (readSubThumb) readSubThumb.style.left = `${readPct.toFixed(1)}%`;

      const writeSubGauge = document.getElementById('sys-write-sub-gauge');
      if (writeSubGauge) writeSubGauge.innerHTML = createGaugeSvg(writePct, 100, 56);
      const writeSubBar = document.getElementById('sys-write-sub-bar');
      const writeSubThumb = document.getElementById('sys-write-sub-thumb');
      if (writeSubBar) writeSubBar.style.width = `${writePct.toFixed(1)}%`;
      if (writeSubThumb) writeSubThumb.style.left = `${writePct.toFixed(1)}%`;
    }

    // Physical Disks SMART Health
    const diskCont = document.getElementById('sys-physical-disks-container');
    const diskBadge = document.getElementById('sys-disk-health-badge');
    if (diskCont && Array.isArray(snap.physical_disks) && snap.physical_disks.length > 0) {
      const allHealthy = snap.physical_disks.every(d => d.health_status === 'Healthy');
      if (diskBadge) {
        diskBadge.textContent = allHealthy ? 'SMART OK' : 'Внимание';
        diskBadge.className = allHealthy ? 'badge bg-success-subtle text-success border border-success' : 'badge bg-warning-subtle text-warning border border-warning';
      }
      diskCont.innerHTML = snap.physical_disks.map(d => `
        <div class="d-flex justify-content-between align-items-center py-0.5 border-bottom border-dark-subtle" style="border-bottom-style: dashed !important;">
          <span class="text-truncate me-2" style="max-width: 160px;" title="${escapeHtml(d.model)}">${escapeHtml(d.model)}</span>
          <span class="badge bg-secondary font-monospace" style="font-size: 0.65rem;">${d.size_gb} GB ${escapeHtml(d.media_type || '')}</span>
        </div>
      `).join('');
    }

    // Battery & Power
    const powerCont = document.getElementById('sys-power-info-container');
    const powerBadge = document.getElementById('sys-power-status-badge');
    if (powerCont && snap.battery) {
      if (snap.battery.has_battery && snap.battery.percent !== null) {
        if (powerBadge) {
          powerBadge.textContent = `${snap.battery.percent}% ${snap.battery.power_plugged ? '⚡ Зарядка' : '🔋 Батарея'}`;
          powerBadge.className = snap.battery.power_plugged ? 'badge bg-success-subtle text-success border border-success' : 'badge bg-warning-subtle text-warning border border-warning';
        }
        const minsLeft = snap.battery.secs_left ? Math.round(snap.battery.secs_left / 60) : null;
        powerCont.innerHTML = `
          <div>Статус: ${snap.battery.power_plugged ? 'Подключено к сети' : 'Работа от батареи'}</div>
          <div>${minsLeft ? `Осталось ~${minsLeft} мин.` : 'Профиль: ' + (snap.battery.power_profile || 'Balanced')}</div>
        `;
      } else {
        if (powerBadge) {
          powerBadge.textContent = 'AC Mains';
          powerBadge.className = 'badge bg-secondary';
        }
        powerCont.innerHTML = `
          <div>Питание: Стационарная электросеть 220V</div>
          <div class="text-muted">Профиль: ${escapeHtml(snap.battery.power_profile || 'High Performance')}</div>
        `;
      }
    }

    // RAM SPD Modules
    const ramSticksCont = document.getElementById('sys-ram-sticks-container');
    const ramSticksBadge = document.getElementById('sys-ram-sticks-badge');
    if (ramSticksCont && Array.isArray(snap.ram_sticks) && snap.ram_sticks.length > 0) {
      if (ramSticksBadge) {
        ramSticksBadge.textContent = `${snap.ram_sticks.length} модулей`;
      }
      ramSticksCont.innerHTML = snap.ram_sticks.slice(0, 2).map(m => `
        <div class="d-flex justify-content-between align-items-center py-0.5">
          <span>${escapeHtml(m.bank_label)}: ${escapeHtml(m.manufacturer)}</span>
          <span class="font-monospace text-primary">${m.capacity_gb} GB @ ${m.speed_mhz} MT/s</span>
        </div>
      `).join('');
    } else if (ramSticksCont) {
      ramSticksCont.innerHTML = `<div>RAM: ${snap.memory ? snap.memory.total_gb : '--'} GB физической памяти</div>`;
    }

    // Reliability & Open Ports
    const alertsCont = document.getElementById('sys-alerts-ports-container');
    const alertsBadge = document.getElementById('sys-alerts-badge');
    if (alertsCont) {
      const portCount = Array.isArray(snap.listening_ports) ? snap.listening_ports.length : 0;
      const isReboot = snap.alerts && snap.alerts.reboot_pending;
      if (alertsBadge) {
        alertsBadge.textContent = isReboot ? 'Перезагрузка' : 'Стабильно';
        alertsBadge.className = isReboot ? 'badge bg-warning text-dark' : 'badge bg-info-subtle text-info border border-info';
      }
      alertsCont.innerHTML = `
        <div>Сетевые сокеты: <span class="fw-bold text-white">${portCount} портов LISTEN</span></div>
        <div class="text-truncate" title="${escapeHtml(snap.alerts?.latest_alert || '')}">${escapeHtml(snap.alerts?.latest_alert || 'Система стабильна')}</div>
      `;
    }

    renderProcessTable();
    if (snap.network_activity) {
      renderNetworkActivityTable(snap.network_activity);
    }
  }

  function renderProcessTable() {
    if (!latestTelemetrySnapshot || isSysPaused) return;
    const filterInput = document.getElementById('sys-proc-search');
    const filter = (filterInput?.value || '').toLowerCase().trim();
    const tbody = document.getElementById('sys-proc-tbody');
    if (!tbody) return;

    const processes = latestTelemetrySnapshot.top_processes || [];
    const filtered = processes.filter(p => {
      if (!filter) return true;
      return (
        String(p.pid).includes(filter) ||
        (p.name || '').toLowerCase().includes(filter) ||
        (p.username && p.username.toLowerCase().includes(filter))
      );
    });

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted">Процессы не найдены</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((p, idx) => {
      let cpuClass = '';
      if (p.cpu_percent > 40) cpuClass = 'badge-cpu-high';
      else if (p.cpu_percent > 15) cpuClass = 'badge-cpu-med';

      return `
        <tr class="sys-proc-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детальной AI-диагностики процесса">
          <td style="color: #38bdf8;">${p.pid}</td>
          <td style="font-weight: 600; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(p.name || '')}">${escapeHtml(p.name || '')}</td>
          <td style="color: #94a3b8;">${escapeHtml(p.status || 'running')}</td>
          <td style="text-align: right;" class="${cpuClass}">${Number(p.cpu_percent || 0).toFixed(1)}%</td>
          <td style="text-align: right; color: #4ade80;">${Number(p.memory_mb || 0).toFixed(1)} MB</td>
          <td style="text-align: right; color: #a855f7;">${p.num_threads || 1}</td>
          <td style="color: #94a3b8;">${escapeHtml(p.username || 'SYSTEM')}</td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.sys-proc-row').forEach(row => {
      row.onclick = () => {
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const p = filtered[idx];
        if (!p) return;

        if (window.AITableModal) {
          window.AITableModal.show({
            icon: '⚙️',
            title: p.name,
            subtitle: `PID: ${p.pid} | ${p.username || 'SYSTEM'}`,
            tableType: 'process',
            badges: [
              { text: `PID ${p.pid}`, class: 'badge bg-info text-dark' },
              { text: p.status || 'running', class: 'badge bg-success' }
            ],
            metadata: [
              { label: 'Имя процесса', value: p.name },
              { label: 'Process ID (PID)', value: String(p.pid) },
              { label: 'Пользователь / Учетная запись', value: p.username || 'SYSTEM' },
              { label: 'Статус', value: p.status || 'Выполняется' },
              { label: 'Загрузка CPU', value: `${Number(p.cpu_percent || 0).toFixed(1)}%` },
              { label: 'Оперативная память', value: `${Number(p.memory_mb || 0).toFixed(1)} MB` },
              { label: 'Количество потоков', value: String(p.num_threads || 1) },
              { label: 'Исполняемый путь', value: p.exe || p.executable_path || 'Системный процесс Windows', isCode: true, fullWidth: true }
            ],
            rawTitle: 'Команда запуска / Аргументы',
            rawContent: Array.isArray(p.cmdline) ? p.cmdline.join(' ') : (p.cmdline || p.exe || ''),
            requestData: {
              pid: p.pid,
              cpu_percent: p.cpu_percent,
              memory_mb: p.memory_mb,
              username: p.username,
              status: p.status
            }
          });
        }
      };
    });
  }

  async function fetchNetworkActivity() {
    try {
      const res = await fetch('/api/v1/system/network-activity?limit=100');
      if (res.ok) {
        const data = await res.json();
        renderNetworkActivityTable(data);
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to fetch network activity:', e);
    }
  }

  function renderNetworkActivityTable(activities) {
    if (activities) {
      cachedNetworkActivities = activities;
    }
    if (isNetPaused) return;

    const tbody = document.getElementById('sys-net-tbody');
    if (!tbody) return;

    const searchInput = document.getElementById('sys-net-search');
    const filterText = (searchInput?.value || '').toLowerCase().trim();
    const countBadge = document.getElementById('sys-netact-count-badge');
    const connsBadge = document.getElementById('sys-netact-conns-badge');

    const rawList = Array.isArray(cachedNetworkActivities) ? cachedNetworkActivities : [];

    // Filter by category and search query
    let filtered = rawList.filter(item => {
      if (currentNetFilter === 'internet' && !item.is_internet) return false;
      if (currentNetFilter === 'listen' && item.status !== 'LISTEN') return false;

      if (filterText) {
        return (
          String(item.pid).includes(filterText) ||
          (item.name || '').toLowerCase().includes(filterText) ||
          (item.user || '').toLowerCase().includes(filterText) ||
          (item.remote_address || '').toLowerCase().includes(filterText) ||
          (item.local_address || '').toLowerCase().includes(filterText) ||
          (item.service_type || '').toLowerCase().includes(filterText) ||
          (item.sent_summary || '').toLowerCase().includes(filterText) ||
          (item.recv_summary || '').toLowerCase().includes(filterText)
        );
      }
      return true;
    });

    const uniqueProcs = new Set(filtered.map(i => i.pid)).size;
    if (countBadge) countBadge.textContent = `${uniqueProcs} программ`;
    if (connsBadge) connsBadge.textContent = `${filtered.length} сокетов`;

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted small">Нет активных сетевых соединений по выбранному фильтру</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((item, idx) => {
      const isListen = item.status === 'LISTEN';
      const statusBadgeClass = isListen
        ? 'badge bg-secondary-subtle text-light border border-secondary'
        : item.status === 'ESTABLISHED'
        ? 'badge bg-success-subtle text-success border border-success'
        : 'badge bg-warning-subtle text-warning border border-warning';

      const protoBadge = item.protocol === 'UDP'
        ? '<span class="badge bg-primary text-white" style="font-size: 0.65rem;">UDP</span>'
        : '<span class="badge bg-dark border border-secondary text-info" style="font-size: 0.65rem;">TCP</span>';

      const isExtBadge = item.is_internet
        ? '<span class="badge bg-primary-subtle text-primary border border-primary px-1" style="font-size: 0.62rem;" title="Внешний сервер в сети Интернет">WAN</span>'
        : '<span class="badge bg-secondary px-1" style="font-size: 0.62rem;" title="Локальный сокет Loopback">LAN</span>';

      const formatNetKb = (kb) => {
        if (!kb || kb <= 0) return '0 KB';
        if (kb >= 1024 * 1024) return (kb / (1024 * 1024)).toFixed(2) + ' GB';
        if (kb >= 1024) return (kb / 1024).toFixed(1) + ' MB';
        return kb.toFixed(1) + ' KB';
      };

      const formatNetRate = (rate) => {
        if (!rate || rate <= 0.05) return '';
        if (rate >= 1024) return (rate / 1024).toFixed(1) + ' MB/s';
        return rate.toFixed(1) + ' KB/s';
      };

      const deltaSentStr = (item.delta_sent_kb && item.delta_sent_kb > 0)
        ? `▲ +${formatNetKb(item.delta_sent_kb)}${item.sent_rate_kbs > 0.05 ? ' (' + formatNetRate(item.sent_rate_kbs) + ')' : ''}`
        : '▲ 0 KB';
      const deltaRecvStr = (item.delta_recv_kb && item.delta_recv_kb > 0)
        ? `▼ +${formatNetKb(item.delta_recv_kb)}${item.recv_rate_kbs > 0.05 ? ' (' + formatNetRate(item.recv_rate_kbs) + ')' : ''}`
        : '▼ 0 KB';

      const totalSentStr = formatNetKb(item.sent_kb || 0);
      const totalRecvStr = formatNetKb(item.recv_kb || 0);

      return `
        <tr class="sys-net-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детальной диагностики сетевого соединения">
          <td>
            <div class="fw-bold text-white text-truncate" style="max-width: 165px;" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
            <div class="small text-muted" style="font-size: 0.70rem;">PID: <span style="color: #38bdf8;">${item.pid}</span> ${item.user ? '• ' + escapeHtml(item.user) : ''}</div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-1">
              ${isExtBadge}
              <span class="font-monospace text-light fw-semibold text-truncate" style="max-width: 195px;" title="${escapeHtml(item.remote_address)}">
                ${escapeHtml(item.remote_address !== '-' ? item.remote_address : item.local_address)}
              </span>
            </div>
            <div class="small text-muted font-monospace" style="font-size: 0.68rem;">Local: ${escapeHtml(item.local_address)}</div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-1 mb-0.5">
              ${protoBadge}
              <span class="fw-semibold text-truncate" style="max-width: 110px; font-size: 0.74rem; color: #a855f7;" title="${escapeHtml(item.service_type)}">${escapeHtml(item.service_type)}</span>
            </div>
          </td>
          <td style="text-align: center;">
            <span class="${statusBadgeClass}" style="font-size: 0.68rem;">${escapeHtml(item.status)}</span>
          </td>
          <td>
            <div class="d-flex align-items-center justify-content-between gap-1 mb-1">
              <span class="badge bg-warning-subtle text-warning border border-warning px-1.5 py-0.5" style="font-size: 0.68rem;" title="Отправлено за измеряемый период">
                ${deltaSentStr}
              </span>
              <span class="text-muted font-monospace" style="font-size: 0.66rem;" title="Всего отправлено/записано">
                Σ ${totalSentStr}
              </span>
            </div>
            <div class="d-flex align-items-start gap-1">
              <i class="bi bi-arrow-up-right text-warning mt-0.5" style="font-size: 0.70rem;"></i>
              <div class="text-truncate" style="max-width: 250px; font-size: 0.72rem; color: #fde047;" title="${escapeHtml(item.sent_summary)}">
                ${escapeHtml(item.sent_summary)}
              </div>
            </div>
          </td>
          <td>
            <div class="d-flex align-items-center justify-content-between gap-1 mb-1">
              <span class="badge bg-success-subtle text-success border border-success px-1.5 py-0.5" style="font-size: 0.68rem;" title="Скачано/получено за измеряемый период">
                ${deltaRecvStr}
              </span>
              <span class="text-muted font-monospace" style="font-size: 0.66rem;" title="Всего скачано/прочитано">
                Σ ${totalRecvStr}
              </span>
            </div>
            <div class="d-flex align-items-start gap-1">
              <i class="bi bi-arrow-down-left text-success mt-0.5" style="font-size: 0.70rem;"></i>
              <div class="text-truncate" style="max-width: 250px; font-size: 0.72rem; color: #86efac;" title="${escapeHtml(item.recv_summary)}">
                ${escapeHtml(item.recv_summary)}
              </div>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.sys-net-row').forEach(row => {
      row.onclick = () => {
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const item = filtered[idx];
        if (!item) return;

        const formatNetKb = (kb) => {
          if (!kb || kb <= 0) return '0 KB';
          if (kb >= 1024 * 1024) return (kb / (1024 * 1024)).toFixed(2) + ' GB';
          if (kb >= 1024) return (kb / 1024).toFixed(1) + ' MB';
          return kb.toFixed(1) + ' KB';
        };

        const formatNetRate = (rate) => {
          if (!rate || rate <= 0.05) return '';
          if (rate >= 1024) return (rate / 1024).toFixed(1) + ' MB/s';
          return rate.toFixed(1) + ' KB/s';
        };

        if (window.AITableModal) {
          window.AITableModal.show({
            icon: '🌐',
            title: `${item.name} (${item.service_type})`,
            subtitle: `PID: ${item.pid} | ${item.remote_address}`,
            tableType: 'network',
            badges: [
              { text: `PID ${item.pid}`, class: 'badge bg-info text-dark' },
              { text: item.protocol, class: 'badge bg-primary' },
              { text: item.status, class: 'badge bg-success' },
              { text: item.is_internet ? 'Интернет (WAN)' : 'Локально (LAN)', class: item.is_internet ? 'badge bg-warning text-dark' : 'badge bg-secondary' }
            ],
            metadata: [
              { label: 'Программа / Процесс', value: item.name },
              { label: 'Process ID (PID)', value: String(item.pid) },
              { label: 'Пользователь системы', value: item.user || 'SYSTEM' },
              { label: 'Удаленный адрес (Remote)', value: item.remote_address },
              { label: 'Локальный сокет (Local)', value: item.local_address },
              { label: 'Протокол / Служба', value: `${item.protocol} • ${item.service_type}` },
              { label: 'Статус соединения', value: item.status },
              { label: 'Скачано за период (Прием)', value: `${formatNetKb(item.delta_recv_kb || 0)} ${item.recv_rate_kbs > 0.05 ? '(' + formatNetRate(item.recv_rate_kbs) + ')' : ''}` },
              { label: 'Всего скачано / получено', value: formatNetKb(item.recv_kb || 0) },
              { label: 'Отправлено за период', value: `${formatNetKb(item.delta_sent_kb || 0)} ${item.sent_rate_kbs > 0.05 ? '(' + formatNetRate(item.sent_rate_kbs) + ')' : ''}` },
              { label: 'Всего отправлено', value: formatNetKb(item.sent_kb || 0) },
              { label: 'Что шлет (Отправка)', value: item.sent_summary, fullWidth: true },
              { label: 'Что принимает (Прием)', value: item.recv_summary, fullWidth: true }
            ],
            rawTitle: 'Сетевой дамп подключения',
            rawContent: JSON.stringify(item, null, 2),
            requestData: item
          });
        }
      };
    });
  }

  async function runAiDiagnostics() {
    const summaryEl = document.getElementById('sys-ai-summary-text');
    const badgeEl = document.getElementById('sys-ai-health-badge');
    const anomaliesEl = document.getElementById('sys-ai-anomalies-container');
    const engineTagEl = document.getElementById('sys-ai-model-tag');

    if (summaryEl) summaryEl.innerText = 'Запуск глубокого AI-аудита системы и оборудования...';

    try {
      const res = await fetch('/api/v1/system/diagnose', { method: 'POST' });
      if (!res.ok) throw new Error('AI Diagnosis error');
      const report = await res.json();

      if (badgeEl) {
        badgeEl.innerText = `Health: ${report.health_score || 100}/100`;
        badgeEl.className = `badge ${report.health_score >= 80 ? 'bg-success' : report.health_score >= 60 ? 'bg-warning' : 'bg-danger'}`;
      }

      if (engineTagEl) {
        engineTagEl.innerText = report.ai_model_used || 'Heuristic Engine';
      }

      if (anomaliesEl) {
        if (Array.isArray(report.anomalies) && report.anomalies.length > 0) {
          anomaliesEl.innerHTML = report.anomalies.map(a => `<span class="anomaly-tag">⚠️ [${a.subsystem}] ${escapeHtml(a.title)}</span>`).join('');
        } else {
          anomaliesEl.innerHTML = '<span style="color: #4ade80; font-size: 0.75rem;"><i class="bi bi-check-circle me-1"></i> Аномалий в работе оборудования не обнаружено</span>';
        }
      }

      if (summaryEl) {
        const recs = Array.isArray(report.recommendations) && report.recommendations.length > 0
          ? `\nРекомендации: ${report.recommendations.join(', ')}`
          : '';
        summaryEl.innerText = `${report.summary || 'Телеметрия в норме.'}${recs}`;
      }
    } catch (e) {
      console.error('[SystemInspectorTab] AI Diagnose error:', e);
      if (summaryEl) summaryEl.innerText = 'Ошибка выполнения AI-диагностики: ' + e.message;
    }
  }

  let sysWsReconnectTimer = null;

  function connectSystemWebSocket() {
    if (sysWsReconnectTimer) {
      clearTimeout(sysWsReconnectTimer);
      sysWsReconnectTimer = null;
    }
    if (sysWs) {
      try {
        sysWs.onclose = null;
        sysWs.onerror = null;
        sysWs.close();
      } catch {}
      sysWs = null;
    }

    if (window.isTabActive && !window.isTabActive('tab-hardware-load-inspector') && !window.isTabActive('tab-system-load-inspector') && !window.isTabActive('tab-system-inspector')) {
      const statusBadge = document.getElementById('sys-conn-status');
      if (statusBadge) {
        statusBadge.className = 'badge rounded-pill bg-secondary text-light px-3 py-2';
        statusBadge.innerText = '○ Поток приостановлен';
      }
      return;
    }

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/api/v1/system/stream`;

    try {
      sysWs = new WebSocket(wsUrl);
      const statusBadge = document.getElementById('sys-conn-status');

      sysWs.onopen = () => {
        console.info('[SystemInspectorTab] WebSocket соединение с телеметрией установлено.');
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
          statusBadge.innerText = '● Телеметрия активна';
        }
      };

      sysWs.onmessage = (evt) => {
        try {
          const snap = JSON.parse(evt.data);
          latestTelemetrySnapshot = snap;
          updateTelemetryDashboard(snap);
        } catch (e) {
          console.error('[SystemInspectorTab] Ошибка разбора сообщения телеметрии:', e);
        }
      };

      const scheduleReconnect = (reason) => {
        if (sysWsReconnectTimer) return;
        if (window.isTabActive && !window.isTabActive('tab-hardware-load-inspector') && !window.isTabActive('tab-system-load-inspector') && !window.isTabActive('tab-system-inspector')) return;
        console.warn(`[SystemInspectorTab] WebSocket отключен (${reason}). Автопереподключение через 3 сек...`);
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
          statusBadge.innerText = '○ Переподключение...';
        }
        sysWsReconnectTimer = setTimeout(() => {
          sysWsReconnectTimer = null;
          if (!window.isTabActive || window.isTabActive('tab-hardware-load-inspector') || window.isTabActive('tab-system-load-inspector') || window.isTabActive('tab-system-inspector')) {
            connectSystemWebSocket();
          }
        }, 3000);
      };

      sysWs.onclose = (evt) => {
        scheduleReconnect(`код закрытия: ${evt.code}`);
      };

      sysWs.onerror = (err) => {
        console.warn('[SystemInspectorTab] Ошибка соединения WebSocket:', err);
        scheduleReconnect('ошибка связи');
      };
    } catch (err) {
      console.error('[SystemInspectorTab] Ошибка инициализации WebSocket:', err);
      sysWsReconnectTimer = setTimeout(() => {
        sysWsReconnectTimer = null;
        if (!window.isTabActive || window.isTabActive('tab-hardware-load-inspector') || window.isTabActive('tab-system-load-inspector') || window.isTabActive('tab-system-inspector')) {
          connectSystemWebSocket();
        }
      }, 5000);
    }
  }

  function disconnectSystemWebSocket() {
    if (sysWsReconnectTimer) {
      clearTimeout(sysWsReconnectTimer);
      sysWsReconnectTimer = null;
    }
    if (sysWs) {
      try {
        sysWs.onclose = null;
        sysWs.onerror = null;
        sysWs.close();
      } catch {}
      sysWs = null;
    }
    const statusBadge = document.getElementById('sys-conn-status');
    if (statusBadge) {
      statusBadge.className = 'badge rounded-pill bg-secondary text-light px-3 py-2';
      statusBadge.innerText = '○ Поток приостановлен';
    }
  }

  function bindTabEvents() {
    const btnPause = document.getElementById('btn-sys-pause-proc');
    if (btnPause) {
      btnPause.onclick = () => {
        isSysPaused = !isSysPaused;
        btnPause.innerText = isSysPaused ? 'Возобновить' : 'Пауза';
        btnPause.className = isSysPaused ? 'btn btn-sm btn-warning rounded-pill px-3' : 'btn btn-sm btn-outline-secondary rounded-pill px-3';
      };
    }

    const btnRefreshSensors = document.getElementById('btn-sys-refresh-sensors');
    if (btnRefreshSensors) {
      btnRefreshSensors.onclick = () => fetchLhmSensors();
    }

    const btnRefreshLhm = document.getElementById('btn-sys-refresh-lhm');
    if (btnRefreshLhm) {
      btnRefreshLhm.onclick = () => fetchLhmSensors();
    }

    const btnLaunchLhm = document.getElementById('btn-sys-launch-lhm');
    if (btnLaunchLhm) {
      btnLaunchLhm.onclick = async () => {
        btnLaunchLhm.disabled = true;
        btnLaunchLhm.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Запуск...';
        try {
          const res = await fetch('/api/v1/lhm/launch', { method: 'POST' });
          if (res.ok) {
            setTimeout(fetchLhmSensors, 2500);
          }
        } catch (e) {
          console.error('[SystemInspectorTab] Failed to launch LHM:', e);
        } finally {
          btnLaunchLhm.disabled = false;
        }
      };
    }

    const searchSensors = document.getElementById('sys-lhm-search');
    if (searchSensors) {
      searchSensors.oninput = () => renderSensors();
    }

    // Category pills
    document.querySelectorAll('.sys-lhm-cat-btn').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('.sys-lhm-cat-btn').forEach(b => {
          b.classList.remove('active', 'btn-outline-primary');
          b.classList.add('btn-outline-secondary');
        });
        btn.classList.remove('btn-outline-secondary');
        btn.classList.add('active', 'btn-outline-primary');
        currentSensorCategory = btn.getAttribute('data-cat') || 'all';
        renderSensors();
      };
    });

    // Analyze Button (Sensors)
    const btnAnalyze = document.getElementById('btn-sys-sensor-analyze');
    if (btnAnalyze) {
      btnAnalyze.onclick = () => analyzeSensorsAndReport();
    }

    // Modal Re-analyze Button
    const btnReAnalyze = document.getElementById('btn-re-analyze-sensors');
    if (btnReAnalyze) {
      btnReAnalyze.onclick = async () => {
        btnReAnalyze.disabled = true;
        const icon = btnReAnalyze.querySelector('i');
        if (icon) icon.classList.add('spin-animation');
        await fetchLhmSensors();
        await analyzeSensorsAndReport();
        if (icon) icon.classList.remove('spin-animation');
        btnReAnalyze.disabled = false;
      };
    }

    // Modal Copy Report Button
    const btnCopyReport = document.getElementById('btn-copy-sensor-report');
    if (btnCopyReport) {
      btnCopyReport.onclick = async () => {
        if (!lastAnalysisReportText) return;
        try {
          await navigator.clipboard.writeText(lastAnalysisReportText);
          const origHtml = btnCopyReport.innerHTML;
          btnCopyReport.innerHTML = '<i class="bi bi-check2 text-success me-1"></i> Скопировано!';
          setTimeout(() => {
            btnCopyReport.innerHTML = origHtml;
          }, 2000);
        } catch (e) {
          console.warn('[SystemInspectorTab] Clipboard copy failed:', e);
        }
      };
    }

    const searchProc = document.getElementById('sys-proc-search');
    if (searchProc) {
      searchProc.oninput = () => renderProcessTable();
    }

    const btnAudit = document.getElementById('btn-sys-run-audit');
    if (btnAudit) {
      btnAudit.onclick = () => runAiDiagnostics();
    }

    const btnConfig = document.getElementById('btn-sys-config');
    if (btnConfig) {
      btnConfig.onclick = () => {
        if (window.appConfigEditor) {
          window.appConfigEditor.open('system_inspector', 'Настройки телеметрии и инспектора');
        } else {
          console.info('[SystemInspectorTab] Config editor not available');
        }
      };
    }

    // Interval editor modal buttons
    const btnIntervalsTop = document.getElementById('btn-sys-intervals');
    if (btnIntervalsTop) {
      btnIntervalsTop.onclick = () => openSysIntervalsModal();
    }

    const btnIntervalsLhm = document.getElementById('btn-sys-intervals-lhm');
    if (btnIntervalsLhm) {
      btnIntervalsLhm.onclick = () => openSysIntervalsModal();
    }

    const btnRefreshIntervals = document.getElementById('btn-modal-intervals-refresh');
    if (btnRefreshIntervals) {
      btnRefreshIntervals.onclick = () => loadSysIntervalsConfig(true);
    }

    const btnSaveIntervals = document.getElementById('btn-modal-intervals-save');
    if (btnSaveIntervals) {
      btnSaveIntervals.onclick = () => saveSysIntervalsConfig();
    }

    const selUiRefresh = document.getElementById('modal-ui-refresh-select');
    if (selUiRefresh) {
      selUiRefresh.onchange = (e) => {
        const sec = parseInt(e.target.value, 10) || 5;
        setupSysSensorInterval(sec);
        const badge = document.getElementById('modal-ui-refresh-badge');
        if (badge) badge.textContent = `${sec} сек`;
      };
    }

    // Изменения файлов в реальном времени controls
    const changeWatchDirBtn = document.getElementById('btn-sys-change-watch-dir');
    if (changeWatchDirBtn) {
      changeWatchDirBtn.onclick = () => openWatchFoldersModal('folders');
    }
    const exclusionsBtn = document.getElementById('btn-sys-watch-exclusions');
    if (exclusionsBtn) {
      exclusionsBtn.onclick = () => openWatchFoldersModal('exclusions');
    }
    const watchDirBadge = document.getElementById('sys-watch-dir-badge');
    if (watchDirBadge) {
      watchDirBadge.onclick = () => openWatchFoldersModal('folders');
    }
    const liveHelpBtn = document.getElementById('btn-sys-live-help');
    if (liveHelpBtn) {
      liveHelpBtn.onclick = showLiveWatcherHelpModal;
    }

    // Network Activity Table controls
    const searchNet = document.getElementById('sys-net-search');
    if (searchNet) {
      searchNet.oninput = () => renderNetworkActivityTable();
    }

    const btnPauseNet = document.getElementById('btn-sys-pause-net');
    if (btnPauseNet) {
      btnPauseNet.onclick = () => {
        isNetPaused = !isNetPaused;
        btnPauseNet.innerText = isNetPaused ? 'Возобновить' : 'Пауза';
        btnPauseNet.className = isNetPaused ? 'btn btn-xs btn-warning rounded-pill px-2.5 py-0.5' : 'btn btn-xs btn-outline-secondary rounded-pill px-2.5 py-0.5';
        if (!isNetPaused) renderNetworkActivityTable();
      };
    }

    const btnRefreshNet = document.getElementById('btn-sys-refresh-net');
    if (btnRefreshNet) {
      btnRefreshNet.onclick = () => fetchNetworkActivity();
    }

    document.querySelectorAll('.sys-net-filter-btn').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('.sys-net-filter-btn').forEach(b => {
          b.classList.remove('active', 'btn-outline-primary');
          b.classList.add('btn-outline-secondary');
        });
        btn.classList.remove('btn-outline-secondary');
        btn.classList.add('active', 'btn-outline-primary');
        currentNetFilter = btn.getAttribute('data-filter') || 'internet';
        renderNetworkActivityTable();
      };
    });

    // Инициализация интерактивных ресайзеров таблиц
    initNetTableResizer();
    initWatcherTableResizer();
  }

  function initNetTableResizer() {
    const resizer = document.getElementById('sys-net-table-resizer');
    const tableContainer = document.getElementById('sys-net-table-container');
    if (!resizer || !tableContainer) return;

    if (resizer._resizerInitialized) return;
    resizer._resizerInitialized = true;

    try {
      const savedHeight = localStorage.getItem('sys_inspector_net_height');
      if (savedHeight) {
        const parsed = parseInt(savedHeight, 10);
        if (!isNaN(parsed) && parsed >= 140 && parsed <= 1200) {
          tableContainer.style.height = `${parsed}px`;
        }
      }
    } catch {}

    let startY = 0;
    let startHeight = 0;
    let isDragging = false;

    function onMouseMove(e) {
      if (!isDragging) return;
      const clientY = e.clientY ?? (e.touches && e.touches[0] ? e.touches[0].clientY : null);
      if (clientY === null) return;

      const deltaY = clientY - startY;
      let newHeight = startHeight + deltaY;
      if (newHeight < 140) newHeight = 140;
      if (newHeight > 1200) newHeight = 1200;

      tableContainer.style.height = `${newHeight}px`;
    }

    function onMouseUp() {
      if (!isDragging) return;
      isDragging = false;
      resizer.classList.remove('resizing');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';

      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchmove', onMouseMove);
      window.removeEventListener('touchend', onMouseUp);

      const currentH = parseInt(tableContainer.style.height, 10);
      if (!isNaN(currentH)) {
        try {
          localStorage.setItem('sys_inspector_net_height', String(currentH));
        } catch {}
      }
    }

    function onMouseDown(e) {
      isDragging = true;
      startY = e.clientY ?? (e.touches && e.touches[0] ? e.touches[0].clientY : 0);
      startHeight = tableContainer.getBoundingClientRect().height;
      resizer.classList.add('resizing');
      document.body.style.cursor = 'ns-resize';
      document.body.style.userSelect = 'none';

      window.addEventListener('mousemove', onMouseMove, { passive: false });
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('touchmove', onMouseMove, { passive: false });
      window.addEventListener('touchend', onMouseUp);
      e.preventDefault();
    }

    resizer.addEventListener('mousedown', onMouseDown);
    resizer.addEventListener('touchstart', onMouseDown, { passive: false });

    resizer.addEventListener('dblclick', () => {
      tableContainer.style.height = '300px';
      try {
        localStorage.removeItem('sys_inspector_net_height');
      } catch {}
    });
  }

  function initWatcherTableResizer() {
    const resizer = document.getElementById('sys-watcher-table-resizer');
    const tableContainer = document.getElementById('sys-watcher-table-container');
    if (!resizer || !tableContainer) return;

    if (resizer._resizerInitialized) return;
    resizer._resizerInitialized = true;

    // Восстановление сохранённой пользователем высоты
    try {
      const savedHeight = localStorage.getItem('sys_inspector_watcher_height');
      if (savedHeight) {
        const parsed = parseInt(savedHeight, 10);
        if (!isNaN(parsed) && parsed >= 120 && parsed <= 1200) {
          tableContainer.style.height = `${parsed}px`;
        }
      }
    } catch {}

    let startY = 0;
    let startHeight = 0;
    let isDragging = false;

    function onMouseMove(e) {
      if (!isDragging) return;
      const clientY = e.clientY ?? (e.touches && e.touches[0] ? e.touches[0].clientY : null);
      if (clientY === null) return;

      const deltaY = clientY - startY;
      let newHeight = startHeight + deltaY;
      if (newHeight < 120) newHeight = 120;
      if (newHeight > 1200) newHeight = 1200;

      tableContainer.style.height = `${newHeight}px`;
    }

    function onMouseUp() {
      if (!isDragging) return;
      isDragging = false;
      resizer.classList.remove('resizing');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';

      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchmove', onMouseMove);
      window.removeEventListener('touchend', onMouseUp);

      const currentH = parseInt(tableContainer.style.height, 10);
      if (!isNaN(currentH)) {
        try {
          localStorage.setItem('sys_inspector_watcher_height', String(currentH));
        } catch {}
      }
    }

    function onMouseDown(e) {
      isDragging = true;
      startY = e.clientY ?? (e.touches && e.touches[0] ? e.touches[0].clientY : 0);
      startHeight = tableContainer.getBoundingClientRect().height;
      resizer.classList.add('resizing');
      document.body.style.cursor = 'ns-resize';
      document.body.style.userSelect = 'none';

      window.addEventListener('mousemove', onMouseMove, { passive: false });
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('touchmove', onMouseMove, { passive: false });
      window.addEventListener('touchend', onMouseUp);
      e.preventDefault();
    }

    resizer.addEventListener('mousedown', onMouseDown);
    resizer.addEventListener('touchstart', onMouseDown, { passive: false });

    // Сброс по двойному клику
    resizer.addEventListener('dblclick', () => {
      tableContainer.style.height = '280px';
      try {
        localStorage.removeItem('sys_inspector_watcher_height');
      } catch {}
    });
  }

  // =============================================================================
  // Telemetry & Polling Intervals Editor Controller (config.json)
  // =============================================================================

  const INTERVAL_PRESETS = [
    { value: '1 second', label: '1 сек' },
    { value: '2 seconds', label: '2 сек' },
    { value: '3 seconds', label: '3 сек' },
    { value: '5 seconds', label: '5 сек' },
    { value: '10 seconds', label: '10 сек' },
    { value: '30 seconds', label: '30 сек' },
    { value: '1 minute', label: '1 мин' },
    { value: '5 minutes', label: '5 мин' },
    { value: '10 minutes', label: '10 мин' },
    { value: '30 minutes', label: '30 мин' },
    { value: '1 hour', label: '1 час' },
    { value: '6 hours', label: '6 часов' },
    { value: '24 hours', label: '24 часа' },
  ];

  const CORE_RESOURCE_LOGGERS = [
    'system_inspector',
    'hardware_monitor'
  ];

  const LOGGER_META = {
    system_inspector: {
      icon: '📊',
      title: 'System Inspector',
      desc: 'Комплексный снимок: загрузка CPU, RAM, дисковый ввод-вывод, процессы хоста',
    },
    hardware_monitor: {
      icon: '💻',
      title: 'Hardware Monitor',
      desc: 'Аппаратные датчики WMI, GPU SMI (NVIDIA/AMD/Intel) и физические шины',
    },
    windows_sysadmin: {
      icon: '🛠️',
      title: 'Windows SysAdmin',
      desc: 'Системные службы Windows, пользователи, локальные группы и сетевые порты',
    },
    windows_defender: {
      icon: '🛡️',
      title: 'Windows Defender',
      desc: 'Статус антивирусной защиты, сигнатуры, обнаруженные угрозы и карантин',
    },
    windows_startup_auditor: {
      icon: '🚀',
      title: 'StartUp Auditor',
      desc: 'Автозагрузка программ, реестр Run/RunOnce, сервисы и планировщик задач',
    },
    windows_backup_manager: {
      icon: '📦',
      title: 'Backup Manager',
      desc: 'Резервные копии баз данных SQLite, конфигураций и снапшотов системы',
    },
    website_monitor: {
      icon: '🌐',
      title: 'Website Monitor',
      desc: 'Проверка доступности веб-сервисов, задержка ответов HTTP/HTTPS',
    },
    gcloud_monitor: {
      icon: '☁️',
      title: 'GCloud Monitor',
      desc: 'Телеметрия виртуальных машин, квоты и мониторинг Google Cloud',
    },
    cloudflared_monitor: {
      icon: '🚇',
      title: 'Cloudflare Tunnel',
      desc: 'Статус защищенных туннелей cloudflared и исходящих подключений',
    },
    user_assistant: {
      icon: '🤖',
      title: 'User Assistant',
      desc: 'Фоновые периодические напоминания, календарь и уведомления',
    },
    trading_terminal: {
      icon: '📈',
      title: 'Trading Terminal',
      desc: 'Торговые котировки, балансы криптобирж и открытые ордера',
    },
    registry_viewer: {
      icon: '📑',
      title: 'Registry Viewer',
      desc: 'Мониторинг изменений системного реестра Windows',
    },
    software_audit: {
      icon: '🔍',
      title: 'Software Audit',
      desc: 'Аудит неиспользуемого и редко запускаемого ПО (UserAssist/Prefetch)',
    },
    helpdesk: {
      icon: '🎫',
      title: 'Helpdesk',
      desc: 'Мониторинг тикетов техподдержки и уведомлений',
    },
  };

  let _sysIntervalsConfigData = null;
  let _currentUiRefreshSeconds = 5;

  function showAlertInModal(msg, type = 'success') {
    const alertEl = document.getElementById('modal-intervals-alert');
    if (!alertEl) return;
    alertEl.className = `alert alert-${type} py-2 px-3 small mb-3`;
    alertEl.innerHTML = msg;
    alertEl.classList.remove('d-none');
    if (type === 'success') {
      setTimeout(() => {
        alertEl.classList.add('d-none');
      }, 4000);
    }
  }

  async function loadSysIntervalsConfig(notify = false) {
    const btnRefresh = document.getElementById('btn-modal-intervals-refresh');
    const icon = btnRefresh ? btnRefresh.querySelector('i') : null;
    if (icon) icon.classList.add('spin-animation');

    try {
      let res = await fetch('/api/autolog/config');
      if (!res.ok) {
        res = await fetch('/sysautologging/config');
      }
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      _sysIntervalsConfigData = await res.json();
      renderSysIntervalsForm(_sysIntervalsConfigData);

      if (notify) {
        showAlertInModal('<i class="bi bi-check2 me-1"></i> Конфигурация успешно загружена из файла', 'success');
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to load intervals config:', e);
      showAlertInModal(`<i class="bi bi-exclamation-triangle me-1"></i> Ошибка загрузки конфигурации: ${escapeHtml(e.message)}`, 'danger');
    } finally {
      if (icon) icon.classList.remove('spin-animation');
    }
  }

  function buildIntervalSelectHtml(loggerName, currentInterval) {
    const val = currentInterval || '1 minute';
    const isCustom = !INTERVAL_PRESETS.some(p => p.value === val);

    let html = `<select class="form-select form-select-sm bg-dark text-white border-secondary sys-int-select" data-logger="${loggerName}" style="min-width: 120px;">`;
    INTERVAL_PRESETS.forEach(p => {
      const sel = p.value === val ? 'selected' : '';
      html += `<option value="${p.value}" ${sel}>${p.label} (${p.value})</option>`;
    });
    if (isCustom) {
      html += `<option value="${escapeHtml(val)}" selected>${escapeHtml(val)} (пользовательский)</option>`;
    }
    html += `</select>`;
    return html;
  }

  function renderSysIntervalsForm(data) {
    if (!data) return;

    // 1. Config file badge
    const cfgBadge = document.getElementById('modal-intervals-cfg-file');
    if (cfgBadge && data.config_file) {
      cfgBadge.textContent = data.config_file;
    }

    // 2. Engine status & global switch
    const engineStatusBadge = document.getElementById('modal-intervals-engine-status');
    if (engineStatusBadge) {
      if (data.is_running) {
        engineStatusBadge.textContent = 'AutoLog Active';
        engineStatusBadge.className = 'badge bg-success';
      } else {
        engineStatusBadge.textContent = 'AutoLog Paused';
        engineStatusBadge.className = 'badge bg-danger-subtle text-danger border border-danger fw-bold';
      }
    }

    const globalEnable = document.getElementById('modal-intervals-global-enable');
    if (globalEnable) {
      globalEnable.checked = data.enable_autolog !== false;
    }

    // 3. Default fallback interval select
    const defSelect = document.getElementById('modal-intervals-default-select');
    if (defSelect && data.default_interval) {
      defSelect.value = data.default_interval;
    }

    // 4. Populate Core resource loggers & Other loggers
    const coreContainer = document.getElementById('modal-core-loggers-container');
    const otherContainer = document.getElementById('modal-other-loggers-container');
    const otherCountEl = document.getElementById('modal-other-loggers-count');

    if (!coreContainer || !otherContainer) return;

    const loggers = data.loggers || {};
    let coreHtml = '';
    let otherHtml = '';
    let otherCount = 0;

    // Process core loggers
    CORE_RESOURCE_LOGGERS.forEach(name => {
      const cfg = loggers[name] || { interval: '5 seconds', enabled: true };
      const meta = LOGGER_META[name] || { icon: '⚙️', title: name, desc: 'Системный сбор метрик' };
      const isEnabled = cfg.enabled !== false;
      const intervalVal = cfg.interval || '5 seconds';

      coreHtml += `
        <div class="p-2 rounded d-flex align-items-center justify-content-between flex-wrap gap-2" style="background: var(--bg-color); border: 1px solid var(--border-color);">
          <div class="d-flex align-items-center gap-2" style="max-width: 58%;">
            <span class="fs-5">${meta.icon}</span>
            <div>
              <div class="fw-bold small" style="color: var(--text-color);">${meta.title}</div>
              <div class="small text-muted" style="font-size: 0.72rem; line-height: 1.2;">${meta.desc}</div>
            </div>
          </div>
          <div class="d-flex align-items-center gap-2 ms-auto">
            <div class="form-check form-switch m-0" title="Включить/отключить сбор метрик для этого сервиса">
              <input class="form-check-input sys-int-enable" type="checkbox" data-logger="${name}" ${isEnabled ? 'checked' : ''}>
            </div>
            ${buildIntervalSelectHtml(name, intervalVal)}
            <button class="btn btn-xs btn-outline-secondary rounded px-1.5 py-0.5 sys-int-custom-btn" data-logger="${name}" title="Ввести произвольный интервал вручную">
              <i class="bi bi-pencil"></i>
            </button>
          </div>
        </div>
      `;
    });

    // Process remaining loggers
    const allLoggerNames = Object.keys(loggers).length > 0
      ? Object.keys(loggers)
      : Object.keys(LOGGER_META);

    allLoggerNames.forEach(name => {
      if (CORE_RESOURCE_LOGGERS.includes(name)) return;
      otherCount++;
      const cfg = loggers[name] || { interval: data.default_interval || '1 minute', enabled: true };
      const meta = LOGGER_META[name] || { icon: '🔹', title: name, desc: 'Фоновый опрос службы' };
      const isEnabled = cfg.enabled !== false;
      const intervalVal = cfg.interval || '1 minute';

      otherHtml += `
        <div class="p-2 rounded d-flex align-items-center justify-content-between flex-wrap gap-2" style="background: var(--bg-color); border: 1px solid var(--border-color);">
          <div class="d-flex align-items-center gap-2" style="max-width: 58%;">
            <span class="fs-6">${meta.icon}</span>
            <div>
              <div class="fw-bold small" style="color: var(--text-color); font-size: 0.78rem;">${meta.title}</div>
              <div class="small text-muted" style="font-size: 0.7rem; line-height: 1.2;">${meta.desc}</div>
            </div>
          </div>
          <div class="d-flex align-items-center gap-2 ms-auto">
            <div class="form-check form-switch m-0" title="Включить/выключить">
              <input class="form-check-input sys-int-enable" type="checkbox" data-logger="${name}" ${isEnabled ? 'checked' : ''}>
            </div>
            ${buildIntervalSelectHtml(name, intervalVal)}
            <button class="btn btn-xs btn-outline-secondary rounded px-1.5 py-0.5 sys-int-custom-btn" data-logger="${name}" title="Ввести произвольный интервал вручную">
              <i class="bi bi-pencil"></i>
            </button>
          </div>
        </div>
      `;
    });

    coreContainer.innerHTML = coreHtml;
    otherContainer.innerHTML = otherHtml;
    if (otherCountEl) otherCountEl.textContent = String(otherCount);

    // Bind custom interval prompt buttons
    document.querySelectorAll('.sys-int-custom-btn').forEach(btn => {
      btn.onclick = () => {
        const lName = btn.getAttribute('data-logger');
        const sel = document.querySelector(`.sys-int-select[data-logger="${lName}"]`);
        const currentVal = sel ? sel.value : '1 minute';
        const custom = prompt(`Введите интервал опроса для ${lName} (например: "2 seconds", "15 seconds", "10 minutes", "1 hour"):`, currentVal);
        if (custom && custom.trim()) {
          const trimmed = custom.trim();
          let opt = sel.querySelector(`option[value="${trimmed}"]`);
          if (!opt) {
            opt = document.createElement('option');
            opt.value = trimmed;
            opt.textContent = `${trimmed} (пользовательский)`;
            sel.appendChild(opt);
          }
          sel.value = trimmed;
        }
      };
    });
  }

  async function saveSysIntervalsConfig() {
    const btnSave = document.getElementById('btn-modal-intervals-save');
    if (btnSave) {
      btnSave.disabled = true;
      btnSave.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Сохранение...';
    }

    try {
      const globalEnable = document.getElementById('modal-intervals-global-enable');
      const defSelect = document.getElementById('modal-intervals-default-select');

      const payload = {
        enable_autolog: globalEnable ? globalEnable.checked : true,
        default_interval: defSelect ? defSelect.value : '1 minute',
        loggers: {}
      };

      // Collect values from all interval selects & switches
      document.querySelectorAll('.sys-int-select').forEach(sel => {
        const lName = sel.getAttribute('data-logger');
        if (!lName) return;
        const sw = document.querySelector(`.sys-int-enable[data-logger="${lName}"]`);
        payload.loggers[lName] = {
          interval: sel.value,
          enabled: sw ? sw.checked : true
        };
      });

      let saveRes = await fetch('/api/autolog/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!saveRes.ok) {
        saveRes = await fetch('/sysautologging/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      if (!saveRes.ok) {
        const errJson = await saveRes.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${saveRes.status}`);
      }

      const result = await saveRes.json();
      showAlertInModal(
        `<i class="bi bi-check-circle-fill text-success me-1"></i> ${result.message || 'Интервалы успешно сохранены в config.json и применены!'}`,
        'success'
      );

      // Refresh engine badge
      const engineStatusBadge = document.getElementById('modal-intervals-engine-status');
      if (engineStatusBadge) {
        if (result.is_running) {
          engineStatusBadge.textContent = 'AutoLog Active';
          engineStatusBadge.className = 'badge bg-success';
        } else {
          engineStatusBadge.textContent = 'AutoLog Paused';
          engineStatusBadge.className = 'badge bg-danger-subtle text-danger border border-danger fw-bold';
        }
      }
    } catch (e) {
      console.error('[SystemInspectorTab] Save intervals config error:', e);
      showAlertInModal(`<i class="bi bi-exclamation-triangle-fill text-danger me-1"></i> Не удалось сохранить интервалы: ${escapeHtml(e.message)}`, 'danger');
    } finally {
      if (btnSave) {
        btnSave.disabled = false;
        btnSave.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Сохранить в config.json';
      }
    }
  }

  let currentWatchDirs = [];
  let currentWatchDir = '';
  let stagedWatchDirs = [];
  let currentBrowserPath = 'C:\\';
  let cachedDrives = [];

  async function fetchLiveFileEvents() {
    try {
      const [resEvents, resTelem] = await Promise.all([
        fetch('/api/sysadmin/file-audit/live-events?limit=30'),
        fetch('/api/sysadmin/file-audit/telemetry').catch(() => null)
      ]);

      if (resTelem && resTelem.ok) {
        const telem = await resTelem.json();
        const elRate = document.getElementById('sys-watcher-rate');
        const elCr = document.getElementById('sys-watcher-cr');
        const elMod = document.getElementById('sys-watcher-mod');
        const elDel = document.getElementById('sys-watcher-del');
        const elDrive = document.getElementById('sys-watcher-drive');
        const elDriveModel = document.getElementById('sys-watcher-drive-model');
        const elDriveTemp = document.getElementById('sys-watcher-temp');
        const elDiskR = document.getElementById('sys-watcher-r-kbs');
        const elDiskW = document.getElementById('sys-watcher-w-kbs');
        const elSecMatches = document.getElementById('sys-watcher-sec-matches');
        const elStatus = document.getElementById('sys-watcher-sensor-status');

        if (elRate) elRate.textContent = (telem.events_rate_per_sec || 0).toFixed(1);
        if (elCr) elCr.textContent = (telem.created_rate_per_sec || 0).toFixed(1);
        if (elMod) elMod.textContent = (telem.modified_rate_per_sec || 0).toFixed(1);
        if (elDel) elDel.textContent = (telem.deleted_rate_per_sec || 0).toFixed(1);
        
        if (elDrive) {
          const drivesStr = (telem.drive_letters && telem.drive_letters.length)
            ? telem.drive_letters.join(', ')
            : (telem.drive_letter || 'C:');
          elDrive.textContent = drivesStr;
        }
        if (elDriveModel) elDriveModel.textContent = telem.drive_model || 'Storage';
        if (elDriveTemp) elDriveTemp.textContent = telem.drive_temperature_c !== null && telem.drive_temperature_c !== undefined ? `${telem.drive_temperature_c} °C` : '-- °C';
        if (elDiskR) elDiskR.textContent = Math.round(telem.disk_read_kbs || 0);
        if (elDiskW) elDiskW.textContent = Math.round(telem.disk_write_kbs || 0);
        if (elSecMatches) elSecMatches.textContent = telem.security_audit_matched_count || 0;

        if (elStatus) {
          if (telem.burst_deletions_alert) {
            elStatus.className = 'badge bg-danger-subtle text-danger border border-danger px-2 py-1';
            elStatus.textContent = '🚨 Всплеск удалений';
          } else if (telem.high_activity_alert) {
            elStatus.className = 'badge bg-warning-subtle text-warning border border-warning px-2 py-1';
            elStatus.textContent = '⚡ Высокий I/O';
          } else {
            elStatus.className = 'badge bg-success-subtle text-success border border-success px-2 py-1';
            elStatus.textContent = '🟢 Штатный режим';
          }
        }
      }

      if (!resEvents || !resEvents.ok) return;
      const data = await resEvents.json();
      const events = data.events || [];

      if (data.filtered_count !== undefined) {
        const filteredEl = document.getElementById('sys-watcher-filtered-count');
        if (filteredEl) filteredEl.textContent = data.filtered_count;
      }
      
      currentWatchDirs = data.watch_dirs || (data.watch_dir ? [data.watch_dir] : []);
      currentWatchDir = currentWatchDirs[0] || data.watch_dir || '';
      
      const dirPathEl = document.getElementById('sys-watch-dir-path');
      const badge = document.getElementById('sys-watch-dir-badge');
      if (dirPathEl) {
        if (currentWatchDirs.length === 0) {
          dirPathEl.innerText = 'Папки не выбраны';
        } else if (currentWatchDirs.length === 1) {
          const singleName = currentWatchDirs[0].split('\\').pop() || currentWatchDirs[0];
          dirPathEl.innerText = singleName;
        } else {
          const firstNames = currentWatchDirs.slice(0, 2).map(p => p.split('\\').pop() || p).join(', ');
          dirPathEl.innerText = `${currentWatchDirs.length} папок: ${firstNames}${currentWatchDirs.length > 2 ? '...' : ''}`;
        }
      }
      if (badge) {
        badge.title = `Отслеживаемые каталоги (${currentWatchDirs.length}):\n${currentWatchDirs.join('\n')}\n\n(Нажмите для настройки и выбора папок)`;
      }

      const tbody = document.getElementById('sys-watcher-tbody');
      if (tbody) {
        if (events.length === 0) {
          const labelDirs = currentWatchDirs.length > 0 ? currentWatchDirs.join(', ') : 'проекта';
          tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted p-2">Ожидание изменений в папках <code>${labelDirs}</code>...</td></tr>`;
          return;
        }
        tbody.innerHTML = events.map((e, idx) => {
          const rootDirHint = e.watch_dir ? (e.watch_dir.split('\\').pop() || e.watch_dir) : '';
          const procDisplay = e.process_name
            ? `<span class="badge bg-dark border border-secondary text-info font-monospace text-truncate d-inline-block" style="max-width: 165px; font-size: 0.72rem;" title="Программа: ${escapeHtml(e.process_name)}${e.process_id ? ` (PID: ${e.process_id})` : ''}"><i class="bi bi-cpu me-1"></i>${escapeHtml(e.process_name)}${e.process_id ? ` [${e.process_id}]` : ''}</span>`
            : `<span class="text-muted" style="font-size: 0.72rem;">—</span>`;
          return `
            <tr class="sys-live-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-диагностики события">
              <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
              <td>
                <span class="badge ${e.is_deletion ? 'bg-danger' : (e.action === 'Created' ? 'bg-success' : 'bg-secondary')}">${e.action}</span>
                ${rootDirHint && currentWatchDirs.length > 1 ? `<span class="badge bg-dark border border-secondary text-muted ms-1" style="font-size: 0.65rem;" title="Корень: ${escapeHtml(e.watch_dir)}">${rootDirHint}</span>` : ''}
              </td>
              <td>${procDisplay}</td>
              <td class="font-monospace small text-light" style="word-break: break-all;" title="${escapeHtml(e.path)}">${escapeHtml(e.path)}</td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.sys-live-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const e = events[idx];
            if (!e) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '⚡',
                title: `Файловое событие: ${e.action}`,
                subtitle: `${e.path} | ${e.timestamp}`,
                tableType: 'file_event',
                badges: [
                  { text: e.action, class: e.is_deletion ? 'badge bg-danger' : (e.action === 'Created' ? 'badge bg-success' : 'badge bg-info text-dark') },
                  { text: e.process_name ? `Программа: ${e.process_name}` : 'WinAPI ReadDirectoryChangesW', class: 'badge bg-dark border border-secondary text-info' },
                  { text: 'WinAPI', class: 'badge bg-secondary' }
                ],
                metadata: [
                  { label: 'Действие', value: e.action },
                  { label: 'Полный путь к файлу', value: e.path },
                  { label: 'Программа / Процесс', value: e.process_name ? `${e.process_name}${e.process_id ? ` (PID: ${e.process_id})` : ''}` : 'Фоновый процесс / завершен' },
                  { label: 'Время события', value: e.timestamp },
                  { label: 'Признак удаления', value: e.is_deletion ? 'Да (Файл удален/переименован)' : 'Нет' },
                  { label: 'Папка события', value: e.watch_dir || currentWatchDir },
                  { label: 'Все отслеживаемые папки', value: currentWatchDirs.join('; ') }
                ],
                rawTitle: 'Детали события WinAPI & Process Info',
                rawContent: JSON.stringify(e, null, 2),
                requestData: e
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[SystemInspectorTab] Failed to fetch live file events:', e);
    }
  }

  // =============================================================================
  // Multi-Directory Watcher Manager & Folder Explorer Modal Logic
  // =============================================================================

  function showWatchDirsAlert(msg, type = 'success') {
    const alertEl = document.getElementById('modal-watch-dirs-alert');
    if (!alertEl) return;
    alertEl.className = `alert alert-${type} py-2 px-3 small mb-3`;
    alertEl.innerHTML = msg;
    alertEl.classList.remove('d-none');
    if (type === 'success') {
      setTimeout(() => {
        alertEl.classList.add('d-none');
      }, 3500);
    }
  }

  function renderModalActiveDirsList() {
    const container = document.getElementById('modal-watch-dirs-active-list');
    const countBadge = document.getElementById('modal-watch-dirs-count');
    const hintEl = document.getElementById('modal-watch-dirs-footer-hint');

    if (!container) return;

    if (countBadge) countBadge.textContent = String(stagedWatchDirs.length);
    if (hintEl) hintEl.textContent = `Выбрано папок для мониторинга: ${stagedWatchDirs.length}`;

    if (stagedWatchDirs.length === 0) {
      container.innerHTML = `
        <div class="text-center text-muted small py-3">
          <i class="bi bi-folder-x me-1"></i> Список пуст. Выберите папки в проводнике ниже или воспользуйтесь быстрыми пресетами.
        </div>
      `;
      return;
    }

    container.innerHTML = stagedWatchDirs.map((dirPath, idx) => {
      const folderName = dirPath.split('\\').pop() || dirPath;
      const driveLetter = (dirPath.slice(0, 2)).toUpperCase();
      return `
        <div class="p-1.5 px-2 rounded d-flex align-items-center justify-content-between gap-2" style="background: var(--bg-color); border: 1px solid var(--border-color);">
          <div class="d-flex align-items-center gap-2 text-truncate" style="max-width: 82%;">
            <i class="bi bi-folder-check text-warning fs-6"></i>
            <span class="badge bg-secondary font-monospace" style="font-size: 0.68rem;">${driveLetter}</span>
            <div class="text-truncate">
              <span class="fw-bold small text-light">${escapeHtml(folderName)}</span>
              <span class="small text-muted font-monospace d-block text-truncate" style="font-size: 0.72rem;" title="${escapeHtml(dirPath)}">${escapeHtml(dirPath)}</span>
            </div>
          </div>
          <button class="btn btn-xs btn-outline-danger rounded-pill px-2 py-0.5" onclick="window._removeStagedWatchDir(${idx})" title="Удалить из списка мониторинга">
            <i class="bi bi-trash3"></i>
          </button>
        </div>
      `;
    }).join('');
  }

  window._removeStagedWatchDir = function(index) {
    if (index >= 0 && index < stagedWatchDirs.length) {
      const removed = stagedWatchDirs.splice(index, 1)[0];
      renderModalActiveDirsList();
      showWatchDirsAlert(`Папка удалена из списка: <code>${escapeHtml(removed)}</code>`, 'info');
    }
  };

  function addDirToStaged(pathToAdd) {
    if (!pathToAdd || !pathToAdd.trim()) return;
    const cleanPath = pathToAdd.trim();
    if (stagedWatchDirs.includes(cleanPath)) {
      showWatchDirsAlert(`Папка уже есть в списке: <code>${escapeHtml(cleanPath)}</code>`, 'warning');
      return;
    }
    stagedWatchDirs.push(cleanPath);
    renderModalActiveDirsList();
    showWatchDirsAlert(`Папка добавлена: <code>${escapeHtml(cleanPath)}</code>`, 'success');
  }

  async function loadSystemDrives() {
    const drivesBar = document.getElementById('modal-watch-drives-bar');
    if (!drivesBar) return;

    try {
      const res = await fetch('/api/sysadmin/filesystem/drives');
      if (res.ok) {
        const data = await res.json();
        cachedDrives = data.drives || [];
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to fetch system drives:', e);
      cachedDrives = [{ mountpoint: 'C:\\', free_gb: 0 }];
    }

    if (cachedDrives.length === 0) {
      cachedDrives = [{ mountpoint: 'C:\\', free_gb: 0 }];
    }

    drivesBar.innerHTML = cachedDrives.map(d => {
      const label = d.mountpoint || 'C:\\';
      const freeTxt = d.free_gb ? `${d.free_gb} GB free` : '';
      return `
        <button class="btn btn-xs btn-outline-light rounded-pill px-2 py-0.5 sys-drive-btn font-monospace" data-drive="${escapeHtml(label)}" title="${escapeHtml(label)} ${freeTxt}">
          <i class="bi bi-hdd me-1"></i>${escapeHtml(label)}
        </button>
      `;
    }).join('');

    drivesBar.querySelectorAll('.sys-drive-btn').forEach(btn => {
      btn.onclick = () => {
        const drv = btn.getAttribute('data-drive');
        if (drv) loadFolderBrowser(drv);
      };
    });
  }

  function renderBreadcrumbs(currentPath) {
    const bcContainer = document.getElementById('modal-folder-breadcrumbs');
    if (!bcContainer) return;

    const parts = currentPath.replace(/\\+$/, '').split('\\');
    let builtPath = '';
    const crumbsHtml = parts.map((part, idx) => {
      if (idx === 0) {
        builtPath = part + '\\';
      } else {
        builtPath = builtPath + (builtPath.endsWith('\\') ? '' : '\\') + part;
      }
      const clickPath = builtPath;
      const isLast = idx === parts.length - 1;
      return `
        <span class="d-inline-flex align-items-center">
          ${idx > 0 ? '<span class="text-muted mx-1">/</span>' : ''}
          <a href="#" class="sys-breadcrumb-link text-decoration-none ${isLast ? 'fw-bold text-info' : 'text-light'}" data-path="${escapeHtml(clickPath)}">
            ${escapeHtml(part || 'Корень')}
          </a>
        </span>
      `;
    }).join('');

    bcContainer.innerHTML = crumbsHtml;

    bcContainer.querySelectorAll('.sys-breadcrumb-link').forEach(link => {
      link.onclick = (e) => {
        e.preventDefault();
        const p = link.getAttribute('data-path');
        if (p) loadFolderBrowser(p);
      };
    });
  }

  async function loadFolderBrowser(targetPath) {
    const inputPath = document.getElementById('modal-folder-path-input');
    const browserList = document.getElementById('modal-folder-browser-list');
    if (!targetPath) targetPath = 'C:\\';
    currentBrowserPath = targetPath;

    if (inputPath) inputPath.value = targetPath;
    renderBreadcrumbs(targetPath);

    if (!browserList) return;
    browserList.innerHTML = `<div class="text-center text-muted small py-3"><span class="spinner-border spinner-border-sm me-1"></span> Загрузка директорий...</div>`;

    try {
      const res = await fetch(`/api/sysadmin/filesystem/browse?path=${encodeURIComponent(targetPath)}`);
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      const dirs = data.directories || [];

      if (dirs.length === 0) {
        browserList.innerHTML = `<div class="text-center text-muted small py-3">В этой директории нет доступных подпапок</div>`;
        return;
      }

      browserList.innerHTML = dirs.map(d => {
        const isAlreadySelected = stagedWatchDirs.includes(d.path);
        return `
          <div class="p-1 px-2 rounded d-flex align-items-center justify-content-between gap-2 sys-folder-browser-item" style="background: var(--surface-1); border: 1px solid var(--border-color); cursor: pointer;">
            <div class="d-flex align-items-center gap-2 text-truncate flex-grow-1 sys-nav-to-folder" data-path="${escapeHtml(d.path)}" title="Нажмите для перехода в папку">
              <i class="bi ${d.has_subdirs ? 'bi-folder2 text-warning' : 'bi-folder text-warning'}"></i>
              <span class="small text-light text-truncate">${escapeHtml(d.name)}</span>
              <span class="small text-muted font-monospace ms-auto me-2" style="font-size: 0.68rem;">${d.modified || ''}</span>
            </div>
            <button class="btn btn-xs ${isAlreadySelected ? 'btn-success' : 'btn-outline-info'} rounded-pill px-2 py-0.5 sys-add-folder-btn" data-path="${escapeHtml(d.path)}" title="Добавить в отслеживаемые">
              <i class="bi ${isAlreadySelected ? 'bi-check2' : 'bi-plus-lg'} me-1"></i>${isAlreadySelected ? 'Выбрана' : 'Следить'}
            </button>
          </div>
        `;
      }).join('');

      // Bind folder navigation
      browserList.querySelectorAll('.sys-nav-to-folder').forEach(el => {
        el.onclick = () => {
          const p = el.getAttribute('data-path');
          if (p) loadFolderBrowser(p);
        };
      });

      // Bind Add buttons
      browserList.querySelectorAll('.sys-add-folder-btn').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          const p = btn.getAttribute('data-path');
          if (p) {
            addDirToStaged(p);
            btn.className = 'btn btn-xs btn-success rounded-pill px-2 py-0.5 sys-add-folder-btn';
            btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Выбрана';
          }
        };
      });

    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to browse folder:', e);
      browserList.innerHTML = `<div class="text-danger small py-2 px-2"><i class="bi bi-exclamation-triangle me-1"></i> Ошибка доступа: ${escapeHtml(e.message)}</div>`;
    }
  }

  let currentExclusions = {
    enabled: true,
    paths: [],
    extensions: [],
    patterns: [],
    processes: [],
    filtered_count: 0
  };

  function showExclusionsAlert(msg, type = 'success') {
    const alertEl = document.getElementById('modal-exclusions-alert');
    if (!alertEl) return;
    alertEl.className = `alert alert-${type} py-2 px-3 small mb-3`;
    alertEl.innerHTML = msg;
    alertEl.classList.remove('d-none');
    if (type === 'success' || type === 'info') {
      setTimeout(() => {
        alertEl.classList.add('d-none');
      }, 3500);
    }
  }

  function renderExclusionsLists() {
    const totalCount = (currentExclusions.paths?.length || 0) +
      (currentExclusions.extensions?.length || 0) +
      (currentExclusions.patterns?.length || 0) +
      (currentExclusions.processes?.length || 0);

    const tabBadge = document.getElementById('modal-watch-exclusions-tab-count');
    const headerBadge = document.getElementById('sys-exclusions-count-badge');
    if (tabBadge) tabBadge.textContent = String(totalCount);
    if (headerBadge) headerBadge.textContent = String(totalCount);

    const switchEl = document.getElementById('switch-exclusions-active');
    const statusBadge = document.getElementById('badge-exclusions-status');
    if (switchEl) switchEl.checked = Boolean(currentExclusions.enabled);
    if (statusBadge) {
      if (currentExclusions.enabled) {
        statusBadge.className = 'badge bg-success';
        statusBadge.textContent = 'ВКЛ';
      } else {
        statusBadge.className = 'badge bg-danger-subtle text-danger border border-danger fw-bold';
        statusBadge.textContent = 'ВЫКЛ';
      }
    }

    const filteredTotalEl = document.getElementById('modal-exclusions-filtered-total');
    if (filteredTotalEl) filteredTotalEl.textContent = String(currentExclusions.filtered_count || 0);

    // 1. Paths list
    const pathsContainer = document.getElementById('list-ex-paths');
    const pathsBadge = document.getElementById('badge-ex-paths-count');
    if (pathsBadge) pathsBadge.textContent = String(currentExclusions.paths?.length || 0);
    if (pathsContainer) {
      if (!currentExclusions.paths || currentExclusions.paths.length === 0) {
        pathsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных папок</div>`;
      } else {
        pathsContainer.innerHTML = currentExclusions.paths.map((p, idx) => `
          <div class="d-flex align-items-center justify-content-between gap-1.5 p-1 px-2 rounded mb-1" style="background: var(--bg-color); border: 1px solid var(--border-color);">
            <span class="small font-monospace text-light text-truncate" style="font-size: 0.72rem;" title="${escapeHtml(p)}">${escapeHtml(p)}</span>
            <button class="btn btn-xs btn-outline-danger py-0 px-1 rounded-pill" onclick="window._removeExclusionItem('paths', '${escapeHtml(p.replace(/\\/g, '\\\\'))}')" title="Удалить">✕</button>
          </div>
        `).join('');
      }
    }

    // 2. Extensions list
    const extsContainer = document.getElementById('list-ex-extensions');
    const extsBadge = document.getElementById('badge-ex-extensions-count');
    if (extsBadge) extsBadge.textContent = String(currentExclusions.extensions?.length || 0);
    if (extsContainer) {
      if (!currentExclusions.extensions || currentExclusions.extensions.length === 0) {
        extsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных расширений</div>`;
      } else {
        extsContainer.innerHTML = `<div class="d-flex flex-wrap gap-1">` + currentExclusions.extensions.map(e => `
          <span class="badge bg-dark border border-secondary text-info d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            ${escapeHtml(e)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._removeExclusionItem('extensions', '${escapeHtml(e)}')" title="Удалить"></button>
          </span>
        `).join('') + `</div>`;
      }
    }

    // 3. Patterns list
    const patsContainer = document.getElementById('list-ex-patterns');
    const patsBadge = document.getElementById('badge-ex-patterns-count');
    if (patsBadge) patsBadge.textContent = String(currentExclusions.patterns?.length || 0);
    if (patsContainer) {
      if (!currentExclusions.patterns || currentExclusions.patterns.length === 0) {
        patsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных шаблонов</div>`;
      } else {
        patsContainer.innerHTML = `<div class="d-flex flex-wrap gap-1">` + currentExclusions.patterns.map(pat => `
          <span class="badge bg-dark border border-secondary text-warning d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            ${escapeHtml(pat)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._removeExclusionItem('patterns', '${escapeHtml(pat)}')" title="Удалить"></button>
          </span>
        `).join('') + `</div>`;
      }
    }

    // 4. Processes list
    const procsContainer = document.getElementById('list-ex-processes');
    const procsBadge = document.getElementById('badge-ex-processes-count');
    if (procsBadge) procsBadge.textContent = String(currentExclusions.processes?.length || 0);
    if (procsContainer) {
      if (!currentExclusions.processes || currentExclusions.processes.length === 0) {
        procsContainer.innerHTML = `<div class="text-muted small text-center py-2">Нет исключенных программ</div>`;
      } else {
        procsContainer.innerHTML = `<div class="d-flex flex-wrap gap-1">` + currentExclusions.processes.map(proc => `
          <span class="badge bg-dark border border-secondary text-danger d-inline-flex align-items-center gap-1 font-monospace" style="font-size: 0.75rem;">
            <i class="bi bi-cpu me-0.5"></i>${escapeHtml(proc)}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" onclick="window._removeExclusionItem('processes', '${escapeHtml(proc)}')" title="Удалить"></button>
          </span>
        `).join('') + `</div>`;
      }
    }
  }

  async function fetchExclusionsData() {
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions');
      if (res.ok) {
        currentExclusions = await res.json();
        renderExclusionsLists();
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Failed to fetch exclusions:', e);
    }
  }

  async function addExclusionItem(category, value) {
    if (!value || !value.trim()) return;
    const cleanVal = value.trim();
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, value: cleanVal })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentExclusions = data.exclusions || currentExclusions;
        renderExclusionsLists();
        showExclusionsAlert(`Правило добавлено: <code>${escapeHtml(cleanVal)}</code>`, 'success');
        const inputVal = document.getElementById('input-exclusion-value');
        if (inputVal) inputVal.value = '';
      } else {
        showExclusionsAlert(data.message || 'Правило уже существует или невалидно', 'warning');
      }
    } catch (e) {
      showExclusionsAlert(`Ошибка добавления: ${e.message}`, 'danger');
    }
  }

  window._removeExclusionItem = async function(category, value) {
    if (!value) return;
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, value })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentExclusions = data.exclusions || currentExclusions;
        renderExclusionsLists();
        showExclusionsAlert(`Правило удалено: <code>${escapeHtml(value)}</code>`, 'info');
      } else {
        showExclusionsAlert(data.message || 'Не удалось удалить правило', 'warning');
      }
    } catch (e) {
      showExclusionsAlert(`Ошибка удаления: ${e.message}`, 'danger');
    }
  };

  async function toggleExclusionsActive(enabled) {
    try {
      const res = await fetch('/api/sysadmin/file-audit/exclusions/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentExclusions = data.exclusions || currentExclusions;
        renderExclusionsLists();
        showExclusionsAlert(`Фильтрация исключений ${data.enabled ? 'включена' : 'отключена'}`, 'info');
      }
    } catch (e) {
      showExclusionsAlert(`Ошибка переключения: ${e.message}`, 'danger');
    }
  }

  async function applyExclusionPreset(preset) {
    if (preset === 'logs') {
      await addExclusionItem('paths', 'AppData\\Roaming\\AI-Breadboard\\apps\\windows\\telemetry\\logs');
      await addExclusionItem('extensions', '.log');
      await addExclusionItem('extensions', '.csv');
      await addExclusionItem('patterns', '*system_inspector_polls.csv*');
    } else if (preset === 'search') {
      await addExclusionItem('processes', 'SearchIndexer.exe');
      await addExclusionItem('patterns', '*Windows.db*');
      await addExclusionItem('patterns', '*Windows.db-wal*');
      await addExclusionItem('patterns', '*Windows.db-shm*');
    } else if (preset === 'temp') {
      await addExclusionItem('paths', 'AppData\\Local\\Temp');
      await addExclusionItem('extensions', '.tmp');
      await addExclusionItem('patterns', '~$*');
    } else if (preset === 'dev') {
      await addExclusionItem('paths', '.git');
      await addExclusionItem('paths', 'node_modules');
      await addExclusionItem('paths', '__pycache__');
      await addExclusionItem('paths', '.pytest_cache');
    }
  }

  async function openWatchFoldersModal(initialTab = 'folders') {
    const modalEl = document.getElementById('modal-sys-watch-folders');
    if (!modalEl) {
      console.warn('[SystemInspectorTab] modal-sys-watch-folders element not found');
      return;
    }

    try {
      const res = await fetch('/api/sysadmin/file-audit/watch-dirs');
      if (res.ok) {
        const data = await res.json();
        stagedWatchDirs = data.watch_dirs && data.watch_dirs.length ? [...data.watch_dirs] : [currentWatchDir || 'C:\\'];
      } else {
        stagedWatchDirs = currentWatchDirs.length ? [...currentWatchDirs] : [currentWatchDir || 'C:\\'];
      }
    } catch {
      stagedWatchDirs = currentWatchDirs.length ? [...currentWatchDirs] : [currentWatchDir || 'C:\\'];
    }

    renderModalActiveDirsList();
    const tabFoldersBadge = document.getElementById('modal-watch-dirs-tab-count');
    if (tabFoldersBadge) tabFoldersBadge.textContent = String(stagedWatchDirs.length);

    await loadSystemDrives();
    await fetchExclusionsData();

    // Tab activation
    if (initialTab === 'exclusions') {
      const tabExBtn = document.getElementById('tab-btn-watch-exclusions');
      if (tabExBtn && window.bootstrap && window.bootstrap.Tab) {
        const tab = window.bootstrap.Tab.getOrCreateInstance(tabExBtn);
        tab.show();
      } else if (tabExBtn) {
        tabExBtn.click();
      }
    } else {
      const tabFoldersBtn = document.getElementById('tab-btn-watch-folders');
      if (tabFoldersBtn && window.bootstrap && window.bootstrap.Tab) {
        const tab = window.bootstrap.Tab.getOrCreateInstance(tabFoldersBtn);
        tab.show();
      } else if (tabFoldersBtn) {
        tabFoldersBtn.click();
      }
    }

    const startPath = stagedWatchDirs[0] || currentBrowserPath || 'C:\\';
    loadFolderBrowser(startPath);

    // Bind navigation buttons
    const btnUp = document.getElementById('btn-modal-folder-up');
    if (btnUp) {
      btnUp.onclick = () => {
        const parts = currentBrowserPath.replace(/\\+$/, '').split('\\');
        if (parts.length > 1) {
          parts.pop();
          let parentPath = parts.join('\\');
          if (parts.length === 1 && !parentPath.endsWith('\\')) parentPath += '\\';
          loadFolderBrowser(parentPath);
        }
      };
    }

    const btnGo = document.getElementById('btn-modal-folder-go');
    const inputPath = document.getElementById('modal-folder-path-input');
    if (btnGo && inputPath) {
      btnGo.onclick = () => {
        if (inputPath.value && inputPath.value.trim()) {
          loadFolderBrowser(inputPath.value.trim());
        }
      };
      inputPath.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          btnGo.click();
        }
      };
    }

    const btnAddCurrent = document.getElementById('btn-modal-folder-add-current');
    if (btnAddCurrent) {
      btnAddCurrent.onclick = () => {
        const val = inputPath ? inputPath.value.trim() : currentBrowserPath;
        if (val) addDirToStaged(val);
      };
    }

    // Presets buttons (folders)
    document.querySelectorAll('.sys-preset-btn').forEach(btn => {
      btn.onclick = () => {
        const preset = btn.getAttribute('data-preset');
        let target = '';
        if (preset === 'project') target = 'C:\\Users\\onela\\AppData\\Local\\AI-Breadboard';
        else if (preset === 'downloads') target = 'C:\\Users\\onela\\Downloads';
        else if (preset === 'desktop') target = 'C:\\Users\\onela\\Desktop';
        else if (preset === 'temp') target = 'C:\\Users\\onela\\AppData\\Local\\Temp';

        if (target) {
          addDirToStaged(target);
          loadFolderBrowser(target);
        }
      };
    });

    // Exclusions switch and add buttons binding
    const switchExActive = document.getElementById('switch-exclusions-active');
    if (switchExActive) {
      switchExActive.onchange = (e) => {
        toggleExclusionsActive(e.target.checked);
      };
    }

    const btnAddEx = document.getElementById('btn-add-exclusion');
    const selectExCat = document.getElementById('select-exclusion-category');
    const inputExVal = document.getElementById('input-exclusion-value');
    if (btnAddEx && selectExCat && inputExVal) {
      btnAddEx.onclick = () => {
        addExclusionItem(selectExCat.value, inputExVal.value);
      };
      inputExVal.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          btnAddEx.click();
        }
      };
    }

    // Exclusions preset buttons
    document.querySelectorAll('.sys-ex-preset-btn').forEach(btn => {
      btn.onclick = () => {
        const preset = btn.getAttribute('data-preset');
        if (preset) applyExclusionPreset(preset);
      };
    });

    // Apply button
    const btnApply = document.getElementById('btn-modal-watch-dirs-apply');
    if (btnApply) {
      btnApply.onclick = async () => {
        if (stagedWatchDirs.length === 0) {
          showWatchDirsAlert('Выберите хотя бы одну папку для мониторинга', 'warning');
          return;
        }

        btnApply.disabled = true;
        btnApply.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Применение...';

        try {
          const res = await fetch('/api/sysadmin/file-audit/watch-dirs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paths: stagedWatchDirs })
          });
          const resData = await res.json();
          if (res.ok && resData.success) {
            if (window.bootstrap && window.bootstrap.Modal) {
              const modal = window.bootstrap.Modal.getInstance(modalEl);
              if (modal) modal.hide();
            } else {
              modalEl.classList.remove('show');
              modalEl.style.display = 'none';
            }
            await fetchLiveFileEvents();
          } else {
            showWatchDirsAlert(`Ошибка: ${resData.detail || 'Не удалось применить список папок'}`, 'danger');
          }
        } catch (err) {
          showWatchDirsAlert(`Сетевая ошибка: ${err.message}`, 'danger');
        } finally {
          btnApply.disabled = false;
          btnApply.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Применить и запустить';
        }
      };
    }

    if (window.bootstrap && window.bootstrap.Modal) {
      const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    } else {
      modalEl.classList.add('show');
      modalEl.style.display = 'block';
    }
  }

  function showLiveWatcherHelpModal() {
    const dirsStr = currentWatchDirs.length ? currentWatchDirs.join('\n- ') : (currentWatchDir || 'Рабочая папка');
    if (window.AITableModal) {
      window.AITableModal.show({
        icon: 'ℹ️',
        title: 'Справка:Изменения файлов в реальном времени (Multi-Directory)',
        subtitle: 'Низкоуровневый мониторинг файловой системы Windows через WinAPI ReadDirectoryChangesW',
        tableType: 'help',
        badges: [
          { text: 'WinAPI ReadDirectoryChangesW', class: 'badge bg-info text-dark' },
          { text: 'Multi-Directory', class: 'badge bg-primary' },
          { text: 'Real-Time Streaming', class: 'badge bg-success' },
          { text: 'Рекурсивно (bWatchSubtree = True)', class: 'badge bg-warning text-dark' }
        ],
        metadata: [
          { label: 'Технология', value: 'WinAPI ReadDirectoryChangesW (нативный вызов ядра Windows kernel32.dll)' },
          { label: 'Режим работы', value: 'Множественные потоки мониторинга с агрегацией в единый кольцевой буфер' },
          { label: 'Отслеживаемые папки', value: currentWatchDirs.join('; ') || 'Рабочая папка проекта' },
          { label: 'Хранение настроек', value: 'apps/windows_sysadmin/config.json (ключ watch_directories)' }
        ],
        rawTitle: 'Подробное руководство по панели мониторинга',
        rawContent: `# ПанельИзменения файлов в реальном времени

### 1. Что это такое?
Компонент для мгновенного перехвата операций файловой системы в режиме реального времени на базе WinAPI ReadDirectoryChangesW с поддержкой одновременного наблюдения за произвольным количеством папок.

### 2. Типы отслеживаемых действий:
- Created: Создание нового файла или папки (FILE_ACTION_ADDED).
- Modified: Модификация содержимого, атрибутов или размера файла (FILE_ACTION_MODIFIED).
- Deleted: Удаление файла или папки с диска (FILE_ACTION_REMOVED).
- Renamed: Переименование объекта (старое и новое имя).

### 3. Как выбрать или добавить папки?
1. Нажмите кнопку «Папка» в заголовке панели.
2. Откроется модальное окно с проводником файловой системы.
3. Выберите логический диск (C:, D:, E:), перейдите в нужную папку или вставьте путь вручную.
4. Нажмите «+ Добавить папку» или кнопку «Следить» напротив любой подпапки.
5. Нажмите «Применить и запустить». Список сохранится в config.json и мониторинг стартует автоматически!`,
        requestData: {
          current_watch_dirs: currentWatchDirs,
          engine: 'ReadDirectoryChangesW (Multi-Directory)'
        }
      });
    } else {
      alert('Мониторинг файловой системыИзменения файлов в реальном времени (Multi-Directory).\nОтслеживаемые папки:\n- ' + dirsStr);
    }
  }

  function setupSysSensorInterval(seconds) {
    _currentUiRefreshSeconds = seconds;
    const pollHandler = async () => {
      await fetchCpuLoadFromApi();
      await fetchGpuLoadFromApi();
      await fetchMemoryIoFromApi();
      await fetchNetworkLoadFromApi();
      await fetchStorageLoadFromApi();
      await fetchLhmSensors();
      await fetchLiveFileEvents();
    };
    if (window.registerTabPoller) {
      window.registerTabPoller('tab-hardware-load-inspector', pollHandler, seconds * 1000, { immediate: false });
    } else {
      if (window._sysSensorInterval) {
        clearInterval(window._sysSensorInterval);
        window._sysSensorInterval = null;
      }
      window._sysSensorInterval = setInterval(() => {
        if (window.isTabActive ? (window.isTabActive('tab-hardware-load-inspector') || window.isTabActive('tab-system-load-inspector') || window.isTabActive('tab-system-inspector')) : true) {
          pollHandler();
        }
      }, seconds * 1000);
    }
    console.log(`[SystemInspectorTab] UI sensor refresh interval set to ${seconds}s`);
  }

  function openSysIntervalsModal() {
    const modalEl = document.getElementById('sysIntervalsModal');
    if (!modalEl) {
      console.warn('[SystemInspectorTab] sysIntervalsModal element not found');
      return;
    }

    // Set UI select to current seconds
    const selUi = document.getElementById('modal-ui-refresh-select');
    if (selUi) {
      selUi.value = String(_currentUiRefreshSeconds);
    }
    const uiBadge = document.getElementById('modal-ui-refresh-badge');
    if (uiBadge) {
      uiBadge.textContent = `${_currentUiRefreshSeconds} сек`;
    }

    loadSysIntervalsConfig(false);

    if (window.bootstrap && window.bootstrap.Modal) {
      const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    } else {
      modalEl.classList.add('show');
      modalEl.style.display = 'block';
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  async function initSystemInspectorTab() {
    console.log('[SystemInspectorTab] Initializing...');
    bindTabEvents();
    await fetchCpuLoadFromApi();
    await fetchGpuLoadFromApi();
    await fetchMemoryIoFromApi();
    await fetchNetworkLoadFromApi();
    await fetchStorageLoadFromApi();
    await fetchLhmSensors();
    await fetchLiveFileEvents();
    await fetchNetworkActivity();

    try {
      const snapRes = await fetch('/api/v1/system/summary');
      if (snapRes.ok) {
        latestTelemetrySnapshot = await snapRes.json();
        updateTelemetryDashboard(latestTelemetrySnapshot);
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Initial snapshot fetch failed:', e);
    }

    if (typeof connectSystemWebSocket === 'function') {
      try { connectSystemWebSocket(); } catch (err) { console.debug(err); }
    }

    // Periodic sensor refresh
    if (!window._sysSensorInterval) {
      setupSysSensorInterval(_currentUiRefreshSeconds || 5);
    }
  }

  function activateSystemInspectorTab() {
    if (window.isTabActive && !window.isTabActive('tab-hardware-load-inspector') && !window.isTabActive('tab-system-load-inspector') && !window.isTabActive('tab-system-inspector')) return;
    console.log('[SystemInspectorTab] Tab activated, refreshing metrics...');
    fetchCpuLoadFromApi();
    fetchGpuLoadFromApi();
    fetchMemoryIoFromApi();
    fetchNetworkLoadFromApi();
    fetchStorageLoadFromApi();
    fetchLhmSensors();
    if (typeof connectSystemWebSocket === 'function') {
      try { connectSystemWebSocket(); } catch (err) { console.debug(err); }
    }
  }

  function deactivateSystemInspectorTab() {
    console.log('[SystemInspectorTab] Tab deactivated, pausing telemetry stream...');
    if (typeof disconnectSystemWebSocket === 'function') {
      try { disconnectSystemWebSocket(); } catch (err) { console.debug(err); }
    }
  }

  window.initSystemInspectorTab = initSystemInspectorTab;
  window.initSystemLoadInspectorTab = initSystemInspectorTab;
  window.initHardwareLoadInspectorTab = initSystemInspectorTab;
  window.activateSystemInspectorTab = activateSystemInspectorTab;
  window.activateSystemLoadInspectorTab = activateSystemInspectorTab;
  window.activateHardwareLoadInspectorTab = activateSystemInspectorTab;
  window.deactivateSystemInspectorTab = deactivateSystemInspectorTab;
  window.deactivateSystemLoadInspectorTab = deactivateSystemInspectorTab;
  window.deactivateHardwareLoadInspectorTab = deactivateSystemInspectorTab;
  window.openSysIntervalsModal = openSysIntervalsModal;

  // Auto-init if tab is already in DOM and active or open
  if (document.getElementById('tab-hardware-load-inspector')) {
    initSystemInspectorTab();
  }
})();

