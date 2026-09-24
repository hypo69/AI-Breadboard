// =============================================================================
// Process Name: Windows System Control Center Web Controller
// =============================================================================
// Description:
//   Client-side JavaScript controller for the System Control Center tab in
//   the administrative web interface.
//
// File: main.js
// Project: ai-breadboard
// Package: src.api.webinterface.system_control_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function () {
  let isSCCInitialized = false;
  let activeProfileSteps = [];

  // Helper to format timestamps
  function formatTime(isoStr) {
    if (!isoStr) return '-';
    try {
      return new Date(isoStr).toLocaleTimeString();
    } catch {
      return isoStr.slice(11, 19);
    }
  }

  // Fetch full status and update cards & monitoring table
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

      // Top Cards
      const sys = data.system || {};
      const sec = data.security || {};
      const rest = data.restore || {};
      const disk = data.disk || {};
      const pwr = data.power || {};
      const upd = data.update || {};

      const cardOs = document.getElementById('scc-card-os');
      const cardHost = document.getElementById('scc-card-host');
      const cardSec = document.getElementById('scc-card-security');
      const cardFw = document.getElementById('scc-card-firewall');
      const cardRest = document.getElementById('scc-card-restore');
      const cardProt = document.getElementById('scc-card-protection');
      const cardStor = document.getElementById('scc-card-storage');
      const cardClean = document.getElementById('scc-card-cleanable');

      if (cardOs) cardOs.innerText = `${sys.os_caption || 'Windows 11'} (${sys.architecture || 'x64'})`;
      if (cardHost) cardHost.innerText = `Host: ${sys.hostname || 'LOCAL'}`;
      if (cardSec) {
        cardSec.innerText = sec.defender_enabled ? 'Active & Protected' : 'Attention Required';
        cardSec.className = sec.defender_enabled ? 'scc-value text-success mt-1' : 'scc-value text-warning mt-1';
      }
      if (cardFw) cardFw.innerText = `Firewall: ${sec.firewall_overall_enabled ? 'ON' : 'OFF'} | UAC: ${sec.uac_enabled ? 'ON' : 'OFF'}`;
      if (cardRest) cardRest.innerText = `${rest.restore_points_count || 0} Checkpoints`;
      if (cardProt) cardProt.innerText = `Protection: ${rest.system_protection_enabled ? 'Active' : 'Disabled'}`;
      if (cardStor) cardStor.innerText = `${disk.system_drive_free_gb || 0} GB Free`;
      if (cardClean) {
        const cleanMb = disk.cleanup_estimate?.total_cleanable_mb || 0;
        cardClean.innerText = `Cleanable: ~${cleanMb} MB`;
        const cleanEstimateTxt = document.getElementById('scc-clean-estimate-txt');
        if (cleanEstimateTxt) cleanEstimateTxt.innerText = `Cleanable: ~${cleanMb} MB`;
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

      // Disks Table
      const disksTbody = document.getElementById('scc-disks-tbody');
      const disksCountBadge = document.getElementById('scc-disks-count');
      const parts = disk.partitions || [];
      if (disksCountBadge) disksCountBadge.innerText = `${parts.length} Drives`;

      if (disksTbody) {
        if (parts.length === 0) {
          disksTbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-3">No active drives detected</td></tr>';
        } else {
          disksTbody.innerHTML = parts.map((p, idx) => `
            <tr class="scc-disk-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-диагностики диска">
              <td class="fw-bold text-white"><i class="bi bi-hdd me-1"></i> ${p.mountpoint}</td>
              <td class="font-monospace text-muted">${p.fstype}</td>
              <td>${p.total_gb} GB</td>
              <td>${p.used_gb} GB</td>
              <td class="text-success fw-semibold">${p.free_gb} GB</td>
              <td>
                <div class="d-flex align-items-center gap-2">
                  <div class="progress flex-grow-1" style="height: 6px; background: #334155;">
                    <div class="progress-bar ${p.percent_used > 85 ? 'bg-danger' : (p.percent_used > 70 ? 'bg-warning' : 'bg-primary')}" style="width: ${p.percent_used}%;"></div>
                  </div>
                  <span class="small font-monospace">${p.percent_used}%</span>
                </div>
              </td>
              <td><span class="badge scc-badge-secure">${p.health_status}</span></td>
            </tr>
          `).join('');

          disksTbody.querySelectorAll('.scc-disk-row').forEach(row => {
            row.onclick = () => {
              const idx = parseInt(row.getAttribute('data-idx'), 10);
              const p = parts[idx];
              if (!p) return;
              if (window.AITableModal) {
                window.AITableModal.show({
                  icon: '💾',
                  title: `Диск ${p.mountpoint}`,
                  subtitle: `Файловая система: ${p.fstype} | Здоровье: ${p.health_status}`,
                  tableType: 'disk',
                  badges: [
                    { text: p.health_status || 'OK', class: 'badge bg-success' },
                    { text: `${p.percent_used}% занято`, class: p.percent_used > 80 ? 'badge bg-warning text-dark' : 'badge bg-info text-dark' }
                  ],
                  metadata: [
                    { label: 'Точка монтирования', value: p.mountpoint },
                    { label: 'Файловая система', value: p.fstype },
                    { label: 'Общий объем', value: `${p.total_gb} GB` },
                    { label: 'Использовано', value: `${p.used_gb} GB` },
                    { label: 'Свободно', value: `${p.free_gb} GB` },
                    { label: 'Процент заполнения', value: `${p.percent_used}%` },
                    { label: 'Статус диска', value: p.health_status || 'Исправен' }
                  ],
                  rawTitle: 'Параметры накопителя',
                  rawContent: JSON.stringify(p, null, 2),
                  requestData: {
                    mountpoint: p.mountpoint,
                    fstype: p.fstype,
                    total_gb: p.total_gb,
                    free_gb: p.free_gb,
                    percent: p.percent_used
                  }
                });
              }
            };
          });
        }
      }

      // Restore points table
      fetchRestorePoints();
    } catch (e) {
      console.error('[SystemControl] Failed to fetch status:', e);
    }
  }

  // Helper to format restore point types into friendly badges
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

  // Helper to format CIM timestamps to readable datetime
  function formatRestoreTime(rawTime) {
    if (!rawTime) return '-';
    const s = String(rawTime).trim();
    if (s.length >= 14 && /^\d{14}/.test(s)) {
      return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)} ${s.slice(8, 10)}:${s.slice(10, 12)}:${s.slice(12, 14)}`;
    }
    return s;
  }

  // Fetch restore points
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

  // Load Post-Install Wizard Checklist
  async function loadWizardProfiles() {
    try {
      const res = await fetch('/api/system-control/profiles');
      if (!res.ok) return;
      const data = await res.json();
      const profiles = data.profiles || [];
      const sel = document.getElementById('scc-profile-select');
      const container = document.getElementById('scc-wizard-steps-container');

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

    container.innerHTML = activeProfileSteps.map((s, idx) => `
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

  // Apply Selected Profile
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
        fetchLogs();
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

  // Activity Log
  async function fetchLogs() {
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
            <td class="fw-bold font-monospace text-info">${l.action}</td>
            <td class="small text-white">${l.target}</td>
            <td><span class="badge ${l.status === 'SUCCESS' ? 'scc-badge-secure' : (l.status === 'WARNING' ? 'scc-badge-warn' : 'scc-badge-danger')}">${l.status}</span></td>
            <td class="small text-muted text-truncate" style="max-width: 250px;">${l.details}</td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.error('[SystemControl] Failed to fetch logs:', e);
    }
  }

  // Interactive Tab Initializer
  function initSystemControlTab() {
    console.log('[SystemControl] Initializing System Control Center Web Tab...');
    fetchStatus();
    loadWizardProfiles();
    fetchLogs();

    if (!isSCCInitialized) {
      const refreshBtn = document.getElementById('btn-scc-refresh');
      const applyProfBtn = document.getElementById('btn-scc-apply-profile');
      const cleanBtn = document.getElementById('btn-scc-action-clean');
      const sfcBtn = document.getElementById('btn-scc-action-sfc');
      const dismBtn = document.getElementById('btn-scc-action-dism');
      const createRestoreBtn = document.getElementById('btn-scc-create-restore');
      const refreshLogsBtn = document.getElementById('btn-scc-refresh-logs');

      if (refreshBtn) refreshBtn.onclick = () => { fetchStatus(); fetchLogs(); };
      if (refreshLogsBtn) refreshLogsBtn.onclick = () => fetchLogs();

      if (applyProfBtn) applyProfBtn.onclick = applyCurrentProfile;

      if (cleanBtn) {
        cleanBtn.onclick = async () => {
          if (confirm('Run safe cleanup on temporary directories and update cache?')) {
            cleanBtn.disabled = true;
            await fetch('/api/system-control/maintenance/cleanup', { method: 'POST' });
            cleanBtn.disabled = false;
            fetchStatus();
            fetchLogs();
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
          fetchLogs();
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
          fetchLogs();
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
            fetchLogs();
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

      isSCCInitialized = true;
    }
  }

  // Load restore policy and quota into modal
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

      // Storage telemetry
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

  // Save restore policy and quota
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
      fetchLogs();
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

  // Prune extra restore points now
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
      fetchLogs();
    } catch (e) {
      console.error('[SystemControl] Failed to prune restore points:', e);
    }
  }

  window.initSystemControlTab = initSystemControlTab;
})();
