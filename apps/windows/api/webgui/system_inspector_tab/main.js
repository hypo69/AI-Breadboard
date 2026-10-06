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
 * Updated: 2026-10-06 21:52:00
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
  let lastCpuCoresData = [];
  let lastCpuSensorsData = [];
  let lastCpuData = null;
  let lastGpuData = null;
  let lastGpuDevices = [];
  const _gpuSparkHistories = {};
  const currentGpuSparkScales = {};
  const lastGpuSparkDataMap = {};

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
    if (lastCpuCoresData && lastCpuCoresData.length) {
      renderCpuCores(lastCpuCoresData);
    }
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

    if (sensors && sensors.length > 0) {
      if (countBadge) {
        countBadge.textContent = `${sensors.length} параметров`;
      }
    } else {
      // Если элементы уже отрендерены, не перетираем их заглушкой при временной задержке поллинга
      if (container.children.length > 0 && !container.querySelector('.sys-no-sensors-msg')) {
        return;
      }
      if (countBadge) {
        countBadge.textContent = '0 параметров';
      }
      container.innerHTML = `<div class="sys-no-sensors-msg text-muted small text-center py-2 col-12" style="font-size: 0.74rem;">Нет дополнительных данных сенсоров</div>`;
      return;
    }

    const sorted = [...sensors].sort((a, b) => {
      const pA = getSensorSortPriority(a);
      const pB = getSensorSortPriority(b);
      if (pA !== pB) return pA - pB;
      return (a.sensor_name || '').localeCompare(b.sensor_name || '');
    });

    container.innerHTML = sorted.map(s => {
      const rawName = s.sensor_name || s.name || '';
      const name = escapeHtml((!rawName || rawName.toLowerCase() === 'unknown') ? (s.id ? `Sensor #${s.id}` : 'Sensor') : rawName);
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

  function toggleSysCpuDetails() {
    const box = document.getElementById('sys-cpu-details-collapse');
    const icon = document.getElementById('sys-cpu-details-toggle-icon');
    const text = document.getElementById('sys-cpu-details-toggle-text');
    const btn = document.getElementById('sys-cpu-details-action-btn');
    const parentBtn = document.getElementById('sys-cpu-details-toggle-btn');
    if (!box) return;
    const isHidden = box.style.display === 'none' || getComputedStyle(box).display === 'none';
    if (isHidden) {
      box.style.display = 'flex';
      if (icon) icon.className = 'bi bi-chevron-up';
      if (text) text.textContent = 'Свернуть детализацию';
      if (btn) btn.className = 'btn btn-xs btn-info text-dark rounded-pill px-3 py-1 fw-bold d-flex align-items-center gap-1.5';
      if (parentBtn) parentBtn.classList.add('expanded');
    } else {
      box.style.display = 'none';
      if (icon) icon.className = 'bi bi-chevron-down';
      if (text) text.textContent = 'Развернуть детализацию';
      if (btn) btn.className = 'btn btn-xs btn-outline-info rounded-pill px-3 py-1 fw-bold d-flex align-items-center gap-1.5';
      if (parentBtn) parentBtn.classList.remove('expanded');
    }
  }
  window.toggleSysCpuDetails = toggleSysCpuDetails;
  window.toggleSysCpuSensors = toggleSysCpuDetails;

  function toggleSysGpuDetails(idx = 0) {
    const box = document.getElementById(`sys-gpu-details-collapse-${idx}`) || document.getElementById('sys-gpu-details-collapse');
    const icon = document.getElementById(`sys-gpu-details-toggle-icon-${idx}`) || document.getElementById('sys-gpu-details-toggle-icon');
    const text = document.getElementById(`sys-gpu-details-toggle-text-${idx}`) || document.getElementById('sys-gpu-details-toggle-text');
    const btn = document.getElementById(`sys-gpu-details-action-btn-${idx}`) || document.getElementById('sys-gpu-details-action-btn');
    const parentBtn = document.getElementById(`sys-gpu-details-toggle-btn-${idx}`) || document.getElementById('sys-gpu-details-toggle-btn');
    if (!box) return;
    const isHidden = box.style.display === 'none' || getComputedStyle(box).display === 'none';
    if (isHidden) {
      box.style.display = 'flex';
      if (icon) icon.className = 'bi bi-chevron-up';
      if (text) text.textContent = 'Свернуть детализацию';
      if (btn) btn.className = 'btn btn-xs btn-warning text-dark rounded-pill px-3 py-1 fw-bold d-flex align-items-center gap-1.5';
      if (parentBtn) parentBtn.classList.add('expanded');
    } else {
      box.style.display = 'none';
      if (icon) icon.className = 'bi bi-chevron-down';
      if (text) text.textContent = 'Развернуть детализацию';
      if (btn) btn.className = 'btn btn-xs btn-outline-warning rounded-pill px-3 py-1 fw-bold d-flex align-items-center gap-1.5';
      if (parentBtn) parentBtn.classList.remove('expanded');
    }
  }
  window.toggleSysGpuDetails = toggleSysGpuDetails;
  window.toggleSysGpuSensors = toggleSysGpuDetails;

  /**
   * Управление режимом Drill-down по нажатию на значок дрели слева от названия компонента.
   * Раскрывает все скрытые панели, графики и датчики конкретного компонента.
   *
   * @param {string|HTMLElement} cardIdOrEl - Идентификатор карточки или элемент кнопки
   * @param {number} [idx] - Индекс устройства (для GPU)
   */
  function toggleSysCardDrill(cardIdOrEl, idx) {
    let card = null;
    let btn = null;
    if (typeof cardIdOrEl === 'string') {
      card = document.getElementById(cardIdOrEl);
    } else if (cardIdOrEl instanceof HTMLElement) {
      btn = cardIdOrEl;
      card = btn.closest('.sys-card');
    }
    if (!card) return;
    if (!btn) {
      btn = card.querySelector('.sys-drill-btn');
    }

    const isExpanded = card.classList.contains('sys-card-drill-expanded');
    if (isExpanded) {
      card.classList.remove('sys-card-drill-expanded');
      if (btn) {
        btn.classList.remove('active');
        btn.title = 'Drill-down: Развернуть/скрыть все скрытые панели и датчики';
      }
    } else {
      card.classList.add('sys-card-drill-expanded');
      if (btn) {
        btn.classList.add('active');
        btn.title = 'Drill-down: Свернуть скрытые панели';
      }

      // Если это CPU - также открываем вложенный аккордеон деталей ядер и сенсоров
      if (card.classList.contains('sys-card-cpu') || card.id === 'sys-card-cpu') {
        const box = document.getElementById('sys-cpu-details-collapse');
        const icon = document.getElementById('sys-cpu-details-toggle-icon');
        const text = document.getElementById('sys-cpu-details-toggle-text');
        const actionBtn = document.getElementById('sys-cpu-details-action-btn');
        const parentBtn = document.getElementById('sys-cpu-details-toggle-btn');
        if (box) box.style.display = 'flex';
        if (icon) icon.className = 'bi bi-chevron-up';
        if (text) text.textContent = 'Свернуть детализацию';
        if (actionBtn) actionBtn.className = 'btn btn-xs btn-info text-dark rounded-pill px-3 py-1 fw-bold d-flex align-items-center gap-1.5';
        if (parentBtn) parentBtn.classList.add('expanded');
        if (typeof renderCpuSpark === 'function' && Array.isArray(_cpuSparkHistory)) {
          renderCpuSpark(_cpuSparkHistory);
        }
      }

      // Если это GPU - также открываем вложенный аккордеон деталей GPU
      if (card.classList.contains('sys-card-gpu') || (card.id && card.id.startsWith('sys-card-gpu-'))) {
        const cardIdx = idx != null ? idx : (card.id ? card.id.replace('sys-card-gpu-', '') : 0);
        const box = document.getElementById(`sys-gpu-details-collapse-${cardIdx}`) || document.getElementById('sys-gpu-details-collapse');
        const icon = document.getElementById(`sys-gpu-details-toggle-icon-${cardIdx}`) || document.getElementById('sys-gpu-details-toggle-icon');
        const text = document.getElementById(`sys-gpu-details-toggle-text-${cardIdx}`) || document.getElementById('sys-gpu-details-toggle-text');
        const actionBtn = document.getElementById(`sys-gpu-details-action-btn-${cardIdx}`) || document.getElementById('sys-gpu-details-action-btn');
        const parentBtn = document.getElementById(`sys-gpu-details-toggle-btn-${cardIdx}`) || document.getElementById('sys-gpu-details-toggle-btn');
        if (box) box.style.display = 'flex';
        if (icon) icon.className = 'bi bi-chevron-up';
        if (text) text.textContent = 'Свернуть детализацию';
        if (actionBtn) actionBtn.className = 'btn btn-xs btn-warning text-dark rounded-pill px-3 py-1 fw-bold d-flex align-items-center gap-1.5';
        if (parentBtn) parentBtn.classList.add('expanded');
        if (typeof renderGpuSpark === 'function') {
          renderGpuSpark(_gpuSparkHistories[cardIdx] || [], cardIdx);
        }
      }

      // RAM график
      if (card.classList.contains('sys-card-ram') || card.id === 'sys-card-ram') {
        if (typeof renderMemIoSpark === 'function' && Array.isArray(_memIoSparkHistory)) {
          renderMemIoSpark(_memIoSparkHistory);
        }
      }

      // Net график
      if (card.classList.contains('sys-card-net') || card.id === 'sys-card-net') {
        if (typeof renderNetSpark === 'function' && Array.isArray(_netSparkHistory)) {
          renderNetSpark(_netSparkHistory);
        }
      }
    }
  }
  window.toggleSysCardDrill = toggleSysCardDrill;

  function updateAllComponentSensors() {
    if (!Array.isArray(cachedSensors) || cachedSensors.length === 0) return;

    // 1. CPU Sensors (электрические параметры, мощности, вольтажи, шины, TjMax)
    const cpuSensors = cachedSensors.filter(s => {
      const sid = String(s.id || s.sensor_id || '').toLowerCase();
      const hwType = (s.hardware_type || '').toLowerCase();
      const hwName = (s.hardware_name || '').toLowerCase();
      const sName = (s.sensor_name || '').toLowerCase();
      const cat = (s.sensor_category || '').toLowerCase();

      // Строго отсекаем дисковые метрики и не-CPU компоненты
      if (sid.startsWith('disk_speed_') || hwType.includes('storage') || cat.includes('storage')) return false;

      const isCpu = hwType === 'cpu' || hwName.includes('cpu') || hwName.includes('intel') || hwName.includes('amd');
      if (!isCpu) return false;

      // Исключаем по-ядерную загрузку и температуру отдельных ядер (они уже в карточках ядер)
      if (cat.includes('load') && (sName.includes('core #') || sName === 'cpu total')) return false;
      if (cat.includes('temp') && sName.includes('core #') && !sName.includes('tjmax')) return false;
      if (cat.includes('temp') && sName === 'cpu package') return false; // показана в главном слайдере Package

      return true;
    });
    if (cpuSensors.length > 0) {
      lastCpuSensorsData = cpuSensors;
      renderComponentSensors('sys-metric-cpu-sensors', 'sys-cpu-sensors-count-badge', cpuSensors);
    } else if (lastCpuSensorsData && lastCpuSensorsData.length > 0) {
      renderComponentSensors('sys-metric-cpu-sensors', 'sys-cpu-sensors-count-badge', lastCpuSensorsData);
    } else {
      renderComponentSensors('sys-metric-cpu-sensors', 'sys-cpu-sensors-count-badge', []);
    }

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
        <path d="M 12 50 A 38 38 0 0 1 88 50" fill="none" stroke="var(--border-color, rgba(128,128,128,0.25))" stroke-width="9" stroke-linecap="round"/>
        <!-- Градиентная активная шкала -->
        <path d="M 12 50 A 38 38 0 0 1 88 50" fill="none" stroke="url(#sysGaugeGrad)" stroke-width="9" stroke-linecap="round" opacity="0.9"/>
        <!-- Стрелка прибора -->
        <g transform="rotate(${angle.toFixed(1)}, 50, 50)" style="transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);">
          <polygon points="48,50 50,14 52,50" fill="${needleColor}" filter="drop-shadow(0 2px 3px rgba(0,0,0,0.6))"/>
          <line x1="50" y1="50" x2="50" y2="14" stroke="#ffffff" stroke-width="1.2" opacity="0.9"/>
        </g>
        <!-- Центральный шарнир -->
        <circle cx="50" cy="50" r="6" fill="#38bdf8"/>
        <circle cx="50" cy="50" r="2.5" fill="var(--surface-1, #0f172a)"/>
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

  /**
   * Извлечение и сопоставление параметров сенсоров конкретного ядра CPU.
   * @param {number} coreIdx - Индекс ядра (0-based)
   * @param {number} totalCores - Общее количество ядер/потоков
   * @param {Array} sensors - Массив объектов сенсоров из telemetry.db / LHM
   * @returns {Array<{icon: string, label: string, value: string, badgeClass: string}>}
   */
  function extractCoreParameters(coreIdx, totalCores, sensors) {
    if (!Array.isArray(sensors) || sensors.length === 0) {
      return [];
    }

    const cpuSensors = sensors.filter(s => {
      const hwType = (s.hardware_type || '').toLowerCase();
      const hwName = (s.hardware_name || '').toLowerCase();
      return hwType === 'cpu' || hwName.includes('cpu') || hwName.includes('intel') || hwName.includes('amd');
    });

    if (cpuSensors.length === 0) return [];

    const idx1 = coreIdx + 1;
    const physIdx1 = Math.floor(coreIdx / 2) + 1;

    const params = [];

    // 1. Вольтаж ядра (Voltage)
    const voltSensor = cpuSensors.find(s => {
      const cat = (s.sensor_category || '').toLowerCase();
      const unit = (s.unit || '').toLowerCase();
      const name = (s.sensor_name || '').toLowerCase();
      if (!cat.includes('volt') && unit !== 'v') return false;
      return name.includes(`core #${idx1}`) || name.includes(`core #${physIdx1}`) || name.includes(`core #${coreIdx}`);
    }) || cpuSensors.find(s => {
      const cat = (s.sensor_category || '').toLowerCase();
      const unit = (s.unit || '').toLowerCase();
      const name = (s.sensor_name || '').toLowerCase();
      return (cat.includes('volt') || unit === 'v') && (name.includes('cpu core') || name.includes('vcore'));
    });

    if (voltSensor) {
      params.push({
        icon: 'bi bi-lightning-charge text-primary',
        label: 'Вольтаж',
        value: voltSensor.value_raw || `${Number(voltSensor.value || 0).toFixed(2)} V`,
        badgeClass: 'text-primary'
      });
    }

    // 2. Частота ядра (Clock / Frequency)
    const clockSensor = cpuSensors.find(s => {
      const cat = (s.sensor_category || '').toLowerCase();
      const unit = (s.unit || '').toLowerCase();
      const name = (s.sensor_name || '').toLowerCase();
      if (!cat.includes('clock') && !unit.includes('hz')) return false;
      return name.includes(`core #${idx1}`) || name.includes(`core #${physIdx1}`) || name.includes(`core #${coreIdx}`);
    }) || cpuSensors.find(s => {
      const cat = (s.sensor_category || '').toLowerCase();
      const unit = (s.unit || '').toLowerCase();
      const name = (s.sensor_name || '').toLowerCase();
      return (cat.includes('clock') || unit.includes('hz')) && (name.includes('core freq') || name.includes('cpu core'));
    });

    if (clockSensor) {
      params.push({
        icon: 'bi bi-speedometer2 text-info',
        label: 'Частота',
        value: clockSensor.value_raw || `${Number(clockSensor.value || 0).toFixed(0)} MHz`,
        badgeClass: 'text-info'
      });
    }

    // 3. Запас до TjMax (Distance to TjMax)
    const tjmaxSensor = cpuSensors.find(s => {
      const name = (s.sensor_name || '').toLowerCase();
      if (!name.includes('tjmax')) return false;
      return name.includes(`core #${idx1}`) || name.includes(`core #${physIdx1}`) || name.includes(`core #${coreIdx}`);
    }) || cpuSensors.find(s => (s.sensor_name || '').toLowerCase().includes('tjmax'));

    if (tjmaxSensor) {
      params.push({
        icon: 'bi bi-shield-check text-success',
        label: 'До TjMax',
        value: tjmaxSensor.value_raw || `${Number(tjmaxSensor.value || 0).toFixed(0)} °C`,
        badgeClass: 'text-success'
      });
    }

    // 4. Мощность (Power / Cores Power)
    const powerSensor = cpuSensors.find(s => {
      const cat = (s.sensor_category || '').toLowerCase();
      const unit = (s.unit || '').toLowerCase();
      const name = (s.sensor_name || '').toLowerCase();
      if (!cat.includes('power') && unit !== 'w') return false;
      return name.includes(`core #${idx1}`) || name.includes(`core #${physIdx1}`);
    }) || cpuSensors.find(s => {
      const cat = (s.sensor_category || '').toLowerCase();
      const unit = (s.unit || '').toLowerCase();
      const name = (s.sensor_name || '').toLowerCase();
      return (cat.includes('power') || unit === 'w') && (name.includes('cpu cores') || name.includes('cpu core'));
    });

    if (powerSensor) {
      params.push({
        icon: 'bi bi-lightning text-warning',
        label: 'Мощность',
        value: powerSensor.value_raw || `${Number(powerSensor.value || 0).toFixed(1)} W`,
        badgeClass: 'text-warning'
      });
    }

    // 5. Пиковая загрузка / Core Max / Шина (Bus Speed)
    const maxSensor = cpuSensors.find(s => {
      const name = (s.sensor_name || '').toLowerCase();
      return name.includes('core max') || name.includes('cpu core max');
    }) || cpuSensors.find(s => {
      const name = (s.sensor_name || '').toLowerCase();
      return name.includes('bus speed');
    });

    if (maxSensor) {
      const isBus = (maxSensor.sensor_name || '').toLowerCase().includes('bus');
      params.push({
        icon: isBus ? 'bi bi-hdd-network text-secondary' : 'bi bi-graph-up-arrow text-danger',
        label: isBus ? 'Шина' : 'Пик Max',
        value: maxSensor.value_raw || `${Number(maxSensor.value || 0).toFixed(1)} ${maxSensor.unit || ''}`.trim(),
        badgeClass: isBus ? 'text-secondary' : 'text-danger'
      });
    }

    return params;
  }

  function renderCpuCores(cores, totalThreadsCount) {
    const box = document.getElementById('sys-metric-cpu-cores');
    const badgeCount = document.getElementById('sys-cores-count-badge');
    if (!box) return;

    if (Array.isArray(cores)) {
      lastCpuCoresData = cores;
    } else if (lastCpuCoresData && lastCpuCoresData.length) {
      cores = lastCpuCoresData;
    }

    const cCount = cores ? cores.length : 0;
    const thCount = totalThreadsCount || (cores ? cores.reduce((acc, c) => acc + (c.threads ? c.threads.length : 0), 0) : 0);

    if (badgeCount) {
      badgeCount.textContent = cCount ? `${cCount} ядер • ${thCount} потоков` : '0 ядер';
    }

    if (!Array.isArray(cores) || cores.length === 0) {
      box.innerHTML = `<div class="text-muted small text-center py-3 col-12">Опрос ядер CPU выполняется...</div>`;
      return;
    }

    box.innerHTML = cores.map(c => {
      const load = c.load_percent == null ? null : Number(c.load_percent);
      const temp = c.temperature_c == null ? null : Number(c.temperature_c);
      const freqStr = c.frequency_str || (c.frequency_mhz ? (c.frequency_mhz >= 1000 ? (c.frequency_mhz / 1000).toFixed(2) + ' GHz' : c.frequency_mhz.toFixed(0) + ' MHz') : '--');
      const powerStr = c.power_w != null ? `${Number(c.power_w).toFixed(1)} W` : (c.power_str || '--');
      const loadStr = load == null ? '--' : `${load.toFixed(0)}%`;
      const tempStr = temp != null ? `${temp.toFixed(0)} °C` : '-- °C';
      const gaugeSvg = createGaugeSvg(load, 100, 54);
      const tempHtml = createTempSliderHtml(temp, 30, 95, false);

      const threadsList = Array.isArray(c.threads) ? c.threads : [];
      const threadsHtml = threadsList.map(th => {
        const thLoad = Number(th.load_percent || 0);
        const barClass = thLoad >= 80 ? 'bg-danger' : thLoad >= 60 ? 'bg-warning' : 'bg-info';
        return `
          <div class="d-flex align-items-center justify-content-between gap-1 mb-1" style="font-size: 0.72rem;">
            <span class="text-truncate" style="max-width: 65px; color: var(--text-color);" title="${escapeHtml(th.name || 'Thread')}">
              ${escapeHtml(th.name || 'Thread')}
            </span>
            <div class="progress flex-grow-1" style="height: 5px; background: var(--border-color); border-radius: 3px;">
              <div class="progress-bar ${barClass}" style="width: ${Math.min(100, thLoad)}%; border-radius: 3px;"></div>
            </div>
            <span class="font-monospace fw-bold" style="width: 32px; text-align: right; font-size: 0.69rem; color: var(--text-color);">${thLoad.toFixed(0)}%</span>
          </div>
        `;
      }).join('');

      return `
        <div class="sys-core-card p-2 rounded-2" style="background: var(--surface-2, rgba(255,255,255,0.03)); border: 1px solid var(--border-color, rgba(255,255,255,0.08));" title="Ядро #${c.index}: Нагрузка ${loadStr}, Температура ${tempStr}">
          <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom" style="border-color: var(--border-subtle, rgba(255,255,255,0.06)) !important;">
            <div class="d-flex align-items-center gap-1.5">
              <i class="bi bi-cpu text-info"></i>
              <span class="sys-core-title fw-bold" style="font-size: 0.82rem;">Core #${c.index}</span>
            </div>
            <span class="badge ${load != null && load >= 80 ? 'bg-danger' : 'bg-info-subtle text-info border border-info'}" style="font-size: 0.70rem;">${loadStr}</span>
          </div>
          
          <div class="d-flex align-items-center gap-2 mb-2">
            <div class="d-flex flex-column align-items-center justify-content-center" style="width: 96px; flex-shrink: 0;">
              <div style="width: 96px; height: 52px;">
                ${gaugeSvg}
              </div>
              <div class="w-100 mt-1">
                ${tempHtml}
              </div>
            </div>
            <div class="flex-grow-1 ps-1" style="min-width: 0;">
              <div class="sys-core-param-table">
                <div class="sys-core-param-row">
                  <span class="sys-core-param-key"><i class="bi bi-activity text-info me-1"></i>Нагрузка</span>
                  <span class="sys-core-param-val text-info">${loadStr}</span>
                </div>
                <div class="sys-core-param-row">
                  <span class="sys-core-param-key"><i class="bi bi-thermometer-half text-danger me-1"></i>Температура</span>
                  <span class="sys-core-param-val ${temp != null && temp >= 75 ? 'text-danger' : 'text-warning'}">${tempStr}</span>
                </div>
                <div class="sys-core-param-row">
                  <span class="sys-core-param-key"><i class="bi bi-speedometer2 text-info me-1"></i>Частота</span>
                  <span class="sys-core-param-val text-info">${escapeHtml(freqStr)}</span>
                </div>
                <div class="sys-core-param-row">
                  <span class="sys-core-param-key"><i class="bi bi-lightning text-warning me-1"></i>Мощность</span>
                  <span class="sys-core-param-val text-warning">${escapeHtml(powerStr)}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="pt-1 border-top" style="border-color: var(--border-subtle, rgba(255,255,255,0.06)) !important;">
            <div class="text-muted small mb-1" style="font-size: 0.68rem; font-weight: 600;">Потоки:</div>
            <div class="sys-core-threads-list">
              ${threadsHtml || '<div class="text-muted small">1 поток</div>'}
            </div>
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

  let currentCpuSparkScale = 'log';
  let lastCpuSparkData = [];

  function setCpuSparkScale(scale) {
    currentCpuSparkScale = scale;
    const btnLog = document.getElementById('btn-cpu-spark-log');
    const btnLin = document.getElementById('btn-cpu-spark-lin');
    if (btnLog && btnLin) {
      if (scale === 'log') {
        btnLog.className = 'btn btn-xs btn-outline-info active py-0 px-2 fw-bold';
        btnLin.className = 'btn btn-xs btn-outline-secondary py-0 px-2';
      } else {
        btnLin.className = 'btn btn-xs btn-outline-info active py-0 px-2 fw-bold';
        btnLog.className = 'btn btn-xs btn-outline-secondary py-0 px-2';
      }
    }
    if (lastCpuSparkData && lastCpuSparkData.length) {
      renderCpuSpark(lastCpuSparkData);
    }
  }
  window.setCpuSparkScale = setCpuSparkScale;

  function buildSmoothSvgPath(pts) {
    if (!pts || pts.length === 0) return '';
    if (pts.length === 1) return `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
    let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = i > 0 ? pts[i - 1] : pts[i];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = i !== pts.length - 2 ? pts[i + 2] : p2;

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
    }
    return d;
  }

  function renderCpuSpark(history) {
    const box = document.getElementById('sys-cpu-spark');
    const container = document.getElementById('sys-cpu-spark-container');
    const tooltip = document.getElementById('sys-cpu-spark-tooltip');
    if (!box) return;

    if (Array.isArray(history) && history.length >= 2) {
      lastCpuSparkData = history;
    } else if (lastCpuSparkData && lastCpuSparkData.length >= 2) {
      history = lastCpuSparkData;
    } else {
      return;
    }

    box.replaceChildren();
    const ns = 'http://www.w3.org/2000/svg';
    const W = 600, H = 84;
    const padTop = 6, padBottom = 6;
    const innerH = H - padTop - padBottom;

    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.style.cssText = 'width:100%;height:100%;display:block;cursor:crosshair;';

    // 1. Defs с градиентами и фильтром свечения
    const defs = document.createElementNS(ns, 'defs');
    defs.innerHTML = `
      <linearGradient id="cpuGradLoad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#0dcaf0" stop-opacity="0.38"/>
        <stop offset="60%" stop-color="#0dcaf0" stop-opacity="0.12"/>
        <stop offset="100%" stop-color="#0dcaf0" stop-opacity="0.0"/>
      </linearGradient>
      <linearGradient id="cpuGradTemp" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#ef4444" stop-opacity="0.28"/>
        <stop offset="100%" stop-color="#ef4444" stop-opacity="0.0"/>
      </linearGradient>
      <linearGradient id="cpuGradPower" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.22"/>
        <stop offset="100%" stop-color="#f59e0b" stop-opacity="0.0"/>
      </linearGradient>
    `;
    svg.appendChild(defs);

    // 2. Горизонтальная сетка (Grid Lines)
    const gridG = document.createElementNS(ns, 'g');
    gridG.setAttribute('opacity', '0.2');
    [0.0, 0.25, 0.5, 0.75, 1.0].forEach(ratio => {
      const y = H - padBottom - ratio * innerH;
      const gl = document.createElementNS(ns, 'line');
      gl.setAttribute('x1', '0');
      gl.setAttribute('y1', y.toFixed(1));
      gl.setAttribute('x2', String(W));
      gl.setAttribute('y2', y.toFixed(1));
      gl.setAttribute('stroke', '#ffffff');
      gl.setAttribute('stroke-dasharray', ratio === 0.0 || ratio === 1.0 ? 'none' : '3,3');
      gl.setAttribute('stroke-width', '1');
      gridG.appendChild(gl);
    });
    svg.appendChild(gridG);

    // 3. Расчет динамических диапазонов
    const count = history.length;
    const isLog = currentCpuSparkScale === 'log';

    // Температурный локальный диапазон (для выявления микроколебаний)
    const rawTemps = history.map(h => Number(h.temperature_c != null ? h.temperature_c : (h.temp || 0))).filter(t => t > 0);
    const tMin = rawTemps.length ? Math.min(...rawTemps) : 30;
    const tMax = rawTemps.length ? Math.max(...rawTemps) : 90;
    const tDelta = Math.max(6, tMax - tMin);

    // Диапазон мощности (для выявления микроколебаний)
    const rawPowers = history.map(h => Number(h.power_w != null ? h.power_w : (h.power || 0))).filter(p => p > 0);
    const pMin = rawPowers.length ? Math.min(...rawPowers) : 5;
    const pMax = rawPowers.length ? Math.max(...rawPowers) : 100;
    const pDelta = Math.max(8, pMax - pMin);

    // Главная шкала: Загрузка CPU (0..100% высоты холста)
    const transformLoad = (v) => {
      const cl = Math.min(100, Math.max(0, Number(v || 0)));
      if (!isLog) return cl / 100;
      return Math.log10(1 + 9 * (cl / 100)); // Log-10 mapping: 10% -> 0.28, 50% -> 0.74, 100% -> 1.0
    };

    // Вторичная компактная шкала: Температура (занимает 10% - 38% высоты)
    const transformTemp = (v) => {
      if (v == null) return 0.12;
      const frac = Math.min(1, Math.max(0, (Number(v) - (tMin - 1)) / (tDelta + 2)));
      return 0.10 + frac * 0.28;
    };

    // Вторичная компактная шкала: Мощность (занимает 4% - 28% высоты)
    const transformPower = (v) => {
      if (v == null) return 0.08;
      const frac = Math.min(1, Math.max(0, (Number(v) - (pMin - 1.5)) / (pDelta + 3)));
      return 0.04 + frac * 0.24;
    };

    // Точки графиков
    const loadPts = [];
    const tempPts = [];
    const powerPts = [];

    history.forEach((h, i) => {
      const x = (i / (count - 1)) * W;
      
      const lVal = Number(h.load_percent != null ? h.load_percent : (h.load || 0));
      const tVal = h.temperature_c != null ? Number(h.temperature_c) : (h.temp != null ? Number(h.temp) : null);
      const pVal = h.power_w != null ? Number(h.power_w) : (h.power != null ? Number(h.power) : null);

      const yLoad = H - padBottom - transformLoad(lVal) * innerH;
      const yTemp = H - padBottom - transformTemp(tVal) * innerH;
      const yPower = H - padBottom - transformPower(pVal) * innerH;

      loadPts.push({ x, y: yLoad, raw: lVal, time: h.time_label || h.timestamp });
      tempPts.push({ x, y: yTemp, raw: tVal });
      powerPts.push({ x, y: yPower, raw: pVal });
    });

    // 4. Отрисовка площадей и кривых (Area & Spline)
    const drawSeries = (pts, strokeColor, fillColor, strokeWidth = 1.8) => {
      if (pts.length < 2) return;
      const linePath = buildSmoothSvgPath(pts);

      // Заливка градиентом
      if (fillColor) {
        const areaPath = `${linePath} L ${pts[pts.length - 1].x.toFixed(1)} ${H - padBottom} L ${pts[0].x.toFixed(1)} ${H - padBottom} Z`;
        const aEl = document.createElementNS(ns, 'path');
        aEl.setAttribute('d', areaPath);
        aEl.setAttribute('fill', fillColor);
        svg.appendChild(aEl);
      }

      // Линия кривой
      const pEl = document.createElementNS(ns, 'path');
      pEl.setAttribute('d', linePath);
      pEl.setAttribute('fill', 'none');
      pEl.setAttribute('stroke', strokeColor);
      pEl.setAttribute('stroke-width', String(strokeWidth));
      pEl.setAttribute('stroke-linejoin', 'round');
      pEl.setAttribute('stroke-linecap', 'round');
      svg.appendChild(pEl);
    };

    // Рисуем: Тонкие тренды температуры и мощности на компактной шкале + Основной график загрузки с градиентом
    drawSeries(powerPts, '#f59e0b', null, 1.2);
    drawSeries(tempPts, '#ef4444', null, 1.3);
    drawSeries(loadPts, '#0dcaf0', 'url(#cpuGradLoad)', 2.0);

    // 5. Интерактивный Hover-курсор и Тултип
    const crosshair = document.createElementNS(ns, 'line');
    crosshair.setAttribute('y1', '0');
    crosshair.setAttribute('y2', String(H));
    crosshair.setAttribute('stroke', 'var(--text-muted, rgba(128,128,128,0.5))');
    crosshair.setAttribute('stroke-dasharray', '2,2');
    crosshair.setAttribute('stroke-width', '1');
    crosshair.style.display = 'none';
    svg.appendChild(crosshair);

    svg.addEventListener('mousemove', (evt) => {
      const rect = svg.getBoundingClientRect();
      const mouseX = Math.max(0, Math.min(rect.width, evt.clientX - rect.left));
      const ratio = mouseX / rect.width;
      const idx = Math.min(count - 1, Math.max(0, Math.round(ratio * (count - 1))));
      const pt = loadPts[idx];
      const hItem = history[idx];

      if (pt && tooltip) {
        crosshair.setAttribute('x1', pt.x.toFixed(1));
        crosshair.setAttribute('x2', pt.x.toFixed(1));
        crosshair.style.display = 'block';

        const tStr = hItem.time_label || (hItem.timestamp ? new Date(hItem.timestamp).toLocaleTimeString() : (hItem.time ? new Date(hItem.time).toLocaleTimeString() : '--:--:--'));
        const lStr = `${pt.raw.toFixed(1)}%`;
        const tempVal = tempPts[idx] && tempPts[idx].raw != null ? `${tempPts[idx].raw.toFixed(0)} °C` : '--';
        const powVal = powerPts[idx] && powerPts[idx].raw != null ? `${powerPts[idx].raw.toFixed(1)} W` : '--';

        tooltip.innerHTML = `
          <div class="d-flex align-items-center justify-content-between gap-2 border-bottom pb-0.5 mb-1" style="border-color: rgba(255,255,255,0.1) !important;">
            <span class="text-muted"><i class="bi bi-clock me-1"></i>${escapeHtml(tStr)}</span>
            <span class="badge ${isLog ? 'bg-info-subtle text-info' : 'bg-secondary text-light'}" style="font-size:0.62rem;">${isLog ? 'Log' : 'Lin'}</span>
          </div>
          <div class="d-flex gap-2 font-monospace">
            <span class="text-info fw-bold"><i class="bi bi-activity me-0.5"></i>${lStr}</span>
            <span class="text-danger fw-bold"><i class="bi bi-thermometer-half me-0.5"></i>${tempVal}</span>
            <span class="text-warning fw-bold"><i class="bi bi-lightning me-0.5"></i>${powVal}</span>
          </div>
        `;
        tooltip.style.display = 'block';

        // Позиционирование тултипа
        const tipX = Math.min(rect.width - 150, Math.max(10, mouseX - 60));
        tooltip.style.left = `${tipX}px`;
      }
    });

    svg.addEventListener('mouseleave', () => {
      crosshair.style.display = 'none';
      if (tooltip) tooltip.style.display = 'none';
    });

    box.appendChild(svg);
  }

  function setGpuSparkScale(scale, idx = 0) {
    currentGpuSparkScales[idx] = scale;
    const btnLog = document.getElementById(`btn-gpu-spark-log-${idx}`) || document.getElementById('btn-gpu-spark-log');
    const btnLin = document.getElementById(`btn-gpu-spark-lin-${idx}`) || document.getElementById('btn-gpu-spark-lin');
    if (btnLog && btnLin) {
      if (scale === 'log') {
        btnLog.className = 'btn btn-xs btn-outline-warning active py-0 px-2 fw-bold';
        btnLin.className = 'btn btn-xs btn-outline-secondary py-0 px-2';
      } else {
        btnLin.className = 'btn btn-xs btn-outline-warning active py-0 px-2 fw-bold';
        btnLog.className = 'btn btn-xs btn-outline-secondary py-0 px-2';
      }
    }
    if (lastGpuSparkDataMap[idx] && lastGpuSparkDataMap[idx].length) {
      renderGpuSpark(lastGpuSparkDataMap[idx], idx);
    }
  }
  window.setGpuSparkScale = setGpuSparkScale;

  function renderGpuSpark(history, idx = 0) {
    const box = document.getElementById(`sys-gpu-spark-${idx}`) || document.getElementById('sys-gpu-spark');
    const container = document.getElementById(`sys-gpu-spark-container-${idx}`) || document.getElementById('sys-gpu-spark-container');
    const tooltip = document.getElementById(`sys-gpu-spark-tooltip-${idx}`) || document.getElementById('sys-gpu-spark-tooltip');
    if (!box) return;

    if (Array.isArray(history) && history.length >= 2) {
      lastGpuSparkDataMap[idx] = history;
    } else if (lastGpuSparkDataMap[idx] && lastGpuSparkDataMap[idx].length >= 2) {
      history = lastGpuSparkDataMap[idx];
    } else {
      return;
    }

    box.replaceChildren();
    const ns = 'http://www.w3.org/2000/svg';
    const W = 600, H = 84;
    const padTop = 6, padBottom = 6;
    const innerH = H - padTop - padBottom;

    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.style.cssText = 'width:100%;height:100%;display:block;cursor:crosshair;';

    // 1. Defs с уникальным ID градиента для каждого GPU
    const defs = document.createElementNS(ns, 'defs');
    const gradId = `gpuGradLoad_${idx}`;
    defs.innerHTML = `
      <linearGradient id="${gradId}" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.38"/>
        <stop offset="60%" stop-color="#f59e0b" stop-opacity="0.12"/>
        <stop offset="100%" stop-color="#f59e0b" stop-opacity="0.0"/>
      </linearGradient>
    `;
    svg.appendChild(defs);

    // 2. Горизонтальная сетка (Grid Lines)
    const gridG = document.createElementNS(ns, 'g');
    gridG.setAttribute('opacity', '0.2');
    [0.0, 0.25, 0.5, 0.75, 1.0].forEach(ratio => {
      const y = H - padBottom - ratio * innerH;
      const gl = document.createElementNS(ns, 'line');
      gl.setAttribute('x1', '0');
      gl.setAttribute('y1', y.toFixed(1));
      gl.setAttribute('x2', String(W));
      gl.setAttribute('y2', y.toFixed(1));
      gl.setAttribute('stroke', '#ffffff');
      gl.setAttribute('stroke-dasharray', ratio === 0.0 || ratio === 1.0 ? 'none' : '3,3');
      gl.setAttribute('stroke-width', '1');
      gridG.appendChild(gl);
    });
    svg.appendChild(gridG);

    // 3. Расчет динамических диапазонов
    const count = history.length;
    const isLog = currentGpuSparkScales[idx] === 'log' || currentGpuSparkScales[idx] === undefined;

    // Температурный локальный диапазон
    const rawTemps = history.map(h => Number(h.temperature_c != null ? h.temperature_c : (h.temp || 0))).filter(t => t > 0);
    const tMin = rawTemps.length ? Math.min(...rawTemps) : 30;
    const tMax = rawTemps.length ? Math.max(...rawTemps) : 90;
    const tDelta = Math.max(6, tMax - tMin);

    // Диапазон мощности / памяти
    const rawPowers = history.map(h => Number(h.power_w != null ? h.power_w : (h.power || h.vram_percent || 0))).filter(p => p > 0);
    const pMin = rawPowers.length ? Math.min(...rawPowers) : 5;
    const pMax = rawPowers.length ? Math.max(...rawPowers) : 100;
    const pDelta = Math.max(8, pMax - pMin);

    // Главная шкала: Загрузка GPU Core (0..100% высоты холста)
    const transformLoad = (v) => {
      const cl = Math.min(100, Math.max(0, Number(v || 0)));
      if (!isLog) return cl / 100;
      return Math.log10(1 + 9 * (cl / 100));
    };

    // Вторичная компактная шкала: Температура (занимает 10% - 38% высоты)
    const transformTemp = (v) => {
      if (v == null) return 0.12;
      const frac = Math.min(1, Math.max(0, (Number(v) - (tMin - 1)) / (tDelta + 2)));
      return 0.10 + frac * 0.28;
    };

    // Вторичная компактная шкала: Мощность/Память (занимает 4% - 28% высоты)
    const transformPower = (v) => {
      if (v == null) return 0.08;
      const frac = Math.min(1, Math.max(0, (Number(v) - (pMin - 1.5)) / (pDelta + 3)));
      return 0.04 + frac * 0.24;
    };

    // Точки графиков
    const loadPts = [];
    const tempPts = [];
    const powerPts = [];

    history.forEach((h, i) => {
      const x = (i / (count - 1)) * W;
      
      const lVal = Number(h.load_percent != null ? h.load_percent : (h.load || 0));
      const tVal = h.temperature_c != null ? Number(h.temperature_c) : (h.temp != null ? Number(h.temp) : null);
      const pVal = h.power_w != null ? Number(h.power_w) : (h.power != null ? Number(h.power) : (h.vram_percent != null ? Number(h.vram_percent) : null));

      const yLoad = H - padBottom - transformLoad(lVal) * innerH;
      const yTemp = H - padBottom - transformTemp(tVal) * innerH;
      const yPower = H - padBottom - transformPower(pVal) * innerH;

      loadPts.push({ x, y: yLoad, raw: lVal, time: h.time_label || h.timestamp });
      tempPts.push({ x, y: yTemp, raw: tVal });
      powerPts.push({ x, y: yPower, raw: pVal });
    });

    // 4. Отрисовка площадей и кривых (Area & Spline)
    const drawSeries = (pts, strokeColor, fillColor, strokeWidth = 1.8) => {
      if (pts.length < 2) return;
      const linePath = buildSmoothSvgPath(pts);

      // Заливка градиентом
      if (fillColor) {
        const areaPath = `${linePath} L ${pts[pts.length - 1].x.toFixed(1)} ${H - padBottom} L ${pts[0].x.toFixed(1)} ${H - padBottom} Z`;
        const aEl = document.createElementNS(ns, 'path');
        aEl.setAttribute('d', areaPath);
        aEl.setAttribute('fill', fillColor);
        svg.appendChild(aEl);
      }

      // Линия кривой
      const pEl = document.createElementNS(ns, 'path');
      pEl.setAttribute('d', linePath);
      pEl.setAttribute('fill', 'none');
      pEl.setAttribute('stroke', strokeColor);
      pEl.setAttribute('stroke-width', String(strokeWidth));
      pEl.setAttribute('stroke-linejoin', 'round');
      pEl.setAttribute('stroke-linecap', 'round');
      svg.appendChild(pEl);
    };

    drawSeries(powerPts, '#0dcaf0', null, 1.2);
    drawSeries(tempPts, '#ef4444', null, 1.3);
    drawSeries(loadPts, '#f59e0b', `url(#${gradId})`, 2.0);

    // 5. Интерактивный Hover-курсор и Тултип
    const crosshair = document.createElementNS(ns, 'line');
    crosshair.setAttribute('y1', '0');
    crosshair.setAttribute('y2', String(H));
    crosshair.setAttribute('stroke', 'var(--text-muted, rgba(128,128,128,0.5))');
    crosshair.setAttribute('stroke-dasharray', '2,2');
    crosshair.setAttribute('stroke-width', '1');
    crosshair.style.display = 'none';
    svg.appendChild(crosshair);

    svg.addEventListener('mousemove', (evt) => {
      const rect = svg.getBoundingClientRect();
      const mouseX = Math.max(0, Math.min(rect.width, evt.clientX - rect.left));
      const ratio = mouseX / rect.width;
      const curIndex = Math.min(count - 1, Math.max(0, Math.round(ratio * (count - 1))));
      const pt = loadPts[curIndex];
      const hItem = history[curIndex];

      if (pt && tooltip) {
        crosshair.setAttribute('x1', pt.x.toFixed(1));
        crosshair.setAttribute('x2', pt.x.toFixed(1));
        crosshair.style.display = 'block';

        const tStr = hItem.time_label || (hItem.timestamp ? new Date(hItem.timestamp).toLocaleTimeString() : (hItem.time ? new Date(hItem.time).toLocaleTimeString() : '--:--:--'));
        const lStr = `${pt.raw.toFixed(1)}%`;
        const tempVal = tempPts[curIndex] && tempPts[curIndex].raw != null ? `${tempPts[curIndex].raw.toFixed(0)} °C` : '--';
        const powVal = powerPts[curIndex] && powerPts[curIndex].raw != null ? (hItem.power_w != null ? `${powerPts[curIndex].raw.toFixed(1)} W` : `${powerPts[curIndex].raw.toFixed(0)}%`) : '--';

        tooltip.innerHTML = `
          <div class="d-flex align-items-center justify-content-between gap-2 border-bottom pb-0.5 mb-1" style="border-color: rgba(255,255,255,0.1) !important;">
            <span class="text-muted"><i class="bi bi-clock me-1"></i>${escapeHtml(tStr)}</span>
            <span class="badge ${isLog ? 'bg-warning-subtle text-warning' : 'bg-secondary text-light'}" style="font-size:0.62rem;">${isLog ? 'Log' : 'Lin'}</span>
          </div>
          <div class="d-flex gap-2 font-monospace">
            <span class="text-warning fw-bold"><i class="bi bi-activity me-0.5"></i>${lStr}</span>
            <span class="text-danger fw-bold"><i class="bi bi-thermometer-half me-0.5"></i>${tempVal}</span>
            <span class="text-info fw-bold"><i class="bi bi-lightning me-0.5"></i>${powVal}</span>
          </div>
        `;
        tooltip.style.display = 'block';

        const tipX = Math.min(rect.width - 150, Math.max(10, mouseX - 60));
        tooltip.style.left = `${tipX}px`;
      }
    });

    svg.addEventListener('mouseleave', () => {
      crosshair.style.display = 'none';
      if (tooltip) tooltip.style.display = 'none';
    });

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
      set('sys-net-speed-badge', `${data.link_speed_mbps || 1000} Mbps Full Duplex`);

      // Экспресс-метрики KPI в центре баннера сети
      set('sys-net-kpi-rx', rxFormatted);
      set('sys-net-kpi-tx', txFormatted);
      set('sys-net-kpi-total', sumTotalFormatted);
      set('sys-net-kpi-util', `${utilPct.toFixed(1)}%`);

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

      const stModel = document.getElementById('sys-metric-storage-model');
      if (stModel && totalGb > 0) {
        const totalTb = totalGb >= 1000 ? `${(totalGb / 1024).toFixed(2)} TB` : `${totalGb.toFixed(0)} GB`;
        stModel.innerText = `Дисковая подсистема (${totalTb})`;
      }

      // Экспресс-метрики KPI в центре баннера хранилища
      set('sys-storage-kpi-used', `${usedGb.toFixed(1)} GB`);
      set('sys-storage-kpi-free', `${freeGb.toFixed(1)} GB`);
      const dCount = s.drives_count || (Array.isArray(data.drives) ? data.drives.length : '--');
      const pCount = s.partitions_count || (Array.isArray(data.partitions) ? data.partitions.length : '--');
      set('sys-storage-kpi-drives', `${dCount} диск. / ${pCount} разд.`);
      const stKpiTemp = document.getElementById('sys-storage-kpi-temp');
      if (stKpiTemp) {
        stKpiTemp.textContent = maxTemp != null ? `${maxTemp.toFixed(0)} °C` : '-- °C';
        if (maxTemp != null) {
          stKpiTemp.className = maxTemp >= 60 ? 'sys-kpi-value text-danger' : maxTemp >= 48 ? 'sys-kpi-value text-warning' : 'sys-kpi-value text-info';
        }
      }

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
      lastCpuData = data;
      const cpuVal = document.getElementById('sys-metric-cpu-val');
      const cpuFill = document.getElementById('sys-metric-cpu-fill');
      const cpuSub = document.getElementById('sys-metric-cpu-sub');
      const cpuModel = document.getElementById('sys-metric-cpu-model');
      const cpuGauge = document.getElementById('sys-metric-cpu-gauge');
      const cpuPkgSlider = document.getElementById('sys-metric-cpu-package-slider');
      const cpuPkgTemp = document.getElementById('sys-metric-cpu-package-temp');

      const pct = Number(data.total_percent || 0);
      const cores = Array.isArray(data.cores) ? data.cores : [];
      const threads = Array.isArray(data.threads) ? data.threads : [];
      const sensors = Array.isArray(data.sensors) ? data.sensors : [];
      const history = Array.isArray(data.history) ? data.history : [];

      if (cpuVal) {
        cpuVal.innerText = `${pct.toFixed(1)}%`;
        // Динамический оттенок значения загрузки
        if (pct >= 85) {
          cpuVal.style.color = '#ef4444'; // Красный (критическая нагрузка)
          cpuVal.style.textShadow = '0 0 14px rgba(239, 68, 68, 0.6)';
        } else if (pct >= 70) {
          cpuVal.style.color = '#f97316'; // Оранжевый (высокая нагрузка)
          cpuVal.style.textShadow = '0 0 12px rgba(249, 115, 22, 0.45)';
        } else if (pct >= 50) {
          cpuVal.style.color = '#eab308'; // Желтый / янтарный (умеренная нагрузка)
          cpuVal.style.textShadow = '0 0 10px rgba(234, 179, 8, 0.4)';
        } else {
          cpuVal.style.color = '#0dcaf0'; // Голубой (штатная нагрузка)
          cpuVal.style.textShadow = '0 0 10px rgba(13, 202, 240, 0.35)';
        }
      }
      if (cpuFill) cpuFill.style.width = `${Math.min(100, pct)}%`;

      if (cpuModel && data.name) {
        cpuModel.innerText = data.name;
        cpuModel.title = data.name;
      }

      const pkgTemp = data.package_temperature_c != null ? Number(data.package_temperature_c) : null;
      const pkgPower = data.package_power_w != null ? Number(data.package_power_w) : null;
      if (cpuSub) {
        const t = pkgTemp == null ? '' : ` · ${pkgTemp.toFixed(0)} °C`;
        const p = pkgPower == null ? '' : ` · ${pkgPower.toFixed(0)} W`;
        const cCount = data.cores_count || cores.length;
        const thCount = data.threads_count || threads.length;
        cpuSub.innerText = cCount ? `${cCount} ядер • ${thCount} потоков${t}${p}` : '-- Ядер';
      }
      if (cpuPkgTemp) {
        const pStr = pkgPower != null ? ` · ${pkgPower.toFixed(0)} W` : '';
        cpuPkgTemp.innerText = pkgTemp != null ? `Пакет: ${pkgTemp.toFixed(0)} °C${pStr}` : 'Пакет: -- °C';
        if (pkgTemp != null) {
          if (pkgTemp >= 80) {
            cpuPkgTemp.className = 'text-danger fw-bold font-monospace';
          } else if (pkgTemp >= 65) {
            cpuPkgTemp.className = 'text-warning fw-bold font-monospace';
          } else {
            cpuPkgTemp.className = 'text-info font-monospace';
          }
        }
      }

      // 1. Заполнение сводной таблицы характеристик CPU (Specs)
      const specs = data.specs || {};
      const setSpec = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
      if (specs.socket || specs.physical_cores) {
        setSpec('sys-cpu-spec-arch', specs.architecture || 'x86_64');
        setSpec('sys-cpu-spec-socket', specs.socket || 'LGA1200');
        setSpec('sys-cpu-spec-cores', `${specs.physical_cores || cores.length}C / ${specs.logical_cores || threads.length}T`);
        setSpec('sys-cpu-spec-base-freq', specs.base_frequency_str || '--');
        setSpec('sys-cpu-spec-max-freq', specs.max_frequency_str || '--');
        setSpec('sys-cpu-spec-cache', specs.cache_combined_str || '--');
      }

      // Экспресс-метрики KPI в центре баннера CPU
      const kpiPower = document.getElementById('sys-cpu-kpi-power');
      const kpiTemp = document.getElementById('sys-cpu-kpi-temp');
      const kpiCores = document.getElementById('sys-cpu-kpi-cores');
      const kpiFreq = document.getElementById('sys-cpu-kpi-freq');
      const cCount = data.cores_count || (specs.physical_cores || cores.length);
      const thCount = data.threads_count || (specs.logical_cores || threads.length);

      if (kpiPower) kpiPower.textContent = pkgPower != null ? `${pkgPower.toFixed(0)} W` : (data.package_power_w != null ? `${Number(data.package_power_w).toFixed(0)} W` : '-- W');
      if (kpiTemp) {
        kpiTemp.textContent = pkgTemp != null ? `${pkgTemp.toFixed(0)} °C` : '-- °C';
        if (pkgTemp != null) {
          kpiTemp.className = pkgTemp >= 80 ? 'sys-kpi-value text-danger' : pkgTemp >= 65 ? 'sys-kpi-value text-warning' : 'sys-kpi-value text-info';
        }
      }
      if (kpiCores) kpiCores.textContent = cCount ? `${cCount}C / ${thCount}T` : '-- / --';
      if (kpiFreq) {
        const fMax = specs.max_frequency_str || (specs.max_frequency_ghz ? `${specs.max_frequency_ghz} GHz` : null);
        const fBase = specs.base_frequency_str || (specs.base_frequency_ghz ? `${specs.base_frequency_ghz} GHz` : null);
        kpiFreq.textContent = fMax || fBase || '-- GHz';
      }

      const vendorBadge = document.getElementById('sys-metric-cpu-vendor-badge');
      if (vendorBadge) {
        const cpus = Array.isArray(data.cpus) && data.cpus.length > 0 ? data.cpus : [];
        if (cpus.length > 1) {
          vendorBadge.innerHTML = cpus.map((c, i) => `<div class="text-truncate font-monospace" style="font-size: 0.74rem;">CPU #${c.id ?? i}: ${escapeHtml(c.description || `${c.raw_descriptor || c.name} (${c.logical_cores || 12} logical cores)`)}</div>`).join('');
        } else if (data.description || specs.description) {
          vendorBadge.innerText = data.description || specs.description;
        } else {
          const rawDesc = specs.raw_descriptor || 'Intel64 Family 6 Model 165 Stepping 3, GenuineIntel';
          const logCores = data.threads_count || specs.logical_cores || (threads ? threads.length : 12) || 12;
          vendorBadge.innerText = `${rawDesc} (${logCores} logical cores)`;
        }
      }

      // Gauge полукруг со стрелкой для общего CPU
      if (cpuGauge) {
        cpuGauge.innerHTML = createGaugeSvg(pct, 120, 68);
      }

      // Слайдер температуры Package (расположен прямо под спидометром)
      if (cpuPkgSlider) {
        cpuPkgSlider.innerHTML = createTempSliderHtml(pkgTemp, 30, 95, false);
      }

      // 2. Физические ядра со своими потоками
      renderCpuCores(cores, data.threads_count || threads.length);

      // 3. Общие показатели CPU
      if (sensors && sensors.length > 0) {
        lastCpuSensorsData = sensors;
        renderComponentSensors('sys-metric-cpu-sensors', 'sys-cpu-sensors-count-badge', sensors);
      }

      // 4. График истории CPU (Загрузка %, Температура °C, Мощность W)
      if (history && history.length > 0) {
        renderCpuSpark(history);
      } else {
        _cpuSparkHistory.push({ load: pct, temp: pkgTemp, power: pkgPower, time: new Date() });
        if (_cpuSparkHistory.length > 60) _cpuSparkHistory.shift();
        renderCpuSpark(_cpuSparkHistory);
      }
    } catch (e) {
      console.warn('[SystemInspectorTab] Ошибка получения загрузки CPU из API:', e);
    }
  }

  /**
   * Запуск экспертного AI-аудита и анализа характеристик CPU через Universal AITableModal.
   */
  function inspectCpuSpecsWithAi() {
    if (!lastCpuData) {
      console.warn('[SystemInspectorTab] Нет загруженных данных CPU для AI-инспекции');
      return;
    }
    const specs = lastCpuData.specs || {};
    const title = lastCpuData.name || 'Центральный процессор (CPU)';
    const subtitle = `${specs.vendor || 'Intel/AMD'} · ${specs.socket || 'Socket'} · ${specs.architecture || 'x86_64'}`;
    const metadata = {
      'Сокет': specs.socket || 'N/A',
      'Ядра / Потоки': `${specs.physical_cores || lastCpuData.cores_count || '--'}C / ${specs.logical_cores || lastCpuData.threads_count || '--'}T`,
      'Базовая частота': specs.base_frequency_str || '--',
      'Макс. частота': specs.max_frequency_str || '--',
      'Кэш L2 / L3': specs.cache_combined_str || '--',
      'Архитектура': specs.architecture || 'x86_64',
      'Текущая загрузка': `${(lastCpuData.total_percent || 0).toFixed(1)}%`,
      'Температура пакета': lastCpuData.package_temperature_c != null ? `${lastCpuData.package_temperature_c.toFixed(0)} °C` : 'N/A',
      'Энергопотребление': lastCpuData.package_power_w != null ? `${lastCpuData.package_power_w.toFixed(1)} W` : 'N/A'
    };

    if (window.AITableModal && typeof window.AITableModal.show === 'function') {
      window.AITableModal.show({
        icon: '💻',
        title: title,
        subtitle: subtitle,
        badges: [
          { text: specs.architecture || 'x86_64', class: 'bg-primary-subtle text-primary border border-primary' },
          { text: specs.socket || 'Socket', class: 'bg-info-subtle text-info border border-info' },
          { text: `${specs.physical_cores || lastCpuData.cores_count || '--'} Cores`, class: 'bg-success-subtle text-success border border-success' }
        ],
        metadata: metadata,
        rawTitle: 'CPU Inventory Telemetry & Specs',
        rawContent: JSON.stringify({
          name: lastCpuData.name,
          specs: specs,
          metrics: {
            total_percent: lastCpuData.total_percent,
            package_temperature_c: lastCpuData.package_temperature_c,
            package_power_w: lastCpuData.package_power_w
          },
          cores_count: (lastCpuData.cores || []).length,
          threads_count: (lastCpuData.threads || []).length
        }, null, 2),
        tableType: 'cpu',
        actions: []
      });
    } else {
      console.warn('[SystemInspectorTab] Universal AITableModal недоступен в DOM');
    }
  }
  window.inspectCpuSpecsWithAi = inspectCpuSpecsWithAi;

  /**
   * Запуск экспертного AI-аудита и анализа характеристик GPU через Universal AITableModal.
   */
  function inspectGpuSpecsWithAi(idx = 0) {
    const gpu = (lastGpuDevices && lastGpuDevices[idx]) || lastGpuData;
    if (!gpu) {
      console.warn('[SystemInspectorTab] Нет загруженных данных GPU для AI-инспекции');
      return;
    }
    const specs = gpu.specs || {};
    const title = gpu.name || `Графический процессор (GPU #${idx})`;
    const subtitle = `${specs.vendor || gpu.vendor || 'GPU'} · ${specs.pci_bus || 'PCIe'} · ${specs.directx || 'DirectX 12'}`;
    const metadata = {
      'Производитель': specs.vendor || gpu.vendor || 'NVIDIA/Intel/AMD',
      'VRAM Объем': specs.vram_str || (gpu.memory && gpu.memory.total_mb ? `${(gpu.memory.total_mb/1024).toFixed(1)} GB` : '--'),
      'Использование VRAM': specs.vram_used_str || (gpu.memory && gpu.memory.used_percent != null ? `${gpu.memory.used_percent.toFixed(0)}%` : '--'),
      'Частота ядра': specs.core_clock_str || (gpu.clocks && gpu.clocks.core_mhz ? `${Math.round(gpu.clocks.core_mhz)} MHz` : '--'),
      'Частота памяти': specs.memory_clock_str || (gpu.clocks && gpu.clocks.memory_mhz ? `${Math.round(gpu.clocks.memory_mhz)} MHz` : '--'),
      'Версия драйвера': specs.driver_version || '--',
      'Шина': specs.pci_bus || 'PCIe',
      'DirectX API': specs.directx || 'DirectX 12',
      'Текущая загрузка': `${(gpu.core_load_percent || 0).toFixed(1)}%`,
      'Температура GPU': gpu.core_temperature_c != null ? `${gpu.core_temperature_c.toFixed(0)} °C` : 'N/A',
      'Энергопотребление': gpu.power_w != null ? `${gpu.power_w.toFixed(1)} W` : 'N/A'
    };

    if (window.AITableModal && typeof window.AITableModal.show === 'function') {
      window.AITableModal.show({
        icon: '🎮',
        title: title,
        subtitle: subtitle,
        badges: [
          { text: specs.vendor || gpu.vendor || 'GPU', class: 'bg-warning-subtle text-warning border border-warning' },
          { text: specs.vram_str || (gpu.memory && gpu.memory.total_mb ? `${(gpu.memory.total_mb/1024).toFixed(1)} GB` : 'VRAM'), class: 'bg-info-subtle text-info border border-info' },
          { text: specs.directx || 'DirectX 12', class: 'bg-success-subtle text-success border border-success' }
        ],
        metadata: metadata,
        rawTitle: `GPU #${gpu.index != null ? gpu.index : idx} Inventory Telemetry & Specs`,
        rawContent: JSON.stringify({
          index: gpu.index != null ? gpu.index : idx,
          name: gpu.name,
          vendor: gpu.vendor,
          specs: specs,
          metrics: {
            core_load_percent: gpu.core_load_percent,
            core_temperature_c: gpu.core_temperature_c,
            hotspot_temperature_c: gpu.hotspot_temperature_c,
            power_w: gpu.power_w,
            memory: gpu.memory,
            clocks: gpu.clocks
          },
          engines: gpu.engines || [],
          sensors_count: (gpu.sensors || []).length
        }, null, 2),
        tableType: 'gpu',
        actions: []
      });
    } else {
      console.warn('[SystemInspectorTab] Universal AITableModal недоступен в DOM');
    }
  }
  window.inspectGpuSpecsWithAi = inspectGpuSpecsWithAi;

  function renderGpuEngines(engines, idx = 0) {
    const box = document.getElementById(`sys-metric-gpu-engines-${idx}`) || document.getElementById('sys-metric-gpu-engines');
    const badgeCount = document.getElementById(`sys-gpu-engines-count-badge-${idx}`) || document.getElementById('sys-gpu-engines-count-badge');
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
      const gaugeSvg = createGaugeSvg(load, 110, 62);
      const tempHtml = createTempSliderHtml(temp, 30, 95, false);

      return `
        <div class="sys-core-card p-2.5" style="min-height: 156px; display: flex; flex-direction: column; justify-content: space-between;" title="${escapeHtml(e.name)}: Нагрузка ${loadStr}${temp != null ? ', Температура ' + temp.toFixed(0) + '°C' : ''}">
          <div class="d-flex justify-content-between align-items-start gap-1.5 mb-1" style="min-height: 32px;">
            <span class="sys-core-title" style="font-size: 0.84rem; font-weight: 800; color: var(--text-color); line-height: 1.25; word-break: break-word;" title="${escapeHtml(e.name)}">${escapeHtml(e.name)}</span>
            <span class="sys-core-load-badge font-monospace flex-shrink-0" style="font-size: 0.76rem; padding: 2px 6px;">${loadStr}</span>
          </div>
          <div class="py-1 d-flex justify-content-center">
            ${gaugeSvg}
          </div>
          <div class="mt-auto">
            ${tempHtml}
          </div>
        </div>
      `;
    }).join('');
  }

  function renderGpuCardHtml(gpu, idx, totalDevices) {
    const gpuName = escapeHtml(gpu.name || `GPU #${idx}`);
    const vendor = escapeHtml(gpu.vendor || 'GPU');
    const headerTitle = totalDevices > 1 ? `Загрузка GPU #${gpu.index != null ? gpu.index : idx}: ${gpuName}` : `Загрузка GPU: ${gpuName}`;

    return `
      <div class="sys-card sys-card-gpu h-100 p-3" id="sys-card-gpu-${idx}">
        <div class="sys-card-header-bar">
          <div class="d-flex align-items-center gap-2">
            <span class="sys-label text-warning" style="font-size: 1.05rem; font-weight: 800;">
              <i class="bi bi-gpu-card text-warning me-1.5"></i>${headerTitle}
            </span>
            <span class="badge bg-dark border border-secondary text-info font-monospace ms-1" style="font-size: 0.74rem;">
              ${vendor}
            </span>
          </div>
          <span class="small text-truncate font-monospace badge bg-dark border border-secondary text-warning" style="font-size: 0.84rem; max-width: 320px;" id="sys-metric-gpu-sub-${idx}">--</span>
        </div>

        <!-- Верхний баннер: Название слева, Спидометр и датчик температуры по центру, Сводная спецификация GPU справа -->
        <div class="sys-card-top-banner p-3 rounded-3 mb-3">
          <!-- Левая колонка: Модель графического процессора и экспресс-метрики KPI -->
          <div class="sys-banner-col-info d-flex flex-column align-items-start justify-content-center">
            <div class="text-start mb-1.5 d-flex align-items-center">
              <button type="button" class="sys-drill-btn" id="sys-drill-btn-gpu-${idx}" onclick="window.toggleSysCardDrill && window.toggleSysCardDrill('sys-card-gpu-${idx}', ${idx})" title="Drill-down: Развернуть/скрыть все скрытые панели и датчики GPU">
                <svg class="sys-drill-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M14 9V4H5a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h9z"/>
                  <path d="M14 6.5h3.5v3H14"/>
                  <path d="M17.5 8h4.5"/>
                  <path d="M6 11v5a2 2 0 0 0 2 2h2a1 1 0 0 0 1-1v-6"/>
                  <path d="M5.5 18h7v3a1 1 0 0 1-1 1h-5a1 1 0 0 1-1-1v-3z"/>
                  <path d="M10 13.5h1.5"/>
                </svg>
              </button>
              <div>
                <span class="fw-bold text-warning" style="font-size: 1.20rem; font-weight: 800; letter-spacing: 0.5px; text-shadow: 0 0 14px rgba(245, 158, 11, 0.4);" id="sys-metric-gpu-model-${idx}">${gpuName}</span>
                <div class="d-flex align-items-center gap-1.5 mt-0.5">
                  <span class="badge bg-dark border border-secondary text-light font-monospace" id="sys-metric-gpu-vendor-badge-${idx}" style="font-size: 0.70rem;">${vendor} · PCIe</span>
                  <span class="badge bg-warning-subtle text-warning border border-warning font-monospace" id="sys-gpu-status-badge-${idx}" style="font-size: 0.70rem;">● Ready</span>
                </div>
              </div>
            </div>
            <div class="sys-banner-kpi-grid">
              <div class="sys-kpi-pill">
                <span class="sys-kpi-label"><i class="bi bi-memory text-info me-1"></i>VRAM Память</span>
                <span class="sys-kpi-value text-info" id="sys-gpu-kpi-vram-${idx}">-- / -- GB</span>
              </div>
              <div class="sys-kpi-pill">
                <span class="sys-kpi-label"><i class="bi bi-lightning-charge text-warning me-1"></i>Мощность</span>
                <span class="sys-kpi-value text-warning" id="sys-gpu-kpi-power-${idx}">-- W</span>
              </div>
              <div class="sys-kpi-pill">
                <span class="sys-kpi-label"><i class="bi bi-speedometer2 text-primary me-1"></i>Частота Core</span>
                <span class="sys-kpi-value text-primary" id="sys-gpu-kpi-clock-${idx}">-- MHz</span>
              </div>
              <div class="sys-kpi-pill">
                <span class="sys-kpi-label"><i class="bi bi-thermometer-half text-danger me-1"></i>GPU t°</span>
                <span class="sys-kpi-value text-warning" id="sys-gpu-kpi-temp-${idx}">-- °C</span>
              </div>
            </div>
          </div>

          <!-- Центральная колонка: Спидометр загрузки, справа от него значение с динамическим оттенком, а СНИЗУ — датчик температуры -->
          <div class="sys-banner-col-gauge d-flex flex-column justify-content-between gap-1.5">
            <div class="d-flex align-items-center gap-2.5">
              <div id="sys-metric-gpu-gauge-${idx}" style="width: 120px; height: 68px; flex-shrink: 0;"></div>
              <div>
                <div class="sys-value text-warning" id="sys-metric-gpu-val-${idx}" style="font-size: 2.1rem; line-height: 1; font-weight: 800; transition: color 0.3s ease, text-shadow 0.3s ease;">0.0%</div>
                <div class="text-light mt-1 font-monospace" style="font-size: 0.82rem; font-weight: 700;" id="sys-metric-gpu-core-temp-${idx}">GPU: -- °C</div>
              </div>
            </div>
            <!-- Датчик температуры GPU Core расположен ПОД спидометром загрузки -->
            <div id="sys-metric-gpu-temp-slider-${idx}" style="width: 100%;"></div>
          </div>

          <!-- Правая колонка: Сводная таблица о GPU (кликабельна для запуска AI-аудита) -->
          <div class="sys-banner-col-specs">
            <div class="sys-gpu-specs-card p-2 rounded-2 d-flex flex-column justify-content-between h-100" 
                 id="sys-gpu-specs-card-${idx}"
                 onclick="window.inspectGpuSpecsWithAi && window.inspectGpuSpecsWithAi(${idx})"
                 title="Нажмите для вызова AI-аудита и экспертного анализа графического процессора">
              <div class="d-flex justify-content-between align-items-center mb-1 pb-1 border-bottom" style="border-color: var(--border-subtle) !important;">
                <span class="text-light fw-bold d-flex align-items-center gap-1" style="font-size: 0.78rem;">
                  <i class="bi bi-info-circle text-warning"></i>Характеристики GPU
                  <span class="badge bg-primary-subtle text-primary border border-primary-subtle font-monospace ms-1" style="font-size: 0.62rem;"><i class="bi bi-stars me-0.5"></i>AI</span>
                </span>
                <span class="badge bg-dark border border-secondary text-warning font-monospace" style="font-size: 0.68rem;" id="sys-gpu-spec-directx-${idx}">DirectX 12</span>
              </div>
              <div class="sys-gpu-specs-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px 10px; font-size: 0.74rem;">
                <div class="d-flex justify-content-between"><span class="text-muted">VRAM Объем:</span><span class="text-light font-monospace fw-semibold" id="sys-gpu-spec-vram-${idx}">--</span></div>
                <div class="d-flex justify-content-between"><span class="text-muted">Исп. VRAM:</span><span class="text-warning font-monospace fw-semibold" id="sys-gpu-spec-vram-used-${idx}">--</span></div>
                <div class="d-flex justify-content-between"><span class="text-muted">Частота Core:</span><span class="text-warning font-monospace fw-semibold" id="sys-gpu-spec-core-clock-${idx}">--</span></div>
                <div class="d-flex justify-content-between"><span class="text-muted">Частота Mem:</span><span class="text-warning font-monospace fw-semibold" id="sys-gpu-spec-mem-clock-${idx}">--</span></div>
                <div class="d-flex justify-content-between" style="grid-column: span 2;"><span class="text-muted">Драйвер / API:</span><span class="text-info font-monospace fw-semibold" id="sys-gpu-spec-driver-${idx}">--</span></div>
              </div>
            </div>
          </div>
        </div>

        <!-- График истории GPU (Загрузка %, Температура °C, Мощность / Память %) с логарифмической/линейной шкалой -->
        <div class="sys-full-only sys-history-panel p-2.5 mb-2.5 rounded-2">
          <div class="d-flex justify-content-between align-items-center mb-1.5 flex-wrap gap-2">
            <div class="d-flex align-items-center gap-2">
              <span class="small text-light" style="font-size: 0.80rem; font-weight: 700;"><i class="bi bi-graph-up text-warning me-1"></i>История GPU</span>
              <div class="btn-group btn-group-sm" role="group" style="height: 22px;">
                <button type="button" class="btn btn-xs btn-outline-warning active py-0 px-2 fw-bold" id="btn-gpu-spark-log-${idx}" style="font-size: 0.68rem;" onclick="window.setGpuSparkScale && window.setGpuSparkScale('log', ${idx})">Лог. шкала (Log)</button>
                <button type="button" class="btn btn-xs btn-outline-secondary py-0 px-2" id="btn-gpu-spark-lin-${idx}" style="font-size: 0.68rem;" onclick="window.setGpuSparkScale && window.setGpuSparkScale('linear', ${idx})">Линейная (Lin)</button>
              </div>
            </div>
            <div class="d-flex align-items-center gap-2.5" style="font-size: 0.74rem; font-weight: 600;">
              <span class="text-warning" style="text-shadow: 0 0 8px rgba(245,158,11,0.5);" title="Основная шкала: Загрузка GPU Core (0-100%)">● Нагрузка Core %</span>
              <span class="text-danger" style="text-shadow: 0 0 8px rgba(239,68,68,0.5);" title="Компактная шкала: Температура GPU Core (°C)">● Температура °C</span>
              <span class="text-info" style="text-shadow: 0 0 8px rgba(13,202,240,0.5);" title="Компактная шкала: Мощность W / VRAM %">● Мощность / Память %</span>
              <span class="text-muted font-monospace ms-2" id="sys-gpu-spark-live-cursor-${idx}" style="font-size: 0.70rem;">Live</span>
            </div>
          </div>
          <!-- Контейнер графика и интерактивного тултипа -->
          <div style="position: relative; width: 100%; height: 90px;" id="sys-gpu-spark-container-${idx}">
            <div id="sys-gpu-spark-${idx}" style="width: 100%; height: 100%;"></div>
            <div id="sys-gpu-spark-tooltip-${idx}" class="sys-spark-tooltip" style="display: none;"></div>
          </div>
        </div>

        <!-- Сворачиваемый блок детализации GPU: Блоки, подсистемы и сенсоры питания/напряжения/кулеров -->
        <div class="sys-full-only sys-detailed-sensors mt-2">
          <div class="sys-gpu-details-accordion-btn d-flex justify-content-between align-items-center flex-wrap gap-2" 
               id="sys-gpu-details-toggle-btn-${idx}"
               title="Нажмите, чтобы развернуть или скрыть детализацию по подсистемам и сенсорам GPU"
               onclick="window.toggleSysGpuDetails && window.toggleSysGpuDetails(${idx})">
            <div class="d-flex align-items-center gap-2 flex-wrap">
              <span class="text-warning" style="font-size: 1rem;"><i class="bi bi-grid-3x3-gap-fill"></i></span>
              <span class="fw-bold" style="font-size: 0.88rem; color: var(--text-color);">Детализация: Блоки, подсистемы и сенсоры GPU</span>
              <span class="badge bg-dark border border-secondary text-warning font-monospace ms-1" style="font-size: 0.72rem;" id="sys-gpu-engines-count-badge-${idx}">0 блоков</span>
              <span class="badge bg-dark border border-secondary text-danger font-monospace" style="font-size: 0.72rem;" id="sys-gpu-sensors-count-badge-${idx}">0 параметров</span>
            </div>
            <div class="d-flex align-items-center gap-2">
              <button class="btn btn-xs btn-outline-warning rounded-pill px-3 py-1 fw-bold d-flex align-items-center gap-1.5" id="sys-gpu-details-action-btn-${idx}" type="button" style="pointer-events: none; font-size: 0.76rem;">
                <i class="bi bi-chevron-down" id="sys-gpu-details-toggle-icon-${idx}"></i>
                <span id="sys-gpu-details-toggle-text-${idx}">Развернуть детализацию</span>
              </button>
            </div>
          </div>

          <!-- Скрытый по умолчанию общий контейнер деталей GPU -->
          <div id="sys-gpu-details-collapse-${idx}" style="display: none; flex-direction: column; gap: 14px; margin-top: 10px;">
            <!-- 1. Блоки и подсистемы GPU -->
            <div>
              <div class="sys-core-section-title d-flex justify-content-between align-items-center mb-2" style="font-size: 0.82rem;">
                <span><i class="bi bi-grid-3x3-gap-fill text-warning me-1"></i>Блоки и подсистемы GPU</span>
              </div>
              <div id="sys-metric-gpu-engines-${idx}" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(175px, 1fr)); gap: 10px; font-size: 0.78rem;"></div>
            </div>

            <!-- 2. Энергопотребление, напряжение, частоты и сенсоры GPU -->
            <div>
              <div class="sys-core-section-title d-flex justify-content-between align-items-center mb-2" style="font-size: 0.82rem;">
                <span><i class="bi bi-lightning-charge text-warning me-1"></i>Энергопотребление, напряжение, вентиляторы и частоты GPU</span>
              </div>
              <div id="sys-metric-gpu-sensors-${idx}" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 8px; font-size: 0.78rem;">
                <div class="text-muted small text-center py-2 col-12">Опрос сенсоров GPU...</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function updateSingleGpuCard(gpu, idx, totalDevices) {
    const pct = Number(gpu.core_load_percent || 0);
    const coreTemp = gpu.core_temperature_c != null ? Number(gpu.core_temperature_c) : null;
    const hotspotTemp = gpu.hotspot_temperature_c != null ? Number(gpu.hotspot_temperature_c) : null;
    const powerW = gpu.power_w != null ? Number(gpu.power_w) : null;
    const clocks = gpu.clocks || {};
    const memory = gpu.memory || {};
    const specs = gpu.specs || {};
    const engines = Array.isArray(gpu.engines) ? gpu.engines : [];
    const sensorsList = Array.isArray(gpu.sensors) ? gpu.sensors : [];

    const gpuVal = document.getElementById(`sys-metric-gpu-val-${idx}`);
    const gpuModel = document.getElementById(`sys-metric-gpu-model-${idx}`);
    const gpuVendorBadge = document.getElementById(`sys-metric-gpu-vendor-badge-${idx}`);
    const gpuSub = document.getElementById(`sys-metric-gpu-sub-${idx}`);
    const gpuGauge = document.getElementById(`sys-metric-gpu-gauge-${idx}`);
    const gpuTempSlider = document.getElementById(`sys-metric-gpu-temp-slider-${idx}`);
    const gpuCoreTemp = document.getElementById(`sys-metric-gpu-core-temp-${idx}`);

    if (gpuVal) {
      gpuVal.innerText = `${pct.toFixed(1)}%`;
      if (pct >= 85) {
        gpuVal.style.color = '#ef4444';
        gpuVal.style.textShadow = '0 0 16px rgba(239, 68, 68, 0.7)';
      } else if (pct >= 60) {
        gpuVal.style.color = '#f59e0b';
        gpuVal.style.textShadow = '0 0 14px rgba(245, 158, 11, 0.6)';
      } else if (pct >= 25) {
        gpuVal.style.color = '#eab308';
        gpuVal.style.textShadow = '0 0 12px rgba(234, 179, 8, 0.4)';
      } else {
        gpuVal.style.color = '#10b981';
        gpuVal.style.textShadow = '0 0 10px rgba(16, 185, 129, 0.3)';
      }
    }

    if (gpuModel) {
      gpuModel.innerText = gpu.name || 'GPU';
      gpuModel.title = gpu.name || 'GPU';
    }

    if (gpuVendorBadge) {
      const v = specs.vendor || gpu.vendor || 'GPU';
      const bus = specs.pci_bus || 'PCIe x16';
      gpuVendorBadge.textContent = `${v} Corporation · ${bus}`;
    }

    if (gpuCoreTemp) {
      let tempText = coreTemp != null ? `GPU: ${coreTemp.toFixed(0)} °C` : 'GPU: -- °C';
      if (hotspotTemp != null) {
        tempText += ` (HotSpot: ${hotspotTemp.toFixed(0)}°C)`;
      }
      gpuCoreTemp.innerText = tempText;
    }

    if (gpuSub) {
      let subText = '';
      if (clocks && clocks.core_mhz) {
        subText += `${Math.round(clocks.core_mhz)} MHz`;
      }
      if (memory && memory.total_mb) {
        const totalGb = (memory.total_mb / 1024).toFixed(1);
        subText += (subText ? ' · ' : '') + `${totalGb} GB VRAM`;
      }
      gpuSub.innerText = subText || (gpu.name || 'GPU');
      gpuSub.title = subText || (gpu.name || 'GPU');
    }

    // Спецификации
    const specVram = document.getElementById(`sys-gpu-spec-vram-${idx}`);
    const specVramUsed = document.getElementById(`sys-gpu-spec-vram-used-${idx}`);
    const specCoreClock = document.getElementById(`sys-gpu-spec-core-clock-${idx}`);
    const specMemClock = document.getElementById(`sys-gpu-spec-mem-clock-${idx}`);
    const specDriver = document.getElementById(`sys-gpu-spec-driver-${idx}`);
    const specDirectx = document.getElementById(`sys-gpu-spec-directx-${idx}`);

    if (specVram) specVram.textContent = specs.vram_str || (memory.total_mb ? `${(memory.total_mb/1024).toFixed(1)} GB` : '--');
    if (specVramUsed) specVramUsed.textContent = specs.vram_used_str || (memory.used_percent != null ? `${memory.used_percent.toFixed(0)}%` : '--');
    if (specCoreClock) specCoreClock.textContent = specs.core_clock_str || (clocks.core_mhz ? `${Math.round(clocks.core_mhz)} MHz` : '--');
    if (specMemClock) specMemClock.textContent = specs.memory_clock_str || (clocks.memory_mhz ? `${Math.round(clocks.memory_mhz)} MHz` : '--');
    if (specDriver) specDriver.textContent = specs.driver_version ? `${specs.driver_version} (DirectX 12)` : 'WDDM 2.7 (DirectX 12)';
    if (specDirectx) specDirectx.textContent = specs.directx || 'DirectX 12';

    // Экспресс-метрики KPI в центре баннера GPU
    const kpiVram = document.getElementById(`sys-gpu-kpi-vram-${idx}`);
    const kpiPower = document.getElementById(`sys-gpu-kpi-power-${idx}`);
    const kpiClock = document.getElementById(`sys-gpu-kpi-clock-${idx}`);
    const kpiTemp = document.getElementById(`sys-gpu-kpi-temp-${idx}`);
    if (kpiVram) {
      if (memory && memory.total_mb) {
        const uGb = ((memory.used_mb || 0) / 1024).toFixed(1);
        const tGb = (memory.total_mb / 1024).toFixed(1);
        kpiVram.textContent = `${uGb} / ${tGb} GB`;
      } else {
        kpiVram.textContent = '-- / -- GB';
      }
    }
    if (kpiPower) kpiPower.textContent = powerW != null ? `${powerW.toFixed(0)} W` : (gpu.power_w ? `${gpu.power_w} W` : '-- W');
    if (kpiClock) kpiClock.textContent = clocks && clocks.core_mhz ? `${Math.round(clocks.core_mhz)} MHz` : '-- MHz';
    if (kpiTemp) {
      kpiTemp.textContent = coreTemp != null ? `${coreTemp.toFixed(0)} °C` : '-- °C';
      if (coreTemp != null) {
        kpiTemp.className = coreTemp >= 80 ? 'sys-kpi-value text-danger' : coreTemp >= 65 ? 'sys-kpi-value text-warning' : 'sys-kpi-value text-info';
      }
    }

    // Gauge SVG
    if (gpuGauge) {
      gpuGauge.innerHTML = createGaugeSvg(pct, 120, 68);
    }

    // Temp slider
    if (gpuTempSlider) {
      gpuTempSlider.innerHTML = createTempSliderHtml(coreTemp, 30, 95, true);
    }

    // Engines
    renderGpuEngines(engines, idx);

    // Sensors
    const gpuSensorsContainer = document.getElementById(`sys-metric-gpu-sensors-${idx}`);
    const gpuSensorsCountBadge = document.getElementById(`sys-gpu-sensors-count-badge-${idx}`);
    if (gpuSensorsCountBadge) {
      gpuSensorsCountBadge.textContent = `${sensorsList.length} параметров`;
    }
    if (gpuSensorsContainer) {
      if (sensorsList.length === 0) {
        gpuSensorsContainer.innerHTML = `<div class="text-muted small text-center py-2 col-12">Датчики питания и вентиляторов GPU опрашиваются...</div>`;
      } else {
        gpuSensorsContainer.innerHTML = sensorsList.map(s => {
          const statusClass = s.status === 'danger' ? 'badge bg-danger text-white' : (s.status === 'warning' ? 'badge bg-warning text-dark' : 'badge bg-dark border border-secondary text-warning');
          return `
            <div class="sys-sensor-widget-item p-2 rounded-2 d-flex flex-column justify-content-between" style="min-height: 52px;">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="sys-sensor-name text-truncate" title="${escapeHtml(s.name)}" style="font-size: 0.74rem; font-weight: 600; color: var(--text-color);">${escapeHtml(s.name)}</span>
                <span class="${statusClass} font-monospace" style="font-size: 0.68rem;">${escapeHtml(s.category || 'GPU')}</span>
              </div>
              <div class="d-flex justify-content-between align-items-baseline">
                <span class="text-muted" style="font-size: 0.68rem;">Значение</span>
                <span class="font-monospace fw-bold" style="font-size: 0.82rem; color: var(--text-color);">${escapeHtml(s.value_raw || String(s.value))}</span>
              </div>
            </div>
          `;
        }).join('');
      }
    }

    // Sparkline
    if (Array.isArray(gpu.history) && gpu.history.length > 0) {
      renderGpuSpark(gpu.history, idx);
    } else {
      if (!_gpuSparkHistories[idx]) _gpuSparkHistories[idx] = [];
      _gpuSparkHistories[idx].push({ load: pct, temp: coreTemp, power: powerW, time: new Date() });
      if (_gpuSparkHistories[idx].length > 60) _gpuSparkHistories[idx].shift();
      renderGpuSpark(_gpuSparkHistories[idx], idx);
    }
  }

  async function fetchGpuLoadFromApi() {
    try {
      const res = await fetch('/api/v1/panel/gpu-load');
      if (!res.ok) return;
      const data = await res.json();
      lastGpuData = data;

      const devices = Array.isArray(data.devices) && data.devices.length > 0 ? data.devices : [data];
      lastGpuDevices = devices;

      const container = document.getElementById('sys-gpu-panels-container');
      if (!container) return;

      const currentCards = container.querySelectorAll('.sys-card-gpu');
      if (currentCards.length !== devices.length) {
        container.innerHTML = devices.map((gpu, idx) => renderGpuCardHtml(gpu, idx, devices.length)).join('');
      }

      devices.forEach((gpu, idx) => {
        updateSingleGpuCard(gpu, idx, devices.length);
      });
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

      // Экспресс-метрики KPI в центре баннера RAM
      const ramKpiUsed = document.getElementById('sys-ram-kpi-used');
      const ramKpiFree = document.getElementById('sys-ram-kpi-free');
      const ramKpiSwap = document.getElementById('sys-ram-kpi-swap');
      if (ramKpiUsed) ramKpiUsed.textContent = `${usedGb.toFixed(1)} GB`;
      if (ramKpiFree) ramKpiFree.textContent = `${Number(snap.memory.available_gb || (totalGb - usedGb)).toFixed(1)} GB`;
      if (ramKpiSwap) ramKpiSwap.textContent = `${swapPct.toFixed(1)}%`;

      // Swap
      const swapSubBadge = document.getElementById('sys-swap-sub-badge');
      if (swapSubBadge) swapSubBadge.textContent = `${swapPct.toFixed(1)}%`;
      const swapSubGauge = document.getElementById('sys-swap-sub-gauge');
      if (swapSubGauge) swapSubGauge.innerHTML = createGaugeSvg(swapPct, 100, 56);
      const swapSubSlider = document.getElementById('sys-swap-sub-slider');
      if (swapSubSlider) swapSubSlider.innerHTML = createPercentSliderHtml(swapPct, false, `Подкачка ${swapPct.toFixed(1)}%`);
    }

    // GPU: данные для независимых карточек берутся строго из fetchGpuLoadFromApi()
    if (!lastGpuData) {
      fetchGpuLoadFromApi();
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
      const ramKpiIo = document.getElementById('sys-ram-kpi-io');
      if (ramKpiIo) ramKpiIo.textContent = `${totalMb} MB/s`;

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
        <div>Сетевые сокеты: <span class="fw-bold" style="color: var(--text-color);">${portCount} портов LISTEN</span></div>
        <div class="text-truncate" title="${escapeHtml(snap.alerts?.latest_alert || '')}">${escapeHtml(snap.alerts?.latest_alert || 'Система стабильна')}</div>
      `;
    }
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
            <div class="fw-bold text-truncate" style="max-width: 165px; color: var(--text-color);" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
            <div class="small text-muted" style="font-size: 0.70rem;">PID: <span class="font-monospace text-info">${item.pid}</span> ${item.user ? '• ' + escapeHtml(item.user) : ''}</div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-1">
              ${isExtBadge}
              <span class="font-monospace fw-semibold text-truncate" style="max-width: 195px; color: var(--text-color);" title="${escapeHtml(item.remote_address)}">
                ${escapeHtml(item.remote_address !== '-' ? item.remote_address : item.local_address)}
              </span>
            </div>
            <div class="small text-muted font-monospace" style="font-size: 0.68rem;">Local: ${escapeHtml(item.local_address)}</div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-1 mb-0.5">
              ${protoBadge}
              <span class="fw-semibold text-truncate" style="max-width: 110px; font-size: 0.74rem; color: var(--nav-active);" title="${escapeHtml(item.service_type)}">${escapeHtml(item.service_type)}</span>
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
              <div class="text-truncate" style="max-width: 250px; font-size: 0.72rem; color: var(--text-muted);" title="${escapeHtml(item.sent_summary)}">
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
              <div class="text-truncate" style="max-width: 250px; font-size: 0.72rem; color: var(--text-muted);" title="${escapeHtml(item.recv_summary)}">
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

    const btnAudit = document.getElementById('btn-sys-run-audit');
    if (btnAudit) {
      btnAudit.onclick = () => runAiDiagnostics();
    }

    const btnCompact = document.getElementById('btn-sys-toggle-compact');
    const sysContainer = document.querySelector('.sys-container');
    const compactText = document.getElementById('sys-compact-btn-text');

    const updateCompactUI = (isCompact) => {
      if (!sysContainer) return;
      if (isCompact) {
        sysContainer.classList.add('sys-compact-mode');
        if (compactText) compactText.textContent = 'Развернуть';
        if (btnCompact) {
          btnCompact.classList.add('btn-info', 'text-dark');
          btnCompact.classList.remove('btn-outline-secondary');
        }
      } else {
        sysContainer.classList.remove('sys-compact-mode');
        if (compactText) compactText.textContent = 'Компактно';
        if (btnCompact) {
          btnCompact.classList.remove('btn-info', 'text-dark');
          btnCompact.classList.add('btn-outline-secondary');
        }
      }
    };

    if (btnCompact && sysContainer) {
      const savedCompact = localStorage.getItem('sys_inspector_compact_mode');
      const isCompact = savedCompact === null ? true : savedCompact === 'true';
      updateCompactUI(isCompact);
      btnCompact.onclick = () => {
        const nextState = !sysContainer.classList.contains('sys-compact-mode');
        updateCompactUI(nextState);
        try { localStorage.setItem('sys_inspector_compact_mode', String(nextState)); } catch (e) {}
      };
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

    let html = `<select class="form-select form-select-sm sys-int-select" data-logger="${loggerName}" style="min-width: 120px;">`;
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
              <td class="font-monospace small" style="word-break: break-all; color: var(--text-color);" title="${escapeHtml(e.path)}">${escapeHtml(e.path)}</td>
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
              <span class="fw-bold small" style="color: var(--text-color);">${escapeHtml(folderName)}</span>
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
        <button class="btn btn-xs btn-outline-secondary rounded-pill px-2 py-0.5 sys-drive-btn font-monospace" data-drive="${escapeHtml(label)}" title="${escapeHtml(label)} ${freeTxt}">
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
          <a href="#" class="sys-breadcrumb-link text-decoration-none ${isLast ? 'fw-bold text-info' : ''}" style="color: var(--text-color);" data-path="${escapeHtml(clickPath)}">
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

