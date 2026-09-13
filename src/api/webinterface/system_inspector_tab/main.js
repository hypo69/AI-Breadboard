// System & Hardware Inspector Tab JS Module
(function() {
  let sysWs = null;
  let isSysInitialized = false;
  let isSysPaused = false;
  let latestTelemetrySnapshot = null;

  async function fetchHardwareTree() {
    const container = document.getElementById('sys-hardware-tree-container');
    if (!container) return;

    try {
      const res = await fetch('/api/v1/system/hardware');
      if (!res.ok) throw new Error('Hardware API error');
      const nodes = await res.json();

      if (!Array.isArray(nodes) || nodes.length === 0) {
        container.innerHTML = '<div class="text-center py-4 text-muted small">Оборудование не обнаружено</div>';
        return;
      }

      container.innerHTML = nodes.map((node, idx) => {
        const propsHtml = Object.entries(node.properties || {}).map(([k, v]) => `
          <div class="sys-prop-row">
            <span class="sys-prop-key">${k}</span>
            <span class="sys-prop-val">${v}</span>
          </div>
        `).join('');

        return `
          <div class="sys-tree-node">
            <div class="sys-tree-title" onclick="const b = document.getElementById('sys-node-body-${idx}'); if(b) b.classList.toggle('d-none')">
              <span>${node.category}: ${node.name}</span>
              <span style="font-size: 0.7rem; color: #38bdf8;">▼</span>
            </div>
            <div class="sys-tree-body" id="sys-node-body-${idx}">
              ${propsHtml}
            </div>
          </div>
        `;
      }).join('');
    } catch (e) {
      console.error('[SystemInspectorTab] Failed to fetch hardware tree:', e);
      container.innerHTML = `<div class="text-center py-4 text-danger small">Ошибка загрузки оборудования: ${e.message}</div>`;
    }
  }

  function updateTelemetryDashboard(snap) {
    if (!snap) return;

    // CPU
    if (snap.cpu) {
      const cpuVal = document.getElementById('sys-metric-cpu-val');
      const cpuFill = document.getElementById('sys-metric-cpu-fill');
      const cpuSub = document.getElementById('sys-metric-cpu-sub');

      const pct = Number(snap.cpu.total_percent || 0);
      if (cpuVal) cpuVal.innerText = `${pct.toFixed(1)}%`;
      if (cpuFill) cpuFill.style.width = `${Math.min(100, pct)}%`;
      if (cpuSub) cpuSub.innerText = `${snap.cpu.physical_cores || '--'} Физических / ${snap.cpu.logical_cores || '--'} Потоков`;
    }

    // RAM
    if (snap.memory) {
      const ramVal = document.getElementById('sys-metric-ram-val');
      const ramFill = document.getElementById('sys-metric-ram-fill');
      const ramSub = document.getElementById('sys-metric-ram-sub');

      const usedGb = Number(snap.memory.used_gb || 0);
      const totalGb = Number(snap.memory.total_gb || 0);
      const pct = Number(snap.memory.percent || 0);

      if (ramVal) ramVal.innerText = `${usedGb.toFixed(1)} / ${totalGb.toFixed(1)} GB`;
      if (ramFill) ramFill.style.width = `${pct}%`;
      if (ramSub) ramSub.innerText = `${pct}% занято (${Number(snap.memory.available_gb || 0).toFixed(1)} GB свободно)`;
    }

    // GPU
    if (Array.isArray(snap.gpus) && snap.gpus.length > 0) {
      const g = snap.gpus[0];
      const gpuVal = document.getElementById('sys-metric-gpu-val');
      const gpuSub = document.getElementById('sys-metric-gpu-sub');

      if (gpuVal) gpuVal.innerText = g.name || 'GPU';
      if (gpuSub) gpuSub.innerText = `VRAM: ${Number(g.memory_total_gb || 0).toFixed(1)} GB | CUDA: ${g.has_cuda ? 'Да' : 'Нет'}`;
    }

    // Disk I/O
    if (snap.disk_io) {
      const diskVal = document.getElementById('sys-metric-disk-val');
      const diskSub = document.getElementById('sys-metric-disk-sub');

      const totalMb = ((snap.disk_io.read_bytes_per_sec + snap.disk_io.write_bytes_per_sec) / (1024 * 1024)).toFixed(2);
      const rKb = (snap.disk_io.read_bytes_per_sec / 1024).toFixed(0);
      const wKb = (snap.disk_io.write_bytes_per_sec / 1024).toFixed(0);

      if (diskVal) diskVal.innerText = `${totalMb} MB/s`;
      if (diskSub) diskSub.innerText = `Чтение: ${rKb} KB/s | Запись: ${wKb} KB/s`;
    }

    renderProcessTable();
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

    tbody.innerHTML = filtered.map(p => {
      let cpuClass = '';
      if (p.cpu_percent > 40) cpuClass = 'badge-cpu-high';
      else if (p.cpu_percent > 15) cpuClass = 'badge-cpu-med';

      return `
        <tr>
          <td style="color: #38bdf8;">${p.pid}</td>
          <td style="font-weight: 600;">${p.name}</td>
          <td style="color: #94a3b8;">${p.status || 'running'}</td>
          <td style="text-align: right;" class="${cpuClass}">${Number(p.cpu_percent || 0).toFixed(1)}%</td>
          <td style="text-align: right; color: #4ade80;">${Number(p.memory_mb || 0).toFixed(1)} MB</td>
          <td style="text-align: right; color: #a855f7;">${p.num_threads || 1}</td>
          <td style="color: #94a3b8;">${p.username || 'SYSTEM'}</td>
        </tr>
      `;
    }).join('');
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
          anomaliesEl.innerHTML = report.anomalies.map(a => `<span class="anomaly-tag">⚠️ [${a.subsystem}] ${a.title}</span>`).join('');
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

  function connectSystemWebSocket() {
    if (sysWs) {
      try { sysWs.close(); } catch {}
    }
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/api/v1/system/stream`;

    try {
      sysWs = new WebSocket(wsUrl);
      const statusBadge = document.getElementById('sys-conn-status');

      sysWs.onopen = () => {
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
          console.error('[SystemInspectorTab] WS message parse error:', e);
        }
      };

      sysWs.onclose = () => {
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
          statusBadge.innerText = '● Отключено';
        }
      };
    } catch (e) {
      console.error('[SystemInspectorTab] WS connection error:', e);
    }
  }

  function initSystemInspectorTab() {
    console.log('[SystemInspectorTab] Initializing System Inspector tab...');
    fetchHardwareTree();
    connectSystemWebSocket();

    if (!isSysInitialized) {
      const refreshHwBtn = document.getElementById('btn-sys-refresh-hw');
      const auditBtn = document.getElementById('btn-sys-run-audit');
      const pauseBtn = document.getElementById('btn-sys-pause-proc');
      const procSearch = document.getElementById('sys-proc-search');
      const configBtn = document.getElementById('btn-sys-config');

      if (refreshHwBtn) refreshHwBtn.onclick = fetchHardwareTree;
      if (auditBtn) auditBtn.onclick = runAiDiagnostics;
      if (configBtn) configBtn.onclick = () => {
        if (typeof window.openAppConfigModal === 'function') {
          window.openAppConfigModal('system_inspector', 'System & Hardware Inspector');
        }
      };
      if (pauseBtn) {
        pauseBtn.onclick = () => {
          isSysPaused = !isSysPaused;
          pauseBtn.innerText = isSysPaused ? 'Возобновить' : 'Пауза';
          pauseBtn.className = isSysPaused ? 'btn btn-sm btn-warning rounded-pill px-3' : 'btn btn-sm btn-outline-secondary rounded-pill px-3';
        };
      }
      if (procSearch) procSearch.oninput = renderProcessTable;

      isSysInitialized = true;
    }
  }

  window.initSystemInspectorTab = initSystemInspectorTab;
})();
