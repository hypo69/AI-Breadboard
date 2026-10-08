/**
 * =============================================================================
 * Process Name: Windows Software Transparency Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/software_transparency_tab/main.js?v=20261008_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/software_transparency_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 09:25:00
 * =============================================================================
 */

// Software Transparency Scanner script
// Frontend Controller
(function () {
  let allApps = [];
  let isScanning = false;

  async function initSoftwareTransparencyTab() {
    console.log('[TransparencyScanner] Initializing tab controller...');
    bindEvents();
    await loadScannerData(false);
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('st-btn-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => loadScannerData(true);
    }

    const searchInput = document.getElementById('st-search-input');
    if (searchInput) {
      searchInput.oninput = () => renderTable();
    }
  }

  async function loadScannerData(forceRefresh = false) {
    if (isScanning) return;
    isScanning = true;

    const badge = document.getElementById('st-status-badge');
    const tbody = document.getElementById('st-table-body');

    if (badge) {
      badge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
      badge.innerText = '● Идет сбор сведений о ПО и сети...';
    }

    if (tbody && (!allApps || allApps.length === 0)) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>Выполняется инвентаризация установленных программ, конфигураций и сетевых сокетов...</td></tr>';
    }

    try {
      const url = '/api/v1/software-scanner/scan?force_refresh=' + (forceRefresh ? 'true' : 'false');
      const res = await fetch(url);
      if (!res.ok) throw new Error('HTTP ' + res.status);

      const data = await res.json();
      allApps = data.apps || [];
      const summary = data.summary || {};

      document.getElementById('st-metric-total-apps').innerText = summary.total_apps || allApps.length;
      document.getElementById('st-metric-total-configs').innerText = summary.total_configs_found || 0;
      document.getElementById('st-metric-total-domains').innerText = summary.total_network_domains || 0;
      document.getElementById('st-metric-scan-duration').innerText = (summary.scan_duration_sec || 0) + ' с.';

      if (badge) {
        badge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
        badge.innerText = '● Обнаружено: ' + allApps.length + ' программ';
      }

      renderTable();
    } catch (err) {
      console.error('[TransparencyScanner] Scan error:', err);
      if (badge) {
        badge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
        badge.innerText = '● Ошибка сканирования';
      }
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger py-4">Ошибка: ' + err.message + '</td></tr>';
      }
    } finally {
      isScanning = false;
    }
  }

  function renderTable() {
    const tbody = document.getElementById('st-table-body');
    const searchInput = document.getElementById('st-search-input');
    const searchVal = (searchInput ? searchInput.value : '').toLowerCase().trim();

    if (!tbody) return;

    const filtered = allApps.filter((a) => {
      if (!searchVal) return true;
      return (
        a.name.toLowerCase().includes(searchVal) ||
        (a.publisher && a.publisher.toLowerCase().includes(searchVal)) ||
        (a.install_location && a.install_location.toLowerCase().includes(searchVal))
      );
    });

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Ничего не найдено по фильтру «' + searchVal + '»</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((app) => renderAppRow(app)).join('');
    bindRowActions();
  }

  function renderAppRow(app) {
    const dirs = (app.data_directories || []).map(d => `<div class="text-truncate small text-muted" title="${d.path}">📁 ${d.path} (${(d.total_size_bytes / (1024*1024)).toFixed(1)} MB)</div>`).join('') || '<span class="text-muted small">—</span>';
    const cfgs = (app.config_files || []).map(c => `<button class="btn btn-link btn-sm p-0 text-warning text-decoration-none text-truncate d-block view-config-btn" data-app-id="${app.id}" data-cfg-path="${c.path}" title="${c.path}">⚙️ ${c.filename}</button>`).join('') || '<span class="text-muted small">—</span>';
    const nets = (app.network_endpoints || []).map(n => `<span class="badge bg-secondary me-1 mb-1" title="${n.endpoint}">${n.domain || n.endpoint}</span>`).join('') || '<span class="text-muted small">—</span>';

    return `
      <tr>
        <td>
          <div class="fw-bold">${escapeHtml(app.name)}</div>
          <div class="small text-muted text-truncate" style="max-width: 250px;" title="${app.install_location || ''}">${escapeHtml(app.install_location || '')}</div>
        </td>
        <td>
          <div>${escapeHtml(app.publisher || '—')}</div>
          <div class="small text-muted">${escapeHtml(app.version || '')}</div>
        </td>
        <td>${dirs}</td>
        <td>${cfgs}</td>
        <td>${nets}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-info research-app-btn" data-app-id="${app.id}" title="AI Исследование">
            <i class="bi bi-robot"></i> Анализ
          </button>
        </td>
      </tr>
    `;
  }

  function bindRowActions() {
    document.querySelectorAll('.view-config-btn').forEach(btn => {
      btn.onclick = () => {
        const appId = btn.getAttribute('data-app-id');
        const cfgPath = btn.getAttribute('data-cfg-path');
        openConfigModal(appId, cfgPath);
      };
    });

    document.querySelectorAll('.research-app-btn').forEach(btn => {
      btn.onclick = () => {
        const appId = btn.getAttribute('data-app-id');
        openResearchModal(appId);
      };
    });
  }

  function openConfigModal(appId, cfgPath) {
    const app = allApps.find(a => a.id === appId);
    const cfg = app ? (app.config_files || []).find(c => c.path === cfgPath) : null;

    document.getElementById('st-config-modal-path').innerText = cfgPath;
    document.getElementById('st-config-modal-content').innerText = cfg ? (cfg.content_preview || '[Пустой файл]') : '[Файл не найден]';

    const modalEl = document.getElementById('st-config-modal');
    if (modalEl && window.bootstrap) {
      new bootstrap.Modal(modalEl).show();
    }
  }

  function openResearchModal(appId) {
    const app = allApps.find(a => a.id === appId);
    const titleEl = document.getElementById('st-research-modal-title');
    const bodyEl = document.getElementById('st-research-modal-body');

    if (titleEl) titleEl.innerText = 'AI Исследование: ' + (app ? app.name : appId);
    if (bodyEl) {
      bodyEl.innerHTML = `
        <div class="p-3 bg-secondary bg-opacity-10 rounded border border-secondary mb-3">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
              <h6 class="fw-bold text-info mb-1">${escapeHtml(app ? app.name : appId)}</h6>
              <div class="text-muted small">Издатель: ${escapeHtml(app?.publisher || 'Неизвестен')} | Версия: ${escapeHtml(app?.version || 'N/A')}</div>
            </div>
            <button class="btn btn-primary btn-sm d-flex align-items-center gap-1.5" id="btn-st-start-research">
              <i class="bi bi-robot"></i> Запросить AI-исследование
            </button>
          </div>
        </div>
        <div id="st-research-result-container">
          <div class="text-secondary small">
            <i class="bi bi-info-circle me-1"></i>Нажмите кнопку «Запросить AI-исследование», чтобы отправить запрос к модели ИИ для анализа рисков, безопасности и назначений конфигураций приложения.
          </div>
        </div>
      `;

      const startBtn = document.getElementById('btn-st-start-research');
      if (startBtn) {
        startBtn.onclick = () => executeAppResearch(appId);
      }
    }

    const modalEl = document.getElementById('st-research-modal');
    if (modalEl && window.bootstrap) {
      const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
      bsModal.show();
    }
  }

  async function executeAppResearch(appId) {
    const container = document.getElementById('st-research-result-container');
    const startBtn = document.getElementById('btn-st-start-research');

    if (startBtn) startBtn.disabled = true;
    if (container) {
      container.innerHTML = `
        <div class="text-center py-4 text-info">
          <div class="spinner-border spinner-border-sm me-2" role="status"></div>
          <span>Выполняется аналитическое исследование программы через языковую модель...</span>
        </div>
      `;
    }

    try {
      const res = await fetch('/api/v1/software-scanner/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: appId })
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();

      if (container) {
        container.innerHTML = `
          <div class="card bg-black border-secondary p-3 mb-2">
            <h6 class="text-info fw-bold mb-2">📋 Описание программы:</h6>
            <p class="mb-2 text-light small">${escapeHtml(data.summary || data.description || 'Нет данных')}</p>
            ${data.risk_score !== undefined ? `<div class="mb-2 small"><strong>Оценка риска:</strong> <span class="badge bg-${data.risk_score > 5 ? 'danger' : 'success'}">${data.risk_score}/10</span></div>` : ''}
            ${data.recommendations ? `<h6 class="text-warning fw-bold mt-2 mb-1">💡 Рекомендации:</h6><p class="mb-0 text-light small">${escapeHtml(data.recommendations)}</p>` : ''}
          </div>
        `;
      }
    } catch (err) {
      if (container) {
        container.innerHTML = `
          <div class="alert alert-danger py-2 d-flex align-items-center justify-content-between flex-wrap gap-2 small">
            <div><i class="bi bi-exclamation-triangle me-1"></i>Ошибка анализа: ${escapeHtml(err.message)}</div>
            <button type="button" class="btn btn-sm btn-outline-danger" id="btn-st-retry-research">Повторить</button>
          </div>
        `;
        const retryBtn = document.getElementById('btn-st-retry-research');
        if (retryBtn) {
          retryBtn.onclick = () => executeAppResearch(appId);
        }
      }
    } finally {
      if (startBtn) startBtn.disabled = false;
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
  }

  window.initSoftwareTransparencyTab = initSoftwareTransparencyTab;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSoftwareTransparencyTab);
  } else {
    initSoftwareTransparencyTab();
  }
})();
