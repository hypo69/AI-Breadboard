/**
 * =============================================================================
 * Process Name: Telemetry Research Web GUI Controller
 * =============================================================================
 * Description:
 *   Клиентский JavaScript контроллер для вкладки глубокого исследования телеметрии:
 *   запуск исследовательских сценариев, проверка системных гипотез, рендеринг
 *   матрицы корреляций, графиков Chart.js, детекции аномалий и записей.
 *
 * File: main.js
 * Project: AI-Breadboard
 * Module: WebInterface.TelemetryResearchTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

let trCurrentReport = null;
let trChartsInstances = [];
let trCurrentPage = 1;
const trPageSize = 25;
let trTotalPages = 1;
let trSearchQuery = 'i18n.t('auto__export_async_function_inittelemetryresearchtab_bindevents_await_loadsources_await_runresearch_function_bindevents_const_btnrun_document_getelementbyid__aeed93')tr-btn-run');
  if (btnRun) {
    btnRun.onclick = () => runResearch();
  }

  const btnDashboard = document.getElementById('tr-btn-dashboard');
  if (btnDashboard) {
    btnDashboard.onclick = () => openHtmlDashboard();
  }

  const btnJson = document.getElementById('tr-btn-json');
  if (btnJson) {
    btnJson.onclick = () => downloadJsonReport();
  }

  const selectSource = document.getElementById('tr-select-source');
  if (selectSource) {
    selectSource.onchange = () => runResearch();
  }

  const searchBtn = document.getElementById('tr-records-search-btn');
  const searchInput = document.getElementById('tr-records-search');
  if (searchBtn && searchInput) {
    searchBtn.onclick = () => {
      trSearchQuery = searchInput.value.trim();
      trCurrentPage = 1;
      loadRecords();
    };
    searchInput.onkeydown = (e) => {
      if (e.key === 'Enter') {
        trSearchQuery = searchInput.value.trim();
        trCurrentPage = 1;
        loadRecords();
      }
    };
  }

  const prevBtn = document.getElementById('tr-records-prev-btn');
  const nextBtn = document.getElementById('tr-records-next-btn');
  if (prevBtn) {
    prevBtn.onclick = () => {
      if (trCurrentPage > 1) {
        trCurrentPage--;
        loadRecords();
      }
    };
  }
  if (nextBtn) {
    nextBtn.onclick = () => {
      if (trCurrentPage < trTotalPages) {
        trCurrentPage++;
        loadRecords();
      }
    };
  }

  const recordsTabBtn = document.getElementById('tr-tab-records-btn');
  if (recordsTabBtn) {
    recordsTabBtn.addEventListener('shown.bs.tabi18n.t('auto__loadrecords_async_function_loadsources_const_select_document_getelementbyid__415483')tr-select-source');
  if (!select) return;

  try {
    const res = await fetch('/apps/telemetry_research/sources');
    if (!res.ok) return;
    const files = await res.json();
    select.innerHTML = '<option value="">Все доступные логи телеметрии</option>';
    files.forEach((f) => {
      const opt = document.createElement('option');
      opt.value = f.path;
      const sizeKb = (f.size_bytes / 1024).toFixed(1);
      opt.textContent = `${f.name} (${sizeKb} KB)`;
      select.appendChild(opt);
    });
  } catch (err) {
    console.warn(i18n.t('auto__telemetryresearch__e197e9'), err);
  }
}

/**
 * Запуск глубокого исследования телеметрии.
 */
async function runResearch() {
  const btnRun = document.getElementById('tr-btn-run');
  const selectSource = document.getElementById('tr-select-source');
  const sourcePath = selectSource ? selectSource.value : null;

  if (btnRun) {
    btnRun.disabled = true;
    btnRun.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Анализ...';
  }

  try {
    const res = await fetch('/apps/telemetry_research/run-research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_source_path_sourcepath_null_if_res_ok_throw_new_error_res_status_const_report_await_res_json_trcurrentreport_report_renderkpi_report_renderhypotheses_report_hypotheses_rendercorrelations_report_correlations_rendercharts_report_base_report_charts_renderanomalies_report_base_report_anomalies_report_base_report_device_summary_if_window_toast_window_toast_success__5653c8')Исследование завершеноi18n.t('auto__report_base_report_records_analyzed_catch_err_console_error__f12b13')[TelemetryResearch] Ошибка анализа:', err);
    if (window.toast) {
      window.toast.error(i18n.t('auto___f0f7da'), err.message);
    }
  } finally {
    if (btnRun) {
      btnRun.disabled = false;
      btnRun.innerHTML = '<i class="bi bi-play-circle-fill"></i> <span>Исследовать</span>i18n.t('auto__kpi_function_renderkpi_report_const_base_report_base_report_const_valhealth_document_getelementbyid__7a0af3')tr-val-health');
  const progHealth = document.getElementById('tr-progress-health');
  const valRecords = document.getElementById('tr-val-records');
  const valTimespan = document.getElementById('tr-val-timespan');
  const valHypotheses = document.getElementById('tr-val-hypotheses');
  const valAnomalies = document.getElementById('tr-val-anomalies');
  const valDevices = document.getElementById('tr-val-devices');

  if (valHealth) valHealth.textContent = `${base.health_score}`;
  if (progHealth) {
    progHealth.style.width = `${base.health_score}%`;
    progHealth.className = `progress-bar ${
      base.health_score >= 80 ? 'bg-success' : base.health_score >= 60 ? 'bg-warning' : 'bg-danger'
    }`;
  }

  if (valRecords) valRecords.textContent = `${base.records_analyzed}`;
  if (valTimespan && base.time_range) {
    valTimespan.textContent = `${base.time_range.start ? base.time_range.start.slice(11, 19) : ''} - ${
      base.time_range.end ? base.time_range.end.slice(11, 19) : 'i18n.t('auto__const_confirmedcount_report_hypotheses_filter_h_h_confirmed_length_if_valhypotheses_valhypotheses_textcontent_confirmedcount_report_hypotheses_report_hypotheses_length_0_if_valanomalies_valanomalies_textcontent_base_anomalies_length_if_valdevices_valdevices_textcontent_base_device_summary_error_count_0_base_device_summary_error_count__f44a09')Оборудование в норме';
  }

  // Summary alert banner
  const banner = document.getElementById('tr-summary-banner');
  const bannerText = document.getElementById('tr-summary-text');
  if (banner && bannerText && report.investigation_summary) {
    banner.classList.remove('d-nonei18n.t('auto__bannertext_textcontent_report_investigation_summary_function_renderhypotheses_hypotheses_const_container_document_getelementbyid__581640')tr-hypotheses-list');
  if (!container) return;

  if (!hypotheses || hypotheses.length === 0) {
    container.innerHTML = '<div class="col-12 text-center text-muted py-4">Гипотезы не проверены</div>';
    return;
  }

  container.innerHTML = '';
  hypotheses.forEach((h) => {
    const col = document.createElement('div');
    col.className = 'col-12 col-md-6';

    const cardBorder = h.confirmed ? 'border-warning' : 'border-success-subtle';
    const statusBadge = h.confirmed
      ? '<span class="badge bg-warning text-dark"><i class="bi bi-exclamation-triangle"></i> Подтверждена</span>'
      : '<span class="badge bg-success"><i class="bi bi-check-circle"></i> В норме</span>';

    const evidenceItems = h.evidence.map((ev) => `<li>${ev}</li>`).join('');

    col.innerHTML = `
      <div class="card bg-dark ${cardBorder} h-100 shadow-sm">
        <div class="card-header bg-transparent border-secondary d-flex justify-content-between align-items-center">
          <span class="fw-bold text-light">${h.title}</span>
          ${statusBadge}
        </div>
        <div class="card-body p-3 small">
          <p class="text-muted mb-2">${h.description}</p>
          <div class="mb-2">
            <strong class="text-secondaryi18n.t('auto__strong_ul_class__9b0c61')text-light text-opacity-75 ps-3 mb-1">${evidenceItems}</ul>
          </div>
          ${
            h.recommendation
              ? `<div class="p-2 rounded bg-body-tertiary bg-opacity-10 text-info mt-2">
                   <strong>👉 Рекомендация:</strong> ${h.recommendation}
                 </div>`
              : ''
          }
        </div>
        <div class="card-footer bg-transparent border-secondary text-muted small d-flex justify-content-between">
          <span>ID: <code>${h.hypothesis_id}</code></span>
          <span>Уверенность: <strong>${Math.round(h.confidence * 100)}%</strong></span>
        </div>
      </div>
    `;
    container.appendChild(col);
  });
}

/**
 * Отрисовка матрицы корреляций.
 */
function renderCorrelations(correlations) {
  const tbody = document.getElementById('tr-correlations-tbody');
  const countBadge = document.getElementById('tr-correlations-count');
  if (!tbody) return;

  if (!correlations || correlations.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Корреляции не рассчитаны</td></tr>';
    if (countBadge) countBadge.textContent = i18n.t('auto_0__999dd8');
    return;
  }

  if (countBadge) countBadge.textContent = `${correlations.length} пар`;

  tbody.innerHTML = correlations
    .map((c) => {
      const absVal = Math.abs(c.coefficient);
      let coeffBadgeClass = 'bg-secondary';
      if (absVal >= 0.7) coeffBadgeClass = 'bg-danger';
      else if (absVal >= 0.5) coeffBadgeClass = 'bg-warning text-dark';
      else if (absVal >= 0.3) coeffBadgeClass = 'bg-info text-dark';

      return `
        <tr>
          <td><code class="text-info">${c.metric_a}</code></td>
          <td><code class="text-info">${c.metric_b}</code></td>
          <td><span class="badge ${coeffBadgeClass} font-monospace">${c.coefficient > 0 ? '+' : ''}${c.coefficient.toFixed(3)}</span></td>
          <td>${c.sample_size} точек</td>
          <td class="text-light text-opacity-75">${c.interpretation}</td>
        </tr>
      `;
    })
    .join('i18n.t('auto__chart_js_function_rendercharts_charts_const_container_document_getelementbyid__ba34b3')tr-charts-containeri18n.t('auto__if_container_return_trchartsinstances_foreach_inst_try_inst_destroy_catch_trchartsinstances_if_charts_charts_length_0_container_innerhtml__bd323d')<div class="col-12 text-center text-muted py-4">Нет доступных графиков</div>';
    return;
  }

  container.innerHTML = '';

  charts.forEach((ch, idx) => {
    const col = document.createElement('div');
    col.className = 'col-12 col-xl-6';

    const canvasId = `tr-chart-canvas-${idx}`;
    col.innerHTML = `
      <div class="card bg-dark border-secondary h-100 shadow-sm">
        <div class="card-header bg-transparent border-secondary d-flex justify-content-between align-items-center">
          <span class="fw-bold text-light">${ch.title}</span>
          <span class="badge bg-secondary small">${ch.chart_type}</span>
        </div>
        <div class="card-body p-2" style="position: relative; height: 280px;">
          <canvas id="${canvasId}"></canvas>
        </div>
      </div>
    `;
    container.appendChild(col);

    const ctx = document.getElementById(canvasId);
    if (ctx && typeof Chart !== 'undefined') {
      const labels = ch.labels.map((l) => (l.length > 19 ? l.slice(11, 19) : l));
      const datasets = ch.datasets.map((ds) => ({
        label: ds.label,
        data: ds.data,
        borderColor: ds.color || '#3b82f6',
        backgroundColor: (ds.color || '#3b82f6') + '22',
        borderWidth: 2,
        fill: ch.chart_type === 'area',
        tension: 0.25,
        pointRadius: ds.data.length > 50 ? 0 : 3,
      }));

      const newInst = new Chart(ctx, {
        type: ch.chart_type === 'bar' ? 'bar' : 'line',
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 400 },
          scales: {
            x: {
              grid: { color: 'rgba(255,255,255,0.06)' },
              ticks: { color: '#9ca3af', font: { size: 10 } },
            },
            y: {
              grid: { color: 'rgba(255,255,255,0.06)' },
              ticks: { color: '#9ca3af', font: { size: 10 } },
            },
          },
          plugins: {
            legend: {
              labels: { color: '#e5e7ebi18n.t('auto__boxwidth_12_font_size_11_trchartsinstances_push_newinst_function_renderanomalies_anomalies_devicesummary_const_tbody_document_getelementbyid__1a3f0d')tr-anomalies-tbody');
  const anomBadge = document.getElementById('tr-anomalies-badge');
  const devBadge = document.getElementById('tr-devices-badge');
  const devContent = document.getElementById('tr-devices-content');

  if (anomBadge) anomBadge.textContent = anomalies ? `${anomalies.length}` : '0';

  if (tbody) {
    if (!anomalies || anomalies.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-success py-3"><i class="bi bi-check-circle"></i> Аномалий в метриках не зафиксировано</td></tr>';
    } else {
      tbody.innerHTML = anomalies
        .map((a) => {
          const sevClass = a.severity === 'critical' ? 'bg-danger' : a.severity === 'high' ? 'bg-warning text-dark' : 'bg-info text-dark';
          return `
            <tr>
              <td class="text-muted">${a.timestamp ? a.timestamp.slice(11, 19) : '--'}</td>
              <td><strong>${a.metric}</strong></td>
              <td><span class="badge ${sevClass}">${a.severity}</span></td>
              <td><code class="text-warning">${a.value}</code> / ${a.threshold}</td>
              <td class="text-light text-opacity-75">${a.message}</td>
            </tr>
          `;
        })
        .join('');
    }
  }

  if (deviceSummary && devContent) {
    const hasIssues = deviceSummary.error_count > 0 || deviceSummary.flapping_devices.length > 0;
    if (devBadge) {
      devBadge.className = `badge ${hasIssues ? 'bg-danger' : 'bg-success'}`;
      devBadge.textContent = hasIssues ? i18n.t('auto___5f5f86') : i18n.t('auto___2b9442');
    }

    let flapHtml = '<span class="text-success">Нет</span>';
    if (deviceSummary.flapping_devices && deviceSummary.flapping_devices.length > 0) {
      flapHtml = deviceSummary.flapping_devices.map((d) => `<span class="badge bg-warning text-dark me-1">${d}</span>`).join('');
    }

    devContent.innerHTML = `
      <div class="mb-2i18n.t('auto__strong_strong_devicesummary_total_events_div_div_class__811ed8')mb-2i18n.t('auto__strong_strong_span_class__5f8352')${deviceSummary.error_count > 0 ? 'text-danger fw-bold' : 'text-success'}">${deviceSummary.error_count}</span></div>
      <div class="mb-2"><strong>Флаппирующие устройства:</strong> ${flapHtml}</div>
    `;
  }
}

/**
 * Загрузка записей телеметрии с пагинацией.
 */
async function loadRecords() {
  const tbody = document.getElementById('tr-records-tbody');
  const infoEl = document.getElementById('tr-records-pagination-info');
  const selectSource = document.getElementById('tr-select-source');
  const sourcePath = selectSource ? selectSource.value : null;

  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3"><span class="spinner-border spinner-border-sm"></span> Загрузка...</td></tr>';
  }

  try {
    const url = new URL('/apps/telemetry_research/records', window.location.origin);
    if (sourcePath) url.searchParams.set('source_path', sourcePath);
    if (trSearchQuery) url.searchParams.set('query', trSearchQuery);
    url.searchParams.set('page', trCurrentPage);
    url.searchParams.set('page_sizei18n.t('auto__trpagesize_const_res_await_fetch_url_tostring_if_res_ok_throw_new_error_http_res_status_const_data_await_res_json_trtotalpages_data_total_pages_1_if_infoel_infoel_textcontent_data_page_trtotalpages_data_total_if_data_items_data_items_length_0_tbody_innerhtml__13c4d7')<tr><td colspan="7" class="text-center text-muted py-3">Записей не найдено</td></tr>';
      return;
    }

    tbody.innerHTML = data.items
      .map((r, i) => {
        const num = (trCurrentPage - 1) * trPageSize + i + 1;
        const ts = r.timestamp || r.time || '--';
        const cpu = r.cpu ? `${r.cpu.total_percent || r.cpu.load_percent || '--'}%` : '--';
        const ram = r.memory ? `${r.memory.percent || '--'}%` : '--';
        const gpu = r.gpu ? `${r.gpu.load_percent || '--'}%` : '--';
        let disk = '--';
        if (r.disk_io) {
          const rMb = ((r.disk_io.read_bytes_per_sec || 0) / 1048576).toFixed(1);
          const wMb = ((r.disk_io.write_bytes_per_sec || 0) / 1048576).toFixed(1);
          disk = `${rMb} / ${wMb} MB/s`;
        }
        const eventInfo = r.event_type || r.friendly_name || JSON.stringify(r).slice(0, 50);

        return `
          <tr>
            <td>${num}</td>
            <td class="text-muted">${ts}</td>
            <td>${cpu}</td>
            <td>${ram}</td>
            <td>${gpu}</td>
            <td>${disk}</td>
            <td class="text-truncate" style="max-width: 250px;" title="${eventInfo}">${eventInfo}</td>
          </tr>
        `;
      })
      .join('');
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-3">Ошибка: ${err.message}</td></tr>`;
    }
  }
}

/**
 * Открытие автономного HTML дашборда.
 */
function openHtmlDashboard() {
  const selectSource = document.getElementById('tr-select-source');
  const sourcePath = selectSource ? selectSource.value : '';
  const url = sourcePath
    ? `/apps/telemetry_research/dashboard?source_path=${encodeURIComponent(sourcePath)}`
    : '/apps/telemetry_research/dashboard';
  window.open(url, '_blanki18n.t('auto__json_function_downloadjsonreport_if_trcurrentreport_if_window_toast_window_toast_warning__660dbe')Нет данных', i18n.t('auto___2c6bf6'));
    return;
  }
  const blob = new Blob([JSON.stringify(trCurrentReport, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('ai18n.t('auto__a_href_url_a_download_telemetry_research_date_now_json_a_click_url_revokeobjecturl_url_if_document_readystate__f0e9a1')loading') {
  document.addEventListener('DOMContentLoaded', initTelemetryResearchTab);
} else {
  initTelemetryResearchTab();
}
