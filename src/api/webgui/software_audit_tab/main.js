/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/software_audit_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/software_audit_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

// Software Audit Tab JavaScript Module
(function() {
  let allApps = [];
  let auditReport = null;
  let isInitialized = false;

  function formatRelativeTime(dateStr) {
    if (!dateStr) return '<span class="text-muted">Нет данных</span>';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '<span class="text-muted">-</span>';
    const now = new Date();
    const diffMs = now - d;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHrs = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHrs / 24);

    if (diffDays > 90) {
      return `<span class="text-warning" title="${d.toLocaleString()}i18n.t('auto__diffdays_span_else_if_diffdays_0_return_span_class__428f7d')text-success" title="${d.toLocaleString()}i18n.t('auto__diffdays_span_else_if_diffhrs_0_return_span_class__2ea964')text-info" title="${d.toLocaleString()}i18n.t('auto__diffhrs_span_else_if_diffmin_0_return_span_class__a53f85')text-info" title="${d.toLocaleString()}i18n.t('auto__diffmin_span_else_return_span_class__81876f')text-info">Только что</span>`;
    }
  }

  function formatDuration(sec) {
    if (!sec || sec <= 0) return '<span class="text-muted">-</span>i18n.t('auto__const_hrs_math_floor_sec_3600_const_mins_math_floor_sec_3600_60_if_hrs_0_return_hrs_mins_if_mins_0_return_mins_return_sec_async_function_loadsoftwareaudit_const_tbody_document_getelementbyid__1d3e7d')sw-audit-tbody');
    const badge = document.getElementById('sw-audit-status-badge');
    if (badge) badge.innerText = i18n.t('auto___bdbb63');

    try {
      // 1. Пытаемся получить сводный аналитический отчет
      let reportRes = await fetch('/api/windows/software/audit');
      if (!reportRes.ok) {
        reportRes = await fetch('/api/v1/windows-admin/software/auditi18n.t('auto__if_reportres_ok_auditreport_await_reportres_json_2_let_appsres_await_fetch__588ef9')/api/windows/software?limit=500i18n.t('auto__if_appsres_ok_fallback_router_windows_admin_appsres_await_fetch__3d729e')/api/v1/windows-admin/software?limit=500i18n.t('auto__if_appsres_ok_allapps_await_appsres_json_else_throw_new_error_http_appsres_status_updatemetrics_populatecategories_rendertable_if_badge_badge_classname__c328de')badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2i18n.t('auto__badge_innertext_allapps_length_const_timeel_document_getelementbyid__484012')sw-last-scanned-timei18n.t('auto__if_timeel_timeel_innertext_new_date_tolocaletimestring_catch_err_console_error__75bb10')[SoftwareAuditTab] Failed to load software audit:', err);
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger p-4">Ошибка сбора сведений об установленном ПО: ${err.message}</td></tr>`;
      }
      if (badge) {
        badge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
        badge.innerText = i18n.t('auto___0e7d63');
      }
    }
  }

  function updateMetrics() {
    const totalEl = document.getElementById('sw-metric-total');
    const activeEl = document.getElementById('sw-metric-active');
    const dormantEl = document.getElementById('sw-metric-dormant');
    const catEl = document.getElementById('sw-metric-categories');

    if (auditReport) {
      if (totalEl) totalEl.innerText = auditReport.total_apps || allApps.length;
      if (activeEl) activeEl.innerText = auditReport.active_apps_count || 0;
      if (dormantEl) dormantEl.innerText = auditReport.never_launched_or_dormant_count || 0;
      if (catEl) catEl.innerText = Object.keys(auditReport.categories_breakdown || {}).length;
    } else {
      const activeCount = allApps.filter(a => a.execution_info && a.execution_info.last_run_time).length;
      if (totalEl) totalEl.innerText = allApps.length;
      if (activeEl) activeEl.innerText = activeCount;
      if (dormantEl) dormantEl.innerText = allApps.length - activeCount;
      const cats = new Set(allApps.map(a => a.category).filter(Boolean));
      if (catEl) catEl.innerText = cats.size;
    }
  }

  function populateCategories() {
    const sel = document.getElementById('sw-category-filter');
    if (!sel) return;

    const currentVal = sel.value;
    const cats = Array.from(new Set(allApps.map(a => a.category).filter(Boolean))).sort();

    sel.innerHTML = '<option value="">Все категории</option>' + cats.map(c =>
      `<option value="${c}" ${c === currentVal ? 'selected' : ''}>${c}</option>`
    ).join('');
  }

  function getFilteredApps() {
    const search = (document.getElementById('sw-search-input')?.value || '').toLowerCase().trim();
    const category = document.getElementById('sw-category-filter')?.value || '';
    const status = document.getElementById('sw-status-filter')?.value || 'alli18n.t('auto__const_dormantthresholdms_90_24_3600_1000_const_now_date_now_return_allapps_filter_app_if_search_const_text_app_display_name__e7c00f')'} ${app.name || ''} ${app.publisher || ''} ${app.purpose_description || 'i18n.t('auto__tolowercase_if_text_includes_search_return_false_if_category_app_category_category_return_false_const_lastrun_app_execution_info_last_run_time_new_date_app_execution_info_last_run_time_gettime_null_if_status__731ed9')active') {
        if (!lastRun || (now - lastRun > dormantThresholdMs)) return false;
      } else if (status === 'dormant') {
        if (lastRun && (now - lastRun <= dormantThresholdMs)) return false;
      }

      return true;
    });
  }

  function renderTable() {
    const tbody = document.getElementById('sw-audit-tbody');
    const badge = document.getElementById('sw-filtered-count-badge');
    if (!tbody) return;

    const filtered = getFilteredApps();
    if (badge) {
      badge.innerText = `${filtered.length} / ${allApps.length}`;
    }

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted p-4">Программы по заданным критериям не найдены</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((app, idx) => {
      const exec = app.execution_info;
      const lastRunFormatted = exec ? formatRelativeTime(exec.last_run_time) : '<span class="text-muted">Никогда</span>';
      const runCount = exec && exec.run_count ? `<span class="badge bg-secondary">${exec.run_count}</span>` : '<span class="text-muted">0</span>';
      const focusTime = exec ? formatDuration(exec.focus_time_seconds) : '<span class="text-muted">-</span>';
      const sizeStr = app.size_mb > 0 ? `${app.size_mb} MB` : '<span class="text-muted">-</span>';
      const archBadge = app.architecture === 'x64' ? '<span class="badge bg-primary-subtle text-primary" style="font-size: 0.65rem;">x64</span>' : '<span class="badge bg-secondary-subtle text-secondary" style="font-size: 0.65rem;">x86</span>';

      return `
        <tr class="sw-row-item" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto__ai__36b4b8')>
          <td>
            <div class="fw-bold text-white text-truncate" style="max-width: 260px;" title="${app.display_name || app.name}">
              ${app.display_name || app.name}
            </div>
            <div class="small text-muted text-truncate" style="max-width: 260px; font-size: 0.72rem;" title="${app.purpose_description || ''}">
              ${app.purpose_description || i18n.t('auto___aa3245')}
            </div>
          </td>
          <td>
            <span class="sw-badge-category">${app.category || i18n.t('auto___2ade33')}</span>
          </td>
          <td>
            <div class="text-truncate text-light" style="max-width: 180px;" title="${app.publisher || i18n.t('auto___1fada4')}">${app.publisher || '<span class="text-muted">-</span>'}</div>
            <div class="small text-muted" style="font-size: 0.72rem;">${app.version || '-'}</div>
          </td>
          <td>${lastRunFormatted}</td>
          <td>${runCount}</td>
          <td class="small text-light">${focusTime}</td>
          <td class="small">
            <div>${sizeStr}</div>
            <div>${archBadge}</div>
          </td>
          <td style="text-align: right;">
            <button class="btn btn-sm btn-outline-info p-1 px-2 btn-sw-detail" data-idx="${idx}" title=i18n.t('auto___ed2f45')>
              <i class="bi bi-info-circle"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('i18n.t('auto__tbody_queryselectorall__dedad1').sw-row-item').forEach(row => {
      row.onclick = (evt) => {
        const idx = parseInt(row.getAttribute('data-idxi18n.t('auto__10_showappdetails_filtered_idx_tbody_queryselectorall__1ab3f7').btn-sw-detail').forEach(btn => {
      btn.onclick = (evt) => {
        evt.stopPropagation();
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        showAppDetails(filtered[idx]);
      };
    });
  }

  function showAppDetails(app) {
    if (!app) return;
    const exec = app.execution_info;

    if (window.AITableModal) {
      window.AITableModal.show({
        icon: '📦',
        title: app.display_name || app.name,
        subtitle: app.publisher || i18n.t('auto___e76ec9'),
        tableType: 'software',
        badges: [
          { text: app.category || i18n.t('auto___e9178d'), class: 'badge bg-info' },
          { text: app.architecture || 'x64', class: 'badge bg-secondary' }
        ],
        metadata: [
          { label: i18n.t('auto___82a9ca'), value: app.display_name || app.name },
          { label: i18n.t('auto___cbd626'), value: app.publisher || i18n.t('auto___3b3c4f') },
          { label: i18n.t('auto___97c248'), value: app.version || i18n.t('auto___72cca1') },
          { label: i18n.t('auto___19c858'), value: app.category || i18n.t('auto___2ade33') },
          { label: i18n.t('auto___169c35'), value: app.size_mb > 0 ? `${app.size_mb} MB` : i18n.t('auto___3b3c4f') },
          { label: i18n.t('auto___e9ca0f'), value: app.install_date || i18n.t('auto___43b44f') },
          { label: i18n.t('auto__userassist__dc970f'), value: exec?.run_count ? `${exec.run_count} раз` : '0' },
          { label: i18n.t('auto___1327f1'), value: exec ? formatDuration(exec.focus_time_seconds) : '-' },
          { label: i18n.t('auto___5e8630'), value: exec?.last_run_time ? new Date(exec.last_run_time).toLocaleString() : i18n.t('auto___d0dd94'), fullWidth: true },
          { label: i18n.t('auto___a9216d'), value: app.install_location || i18n.t('auto___3b3c4f'), isCode: true, fullWidth: true }
        ],
        rawTitle: i18n.t('auto___f6a08b'),
        rawContent: app.uninstall_string || app.install_location || '',
        requestData: {
          install_location: app.install_location,
          uninstall_string: app.uninstall_string,
          version: app.version,
          size_mb: app.size_mb,
          run_count: exec?.run_count
        }
      });
      return;
    }
  }

  function exportJson() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(allApps, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `software_audit_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();
  }

  window.initSoftwareAuditTab = async function() {
    console.log('[SoftwareAuditTab] Initializing Software Audit tab...i18n.t('auto__const_searchinput_document_getelementbyid__005f83')sw-search-input');
    const catSelect = document.getElementById('sw-category-filter');
    const statusSelect = document.getElementById('sw-status-filter');
    const refreshBtn = document.getElementById('btn-sw-audit-refresh');
    const exportBtn = document.getElementById('btn-sw-audit-export');

    if (searchInput) searchInput.oninput = renderTable;
    if (catSelect) catSelect.onchange = renderTable;
    if (statusSelect) statusSelect.onchange = renderTable;
    if (refreshBtn) refreshBtn.onclick = loadSoftwareAudit;
    if (exportBtn) exportBtn.onclick = exportJson;

    await loadSoftwareAudit();
    isInitialized = true;
  };
})();
