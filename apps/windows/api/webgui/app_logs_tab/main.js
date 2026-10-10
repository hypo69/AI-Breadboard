/**
 * =============================================================================
 * Process Name: Windows App Logs Tab - Main Controller Script
 * =============================================================================
 * Description:
 *   Клиентский контроллер продвинутого анализатора внутренних логов программы
 *   AI-Breadboard строго из %APPDATA%\AI-Breadboard\logs.
 *   Включает глубокую интеграцию с AIModalDialog (WikiLLM L1 Cache + AI Root Cause),
 *   интерактивный Timeline-график, быстрые пресеты фильтрации, экспорт (CSV/JSON/MD)
 *   и высокопроизводительный Live Tail Terminal.
 *   Полная адаптивность к светлой, кирпичной, темной и терминальной темам.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script type="module" src="/html/app_logs_tab/main.js?v=20261010_v3"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/app_logs_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-10 12:45:00
 * =============================================================================
 */

let state = {
  currentFile: 'log.json',
  currentMode: 'table',
  liveActive: false,
  liveTimer: null,
  records: [],
  files: [],
  overview: null,
  stats: null,
  selectedEntry: null,
  activePreset: 'all',
};

/**
 * Инициализация вкладки анализатора логов
 */
export async function initAppLogsTab() {
  bindEvents();
  await loadOverviewAndFiles();
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
      });
      btn.classList.add('active');

      state.currentMode = btn.dataset.mode;
      switchViewMode(state.currentMode);
    });
  });

  // Быстрые пресеты фильтрации
  document.querySelectorAll('.apl-quick-preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.apl-quick-preset-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activePreset = btn.dataset.preset;
      applyQuickPreset(state.activePreset);
    });
  });

  // Кнопка обновления
  const btnRefresh = document.getElementById('btn-apl-refresh');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', async () => {
      await loadOverviewAndFiles();
      await refreshCurrentView();
      if (window.toast) window.toast.info('Обновлено', 'Данные журналов успешно обновлены');
    });
  }

  // Кнопка AI диагностики
  const btnDiagnose = document.getElementById('btn-apl-diagnose');
  if (btnDiagnose) {
    btnDiagnose.addEventListener('click', async () => {
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

  const timePresetSelect = document.getElementById('apl-time-preset-select');
  if (timePresetSelect) {
    timePresetSelect.addEventListener('change', () => refreshCurrentView());
  }

  const limitSelect = document.getElementById('apl-limit-select');
  if (limitSelect) {
    limitSelect.addEventListener('change', () => refreshCurrentView());
  }

  // Сброс фильтров
  const btnReset = document.getElementById('btn-apl-reset-filters');
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      resetAllFilters();
    });
  }

  // Экспорт CSV
  const btnExportCsv = document.getElementById('btn-apl-export-csv');
  if (btnExportCsv) {
    btnExportCsv.addEventListener('click', (e) => {
      e.preventDefault();
      triggerExport('csv');
    });
  }

  // Экспорт JSON
  const btnExportJson = document.getElementById('btn-apl-export-json');
  if (btnExportJson) {
    btnExportJson.addEventListener('click', (e) => {
      e.preventDefault();
      triggerExport('json');
    });
  }

  // Экспорт Markdown
  const btnExportMd = document.getElementById('btn-apl-export-md');
  if (btnExportMd) {
    btnExportMd.addEventListener('click', (e) => {
      e.preventDefault();
      triggerExport('markdown');
    });
  }

  // Скачивание сырого файла
  const btnDownloadRaw = document.getElementById('btn-apl-download-raw');
  if (btnDownloadRaw) {
    btnDownloadRaw.addEventListener('click', (e) => {
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
          await loadOverviewAndFiles();
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

  // Поиск внутри терминала
  const tailFilterInput = document.getElementById('apl-tail-filter');
  if (tailFilterInput) {
    tailFilterInput.addEventListener('input', () => {
      loadTailTerminal();
    });
  }

  // Копирование сырого содержимого
  const btnCopyRaw = document.getElementById('btn-apl-copy-raw');
  if (btnCopyRaw) {
    btnCopyRaw.addEventListener('click', () => {
      const content = document.getElementById('apl-raw-content')?.textContent || '';
      navigator.clipboard.writeText(content).then(() => {
        if (window.toast) window.toast.success('Скопировано', 'Содержимое файла скопировано');
      });
    });
  }
}

/**
 * Применение быстрых пресетов фильтрации
 */
function applyQuickPreset(preset) {
  const levelSelect = document.getElementById('apl-level-select');
  const compSelect = document.getElementById('apl-component-select');
  const timeSelect = document.getElementById('apl-time-preset-select');
  const searchInput = document.getElementById('apl-search-input');

  if (preset === 'all') {
    if (levelSelect) levelSelect.value = '';
    if (compSelect) compSelect.value = '';
    if (timeSelect) timeSelect.value = '';
    if (searchInput) searchInput.value = '';
  } else if (preset === 'errors') {
    if (levelSelect) levelSelect.value = 'ERRORS';
  } else if (preset === 'warnings_errors') {
    if (levelSelect) levelSelect.value = 'WARNINGS_ERRORS';
  } else if (preset === 'windows') {
    if (searchInput) searchInput.value = 'Windows';
  } else if (preset === 'ai') {
    if (searchInput) searchInput.value = 'AI';
  } else if (preset === 'fastapi') {
    if (searchInput) searchInput.value = 'FastAPI';
  } else if (preset === 'hour') {
    if (timeSelect) timeSelect.value = '1h';
  } else if (preset === 'day') {
    if (timeSelect) timeSelect.value = '24h';
  }

  refreshCurrentView();
}

/**
 * Сброс всех фильтров
 */
function resetAllFilters() {
  const searchInput = document.getElementById('apl-search-input');
  const levelSelect = document.getElementById('apl-level-select');
  const compSelect = document.getElementById('apl-component-select');
  const timeSelect = document.getElementById('apl-time-preset-select');
  const limitSelect = document.getElementById('apl-limit-select');

  if (searchInput) searchInput.value = '';
  if (levelSelect) levelSelect.value = '';
  if (compSelect) compSelect.value = '';
  if (timeSelect) timeSelect.value = '';
  if (limitSelect) limitSelect.value = '200';

  document.querySelectorAll('.apl-quick-preset-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.preset === 'all');
  });

  refreshCurrentView();
}

/**
 * Запуск экспорта данных
 */
function triggerExport(format) {
  const search = document.getElementById('apl-search-input')?.value || '';
  const level = document.getElementById('apl-level-select')?.value || '';
  const url = `/api/v1/app_logs/export?file_name=${encodeURIComponent(state.currentFile)}&export_format=${format}&search=${encodeURIComponent(search)}&level=${encodeURIComponent(level)}`;
  window.open(url, '_blank');
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
 * Загрузка сводки и списка файлов логов
 */
async function loadOverviewAndFiles() {
  try {
    const [ovRes, filesRes] = await Promise.all([
      fetch('/api/v1/app_logs/overview').catch(() => null),
      fetch('/api/v1/app_logs/files').catch(() => null),
    ]);

    if (ovRes && ovRes.ok) {
      state.overview = await ovRes.json();
    }
    if (filesRes && filesRes.ok) {
      const data = await filesRes.json();
      state.files = data.files || [];
      const pathLabel = document.getElementById('apl-full-path-label');
      if (pathLabel && data.logs_dir) {
        pathLabel.textContent = data.logs_dir;
        pathLabel.title = data.logs_dir;
      }
    }

    renderFilesBadges();
  } catch (err) {
    console.error('[AppLogs] Ошибка загрузки файлов и сводки:', err);
  }
}

/**
 * Отрисовка бейджей файлов журналов со статусными индикаторами
 */
function renderFilesBadges() {
  const container = document.getElementById('apl-files-badges-container');
  if (!container) return;

  container.innerHTML = '';
  if (state.files.length === 0) {
    container.innerHTML = '<span class="text-muted small">Файлы журналов не обнаружены.</span>';
    return;
  }

  // Карта ошибок по файлам из overview
  const errorMap = {};
  if (state.overview && state.overview.files) {
    state.overview.files.forEach(f => {
      errorMap[f.name] = f.recent_errors || 0;
    });
  }

  state.files.forEach(f => {
    const btn = document.createElement('button');
    btn.type = 'button';
    const isActive = f.name === state.currentFile;
    const errorsCount = errorMap[f.name] || 0;
    const hasError = errorsCount > 0;

    btn.className = `btn btn-sm rounded-pill px-2.5 py-0.5 small apl-file-badge ${isActive ? 'active' : ''} ${hasError ? 'has-error' : ''}`;
    btn.style.fontSize = '0.76rem';

    const icon = f.is_json ? 'bi-filetype-json text-info' : 'bi-file-text text-warning';
    const errIndicator = hasError ? `<span class="badge bg-danger ms-1" style="font-size:0.65rem;" title="Ошибок: ${errorsCount}">${errorsCount}</span>` : '';

    btn.innerHTML = `<i class="bi ${icon} me-1"></i><strong>${f.name}</strong> <span class="badge apl-card border border-secondary-subtle ms-1">${f.size_formatted}</span>${errIndicator}`;

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
  const timePreset = document.getElementById('apl-time-preset-select')?.value || '';
  const limit = document.getElementById('apl-limit-select')?.value || '200';

  const fnStat = document.getElementById('apl-stat-filename');
  if (fnStat) fnStat.textContent = state.currentFile;

  try {
    const queryParams = new URLSearchParams({
      file_name: state.currentFile,
      limit: limit,
      search: search,
      level: level,
      component: component,
      time_preset: timePreset,
    });

    const res = await fetch(`/api/v1/app_logs/records?${queryParams.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.records = data.records || [];
    state.stats = data.stats || null;

    updateHeaderStats(data);
    updateComponentsDropdown(data.stats?.components || []);

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
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">Ошибка загрузки: ${escapeHtml(err.message)}</td></tr>`;
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
 * Отрисовка строк таблицы записей
 */
function renderRecordsTable(records) {
  const tbody = document.getElementById('apl-table-body');
  if (!tbody) return;

  if (!records || records.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Нет записей, удовлетворяющих условиям фильтрации.</td></tr>';
    return;
  }

  tbody.innerHTML = records.map(entry => {
    let badgeClass = 'badge-apl-inf';
    const lvl = (entry.level || '').toUpperCase();
    if (lvl === 'CRITICAL' || lvl === 'FATAL') badgeClass = 'badge-apl-crit';
    else if (lvl === 'ERROR') badgeClass = 'badge-apl-err';
    else if (lvl === 'WARNING' || lvl === 'WARN') badgeClass = 'badge-apl-warn';
    else if (lvl === 'DEBUG') badgeClass = 'badge-apl-deb';

    const repeatBadge = entry.repeat_count > 1 ? `<span class="badge apl-card border border-secondary-subtle text-warning ms-1" title="Повторений">${entry.repeat_count}x</span>` : '';
    const hasExc = !!entry.exc_info;
    const excBadge = hasExc ? `<span class="badge bg-danger ms-1" title="Содержит Stacktrace"><i class="bi bi-bug"></i> Trace</span>` : '';

    return `
      <tr class="interactive-log-row" data-id="${entry.id}">
        <td class="font-monospace small text-muted text-nowrap">${escapeHtml(entry.timestamp || '--:--:--')}</td>
        <td><span class="badge ${badgeClass} small">${escapeHtml(entry.level || 'INFO')}</span>${repeatBadge}</td>
        <td><span class="badge apl-comp-badge font-monospace text-truncate" style="max-width: 120px;" title="${escapeHtml(entry.component)}">${escapeHtml(entry.component)}</span></td>
        <td class="font-monospace small text-break text-body">${escapeHtml(entry.message || '')}${excBadge}</td>
        <td class="text-end no-modal-trigger">
          <button type="button" class="btn btn-xs btn-outline-info rounded px-1.5 py-0.5 btn-entry-ai" data-id="${entry.id}" title="AI Анализ в модальном окне">
            <i class="bi bi-robot"></i> AI
          </button>
        </td>
      </tr>
    `;
  }).join('');

  // Привязка обработчиков клика по строкам для вызова AIModalDialog
  tbody.querySelectorAll('.interactive-log-row').forEach(row => {
    row.addEventListener('click', (event) => {
      const entryId = row.getAttribute('data-id');
      const entry = records.find(x => String(x.id) === String(entryId));
      if (!entry) return;

      openItemAiModal(entry);
    });
  });

  // Кнопка AI Анализа в строке
  tbody.querySelectorAll('.btn-entry-ai').forEach(btn => {
    btn.addEventListener('click', (event) => {
      event.stopPropagation();
      const entryId = btn.getAttribute('data-id');
      const entry = records.find(x => String(x.id) === String(entryId));
      if (!entry) return;

      openItemAiModal(entry);
    });
  });
}

/**
 * Открытие универсального модального окна AIModalDialog для анализа записи
 */
function openItemAiModal(entry) {
  state.selectedEntry = entry;
  const modal = window.AIModalDialog || window.AITableModal;

  let badgeClass = 'badge bg-info';
  const lvl = (entry.level || '').toUpperCase();
  if (lvl === 'CRITICAL' || lvl === 'FATAL' || lvl === 'ERROR') badgeClass = 'badge bg-danger';
  else if (lvl === 'WARNING' || lvl === 'WARN') badgeClass = 'badge bg-warning text-dark';
  else if (lvl === 'DEBUG') badgeClass = 'badge bg-secondary';

  const icon = (lvl === 'CRITICAL' || lvl === 'ERROR') ? '🚨' : ((lvl === 'WARNING' || lvl === 'WARN') ? '⚠️' : '📑');

  if (modal && typeof modal.show === 'function') {
    modal.show({
      title: `[${entry.level}] ${entry.component || 'Log Entry'}`,
      subtitle: `Время: ${entry.timestamp || 'N/A'} | Файл: ${state.currentFile} | Повторов: ${entry.repeat_count || 1}`,
      icon: icon,
      tableType: 'process',
      badges: [
        { text: entry.level || 'INFO', class: badgeClass },
        { text: entry.component || 'System', class: 'badge apl-comp-badge' },
        { text: `${entry.repeat_count || 1}x`, class: 'badge border text-secondary' }
      ],
      metadata: [
        { label: 'Временная метка', value: entry.timestamp || 'N/A' },
        { label: 'Компонент / Модуль', value: entry.component || 'N/A' },
        { label: 'Уровень события', value: entry.level || 'INFO' },
        { label: 'Файл журнала', value: state.currentFile },
        { label: 'Повторений инцидента', value: `${entry.repeat_count || 1}` },
        { label: 'Сообщение лога', value: entry.message || '', fullWidth: true, isCode: true },
      ],
      rawTitle: 'Стек вызовов (Traceback) / Сырая запись',
      rawContent: entry.exc_info ? (typeof entry.exc_info === 'string' ? entry.exc_info : JSON.stringify(entry.exc_info, null, 2)) : entry.raw || entry.message,
      autoRun: false,
      actions: [
        {
          label: 'Копировать запись',
          icon: 'bi-clipboard',
          class: 'btn-outline-info',
          onClick: () => {
            navigator.clipboard.writeText(JSON.stringify(entry, null, 2)).then(() => {
              if (window.toast) window.toast.success('Скопировано', 'Лог-запись скопирована в буфер обмена');
            });
          }
        }
      ]
    });
  } else {
    // Fallback: alert
    console.log('[AppLogs] Запись лога:', entry);
    alert(`[${entry.level}] ${entry.component}\n\n${entry.message}`);
  }
}

/**
 * Выполнение глубокой AI Диагностики и кластеризации сбоев
 */
async function runAiDiagnostics() {
  const summaryEl = document.getElementById('apl-audit-summary-text');
  const healthScoreEl = document.getElementById('apl-audit-health-score');
  const healthBar = document.getElementById('apl-audit-health-bar');
  const recsContainer = document.getElementById('apl-audit-recommendations-list');
  const clustersBody = document.getElementById('apl-audit-clusters-body');

  if (summaryEl) summaryEl.innerHTML = '<div class="spinner-border spinner-border-sm text-info me-2"></div>Глубокий анализ логов, поиск первопричин и кластеризация сбоев...';

  try {
    const res = await fetch('/api/v1/app_logs/diagnose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_name: state.currentFile,
        limit: 150,
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
        recsContainer.innerHTML = '<div class="alert alert-success small mb-0"><i class="bi bi-check-circle me-1"></i>Активных сбоев и критических предупреждений не зафиксировано.</div>';
      } else {
        recsContainer.innerHTML = data.recommendations.map(r => `
          <div class="card apl-card border-${r.severity === 'high' ? 'danger' : 'warning'} p-2.5 mb-2 shadow-sm">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="fw-bold text-${r.severity === 'high' ? 'danger' : 'warning'} small"><i class="bi bi-exclamation-triangle me-1"></i>${escapeHtml(r.title)}</span>
              <span class="badge bg-${r.severity === 'high' ? 'danger' : 'warning'} small">${r.severity.toUpperCase()}</span>
            </div>
            <div class="small text-body mb-1">${escapeHtml(r.description)}</div>
            <div class="small text-info"><i class="bi bi-arrow-right-circle me-1"></i><strong>Рекомендуемое действие:</strong> ${escapeHtml(r.action)}</div>
          </div>
        `).join('');
      }
    }

    // Отрисовка кластеров
    if (clustersBody) {
      if (!data.clusters || data.clusters.length === 0) {
        clustersBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Ошибок и повторяющихся инцидентов не зафиксировано.</td></tr>';
      } else {
        clustersBody.innerHTML = data.clusters.map((c, idx) => `
          <tr class="interactive-cluster-row" data-cluster-idx="${idx}">
            <td><span class="badge bg-danger fw-bold">${c.count}x</span></td>
            <td><span class="badge apl-card border border-danger text-danger">${escapeHtml(c.level)}</span></td>
            <td class="font-monospace small text-muted text-nowrap">${escapeHtml(c.last_seen || '--')}</td>
            <td class="font-monospace small text-break">
              <div class="fw-bold text-warning">${escapeHtml(c.pattern)}</div>
              <div class="text-muted small mt-0.5">${escapeHtml(c.sample_message)}</div>
            </td>
            <td class="text-end">
              <button type="button" class="btn btn-xs btn-outline-warning rounded px-1.5 py-0.5 btn-cluster-inspect" data-cluster-idx="${idx}" title="AI инспекция кластера">
                <i class="bi bi-robot"></i> Инспекция
              </button>
            </td>
          </tr>
        `).join('');

        // Обработчик инспекции кластера
        clustersBody.querySelectorAll('.btn-cluster-inspect').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const idx = parseInt(btn.getAttribute('data-cluster-idx'), 10);
            const cluster = data.clusters[idx];
            if (!cluster) return;

            openItemAiModal({
              id: `cluster-${idx}`,
              level: cluster.level,
              component: 'Error Cluster',
              timestamp: cluster.last_seen,
              repeat_count: cluster.count,
              message: cluster.sample_message,
              exc_info: cluster.exc_info,
              raw: cluster.sample_message
            });
          });
        });
      }
    }

  } catch (err) {
    console.error('[AppLogs] Ошибка AI диагностики:', err);
    if (summaryEl) summaryEl.innerHTML = `<span class="text-danger">Ошибка диагностики: ${escapeHtml(err.message)}</span>`;
  }
}

/**
 * Отрисовка интерактивного графика временной шкалы (Timeline)
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
        const heightPct = Math.max(10, (t.total / maxTotal) * 100);
        const timeLabel = t.time.slice(11, 16);

        const hasErr = t.errors > 0;
        const hasWarn = t.warnings > 0;
        let barBg = 'linear-gradient(to top, var(--nav-active, #0284c7) 0%, var(--nav-active, #38bdf8) 100%)';
        if (hasErr) {
          barBg = 'linear-gradient(to top, #ef4444 0%, #dc2626 100%)';
        } else if (hasWarn) {
          barBg = 'linear-gradient(to top, #f59e0b 0%, #d97706 100%)';
        }

        return `
          <div class="d-flex flex-column align-items-center apl-timeline-bar-item" data-time="${t.time}" style="flex: 1; min-width: 32px; height: 100%; justify-content: flex-end;" title="${t.time}: Всего событий: ${t.total}, Ошибок: ${t.errors}, Предупреждений: ${t.warnings}">
            <span class="small font-monospace text-muted" style="font-size: 0.65rem;">${t.total}</span>
            <div class="w-100 rounded-top" style="height: ${heightPct}%; background: ${barBg}; position: relative;">
            </div>
            <span class="small font-monospace text-muted text-truncate" style="font-size: 0.65rem; margin-top: 4px;">${timeLabel}</span>
          </div>
        `;
      }).join('');

      // Клик по столбцу фильтрует таблицу по этому временному слоту
      barsContainer.querySelectorAll('.apl-timeline-bar-item').forEach(bar => {
        bar.addEventListener('click', () => {
          const tVal = bar.getAttribute('data-time');
          const searchInput = document.getElementById('apl-search-input');
          if (searchInput && tVal) {
            searchInput.value = tVal.slice(0, 13);
            const tableTab = document.querySelector('#apl-mode-tabs [data-mode="table"]');
            if (tableTab) tableTab.click();
            refreshCurrentView();
          }
        });
      });
    }
  }

  if (compContainer && state.stats.components) {
    compContainer.innerHTML = state.stats.components.map(c => `
      <div class="col-md-3 col-sm-6">
        <div class="card apl-card p-2 d-flex flex-row justify-content-between align-items-center shadow-sm" style="cursor: pointer;" title="Фильтровать по модулю: ${escapeHtml(c.name)}">
          <span class="font-monospace small text-info text-truncate" style="max-width: 130px;">${escapeHtml(c.name)}</span>
          <span class="badge bg-primary rounded-pill font-monospace">${c.count}</span>
        </div>
      </div>
    `).join('');

    // Клик по компоненту фильтрует по нему
    compContainer.querySelectorAll('.card').forEach((card, idx) => {
      card.addEventListener('click', () => {
        const cName = state.stats.components[idx]?.name;
        const compSelect = document.getElementById('apl-component-select');
        if (compSelect && cName) {
          compSelect.value = cName;
          const tableTab = document.querySelector('#apl-mode-tabs [data-mode="table"]');
          if (tableTab) tableTab.click();
          refreshCurrentView();
        }
      });
    });
  }
}

/**
 * Загрузка терминала Live Tail
 */
async function loadTailTerminal() {
  const term = document.getElementById('apl-tail-terminal');
  if (!term) return;

  const filterText = (document.getElementById('apl-tail-filter')?.value || '').toLowerCase();

  try {
    const res = await fetch(`/api/v1/app_logs/tail?file_name=${encodeURIComponent(state.currentFile)}&lines=150`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    let lines = data.lines || [];
    if (filterText) {
      lines = lines.filter(l => l.toLowerCase().includes(filterText));
    }

    term.textContent = lines.join('\n') || '[Файл логов пуст или нет совпадений по фильтру]';

    const autoscroll = document.getElementById('apl-tail-autoscroll')?.checked;
    if (autoscroll) {
      term.scrollTop = term.scrollHeight;
    }
  } catch (err) {
    term.textContent = `[Ошибка чтения tail: ${escapeHtml(err.message)}]`;
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
    pre.textContent = `[Ошибка чтения: ${escapeHtml(err.message)}]`;
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
