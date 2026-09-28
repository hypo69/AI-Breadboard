/**
 * file_history_ai_search_tab/main.js — Логика веб-интерфейса поиска по истории файлов Windows через RAG
 */

(function () {
  'use strict';

  let currentItems = [];

  /**
   * Инициализация событий и обработчиков вкладки
   */
  function initFileHistoryTab() {
    const btnSearch = document.getElementById('btn-fh-search');
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
      btnStopSched.addEventListener('click', () => toggleScheduler('stop'));
    }

    // Первоначальная загрузка статуса
    loadStatus();
  }

  /**
   * Получение текущего статуса RAG индекса и планировщика
   */
  async function loadStatus() {
    try {
      const resp = await fetch('/api/windows/file-history/status');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const elCount = document.getElementById('fh-stat-docs-count');
      const elLastIdx = document.getElementById('fh-stat-last-index');
      const elSchedStat = document.getElementById('fh-stat-scheduler-status');
      const elSchedIcon = document.getElementById('fh-scheduler-icon');
      const elSchedInt = document.getElementById('fh-stat-scheduler-interval');
      const elFaissFile = document.getElementById('fh-stat-faiss-file');

      if (elCount) elCount.textContent = data.total_indexed_documents || 0;
      if (elLastIdx) {
        elLastIdx.textContent = data.last_indexed_at
          ? `Обновлено: ${new Date(data.last_indexed_at).toLocaleString('ru-RU')}`
          : 'Индексация не проводилась';
      }

      if (elSchedStat) {
        if (data.scheduler_running) {
          elSchedStat.textContent = 'Активен';
          elSchedStat.className = 'fh-stat-val text-success';
          if (elSchedIcon) elSchedIcon.className = 'bi bi-arrow-repeat fs-4 text-success opacity-75 spin';
        } else {
          elSchedStat.textContent = 'Остановлен';
          elSchedStat.className = 'fh-stat-val text-warning';
          if (elSchedIcon) elSchedIcon.className = 'bi bi-arrow-repeat fs-4 text-warning opacity-50';
        }
      }

      if (elSchedInt) {
        elSchedInt.textContent = `Интервал: ${data.update_interval_minutes || 15} мин`;
      }

      if (elFaissFile && data.index_file_path) {
        const parts = data.index_file_path.split(/[\\/]/);
        elFaissFile.textContent = parts[parts.length - 1] || data.index_file_path;
        elFaissFile.title = data.index_file_path;
      }
    } catch (err) {
      console.error('[FileHistoryUI] Ошибка загрузки статуса:', err);
    }
  }

  /**
   * Принудительный запуск сканирования истории файлов Windows
   */
  async function triggerScan() {
    const tbody = document.getElementById('fh-items-tbody');
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
      const resp = await fetch('/api/windows/file-history/scan');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      currentItems = await resp.json();
      renderItemsTable(currentItems);
      if (window.showToast) {
        window.showToast(`Сканирование завершено: найдено ${currentItems.length} элементов`, 'info');
      }
    } catch (err) {
      console.error('[FileHistoryUI] Ошибка сканирования:', err);
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
            <button class="btn btn-sm btn-outline-secondary py-0 px-2 btn-copy-path" data-path="${escapeHtml(item.file_path)}" title="Копировать путь">
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
          if (window.showToast) window.showToast('Путь скопирован в буфер обмена', 'success');
        }
      });
    });
  }

  /**
   * Пересчет и векторизация RAG-индекса
   */
  async function triggerReindex() {
    const btnReindex = document.getElementById('btn-fh-reindex');
    if (btnReindex) btnReindex.disabled = true;

    if (window.showToast) {
      window.showToast('Запущен процесс сканирования и векторной RAG-индексации...', 'info');
    }

    try {
      const resp = await fetch('/api/windows/file-history/index', { method: 'POST' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      if (window.showToast) {
        window.showToast(`RAG-индекс перестроен: проиндексировано ${data.indexed_count} элементов!`, 'success');
      }
      loadStatus();
    } catch (err) {
      console.error('[FileHistoryUI] Ошибка перестроения RAG:', err);
      if (window.showToast) {
        window.showToast(`Ошибка индексации RAG: ${err.message}`, 'error');
      }
    } finally {
      if (btnReindex) btnReindex.disabled = false;
    }
  }

  /**
   * Выполнение семантического поиска
   */
  async function executeSearch() {
    const searchInput = document.getElementById('fh-search-input');
    const filterSource = document.getElementById('fh-filter-source');
    const filterTopk = document.getElementById('fh-filter-topk');
    const spinner = document.getElementById('fh-search-spinner');
    const container = document.getElementById('fh-search-results-container');

    const query = searchInput ? searchInput.value.trim() : '';
    if (!query) {
      if (window.showToast) window.showToast('Введите поисковый запрос', 'warning');
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
      console.error('[FileHistoryUI] Ошибка поиска:', err);
      if (container) {
        container.innerHTML = `
          <div class="alert alert-danger mb-0">
            <i class="bi bi-exclamation-octagon me-1"></i> Ошибка семантического поиска: ${err.message}
          </div>`;
      }
    } finally {
      if (spinner) spinner.classList.add('d-none');
    }
  }

  /**
   * Отрисовка карточек результатов семантического поиска
   */
  function renderSearchResults(data) {
    const container = document.getElementById('fh-search-results-container');
    if (!container) return;

    if (!data.results || data.results.length === 0) {
      container.innerHTML = `
        <div class="text-center text-muted py-4 border rounded-3">
          <i class="bi bi-emoji-frown fs-3 d-block mb-1 text-warning opacity-50"></i>
          <span>Совпадений по запросу «<strong>${escapeHtml(data.query)}</strong>» не найдено.</span><br>
          <small class="text-secondary">Попробуйте изменить запрос или нажать «Перестроить RAG» для обновения индекса.</small>
        </div>`;
      return;
    }

    let html = `
      <div class="d-flex justify-content-between align-items-center mb-2 px-1">
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
              <span class="badge ${badgeScoreClass} fh-score-badge" title="Косинусное сходство / Релевантность">
                Score: ${item.score}
              </span>
              <button class="btn btn-sm btn-outline-secondary py-0 px-2 btn-copy-path" data-path="${escapeHtml(item.file_path)}" title="Скопировать путь">
                <i class="bi bi-clipboard"></i>
              </button>
            </div>
          </div>

          <div class="small text-muted text-truncate mb-2 font-monospace">
            <i class="bi bi-folder2-open me-1 text-secondary"></i>${escapeHtml(item.file_path)}
            <span class="ms-2 text-secondary">| Время: ${timeStr}</span>
          </div>

          <div class="fh-snippet-box">
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
          if (window.showToast) window.showToast('Путь скопирован в буфер обмена', 'success');
        }
      });
    });
  }

  /**
   * Управление фоновым планировщиком
   */
  async function toggleScheduler(action) {
    const url = `/api/windows/file-history/scheduler/${action}`;
    try {
      const resp = await fetch(url, { method: 'POST' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      if (window.showToast) {
        window.showToast(
          action === 'start' ? 'Фоновый планировщик RAG запущен' : 'Фоновый планировщик остановлен',
          action === 'start' ? 'success' : 'info'
        );
      }
      loadStatus();
    } catch (err) {
      console.error('[FileHistoryUI] Ошибка управления планировщиком:', err);
      if (window.showToast) window.showToast(`Ошибка: ${err.message}`, 'error');
    }
  }

  /**
   * Получение бейджа источника
   */
  function getSourceBadge(sourceType) {
    switch (sourceType) {
      case 'file_history_xml':
        return '<span class="badge bg-primary bg-opacity-75"><i class="bi bi-file-earmark-xml me-1"></i>File History XML</span>';
      case 'recent_lnk':
        return '<span class="badge bg-info bg-opacity-75"><i class="bi bi-link-45deg me-1"></i>Recent LNK</span>';
      case 'activity_db':
        return '<span class="badge bg-warning text-dark bg-opacity-75"><i class="bi bi-database me-1"></i>Activity DB</span>';
      case 'fs_scan':
        return '<span class="badge bg-success bg-opacity-75"><i class="bi bi-hdd-network me-1"></i>FS Scan</span>';
      default:
        return `<span class="badge bg-secondary">${escapeHtml(sourceType || 'unknown')}</span>`;
    }
  }

  /**
   * Форматирование байт
   */
  function formatBytes(bytes, decimals = 1) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  /**
   * Экранирование спецсимволов HTML
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

  // Запуск при загрузке DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFileHistoryTab);
  } else {
    initFileHistoryTab();
  }
})();
