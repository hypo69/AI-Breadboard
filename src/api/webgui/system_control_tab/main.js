/**
 * =============================================================================
 * Process Name: Windows System Control Center Web Controller
 * =============================================================================
 * Description:
 *   Client-side JavaScript controller for the System Control Center tab in
 *   the administrative web interface. Includes monitoring, post-install wizard,
 *   maintenance & recovery, and the unified Windows OS System Log Center.
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src.api.webinterface.system_control_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

(function () {
  'use strict';

  let isSCCInitialized = false;
  let activeProfileSteps = [];

  // System Log Center states
  let currentChannel = 'System';
  let currentFilePath = '';
  let currentMode = 'live';
  let cachedEvents = [];
  let cachedChannels = [];
  let selectedEvent = null;
  let liveIntervalTimer = null;
  let isLogRequestInProgress = false;
  let globalTooltipEl = null;

  /**
   * Escape HTML entities to protect against XSS injection.
   *
   * @param {string} str - Raw input text.
   * @returns {string} Sanitized string.
   */
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Format ISO timestamps.
   *
   * @param {string} isoStr - ISO Timestamp string.
   * @returns {string} Formatted time string.
   */
  function formatTime(isoStr) {
    if (!isoStr) return '-';
    try {
      return new Date(isoStr).toLocaleTimeString();
    } catch {
      return isoStr.slice(11, 19);
    }
  }

  /**
   * Map log severity to badge styling class.
   *
   * @param {string} level - Severity level.
   * @returns {string} CSS class name.
   */
  function getSeverityClass(level) {
    const lvl = (level || '').toLowerCase();
    if (lvl.includes('crit')) return 'badge-crit';
    if (lvl.includes('err')) return 'badge-err';
    if (lvl.includes('warn')) return 'badge-warn';
    if (lvl.includes('verb')) return 'badge-verb';
    return 'badge-inf';
  }

  // =========================================================================
  // SECTION 1: System Control Status & Monitoring
  // =========================================================================

  async function fetchStatus() {
    try {
      const res = await fetch('/api/system-control/status');
      if (!res.ok) return;
      const data = await res.json();

      // Elevation badge
      const elevBadge = document.getElementById('scc-elevation-badge');
      if (elevBadge) {
        if (data.is_elevated) {
          elevBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
          elevBadge.innerHTML = '🛡️ Mode: Administrator (Full Access)';
        } else {
          elevBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
          elevBadge.innerHTML = '👁️ Mode: Standard User (Read-Only)';
        }
      }

      const sys = data.system || {};
      const sec = data.security || {};
      const rest = data.restore || {};
      const disk = data.disk || {};
      const pwr = data.power || {};
      const upd = data.update || {};

      const cleanEstimateTxt = document.getElementById('scc-clean-estimate-txt');
      if (cleanEstimateTxt) {
        const cleanMb = disk.cleanup_estimate?.total_cleanable_mb || 0;
        cleanEstimateTxt.innerText = `Cleanable: ~${cleanMb} MB`;
      }

      // Specifications Table
      const uptimeSec = sys.uptime_seconds || 0;
      const uptimeTxt = `${Math.floor(uptimeSec / 3600)}h ${Math.floor((uptimeSec % 3600) / 60)}m`;
      const upBadge = document.getElementById('scc-overview-uptime');
      if (upBadge) upBadge.innerText = `Uptime: ${uptimeTxt}`;

      const setTxt = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val || '-';
      };

      setTxt('scc-spec-host', sys.hostname);
      setTxt('scc-spec-os', `${sys.os_caption} (Build ${sys.os_build})`);
      setTxt('scc-spec-cpu', `${sys.cpu_model} (${sys.cpu_cores_logical} logical cores)`);
      setTxt('scc-spec-ram', `${sys.ram_available_gb} GB free / ${sys.ram_total_gb} GB total (${sys.ram_percent}% used)`);
      setTxt('scc-spec-power', pwr.active_plan_name);
      setTxt('scc-spec-update', `${upd.status} (${upd.recent_hotfixes_count} KBs installed)`);

      // Security Table
      setTxt('scc-sec-def', sec.defender_enabled ? 'Enabled' : 'Disabled');
      setTxt('scc-sec-rt', sec.realtime_protection_enabled ? 'Enabled' : 'Disabled');
      setTxt('scc-sec-fw-dom', sec.firewall_domain_enabled ? 'Active' : 'Disabled');
      setTxt('scc-sec-fw-priv', sec.firewall_private_enabled ? 'Active' : 'Disabled');
      setTxt('scc-sec-fw-pub', sec.firewall_public_enabled ? 'Active' : 'Disabled');
      setTxt('scc-sec-uac', sec.uac_enabled ? 'Enabled' : 'Disabled');

      const secBadge = document.getElementById('scc-sec-badge');
      if (secBadge) {
        secBadge.innerText = sec.overall_status;
        secBadge.className = sec.overall_status === 'SECURE' ? 'badge bg-success-subtle text-success' : 'badge bg-warning-subtle text-warning';
      }

      // Restore points table
      fetchRestorePoints();
    } catch (e) {
      console.error('[SystemControl] Failed to fetch status:', e);
    }
  }

  function formatRestorePointType(rawType) {
    if (!rawType) return 'System Checkpoint';
    const s = String(rawType).toUpperCase();
    if (s.includes('APPLICATION_INSTALL') || s === '0') return 'App Install';
    if (s.includes('APPLICATION_UNINSTALL') || s === '1') return 'App Uninstall';
    if (s.includes('DEVICE_DRIVER') || s === '10') return 'Driver Install';
    if (s.includes('MODIFY_SETTINGS') || s === '12') return 'Settings Change';
    if (s.includes('CANCELLED') || s === '13') return 'Cancelled Op';
    if (s.includes('WINDOWS_UPDATE') || s === '17') return 'Windows Update';
    return s.replace(/_/g, ' ');
  }

  function formatRestoreTime(rawTime) {
    if (!rawTime) return '-';
    const s = String(rawTime).trim();
    if (s.length >= 14 && /^\d{14}/.test(s)) {
      return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)} ${s.slice(8, 10)}:${s.slice(10, 12)}:${s.slice(12, 14)}`;
    }
    return s;
  }

  async function fetchRestorePoints() {
    try {
      const res = await fetch('/api/system-control/restore-points');
      if (!res.ok) return;
      const data = await res.json();
      const points = data.restore_points || [];

      const tbody = document.getElementById('scc-restore-tbody');
      if (tbody) {
        if (points.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted p-3">No restore points found. Click "Create Restore Point" to generate one.</td></tr>';
          return;
        }
        tbody.innerHTML = points.map((p, idx) => {
          const typeBadge = formatRestorePointType(p.restore_point_type);
          const timeFormatted = formatRestoreTime(p.creation_time);
          return `
          <tr class="scc-restore-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для анализа точки восстановления">
            <td class="font-monospace text-info fw-bold">#${p.sequence_number}</td>
            <td class="fw-semibold text-white">${p.description}</td>
            <td><span class="badge bg-secondary text-light px-2 py-1 font-monospace" style="font-size: 0.75rem;">${typeBadge}</span></td>
            <td class="small text-light font-monospace">${timeFormatted}</td>
          </tr>
        `;
        }).join('');

        tbody.querySelectorAll('.scc-restore-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const p = points[idx];
            if (!p) return;
            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '🔄',
                title: `Точка восстановления #${p.sequence_number}`,
                subtitle: p.description,
                tableType: 'generic',
                badges: [
                  { text: p.restore_point_type || 'System Checkpoint', class: 'badge bg-info text-dark' }
                ],
                metadata: [
                  { label: 'Номер', value: String(p.sequence_number) },
                  { label: 'Описание', value: p.description },
                  { label: 'Тип', value: p.restore_point_type },
                  { label: 'Дата создания', value: p.creation_time }
                ],
                rawTitle: 'Метаданные точки восстановления',
                rawContent: JSON.stringify(p, null, 2)
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[SystemControl] Failed to fetch restore points:', e);
    }
  }

  // =========================================================================
  // SECTION 2: Post-Install Wizard
  // =========================================================================

  async function loadWizardProfiles() {
    try {
      const res = await fetch('/api/system-control/profiles');
      if (!res.ok) return;
      const data = await res.json();
      const profiles = data.profiles || [];
      const sel = document.getElementById('scc-profile-select');

      if (sel && profiles.length > 0) {
        sel.innerHTML = profiles.map(p => `<option value="${p.profile_id}">${p.name}</option>`).join('');
        renderStepsForSelectedProfile(profiles[0]);
        
        sel.onchange = () => {
          const selected = profiles.find(p => p.profile_id === sel.value);
          if (selected) renderStepsForSelectedProfile(selected);
        };
      }
    } catch (e) {
      console.error('[SystemControl] Failed to load wizard profiles:', e);
    }
  }

  function renderStepsForSelectedProfile(profile) {
    const container = document.getElementById('scc-wizard-steps-container');
    if (!container) return;
    activeProfileSteps = profile.steps || [];

    container.innerHTML = activeProfileSteps.map((s) => `
      <div class="card bg-body-tertiary border-secondary p-2 d-flex flex-row align-items-center justify-content-between" id="step-row-${s.id}">
        <div class="d-flex align-items-center gap-3">
          <input class="form-check-input scc-step-checkbox" type="checkbox" id="chk-step-${s.id}" data-id="${s.id}" ${s.enabled ? 'checked' : ''} style="cursor: pointer;">
          <div>
            <div class="fw-semibold text-white">${s.title}</div>
            <div class="small text-muted">${s.description}</div>
          </div>
        </div>
        <div class="d-flex align-items-center gap-2">
          ${s.requires_elevation ? '<span class="badge bg-secondary font-monospace" style="font-size: 0.7rem;">Admin</span>' : ''}
          <span class="badge ${s.status === 'SUCCESS' ? 'scc-badge-secure' : (s.status === 'WARNING' ? 'scc-badge-warn' : (s.status === 'FAILED' ? 'scc-badge-danger' : 'bg-secondary'))}" id="step-status-${s.id}">
            ${s.status}
          </span>
        </div>
      </div>
    `).join('');
  }

  async function applyCurrentProfile() {
    const sel = document.getElementById('scc-profile-select');
    const profileId = sel ? sel.value : 'post_install';
    const applyBtn = document.getElementById('btn-scc-apply-profile');

    const selectedStepIds = [];
    document.querySelectorAll('.scc-step-checkbox:checked').forEach(chk => {
      selectedStepIds.push(chk.getAttribute('data-id'));
    });

    if (applyBtn) {
      applyBtn.disabled = true;
      applyBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Applying...';
    }

    try {
      const res = await fetch('/api/system-control/profiles/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile_id: profileId,
          selected_step_ids: selectedStepIds
        })
      });
      if (res.ok) {
        const outcome = await res.json();
        (outcome.steps || []).forEach(st => {
          const badge = document.getElementById(`step-status-${st.id}`);
          if (badge) {
            badge.innerText = st.status;
            badge.className = `badge ${st.status === 'SUCCESS' ? 'scc-badge-secure' : (st.status === 'WARNING' ? 'scc-badge-warn' : 'scc-badge-danger')}`;
            badge.title = st.result_message;
          }
        });
        fetchStatus();
        fetchAppActivityLogs();
      }
    } catch (e) {
      console.error('[SystemControl] Failed to apply profile:', e);
    } finally {
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="bi bi-play-fill me-1"></i> Apply Profile';
      }
    }
  }

  // =========================================================================
  // SECTION 3: System Control Restore Policy & Storage
  // =========================================================================

  async function loadRestorePolicyModal() {
    try {
      const res = await fetch('/api/system-control/restore-points/config');
      if (!res.ok) return;
      const data = await res.json();

      const storageSel = document.getElementById('scc-policy-storage-size');
      const triggerSel = document.getElementById('scc-policy-trigger');
      const timeInput = document.getElementById('scc-policy-time');
      const timeWrapper = document.getElementById('scc-policy-time-wrapper');
      const freqChk = document.getElementById('scc-policy-freq-limit');
      const maxPtsSel = document.getElementById('scc-policy-max-points');
      const autoPruneChk = document.getElementById('scc-policy-auto-prune');
      const storageBar = document.getElementById('scc-policy-storage-bar');
      const storageLabel = document.getElementById('scc-policy-storage-label');

      if (storageSel && data.max_storage_size) storageSel.value = data.max_storage_size;
      if (triggerSel && data.schedule_trigger) {
        triggerSel.value = data.schedule_trigger;
        if (timeWrapper) timeWrapper.style.display = (data.schedule_trigger === 'daily' || data.schedule_trigger === 'weekly') ? 'block' : 'none';
      }
      if (timeInput && data.schedule_time) timeInput.value = data.schedule_time;
      if (freqChk) freqChk.checked = data.frequency_limit_minutes === 0;
      if (maxPtsSel && data.max_points) maxPtsSel.value = String(data.max_points);
      if (autoPruneChk && data.auto_prune !== undefined) autoPruneChk.checked = Boolean(data.auto_prune);

      const st = data.storage_info || {};
      if (storageBar && storageLabel) {
        const pct = st.usage_percent || 0;
        const usedGb = (st.used_bytes ? (st.used_bytes / (1024 ** 3)).toFixed(2) : '0.00');
        const maxGb = (st.max_bytes ? (st.max_bytes / (1024 ** 3)).toFixed(2) : '0.00');
        storageBar.style.width = `${Math.min(pct, 100)}%`;
        storageBar.className = pct > 85 ? 'progress-bar bg-danger' : (pct > 60 ? 'progress-bar bg-warning' : 'progress-bar bg-info');
        storageLabel.innerHTML = `<span>Used: ${usedGb} GB (${pct}%)</span><span>Max: ${maxGb} GB</span>`;
      }

      if (triggerSel) {
        triggerSel.onchange = () => {
          if (timeWrapper) timeWrapper.style.display = (triggerSel.value === 'daily' || triggerSel.value === 'weekly') ? 'block' : 'none';
        };
      }

      const modalEl = document.getElementById('modal-scc-restore-config');
      if (modalEl && window.bootstrap?.Modal) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
      }
    } catch (e) {
      console.error('[SystemControl] Failed to load restore policy config:', e);
    }
  }

  async function saveRestorePolicy() {
    const saveBtn = document.getElementById('btn-scc-save-restore-policy');
    const storageSel = document.getElementById('scc-policy-storage-size');
    const triggerSel = document.getElementById('scc-policy-trigger');
    const timeInput = document.getElementById('scc-policy-time');
    const freqChk = document.getElementById('scc-policy-freq-limit');
    const maxPtsSel = document.getElementById('scc-policy-max-points');
    const autoPruneChk = document.getElementById('scc-policy-auto-prune');

    const payload = {
      max_storage_size: storageSel ? storageSel.value : '10%',
      schedule_trigger: triggerSel ? triggerSel.value : 'daily',
      schedule_time: timeInput ? timeInput.value : '03:00',
      frequency_limit_minutes: freqChk && freqChk.checked ? 0 : 1440,
      max_points: maxPtsSel ? parseInt(maxPtsSel.value, 10) : 5,
      auto_prune: autoPruneChk ? autoPruneChk.checked : true,
    };

    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerText = 'Сохранение...';
    }

    try {
      const res = await fetch('/api/system-control/restore-points/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const d = await res.json();
      window.showToast?.(d.message || 'Политика успешно сохранена', d.success ? 'success' : 'danger') || alert(d.message || 'Политика сохранена');
      const modalEl = document.getElementById('modal-scc-restore-config');
      if (modalEl && window.bootstrap?.Modal) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal?.hide();
      }
      fetchRestorePoints();
      fetchAppActivityLogs();
    } catch (e) {
      console.error('[SystemControl] Failed to save restore policy:', e);
      alert('Ошибка сохранения политики точек восстановления: ' + e);
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-check-lg me-1"></i> Сохранить и применить';
      }
    }
  }

  async function pruneRestorePointsNow() {
    const maxPtsSel = document.getElementById('scc-policy-max-points');
    const keep = maxPtsSel ? parseInt(maxPtsSel.value, 10) : 5;
    if (!confirm(`Выполнить принудительную ротацию точек восстановления и оставить только ${keep} последних?`)) {
      return;
    }
    try {
      const res = await fetch('/api/system-control/restore-points/prune', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keep_count: keep })
      });
      const d = await res.json();
      window.showToast?.(d.message || 'Ротация выполнена', 'info') || alert(d.message || 'Ротация выполнена');
      fetchRestorePoints();
      fetchAppActivityLogs();
    } catch (e) {
      console.error('[SystemControl] Failed to prune restore points:', e);
    }
  }

  // =========================================================================
  // SECTION 4: Application Activity Logs (SCC operations)
  // =========================================================================

  async function fetchAppActivityLogs() {
    try {
      const res = await fetch('/api/system-control/logs');
      if (!res.ok) return;
      const data = await res.json();
      const logs = data.logs || [];

      const tbody = document.getElementById('scc-logs-tbody');
      if (tbody) {
        if (logs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted p-3">No activity logs recorded.</td></tr>';
          return;
        }
        tbody.innerHTML = logs.slice(0, 50).map(l => `
          <tr>
            <td class="small font-monospace text-muted">${formatTime(l.timestamp)}</td>
            <td class="fw-bold font-monospace text-info">${escapeHtml(l.action)}</td>
            <td class="small text-white">${escapeHtml(l.target)}</td>
            <td><span class="badge ${l.status === 'SUCCESS' ? 'scc-badge-secure' : (l.status === 'WARNING' ? 'scc-badge-warn' : 'scc-badge-danger')}">${escapeHtml(l.status)}</span></td>
            <td class="small text-muted text-truncate" style="max-width: 250px;">${escapeHtml(l.details)}</td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.error('[SystemControl] Failed to fetch activity logs:', e);
    }
  }

  // =========================================================================
  // SECTION 5: Full Windows OS & System Log Center (Channels, Discovery, RAG)
  // =========================================================================

  function getOrCreateTooltipEl() {
    if (!globalTooltipEl) {
      globalTooltipEl = document.createElement('div');
      globalTooltipEl.className = 'slc-tooltip-popup';
      document.body.appendChild(globalTooltipEl);
    }
    return globalTooltipEl;
  }

  function showChannelTooltip(e, channel) {
    const tip = getOrCreateTooltipEl();
    const countFormatted = (channel.record_count || 0).toLocaleString();
    const descText = channel.description || 'Служебный журнал операционной системы Windows.';
    const typeLabel = channel.source_type === 'channel' ? 'Windows Event Channel' : 'Log File';

    tip.innerHTML = `
      <div class="slc-tooltip-title">
        <i class="bi bi-info-circle text-info"></i>
        <span>${escapeHtml(channel.display_name)}</span>
      </div>
      <div style="color: #cbd5e1; margin-bottom: 0.35rem;">${escapeHtml(descText)}</div>
      <div class="slc-tooltip-meta">
        <span><strong class="text-info">${countFormatted}</strong> записей</span>
        <span class="text-muted font-monospace">${typeLabel}</span>
      </div>
    `;

    tip.classList.add('show');
    positionTooltip(e, tip);
  }

  function hideChannelTooltip() {
    if (globalTooltipEl) {
      globalTooltipEl.classList.remove('show');
    }
  }

  function positionTooltip(e, tip) {
    const margin = 12;
    let x = e.clientX + margin;
    let y = e.clientY + margin;

    const tipRect = tip.getBoundingClientRect();
    if (x + tipRect.width > window.innerWidth) {
      x = e.clientX - tipRect.width - margin;
    }
    if (y + tipRect.height > window.innerHeight) {
      y = e.clientY - tipRect.height - margin;
    }

    tip.style.left = `${Math.max(10, x)}px`;
    tip.style.top = `${Math.max(10, y)}px`;
  }

  async function performSystemScan(force = false) {
    try {
      const response = await fetch(`/api/v1/system_logs/scan?force=${force}`);
      if (!response.ok) return;
      const data = await response.json();

      cachedChannels = data.channels || [];
      const activeChannels = cachedChannels.filter((c) => (c.record_count || 0) > 0);
      const sourcesBadge = document.getElementById('slc-stat-sources');
      const countBadge = document.getElementById('slc-channel-count-badge');

      if (sourcesBadge) {
        sourcesBadge.textContent = `${activeChannels.length.toLocaleString()} active / ${data.total_sources.toLocaleString()} sources`;
      }
      if (countBadge) {
        countBadge.textContent = String(activeChannels.length);
      }

      renderChannelsTree();
    } catch (err) {
      console.warn('[SystemControl] Failed to perform system log scan:', err);
    }
  }

  function renderChannelsTree() {
    const container = document.getElementById('slc-channel-tree-container');
    const filterInput = document.getElementById('slc-channel-filter-input');
    const filterText = filterInput ? filterInput.value.trim().toLowerCase() : '';

    if (!container) return;
    container.innerHTML = '';

    const filtered = cachedChannels.filter((c) => {
      if (c.record_count === 0) return false;
      if (!filterText) return true;
      return (
        c.channel_name.toLowerCase().includes(filterText) ||
        c.display_name.toLowerCase().includes(filterText) ||
        (c.description && c.description.toLowerCase().includes(filterText)) ||
        (c.category && c.category.toLowerCase().includes(filterText))
      );
    });

    const grouped = {};
    filtered.forEach((c) => {
      const cat = c.category || 'Windows Event Log';
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(c);
    });

    const categoryIcons = {
      'Windows Event Log': '🛡️',
      'Windows OS Logs': '📁',
      'Application Logs': '💻',
      'AI-Breadboard Logs': '🤖',
    };

    Object.keys(grouped).forEach((catName) => {
      const catHeader = document.createElement('div');
      catHeader.className = 'd-flex justify-content-between align-items-center px-2 py-1 mt-2 mb-1 rounded bg-dark border border-secondary text-info small fw-bold';
      const icon = categoryIcons[catName] || '📜';
      catHeader.innerHTML = `
        <span>${icon} ${escapeHtml(catName)}</span>
        <span class="badge bg-secondary font-monospace">${grouped[catName].length}</span>
      `;
      container.appendChild(catHeader);

      grouped[catName].slice(0, 400).forEach((c) => {
        const item = document.createElement('div');
        const isActive = (c.channel_name === currentChannel && !currentFilePath) || (currentFilePath && currentFilePath === c.location);
        item.className = `slc-tree-item ${isActive ? 'active' : ''}`;
        
        let subBadge = '0';
        let badgeStyle = 'bg-dark text-secondary';
        if (c.record_count > 0) {
          subBadge = c.record_count >= 1000 ? `${(c.record_count / 1000).toFixed(1)}k` : String(c.record_count);
          badgeStyle = c.record_count > 1000 ? 'bg-primary text-white' : 'bg-dark text-info border border-secondary';
        } else if (c.source_type !== 'channel') {
          subBadge = 'FILE';
        }

        item.innerHTML = `
          <span class="text-truncate me-2" style="max-width: 175px;">${escapeHtml(c.display_name)}</span>
          <span class="badge ${badgeStyle} font-monospace" style="font-size: 0.72rem; min-width: 32px; text-align: right;">${subBadge}</span>
        `;

        item.onmouseenter = (e) => showChannelTooltip(e, c);
        item.onmousemove = (e) => {
          const tip = getOrCreateTooltipEl();
          if (tip.classList.contains('show')) positionTooltip(e, tip);
        };
        item.onmouseleave = () => hideChannelTooltip();

        item.onclick = () => {
          hideChannelTooltip();
          if (c.source_type === 'channel') {
            currentChannel = c.channel_name;
            currentFilePath = '';
          } else {
            currentChannel = c.display_name;
            currentFilePath = c.location;
          }
          const statChan = document.getElementById('slc-stat-channel');
          if (statChan) statChan.textContent = c.display_name;
          renderChannelsTree();
          loadEvents();
        };
        container.appendChild(item);
      });
    });
  }

  async function loadEvents() {
    if (isLogRequestInProgress) return;
    isLogRequestInProgress = true;

    const levelSelect = document.getElementById('slc-level-select');
    const hoursSelect = document.getElementById('slc-hours-select');
    const searchInput = document.getElementById('slc-search-input');
    const eventIdInput = document.getElementById('slc-eventid-input');
    const limitSelect = document.getElementById('slc-limit-select');
    const tableBody = document.getElementById('slc-table-body');
    const eventsBadge = document.getElementById('slc-stat-events');
    const faultsBadge = document.getElementById('slc-stat-incidents');
    const streamBadge = document.getElementById('slc-stream-count-badge');

    const level = levelSelect ? levelSelect.value : '';
    const hours = hoursSelect ? hoursSelect.value : '24';
    const search = searchInput ? searchInput.value.trim() : '';
    const eventId = eventIdInput && eventIdInput.value.trim() ? eventIdInput.value.trim() : '0';
    const limit = limitSelect ? limitSelect.value : '100';

    try {
      const url = `/api/v1/system_logs/events?channel=${encodeURIComponent(currentChannel)}&limit=${limit}&level=${encodeURIComponent(level)}&search=${encodeURIComponent(search)}&hours=${hours}&event_id=${eventId}&file_path=${encodeURIComponent(currentFilePath)}`;

      const res = await fetch(url);
      if (!res.ok) {
        if (tableBody) tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-3">Error reading channel (HTTP ${res.status})</td></tr>`;
        isLogRequestInProgress = false;
        return;
      }

      const data = await res.json();
      cachedEvents = data.entries || [];

      if (eventsBadge) eventsBadge.textContent = String(cachedEvents.length);
      if (streamBadge) streamBadge.textContent = `${cachedEvents.length} records`;

      let errCount = 0;
      let critCount = 0;
      cachedEvents.forEach((e) => {
        const lvl = (e.level || '').toLowerCase();
        if (lvl.includes('crit')) critCount++;
        if (lvl.includes('err')) errCount++;
      });

      if (faultsBadge) {
        faultsBadge.textContent = `${errCount + critCount} faults`;
      }

      renderCurrentModeView();
    } catch (err) {
      console.warn('[SystemControl] Failed to load events:', err);
      if (tableBody) tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-3">Network error loading logs.</td></tr>`;
    } finally {
      isLogRequestInProgress = false;
    }
  }

  function renderCurrentModeView() {
    const tableContainer = document.getElementById('slc-table-container');
    const incidentsContainer = document.getElementById('slc-incidents-container');
    const timelineContainer = document.getElementById('slc-timeline-container');
    const rawContainer = document.getElementById('slc-raw-container');
    const auditContainer = document.getElementById('slc-audit-container');
    const ragContainer = document.getElementById('slc-rag-container');
    const activityContainer = document.getElementById('slc-activity-container');
    const tableBody = document.getElementById('slc-table-body');
    const viewTitle = document.getElementById('slc-main-view-title');

    // Reset visibility
    if (tableContainer) tableContainer.classList.add('d-none');
    if (incidentsContainer) incidentsContainer.classList.add('d-none');
    if (timelineContainer) timelineContainer.classList.add('d-none');
    if (rawContainer) rawContainer.classList.add('d-none');
    if (auditContainer) auditContainer.classList.add('d-none');
    if (ragContainer) ragContainer.classList.add('d-none');
    if (activityContainer) activityContainer.classList.add('d-none');

    if (currentMode === 'activity') {
      if (viewTitle) viewTitle.innerHTML = `<i class="bi bi-journal-text text-warning me-2"></i>Application Activity & Operation Logs`;
      if (activityContainer) {
        activityContainer.classList.remove('d-none');
        fetchAppActivityLogs();
      }
    } else if (currentMode === 'audit') {
      if (viewTitle) viewTitle.innerHTML = `<i class="bi bi-shield-check text-info me-2"></i>Интеллектуальный Аудит Логирования (Zero-LLM Overhead)`;
      if (auditContainer) {
        auditContainer.classList.remove('d-none');
        loadAuditView();
      }
    } else if (currentMode === 'rag') {
      if (viewTitle) viewTitle.innerHTML = `<i class="bi bi-brain text-info me-2"></i>Динамический RAG-поиск по логам`;
      if (ragContainer) {
        ragContainer.classList.remove('d-none');
      }
    } else if (currentMode === 'incidents') {
      if (viewTitle) viewTitle.innerHTML = `<i class="bi bi-diagram-3 me-2"></i>Correlated Incident Cascades`;
      if (incidentsContainer) {
        incidentsContainer.classList.remove('d-none');
        loadIncidentsView();
      }
    } else if (currentMode === 'timeline') {
      if (viewTitle) viewTitle.innerHTML = `<i class="bi bi-bar-chart me-2"></i>Event Frequency Histogram`;
      if (timelineContainer) {
        timelineContainer.classList.remove('d-none');
        loadTimelineView();
      }
    } else if (currentMode === 'raw') {
      if (viewTitle) viewTitle.innerHTML = `<i class="bi bi-code-square me-2"></i>Raw Event Payload Data`;
      if (rawContainer) {
        rawContainer.classList.remove('d-none');
        const rawText = document.getElementById('slc-raw-text');
        if (rawText) {
          rawText.textContent = selectedEvent ? (selectedEvent.raw_data || JSON.stringify(selectedEvent, null, 2)) : JSON.stringify(cachedEvents.slice(0, 10), null, 2);
        }
      }
    } else {
      // Live or Errors Table Mode
      if (tableContainer) tableContainer.classList.remove('d-none');
      if (viewTitle) {
        viewTitle.innerHTML = currentMode === 'errors'
          ? `<i class="bi bi-exclamation-octagon text-danger me-2"></i>Critical & Error Events (${escapeHtml(currentChannel)})`
          : `<i class="bi bi-list-columns-reverse me-2"></i>Live Windows Event Stream (${escapeHtml(currentChannel)})`;
      }

      if (!tableBody) return;

      let entriesToRender = cachedEvents;
      if (currentMode === 'errors') {
        entriesToRender = cachedEvents.filter((e) => {
          const l = (e.level || '').toLowerCase();
          return l.includes('err') || l.includes('crit') || l.includes('warn');
        });
      }

      if (entriesToRender.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No events found matching active filter.</td></tr>`;
        return;
      }

      tableBody.innerHTML = entriesToRender.map((e, idx) => {
        const badgeClass = getSeverityClass(e.level);
        const eidStr = e.event_id > 0 ? String(e.event_id) : '-';
        const pidStr = e.process_id > 0 ? String(e.process_id) : '-';
        const isSelected = selectedEvent && (
          selectedEvent.timestamp === e.timestamp &&
          selectedEvent.event_id === e.event_id &&
          (selectedEvent.provider || selectedEvent.source) === (e.provider || e.source)
        );
        return `
          <tr data-index="${idx}" class="${isSelected ? 'selected table-active' : ''}">
            <td class="font-monospace text-secondary text-nowrap">${escapeHtml(e.timestamp)}</td>
            <td><span class="badge ${badgeClass} text-uppercase px-2 py-1">${escapeHtml(e.level)}</span></td>
            <td class="text-center font-monospace">${escapeHtml(eidStr)}</td>
            <td class="text-truncate text-info" style="max-width: 160px;" title="${escapeHtml(e.provider || e.source)}">${escapeHtml(e.provider || e.source)}</td>
            <td class="text-center font-monospace text-muted">${escapeHtml(pidStr)}</td>
            <td class="font-monospace text-light" style="word-break: break-word;">${escapeHtml(e.message)}</td>
          </tr>
        `;
      }).join('');

      tableBody.querySelectorAll('tr').forEach((row) => {
        row.onclick = () => {
          const idx = parseInt(row.getAttribute('data-index') || '0', 10);
          selectedEvent = entriesToRender[idx];
          tableBody.querySelectorAll('tr').forEach(r => r.classList.remove('selected', 'table-active'));
          row.classList.add('selected', 'table-active');
          showEventModal(selectedEvent);
        };
      });
    }
  }

  async function loadIncidentsView() {
    const listEl = document.getElementById('slc-incidents-list');
    if (!listEl) return;
    listEl.innerHTML = `<div class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-info me-2"></div>Correlating incident cascades...</div>`;

    try {
      const res = await fetch('/api/v1/system_logs/incidents?window_seconds=25.0');
      if (!res.ok) return;
      const data = await res.json();
      const incidents = data.incidents || [];

      if (incidents.length === 0) {
        listEl.innerHTML = `<div class="card bg-dark border-secondary p-4 text-center text-muted">No fault cascades or correlated incidents detected in the active timeframe.</div>`;
        return;
      }

      listEl.innerHTML = incidents.map((inc) => `
        <div class="card bg-dark border-secondary mb-3 shadow-sm">
          <div class="card-header bg-black d-flex justify-content-between align-items-center">
            <span class="fw-bold text-info"><i class="bi bi-lightning-charge me-1"></i>${escapeHtml(inc.title)}</span>
            <span class="badge ${getSeverityClass(inc.severity)}">${escapeHtml(inc.severity)}</span>
          </div>
          <div class="card-body">
            <div class="row g-2 mb-2 small text-muted font-monospace">
              <div class="col-sm-4">Window: ${escapeHtml(inc.start_time)} (${inc.duration_seconds}s)</div>
              <div class="col-sm-4">Primary: ${escapeHtml(inc.primary_source)}</div>
              <div class="col-sm-4">Events Count: ${inc.events_count}</div>
            </div>
            <p class="small text-light mb-2"><strong class="text-warning">Root Cause:</strong> ${escapeHtml(inc.root_cause_hint)}</p>
            <p class="small text-muted mb-0">${escapeHtml(inc.summary)}</p>
          </div>
        </div>
      `).join('');
    } catch (err) {
      listEl.innerHTML = `<div class="alert alert-danger">Error retrieving incidents: ${err.message}</div>`;
    }
  }

  async function loadTimelineView() {
    const listEl = document.getElementById('slc-timeline-list');
    if (!listEl) return;

    try {
      const res = await fetch('/api/v1/system_logs/timeline');
      if (!res.ok) return;
      const data = await res.json();
      const histogram = data.histogram || [];

      if (histogram.length === 0) {
        listEl.innerHTML = `<div class="card bg-dark border-secondary p-4 text-center text-muted">No timeline data available.</div>`;
        return;
      }

      listEl.innerHTML = histogram.map((h) => `
        <div class="d-flex justify-content-between align-items-center p-2 mb-2 bg-dark rounded border border-secondary">
          <span class="font-monospace text-info">${escapeHtml(h.time)}</span>
          <div class="d-flex align-items-center gap-2">
            <span class="badge bg-secondary">Total: ${h.total}</span>
            <span class="badge badge-err">Errors: ${h.errors}</span>
            <span class="badge badge-warn">Warnings: ${h.warnings}</span>
            <span class="badge badge-inf">Info: ${h.info}</span>
          </div>
        </div>
      `).join('');
    } catch (err) {
      listEl.innerHTML = `<div class="alert alert-danger">Error loading timeline: ${err.message}</div>`;
    }
  }

  async function loadAuditView() {
    const contentEl = document.getElementById('slc-audit-content');
    if (!contentEl) return;

    const hoursSelect = document.getElementById('slc-hours-select');
    const limitSelect = document.getElementById('slc-limit-select');
    const hours = hoursSelect ? hoursSelect.value : '24';
    const limit = limitSelect ? limitSelect.value : '500';

    contentEl.innerHTML = `
      <div class="text-center py-5 text-muted">
        <div class="spinner-border text-info mb-3" role="status"></div>
        <div class="fw-bold text-light">Выполняется многоуровневый аудит массива логов...</div>
        <div class="small text-secondary mt-1">Фильтрация шума • Шаблонизация • Детекция аномалий • Сжатие данных</div>
      </div>
    `;

    try {
      const url = `/api/v1/system_logs/audit?channel=${encodeURIComponent(currentChannel)}&limit=${limit}&hours=${hours}&file_path=${encodeURIComponent(currentFilePath)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const anomaliesHtml = (data.anomalies || []).map((a) => {
        const badgeClass = getSeverityClass(a.level);
        return `
          <div class="p-2 mb-2 rounded bg-black border border-secondary d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
              <span class="badge ${badgeClass} text-uppercase me-2">${escapeHtml(a.level)}</span>
              <strong class="text-info">${escapeHtml(a.provider)}</strong>
              <span class="text-muted font-monospace small">(ID ${a.event_id})</span>
              <div class="small text-light mt-1 font-monospace" style="word-break: break-word;">${escapeHtml(a.sample)}</div>
              <div class="small text-secondary mt-1"><i class="bi bi-clock me-1"></i>Окно: ${escapeHtml(a.time_window)}</div>
            </div>
            <div class="text-end">
              <span class="badge bg-danger rounded-pill px-3 py-2 fs-6">${a.count}x</span>
            </div>
          </div>
        `;
      }).join('') || `<div class="text-success small p-2"><i class="bi bi-check-circle me-1"></i>Аномалий и критических сбоев не обнаружено.</div>`;

      const clustersHtml = (data.top_clusters || []).map((cl, idx) => {
        const badgeClass = getSeverityClass(cl.level);
        return `
          <tr class="small">
            <td class="text-center font-monospace">${idx + 1}</td>
            <td><span class="badge ${badgeClass}">${escapeHtml(cl.level)}</span></td>
            <td class="text-info text-truncate" style="max-width: 140px;" title="${escapeHtml(cl.provider)}">${escapeHtml(cl.provider)}</td>
            <td class="text-center font-monospace">${cl.event_id || '-'}</td>
            <td class="font-monospace text-light" style="max-width: 320px; word-break: break-word;" title="${escapeHtml(cl.template)}">${escapeHtml(cl.template)}</td>
            <td class="text-center"><span class="badge bg-secondary font-monospace">${cl.count}</span></td>
            <td class="small text-secondary font-monospace text-nowrap">${escapeHtml(cl.first_seen)}</td>
          </tr>
        `;
      }).join('');

      const totalScanned = data.total_analyzed ?? data.total_scanned ?? 0;
      const uniqueCount = data.unique_patterns_count ?? (data.top_clusters ? data.top_clusters.length : 0);
      const redundancyPct = data.redundancy_pct !== undefined ? `${data.redundancy_pct.toFixed(1)}%` : (data.compression_ratio || '0%');
      const errSum = (data.error_count || 0) + (data.critical_count || 0);
      const warnSum = data.warning_count || 0;
      const summaryText = data.strategy_rationale || data.executive_summary || `Стратегия обработки: ${data.strategy || 'Стандартная'}. Найдено ${uniqueCount} ключевых шаблонов.`;

      contentEl.innerHTML = `
        <div class="card bg-dark border-info mb-2 shadow-sm">
          <div class="card-header bg-black text-info fw-bold py-1 px-3 d-flex justify-content-between align-items-center small">
            <span><i class="bi bi-cpu me-1"></i>Сводка аудита: ${escapeHtml(data.channel)}</span>
            <span class="badge bg-info text-dark font-monospace">Дублирование: ${redundancyPct}</span>
          </div>
          <div class="card-body p-2">
            <div class="row g-2 text-center mb-2">
              <div class="col-sm-3 col-6">
                <div class="p-1 rounded bg-black border border-secondary">
                  <div class="small text-muted" style="font-size: 0.72rem;">Просканировано</div>
                  <div class="fs-5 fw-bold text-light font-monospace">${totalScanned}</div>
                </div>
              </div>
              <div class="col-sm-3 col-6">
                <div class="p-1 rounded bg-black border border-secondary">
                  <div class="small text-muted" style="font-size: 0.72rem;">Шаблонов</div>
                  <div class="fs-5 fw-bold text-info font-monospace">${uniqueCount}</div>
                </div>
              </div>
              <div class="col-sm-3 col-6">
                <div class="p-1 rounded bg-black border border-secondary">
                  <div class="small text-muted" style="font-size: 0.72rem;">Ошибок / Сбоев</div>
                  <div class="fs-5 fw-bold text-danger font-monospace">${errSum}</div>
                </div>
              </div>
              <div class="col-sm-3 col-6">
                <div class="p-1 rounded bg-black border border-secondary">
                  <div class="small text-muted" style="font-size: 0.72rem;">Предупреждений</div>
                  <div class="fs-5 fw-bold text-warning font-monospace">${warnSum}</div>
                </div>
              </div>
            </div>
            <p class="mb-0 text-light small"><i class="bi bi-info-circle text-info me-1"></i>${escapeHtml(summaryText)}</p>
          </div>
        </div>

        <div class="card bg-dark border-secondary mb-2 shadow-sm">
          <div class="card-header bg-black text-warning fw-bold py-1 px-3 small">
            <i class="bi bi-exclamation-triangle me-1"></i>Обнаруженные аномалии и всплески
          </div>
          <div class="card-body p-2">
            ${anomaliesHtml}
          </div>
        </div>

        <div class="card bg-dark border-secondary">
          <div class="card-header bg-black text-light fw-bold d-flex justify-content-between align-items-center">
            <span><i class="bi bi-collection me-2"></i>Топ шаблонов событий (Дедупликация)</span>
            <span class="small text-muted">Топ 10 кластеров</span>
          </div>
          <div class="table-responsive">
            <table class="table slc-table mb-0">
              <thead>
                <tr>
                  <th style="width: 40px;">#</th>
                  <th style="width: 80px;">Уровень</th>
                  <th style="width: 140px;">Поставщик</th>
                  <th style="width: 60px;">ID</th>
                  <th>Шаблон сообщения (Masked)</th>
                  <th style="width: 70px;" class="text-center">Кол-во</th>
                  <th style="width: 140px;">Впервые</th>
                </tr>
              </thead>
              <tbody>
                ${clustersHtml}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      contentEl.innerHTML = `<div class="alert alert-danger">Ошибка проведения аудита: ${escapeHtml(err.message)}</div>`;
    }
  }

  async function performRAGSearch() {
    const inputEl = document.getElementById('slc-rag-input');
    const resultsEl = document.getElementById('slc-rag-results');
    if (!inputEl || !resultsEl) return;

    const query = inputEl.value.trim();
    if (!query) return;

    resultsEl.innerHTML = `<div class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-info me-2"></div>Поиск по динамическому RAG-индексу...</div>`;

    try {
      const res = await fetch('/api/v1/system_logs/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, channel: currentChannel, top_k: 6 }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const results = data.results || [];

      if (results.length === 0) {
        resultsEl.innerHTML = `
          <div class="card bg-dark border-secondary p-4 text-center text-muted">
            По запросу «${escapeHtml(query)}» ничего не найдено в RAG-индексе. Попробуйте нажать «Перестроить RAG-индекс».
          </div>
        `;
        return;
      }

      resultsEl.innerHTML = results.map((r) => {
        const badgeClass = getSeverityClass(r.meta?.level || 'info');
        return `
          <div class="card bg-dark border-secondary mb-3 shadow-sm">
            <div class="card-header bg-black d-flex justify-content-between align-items-center">
              <span class="fw-bold text-info"><i class="bi bi-file-earmark-text me-2"></i>${escapeHtml(r.title)}</span>
              <div class="d-flex align-items-center gap-2">
                <span class="badge ${badgeClass}">${escapeHtml(r.meta?.level || r.type)}</span>
                <span class="badge bg-secondary font-monospace">Score: ${r.relevance_score}</span>
              </div>
            </div>
            <div class="card-body">
              <pre class="bg-black text-light p-3 rounded font-monospace small mb-0" style="white-space: pre-wrap; word-break: break-word;">${escapeHtml(r.text)}</pre>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      resultsEl.innerHTML = `<div class="alert alert-danger">Ошибка поиска RAG: ${escapeHtml(err.message)}</div>`;
    }
  }

  async function rebuildRAGIndex() {
    const resultsEl = document.getElementById('slc-rag-results');
    if (!resultsEl) return;
    resultsEl.innerHTML = `<div class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-info me-2"></div>Перестроение динамического RAG-индекса для «${escapeHtml(currentChannel)}»...</div>`;

    try {
      const res = await fetch(`/api/v1/system_logs/rag/build?channel=${encodeURIComponent(currentChannel)}&limit=500&hours=24&file_path=${encodeURIComponent(currentFilePath)}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      resultsEl.innerHTML = `
        <div class="alert alert-success d-flex align-items-center gap-2">
          <i class="bi bi-check-circle-fill fs-5"></i>
          <div>
            <strong>RAG-индекс успешно обновлен!</strong> Добавлено ${data.chunks_added} чанков (Всего в индексе: ${data.total_index_chunks}).
            <div class="small mt-1 text-light">${escapeHtml(data.executive_summary)}</div>
          </div>
        </div>
      `;
    } catch (err) {
      resultsEl.innerHTML = `<div class="alert alert-danger">Ошибка перестроения RAG: ${escapeHtml(err.message)}</div>`;
    }
  }

  function showEventModal(entry) {
    if (!entry) return;
    selectedEvent = entry;

    const modalEl = document.getElementById('slc-event-detail-modal');
    if (!modalEl) return;

    const setElTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val || '';
    };

    setElTxt('slc-modal-time', entry.timestamp);
    const lvlEl = document.getElementById('slc-modal-level');
    if (lvlEl) lvlEl.innerHTML = `<span class="badge ${getSeverityClass(entry.level)}">${escapeHtml(entry.level)}</span>`;
    setElTxt('slc-modal-id', entry.event_id > 0 ? String(entry.event_id) : '-');
    setElTxt('slc-modal-provider', entry.provider || entry.source);
    setElTxt('slc-modal-computer', entry.computer || 'Localhost');
    setElTxt('slc-modal-pid', entry.process_id > 0 ? String(entry.process_id) : '-');
    setElTxt('slc-modal-channel', entry.channel || currentChannel);
    setElTxt('slc-modal-message', entry.message);

    const aiExplanation = document.getElementById('slc-modal-ai-explanation');
    if (aiExplanation) {
      aiExplanation.innerHTML = `Нажмите «Анализ контекста», чтобы провести диагностику выбранной записи и сопутствующих событий.`;
    }

    const diagnoseBtn = document.getElementById('btn-slc-modal-diagnose');
    if (diagnoseBtn) {
      diagnoseBtn.onclick = async () => {
        aiExplanation.innerHTML = `<div class="spinner-border spinner-border-sm text-info me-2"></div>Анализ выбранной записи...`;
        try {
          const res = await fetch('/api/v1/system_logs/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              target_timestamp: entry.timestamp,
              window_minutes: 5,
              channel: entry.channel || currentChannel,
              event_id: entry.event_id || 0,
              provider: entry.provider || entry.source || '',
              level: entry.level || '',
              message: entry.message || '',
              target_entry: entry,
              query_text: `Диагностика события ${entry.provider || entry.source} (ID ${entry.event_id || 0}): ${entry.message || ''}`,
            }),
          });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const report = await res.json();
          aiExplanation.innerHTML = `
            <div class="mb-2"><strong class="text-info">Сводка:</strong> ${escapeHtml(report.summary)}</div>
            <div class="mb-2"><strong class="text-warning">Причина / Анализ:</strong> ${escapeHtml(report.root_cause)}</div>
            <h6 class="small text-uppercase text-muted fw-bold mb-1">Рекомендации:</h6>
            <ul class="mb-0 ps-3">
              ${(report.recommendations || []).map(r => `<li>${escapeHtml(r)}</li>`).join('')}
            </ul>
          `;
        } catch (err) {
          aiExplanation.innerHTML = `<div class="text-danger">Ошибка диагностики: ${escapeHtml(err.message)}</div>`;
        }
      };
    }

    if (window.bootstrap?.Modal) {
      const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
      bsModal.show();
    }
  }

  function exportLogs(format) {
    const level = (document.getElementById('slc-level-select') || {}).value || '';
    const search = (document.getElementById('slc-search-input') || {}).value || '';
    const limit = (document.getElementById('slc-limit-select') || {}).value || '200';
    const hours = (document.getElementById('slc-hours-select') || {}).value || '24';

    const url = `/api/v1/system_logs/export?format=${format}&channel=${encodeURIComponent(currentChannel)}&level=${encodeURIComponent(level)}&search=${encodeURIComponent(search)}&hours=${hours}&limit=${limit}`;
    window.open(url, '_blank');
  }

  // =========================================================================
  // SECTION 6: Master Initializer
  // =========================================================================

  function initSystemControlTab() {
    console.log('[SystemControl] Initializing System Control Center & OS System Logs...');
    fetchStatus();
    loadWizardProfiles();
    fetchAppActivityLogs();

    // Initialize OS log explorer
    performSystemScan().then(() => {
      loadEvents();
    });

    if (!isSCCInitialized) {
      const refreshBtn = document.getElementById('btn-scc-refresh');
      const applyProfBtn = document.getElementById('btn-scc-apply-profile');
      const cleanBtn = document.getElementById('btn-scc-action-clean');
      const sfcBtn = document.getElementById('btn-scc-action-sfc');
      const dismBtn = document.getElementById('btn-scc-action-dism');
      const createRestoreBtn = document.getElementById('btn-scc-create-restore');
      const refreshLogsBtn = document.getElementById('btn-scc-refresh-logs');

      if (refreshBtn) refreshBtn.onclick = () => { fetchStatus(); loadEvents(); fetchAppActivityLogs(); };
      if (refreshLogsBtn) refreshLogsBtn.onclick = () => fetchAppActivityLogs();
      if (applyProfBtn) applyProfBtn.onclick = applyCurrentProfile;

      if (cleanBtn) {
        cleanBtn.onclick = async () => {
          if (confirm('Run safe cleanup on temporary directories and update cache?')) {
            cleanBtn.disabled = true;
            await fetch('/api/system-control/maintenance/cleanup', { method: 'POST' });
            cleanBtn.disabled = false;
            fetchStatus();
            fetchAppActivityLogs();
          }
        };
      }

      if (sfcBtn) {
        sfcBtn.onclick = async () => {
          sfcBtn.disabled = true;
          sfcBtn.innerText = 'Scanning...';
          const res = await fetch('/api/system-control/maintenance/sfc', { method: 'POST' });
          const d = await res.json();
          window.showToast?.(d.message || 'SFC Scan Completed', d.status === 'error' ? 'danger' : 'success') || alert(d.message || 'SFC Scan Completed');
          sfcBtn.disabled = false;
          sfcBtn.innerHTML = '<i class="bi bi-search me-1"></i> Run SFC Integrity Scan';
          fetchAppActivityLogs();
        };
      }

      if (dismBtn) {
        dismBtn.onclick = async () => {
          dismBtn.disabled = true;
          dismBtn.innerText = 'Checking...';
          const res = await fetch('/api/system-control/maintenance/dism', { method: 'POST' });
          const d = await res.json();
          window.showToast?.(d.message || 'DISM Check Completed', d.status === 'error' ? 'danger' : 'success') || alert(d.message || 'DISM Check Completed');
          dismBtn.disabled = false;
          dismBtn.innerHTML = '<i class="bi bi-activity me-1"></i> Check DISM Store';
          fetchAppActivityLogs();
        };
      }

      if (createRestoreBtn) {
        createRestoreBtn.onclick = async () => {
          const desc = prompt('Enter restore point description:', 'System Control Center Checkpoint');
          if (desc) {
            createRestoreBtn.disabled = true;
            const res = await fetch('/api/system-control/restore-points', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ description: desc })
            });
            const d = await res.json();
            window.showToast?.(d.message || 'Restore point created.', d.status === 'error' ? 'danger' : 'success') || alert(d.message || 'Restore point created.');
            createRestoreBtn.disabled = false;
            fetchRestorePoints();
            fetchAppActivityLogs();
          }
        };
      }

      // Policy & Storage Config Modal Button
      const configRestoreBtn = document.getElementById('btn-scc-config-restore');
      if (configRestoreBtn) {
        configRestoreBtn.onclick = loadRestorePolicyModal;
      }

      const savePolicyBtn = document.getElementById('btn-scc-save-restore-policy');
      if (savePolicyBtn) {
        savePolicyBtn.onclick = saveRestorePolicy;
      }

      const pruneNowBtn = document.getElementById('btn-scc-policy-prune-now');
      if (pruneNowBtn) {
        pruneNowBtn.onclick = pruneRestorePointsNow;
      }

      // System Log Center toolbar and listeners
      const scanBtn = document.getElementById('btn-slc-scan');
      if (scanBtn) {
        scanBtn.onclick = () => performSystemScan(true);
      }

      const slcRefreshBtn = document.getElementById('btn-slc-refresh');
      if (slcRefreshBtn) {
        slcRefreshBtn.onclick = loadEvents;
      }

      const jsonExportBtn = document.getElementById('btn-slc-export-json');
      if (jsonExportBtn) {
        jsonExportBtn.onclick = (e) => {
          e.preventDefault();
          exportLogs('json');
        };
      }

      const csvExportBtn = document.getElementById('btn-slc-export-csv');
      if (csvExportBtn) {
        csvExportBtn.onclick = (e) => {
          e.preventDefault();
          exportLogs('csv');
        };
      }

      const modeTabs = document.querySelectorAll('#slc-mode-tabs .nav-link');
      modeTabs.forEach((tab) => {
        tab.onclick = () => {
          modeTabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          currentMode = tab.getAttribute('data-mode') || 'live';
          renderCurrentModeView();
        };
      });

      const auditBtn = document.getElementById('btn-slc-audit');
      if (auditBtn) {
        auditBtn.onclick = () => {
          modeTabs.forEach(t => {
            if (t.getAttribute('data-mode') === 'audit') {
              t.classList.add('active');
            } else {
              t.classList.remove('active');
            }
          });
          currentMode = 'audit';
          renderCurrentModeView();
        };
      }

      const ragSearchBtn = document.getElementById('btn-slc-rag-search');
      if (ragSearchBtn) {
        ragSearchBtn.onclick = performRAGSearch;
      }

      const ragRebuildBtn = document.getElementById('btn-slc-rag-rebuild');
      if (ragRebuildBtn) {
        ragRebuildBtn.onclick = rebuildRAGIndex;
      }

      const ragInput = document.getElementById('slc-rag-input');
      if (ragInput) {
        ragInput.onkeydown = (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            performRAGSearch();
          }
        };
      }

      const askAiBtn = document.getElementById('btn-slc-ask-ai');
      if (askAiBtn) {
        askAiBtn.onclick = () => {
          if (selectedEvent) {
            showEventModal(selectedEvent);
          } else if (cachedEvents.length > 0) {
            selectedEvent = cachedEvents[0];
            showEventModal(selectedEvent);
          }
        };
      }

      const levelSelect = document.getElementById('slc-level-select');
      if (levelSelect) levelSelect.onchange = loadEvents;

      const hoursSelect = document.getElementById('slc-hours-select');
      if (hoursSelect) hoursSelect.onchange = loadEvents;

      const limitSelect = document.getElementById('slc-limit-select');
      if (limitSelect) limitSelect.onchange = loadEvents;

      const eventIdInput = document.getElementById('slc-eventid-input');
      if (eventIdInput) eventIdInput.onchange = loadEvents;

      let searchTimer = null;
      const searchInput = document.getElementById('slc-search-input');
      if (searchInput) {
        searchInput.oninput = () => {
          clearTimeout(searchTimer);
          searchTimer = setTimeout(loadEvents, 350);
        };
      }

      const channelFilterInput = document.getElementById('slc-channel-filter-input');
      if (channelFilterInput) {
        channelFilterInput.oninput = renderChannelsTree;
      }

      const liveSwitch = document.getElementById('slc-live-switch');
      if (liveSwitch) {
        liveSwitch.onchange = () => {
          if (window.registerTabPoller && window.unregisterTabPoller) {
            if (liveSwitch.checked) {
              window.registerTabPoller('tab-system-control_logs', loadEvents, 4000, { immediate: true });
            } else {
              window.unregisterTabPoller('tab-system-control_logs');
            }
          } else {
            if (liveSwitch.checked) {
              liveIntervalTimer = setInterval(loadEvents, 4000);
            } else {
              clearInterval(liveIntervalTimer);
              liveIntervalTimer = null;
            }
          }
        };
      }

      isSCCInitialized = true;
    }
  }

  window.initSystemControlTab = initSystemControlTab;
})();
