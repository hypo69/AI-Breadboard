/**
 * =============================================================================
 * Process Name: Windows App Logs Tab - Main Controller Script
 * =============================================================================
 * Description:
 *   Клиентский контроллер вкладки анализа внутренних логов программы
 *   AI-Breadboard strictly из %APPDATA%\AI-Breadboard\logs.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script type="module" src="/html/app_logs_tab/main.js?v=20261008_v1"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/app_logs_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 10:25:00
 * =============================================================================
 */

let state = {
  currentFile: 'log.json',
  currentMode: 'table',
  liveActive: false,
  liveTimer: null,
  records: [],
  files: [],
  stats: null,
  selectedEntry: null,
};

/**
 * Инициализация вкладки
 */
export async function initAppLogsTab() {
  bindEvents();
  await loadFilesList();
  await refreshCurrentView();
}

/**
 * Привязка событий элементов управления
 */
function bindEvents() {
  // Переключение режимов отображения (таблица, аудит, график, tail, raw)
  document.querySelectorAll('#apl-mode-tabs .nav-link').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('#apl-mode-tabs .nav-link').forEach(b => {
        b.classList.remove('active');
        b.classList.add('text-light');
      });
      btn.classList.add('active');
      btn.classList.remove('text-light');

      state.currentMode = btn.dataset.mode;
      switchViewMode(state.currentMode);
    });
  });

  // Кнопка обновления
  const btnRefresh = document.getElementById('btn-apl-refresh');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', async () => {
      await refreshCurrentView();
      if (window.toast) window.toast.info('Обновлено', 'Данные логов успешно обновлены');
    });
  }

  // Кнопка AI диагностики
  const btnDiagnose = document.getElementById('btn-apl-diagnose');
  if (btnDiagnose) {
    btnDiagnose.addEventListener('click', async () => {
      // Переключаем вкладку в режим аудита и запускаем диагностику
      const auditBtn = document.querySelector('#apl-mode-tabs [data-mode="audit"]');
      if (auditBtn) auditBtn.click();
      await runAiDiagnostics();
    });
  }

  // Переключатель Live Stream
  const liveSwitch = document.getElementById('apl-live-switch');
  if (liveSwitch) {
    liveSwitch.addEventListener('change', (e) => {
      state.liveActive = e.target.checked;
      if (state.liveActive) {
        startLivePolling();
        if (window.toast) window.toast.success('Live Stream', 'Потоковое обновление активировано (3 сек)');
      } else {
        stopLivePolling();
        if (window.toast) window.toast.info('Live Stream', 'Потоковое обновление приостановлено');
      }
    });
  }

  // Фильтры с debounce
  let searchTimeout = null;
  const searchInput = document.getElementById('apl-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => refreshCurrentView(), 300);
    });
  }

  const levelSelect = document.getElementById('apl-level-select');
  if (levelSelect) {
    levelSelect.addEventListener('change', () => refreshCurrentView());
  }

  const compSelect = document.getElementById('apl-component-select');
  if (compSelect) {
    compSelect.addEventListener('change', () => refreshCurrentView());
  }

  const limitSelect = document.getElementById('apl-limit-select');
  if (limitSelect) {
    limitSelect.addEventListener('change', () => refreshCurrentView());
  }

  // Сброс фильтров
  const btnReset = document.getElementById('btn-apl-reset-filters');
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      if (levelSelect) levelSelect.value = '';
      if (compSelect) compSelect.value = '';
      if (limitSelect) limitSelect.value = '200';
      refreshCurrentView();
    });
  }

  // Скачивание файла
  const btnDownload = document.getElementById('btn-apl-download');
  if (btnDownload) {
    btnDownload.addEventListener('click', (e) => {
      e.preventDefault();
      window.open(`/api/v1/app_logs/download?file_name=${encodeURIComponent(state.currentFile)}`, '_blank');
    });
  }

  // Очистка лог-файла
  const btnClear = document.getElementById('btn-apl-clear');
  if (btnClear) {
    btnClear.addEventListener('click', async (e) => {
      e.preventDefault();
      if (!confirm(`Вы действительно хотите очистить файл ${state.currentFile}? Это действие необратимо.`)) {
        return;
      }
      try {
        const res = await fetch('/api/v1/app_logs/clear', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_name: state.currentFile })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          if (window.toast) window.toast.success('Очищено', data.message);
          await loadFilesList();
          await refreshCurrentView();
        } else {
          if (window.toast) window.toast.error('Ошибка', data.detail || 'Не удалось очистить файл');
        }
      } catch (err) {
        if (window.toast) window.toast.error('Ошибка', err.message);
      }
    });
  }

  // Кнопка очистки терминала
  const btnClearTerm = document.getElementById('btn-apl-clear-terminal');
  if (btnClearTerm) {
    btnClearTerm.addEventListener('click', () => {
      const term = document.getElementById('apl-tail-terminal');
      if (term) term.textContent = '';
    });
  }

  // Кнопка копирования в модальном окне
  const btnModalCopy = document.getElementById('btn-apl-modal-copy');
  if (btnModalCopy) {
    btnModalCopy.addEventListener('click', () => {
      if (!state.selectedEntry) return;
      const textToCopy = JSON.stringify(state.selectedEntry, null, 2);
      navigator.clipboard.writeText(textToCopy).then(() => {
        if (window.toast) window.toast.success('Скопировано', 'Лог-запись скопирована в буфер обмена');
      });
    });
  }
}

/**
 * Переключение видимого представления
 */
function switchViewMode(mode) {
  const views = {
    table: document.getElementById('apl-view-table'),
    audit: document.getElementById('apl-view-audit'),
    timeline: document.getElementById('apl-view-timeline'),
    tail: document.getElementById('apl-view-tail'),
    raw: document.getElementById('apl-view-raw'),
  };

  Object.entries(views).forEach(([m, el]) => {
    if (!el) return;
    if (m === mode) {
      el.classList.remove('d-none');
    } else {
      el.classList.add('d-none');
    }
  });

  if (mode === 'audit') {
    runAiDiagnostics();
  } else if (mode === 'tail') {
    loadTailTerminal();
  } else if (mode === 'raw') {
    loadRawContent();
  } else if (mode === 'timeline') {
    renderTimelineChart();
  }
}

/**
 * Загрузка списка файлов логов
 */
async function loadFilesList() {
  try {
    const res = await fetch('/api/v1/app_logs/files');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.files = data.files || [];

    const pathLabel = document.getElementById('apl-full-path-label');
    if (pathLabel && data.logs_dir) {
      pathLabel.textContent = data.logs_dir;
      pathLabel.title = data.logs_dir;
    }

    renderFilesBadges();
  } catch (err) {
    console.error('[AppLogs] Ошибка загрузки списка файлов:', err);
  }
}

/**
 * Отрисовка бейджей файлов
 */
function renderFilesBadges() {
  const container = document.getElementById('apl-files-badges-container');
  if (!container) return;

  container.innerHTML = '';
  if (state.files.length === 0) {
    container.innerHTML = '<span class="text-muted small">Файлы логов не обнаружены.</span>';
    return;
  }

  state.files.forEach(f => {
    const btn = document.createElement('button');
    btn.type = 'button';
    const isActive = f.name === state.currentFile;
    btn.className = `btn btn-sm rounded-pill px-2.5 py-0.5 small apl-file-badge ${isActive ? 'btn-primary active' : 'btn-outline-secondary text-light'}`;
    btn.style.fontSize = '0.76rem';

    const icon = f.is_json ? 'bi-filetype-json text-info' : 'bi-file-text text-warning';
    btn.innerHTML = `<i class="bi ${icon} me-1"></i><strong>${f.name}</strong> <span class="badge bg-dark ms-1">${f.size_formatted}</span>`;

    btn.addEventListener('click', async () => {
      state.currentFile = f.name;
      renderFilesBadges();
      await refreshCurrentView();
    });

    container.appendChild(btn);
  });
}

/**
 * Обновление текущего представления
 */
async function refreshCurrentView() {
  const search = document.getElementById('apl-search-input')?.value || '';
  const level = document.getElementById('apl-level-select')?.value || '';
  const component = document.getElementById('apl-component-select')?.value || '';
  const limit = document.getElementById('apl-limit-select')?.value || '200';

  // Обновляем заголовок файла
  const fnStat = document.getElementById('apl-stat-filename');
  if (fnStat) fnStat.textContent = state.currentFile;

  try {
    const queryParams = new URLSearchParams({
      file_name: state.currentFile,
      limit: limit,
      search: search,
      level: level,
      component: component,
    });

    const res = await fetch(`/api/v1/app_logs/records?${queryParams.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.records = data.records || [];
    state.stats = data.stats || null;

    // Обновляем метрики в шапке
    updateHeaderStats(data);
    // Обновляем селектор компонентов
    updateComponentsDropdown(data.stats?.components || []);

    // Рендерим активный вид
    if (state.currentMode === 'table') {
      renderRecordsTable(state.records);
    } else if (state.currentMode === 'timeline') {
      renderTimelineChart();
    } else if (state.currentMode === 'tail') {
      loadTailTerminal();
    } else if (state.currentMode === 'raw') {
      loadRawContent();
    }
  } catch (err) {
    console.error('[AppLogs] Ошибка обновления логов:', err);
    const tbody = document.getElementById('apl-table-body');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">Ошибка загрузки: ${err.message}</td></tr>`;
    }
  }
}

/**
 * Обновление счетчиков в шапке
 */
function updateHeaderStats(data) {
  const sizeEl = document.getElementById('apl-stat-size');
  if (sizeEl && data.file_info) {
    sizeEl.textContent = data.file_info.size_formatted || '0 KB';
  }

  const loadedEl = document.getElementById('apl-stat-loaded');
  if (loadedEl) {
    loadedEl.textContent = `${data.records.length} / ${data.total_matches}`;
  }

  const errEl = document.getElementById('apl-stat-errors');
  if (errEl && data.stats) {
    errEl.textContent = data.stats.errors_count || 0;
  }

  const warnEl = document.getElementById('apl-stat-warnings');
  if (warnEl && data.stats) {
    warnEl.textContent = data.stats.warnings_count || 0;
  }
}

/**
 * Обновление выпадающего списка компонентов
 */
function updateComponentsDropdown(components) {
  const select = document.getElementById('apl-component-select');
  if (!select) return;

  const currentVal = select.value;
  select.innerHTML = '<option value="">Все модули/компоненты</option>';

  components.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name;
    opt.textContent = `${c.name} (${c.count})`;
    if (c.name === currentVal) opt.selected = true;
    select.appendChild(opt);
  });
}

/**
 * Отрисовка таблицы записей
 */
function renderRecordsTable(records) {
  const tbody = document.getElementById('apl-table-body');
  if (!tbody) return;

  if (!records || records.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Нет записей, удовлетворяющих условиям фильтра.</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  records.forEach(entry => {
    const tr = document.createElement('tr');

    let badgeClass = 'badge-apl-inf';
    const lvl = (entry.level || '').toUpperCase();
    if (lvl === 'CRITICAL' || lvl === 'FATAL') badgeClass = 'badge-apl-crit';
    else if (lvl === 'ERROR') badgeClass = 'badge-apl-err';
    else if (lvl === 'WARNING' || lvl === 'WARN') badgeClass = 'badge-apl-warn';
    else if (lvl === 'DEBUG') badgeClass = 'badge-apl-deb';

    const repeatBadge = entry.repeat_count > 1 ? `<span class="badge bg-dark border border-secondary text-warning ms-1" title="Повторений">${entry.repeat_count}x</span>` : '';
    const hasExc = !!entry.exc_info;
    const excBadge = hasExc ? `<span class="badge bg-danger ms-1" title="Содержит Stacktrace"><i class="bi bi-bug"></i> Trace</span>` : '';

    tr.innerHTML = `
      <td class="font-monospace small text-muted text-nowrap">${escapeHtml(entry.timestamp || '--:--:--')}</td>
      <td><span class="badge ${badgeClass} small">${escapeHtml(entry.level || 'INFO')}</span>${repeatBadge}</td>
      <td><span class="badge bg-dark border border-secondary text-info font-monospace text-truncate" style="max-width: 120px;" title="${escapeHtml(entry.component)}">${escapeHtml(entry.component)}</span></td>
      <td class="font-monospace small text-break">${escapeHtml(entry.message || '')}${excBadge}</td>
      <td class="text-end">
        <button class="btn btn-xs btn-outline-info rounded px-1.5 py-0.5 btn-entry-view" title="Посмотреть детали">
          <i class="bi bi-eye"></i>
        </button>
      </td>
    `;

    // Клик по строке открывает детали
    tr.addEventListener('click', (e) => {
      state.selectedEntry = entry;
      openEntryModal(entry);
    });

    tbody.appendChild(tr);
  });
}

/**
 * Открытие модального окна деталей записи
 */
function openEntryModal(entry) {
  document.getElementById('apl-modal-time').textContent = entry.timestamp || 'N/A';
  document.getElementById('apl-modal-level').textContent = entry.level || 'INFO';
  document.getElementById('apl-modal-component').textContent = entry.component || 'N/A';
  document.getElementById('apl-modal-repeat').textContent = entry.repeat_count || 1;
  document.getElementById('apl-modal-message').textContent = entry.message || '';
  document.getElementById('apl-modal-raw').textContent = entry.raw || JSON.stringify(entry);

  const excCard = document.getElementById('apl-modal-exc-card');
  const excPre = document.getElementById('apl-modal-exc');
  if (entry.exc_info) {
    excCard.classList.remove('d-none');
    excPre.textContent = typeof entry.exc_info === 'string' ? entry.exc_info : JSON.stringify(entry.exc_info, null, 2);
  } else {
    excCard.classList.add('d-none');
    excPre.textContent = '';
  }

  const modalEl = document.getElementById('apl-entry-modal');
  if (modalEl && window.bootstrap) {
    const modal = new window.bootstrap.Modal(modalEl);
    modal.show();
  }
}

/**
 * Выполнение AI Диагностики
 */
async function runAiDiagnostics() {
  const summaryEl = document.getElementById('apl-audit-summary-text');
  const healthScoreEl = document.getElementById('apl-audit-health-score');
  const healthBar = document.getElementById('apl-audit-health-bar');
  const recsContainer = document.getElementById('apl-audit-recommendations-list');
  const clustersBody = document.getElementById('apl-audit-clusters-body');

  if (summaryEl) summaryEl.innerHTML = '<div class="spinner-border spinner-border-sm text-info me-2"></div>Анализ логов и поиск первопричин сбоев...';

  try {
    const res = await fetch('/api/v1/app_logs/diagnose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_name: state.currentFile,
        limit: 100,
        focus_errors_only: true,
      })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (healthScoreEl) healthScoreEl.textContent = `${data.health_score}%`;
    if (healthBar) {
      healthBar.style.width = `${data.health_score}%`;
      healthBar.className = `progress-bar ${data.health_score > 80 ? 'bg-success' : (data.health_score > 50 ? 'bg-warning' : 'bg-danger')}`;
    }

    if (summaryEl) summaryEl.textContent = data.summary;

    // Отрисовка рекомендаций
    if (recsContainer) {
      if (!data.recommendations || data.recommendations.length === 0) {
        recsContainer.innerHTML = '<div class="alert alert-success small mb-0"><i class="bi bi-check-circle me-1"></i>Активных проблем и предупреждений не обнаружено.</div>';
      } else {
        recsContainer.innerHTML = data.recommendations.map(r => `
          <div class="card bg-black border-${r.severity === 'high' ? 'danger' : 'warning'} p-2.5 mb-2 shadow-sm">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="fw-bold text-${r.severity === 'high' ? 'danger' : 'warning'} small"><i class="bi bi-exclamation-triangle me-1"></i>${escapeHtml(r.title)}</span>
              <span class="badge bg-${r.severity === 'high' ? 'danger' : 'warning'} small">${r.severity.toUpperCase()}</span>
            </div>
            <div class="small text-light mb-1">${escapeHtml(r.description)}</div>
            <div class="small text-info"><i class="bi bi-arrow-right-circle me-1"></i><strong>Действие:</strong> ${escapeHtml(r.action)}</div>
          </div>
        `).join('');
      }
    }

    // Отрисовка кластеров
    if (clustersBody) {
      if (!data.clusters || data.clusters.length === 0) {
        clustersBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Ошибок и повторяющихся инцидентов не зафиксировано.</td></tr>';
      } else {
        clustersBody.innerHTML = data.clusters.map(c => `
          <tr>
            <td><span class="badge bg-danger fw-bold">${c.count}x</span></td>
            <td><span class="badge bg-dark border border-danger text-danger">${escapeHtml(c.level)}</span></td>
            <td class="font-monospace small text-muted text-nowrap">${escapeHtml(c.last_seen || '--')}</td>
            <td class="font-monospace small text-break">
              <div class="fw-bold text-warning">${escapeHtml(c.pattern)}</div>
              <div class="text-secondary small mt-0.5">${escapeHtml(c.sample_message)}</div>
            </td>
          </tr>
        `).join('');
      }
    }

  } catch (err) {
    console.error('[AppLogs] Ошибка AI диагностики:', err);
    if (summaryEl) summaryEl.innerHTML = `<span class="text-danger">Ошибка диагностики: ${err.message}</span>`;
  }
}

/**
 * Отрисовка графика временной шкалы (Timeline)
 */
function renderTimelineChart() {
  const barsContainer = document.getElementById('apl-timeline-bars');
  const compContainer = document.getElementById('apl-top-components-container');
  if (!state.stats) return;

  const timeline = state.stats.timeline || [];
  if (barsContainer) {
    if (timeline.length === 0) {
      barsContainer.innerHTML = '<div class="text-muted small p-3 text-center w-100">Недостаточно временных меток для построения графика.</div>';
    } else {
      const maxTotal = Math.max(...timeline.map(t => t.total), 1);
      barsContainer.innerHTML = timeline.map(t => {
        const heightPct = Math.max(8, (t.total / maxTotal) * 100);
        const errPct = (t.errors / t.total) * 100;
        const warnPct = (t.warnings / t.total) * 100;
        const timeLabel = t.time.slice(11, 16);

        return `
          <div class="d-flex flex-column align-items-center" style="flex: 1; min-width: 28px; height: 100%; justify-content: flex-end;" title="${t.time}: Всего: ${t.total}, Ошибок: ${t.errors}">
            <span class="small font-monospace text-muted" style="font-size: 0.65rem;">${t.total}</span>
            <div class="w-100 rounded-top" style="height: ${heightPct}%; background: linear-gradient(to top, #0284c7 0%, ${t.errors > 0 ? '#ef4444' : '#38bdf8'} 100%); position: relative;">
            </div>
            <span class="small font-monospace text-secondary text-truncate" style="font-size: 0.65rem; margin-top: 4px;">${timeLabel}</span>
          </div>
        `;
      }).join('');
    }
  }

  if (compContainer && state.stats.components) {
    compContainer.innerHTML = state.stats.components.map(c => `
      <div class="col-md-3 col-sm-6">
        <div class="card bg-black border-secondary p-2 d-flex flex-row justify-content-between align-items-center">
          <span class="font-monospace small text-info text-truncate" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</span>
          <span class="badge bg-primary rounded-pill font-monospace">${c.count}</span>
        </div>
      </div>
    `).join('');
  }
}

/**
 * Загрузка терминала Live Tail
 */
async function loadTailTerminal() {
  const term = document.getElementById('apl-tail-terminal');
  if (!term) return;

  try {
    const res = await fetch(`/api/v1/app_logs/tail?file_name=${encodeURIComponent(state.currentFile)}&lines=120`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    term.textContent = (data.lines || []).join('\n') || '[Файл логов пуст]';

    const autoscroll = document.getElementById('apl-tail-autoscroll')?.checked;
    if (autoscroll) {
      term.scrollTop = term.scrollHeight;
    }
  } catch (err) {
    term.textContent = `[Ошибка чтения tail: ${err.message}]`;
  }
}

/**
 * Загрузка сырого содержимого файла
 */
async function loadRawContent() {
  const pre = document.getElementById('apl-raw-content');
  if (!pre) return;

  pre.textContent = 'Загрузка содержимого файла...';
  try {
    const res = await fetch(`/api/v1/app_logs/tail?file_name=${encodeURIComponent(state.currentFile)}&lines=500`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    pre.textContent = (data.lines || []).join('\n') || '[Файл логов пуст]';
  } catch (err) {
    pre.textContent = `[Ошибка чтения: ${err.message}]`;
  }
}

/**
 * Запуск фонового Live Stream опроса
 */
function startLivePolling() {
  stopLivePolling();
  state.liveTimer = setInterval(async () => {
    if (state.currentMode === 'tail') {
      await loadTailTerminal();
    } else {
      await refreshCurrentView();
    }
  }, 3000);
}

/**
 * Остановка фонового опроса
 */
function stopLivePolling() {
  if (state.liveTimer) {
    clearInterval(state.liveTimer);
    state.liveTimer = null;
  }
}

/**
 * Экранирование HTML
 */
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Авто-инициализация при загрузке скрипта
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAppLogsTab);
} else {
  initAppLogsTab();
}
