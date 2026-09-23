// =============================================================================
// Process Name: About System Tab Web Controller
// =============================================================================
// Description:
//   Client-side JavaScript controller for the About System tab.
//   Provides real-time host telemetry, system identity & locale parameters,
//   AIDA64-like hardware tree, LibreHardwareMonitor sensors, live top processes,
//   disk volumes and security status.
//
// File: main.js
// Package: src.api.webgui.about_system_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function () {
  let hardwareData = [];
  let currentSensors = [];
  let currentProcesses = [];
  let currentDisks = [];
  let activeSensorFilter = 'all';
  let isLiveActive = true;
  let liveIntervalId = null;
  let isUpdating = false;
  let hasAutoRunAiDiagnostics = false;
  let isAiRunning = false;

  async function apiFetch(url, options = {}) {
    if (window.api && typeof window.api.fetch === 'function') {
      return await window.api.fetch(url, options);
    }
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text !== null && text !== undefined ? String(text) : '--';
  }

  function setHtml(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  async function initAboutSystemTab() {
    console.log('[AboutSystemTab] Initializing tab controller...');
    bindEvents();
    bindAIEvents();
    updateLocalClock();

    // Fast initial render from quick summary (<100ms) so tab is never empty
    fetchSystemSummary().catch(err => console.warn('[AboutSystemTab] Quick summary error:', err));
    fetchHardwareSensors().catch(err => console.warn('[AboutSystemTab] Sensors error:', err));
    fetchHardwareSpec().catch(err => console.warn('[AboutSystemTab] Hardware spec error:', err));

    // Async background fetches for heavier diagnostics without blocking UI
    fetchSystemControlStatus().catch(err => console.warn('[AboutSystemTab] Control status error:', err));

    // Execute AI Diagnostics only ONCE on system start / initial tab load
    if (!hasAutoRunAiDiagnostics) {
      hasAutoRunAiDiagnostics = true;
      runAIDiagnostics(false).catch(err => console.warn('[AboutSystemTab] Initial AI diagnose error:', err));
    }

    // Start live telemetry ticker
    startLiveStream();
  }
  window.initAboutSystemTab = initAboutSystemTab;

  function updateLocalClock() {
    const clockEl = document.getElementById('about-ident-time-badge');
    if (clockEl) {
      const now = new Date();
      clockEl.textContent = `Локальное время: ${now.toLocaleTimeString()}`;
    }
  }

  function startLiveStream() {
    if (liveIntervalId) clearInterval(liveIntervalId);
    liveIntervalId = setInterval(async () => {
      updateLocalClock();
      if (isLiveActive && !isUpdating) {
        await pollLiveTelemetry();
      }
    }, 3000);
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('btn-about-sys-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = async () => {
        btnRefresh.disabled = true;
        const icon = btnRefresh.querySelector('i');
        if (icon) icon.classList.add('spin-animation');
        await refreshAllData();
        if (icon) icon.classList.remove('spin-animation');
        btnRefresh.disabled = false;
      };
    }

    const btnLiveToggle = document.getElementById('btn-about-sys-live-toggle');
    if (btnLiveToggle) {
      btnLiveToggle.onclick = () => {
        isLiveActive = !isLiveActive;
        const icon = document.getElementById('icon-about-sys-live');
        const txt = document.getElementById('txt-about-sys-live');
        const liveBadge = document.getElementById('about-sys-live-badge');
        if (isLiveActive) {
          if (icon) icon.className = 'bi bi-pause-fill me-1';
          if (txt) txt.textContent = 'Пауза';
          if (liveBadge) {
            liveBadge.className = 'badge rounded-pill bg-info-subtle text-info border border-info px-2.5 py-1';
            liveBadge.textContent = '● Live Host Telemetry';
          }
        } else {
          if (icon) icon.className = 'bi bi-play-fill me-1';
          if (txt) txt.textContent = 'Возобновить';
          if (liveBadge) {
            liveBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-2.5 py-1';
            liveBadge.textContent = '⏸ Stream Paused';
          }
        }
      };
    }

    const btnExpandAll = document.getElementById('btn-about-sys-expand-all');
    if (btnExpandAll) {
      btnExpandAll.onclick = () => {
        document.querySelectorAll('.about-sys-tree-body').forEach(b => b.classList.remove('d-none'));
        document.querySelectorAll('.about-sys-chevron').forEach(c => c.textContent = '▲');
      };
    }

    const btnCollapseAll = document.getElementById('btn-about-sys-collapse-all');
    if (btnCollapseAll) {
      btnCollapseAll.onclick = () => {
        document.querySelectorAll('.about-sys-tree-body').forEach(b => b.classList.add('d-none'));
        document.querySelectorAll('.about-sys-chevron').forEach(c => c.textContent = '▼');
      };
    }

    const treeSearch = document.getElementById('about-sys-search');
    if (treeSearch) {
      treeSearch.oninput = () => {
        renderHardwareTree(hardwareData, treeSearch.value.trim().toLowerCase());
      };
    }

    const sensorSearch = document.getElementById('about-sensor-search');
    if (sensorSearch) {
      sensorSearch.oninput = () => {
        renderSensorsList(currentSensors);
      };
    }

    const procSearch = document.getElementById('about-proc-search');
    if (procSearch) {
      procSearch.oninput = () => {
        renderProcessesTable(currentProcesses);
      };
    }

    // Sensor category filter buttons
    const filterGroup = document.getElementById('about-sensor-filter-group');
    if (filterGroup) {
      filterGroup.querySelectorAll('button').forEach(btn => {
        btn.onclick = () => {
          filterGroup.querySelectorAll('button').forEach(b => {
            b.classList.remove('active', 'btn-outline-info');
            b.classList.add('btn-outline-secondary');
          });
          btn.classList.add('active', 'btn-outline-info');
          btn.classList.remove('btn-outline-secondary');
          activeSensorFilter = btn.getAttribute('data-sensor-cat') || 'all';
          renderSensorsList(currentSensors);
        };
      });
    }
  }

  async function refreshAllData() {
    isUpdating = true;
    try {
      await Promise.allSettled([
        fetchSystemSummary(),
        fetchSystemControlStatus(),
        fetchHardwareSpec(),
        fetchHardwareSensors()
      ]);
    } finally {
      isUpdating = false;
    }
  }

  async function pollLiveTelemetry() {
    isUpdating = true;
    try {
      await Promise.allSettled([
        fetchSystemSummary(true),
        fetchHardwareSensors(true)
      ]);
    } finally {
      isUpdating = false;
    }
  }

  async function fetchSystemSummary(isLightPoll = false) {
    try {
      const snap = await apiFetch('/api/v1/system/summary?process_limit=25');
      if (!snap) return;

      // 1. Identity & Locale Block
      const host = snap.hostname || 'DELL-VOSTRO';
      const user = snap.username || 'onela';
      const lang = snap.system_language || 'Русский (Россия) [ru-RU]';
      const userLoc = snap.user_locale || 'ru-RU';
      const sysLoc = snap.system_locale || 'ru-RU';
      const tz = snap.timezone || 'UTC+03:00';
      const cp = snap.codepage || 'UTF-8 (ACP: 65001)';
      const inputs = Array.isArray(snap.input_languages) && snap.input_languages.length > 0
        ? snap.input_languages.join(', ')
        : 'Русский (RU), English (US), עברית (IL)';
      const osBuild = snap.os_build ? `${snap.os_name || 'Windows 11'} (Build ${snap.os_build})` : (snap.os_name || 'Windows 11');

      setText('about-ident-hostname', host);
      setText('about-ident-domain', `Workgroup / Host: ${host}`);
      setText('about-ident-username', user);
      setText('about-ident-language', lang);
      setText('about-ident-locales', `Локали: User: ${userLoc} | Sys: ${sysLoc}`);
      setText('about-ident-timezone', tz);
      setText('about-ident-codepage', `Кодировка: ${cp}`);
      setText('about-ident-inputs', inputs);
      setText('about-ident-os-build', osBuild);
      setText('about-ident-install-date', snap.os_install_date || 'Не определена');

      // Top KPI Card 1: Operating System
      setText('about-kpi-os-title', `${snap.os_name || 'Windows 11'} (${snap.cpu?.architecture || 'AMD64'})`);
      setText('about-kpi-os-host', `Host: ${host}`);

      // 2. Telemetry Live Bar
      if (snap.cpu) {
        const cpuPct = snap.cpu.total_percent || 0;
        setText('about-telemetry-cpu-val', `${cpuPct.toFixed(1)}%`);
        const cpuBar = document.getElementById('about-telemetry-cpu-bar');
        if (cpuBar) {
          cpuBar.style.width = `${Math.min(100, Math.max(0, cpuPct))}%`;
          cpuBar.className = cpuPct > 85 ? 'about-sys-progress-bar bg-danger' : (cpuPct > 60 ? 'about-sys-progress-bar bg-warning' : 'about-sys-progress-bar bg-info');
        }
        const freqTxt = snap.cpu.frequency_mhz ? `${snap.cpu.frequency_mhz} MHz` : '';
        setText('about-telemetry-cpu-freq', freqTxt);
        const cores = snap.cpu.physical_cores || 6;
        const threads = snap.cpu.logical_cores || 12;
        setText('about-telemetry-cpu-cores', `${cores} физ. / ${threads} Потоков`);

        // Specification Table CPU
        setText('about-spec-cpu', `${snap.cpu.model || 'Intel Processor'} (${threads} logical cores)`);
      }

      if (snap.memory) {
        const total = Number(snap.memory.total_gb || 0).toFixed(1);
        const used = Number(snap.memory.used_gb || 0).toFixed(1);
        const avail = Number(snap.memory.available_gb || 0).toFixed(1);
        const pct = snap.memory.percent || 0;

        setText('about-telemetry-ram-val', `${used} / ${total} GB`);
        setText('about-telemetry-ram-sub', `${pct}% занято (${avail} GB свободно)`);
        const ramBar = document.getElementById('about-telemetry-ram-bar');
        if (ramBar) {
          ramBar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
          ramBar.className = pct > 85 ? 'about-sys-progress-bar bg-danger' : (pct > 65 ? 'about-sys-progress-bar bg-warning' : 'about-sys-progress-bar bg-info');
        }

        // Specification Table RAM
        setText('about-spec-ram', `${avail} GB free / ${total} GB total (${pct}% used)`);
      }

      if (Array.isArray(snap.gpus) && snap.gpus.length > 0) {
        const gpu = snap.gpus[0];
        setText('about-telemetry-gpu-name', gpu.name || 'GPU');
        const vramTxt = gpu.memory_total_gb ? `VRAM: ${Number(gpu.memory_total_gb).toFixed(1)} GB` : 'VRAM: N/A';
        const loadTxt = gpu.load_percent !== null && gpu.load_percent !== undefined ? ` | Нагрузка: ${gpu.load_percent}%` : '';
        setText('about-telemetry-gpu-vram', `${vramTxt}${loadTxt}`);

        const badgeGpu = document.getElementById('about-telemetry-gpu-badge');
        if (badgeGpu) {
          const caps = [];
          if (gpu.has_cuda) caps.push('CUDA');
          if (gpu.has_directml) caps.push('DirectML');
          badgeGpu.textContent = caps.length > 0 ? caps.join(' + ') : 'Active GPU';
        }
      }

      if (snap.disk_io) {
        const rKbs = Math.round((snap.disk_io.read_bytes_per_sec || 0) / 1024);
        const wKbs = Math.round((snap.disk_io.write_bytes_per_sec || 0) / 1024);
        const totalMb = (((snap.disk_io.read_bytes_per_sec || 0) + (snap.disk_io.write_bytes_per_sec || 0)) / (1024 * 1024)).toFixed(2);
        setText('about-telemetry-disk-val', `${totalMb} MB/s`);
        setText('about-telemetry-disk-rates', `Чтение: ${rKbs} КБ/с | Запись: ${wKbs} КБ/с`);
      }

      // Specification Table general
      setText('about-spec-host', host);
      setText('about-spec-os', osBuild);
      if (snap.uptime_seconds) {
        const sec = snap.uptime_seconds;
        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        setText('about-spec-uptime', `Uptime: ${h}h ${m}m`);
      }

      // 3. Disks Table
      if (Array.isArray(snap.disks) && snap.disks.length > 0) {
        currentDisks = snap.disks;
        renderDisksTable(snap.disks);

        // Update Top KPI Storage C:
        const cDrive = snap.disks.find(d => (d.device || '').toUpperCase().startsWith('C')) || snap.disks[0];
        if (cDrive) {
          const freeGb = Number(cDrive.free_gb || 0).toFixed(1);
          const totalGb = Number(cDrive.total_gb || 0).toFixed(1);
          setText('about-kpi-stor-title', `${freeGb} GB Free / ${totalGb} GB`);
        }
      }

      // 4. Monitors & Displays Block
      if (Array.isArray(snap.monitors) && snap.monitors.length > 0) {
        const monShorts = snap.monitors.map(m => {
          const prim = m.is_primary ? ' [Основной]' : '';
          return `${m.name || 'Monitor'} (${m.width}x${m.height}@${m.frequency_hz}Hz${prim})`;
        });
        setText('about-ident-monitors', monShorts.join(', '));
        setText('about-spec-monitors', monShorts.join(', '));
      }

      // 5. Windows Updates Block
      if (snap.updates) {
        const kbCount = snap.updates.installed_kb_count ? ` (${snap.updates.installed_kb_count} KBs)` : '';
        const updTxt = `${snap.updates.status || 'Up to date'}${kbCount}`;
        setText('about-ident-updates', updTxt);
        setText('about-spec-update', updTxt);
      }

      // 6. Processes Table
      if (Array.isArray(snap.top_processes)) {
        currentProcesses = snap.top_processes;
        renderProcessesTable(snap.top_processes);
      }

    } catch (e) {
      console.warn('[AboutSystemTab] fetchSystemSummary warning:', e);
    }
  }

  async function fetchSystemControlStatus() {
    try {
      const res = await apiFetch('/api/system-control/status');
      if (!res) return;

      const isElevated = res.is_elevated;
      const privBadge = document.getElementById('about-sys-privilege-badge');
      if (privBadge) {
        if (isElevated) {
          privBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-2.5 py-1';
          privBadge.textContent = '🛡️ Administrator Access';
        } else {
          privBadge.className = 'badge rounded-pill bg-secondary-subtle text-secondary border border-secondary px-2.5 py-1';
          privBadge.textContent = '👁️ Standard User Mode';
        }
      }
      setText('about-ident-privilege', isElevated ? 'Права: Администратор (Full Access)' : 'Права: Стандартный пользователь');

      // Security Details
      const sec = res.security || {};
      const rest = res.restore || {};
      const disk = res.disk || {};
      const pwr = res.power || {};
      const upd = res.update || {};

      // KPI 2: Security & Defender
      const defActive = sec.defender_enabled !== false;
      setText('about-kpi-sec-title', defActive ? 'Active & Protected' : 'Attention Required');
      const fwOk = sec.firewall_overall_enabled !== false;
      const uacOk = sec.uac_enabled !== false;
      setText('about-kpi-sec-sub', `Firewall: ${fwOk ? 'ON' : 'OFF'} | UAC: ${uacOk ? 'ON' : 'OFF'}`);

      // KPI 3: System Protection
      const countPoints = rest.restore_points_count || 0;
      setText('about-kpi-prot-title', `${countPoints} Checkpoints`);
      setText('about-kpi-prot-sub', `Protection: ${rest.system_protection_enabled ? 'Active' : 'Disabled'}`);

      // KPI 4: Cleanable estimate & Total Disk Size
      const cleanMb = disk.cleanup_estimate?.total_cleanable_mb || 150;
      const cDrive = currentDisks.find(d => (d.device || '').toUpperCase().startsWith('C')) || currentDisks[0];
      const totalGbTxt = cDrive ? ` | Всего: ${Number(cDrive.total_gb || 0).toFixed(1)} GB` : '';
      setText('about-kpi-stor-clean', `Cleanable: ~${cleanMb} MB${totalGbTxt}`);

      // Security table rows
      setText('about-sec-defender', defActive ? 'Enabled' : 'Disabled');
      setText('about-sec-realtime', sec.realtime_protection_enabled !== false ? 'Enabled' : 'Disabled');
      setText('about-sec-fw-domain', sec.firewall_profiles?.Domain ? 'Active' : 'Disabled');
      setText('about-sec-fw-private', sec.firewall_profiles?.Private ? 'Active' : 'Disabled');
      setText('about-sec-fw-public', sec.firewall_profiles?.Public ? 'Active' : 'Disabled');
      setText('about-sec-uac', uacOk ? 'Enabled' : 'Disabled');

      // Power Scheme & Updates
      if (pwr.active_plan_name) setText('about-spec-power', pwr.active_plan_name);
      if (upd.status) {
        const kbCount = upd.recent_hotfixes_count ? ` (${upd.recent_hotfixes_count} KBs installed)` : '';
        const updTxt = `${upd.status}${kbCount}`;
        setText('about-spec-update', updTxt);
        setText('about-ident-updates', updTxt);
      }

    } catch (e) {
      console.warn('[AboutSystemTab] fetchSystemControlStatus warning:', e);
    }
  }

  async function fetchHardwareSensors(isPoll = false) {
    try {
      const sensors = await apiFetch('/api/v1/system/sensors');
      if (Array.isArray(sensors)) {
        currentSensors = sensors;
        const badge = document.getElementById('about-sensors-count-badge');
        if (badge) badge.textContent = `LHM Active (${sensors.length} шт.)`;
        renderSensorsList(sensors);
      }
    } catch (e) {
      console.warn('[AboutSystemTab] fetchHardwareSensors warning:', e);
    }
  }

  function bindAIEvents() {
    const btnRescan = document.getElementById('btn-about-ai-rescan');
    if (btnRescan) {
      btnRescan.onclick = () => runAIDiagnostics(true);
    }

    const btnToggleStages = document.getElementById('btn-about-ai-toggle-stages');
    const stagesBox = document.getElementById('about-ai-stages-container');
    const icStages = document.getElementById('ic-about-ai-toggle-stages');
    const txtStages = document.getElementById('txt-about-ai-toggle-stages');
    if (btnToggleStages && stagesBox) {
      btnToggleStages.onclick = () => {
        const isHidden = stagesBox.classList.toggle('d-none');
        if (icStages) {
          icStages.className = isHidden ? 'bi bi-chevron-down ms-0.5' : 'bi bi-chevron-up ms-0.5';
        }
        if (txtStages) {
          txtStages.textContent = isHidden ? 'Показать этапы' : 'Свернуть этапы';
        }
      };
    }

    const btnTogglePrompt = document.getElementById('btn-about-ai-toggle-prompt');
    const promptCollapse = document.getElementById('about-ai-prompt-collapse');
    const icPrompt = document.getElementById('ic-about-ai-prompt');
    if (btnTogglePrompt && promptCollapse) {
      btnTogglePrompt.onclick = () => {
        const isShown = !promptCollapse.classList.toggle('d-none');
        if (icPrompt) {
          icPrompt.className = isShown ? 'bi bi-chevron-up text-muted ms-1' : 'bi bi-chevron-down text-muted ms-1';
        }
      };
    }

    const btnCopyPrompt = document.getElementById('btn-about-ai-copy-prompt');
    if (btnCopyPrompt) {
      btnCopyPrompt.onclick = () => {
        const text = document.getElementById('about-ai-prompt-text')?.textContent || '';
        navigator.clipboard.writeText(text).then(() => {
          const s = document.getElementById('txt-about-ai-copy-prompt');
          if (s) s.textContent = 'Скопировано!';
          setTimeout(() => { if (s) s.textContent = 'Копировать'; }, 1800);
        });
      };
    }

    const btnToggleRaw = document.getElementById('btn-about-ai-toggle-raw');
    const rawCollapse = document.getElementById('about-ai-raw-collapse');
    const icRaw = document.getElementById('ic-about-ai-raw');
    if (btnToggleRaw && rawCollapse) {
      btnToggleRaw.onclick = () => {
        const isShown = !rawCollapse.classList.toggle('d-none');
        if (icRaw) {
          icRaw.className = isShown ? 'bi bi-chevron-up text-muted ms-1' : 'bi bi-chevron-down text-muted ms-1';
        }
      };
    }

    const btnCopyRaw = document.getElementById('btn-about-ai-copy-raw');
    if (btnCopyRaw) {
      btnCopyRaw.onclick = () => {
        const text = document.getElementById('about-ai-raw-text')?.textContent || '';
        navigator.clipboard.writeText(text).then(() => {
          const s = document.getElementById('txt-about-ai-copy-raw');
          if (s) s.textContent = 'Скопировано!';
          setTimeout(() => { if (s) s.textContent = 'Копировать'; }, 1800);
        });
      };
    }
  }

  function renderAIDiagnosticStages(stages, isCompleted = true) {
    const container = document.getElementById('about-ai-stages-container');
    if (!container) return;
    if (!Array.isArray(stages) || stages.length === 0) {
      container.innerHTML = '<div class="small text-muted text-center py-2">Этапы аудита не зарегистрированы</div>';
      return;
    }

    container.innerHTML = stages.map((st, idx) => {
      const isLatest = idx === stages.length - 1 && !isCompleted;
      const icon = isLatest
        ? '<div class="spinner-grow spinner-grow-sm text-info" style="width: 0.6rem; height: 0.6rem;" role="status"></div>'
        : '<span class="text-success small fw-bold" style="font-size: 0.72rem;">✔</span>';
      const textClass = isLatest ? 'text-light fw-semibold' : 'text-muted';
      return `
        <div class="about-ai-stage-row ${textClass}">
          <div class="d-flex align-items-center gap-2">
            <span>${icon}</span>
            <span>${escapeHtml(st.message || st.title || 'Выполнение этапа...')}</span>
          </div>
          ${st.details ? `<div class="text-secondary ps-3 font-monospace" style="font-size: 0.68rem; word-break: break-all;">↳ ${escapeHtml(st.details)}</div>` : ''}
        </div>
      `;
    }).join('');
  }

  function renderAIAnomalies(anomalies) {
    const container = document.getElementById('about-ai-anomalies-container');
    if (!container) return;
    if (!Array.isArray(anomalies) || anomalies.length === 0) {
      container.innerHTML = '<span class="badge bg-success-subtle text-success border border-success px-2.5 py-1" style="font-size: 0.72rem;"><i class="bi bi-check-circle me-1"></i> Аномалий в подсистемах оборудования не обнаружено</span>';
      return;
    }

    container.innerHTML = anomalies.map(a => {
      const isCrit = a.severity === 'critical';
      return `<span class="anomaly-pill ${isCrit ? 'critical' : 'warning'}">⚠️ [${escapeHtml(a.subsystem || 'SYS')}] ${escapeHtml(a.title || '')}: ${escapeHtml(a.description || '')}</span>`;
    }).join('');
  }

  async function runAIDiagnostics(isManualRescan = false) {
    if (isAiRunning) return;
    isAiRunning = true;

    const btnRescan = document.getElementById('btn-about-ai-rescan');
    const txtRescan = document.getElementById('txt-about-ai-rescan');
    const icRescan = document.getElementById('ic-about-ai-rescan');
    const badgeHealth = document.getElementById('about-ai-health-badge');
    const engineTag = document.getElementById('about-ai-engine-name');
    const summaryEl = document.getElementById('about-ai-summary-text');
    const promptSec = document.getElementById('about-ai-prompt-section');
    const promptText = document.getElementById('about-ai-prompt-text');
    const rawSec = document.getElementById('about-ai-raw-section');
    const rawText = document.getElementById('about-ai-raw-text');

    if (btnRescan) btnRescan.disabled = true;
    if (icRescan) icRescan.className = 'spinner-border spinner-border-sm text-dark';
    if (txtRescan) txtRescan.textContent = 'Сканирование...';

    if (badgeHealth) {
      badgeHealth.textContent = 'Health: Анализ...';
      badgeHealth.className = 'badge bg-warning-subtle text-warning border border-warning font-monospace';
    }

    // Render initial in-progress stages
    renderAIDiagnosticStages([
      {
        stage: 'init',
        title: 'Сбор телеметрии',
        message: '🔌 Опрос системных метрик WMI, сенсоров и топовых процессов...',
        details: 'Формирование системного снимка (SystemSnapshot)',
      }
    ], false);

    if (summaryEl) {
      summaryEl.textContent = 'Выполняется глубокий аудит аппаратных ресурсов и поиск узких мест...';
    }

    try {
      const report = await apiFetch('/api/v1/system/diagnose', { method: 'POST' });
      if (!report) throw new Error('Пустой ответ от сервера');

      // Update Health Score Badge
      const score = Number(report.health_score || 100);
      if (badgeHealth) {
        badgeHealth.textContent = `Health: ${score}/100`;
        badgeHealth.className = `badge font-monospace ${
          score >= 80 ? 'bg-success-subtle text-success border border-success' :
          score >= 60 ? 'bg-warning-subtle text-warning border border-warning' :
          'bg-danger-subtle text-danger border border-danger'
        }`;
      }

      // Update Engine Badge
      if (engineTag) {
        engineTag.innerHTML = `<i class="bi bi-cpu me-1"></i>${escapeHtml(report.ai_model_used || 'Heuristic Engine')}`;
      }

      // Render Completed Stages
      const stages = Array.isArray(report.stages) && report.stages.length > 0
        ? report.stages
        : [
            { stage: 'init', title: 'Сбор телеметрии', message: '🔌 Сбор телеметрии хоста завершён' },
            { stage: 'eval', title: 'Эвристика', message: '⚙️ Эвристический анализ подсистем завершён' },
            { stage: 'done', title: 'Сводка', message: '✅ Аудит системы успешно выполнен' }
          ];
      renderAIDiagnosticStages(stages, true);

      // Render Anomalies
      renderAIAnomalies(report.anomalies);

      // Render Summary and Recommendations
      if (summaryEl) {
        let text = report.summary || 'Телеметрия в норме.';
        if (Array.isArray(report.recommendations) && report.recommendations.length > 0) {
          text += '\n\n💡 Рекомендации по оптимизации:\n' + report.recommendations.map(r => `• ${r}`).join('\n');
        }
        summaryEl.textContent = text;
      }

      // Handle Generated Prompt Viewer
      if (report.generated_prompt) {
        if (promptSec) promptSec.style.display = 'block';
        if (promptText) promptText.textContent = report.generated_prompt;
      } else {
        if (promptSec) promptSec.style.display = 'none';
      }

      // Handle Raw Response Viewer
      if (report.raw_response || report.summary) {
        if (rawSec) rawSec.style.display = 'block';
        if (rawText) rawText.textContent = report.raw_response || report.summary;
      } else {
        if (rawSec) rawSec.style.display = 'none';
      }
    } catch (e) {
      console.error('[AboutSystemTab] AI Diagnosis error:', e);
      if (summaryEl) summaryEl.textContent = 'Ошибка выполнения AI-диагностики: ' + e.message;
      if (badgeHealth) {
        badgeHealth.textContent = 'Health: Error';
        badgeHealth.className = 'badge bg-danger-subtle text-danger border border-danger font-monospace';
      }
      renderAIDiagnosticStages([
        { stage: 'error', title: 'Ошибка', message: `❌ Ошибка выполнения диагностики: ${e.message}`, details: 'Проверьте доступность бэкенда и настройки провайдеров' }
      ], true);
    } finally {
      isAiRunning = false;
      if (btnRescan) btnRescan.disabled = false;
      if (icRescan) icRescan.className = 'bi bi-lightning-charge-fill';
      if (txtRescan) txtRescan.textContent = 'Rescan';
    }
  }

  async function fetchHardwareSpec() {
    const container = document.getElementById('about-sys-tree-container');
    const badgeCount = document.getElementById('about-sys-node-count');
    if (!container) return;

    try {
      const nodes = await apiFetch('/api/v1/system/hardware');
      hardwareData = Array.isArray(nodes) ? nodes : [];

      if (badgeCount) {
        badgeCount.textContent = `${hardwareData.length} категорий`;
      }

      const searchInput = document.getElementById('about-sys-search');
      const filter = searchInput ? searchInput.value.trim().toLowerCase() : '';
      renderHardwareTree(hardwareData, filter);
    } catch (e) {
      console.error('[AboutSystemTab] Failed to fetch hardware spec:', e);
      container.innerHTML = `<div class="text-center py-4 text-danger small">Ошибка загрузки оборудования: ${escapeHtml(e.message)}</div>`;
    }
  }

  function renderDisksTable(disks) {
    const tbody = document.getElementById('about-sys-disks-tbody');
    const countBadge = document.getElementById('about-disks-count');
    if (!tbody) return;

    if (!Array.isArray(disks) || disks.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted">Дисковые разделы не обнаружены</td></tr>';
      return;
    }

    if (countBadge) countBadge.textContent = `${disks.length} Drives`;

    tbody.innerHTML = disks.map(d => {
      const pct = Math.min(100, Math.max(0, d.percent || 0));
      let barClass = 'bg-info';
      if (pct > 88) barClass = 'bg-danger';
      else if (pct > 70) barClass = 'bg-warning';

      return `
        <tr>
          <td><i class="bi bi-hdd me-1 text-primary"></i><strong>${escapeHtml(d.device || d.mountpoint || 'C:\\')}</strong></td>
          <td><span class="badge bg-secondary-subtle text-secondary border border-secondary">${escapeHtml(d.fstype || 'NTFS')}</span></td>
          <td>${Number(d.total_gb || 0).toFixed(1)} GB</td>
          <td class="text-light">${Number(d.used_gb || 0).toFixed(1)} GB</td>
          <td class="text-info fw-semibold">${Number(d.free_gb || 0).toFixed(1)} GB</td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <div class="about-sys-progress-track flex-grow-1" style="height: 6px;">
                <div class="about-sys-progress-bar ${barClass}" style="width: ${pct}%;"></div>
              </div>
              <span class="small" style="min-width: 42px; text-align: right;">${pct.toFixed(1)}%</span>
            </div>
          </td>
          <td><span class="about-sys-badge-ok">OK</span></td>
        </tr>
      `;
    }).join('');
  }

  function renderSensorsList(sensors) {
    const container = document.getElementById('about-sensors-container');
    if (!container) return;

    if (!Array.isArray(sensors) || sensors.length === 0) {
      container.innerHTML = '<div class="text-center py-4 text-muted small">Нет доступных сенсоров LHM</div>';
      return;
    }

    const searchInput = document.getElementById('about-sensor-search');
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

    const filtered = sensors.filter(s => {
      if (activeSensorFilter !== 'all') {
        const cat = (s.category || '').toLowerCase();
        if (activeSensorFilter === 'temperature' && !cat.includes('temp')) return false;
        if (activeSensorFilter === 'voltage' && !cat.includes('volt')) return false;
        if (activeSensorFilter === 'clock' && !cat.includes('clock') && !cat.includes('freq')) return false;
        if (activeSensorFilter === 'power' && !cat.includes('power') && !cat.includes('load')) return false;
      }
      if (query) {
        return (s.name || '').toLowerCase().includes(query) || (s.category || '').toLowerCase().includes(query);
      }
      return true;
    });

    if (filtered.length === 0) {
      container.innerHTML = '<div class="text-center py-3 text-muted small">Сенсоры по заданному фильтру не найдены</div>';
      return;
    }

    container.innerHTML = filtered.map(s => {
      let icon = 'bi bi-thermometer-half text-danger';
      let valColor = 'text-info';
      const cat = (s.category || '').toLowerCase();

      if (cat.includes('volt')) {
        icon = 'bi bi-lightning-charge text-warning';
        valColor = 'text-warning';
      } else if (cat.includes('clock') || cat.includes('freq')) {
        icon = 'bi bi-speedometer text-info';
        valColor = 'text-info';
      } else if (cat.includes('power')) {
        icon = 'bi bi-plug text-success';
        valColor = 'text-success';
      } else if (cat.includes('load')) {
        icon = 'bi bi-percent text-primary';
        valColor = 'text-light';
      }

      return `
        <div class="d-flex align-items-center justify-content-between py-1 px-2 border-bottom border-secondary-subtle">
          <div class="d-flex align-items-center gap-2 text-truncate" style="max-width: 68%;">
            <i class="${icon}" style="font-size: 0.85rem;"></i>
            <span class="small text-truncate" title="${escapeHtml(s.name)}">${escapeHtml(s.name)}</span>
          </div>
          <div class="sensor-badge-val ${valColor}">${s.value} ${escapeHtml(s.unit || '')}</div>
        </div>
      `;
    }).join('');
  }

  function renderProcessesTable(procs) {
    const tbody = document.getElementById('about-sys-procs-tbody');
    if (!tbody) return;

    if (!Array.isArray(procs) || procs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Процессы не найдены</td></tr>';
      return;
    }

    const searchInput = document.getElementById('about-proc-search');
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

    const filtered = procs.filter(p => {
      if (!query) return true;
      return String(p.pid).includes(query) ||
             (p.name || '').toLowerCase().includes(query) ||
             (p.username || '').toLowerCase().includes(query);
    });

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Процессы по запросу не найдены</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.slice(0, 30).map(p => {
      const cpuVal = Number(p.cpu_percent || 0).toFixed(1);
      const memVal = Number(p.memory_mb || 0).toFixed(1);
      const isHigh = p.cpu_percent > 10;

      return `
        <tr>
          <td class="text-muted">${p.pid}</td>
          <td class="text-white fw-semibold text-truncate" style="max-width: 160px;" title="${escapeHtml(p.name)}">
            ${escapeHtml(p.name)}
          </td>
          <td><span class="badge bg-dark border border-secondary text-secondary" style="font-size: 0.68rem;">${escapeHtml(p.status || 'running')}</span></td>
          <td class="${isHigh ? 'text-danger fw-bold' : 'text-info'}">${cpuVal}%</td>
          <td class="text-light">${memVal} MB</td>
          <td class="text-secondary">${p.num_threads || 1}</td>
          <td class="text-muted small text-truncate" style="max-width: 140px;" title="${escapeHtml(p.username || '')}">
            ${escapeHtml(p.username || '-')}
          </td>
        </tr>
      `;
    }).join('');
  }

  function renderHardwareTree(nodes, filter) {
    const container = document.getElementById('about-sys-tree-container');
    if (!container) return;

    if (!Array.isArray(nodes) || nodes.length === 0) {
      container.innerHTML = '<div class="text-center py-4 text-muted small">Оборудование не обнаружено или опрашивается...</div>';
      return;
    }

    const filtered = nodes.filter(node => {
      if (!filter) return true;
      const catMatch = (node.category || '').toLowerCase().includes(filter);
      const nameMatch = (node.name || '').toLowerCase().includes(filter);
      const propsMatch = Object.entries(node.properties || {}).some(
        ([k, v]) => k.toLowerCase().includes(filter) || String(v).toLowerCase().includes(filter)
      );
      return catMatch || nameMatch || propsMatch;
    });

    if (filtered.length === 0) {
      container.innerHTML = `<div class="text-center py-4 text-muted small">По запросу «${escapeHtml(filter)}» компонентов не найдено</div>`;
      return;
    }

    container.innerHTML = filtered.map((node, idx) => {
      const propsEntries = Object.entries(node.properties || {});
      const propsHtml = propsEntries.length > 0
        ? propsEntries.map(([k, v]) => `
            <div class="about-sys-prop-row">
              <span class="about-sys-prop-key">${escapeHtml(k)}</span>
              <span class="about-sys-prop-val">${escapeHtml(String(v))}</span>
            </div>
          `).join('')
        : '<div class="text-muted small py-1">Свойства не указаны</div>';

      const iconClass = getNodeIcon(node.category);

      return `
        <div class="about-sys-tree-node">
          <div class="about-sys-tree-title" onclick="toggleNode(${idx})">
            <span class="d-flex align-items-center gap-2">
              <i class="${iconClass} text-info"></i>
              <strong>${escapeHtml(node.category)}:</strong>
              <span class="text-white">${escapeHtml(node.name || '')}</span>
            </span>
            <span class="about-sys-chevron" id="about-chevron-${idx}" style="font-size: 0.72rem; color: #38bdf8;">▼</span>
          </div>
          <div class="about-sys-tree-body" id="about-node-body-${idx}">
            ${propsHtml}
          </div>
        </div>
      `;
    }).join('');
  }

  window.toggleNode = function(idx) {
    const body = document.getElementById(`about-node-body-${idx}`);
    const chevron = document.getElementById(`about-chevron-${idx}`);
    if (body) {
      body.classList.toggle('d-none');
      if (chevron) {
        chevron.textContent = body.classList.contains('d-none') ? '▼' : '▲';
      }
    }
  };

  function getNodeIcon(category) {
    const cat = (category || '').toLowerCase();
    if (cat.includes('processor') || cat.includes('cpu')) return 'bi bi-cpu';
    if (cat.includes('memory') || cat.includes('ram')) return 'bi bi-memory';
    if (cat.includes('system') || cat.includes('os')) return 'bi bi-laptop';
    if (cat.includes('motherboard') || cat.includes('mainboard')) return 'bi bi-motherboard';
    if (cat.includes('display') || cat.includes('gpu') || cat.includes('video') || cat.includes('graphics')) return 'bi bi-gpu-card';
    if (cat.includes('disk') || cat.includes('storage') || cat.includes('drive')) return 'bi bi-hdd';
    if (cat.includes('network') || cat.includes('adapter') || cat.includes('ethernet')) return 'bi bi-ethernet';
    return 'bi bi-gear-fill';
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

  // Self-trigger if container is already in DOM
  if (document.getElementById('about-sys-wrapper') || document.getElementById('tab-about-system')) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => initAboutSystemTab());
    } else {
      setTimeout(() => initAboutSystemTab(), 10);
    }
  }
})();

