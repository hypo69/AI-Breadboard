/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Telemetry History Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт для отображения графиков телеметрии, многоуровневых роллапов
 *   SQLite и мониторинга состояния базы данных.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/html/telemetry_history_tab/main.js?v=20261006_v2" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/telemetry_history_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 06:10:00
 * =============================================================================
 */

(function () {
  'use strict';

  let chartInstances = {};
  let currentReport = null;
  let autoRefreshTimer = null;
  let currentPage = 1;
  let pageSize = 50;
  let currentSearchQuery = '';

  async function init() {
    bindEvents();
    await Promise.all([
      loadAvailableFiles(),
      fetchReportAndRender(),
      loadRecordsTable(),
      loadRollups(),
      loadDbStats(),
      loadAnomaliesTable(),
    ]);
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('th-btn-refresh');
    if (btnRefresh) {
      btnRefresh.addEventListener('click', async () => {
        btnRefresh.classList.add('disabled');
        await Promise.all([
          fetchReportAndRender(),
          loadRecordsTable(),
          loadAvailableFiles(),
          loadRollups(),
          loadDbStats(),
          loadAnomaliesTable(),
        ]);
        btnRefresh.classList.remove('disabled');
      });
    }

    const selectSource = document.getElementById('th-select-source');
    if (selectSource) {
      selectSource.addEventListener('change', async () => {
        currentPage = 1;
        await Promise.all([fetchReportAndRender(), loadRecordsTable()]);
      });
    }

    const switchAuto = document.getElementById('th-auto-refresh');
    if (switchAuto) {
      switchAuto.addEventListener('change', (e) => {
        if (e.target.checked) {
          if (autoRefreshTimer) clearInterval(autoRefreshTimer);
          autoRefreshTimer = setInterval(async () => {
            await Promise.all([fetchReportAndRender(false), loadDbStats()]);
          }, 5000);
        } else {
          if (autoRefreshTimer) {
            clearInterval(autoRefreshTimer);
            autoRefreshTimer = null;
          }
        }
      });
    }

    const btnExportHtml = document.getElementById('th-btn-export-html');
    if (btnExportHtml) {
      btnExportHtml.addEventListener('click', () => {
        const source = document.getElementById('th-select-source')?.value || '';
        const url = `/api/windows/telemetry/research/dashboard${source ? `?source_path=${encodeURIComponent(source)}` : ''}`;
        window.open(url, '_blank');
      });
    }

    const btnExportJson = document.getElementById('th-btn-export-json');
    if (btnExportJson) {
      btnExportJson.addEventListener('click', () => {
        if (!currentReport) return;
        const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(currentReport, null, 2));
        const a = document.createElement('a');
        a.setAttribute('href', dataStr);
        a.setAttribute('download', `telemetry_report_${currentReport.report_id || Date.now()}.json`);
        document.body.appendChild(a);
        a.click();
        a.remove();
      });
    }

    const inputFilter = document.getElementById('th-input-filter-records');
    if (inputFilter) {
      let debounceTimer = null;
      inputFilter.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          currentSearchQuery = e.target.value.trim();
          currentPage = 1;
          loadRecordsTable();
        }, 300);
      });
    }

    const selectPageSize = document.getElementById('th-select-page-size');
    if (selectPageSize) {
      selectPageSize.addEventListener('change', (e) => {
        pageSize = parseInt(e.target.value, 10) || 50;
        currentPage = 1;
        loadRecordsTable();
      });
    }

    const btnReloadRecords = document.getElementById('th-btn-reload-records');
    if (btnReloadRecords) {
      btnReloadRecords.addEventListener('click', () => loadRecordsTable());
    }

    const btnPrev = document.getElementById('th-btn-prev-page');
    if (btnPrev) {
      btnPrev.addEventListener('click', () => {
        if (currentPage > 1) {
          currentPage--;
          loadRecordsTable();
        }
      });
    }

    const btnNext = document.getElementById('th-btn-next-page');
    if (btnNext) {
      btnNext.addEventListener('click', () => {
        currentPage++;
        loadRecordsTable();
      });
    }

    const btnRefreshFiles = document.getElementById('th-btn-refresh-files');
    if (btnRefreshFiles) {
      btnRefreshFiles.addEventListener('click', () => loadAvailableFiles());
    }

    // Rollups Level Selector & Reload
    const selectRollupLevel = document.getElementById('th-select-rollup-level');
    if (selectRollupLevel) {
      selectRollupLevel.addEventListener('change', () => loadRollups());
    }

    const btnReloadRollups = document.getElementById('th-btn-reload-rollups');
    if (btnReloadRollups) {
      btnReloadRollups.addEventListener('click', () => loadRollups());
    }

    const btnReloadDbStats = document.getElementById('th-btn-reload-dbstats');
    if (btnReloadDbStats) {
      btnReloadDbStats.addEventListener('click', () => loadDbStats());
    }
  }

  async function loadAvailableFiles() {
    const select = document.getElementById('th-select-source');
    const tbody = document.getElementById('th-tbody-files');
    const badge = document.getElementById('th-badge-table-files');

    try {
      const resp = await fetch('/api/windows/telemetry/research/sources');
      if (!resp.ok) return;
      const data = await resp.json();
      const files = data.sources || [];

      if (badge) badge.textContent = files.length;

      if (select) {
        const currentVal = select.value;
        select.innerHTML = '<option value="">Автовыбор источника</option>' +
          files.map(f => `<option value="${f.path}" ${f.path === currentVal ? 'selected' : ''}>${f.filename} (${formatBytes(f.size_bytes)})</option>`).join('');
      }

      if (tbody) {
        if (files.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Лог-файлы не найдены</td></tr>';
        } else {
          tbody.innerHTML = files.map(f => `
            <tr>
              <td><strong class="text-white">${f.filename}</strong></td>
              <td class="font-monospace text-muted small">${f.path}</td>
              <td class="text-end text-nowrap">${formatBytes(f.size_bytes)}</td>
              <td class="text-nowrap text-muted">${f.modified_at || '--'}</td>
              <td class="text-center">
                <button class="btn btn-sm btn-outline-info py-0 px-2 th-btn-select-file" data-path="${f.path}">Выбрать</button>
              </td>
            </tr>
          `).join('');

          tbody.querySelectorAll('.th-btn-select-file').forEach(btn => {
            btn.addEventListener('click', async (e) => {
              const p = e.target.getAttribute('data-path');
              if (select) select.value = p;
              await Promise.all([fetchReportAndRender(), loadRecordsTable()]);
            });
          });
        }
      }
    } catch (err) {
      console.error('Ошибка загрузки списка файлов:', err);
    }
  }

  async function fetchReportAndRender(showLoading = true) {
    const container = document.getElementById('th-charts-container');
    const source = document.getElementById('th-select-source')?.value || '';

    if (showLoading && container) {
      container.innerHTML = `
        <div class="col-12 text-center py-5 text-muted">
          <div class="spinner-border spinner-border-sm text-info me-2" role="status"></div>
          Анализ телеметрии и построение графиков...
        </div>
      `;
    }

    try {
      const url = `/api/windows/telemetry/research/report${source ? `?source_path=${encodeURIComponent(source)}` : ''}`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      currentReport = await resp.json();

      renderKpis(currentReport);
      renderConclusions(currentReport);
      renderCharts(currentReport);
    } catch (err) {
      console.error('Ошибка получения отчета телеметрии:', err);
      if (container) {
        container.innerHTML = `
          <div class="col-12 text-center py-5 text-danger">
            <i class="bi bi-exclamation-triangle-fill fs-3 mb-2 d-block"></i>
            Не удалось загрузить отчет: ${err.message}
          </div>
        `;
      }
    }
  }

  function renderKpis(report) {
    const kpiHealth = document.getElementById('th-kpi-health-score');
    const kpiRecords = document.getElementById('th-kpi-records-count');
    const kpiAnomalies = document.getElementById('th-kpi-anomalies-count');

    if (kpiHealth) {
      const score = report.health_score !== undefined ? report.health_score : '--';
      kpiHealth.textContent = `${score}%`;
      kpiHealth.className = `fw-bold fs-4 mt-0.5 ${score >= 80 ? 'text-success' : score >= 60 ? 'text-warning' : 'text-danger'}`;
    }

    if (kpiRecords) {
      kpiRecords.textContent = (report.records_count || 0).toLocaleString('ru-RU');
    }

    if (kpiAnomalies) {
      const cnt = (report.anomalies || []).length;
      kpiAnomalies.textContent = cnt;
      const badge = document.getElementById('th-badge-table-anomalies');
      if (badge) badge.textContent = cnt;
    }
  }

  function renderConclusions(report) {
    const card = document.getElementById('th-conclusions-card');
    const list = document.getElementById('th-conclusions-list');
    const conclusions = report.conclusions || [];

    if (!card || !list) return;

    if (conclusions.length === 0) {
      card.style.display = 'none';
      return;
    }

    card.style.display = 'block';
    list.innerHTML = conclusions.map(c => `
      <li class="mb-1">
        <strong class="${c.type === 'danger' ? 'text-danger' : c.type === 'warning' ? 'text-warning' : 'text-info'}">${c.title || ''}:</strong>
        <span class="text-light ms-1">${c.description || c.text || ''}</span>
      </li>
    `).join('');
  }

  function renderCharts(report) {
    const container = document.getElementById('th-charts-container');
    if (!container) return;

    // Destroy existing charts
    Object.values(chartInstances).forEach(chart => {
      try { chart.destroy(); } catch (_) {}
    });
    chartInstances = {};

    const charts = report.charts || [];
    if (charts.length === 0) {
      container.innerHTML = '<div class="col-12 text-center py-5 text-muted">Нет данных для графиков</div>';
      return;
    }

    container.innerHTML = charts.map((c, idx) => `
      <div class="${c.col_width === 12 ? 'col-12' : 'col-12 col-lg-6'}">
        <div class="card shadow-sm border-secondary-subtle bg-dark h-100">
          <div class="card-header bg-dark border-secondary py-2 px-3 d-flex justify-content-between align-items-center">
            <span class="fw-semibold text-white small">${c.title || 'График'}</span>
            <span class="badge bg-secondary-subtle text-light small">${c.chart_type || 'line'}</span>
          </div>
          <div class="card-body p-2" style="position: relative; height: 260px;">
            <canvas id="th-chart-canvas-${idx}"></canvas>
          </div>
        </div>
      </div>
    `).join('');

    charts.forEach((c, idx) => {
      const canvas = document.getElementById(`th-chart-canvas-${idx}`);
      if (!canvas) return;

      try {
        const isDoughnut = c.chart_type === 'doughnut' || c.chart_type === 'pie';
        chartInstances[idx] = new Chart(canvas.getContext('2d'), {
          type: c.chart_type || 'line',
          data: {
            labels: c.labels || [],
            datasets: (c.datasets || []).map(ds => ({
              label: ds.label || '',
              data: ds.data || [],
              borderColor: ds.borderColor || '#38bdf8',
              backgroundColor: ds.backgroundColor || 'rgba(56, 189, 248, 0.2)',
              fill: ds.fill !== undefined ? ds.fill : !isDoughnut,
              tension: 0.3,
            })),
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                labels: { color: '#e2e8f0', boxWidth: 12, font: { size: 11 } },
              },
            },
            scales: isDoughnut ? {} : {
              x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#1e293b' } },
              y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#1e293b' } },
            },
          },
        });
      } catch (err) {
        console.error(`Ошибка отрисовки графика ${idx}:`, err);
      }
    });
  }

  async function loadRollups() {
    const selectLevel = document.getElementById('th-select-rollup-level');
    const level = selectLevel ? selectLevel.value : 'hourly';
    const tbody = document.getElementById('th-tbody-rollups');
    const badge = document.getElementById('th-badge-table-rollups');

    try {
      const resp = await fetch(`/api/v1/tc/telemetry/rollups?level=${encodeURIComponent(level)}&limit=100`);
      if (!resp.ok) return;
      const data = await resp.json();
      const rows = data.rollups || [];

      if (badge) badge.textContent = rows.length;

      if (tbody) {
        if (rows.length === 0) {
          tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">Нет агрегированных роллапов уровня "${level}"</td></tr>`;
          return;
        }

        tbody.innerHTML = rows.map(r => {
          const start = r.bucket_start || r.period_start || '--';
          const sensor = r.sensor_id || r.metric_name || r.name || 'Сенсор';
          const count = r.sample_count || r.count || 0;
          const avg = r.avg_value !== undefined ? Number(r.avg_value).toFixed(2) : '--';
          const min = r.min_value !== undefined ? Number(r.min_value).toFixed(2) : '--';
          const max = r.max_value !== undefined ? Number(r.max_value).toFixed(2) : '--';
          const p95 = r.p95_value !== undefined ? Number(r.p95_value).toFixed(2) : '--';

          return `
            <tr>
              <td class="font-monospace text-muted small text-nowrap">${start}</td>
              <td><strong class="text-warning">${sensor}</strong></td>
              <td class="text-end font-monospace text-white">${count}</td>
              <td class="text-end font-monospace fw-bold text-info">${avg}</td>
              <td class="text-end font-monospace text-success">${min}</td>
              <td class="text-end font-monospace text-danger">${max}</td>
              <td class="text-end font-monospace text-white">${p95}</td>
            </tr>
          `;
        }).join('');
      }
    } catch (err) {
      console.error('Ошибка загрузки роллапов:', err);
      if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger py-4">Ошибка загрузки роллапов</td></tr>';
    }
  }

  async function loadDbStats() {
    try {
      const resp = await fetch('/api/v1/tc/telemetry/db-stats');
      if (!resp.ok) return;
      const data = await resp.json();

      const elPath = document.getElementById('th-db-path');
      const elDbSize = document.getElementById('th-db-size');
      const elWalSize = document.getElementById('th-wal-size');
      const elKpiDb = document.getElementById('th-kpi-db-status');

      if (elPath) elPath.textContent = data.db_path || '--';
      if (elDbSize) elDbSize.textContent = `${data.db_size_mb || 0} МБ (${(data.db_size_bytes || 0).toLocaleString()} байт)`;
      if (elWalSize) elWalSize.textContent = `${data.wal_size_mb || 0} МБ (${(data.wal_size_bytes || 0).toLocaleString()} байт)`;
      if (elKpiDb) elKpiDb.textContent = `WAL (${data.db_size_mb || 0}MB) | MMAP 256MB`;

      const counts = data.table_counts || {};
      const elSnap = document.getElementById('th-cnt-snapshots');
      const elProc = document.getElementById('th-cnt-processes');
      const elInc = document.getElementById('th-cnt-incidents');
      const elHourly = document.getElementById('th-cnt-hourly');
      const elDaily = document.getElementById('th-cnt-daily');

      if (elSnap) elSnap.textContent = (counts.system_snapshots || 0).toLocaleString();
      if (elProc) elProc.textContent = (counts.process_snapshots || 0).toLocaleString();
      if (elInc) elInc.textContent = (counts.incidents || 0).toLocaleString();
      if (elHourly) elHourly.textContent = (counts.telemetry_hourly || 0).toLocaleString();
      if (elDaily) elDaily.textContent = (counts.telemetry_daily || 0).toLocaleString();
    } catch (err) {
      console.error('Ошибка загрузки статистики БД:', err);
    }
  }

  async function loadAnomaliesTable() {
    const tbody = document.getElementById('th-tbody-anomalies');
    const headerCount = document.getElementById('th-anomalies-header-count');

    try {
      const resp = await fetch('/api/v1/tc/telemetry/incidents?limit=50');
      if (!resp.ok) return;
      const data = await resp.json();
      const incidents = data.incidents || [];

      if (headerCount) headerCount.textContent = incidents.length;

      if (tbody) {
        if (incidents.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Аномалий и инцидентов не зафиксировано</td></tr>';
          return;
        }

        tbody.innerHTML = incidents.map(inc => {
          const sev = (inc.severity || 'warning').toLowerCase();
          const sevBadge = sev === 'critical' || sev === 'high' ? 'bg-danger' : sev === 'warning' ? 'bg-warning text-dark' : 'bg-info text-dark';
          const time = inc.created_at || inc.timestamp || '--';
          const trigger = inc.trigger_type || inc.type || 'Anomaly';
          const metric = inc.metric_name || inc.sensor || 'System';
          const desc = inc.description || inc.message || JSON.stringify(inc);

          return `
            <tr>
              <td class="text-center"><span class="badge ${sevBadge}">${sev.toUpperCase()}</span></td>
              <td class="font-monospace small text-muted text-nowrap">${time}</td>
              <td><strong class="text-white">${trigger}</strong></td>
              <td><span class="text-info">${metric}</span></td>
              <td class="small text-light">${desc}</td>
            </tr>
          `;
        }).join('');
      }
    } catch (err) {
      console.error('Ошибка загрузки аномалий:', err);
    }
  }

  async function loadRecordsTable() {
    const tbody = document.getElementById('th-tbody-records');
    const badge = document.getElementById('th-badge-table-records');
    const pageInfo = document.getElementById('th-records-pagination-info');
    const pageIndicator = document.getElementById('th-page-indicator');
    const btnPrev = document.getElementById('th-btn-prev-page');
    const btnNext = document.getElementById('th-btn-next-page');

    const source = document.getElementById('th-select-source')?.value || '';
    const queryParams = new URLSearchParams({
      page: currentPage.toString(),
      page_size: pageSize.toString(),
    });
    if (source) queryParams.set('source_path', source);
    if (currentSearchQuery) queryParams.set('query', currentSearchQuery);

    try {
      const resp = await fetch(`/api/windows/telemetry/research/records?${queryParams.toString()}`);
      if (!resp.ok) return;
      const data = await resp.json();

      if (badge) badge.textContent = (data.total || 0).toLocaleString('ru-RU');
      if (pageInfo) {
        const start = ((data.page || 1) - 1) * (data.page_size || 50) + 1;
        const end = Math.min((data.page || 1) * (data.page_size || 50), data.total || 0);
        pageInfo.textContent = `${data.total ? start : 0}–${end} из ${data.total || 0}`;
      }
      if (pageIndicator) pageIndicator.textContent = `${data.page || 1} / ${data.total_pages || 1}`;
      if (btnPrev) btnPrev.disabled = (data.page || 1) <= 1;
      if (btnNext) btnNext.disabled = (data.page || 1) >= (data.total_pages || 1);

      if (!tbody) return;

      if (!data.items || data.items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Нет записей по заданному запросу</td></tr>';
        return;
      }

      tbody.innerHTML = data.items.map(r => {
        const ts = r.timestamp || r.time || r.datetime || '--';
        const metric = r.metric_name || r.sensor_name || r.name || r.category || 'telemetry';
        const val = r.value !== undefined ? r.value : r.val !== undefined ? r.val : '--';
        const unit = r.unit || r.unit_symbol || '';
        const details = Object.entries(r)
          .filter(([k]) => !['timestamp', 'time', 'datetime', 'metric_name', 'sensor_name', 'name', 'value', 'val', 'unit', 'unit_symbol'].includes(k))
          .map(([k, v]) => `${k}=${typeof v === 'object' ? JSON.stringify(v) : v}`)
          .join(', ');

        return `
          <tr>
            <td class="text-nowrap small font-monospace text-muted">${ts}</td>
            <td><strong class="text-info">${metric}</strong></td>
            <td class="text-end font-monospace fw-bold text-white">${val}</td>
            <td class="text-center small text-secondary">${unit}</td>
            <td class="small text-truncate text-muted" style="max-width: 320px;" title="${details}">${details || '—'}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Ошибка загрузки записей:', err);
      if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger py-4">Ошибка загрузки записей</td></tr>';
    }
  }

  function formatBytes(bytes) {
    if (bytes === 0 || !bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
