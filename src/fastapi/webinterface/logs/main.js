// =============================================================================
// Webinterface: Logs Tab Logic & AI Log Analysis
// Module: webinterface/logs/main.js
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

'use strict';

(function () {
  const state = {
    files: [],
    selectedFile: '',
    rawContent: '',
    lines: [],
    filterLevel: 'ALL',
    searchQuery: '',
    tail: 250,
    autoRefreshInterval: null,
    isInitialized: false,
    reports: []
  };

  /**
   * Initializes the Logs inspection tab.
   */
  async function initLogsTab() {
    console.log('[LogsTab] Initializing logs viewer...');
    await loadLogStats();
    await loadLogFilesList();
    setupAutoRefresh();
    state.isInitialized = true;
  }

  /**
   * Loads general statistics about system logs.
   */
  async function loadLogStats() {
    try {
      const stats = await window.api.fetch('/api/logs/stats');
      const filesCountEl = document.getElementById('log-stat-files-count');
      const totalSizeEl = document.getElementById('log-stat-total-size');
      const sizeMbEl = document.getElementById('log-stat-size-mb');
      const reportsCountEl = document.getElementById('log-stat-reports-count');

      if (filesCountEl) filesCountEl.textContent = stats.file_count ?? 0;
      if (totalSizeEl) totalSizeEl.textContent = `${stats.total_size_kb ?? 0} KB`;
      if (sizeMbEl) sizeMbEl.textContent = `${stats.total_size_mb ?? 0} MB на диске`;
      if (reportsCountEl) reportsCountEl.textContent = stats.report_count ?? 0;
    } catch (e) {
      console.warn('[LogsTab] Failed to load log stats:', e);
    }
  }

  /**
   * Fetches available log files from server.
   */
  async function loadLogFilesList() {
    const selector = document.getElementById('log-file-selector');
    if (!selector) return;

    try {
      const data = await window.api.fetch('/api/logs/files');
      state.files = Array.isArray(data.files) ? data.files : [];
      state.files.sort((a, b) => new Date(b.modified || 0) - new Date(a.modified || 0));

      if (state.files.length === 0) {
        selector.innerHTML = '<option value="">(Лог-файлы не найдены)</option>';
        renderLogTerminal('Лог-файлы не найдены на сервере.');
        return;
      }

      selector.innerHTML = state.files.map(f => {
        return `<option value="${f.name}">${f.name} (${f.size_kb} KB)</option>`;
      }).join('');

      // Auto-select preferred log file (fastapi.log or info.log or first)
      if (!state.selectedFile || !state.files.some(f => f.name === state.selectedFile)) {
        const preferred = state.files.find(f => f.name === 'fastapi.log') ||
                          state.files.find(f => f.name === 'info.log') ||
                          state.files.find(f => f.name.startsWith('uvicorn_')) ||
                          state.files[0];
        state.selectedFile = preferred ? preferred.name : state.files[0].name;
      }

      selector.value = state.selectedFile;
      await readCurrentLogFile();
    } catch (err) {
      console.error('[LogsTab] Error loading files list:', err);
      selector.innerHTML = `<option value="">Ошибка: ${err.message}</option>`;
    }
  }

  /**
   * Reads contents of the currently selected log file.
   */
  async function readCurrentLogFile() {
    if (!state.selectedFile) return;

    const tailSelect = document.getElementById('log-tail-selector');
    state.tail = tailSelect ? parseInt(tailSelect.value, 10) : 250;

    try {
      const url = `/api/logs/read?filename=${encodeURIComponent(state.selectedFile)}&tail=${state.tail}`;
      const res = await window.api.fetch(url);

      state.rawContent = res.content || '';
      // Reverse lines so newest entries are displayed first (descending order by date)
      state.lines = state.rawContent
        .split(/\r?\n/)
        .filter(line => line.trim().length > 0)
        .reverse();

      // Update terminal metadata
      const filenameEl = document.getElementById('log-terminal-filename');
      const currentFilenameStat = document.getElementById('log-stat-current-filename');
      const currentLinesStat = document.getElementById('log-stat-current-lines');
      const timestampEl = document.getElementById('log-terminal-timestamp');

      if (filenameEl) filenameEl.textContent = res.filename || state.selectedFile;
      if (currentFilenameStat) currentFilenameStat.textContent = res.filename || state.selectedFile;
      if (currentLinesStat) currentLinesStat.textContent = `${res.returned_lines || 0} / ${res.total_lines || 0}`;
      if (timestampEl) timestampEl.textContent = new Date().toLocaleTimeString();

      applyLogFiltersAndRender();
    } catch (err) {
      console.error('[LogsTab] Error reading log:', err);
      renderLogTerminal(`Ошибка чтения лога: ${err.message}`);
    }
  }

  /**
   * Formats and highlights raw log lines.
   */
  function applyLogFiltersAndRender() {
    const query = (state.searchQuery || '').toLowerCase().trim();
    const level = state.filterLevel;

    const filtered = state.lines.filter(line => {
      if (!line) return false;
      if (query && !line.toLowerCase().includes(query)) return false;

      if (level !== 'ALL') {
        const upper = line.toUpperCase();
        if (level === 'ERROR' && !upper.includes('ERROR') && !upper.includes('CRITICAL') && !upper.includes('EXCEPTION')) {
          return false;
        }
        if (level === 'WARNING' && !upper.includes('WARN') && !upper.includes('WARNING')) {
          return false;
        }
        if (level === 'INFO' && !upper.includes('INFO')) {
          return false;
        }
        if (level === 'DEBUG' && !upper.includes('DEBUG')) {
          return false;
        }
      }
      return true;
    });

    const badge = document.getElementById('log-visible-lines-badge');
    if (badge) badge.textContent = `${filtered.length} отображается`;

    if (filtered.length === 0) {
      renderLogTerminal('(Нет записей, удовлетворяющих условиям фильтра)');
      return;
    }

    // Colorize lines
    const html = filtered.map(line => {
      const escaped = escapeHtml(line);
      const upper = line.toUpperCase();
      if (upper.includes('ERROR') || upper.includes('CRITICAL') || upper.includes('EXCEPTION')) {
        return `<span class="text-danger fw-semibold">${escaped}</span>`;
      }
      if (upper.includes('WARN') || upper.includes('WARNING')) {
        return `<span class="text-warning">${escaped}</span>`;
      }
      if (upper.includes('INFO')) {
        return `<span class="text-info-emphasis" style="color: #67e8f9 !important;">${escaped}</span>`;
      }
      if (upper.includes('DEBUG')) {
        return `<span class="text-success">${escaped}</span>`;
      }
      return `<span class="text-light">${escaped}</span>`;
    }).join('\n');

    const container = document.getElementById('log-output-container');
    if (container) {
      container.innerHTML = html;
    }
  }

  function renderLogTerminal(msg) {
    const container = document.getElementById('log-output-container');
    if (container) container.textContent = msg;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function setupAutoRefresh() {
    if (state.autoRefreshInterval) {
      clearInterval(state.autoRefreshInterval);
      state.autoRefreshInterval = null;
    }

    state.autoRefreshInterval = setInterval(() => {
      const toggle = document.getElementById('logs-auto-refresh');
      if (toggle && toggle.checked) {
        const tabPane = document.getElementById('tab-logs');
        if (tabPane && tabPane.classList.contains('active')) {
          readCurrentLogFile();
          loadLogStats();
        }
      }
    }, 3000);
  }

  // --- Actions ---

  window.onLogFileSelected = function(filename) {
    state.selectedFile = filename;
    readCurrentLogFile();
  };

  window.refreshCurrentLog = async function() {
    await loadLogStats();
    await readCurrentLogFile();
  };

  window.clearCurrentLog = async function() {
    if (!state.selectedFile) return;
    if (!confirm(`Вы действительно хотите очистить файл "${state.selectedFile}"?`)) {
      return;
    }

    try {
      await window.api.fetch(`/api/logs/clear?filename=${encodeURIComponent(state.selectedFile)}`, {
        method: 'DELETE'
      });
      await readCurrentLogFile();
      await loadLogStats();
      if (typeof window.showNotification === 'function') {
        window.showNotification(`Лог ${state.selectedFile} очищен`, 'success');
      }
    } catch (err) {
      alert(`Ошибка очистки лога: ${err.message}`);
    }
  };

  window.triggerLogAnalysis = async function() {
    if (!state.selectedFile) return;
    try {
      const res = await window.api.fetch('/api/logs/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: state.selectedFile })
      });
      alert(res.message || 'Анализ запущен в фоне. Результаты появятся во вкладке отчётов.');
      await loadLogStats();
    } catch (err) {
      alert(`Ошибка вызова AI-анализа: ${err.message}`);
    }
  };

  window.setLogLevelFilter = function(level) {
    state.filterLevel = level;
    document.querySelectorAll('#log-level-filters button').forEach(b => {
      b.classList.toggle('active', b.getAttribute('data-level') === level);
    });
    applyLogFiltersAndRender();
  };

  window.filterLogsInViewer = function() {
    const input = document.getElementById('log-search-input');
    state.searchQuery = input ? input.value : '';
    applyLogFiltersAndRender();
  };

  window.clearLogSearch = function() {
    const input = document.getElementById('log-search-input');
    if (input) input.value = '';
    state.searchQuery = '';
    applyLogFiltersAndRender();
  };

  window.copyLogContent = function() {
    if (!state.rawContent) return;
    navigator.clipboard.writeText(state.rawContent).then(() => {
      alert('Содержимое скопировано в буфер обмена');
    }).catch(e => {
      alert('Ошибка копирования: ' + e);
    });
  };

  window.downloadLogFile = function() {
    if (!state.rawContent || !state.selectedFile) return;
    const blob = new Blob([state.rawContent], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = state.selectedFile;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  window.scrollLogToBottom = function() {
    const container = document.getElementById('log-output-container');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  };

  window.toggleReportsModal = async function() {
    const modalEl = document.getElementById('logReportsModal');
    if (!modalEl) return;
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
    await loadAiReports();
  };

  async function loadAiReports() {
    const listGroup = document.getElementById('reports-list-group');
    if (!listGroup) return;

    try {
      const data = await window.api.fetch('/api/logs/reports');
      const reports = data.reports || [];
      if (reports.length === 0) {
        listGroup.innerHTML = '<div class="text-muted small p-2">Отчёты пока не сгенерированы. Запустите AI-анализ.</div>';
        return;
      }

      listGroup.innerHTML = reports.map((r, i) => {
        return `
          <button type="button" class="list-group-item list-group-item-action bg-dark text-white border-secondary small ${i === 0 ? 'active' : ''}" onclick="viewReportContent('${r.name}', '${r.modified}')">
            <div class="fw-semibold text-truncate">${r.name}</div>
            <div class="text-muted" style="font-size: 0.75rem;">${r.modified} (${r.size_kb} KB)</div>
          </button>
        `;
      }).join('');

      if (reports[0]) {
        await viewReportContent(reports[0].name, reports[0].modified);
      }
    } catch (e) {
      listGroup.innerHTML = `<div class="text-danger small p-2">Ошибка: ${e.message}</div>`;
    }
  }

  window.viewReportContent = async function(filename, date) {
    const titleEl = document.getElementById('report-view-title');
    const dateEl = document.getElementById('report-view-date');
    const contentEl = document.getElementById('report-view-content');

    if (titleEl) titleEl.textContent = filename;
    if (dateEl) dateEl.textContent = date;
    if (contentEl) contentEl.textContent = 'Загрузка отчёта...';

    try {
      const res = await window.api.fetch(`/api/logs/report?filename=${encodeURIComponent(filename)}`);
      if (contentEl) {
        contentEl.textContent = res.content || '(Пустой отчёт)';
      }
    } catch (e) {
      if (contentEl) contentEl.textContent = `Ошибка загрузки отчёта: ${e.message}`;
    }
  };

  // Global export
  window.initLogsTab = initLogsTab;
})();
