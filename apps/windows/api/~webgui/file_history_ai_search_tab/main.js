/**
 * =============================================================================
 * Process Name: Windows File History Ai Search Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/file_history_ai_search_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/file_history_ai_search_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * file_history_ai_search_tab/main.js — Логика веб-интерфейса поиска по истории файлов Windows через RAG
 */

(function () {
  'use stricti18n.t('auto__let_currentitems_function_initfilehistorytab_const_btnsearch_document_getelementbyid__e6ed42')btn-fh-search');
    const searchInput = document.getElementById('fh-search-input');
    const btnRefreshStatus = document.getElementById('btn-fh-refresh-status');
    const btnReindex = document.getElementById('btn-fh-reindex');
    const btnScanNow = document.getElementById('btn-fh-scan-now');
    const btnStartSched = document.getElementById('btn-fh-start-scheduler');
    const btnStopSched = document.getElementById('btn-fh-stop-scheduler');

    if (btnSearch) {
      btnSearch.addEventListener('click', executeSearch);
    }

    if (searchInput) {
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          executeSearch();
        }
      });
    }

    if (btnRefreshStatus) {
      btnRefreshStatus.addEventListener('click', loadStatus);
    }

    if (btnReindex) {
      btnReindex.addEventListener('click', triggerReindex);
    }

    if (btnScanNow) {
      btnScanNow.addEventListener('click', triggerScan);
    }

    if (btnStartSched) {
      btnStartSched.addEventListener('click', () => toggleScheduler('start'));
    }

    if (btnStopSched) {
      btnStopSched.addEventListener('click', () => toggleScheduler('stopi18n.t('auto__loadstatus_rag_async_function_loadstatus_try_const_resp_await_fetch__d52650')/api/windows/file-history/status');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const elCount = document.getElementById('fh-stat-docs-count');
      const elLastIdx = document.getElementById('fh-stat-last-index');
      const elSchedStat = document.getElementById('fh-stat-scheduler-status');
      const elSchedIcon = document.getElementById('fh-scheduler-icon');
      const elSchedInt = document.getElementById('fh-stat-scheduler-interval');
      const elFaissFile = document.getElementById('fh-stat-faiss-filei18n.t('auto__if_elcount_elcount_textcontent_data_total_indexed_documents_0_if_ellastidx_ellastidx_textcontent_data_last_indexed_at_new_date_data_last_indexed_at_tolocalestring__c32c12')ru-RU')}`
          : i18n.t('auto___16deed');
      }

      if (elSchedStat) {
        if (data.scheduler_running) {
          elSchedStat.textContent = i18n.t('auto___667904');
          elSchedStat.className = 'fh-stat-val text-success';
          if (elSchedIcon) elSchedIcon.className = 'bi bi-arrow-repeat fs-4 text-success opacity-75 spin';
        } else {
          elSchedStat.textContent = i18n.t('auto___aa0d25');
          elSchedStat.className = 'fh-stat-val text-warning';
          if (elSchedIcon) elSchedIcon.className = 'bi bi-arrow-repeat fs-4 text-warning opacity-50i18n.t('auto__if_elschedint_elschedint_textcontent_data_update_interval_minutes_15_if_elfaissfile_data_index_file_path_const_parts_data_index_file_path_split_elfaissfile_textcontent_parts_parts_length_1_data_index_file_path_elfaissfile_title_data_index_file_path_catch_err_console_error__3cb452')[FileHistoryUI] Ошибка загрузки статуса:i18n.t('auto__err_windows_async_function_triggerscan_const_tbody_document_getelementbyid__5b14c9')fh-items-tbody');
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-4">
            <div class="spinner-border spinner-border-sm text-info me-2" role="status"></div>
            <span>Сканирование источников истории файлов Windows...</span>
          </td>
        </tr>`;
    }

    try {
      const resp = await fetch('/api/windows/file-history/scani18n.t('auto__if_resp_ok_throw_new_error_http_resp_status_currentitems_await_resp_json_renderitemstable_currentitems_if_window_showtoast_window_showtoast_currentitems_length__a2f871')info');
      }
    } catch (err) {
      console.error(i18n.t('auto__filehistoryui__c71a7b'), err);
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" class="text-center py-4 text-danger">
              <i class="bi bi-exclamation-triangle me-1"></i> Ошибка при сканировании: ${err.message}
            </td>
          </tr>`;
      }
    }
  }

  /**
   * Отрисовка таблицы сохраненных элементов телеметрии
   */
  function renderItemsTable(items) {
    const tbody = document.getElementById('fh-items-tbody');
    if (!tbody) return;

    if (!items || items.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-4 text-muted">
            Элементы истории файлов не обнаружены.
          </td>
        </tr>`;
      return;
    }

    let html = '';
    items.slice(0, 100).forEach((item, idx) => {
      const badgeSource = getSourceBadge(item.source_type);
      const formattedSize = formatBytes(item.file_size);
      const timeStr = item.timestamp ? new Date(item.timestamp).toLocaleString('ru-RU') : '—';

      html += `
        <tr>
          <td class="text-muted small">${idx + 1}</td>
          <td>
            <div class="fw-semibold text-truncate" style="max-width: 280px;" title="${escapeHtml(item.file_name)}">
              <i class="bi bi-file-earmark-text me-1 text-primary"></i>${escapeHtml(item.file_name)}
            </div>
            <div class="small text-muted text-truncate" style="max-width: 320px;" title="${escapeHtml(item.file_path)}">
              ${escapeHtml(item.file_path)}
            </div>
          </td>
          <td>${badgeSource}</td>
          <td><span class="badge bg-secondary bg-opacity-50 text-light">${escapeHtml(item.event_type)}</span></td>
          <td class="small text-muted">${timeStr}</td>
          <td class="small font-monospace">${formattedSize}</td>
          <td class="text-end">
            <button class="btn btn-sm btn-outline-secondary py-0 px-2 btn-copy-path" data-path="${escapeHtml(item.file_path)}" title=i18n.t('auto___8a5b6a')>
              <i class="bi bi-clipboard"></i>
            </button>
          </td>
        </tr>`;
    });

    tbody.innerHTML = html;

    // Привязка копирования пути
    tbody.querySelectorAll('.btn-copy-path').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const path = e.currentTarget.getAttribute('data-path');
        if (path) {
          navigator.clipboard.writeText(path);
          if (window.showToast) window.showToast(i18n.t('auto___f6358a'), 'successi18n.t('auto__rag_async_function_triggerreindex_const_btnreindex_document_getelementbyid__29bc61')btn-fh-reindex');
    if (btnReindex) btnReindex.disabled = true;

    if (window.showToast) {
      window.showToast(i18n.t('auto__rag__9ef43b'), 'info');
    }

    try {
      const resp = await fetch('/api/windows/file-history/index', { method: 'POSTi18n.t('auto__if_resp_ok_throw_new_error_http_resp_status_const_data_await_resp_json_if_window_showtoast_window_showtoast_rag_data_indexed_count__d44568')success');
      }
      loadStatus();
    } catch (err) {
      console.error(i18n.t('auto__filehistoryui_rag__ffcf9a'), err);
      if (window.showToast) {
        window.showToast(`Ошибка индексации RAG: ${err.message}`, 'errori18n.t('auto__finally_if_btnreindex_btnreindex_disabled_false_async_function_executesearch_const_searchinput_document_getelementbyid__f45f1d')fh-search-input');
    const filterSource = document.getElementById('fh-filter-source');
    const filterTopk = document.getElementById('fh-filter-topk');
    const spinner = document.getElementById('fh-search-spinner');
    const container = document.getElementById('fh-search-results-container');

    const query = searchInput ? searchInput.value.trim() : '';
    if (!query) {
      if (window.showToast) window.showToast(i18n.t('auto___f4f030'), 'warning');
      return;
    }

    const topK = filterTopk ? parseInt(filterTopk.value, 10) : 5;
    const sourceType = filterSource && filterSource.value ? filterSource.value : null;

    if (spinner) spinner.classList.remove('d-none');
    if (container) container.innerHTML = '';

    try {
      const resp = await fetch('/api/windows/file-history/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          top_k: topK,
          source_type: sourceType,
        }),
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      renderSearchResults(data);
    } catch (err) {
      console.error(i18n.t('auto__filehistoryui__1be39c'), err);
      if (container) {
        container.innerHTML = `
          <div class="alert alert-danger mb-0">
            <i class="bi bi-exclamation-octagon me-1"></i> Ошибка семантического поиска: ${err.message}
          </div>`;
      }
    } finally {
      if (spinner) spinner.classList.add('d-nonei18n.t('auto__function_rendersearchresults_data_const_container_document_getelementbyid__482c76')fh-search-results-container');
    if (!container) return;

    if (!data.results || data.results.length === 0) {
      container.innerHTML = `
        <div class="text-center text-muted py-4 border rounded-3">
          <i class="bi bi-emoji-frown fs-3 d-block mb-1 text-warning opacity-50i18n.t('auto__i_span_strong_escapehtml_data_query_strong_span_br_small_class__5ef260')text-secondaryi18n.t('auto__rag_small_div_return_let_html_div_class__1b153c')d-flex justify-content-between align-items-center mb-2 px-1">
        <span class="small text-muted">
          Найдено результатов: <strong>${data.total_found}</strong> (Время выполнения: <strong>${data.execution_time_ms} мс</strong>)
        </span>
      </div>`;

    data.results.forEach((item, idx) => {
      const badgeSource = getSourceBadge(item.source_type);
      const scorePct = Math.round(item.score * 100);
      const badgeScoreClass = item.score > 0.6 ? 'bg-success' : item.score > 0.3 ? 'bg-info' : 'bg-secondary';
      const timeStr = item.timestamp ? new Date(item.timestamp).toLocaleString('ru-RU') : '—';

      html += `
        <div class="fh-result-card">
          <div class="d-flex justify-content-between align-items-start gap-2 mb-1">
            <div class="d-flex align-items-center gap-2">
              <span class="badge rounded-circle bg-body-tertiary text-muted p-2 fw-bold me-1" style="width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center;">
                ${idx + 1}
              </span>
              <h6 class="mb-0 fw-bold text-truncate" style="max-width: 450px;" title="${escapeHtml(item.file_name)}">
                <i class="bi bi-file-earmark-code me-1 text-primary"></i>${escapeHtml(item.file_name)}
              </h6>
              ${badgeSource}
            </div>
            <div class="d-flex align-items-center gap-2">
              <span class="badge ${badgeScoreClass} fh-score-badge" title=i18n.t('auto___4c2381')>
                Score: ${item.score}
              </span>
              <button class="btn btn-sm btn-outline-secondary py-0 px-2 btn-copy-path" data-path="${escapeHtml(item.file_path)}" title=i18n.t('auto___bbf33e')>
                <i class="bi bi-clipboard"></i>
              </button>
            </div>
          </div>

          <div class="small text-muted text-truncate mb-2 font-monospace">
            <i class="bi bi-folder2-open me-1 text-secondary"></i>${escapeHtml(item.file_path)}
            <span class="ms-2 text-secondaryi18n.t('auto__timestr_span_div_div_class__41bff1')fh-snippet-box">
            ${escapeHtml(item.snippet)}
          </div>
        </div>`;
    });

    container.innerHTML = html;

    // Привязка копирования в результатах поиска
    container.querySelectorAll('.btn-copy-path').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const path = e.currentTarget.getAttribute('data-path');
        if (path) {
          navigator.clipboard.writeText(path);
          if (window.showToast) window.showToast(i18n.t('auto___f6358a'), 'successi18n.t('auto__async_function_togglescheduler_action_const_url_api_windows_file_history_scheduler_action_try_const_resp_await_fetch_url_method__3e7cc6')POST' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      if (window.showToast) {
        window.showToast(
          action === 'start' ? i18n.t('auto__rag__8d29a5') : i18n.t('auto___426630'),
          action === 'start' ? 'success' : 'info'
        );
      }
      loadStatus();
    } catch (err) {
      console.error(i18n.t('auto__filehistoryui__5680c6'), err);
      if (window.showToast) window.showToast(`Ошибка: ${err.message}`, 'errori18n.t('auto__function_getsourcebadge_sourcetype_switch_sourcetype_case_f06986')file_history_xml':
        return '<span class="badge bg-primary bg-opacity-75"><i class="bi bi-file-earmark-xml me-1"></i>File History XML</span>';
      case 'recent_lnk':
        return '<span class="badge bg-info bg-opacity-75"><i class="bi bi-link-45deg me-1"></i>Recent LNK</span>';
      case 'activity_db':
        return '<span class="badge bg-warning text-dark bg-opacity-75"><i class="bi bi-database me-1"></i>Activity DB</span>';
      case 'fs_scan':
        return '<span class="badge bg-success bg-opacity-75"><i class="bi bi-hdd-network me-1"></i>FS Scan</span>';
      default:
        return `<span class="badge bg-secondary">${escapeHtml(sourceType || 'unknowni18n.t('auto__span_function_formatbytes_bytes_decimals_1_if_bytes_bytes_0_return_98f56d')0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' i18n.t('auto__sizes_i_html_function_escapehtml_str_if_str_return_ddd7ae')';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;i18n.t('auto__dom_if_document_readystate__83155a')loading') {
    document.addEventListener('DOMContentLoaded', initFileHistoryTab);
  } else {
    initFileHistoryTab();
  }
})();
