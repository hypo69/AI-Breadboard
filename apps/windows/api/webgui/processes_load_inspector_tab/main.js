/**
 * =============================================================================
 * Process Name: Windows Processes Load Inspector Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля инспектора активности процессов
 *   (Process Intelligence & Activity Deep Dive — 7 функциональных виджетов,
 *   сетевая активность и мониторинг изменений файлов в реальном времени).
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/processes_load_inspector_tab/main.js?v=20261008_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/processes_load_inspector_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 13:58:00
 * =============================================================================
 */

(function() {
  // Текущее состояние вкладки
  let currentMode = 'deep-dive'; // 'deep-dive' | 'host-overview'
  let currentInstanceFilter = 'active'; // 'active' | 'history'
  let selectedInstanceId = null;
  let selectedInstanceData = null;
  let currentChartInterval = '1m';
  let isDeepDivePaused = false;
  let deepDiveTimer = null;
  let hostOverviewTimer = null;

  // Кэшированные данные
  let cachedActiveInstances = [];
  let cachedHistoryInstances = [];
  let cachedTopProcesses = [];
  let isProcPaused = false;

  // Состояние сетевой активности хоста
  let cachedNetworkActivities = [];
  let currentNetFilter = 'internet'; // 'internet' | 'all' | 'listen'
  let isNetPaused = false;

  // Состояние мониторинга файлов хоста
  let cachedFileEvents = [];
  let currentWatchDirs = [];
  let currentWatchDir = '';
  let isWatcherPaused = false;

  // Chart.js экземпляры
  let chartCpu = null;
  let chartRam = null;
  let chartGpu = null;
  let chartDisk = null;

  // ---------------------------------------------------------------------------
  // Вспомогательные утилиты
  // ---------------------------------------------------------------------------

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function formatDuration(seconds) {
    if (!seconds || seconds <= 0) return '00:00:00';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  function showToast(msg, type = 'info') {
    if (window.showToast) {
      window.showToast(msg, type);
    } else {
      console.log(`[Toast ${type}] ${msg}`);
    }
  }

  // ---------------------------------------------------------------------------
  // Инициализация графиков Chart.js (Виджет 3.2)
  // ---------------------------------------------------------------------------

  function initCharts() {
    const commonChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: {
          display: true,
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          ticks: { color: '#888', font: { size: 9 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 6 }
        },
        y: {
          display: true,
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          ticks: { color: '#888', font: { size: 9 } }
        }
      },
      plugins: {
        legend: { labels: { color: '#bbb', font: { size: 10 }, boxWidth: 10 } },
        tooltip: { mode: 'index', intersect: false }
      }
    };

    // 1. CPU Chart
    const ctxCpu = document.getElementById('chart-proc-cpu')?.getContext('2d');
    if (ctxCpu && !chartCpu) {
      chartCpu = new Chart(ctxCpu, {
        type: 'line',
        data: {
          labels: [],
          datasets: [
            { label: 'ЦП Общая %', data: [], borderColor: '#0dcaf0', backgroundColor: 'rgba(13, 202, 240, 0.1)', borderWidth: 1.5, fill: true, tension: 0.2 },
            { label: 'User Mode %', data: [], borderColor: '#818cf8', borderWidth: 1, borderDash: [4, 4], fill: false, tension: 0.2 },
            { label: 'Потоки', data: [], borderColor: '#f59e0b', borderWidth: 1, yAxisID: 'y1', fill: false }
          ]
        },
        options: {
          ...commonChartOptions,
          scales: {
            ...commonChartOptions.scales,
            y: { ...commonChartOptions.scales.y, min: 0, max: 100 },
            y1: { type: 'linear', display: false, position: 'right', min: 0 }
          }
        }
      });
    }

    // 2. RAM Chart
    const ctxRam = document.getElementById('chart-proc-ram')?.getContext('2d');
    if (ctxRam && !chartRam) {
      chartRam = new Chart(ctxRam, {
        type: 'line',
        data: {
          labels: [],
          datasets: [
            { label: 'Working Set (MB)', data: [], borderColor: '#fbbf24', backgroundColor: 'rgba(251, 191, 36, 0.15)', borderWidth: 1.5, fill: true, tension: 0.2 },
            { label: 'Private Bytes (MB)', data: [], borderColor: '#f97316', borderWidth: 1.2, fill: false, tension: 0.2 }
          ]
        },
        options: commonChartOptions
      });
    }

    // 3. GPU Chart
    const ctxGpu = document.getElementById('chart-proc-gpu')?.getContext('2d');
    if (ctxGpu && !chartGpu) {
      chartGpu = new Chart(ctxGpu, {
        type: 'line',
        data: {
          labels: [],
          datasets: [
            { label: 'GPU Load %', data: [], borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', borderWidth: 1.5, fill: true, tension: 0.2 },
            { label: 'VRAM (MB)', data: [], borderColor: '#34d399', borderWidth: 1, yAxisID: 'y1', fill: false }
          ]
        },
        options: {
          ...commonChartOptions,
          scales: {
            ...commonChartOptions.scales,
            y: { ...commonChartOptions.scales.y, min: 0, max: 100 },
            y1: { type: 'linear', display: false, position: 'right', min: 0 }
          }
        }
      });
    }

    // 4. Disk Chart
    const ctxDisk = document.getElementById('chart-proc-disk')?.getContext('2d');
    if (ctxDisk && !chartDisk) {
      chartDisk = new Chart(ctxDisk, {
        type: 'line',
        data: {
          labels: [],
          datasets: [
            { label: 'Чтение (KB/s)', data: [], borderColor: '#38bdf8', borderWidth: 1.2, tension: 0.2 },
            { label: 'Запись (KB/s)', data: [], borderColor: '#ef4444', borderWidth: 1.2, tension: 0.2 }
          ]
        },
        options: commonChartOptions
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Виджет 3.1: Загрузка списка инстансов и Карточка профиля
  // ---------------------------------------------------------------------------

  async function loadInstancesList() {
    try {
      const searchVal = document.getElementById('deep-dive-search')?.value.trim() || '';
      const endpoint = currentInstanceFilter === 'active'
        ? `/api/v1/telemetry/instances/active?limit=100${searchVal ? '&search=' + encodeURIComponent(searchVal) : ''}`
        : `/api/v1/telemetry/instances/history?limit=100${searchVal ? '&search=' + encodeURIComponent(searchVal) : ''}`;

      const res = await fetch(endpoint);
      if (!res.ok) return;

      const instances = await res.json();
      if (currentInstanceFilter === 'active') {
        cachedActiveInstances = instances;
        const countBadge = document.getElementById('count-inst-active');
        if (countBadge) countBadge.textContent = instances.length;
      } else {
        cachedHistoryInstances = instances;
      }

      renderInstanceDropdown(instances);

      // Если процесс не выбран, выбираем первый
      if (!selectedInstanceId && instances.length > 0) {
        selectInstance(instances[0].instance_id);
      }
    } catch (e) {
      console.warn('[ProcessActivity] Error loading instances:', e);
    }
  }

  function renderInstanceDropdown(instances) {
    const select = document.getElementById('deep-dive-instance-select');
    if (!select) return;

    const currentVal = selectedInstanceId;
    select.innerHTML = '<option value="">Выберите процесс для анализа...</option>';

    instances.forEach(inst => {
      const opt = document.createElement('option');
      opt.value = inst.instance_id;
      const statusIcon = inst.status === 'RUNNING' ? '🟢' : inst.status === 'SUSPENDED' ? '🟡' : '⚪';
      opt.textContent = `${statusIcon} ${inst.name} (PID: ${inst.pid}, #${inst.instance_id}) - CPU: ${inst.cpu_percent.toFixed(1)}% | ${inst.memory_mb.toFixed(0)} MB`;
      if (inst.instance_id === currentVal) {
        opt.selected = true;
      }
      select.appendChild(opt);
    });
  }

  async function selectInstance(instanceId) {
    if (!instanceId) return;
    selectedInstanceId = parseInt(instanceId, 10);

    // Подгружаем паспорт инстанса
    try {
      const res = await fetch(`/api/v1/telemetry/instances/${selectedInstanceId}`);
      if (res.ok) {
        selectedInstanceData = await res.json();
        renderInstanceProfileCard(selectedInstanceData);
        await Promise.all([
          loadInstanceSamples(),
          loadInstanceLineage(),
          loadInstanceSockets(),
          loadInstanceFileActivity()
        ]);
      }
    } catch (e) {
      console.error('[ProcessActivity] Error fetching instance details:', e);
    }
  }

  function renderInstanceProfileCard(inst) {
    if (!inst) return;

    document.getElementById('inst-card-name').textContent = inst.name || 'Unknown';
    document.getElementById('inst-card-pid').textContent = `PID: ${inst.pid}`;
    document.getElementById('inst-card-id').textContent = `instance_id: #${inst.instance_id}`;
    document.getElementById('inst-card-path').textContent = inst.executable_path || '-';
    document.getElementById('inst-card-user').textContent = inst.user_name || 'SYSTEM / Local';
    document.getElementById('inst-card-integrity').textContent = inst.integrity_level || 'Medium';
    document.getElementById('inst-card-start').textContent = inst.start_time ? new Date(inst.start_time).toLocaleString('ru-RU') : '--';
    document.getElementById('inst-card-uptime').textContent = `⏱️ Uptime: ${formatDuration(inst.uptime_seconds)}`;
    document.getElementById('inst-card-cmdline').textContent = inst.command_line || inst.executable_path || '-';

    const parentLink = document.getElementById('inst-card-parent-link');
    if (parentLink) {
      if (inst.parent_instance_id) {
        parentLink.innerHTML = `<a href="javascript:void(0)" class="text-info text-decoration-none fw-bold" id="link-parent-inst">Родитель #${inst.parent_instance_id}</a>`;
        document.getElementById('link-parent-inst')?.addEventListener('click', () => selectInstance(inst.parent_instance_id));
      } else {
        parentLink.textContent = inst.ppid ? `PPID: ${inst.ppid}` : 'Корневой (Root)';
      }
    }

    // Статус бейдж
    const statusBadge = document.getElementById('inst-card-status');
    const suspendBtn = document.getElementById('btn-safeops-suspend');
    const resumeBtn = document.getElementById('btn-safeops-resume');

    if (statusBadge) {
      statusBadge.textContent = inst.status;
      if (inst.status === 'RUNNING') {
        statusBadge.className = 'badge bg-success fs-6 px-3 py-1.5';
        suspendBtn?.classList.remove('d-none');
        resumeBtn?.classList.add('d-none');
      } else if (inst.status === 'SUSPENDED') {
        statusBadge.className = 'badge bg-warning text-dark fs-6 px-3 py-1.5';
        suspendBtn?.classList.add('d-none');
        resumeBtn?.classList.remove('d-none');
      } else {
        statusBadge.className = 'badge bg-secondary fs-6 px-3 py-1.5';
        statusBadge.textContent = `EXITED (${inst.exit_code !== null ? 'code: ' + inst.exit_code : '0'})`;
        suspendBtn?.classList.add('d-none');
        resumeBtn?.classList.add('d-none');
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Виджет 3.2: Загрузка сэмплов и обновление графиков
  // ---------------------------------------------------------------------------

  async function loadInstanceSamples() {
    if (!selectedInstanceId) return;
    try {
      const limitMap = { '1m': 60, '5m': 150, '1h': 300, '24h': 1000 };
      const limit = limitMap[currentChartInterval] || 100;
      const res = await fetch(`/api/v1/telemetry/instances/${selectedInstanceId}/samples?limit=${limit}`);
      if (!res.ok) return;

      const samples = await res.json();
      if (!Array.isArray(samples)) return;

      const labels = samples.map(s => {
        try {
          return new Date(s.timestamp).toLocaleTimeString('ru-RU', { hour12: false });
        } catch {
          return '';
        }
      });

      // Update Chart 1: CPU
      if (chartCpu) {
        chartCpu.data.labels = labels;
        chartCpu.data.datasets[0].data = samples.map(s => s.cpu_percent);
        chartCpu.data.datasets[1].data = samples.map(s => s.cpu_user_time);
        chartCpu.data.datasets[2].data = samples.map(s => s.thread_count);
        chartCpu.update();
      }

      // Update Chart 2: RAM
      if (chartRam) {
        chartRam.data.labels = labels;
        chartRam.data.datasets[0].data = samples.map(s => s.working_set_mb);
        chartRam.data.datasets[1].data = samples.map(s => s.private_bytes_mb);
        chartRam.update();
      }

      // Update Chart 3: GPU
      if (chartGpu) {
        chartGpu.data.labels = labels;
        chartGpu.data.datasets[0].data = samples.map(s => s.gpu_load_percent);
        chartGpu.data.datasets[1].data = samples.map(s => s.gpu_vram_mb);
        chartGpu.update();
      }

      // Update Chart 4: Disk
      if (chartDisk) {
        chartDisk.data.labels = labels;
        chartDisk.data.datasets[0].data = samples.map(s => (s.disk_read_bytes_sec / 1024).toFixed(1));
        chartDisk.data.datasets[1].data = samples.map(s => (s.disk_write_bytes_sec / 1024).toFixed(1));
        chartDisk.update();
      }

      // Update current metric badges and Widget 3.6 Gauges
      if (samples.length > 0) {
        const last = samples[samples.length - 1];
        document.getElementById('chart-cpu-current').textContent = `${last.cpu_percent.toFixed(1)}% | ${last.thread_count} thr`;
        document.getElementById('chart-ram-current').textContent = `${last.working_set_mb.toFixed(1)} MB`;
        document.getElementById('chart-gpu-current').textContent = `${last.gpu_load_percent.toFixed(1)}% | ${last.gpu_vram_mb.toFixed(0)} MB`;
        document.getElementById('chart-disk-current').textContent = `${(last.disk_read_bytes_sec / 1024).toFixed(0)} R / ${(last.disk_write_bytes_sec / 1024).toFixed(0)} W KB/s`;

        // Widget 3.6
        document.getElementById('metric-handles-count').textContent = last.handle_count || 0;
        document.getElementById('metric-gdi-count').textContent = last.gdi_objects || 0;
        document.getElementById('metric-user-count').textContent = last.user_objects || 0;
        document.getElementById('metric-page-faults').textContent = (last.page_faults_sec || 0).toFixed(1);

        const leakBadge = document.getElementById('badge-leak-risk');
        if (leakBadge) {
          if ((last.gdi_objects || 0) > 8000 || (last.user_objects || 0) > 8000 || (last.handle_count || 0) > 50000) {
            leakBadge.className = 'badge bg-danger';
            leakBadge.textContent = 'КРИТИЧЕСКИЙ РИСК УТЕЧКИ';
          } else if ((last.gdi_objects || 0) > 3000 || (last.handle_count || 0) > 10000) {
            leakBadge.className = 'badge bg-warning text-dark';
            leakBadge.textContent = 'Умеренный риск';
          } else {
            leakBadge.className = 'badge bg-success';
            leakBadge.textContent = 'Низкий риск';
          }
        }
      }
    } catch (e) {
      console.warn('[ProcessActivity] Error loading samples:', e);
    }
  }

  // ---------------------------------------------------------------------------
  // Виджет 3.3: Иерархическое дерево происхождения (Process Lineage)
  // ---------------------------------------------------------------------------

  async function loadInstanceLineage() {
    if (!selectedInstanceId) return;
    const container = document.getElementById('lineage-container');
    if (!container) return;

    try {
      const res = await fetch(`/api/v1/telemetry/instances/${selectedInstanceId}/lineage`);
      if (!res.ok) {
        container.innerHTML = '<div class="text-muted small p-2">Генеалогические связи не найдены</div>';
        return;
      }

      const node = await res.json();
      let html = '<div class="d-flex flex-column gap-2">';

      // Родитель
      if (node.parent) {
        html += `
          <div class="lineage-node-card d-flex align-items-center justify-content-between" data-inst-id="${node.parent.instance_id}">
            <div class="d-flex align-items-center gap-2">
              <i class="bi bi-arrow-return-right text-muted"></i>
              <span class="fw-bold text-light">${escapeHtml(node.parent.name)}</span>
              <span class="badge bg-secondary">PID: ${node.parent.pid}</span>
              <span class="badge bg-dark border border-secondary text-info">#${node.parent.instance_id}</span>
            </div>
            <span class="badge bg-dark border border-secondary text-muted">Родитель</span>
          </div>
          <div class="text-center text-muted small my-0"><i class="bi bi-arrow-down"></i></div>
        `;
      }

      // Текущий инстанс
      html += `
        <div class="lineage-node-card active d-flex align-items-center justify-content-between" data-inst-id="${node.instance_id}">
          <div class="d-flex align-items-center gap-2">
            <span class="fs-6">⭐</span>
            <span class="fw-bold text-info fs-6">${escapeHtml(node.name)}</span>
            <span class="badge bg-primary">PID: ${node.pid}</span>
            <span class="badge bg-info text-dark fw-bold">#${node.instance_id}</span>
          </div>
          <span class="badge bg-success">[Текущий инстанс]</span>
        </div>
      `;

      // Дочерние процессы
      if (node.children && node.children.length > 0) {
        html += '<div class="text-center text-muted small my-0"><i class="bi bi-arrow-down"></i></div>';
        html += '<div class="ms-4 d-flex flex-column gap-1.5">';
        node.children.forEach(c => {
          html += `
            <div class="lineage-node-card d-flex align-items-center justify-content-between" data-inst-id="${c.instance_id}">
              <div class="d-flex align-items-center gap-2">
                <i class="bi bi-diagram-2 text-warning"></i>
                <span class="fw-bold text-light">${escapeHtml(c.name)}</span>
                <span class="badge bg-secondary">PID: ${c.pid}</span>
                <span class="badge bg-dark border border-secondary text-info">#${c.instance_id}</span>
              </div>
              <span class="badge bg-dark border border-secondary text-warning">Дочерний процесс</span>
            </div>
          `;
        });
        html += '</div>';
      }

      html += '</div>';
      container.innerHTML = html;

      // Привязка кликов по узлам графа для мгновенного перехода
      container.querySelectorAll('.lineage-node-card').forEach(card => {
        card.addEventListener('click', () => {
          const instId = card.getAttribute('data-inst-id');
          if (instId && parseInt(instId, 10) !== selectedInstanceId) {
            selectInstance(parseInt(instId, 10));
          }
        });
      });
    } catch (e) {
      container.innerHTML = `<div class="text-danger small p-2">Ошибка загрузки Lineage: ${escapeHtml(e.message)}</div>`;
    }
  }

  // ---------------------------------------------------------------------------
  // Виджет 3.4: Сетевые сокеты процесса
  // ---------------------------------------------------------------------------

  async function loadInstanceSockets() {
    if (!selectedInstanceId) return;
    const tbody = document.getElementById('inst-sockets-tbody');
    const countBadge = document.getElementById('badge-inst-sockets-count');
    if (!tbody) return;

    try {
      const res = await fetch(`/api/v1/telemetry/instances/${selectedInstanceId}/sockets`);
      if (!res.ok) return;

      const sockets = await res.json();
      if (countBadge) countBadge.textContent = sockets.length;

      if (!sockets || sockets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Нет активных сетевых сокетов</td></tr>';
        return;
      }

      tbody.innerHTML = sockets.map(s => `
        <tr>
          <td><span class="badge bg-dark border border-secondary text-info">${escapeHtml(s.protocol)}</span></td>
          <td class="font-monospace text-light">${escapeHtml(s.local_address)}</td>
          <td class="font-monospace text-warning">${escapeHtml(s.remote_address)}</td>
          <td><span class="badge bg-success-subtle text-success border border-success">${escapeHtml(s.status)}</span></td>
        </tr>
      `).join('');
    } catch (e) {
      console.warn('[ProcessActivity] Error loading sockets:', e);
    }
  }

  // ---------------------------------------------------------------------------
  // Виджет 3.5: Файловые операции инстанса
  // ---------------------------------------------------------------------------

  async function loadInstanceFileActivity() {
    if (!selectedInstanceId) return;
    const tbody = document.getElementById('inst-file-events-tbody');
    if (!tbody) return;

    try {
      const searchVal = document.getElementById('inst-file-search')?.value.trim() || '';
      let url = `/api/v1/telemetry/instances/${selectedInstanceId}/file-activity?limit=50`;
      if (searchVal) {
        if (searchVal.startsWith('.')) {
          url += `&extension=${encodeURIComponent(searchVal)}`;
        } else {
          url += `&action=${encodeURIComponent(searchVal)}`;
        }
      }

      const res = await fetch(url);
      if (!res.ok) return;

      const events = await res.json();
      if (!events || events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-3">Журнал файловых операций пуст</td></tr>';
        return;
      }

      tbody.innerHTML = events.map(ev => {
        let actionBadge = 'bg-secondary';
        if (ev.action === 'CREATE') actionBadge = 'bg-success';
        else if (ev.action === 'MODIFY') actionBadge = 'bg-warning text-dark';
        else if (ev.action === 'DELETE') actionBadge = 'bg-danger';
        else if (ev.action === 'RENAME') actionBadge = 'bg-info text-dark';

        const timeStr = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString('ru-RU') : '--';
        return `
          <tr>
            <td class="font-monospace text-muted">${timeStr}</td>
            <td><span class="badge ${actionBadge}">${escapeHtml(ev.action)}</span></td>
            <td class="font-monospace text-truncate text-light" style="max-width: 280px;" title="${escapeHtml(ev.file_path)}">
              ${escapeHtml(ev.file_path)}
            </td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.warn('[ProcessActivity] Error loading file activity:', e);
    }
  }

  // ---------------------------------------------------------------------------
  // Виджет 3.7: SafeOps Действия над процессом
  // ---------------------------------------------------------------------------

  let pendingSafeOpsAction = null;

  function initSafeOps() {
    // 1. Изменение приоритета CPU
    document.getElementById('btn-safeops-set-priority')?.addEventListener('click', async () => {
      if (!selectedInstanceId) return;
      const prio = document.getElementById('select-proc-priority')?.value || 'Normal';
      try {
        const res = await fetch(`/api/v1/telemetry/instances/${selectedInstanceId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'priority', priority_class: prio })
        });
        const data = await res.json();
        showToast(data.message || 'Приоритет обновлен', data.success ? 'success' : 'danger');
      } catch (e) {
        showToast(`Ошибка SafeOps: ${e.message}`, 'danger');
      }
    });

    // 2. Приостановить процесс
    document.getElementById('btn-safeops-suspend')?.addEventListener('click', async () => {
      if (!selectedInstanceId) return;
      try {
        const res = await fetch(`/api/v1/telemetry/instances/${selectedInstanceId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'suspend' })
        });
        const data = await res.json();
        showToast(data.message, data.success ? 'success' : 'danger');
        selectInstance(selectedInstanceId);
      } catch (e) {
        showToast(`Ошибка: ${e.message}`, 'danger');
      }
    });

    // 3. Возобновить процесс
    document.getElementById('btn-safeops-resume')?.addEventListener('click', async () => {
      if (!selectedInstanceId) return;
      try {
        const res = await fetch(`/api/v1/telemetry/instances/${selectedInstanceId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'resume' })
        });
        const data = await res.json();
        showToast(data.message, data.success ? 'success' : 'danger');
        selectInstance(selectedInstanceId);
      } catch (e) {
        showToast(`Ошибка: ${e.message}`, 'danger');
      }
    });

    // 4. Снять дамп памяти
    document.getElementById('btn-safeops-dump')?.addEventListener('click', async () => {
      if (!selectedInstanceId) return;
      try {
        const res = await fetch(`/api/v1/telemetry/instances/${selectedInstanceId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'dump' })
        });
        const data = await res.json();
        showToast(data.message, data.success ? 'success' : 'danger');
      } catch (e) {
        showToast(`Ошибка: ${e.message}`, 'danger');
      }
    });

    // 5. Завершить процесс (с модальным подтверждением)
    document.getElementById('btn-safeops-kill')?.addEventListener('click', () => {
      if (!selectedInstanceId || !selectedInstanceData) return;
      pendingSafeOpsAction = 'kill';
      document.getElementById('safeops-confirm-text').textContent = `Вы уверены, что хотите принудительно завершить процесс ${selectedInstanceData.name}?`;
      document.getElementById('safeops-target-info').textContent = `PID: ${selectedInstanceData.pid} | #${selectedInstanceData.instance_id} | ${selectedInstanceData.executable_path}`;

      const modalEl = document.getElementById('modal-safeops-confirm');
      if (modalEl && window.bootstrap) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
      }
    });

    document.getElementById('btn-safeops-execute-confirmed')?.addEventListener('click', async () => {
      if (!selectedInstanceId || pendingSafeOpsAction !== 'kill') return;
      try {
        const res = await fetch(`/api/v1/telemetry/instances/${selectedInstanceId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'kill', reason: 'User confirmed kill in Deep Dive UI' })
        });
        const data = await res.json();
        showToast(data.message, data.success ? 'success' : 'danger');

        const modalEl = document.getElementById('modal-safeops-confirm');
        if (modalEl && window.bootstrap) {
          const modal = bootstrap.Modal.getInstance(modalEl);
          modal?.hide();
        }
        selectInstance(selectedInstanceId);
        loadInstancesList();
      } catch (e) {
        showToast(`Ошибка завершения: ${e.message}`, 'danger');
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Сводный мониторинг хоста (Секция 2)
  // ---------------------------------------------------------------------------

  async function fetchHostOverview() {
    await Promise.all([
      fetchHostProcesses(),
      fetchNetworkActivity(),
      fetchLiveFileEvents()
    ]);
  }

  async function fetchHostProcesses() {
    try {
      const res = await fetch('/api/v1/system/summary?process_limit=50');
      if (res.ok) {
        const snap = await res.json();
        const processes = snap.top_processes || snap.processes || [];
        cachedTopProcesses = processes;
        renderHostProcessesTable(processes);
      }
    } catch (e) {
      console.warn('[HostOverview] Error fetching host processes:', e);
    }
  }

  function renderHostProcessesTable(processes) {
    if (processes) {
      cachedTopProcesses = processes;
    }
    if (isProcPaused) return;

    const tbody = document.getElementById('sys-proc-tbody');
    const countBadge = document.getElementById('proc-top-count-badge');
    if (!tbody) return;

    const searchInput = document.getElementById('sys-proc-search');
    const filterText = (searchInput?.value || '').toLowerCase().trim();

    const rawList = Array.isArray(cachedTopProcesses) ? cachedTopProcesses : [];
    const filtered = filterText
      ? rawList.filter(p => String(p.pid).includes(filterText) || (p.name || '').toLowerCase().includes(filterText) || (p.username || '').toLowerCase().includes(filterText))
      : rawList;

    if (countBadge) countBadge.textContent = `${filtered.length} процессов`;

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center py-3 text-muted">Процессы не найдены</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map(p => `
      <tr class="proc-host-row interactive-table-row" data-pid="${p.pid}" style="cursor: pointer;">
        <td class="font-monospace fw-bold text-info">${p.pid}</td>
        <td class="font-monospace text-truncate text-light fw-semibold" style="max-width: 220px;" title="${escapeHtml(p.name)}">${escapeHtml(p.name)}</td>
        <td><span class="badge bg-success-subtle text-success">${escapeHtml(p.status || 'RUNNING')}</span></td>
        <td class="text-end font-monospace">${(p.cpu_percent || 0).toFixed(1)}%</td>
        <td class="text-end font-monospace">${(p.memory_mb || 0).toFixed(1)} MB</td>
        <td class="text-end font-monospace">${p.num_threads || 1}</td>
        <td class="text-muted small">${escapeHtml(p.username || '-')}</td>
        <td class="text-center no-modal-trigger">
          <button class="btn btn-xs btn-outline-info rounded-pill px-2 py-0.5 btn-drilldown-proc" data-pid="${p.pid}" title="Глубокий анализ инстанса">
            🔬 Deep Dive
          </button>
        </td>
      </tr>
    `).join('');

    tbody.querySelectorAll('.proc-host-row').forEach(row => {
      row.addEventListener('click', (e) => {
        if (e.target.closest('button, a, input, select, .no-modal-trigger')) return;
        const pid = parseInt(row.getAttribute('data-pid'), 10);
        const p = filtered.find(x => x.pid === pid);
        if (!p) return;

        const modal = window.AIModalDialog || window.AITableModal;
        if (modal) {
          modal.show({
            title: p.name,
            subtitle: `PID: ${p.pid} | CPU: ${(p.cpu_percent || 0).toFixed(1)}% | RAM: ${(p.memory_mb || 0).toFixed(1)} MB`,
            icon: '⚙️',
            tableType: 'process',
            badges: [
              { text: p.status || 'RUNNING', class: 'badge bg-success' },
              { text: `Threads: ${p.num_threads || 1}`, class: 'badge bg-dark border border-secondary text-info' }
            ],
            metadata: [
              { label: 'Имя процесса', value: p.name },
              { label: 'PID процесса', value: p.pid },
              { label: 'Использование CPU', value: `${(p.cpu_percent || 0).toFixed(1)}%` },
              { label: 'Память (RAM)', value: `${(p.memory_mb || 0).toFixed(1)} MB` },
              { label: 'Количество потоков', value: p.num_threads || 1 },
              { label: 'Пользователь', value: p.username || 'SYSTEM' },
              { label: 'Исполняемый путь', value: p.executable_path || p.exe || '', isCode: true }
            ],
            rawTitle: 'Дамп процесса',
            rawContent: JSON.stringify(p, null, 2),
            actions: [
              {
                label: '🔬 Deep Dive',
                icon: 'bi-cpu',
                class: 'btn-outline-info',
                onClick: () => {
                  const match = cachedActiveInstances.find(i => i.pid === p.pid);
                  if (match) {
                    selectInstance(match.instance_id);
                  }
                  switchToDeepDiveMode();
                }
              }
            ]
          });
        }
      });
    });

    tbody.querySelectorAll('.btn-drilldown-proc').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const pid = parseInt(btn.getAttribute('data-pid'), 10);
        const match = cachedActiveInstances.find(i => i.pid === pid);
        if (match) {
          selectInstance(match.instance_id);
        }
        switchToDeepDiveMode();
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Панель: Сетевая активность программ (Интернет, Отправка и Прием)
  // ---------------------------------------------------------------------------

  async function fetchNetworkActivity() {
    try {
      const res = await fetch('/api/v1/system/network-activity?limit=100');
      if (res.ok) {
        const data = await res.json();
        renderNetworkActivityTable(data);
      }
    } catch (e) {
      console.warn('[ProcessActivity] Failed to fetch network activity:', e);
    }
  }

  function renderNetworkActivityTable(activities) {
    if (activities) {
      cachedNetworkActivities = activities;
    }
    if (isNetPaused) return;

    const tbody = document.getElementById('proc-net-tbody');
    if (!tbody) return;

    const searchInput = document.getElementById('proc-net-search');
    const filterText = (searchInput?.value || '').toLowerCase().trim();
    const countBadge = document.getElementById('proc-netact-count-badge');
    const connsBadge = document.getElementById('proc-netact-conns-badge');

    const rawList = Array.isArray(cachedNetworkActivities) ? cachedNetworkActivities : [];

    const filtered = rawList.filter(item => {
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
        <tr class="proc-net-row interactive-table-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детальной диагностики сетевого соединения">
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
                ${escapeHtml(item.sent_summary || '-')}
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
                ${escapeHtml(item.recv_summary || '-')}
              </div>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.proc-net-row').forEach(row => {
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

        const modal = window.AIModalDialog || window.AITableModal;
        if (modal) {
          modal.show({
            title: `${item.name} (PID: ${item.pid}) — ${item.service_type || item.protocol}`,
            subtitle: `${item.protocol} ${item.local_address} -> ${item.remote_address} | Состояние: ${item.status}`,
            icon: '🌐',
            tableType: 'network',
            badges: [
              { text: item.is_internet ? 'WAN (Интернет)' : 'LAN (Локальный)', class: item.is_internet ? 'badge bg-primary' : 'badge bg-secondary' },
              { text: item.status, class: item.status === 'ESTABLISHED' ? 'badge bg-success' : 'badge bg-warning text-dark' },
              { text: item.protocol, class: 'badge bg-dark border border-secondary text-info' }
            ],
            metadata: [
              { label: 'Программа / Процесс', value: `${item.name} (PID: ${item.pid})` },
              { label: 'Пользователь процесса', value: item.user || 'SYSTEM' },
              { label: 'Локальный сокет', value: item.local_address, isCode: true },
              { label: 'Удаленный сервер', value: item.remote_address, isCode: true },
              { label: 'Служба / Протокол', value: `${item.service_type || 'Custom'} (${item.protocol})` },
              { label: 'Статус сокета', value: item.status },
              { label: 'Отправлено (дельта)', value: formatNetKb(item.delta_sent_kb) },
              { label: 'Принято (дельта)', value: formatNetKb(item.delta_recv_kb) },
              { label: 'Всего передано', value: `Отправлено: ${formatNetKb(item.sent_kb)} | Скачано: ${formatNetKb(item.recv_kb)}` },
              { label: 'Исходящий трафик (описание)', value: item.sent_summary || '-', fullWidth: true },
              { label: 'Входящий трафик (описание)', value: item.recv_summary || '-', fullWidth: true }
            ],
            rawTitle: 'Сырой дамп сетевого сокета (JSON)',
            rawContent: JSON.stringify(item, null, 2),
            requestData: item
          });
        }
      };
    });
  }

  // ---------------------------------------------------------------------------
  // Панель: Изменения файлов в реальном времени (WinAPI ReadDirectoryChangesW)
  // ---------------------------------------------------------------------------

  async function fetchLiveFileEvents() {
    try {
      const [resEvents, resTelem] = await Promise.all([
        fetch('/api/v1/system/file-audit/live-events?limit=30'),
        fetch('/api/v1/system/file-audit/telemetry').catch(() => null)
      ]);

      if (resTelem && resTelem.ok) {
        const telem = await resTelem.json();
        if (telem.watch_dirs || telem.watch_dir) {
          currentWatchDirs = telem.watch_dirs || (telem.watch_dir ? [telem.watch_dir] : []);
          currentWatchDir = currentWatchDirs[0] || telem.watch_dir || '';
        }
      }

      if (!resEvents.ok) return;
      const data = await resEvents.json();
      const events = Array.isArray(data) ? data : (data.events || []);

      if (data.watch_dirs || data.watch_dir) {
        currentWatchDirs = data.watch_dirs || (data.watch_dir ? [data.watch_dir] : []);
        currentWatchDir = currentWatchDirs[0] || data.watch_dir || '';
      }

      cachedFileEvents = events;

      // Обновление бейджа отслеживаемой папки
      const dirPathEl = document.getElementById('proc-watch-dir-path');
      const badge = document.getElementById('proc-watch-dir-badge');
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
        badge.title = `Отслеживаемые каталоги (${currentWatchDirs.length}):\n${currentWatchDirs.join('\n')}\n\n(Нажмите для детальной информации)`;
      }

      const tbody = document.getElementById('proc-watcher-tbody');
      if (!tbody) return;

      if (events.length === 0) {
        const labelDirs = currentWatchDirs.length > 0 ? currentWatchDirs.join(', ') : 'проекта';
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted p-3">Ожидание изменений в папках <code>${escapeHtml(labelDirs)}</code>...</td></tr>`;
        return;
      }

      tbody.innerHTML = events.map((e, idx) => {
        const rootDirHint = e.watch_dir ? (e.watch_dir.split('\\').pop() || e.watch_dir) : '';
        const procDisplay = e.process_name
          ? `<span class="badge bg-dark border border-secondary text-info font-monospace text-truncate d-inline-block" style="max-width: 165px; font-size: 0.72rem;" title="Программа: ${escapeHtml(e.process_name)}${e.process_id ? ` (PID: ${e.process_id})` : ''}"><i class="bi bi-cpu me-1"></i>${escapeHtml(e.process_name)}${e.process_id ? ` [${e.process_id}]` : ''}</span>`
          : `<span class="text-muted" style="font-size: 0.72rem;">—</span>`;
        return `
          <tr class="proc-watcher-row interactive-table-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для детальной диагностики события">
            <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
            <td>
              <span class="badge ${e.is_deletion ? 'bg-danger' : (e.action === 'Created' ? 'bg-success' : 'bg-secondary')}">${escapeHtml(e.action)}</span>
              ${rootDirHint && currentWatchDirs.length > 1 ? `<span class="badge bg-dark border border-secondary text-muted ms-1" style="font-size: 0.65rem;" title="Корень: ${escapeHtml(e.watch_dir)}">${escapeHtml(rootDirHint)}</span>` : ''}
            </td>
            <td>${procDisplay}</td>
            <td class="font-monospace small" style="word-break: break-all; color: var(--text-color);" title="${escapeHtml(e.path)}">${escapeHtml(e.path)}</td>
          </tr>
        `;
      }).join('');

      tbody.querySelectorAll('.proc-watcher-row').forEach(row => {
        row.onclick = () => {
          const idx = parseInt(row.getAttribute('data-idx'), 10);
          const e = events[idx];
          if (!e) return;

          const modal = window.AIModalDialog || window.AITableModal;
          if (modal) {
            modal.show({
              icon: '⚡',
              title: `Файловое событие: ${e.action}`,
              subtitle: `${e.path} | ${e.timestamp}`,
              tableType: 'generic',
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
                { label: 'Папка события', value: e.watch_dir || currentWatchDir || '-' },
                { label: 'Все отслеживаемые папки', value: currentWatchDirs.join('; ') || '-' }
              ],
              rawTitle: 'Детали события WinAPI & Process Info',
              rawContent: JSON.stringify(e, null, 2),
              requestData: e
            });
          }
        };
      });
    } catch (e) {
      console.warn('[ProcessActivity] Failed to fetch live file events:', e);
    }
  }

  async function handleWatchExclusionsClick() {
    try {
      const res = await fetch('/api/v1/system/file-audit/exclusions');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      const ex = data.exclusions || data;
      const modal = window.AIModalDialog || window.AITableModal;
      if (modal) {
        modal.show({
          title: 'Исключения файлового мониторинга (WinAPI)',
          subtitle: `Статус фильтрации: ${data.enabled !== false ? 'ВКЛЮЧЕНА' : 'ВЫКЛЮЧЕНА'}`,
          icon: '🛡️',
          tableType: 'generic',
          badges: [
            { text: data.enabled !== false ? 'Фильтрация активна' : 'Фильтрация выключена', class: data.enabled !== false ? 'badge bg-success' : 'badge bg-secondary' }
          ],
          metadata: [
            { label: 'Игнорируемые расширения', value: (ex.extensions || []).join(', ') || 'нет' },
            { label: 'Игнорируемые каталоги', value: (ex.directories || []).join(', ') || 'нет' },
            { label: 'Игнорируемые процессы', value: (ex.processes || []).join(', ') || 'нет' }
          ],
          rawTitle: 'Правила фильтрации WinAPI Watcher',
          rawContent: JSON.stringify(data, null, 2)
        });
      } else {
        alert(`Исключения файлового мониторинга:\nРасширения: ${(ex.extensions || []).join(', ')}\nКаталоги: ${(ex.directories || []).join(', ')}`);
      }
    } catch (e) {
      showToast(`Ошибка загрузки исключений: ${e.message}`, 'danger');
    }
  }

  async function handleChangeWatchDirClick() {
    const newDir = prompt('Введите абсолютный путь к папке для отслеживания (или несколько через точку с запятой):', currentWatchDirs.join('; '));
    if (!newDir || !newDir.trim()) return;
    const dirsList = newDir.split(';').map(s => s.trim()).filter(Boolean);
    try {
      const res = await fetch('/api/v1/system/file-audit/watch-dirs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paths: dirsList })
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      currentWatchDirs = data.watch_dirs || dirsList;
      showToast(`Отслеживаемые папки обновлены (${currentWatchDirs.length})`, 'success');
      await fetchLiveFileEvents();
    } catch (e) {
      showToast(`Ошибка обновления папок: ${e.message}`, 'danger');
    }
  }

  function initTableResizers() {
    const resizer = document.getElementById('sys-proc-table-resizer');
    const container = document.getElementById('sys-proc-table-container');
    if (!resizer || !container) return;

    let startY = 0;
    let startHeight = 0;

    const onMouseMove = (e) => {
      const delta = e.clientY - startY;
      const newH = Math.max(140, Math.min(850, startHeight + delta));
      container.style.height = `${newH}px`;
    };

    const onMouseUp = () => {
      resizer.classList.remove('resizing');
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    resizer.addEventListener('mousedown', (e) => {
      startY = e.clientY;
      startHeight = container.getBoundingClientRect().height;
      resizer.classList.add('resizing');
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    });
  }

  function switchToDeepDiveMode() {
    currentMode = 'deep-dive';
    document.getElementById('section-deep-dive')?.classList.remove('d-none');
    document.getElementById('section-host-overview')?.classList.add('d-none');
    document.getElementById('btn-mode-deep-dive')?.classList.add('active', 'btn-outline-primary');
    document.getElementById('btn-mode-deep-dive')?.classList.remove('btn-outline-secondary');
    document.getElementById('btn-mode-host-overview')?.classList.remove('active', 'btn-outline-primary');
    document.getElementById('btn-mode-host-overview')?.classList.add('btn-outline-secondary');
  }

  function switchToHostOverviewMode() {
    currentMode = 'host-overview';
    document.getElementById('section-deep-dive')?.classList.add('d-none');
    document.getElementById('section-host-overview')?.classList.remove('d-none');
    document.getElementById('btn-mode-host-overview')?.classList.add('active', 'btn-outline-primary');
    document.getElementById('btn-mode-host-overview')?.classList.remove('btn-outline-secondary');
    document.getElementById('btn-mode-deep-dive')?.classList.remove('active', 'btn-outline-primary');
    document.getElementById('btn-mode-deep-dive')?.classList.add('btn-outline-secondary');
    fetchHostOverview();
  }

  // ---------------------------------------------------------------------------
  // Таймеры автообновления и События UI
  // ---------------------------------------------------------------------------

  function setupEventListeners() {
    // Режимы (Deep Dive VS Host Overview)
    document.getElementById('btn-mode-deep-dive')?.addEventListener('click', switchToDeepDiveMode);
    document.getElementById('btn-mode-host-overview')?.addEventListener('click', switchToHostOverviewMode);

    // Активные / История
    document.getElementById('btn-filter-inst-active')?.addEventListener('click', () => {
      currentInstanceFilter = 'active';
      document.getElementById('btn-filter-inst-active').classList.add('active', 'btn-outline-success');
      document.getElementById('btn-filter-inst-active').classList.remove('btn-outline-secondary');
      document.getElementById('btn-filter-inst-history').classList.remove('active', 'btn-outline-success');
      document.getElementById('btn-filter-inst-history').classList.add('btn-outline-secondary');
      loadInstancesList();
    });

    document.getElementById('btn-filter-inst-history')?.addEventListener('click', () => {
      currentInstanceFilter = 'history';
      document.getElementById('btn-filter-inst-history').classList.add('active', 'btn-outline-success');
      document.getElementById('btn-filter-inst-history').classList.remove('btn-outline-secondary');
      document.getElementById('btn-filter-inst-active').classList.remove('active', 'btn-outline-success');
      document.getElementById('btn-filter-inst-active').classList.add('btn-outline-secondary');
      loadInstancesList();
    });

    // Селектор выпадающего списка
    document.getElementById('deep-dive-instance-select')?.addEventListener('change', (e) => {
      selectInstance(e.target.value);
    });

    // Поиск Deep Dive
    document.getElementById('deep-dive-search')?.addEventListener('input', () => {
      loadInstancesList();
    });

    // Фильтр файлов инстанса
    document.getElementById('inst-file-search')?.addEventListener('input', () => {
      loadInstanceFileActivity();
    });

    // Кнопка глобальной синхронизации
    document.getElementById('btn-global-refresh')?.addEventListener('click', async () => {
      showToast('Синхронизация процессов с ОС...', 'info');
      await loadInstancesList();
      if (selectedInstanceId) {
        await selectInstance(selectedInstanceId);
      }
      if (currentMode === 'host-overview') {
        await fetchHostOverview();
      }
      showToast('Синхронизация завершена', 'success');
    });

    // Интервалы чартов
    document.querySelectorAll('.chart-interval-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.chart-interval-btn').forEach(b => {
          b.classList.remove('active', 'btn-outline-primary');
          b.classList.add('btn-outline-secondary');
        });
        btn.classList.add('active', 'btn-outline-primary');
        btn.classList.remove('btn-outline-secondary');
        currentChartInterval = btn.getAttribute('data-interval') || '1m';
        loadInstanceSamples();
      });
    });

    // Сетевая активность (фильтры, поиск, пауза, обновление)
    document.getElementById('btn-proc-net-filter-internet')?.addEventListener('click', () => {
      currentNetFilter = 'internet';
      document.getElementById('btn-proc-net-filter-internet')?.classList.add('active', 'btn-outline-primary');
      document.getElementById('btn-proc-net-filter-internet')?.classList.remove('btn-outline-secondary');
      document.getElementById('btn-proc-net-filter-all')?.classList.remove('active', 'btn-outline-primary');
      document.getElementById('btn-proc-net-filter-all')?.classList.add('btn-outline-secondary');
      document.getElementById('btn-proc-net-filter-listen')?.classList.remove('active', 'btn-outline-primary');
      document.getElementById('btn-proc-net-filter-listen')?.classList.add('btn-outline-secondary');
      renderNetworkActivityTable();
    });

    document.getElementById('btn-proc-net-filter-all')?.addEventListener('click', () => {
      currentNetFilter = 'all';
      document.getElementById('btn-proc-net-filter-all')?.classList.add('active', 'btn-outline-primary');
      document.getElementById('btn-proc-net-filter-all')?.classList.remove('btn-outline-secondary');
      document.getElementById('btn-proc-net-filter-internet')?.classList.remove('active', 'btn-outline-primary');
      document.getElementById('btn-proc-net-filter-internet')?.classList.add('btn-outline-secondary');
      document.getElementById('btn-proc-net-filter-listen')?.classList.remove('active', 'btn-outline-primary');
      document.getElementById('btn-proc-net-filter-listen')?.classList.add('btn-outline-secondary');
      renderNetworkActivityTable();
    });

    document.getElementById('btn-proc-net-filter-listen')?.addEventListener('click', () => {
      currentNetFilter = 'listen';
      document.getElementById('btn-proc-net-filter-listen')?.classList.add('active', 'btn-outline-primary');
      document.getElementById('btn-proc-net-filter-listen')?.classList.remove('btn-outline-secondary');
      document.getElementById('btn-proc-net-filter-internet')?.classList.remove('active', 'btn-outline-primary');
      document.getElementById('btn-proc-net-filter-internet')?.classList.add('btn-outline-secondary');
      document.getElementById('btn-proc-net-filter-all')?.classList.remove('active', 'btn-outline-primary');
      document.getElementById('btn-proc-net-filter-all')?.classList.add('btn-outline-secondary');
      renderNetworkActivityTable();
    });

    document.getElementById('proc-net-search')?.addEventListener('input', () => {
      renderNetworkActivityTable();
    });

    document.getElementById('btn-proc-pause-net')?.addEventListener('click', (e) => {
      isNetPaused = !isNetPaused;
      e.target.textContent = isNetPaused ? 'Продолжить' : 'Пауза';
      e.target.className = isNetPaused ? 'btn btn-xs btn-warning rounded-pill px-2.5 py-0.5' : 'btn btn-xs btn-outline-secondary rounded-pill px-2.5 py-0.5';
      if (!isNetPaused) fetchNetworkActivity();
    });

    document.getElementById('btn-proc-refresh-net')?.addEventListener('click', async () => {
      await fetchNetworkActivity();
      showToast('Сетевая активность обновлена', 'info');
    });

    // Мониторинг файлов (исключения, смена папки)
    document.getElementById('btn-proc-watch-exclusions')?.addEventListener('click', handleWatchExclusionsClick);
    document.getElementById('btn-proc-change-watch-dir')?.addEventListener('click', handleChangeWatchDirClick);
    document.getElementById('proc-watch-dir-badge')?.addEventListener('click', handleChangeWatchDirClick);

    // Топ процессов хоста (поиск, пауза, обновление)
    document.getElementById('sys-proc-search')?.addEventListener('input', () => {
      renderHostProcessesTable();
    });

    document.getElementById('btn-sys-pause-proc')?.addEventListener('click', (e) => {
      isProcPaused = !isProcPaused;
      e.target.textContent = isProcPaused ? 'Продолжить' : 'Пауза';
      e.target.className = isProcPaused ? 'btn btn-xs btn-warning rounded-pill px-2.5 py-0.5' : 'btn btn-xs btn-outline-secondary rounded-pill px-2.5 py-0.5';
      if (!isProcPaused) fetchHostProcesses();
    });

    document.getElementById('btn-sys-refresh-proc')?.addEventListener('click', async () => {
      await fetchHostProcesses();
      showToast('Список процессов обновлен', 'info');
    });

    initSafeOps();
    initTableResizers();
  }

  function startPolling() {
    // 1. Поллинг для активного инстанса Deep Dive (1 сек)
    if (deepDiveTimer) clearInterval(deepDiveTimer);
    deepDiveTimer = setInterval(async () => {
      if (isDeepDivePaused || currentMode !== 'deep-dive') return;
      if (selectedInstanceId && selectedInstanceData && selectedInstanceData.status === 'RUNNING') {
        await loadInstanceSamples();
      }
    }, 1000);

    // 2. Поллинг инстансов и хоста (3 сек)
    if (hostOverviewTimer) clearInterval(hostOverviewTimer);
    hostOverviewTimer = setInterval(async () => {
      if (currentMode === 'host-overview') {
        await fetchHostOverview();
      } else {
        await loadInstancesList();
      }
    }, 3000);
  }

  // ---------------------------------------------------------------------------
  // Точка входа модуля
  // ---------------------------------------------------------------------------

  async function init() {
    initCharts();
    setupEventListeners();
    await loadInstancesList();
    fetchNetworkActivity();
    fetchLiveFileEvents();
    startPolling();
  }

  window.initProcessesLoadInspectorTab = init;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
