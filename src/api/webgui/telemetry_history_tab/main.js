/**
 * =============================================================================
 * Process Name: Windows Telemetry History & Visualization Logic
 * =============================================================================
 * Description:
 *   Клиентский контроллер вкладки визуализации истории телеметрии:
 *   построение графиков Chart.js, табличный рендеринг логов, пагинация,
 *   детекция аномалий и интеграция с REST API.
 *
 * File: main.js
 * Project: AI-Breadboard
 * Module: WebInterface.TelemetryHistoryTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
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

  /**
   * Инициализация вкладки
   */
  async function init() {
    bindEvents();
    await loadAvailableFiles();
    await fetchReportAndRender();
    await loadRecordsTable();
  }

  /**
   * Привязка обработчиков событий
   */
  function bindEvents() {
    const btnRefresh = document.getElementById('th-btn-refresh');
    if (btnRefresh) {
      btnRefresh.addEventListener('click', async () => {
        btnRefresh.classList.add('disabled');
        await Promise.all([fetchReportAndRender(), loadRecordsTable(), loadAvailableFiles()]);
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
            await fetchReportAndRender(false);
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

    const btnReloadRecords = document.getElementById('th-btn-reload-records');
    if (btnReloadRecords) {
      btnReloadRecords.addEventListener('click', loadRecordsTable);
    }

    const btnRefreshFiles = document.getElementById('th-btn-refresh-files');
    if (btnRefreshFiles) {
      btnRefreshFiles.addEventListener('click', loadAvailableFiles);
    }
  }

  /**
   * Загрузка списка доступных файлов логов
   */
  async function loadAvailableFiles() {
    try {
      const resp = await fetch('/api/windows/telemetry/research/files');
      if (!resp.ok) return;
      const files = await resp.json();

      const selectSource = document.getElementById('th-select-source');
      const badgeFiles = document.getElementById('th-badge-table-files');
      if (badgeFiles) badgeFiles.textContent = files.length;

      if (selectSource) {
        const curVal = selectSource.value;
        selectSource.innerHTML = '<option value="">Все обнаруженные логи</option>';
        files.forEach((f) => {
          const opt = document.createElement('option');
          opt.value = f.path;
          opt.textContent = `${f.name} (${formatBytes(f.size_bytes)})`;
          if (f.path === curVal) opt.selected = true;
          selectSource.appendChild(opt);
        });
      }

      const tbody = document.getElementById('th-tbody-files');
      if (tbody) {
        if (files.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Файлы логов не обнаружены</td></tr>';
          return;
        }
        tbody.innerHTML = files
          .map((f) => {
            const dateStr = new Date(f.modified * 1000).toLocaleString('ru-RU');
            return `
            <tr>
              <td><span class="fw-semibold text-info">${f.name}</span></td>
              <td><code class="small text-muted">${f.path}</code></td>
              <td class="text-end font-monospace">${formatBytes(f.size_bytes)}</td>
              <td>${dateStr}</td>
              <td class="text-center">
                <button class="btn btn-xs btn-outline-primary py-0 px-2 th-btn-select-file" data-path="${f.path}">
                  Анализ
                </button>
              </td>
            </tr>
          `;
          })
          .join('');

        tbody.querySelectorAll('.th-btn-select-file').forEach((btn) => {
          btn.addEventListener('click', (e) => {
            const p = e.target.getAttribute('data-path');
            if (selectSource) {
              selectSource.value = p;
              const evt = new Event('change');
              selectSource.dispatchEvent(evt);
            }
          });
        });
      }
    } catch (err) {
      console.warn('Ошибка загрузки списка файлов логов:', err);
    }
  }

  /**
   * Получение отчета исследования и рендеринг графиков
   */
  async function fetchReportAndRender(showLoading = true) {
    const container = document.getElementById('th-charts-container');
    if (showLoading && container && Object.keys(chartInstances).length === 0) {
      container.innerHTML = `
        <div class="col-12 text-center py-5 text-muted">
          <div class="spinner-border spinner-border-sm text-info me-2" role="status"></div>
          Выполняется анализ телеметрии и построение графиков...
        </div>
      `;
    }

    try {
      const source = document.getElementById('th-select-source')?.value || null;
      const resp = await fetch('/api/windows/telemetry/research/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_path: source }),
      });

      if (!resp.ok) {
        if (container) {
          container.innerHTML = `
            <div class="col-12 text-center py-4 text-warning">
              <i class="bi bi-exclamation-triangle fs-4 d-block mb-1"></i>
              Не удалось загрузить данные исследования (${resp.status})
            </div>
          `;
        }
        return;
      }

      currentReport = await resp.json();
      renderKPIs(currentReport);
      renderConclusions(currentReport);
      renderAnomalies(currentReport);
      renderCharts(currentReport.charts || []);
    } catch (err) {
      console.error('Ошибка анализа телеметрии:', err);
      if (container) {
        container.innerHTML = `
          <div class="col-12 text-center py-4 text-danger">
            <i class="bi bi-bug fs-4 d-block mb-1"></i>
            Ошибка выполнения анализа: ${err.message}
          </div>
        `;
      }
    }
  }

  /**
   * Рендеринг KPI карточек
   */
  function renderKPIs(report) {
    const elHealth = document.getElementById('th-kpi-health-score');
    const elHealthIcon = document.getElementById('th-kpi-health-icon');
    if (elHealth) {
      const score = Math.round(report.health_score || 100);
      elHealth.textContent = `${score}%`;
      elHealth.className = score >= 85 ? 'fw-bold fs-4 mt-0.5 text-success' : score >= 60 ? 'fw-bold fs-4 mt-0.5 text-warning' : 'fw-bold fs-4 mt-0.5 text-danger';
      if (elHealthIcon) {
        elHealthIcon.className = score >= 85 ? 'fs-2 text-success opacity-75' : score >= 60 ? 'fs-2 text-warning opacity-75' : 'fs-2 text-danger opacity-75';
      }
    }

    const elRecords = document.getElementById('th-kpi-records-count');
    if (elRecords) elRecords.textContent = report.records_analyzed.toLocaleString('ru-RU');

    const elAnomalies = document.getElementById('th-kpi-anomalies-count');
    if (elAnomalies) {
      const anomCount = (report.anomalies || []).length;
      elAnomalies.textContent = anomCount;
      elAnomalies.className = anomCount > 0 ? 'fw-bold fs-4 text-warning mt-0.5' : 'fw-bold fs-4 text-success mt-0.5';
    }

    const elTimeWindow = document.getElementById('th-kpi-time-window');
    if (elTimeWindow) {
      const s = report.time_window_start ? report.time_window_start.split('T')[0] : '';
      const e = report.time_window_end ? report.time_window_end.split('T')[0] : '';
      elTimeWindow.textContent = s && e ? `${s} — ${e}` : 'Актуальный срез';
    }
  }

  /**
   * Рендеринг выводов аналитического движка
   */
  function renderConclusions(report) {
    const card = document.getElementById('th-conclusions-card');
    const list = document.getElementById('th-conclusions-list');
    if (!card || !list) return;

    if (report.summary_conclusions && report.summary_conclusions.length > 0) {
      list.innerHTML = report.summary_conclusions.map((c) => `<li>${c}</li>`).join('');
      card.style.display = 'block';
    } else {
      card.style.display = 'none';
    }
  }

  /**
   * Рендеринг таблицы аномалий
   */
  function renderAnomalies(report) {
    const tbody = document.getElementById('th-tbody-anomalies');
    const badge = document.getElementById('th-badge-table-anomalies');
    const headerCount = document.getElementById('th-anomalies-header-count');
    const anomalies = report.anomalies || [];

    if (badge) badge.textContent = anomalies.length;
    if (headerCount) headerCount.textContent = anomalies.length;

    if (!tbody) return;
    if (anomalies.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Аномалий и критических отклонений не зафиксировано</td></tr>';
      return;
    }

    tbody.innerHTML = anomalies
      .map((a) => {
        const isCrit = a.severity === 'critical';
        const badgeCls = isCrit ? 'bg-danger text-white' : 'bg-warning text-dark';
        return `
        <tr>
          <td class="text-center"><span class="badge ${badgeCls}">${a.severity.toUpperCase()}</span></td>
          <td class="text-nowrap small font-monospace">${a.timestamp || '--'}</td>
          <td><strong class="text-info">${a.metric}</strong></td>
          <td><span class="fw-bold">${a.value}</span> <span class="text-muted small">(порог: ${a.threshold})</span></td>
          <td>${a.description}</td>
        </tr>
      `;
      })
      .join('');
  }

  /**
   * Построение графиков с помощью Chart.js
   */
  function renderCharts(charts) {
    const container = document.getElementById('th-charts-container');
    if (!container) return;

    // Уничтожаем старые инстансы Chart.js
    Object.values(chartInstances).forEach((inst) => {
      try {
        inst.destroy();
      } catch (e) {}
    });
    chartInstances = {};

    if (!charts || charts.length === 0) {
      container.innerHTML = `
        <div class="col-12 text-center py-5 text-muted">
          <i class="bi bi-info-circle fs-4 d-block mb-1"></i>
          Нет достаточного количества данных для построения графиков
        </div>
      `;
      return;
    }

    // Рендерим сетку карточек под графики
    container.innerHTML = charts
      .map((c) => {
        const colClass = c.chart_type === 'doughnut' ? 'col-12 col-md-6' : 'col-12 col-xl-6';
        return `
        <div class="${colClass}">
          <div class="card shadow-sm border-secondary h-100" style="background: #0f172a; border-radius: 8px;">
            <div class="card-header bg-dark border-secondary py-2 px-3 d-flex justify-content-between align-items-center">
              <div>
                <h6 class="mb-0 fw-bold text-white small">${c.title}</h6>
                <small class="text-muted" style="font-size: 0.7rem;">${c.description || ''}</small>
              </div>
              <span class="badge bg-secondary small">${c.chart_type.toUpperCase()}</span>
            </div>
            <div class="card-body p-2" style="position: relative; min-height: 250px; max-height: 320px;">
              <canvas id="${c.id}"></canvas>
            </div>
          </div>
        </div>
      `;
      })
      .join('');

    // Инициализируем Chart.js для каждого canvas
    if (typeof Chart === 'undefined') {
      loadChartJsScript(() => initChartObjects(charts));
    } else {
      initChartObjects(charts);
    }
  }

  function loadChartJsScript(callback) {
    if (document.getElementById('chartjs-cdn-script')) return;
    const script = document.createElement('script');
    script.id = 'chartjs-cdn-script';
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = callback;
    document.head.appendChild(script);
  }

  function initChartObjects(charts) {
    charts.forEach((cfg) => {
      const canvas = document.getElementById(cfg.id);
      if (!canvas) return;
      const ctx = canvas.getContext('2d');

      const isDoughnut = cfg.chart_type === 'doughnut';

      const chartObj = new Chart(ctx, {
        type: cfg.chart_type,
        data: {
          labels: cfg.labels,
          datasets: cfg.datasets,
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 400 },
          plugins: {
            legend: {
              position: isDoughnut ? 'right' : 'top',
              labels: {
                color: '#cbd5e1',
                boxWidth: 12,
                font: { size: 11 },
              },
            },
            tooltip: {
              mode: isDoughnut ? 'nearest' : 'index',
              intersect: false,
            },
          },
          scales: isDoughnut
            ? {}
            : {
                x: {
                  ticks: { color: '#94a3b8', font: { size: 10 }, maxRotation: 45, maxTicksLimit: 12 },
                  grid: { color: '#1e293b' },
                },
                y: {
                  ticks: { color: '#94a3b8', font: { size: 10 } },
                  grid: { color: '#1e293b' },
                  title: {
                    display: !!cfg.y_axis_label,
                    text: cfg.y_axis_label || '',
                    color: '#94a3b8',
                    font: { size: 11 },
                  },
                },
              },
        },
      });

      chartInstances[cfg.id] = chartObj;
    });
  }

  /**
   * Загрузка записей логов в таблицу
   */
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

      if (badge) badge.textContent = data.total.toLocaleString('ru-RU');
      if (pageInfo) {
        const start = (data.page - 1) * data.page_size + 1;
        const end = Math.min(data.page * data.page_size, data.total);
        pageInfo.textContent = `Показано ${data.total > 0 ? start : 0}–${end} из ${data.total}`;
      }
      if (pageIndicator) pageIndicator.textContent = `${data.page} / ${data.total_pages}`;
      if (btnPrev) btnPrev.disabled = data.page <= 1;
      if (btnNext) btnNext.disabled = data.page >= data.total_pages;

      if (!tbody) return;
      if (data.items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Нет записей по заданному запросу</td></tr>';
        return;
      }

      tbody.innerHTML = data.items
        .map((r) => {
          const ts = r.timestamp || r.time || r.datetime || '--';
          const metric = r.metric_name || r.sensor_name || r.name || r.category || 'telemetry';
          const val = r.value !== undefined ? r.value : r.val !== undefined ? r.val : '--';
          const unit = r.unit || r.unit_symbol || '';
          
          // Дополнительные детали
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
        })
        .join('');
    } catch (err) {
      console.error('Ошибка загрузки таблицы записей:', err);
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

  // Запуск при загрузке
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
