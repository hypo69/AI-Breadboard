/**
 * =============================================================================
 * Process Name: Windows System Logs & Activity - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля журналов событий и активности системы Windows.
 *   Полная поддержка светлой и тёмной темы с надежным парсингом каналов и событий.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/html/system_control_tab/main.js?v=20261006_v12" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/system_control_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 10:56:00
 * =============================================================================
 */

(function () {
  'use strict';

  let isSCCInitialized = false;

  // Состояния центра журналов событий
  let currentChannel = 'System';
  let currentFilePath = '';
  let currentMode = 'live';
  let cachedEvents = [];
  let cachedChannels = [];
  let selectedEvent = null;
  let liveIntervalTimer = null;
  let isLogRequestInProgress = false;
  let globalTooltipEl = null;

  /**
   * Экранирование HTML-символов для защиты от XSS.
   *
   * @param {string} str - Исходная строка.
   * @returns {string} Экранированная строка.
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

  /**
   * Форматирование ISO-времени.
   *
   * @param {string} isoStr - Строка ISO Timestamp.
   * @returns {string} Отформатированное время.
   */
  function formatTime(isoStr) {
    if (!isoStr) return '-';
    try {
      return new Date(isoStr).toLocaleTimeString();
    } catch {
      return isoStr.slice(11, 19);
    }
  }

  /**
   * Определение CSS-класса для уровня важности события.
   *
   * @param {string} level - Уровень важности.
   * @returns {string} Имя CSS-класса.
   */
  function getSeverityClass(level) {
    const lvl = (level || '').toLowerCase();
    if (lvl.includes('crit')) return 'badge-crit';
    if (lvl.includes('err')) return 'badge-err';
    if (lvl.includes('warn')) return 'badge-warn';
    if (lvl.includes('verb')) return 'badge-verb';
    return 'badge-inf';
  }

  /**
   * Проверка прав администратора и обновление бейджа.
   */
  async function fetchStatus() {
    try {
      const res = await fetch('/api/system-control/status');
      if (!res.ok) return;
      const data = await res.json();

      const elevBadge = document.getElementById('scc-elevation-badge');
      if (elevBadge) {
        if (data.is_elevated) {
          elevBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
          elevBadge.innerHTML = '🛡️ Режим: Администратор (Полный доступ)';
        } else {
          elevBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
          elevBadge.innerHTML = '👁️ Режим: Обычный пользователь (Ограничено)';
        }
      }
    } catch (e) {
      console.warn('[SystemLogs] Ошибка проверки прав:', e);
    }
  }

  // =========================================================================
  // ЖУРНАЛ АКТИВНОСТИ И ОПЕРАЦИЙ
  // =========================================================================

  async function loadSccActivityLogs() {
    const tbody = document.getElementById('scc-logs-tbody');
    if (!tbody) return;

    try {
      const res = await fetch('/api/system-control/logs');
      if (!res.ok) return;
      const data = await res.json();
      const logs = data.logs || [];

      if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted p-3">Журнал операций пуст.</td></tr>';
        return;
      }

      tbody.innerHTML = logs.map(l => `
        <tr>
          <td class="font-monospace small" style="color: var(--text-muted);">${escapeHtml(l.timestamp)}</td>
          <td><span class="badge bg-secondary font-monospace">${escapeHtml(l.action)}</span></td>
          <td style="color: var(--text-color);">${escapeHtml(l.target)}</td>
          <td><span class="badge ${l.status === 'SUCCESS' || l.status === 'OK' ? 'bg-success' : 'bg-warning text-dark'}">${escapeHtml(l.status)}</span></td>
          <td class="small text-truncate" style="max-width: 280px; color: var(--text-muted);" title="${escapeHtml(l.details)}">${escapeHtml(l.details)}</td>
        </tr>
      `).join('');
    } catch (e) {
      console.warn('[SystemLogs] Ошибка загрузки логов активности:', e);
    }
  }

  // =========================================================================
  // WINDOWS OS SYSTEM LOG CENTER (ПОТОК, КАНАЛЫ, АУДИТ, RAG, ИНЦИДЕНТЫ)
  // =========================================================================

  function createGlobalChannelTooltip() {
    if (globalTooltipEl) return;
    globalTooltipEl = document.createElement('div');
    globalTooltipEl.className = 'slc-tooltip-popup';
    globalTooltipEl.id = 'slc-global-tooltip';
    document.body.appendChild(globalTooltipEl);
  }

  function showChannelTooltip(channelData, mouseEvent) {
    if (!globalTooltipEl) createGlobalChannelTooltip();
    const isFile = !!(channelData.file_path || channelData.location || (channelData.source_type && channelData.source_type !== 'channel'));
    const icon = isFile ? '📄' : '📁';
    const chanTitle = channelData.display_name || channelData.channel_name || channelData.name || 'Журнал';
    const typeLabel = channelData.source_type === 'channel' || !isFile ? 'Live Windows Channel' : 'EVTX File Archive';
    const countVal = channelData.record_count !== undefined ? channelData.record_count : (channelData.records || 'N/A');
    const recCount = typeof countVal === 'number' ? countVal.toLocaleString() : String(countVal);
    const sizeStr = channelData.file_size_mb ? `${channelData.file_size_mb} MB` : (channelData.size_bytes ? `${(channelData.size_bytes / 1024 / 1024).toFixed(1)} MB` : 'N/A');

    globalTooltipEl.innerHTML = `
      <div class="fw-bold mb-1 d-flex align-items-center gap-1.5" style="color: var(--text-color);">
        <span>${icon}</span>
        <span class="text-truncate">${escapeHtml(chanTitle)}</span>
      </div>
      <div class="mb-2" style="font-size: 0.76rem; color: var(--text-muted) !important;">
        ${escapeHtml(channelData.description || 'Стандартный системный канал событий Windows.')}
      </div>
      <div class="d-flex justify-content-between align-items-center pt-1 border-top" style="border-color: var(--border-color) !important; font-size: 0.74rem;">
        <span class="text-muted">Тип: <strong style="color: var(--text-color);">${typeLabel}</strong></span>
        <span class="text-muted">Записей: <strong class="text-info">${recCount}</strong></span>
      </div>
      <div class="d-flex justify-content-between align-items-center pt-1" style="font-size: 0.74rem;">
        <span class="text-muted">Размер: <strong style="color: var(--text-color);">${sizeStr}</strong></span>
        <span class="text-success fw-bold">Доступен</span>
      </div>
    `;

    const pad = 15;
    let left = mouseEvent.clientX + pad;
    let top = mouseEvent.clientY + pad;
    if (left + 330 > window.innerWidth) left = mouseEvent.clientX - 335;
    if (top + 140 > window.innerHeight) top = mouseEvent.clientY - 145;

    globalTooltipEl.style.left = `${Math.max(10, left)}px`;
    globalTooltipEl.style.top = `${Math.max(10, top)}px`;
    globalTooltipEl.classList.add('show');
  }

  function hideChannelTooltip() {
    if (globalTooltipEl) {
      globalTooltipEl.classList.remove('show');
    }
  }

  async function scanChannels(force = false) {
    const treeEl = document.getElementById('slc-channel-tree-container');
    const countBadge = document.getElementById('slc-channel-count-badge');
    const sourcesStat = document.getElementById('slc-stat-sources');

    if (treeEl && (!cachedChannels || cachedChannels.length === 0)) {
      treeEl.innerHTML = '<div class="text-muted p-2 small"><div class="spinner-border spinner-border-sm text-info me-1"></div>Поиск каналов...</div>';
    }

    try {
      const response = await fetch(`/api/v1/system_logs/scan?force=${force}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      cachedChannels = data.channels || [];

      if (countBadge) countBadge.textContent = cachedChannels.length;
      if (sourcesStat) sourcesStat.textContent = cachedChannels.length.toLocaleString();

      renderChannelTree(cachedChannels);
    } catch (err) {
      if (treeEl) treeEl.innerHTML = `<div class="text-danger p-2 small">Ошибка сканирования каналов: ${escapeHtml(err.message)}</div>`;
    }
  }

  function renderChannelTree(channels) {
    const treeEl = document.getElementById('slc-channel-tree-container');
    if (!treeEl) return;

    if (!channels || channels.length === 0) {
      treeEl.innerHTML = '<div class="text-muted p-2 small">Каналы не найдены.</div>';
      return;
    }

    createGlobalChannelTooltip();

    treeEl.innerHTML = channels.map(ch => {
      const isFile = !!(ch.file_path || (ch.source_type && ch.source_type !== 'channel'));
      const chName = ch.channel_name || ch.display_name || ch.name || 'Channel';
      const chPath = ch.location || ch.file_path || '';
      const isActive = isFile ? (currentFilePath === chPath) : (currentChannel === chName && !currentFilePath);
      const icon = isFile ? 'bi-file-earmark-text text-secondary' : 'bi-folder-fill text-warning';
      
      let sizeBadge = '';
      if (ch.record_count !== undefined && ch.record_count > 0) {
        const countText = ch.record_count >= 1000 ? `${(ch.record_count / 1000).toFixed(1)}k` : String(ch.record_count);
        sizeBadge = `<span class="badge bg-secondary font-monospace" style="font-size: 0.68rem;">${countText}</span>`;
      } else if (ch.file_size_mb) {
        sizeBadge = `<span class="badge bg-secondary font-monospace" style="font-size: 0.68rem;">${ch.file_size_mb} MB</span>`;
      }

      return `
        <div class="slc-tree-item ${isActive ? 'active' : ''}" data-name="${escapeHtml(chName)}" data-path="${escapeHtml(chPath)}">
          <div class="d-flex align-items-center gap-2 text-truncate me-2" style="min-width: 0; flex: 1 1 auto;">
            <i class="bi ${icon} flex-shrink-0"></i>
            <span class="text-truncate fw-medium" title="${escapeHtml(chName)}">${escapeHtml(chName)}</span>
          </div>
          <div class="d-flex align-items-center flex-shrink-0">
            ${sizeBadge}
          </div>
        </div>
      `;
    }).join('');

    treeEl.querySelectorAll('.slc-tree-item').forEach((el, index) => {
      const chData = channels[index];
      el.addEventListener('mouseenter', (e) => {
        if (chData) showChannelTooltip(chData, e);
      });
      el.addEventListener('mousemove', (e) => {
        if (chData) showChannelTooltip(chData, e);
      });
      el.addEventListener('mouseleave', () => {
        hideChannelTooltip();
      });

      el.addEventListener('click', () => {
        hideChannelTooltip();
        treeEl.querySelectorAll('.slc-tree-item').forEach(i => i.classList.remove('active'));
        el.classList.add('active');

        currentChannel = el.getAttribute('data-name') || 'System';
        currentFilePath = el.getAttribute('data-path') || '';

        const statChan = document.getElementById('slc-stat-channel');
        if (statChan) statChan.textContent = currentChannel;

        const mainTitle = document.getElementById('slc-main-view-title');
        if (mainTitle) mainTitle.innerHTML = `<i class="bi bi-list-columns-reverse me-2 text-primary"></i>События канала: <span class="text-info">${escapeHtml(currentChannel)}</span>`;

        loadEvents();
      });
    });
  }

  async function loadEvents() {
    if (isLogRequestInProgress) return;
    isLogRequestInProgress = true;

    const tbody = document.getElementById('slc-table-body');
    const statEvents = document.getElementById('slc-stat-events');
    const statIncidents = document.getElementById('slc-stat-incidents');
    const streamBadge = document.getElementById('slc-stream-count-badge');

    const searchInput = document.getElementById('slc-search-input');
    const levelSelect = document.getElementById('slc-level-select');
    const hoursSelect = document.getElementById('slc-hours-select');
    const limitSelect = document.getElementById('slc-limit-select');
    const eventIdInput = document.getElementById('slc-eventid-input');

    const query = searchInput ? searchInput.value.trim() : '';
    const level = levelSelect ? levelSelect.value : '';
    const hours = hoursSelect ? hoursSelect.value : '24';
    const limit = limitSelect ? limitSelect.value : '100';
    const eventId = eventIdInput ? eventIdInput.value.trim() : '';

    const params = new URLSearchParams({
      channel: currentChannel,
      limit: limit,
      hours: hours,
    });

    if (query) params.append('query', query);
    if (level) params.append('level', level);
    if (eventId) params.append('event_id', eventId);
    if (currentFilePath) params.append('file_path', currentFilePath);

    let url = `/api/v1/system_logs/events?${params.toString()}`;
    if (currentMode === 'errors') {
      params.set('level', 'Error');
      url = `/api/v1/system_logs/events?${params.toString()}`;
    }

    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      cachedEvents = data.events || [];

      if (statEvents) statEvents.textContent = cachedEvents.length.toLocaleString();
      if (streamBadge) streamBadge.textContent = `${cachedEvents.length} записей`;

      const faults = cachedEvents.filter(e => {
        const l = (e.level || '').toLowerCase();
        return l.includes('err') || l.includes('crit');
      }).length;
      if (statIncidents) statIncidents.textContent = faults;

      renderEventsTable(cachedEvents);
    } catch (err) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">Ошибка загрузки событий: ${escapeHtml(err.message)}</td></tr>`;
    } finally {
      isLogRequestInProgress = false;
    }
  }

  function renderEventsTable(events) {
    const tbody = document.getElementById('slc-table-body');
    if (!tbody) return;

    if (!events || events.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Нет записей, удовлетворяющих заданным фильтрам.</td></tr>';
      return;
    }

    tbody.innerHTML = events.map((e, idx) => {
      const timeFormatted = formatTime(e.timestamp);
      const isErr = (e.level || '').toLowerCase().includes('err') || (e.level || '').toLowerCase().includes('crit');
      const provName = e.provider || e.source || '-';
      const msgText = e.message || e.raw_data || '-';

      return `
        <tr data-index="${idx}" class="${isErr ? 'table-danger-subtle' : ''}">
          <td class="font-monospace small" style="color: var(--text-muted);">${escapeHtml(timeFormatted)}</td>
          <td><span class="badge ${getSeverityClass(e.level)} text-uppercase" style="font-size: 0.68rem;">${escapeHtml(e.level || 'Info')}</span></td>
          <td class="font-monospace small fw-bold" style="color: #0284c7;">${e.event_id > 0 ? e.event_id : '-'}</td>
          <td class="text-truncate small" style="max-width: 160px; color: var(--text-color);" title="${escapeHtml(provName)}">${escapeHtml(provName)}</td>
          <td class="font-monospace small" style="color: var(--text-muted);">${e.process_id || '-'}</td>
          <td class="text-truncate" style="max-width: 420px; color: var(--text-color);" title="${escapeHtml(msgText)}">${escapeHtml(msgText)}</td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('tr').forEach(row => {
      row.onclick = () => {
        tbody.querySelectorAll('tr').forEach(r => r.classList.remove('table-active'));
        row.classList.add('table-active');
        const idx = parseInt(row.getAttribute('data-index'), 10);
        selectedEvent = events[idx];

        if (currentMode === 'raw') {
          const rawEl = document.getElementById('slc-raw-text');
          if (rawEl && selectedEvent) rawEl.textContent = JSON.stringify(selectedEvent, null, 2);
        } else {
          showEventDetails(selectedEvent);
        }
      };
    });
  }

  async function loadAuditDigest() {
    const contentEl = document.getElementById('slc-audit-content');
    if (!contentEl) return;
    contentEl.innerHTML = '<div class="text-center text-muted py-4"><div class="spinner-border spinner-border-sm text-info me-2"></div>Формирование сводки аудита и дедупликации...</div>';

    try {
      const hoursSelect = document.getElementById('slc-hours-select');
      const hours = hoursSelect ? hoursSelect.value : '24';
      const res = await fetch(`/api/v1/system_logs/audit?channel=${encodeURIComponent(currentChannel)}&hours=${hours}&limit=300&file_path=${encodeURIComponent(currentFilePath)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const totalEvents = data.total_events || 0;
      const critSum = data.severity_summary?.Critical || 0;
      const errSum = data.severity_summary?.Error || 0;
      const warnSum = data.severity_summary?.Warning || 0;

      let anomaliesHtml = '<div class="text-muted small">Аномалий и резких всплесков частоты ошибок не обнаружено.</div>';
      if (data.anomalies && data.anomalies.length > 0) {
        anomaliesHtml = data.anomalies.map(a => `
          <div class="alert alert-warning py-1 px-2 mb-1.5 small d-flex justify-content-between align-items-center">
            <div><strong class="text-danger">[Аномалия]</strong> ${escapeHtml(a.description || a.message)}</div>
            <span class="badge bg-danger font-monospace">${a.count || ''} событий</span>
          </div>
        `).join('');
      }

      let clustersHtml = '';
      if (data.clusters && data.clusters.length > 0) {
        clustersHtml = data.clusters.slice(0, 15).map((c, i) => `
          <tr>
            <td class="font-monospace" style="color: var(--text-muted);">${i + 1}</td>
            <td><span class="badge ${getSeverityClass(c.level)}">${escapeHtml(c.level || 'Info')}</span></td>
            <td class="text-truncate" style="max-width: 140px; color: var(--text-color);" title="${escapeHtml(c.provider)}">${escapeHtml(c.provider)}</td>
            <td class="font-monospace fw-bold" style="color: #0284c7;">${c.event_id || '-'}</td>
            <td class="small text-truncate" style="max-width: 340px; color: var(--text-color);" title="${escapeHtml(c.pattern)}">${escapeHtml(c.pattern)}</td>
            <td class="font-monospace text-center fw-bold" style="color: var(--text-color);">${c.count}</td>
            <td class="font-monospace small" style="color: var(--text-muted);">${escapeHtml(formatTime(c.first_seen))}</td>
          </tr>
        `).join('');
      } else {
        clustersHtml = '<tr><td colspan="7" class="text-center text-muted py-3">Кластеры не сформированы.</td></tr>';
      }

      contentEl.innerHTML = `
        <div class="row g-2 mb-3">
          <div class="col-sm-3 col-6">
            <div class="p-2 rounded border" style="background: var(--surface-1); border-color: var(--border-color) !important;">
              <div class="small text-muted" style="font-size: 0.72rem;">Всего проанализировано</div>
              <div class="fs-5 fw-bold text-info font-monospace">${totalEvents}</div>
            </div>
          </div>
          <div class="col-sm-3 col-6">
            <div class="p-2 rounded border" style="background: var(--surface-1); border-color: var(--border-color) !important;">
              <div class="small text-muted" style="font-size: 0.72rem;">Критических сбоев</div>
              <div class="fs-5 fw-bold text-danger font-monospace">${critSum}</div>
            </div>
          </div>
          <div class="col-sm-3 col-6">
            <div class="p-2 rounded border" style="background: var(--surface-1); border-color: var(--border-color) !important;">
              <div class="small text-muted" style="font-size: 0.72rem;">Ошибок</div>
              <div class="fs-5 fw-bold text-danger font-monospace">${errSum}</div>
            </div>
          </div>
          <div class="col-sm-3 col-6">
            <div class="p-2 rounded border" style="background: var(--surface-1); border-color: var(--border-color) !important;">
              <div class="small text-muted" style="font-size: 0.72rem;">Предупреждений</div>
              <div class="fs-5 fw-bold text-warning font-monospace">${warnSum}</div>
            </div>
          </div>
        </div>

        <div class="slc-card mb-2 shadow-sm">
          <div class="slc-card-header text-warning fw-bold py-1.5 px-3 small">
            <i class="bi bi-exclamation-triangle me-1"></i>Обнаруженные аномалии и всплески
          </div>
          <div class="p-2">
            ${anomaliesHtml}
          </div>
        </div>

        <div class="slc-card shadow-sm">
          <div class="slc-card-header fw-bold d-flex justify-content-between align-items-center py-1.5 px-3">
            <span><i class="bi bi-collection me-2 text-primary"></i>Топ шаблонов событий (Дедупликация)</span>
            <span class="small text-muted">Топ 15 кластеров</span>
          </div>
          <div class="table-responsive">
            <table class="slc-table mb-0">
              <thead>
                <tr>
                  <th style="width: 40px;">#</th>
                  <th style="width: 80px;">Уровень</th>
                  <th style="width: 140px;">Поставщик</th>
                  <th style="width: 60px;">ID</th>
                  <th>Шаблон сообщения (Masked)</th>
                  <th style="width: 70px;" class="text-center">Кол-во</th>
                  <th style="width: 140px;">Впервые</th>
                </tr>
              </thead>
              <tbody>
                ${clustersHtml}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      contentEl.innerHTML = `<div class="alert alert-danger">Ошибка проведения аудита: ${escapeHtml(err.message)}</div>`;
    }
  }

  async function runRagSearch() {
    const inputEl = document.getElementById('slc-rag-input');
    const resultsEl = document.getElementById('slc-rag-results');
    if (!inputEl || !resultsEl) return;
    const query = inputEl.value.trim();
    if (!query) return;

    resultsEl.innerHTML = '<div class="text-center text-muted py-4"><div class="spinner-border spinner-border-sm text-info me-2"></div>Семантический поиск по RAG-индексу...</div>';

    try {
      const res = await fetch('/api/v1/system_logs/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, channel: currentChannel, top_k: 8 }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const chunks = data.results || [];

      if (chunks.length === 0) {
        resultsEl.innerHTML = '<div class="slc-card p-3 text-center text-muted">По вашему запросу совпадений в RAG-индексе не найдено. Попробуйте нажать «Перестроить RAG-индекс».</div>';
        return;
      }

      resultsEl.innerHTML = chunks.map(c => `
        <div class="slc-card mb-2 p-2.5 shadow-sm">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="badge bg-info text-dark font-monospace">Relevance: ${Math.round((c.score || 0) * 100)}%</span>
            <span class="small font-monospace" style="color: var(--text-muted);">${escapeHtml(c.metadata?.timestamp || '')}</span>
          </div>
          <div class="small font-monospace" style="white-space: pre-wrap; color: var(--text-color);">${escapeHtml(c.text || c.content)}</div>
        </div>
      `).join('');
    } catch (err) {
      resultsEl.innerHTML = `<div class="alert alert-danger">Ошибка поиска RAG: ${escapeHtml(err.message)}</div>`;
    }
  }

  async function rebuildRagIndex() {
    const resultsEl = document.getElementById('slc-rag-results');
    if (!resultsEl) return;
    resultsEl.innerHTML = '<div class="text-center text-info py-4"><div class="spinner-border spinner-border-sm text-info me-2"></div>Перестроение семантического RAG-индекса...</div>';

    try {
      const res = await fetch(`/api/v1/system_logs/rag/build?channel=${encodeURIComponent(currentChannel)}&limit=500&hours=24&file_path=${encodeURIComponent(currentFilePath)}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      resultsEl.innerHTML = `
        <div class="alert alert-success d-flex align-items-center gap-2">
          <i class="bi bi-check-circle-fill fs-5"></i>
          <div>
            <strong>RAG-индекс успешно обновлен!</strong> Добавлено ${data.chunks_added} чанков (Всего в индексе: ${data.total_index_chunks}).
            <div class="small mt-1 text-muted">${escapeHtml(data.executive_summary || '')}</div>
          </div>
        </div>
      `;
    } catch (err) {
      resultsEl.innerHTML = `<div class="alert alert-danger">Ошибка обновления RAG: ${escapeHtml(err.message)}</div>`;
    }
  }

  function showEventDetails(entry) {
    if (!entry) return;
    const modalEl = document.getElementById('slc-event-detail-modal');
    if (!modalEl) return;

    const setElTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val || '';
    };

    setElTxt('slc-modal-time', entry.timestamp);
    const lvlEl = document.getElementById('slc-modal-level');
    if (lvlEl) lvlEl.innerHTML = `<span class="badge ${getSeverityClass(entry.level)}">${escapeHtml(entry.level)}</span>`;
    setElTxt('slc-modal-id', entry.event_id > 0 ? String(entry.event_id) : '-');
    setElTxt('slc-modal-provider', entry.provider || entry.source || '-');
    setElTxt('slc-modal-computer', entry.computer || '-');
    setElTxt('slc-modal-pid', entry.process_id > 0 ? String(entry.process_id) : '-');
    setElTxt('slc-modal-channel', entry.channel || currentChannel);
    setElTxt('slc-modal-message', entry.message);

    const aiExplanation = document.getElementById('slc-modal-ai-explanation');
    if (aiExplanation) {
      aiExplanation.innerHTML = `Нажмите «Анализ контекста», чтобы провести диагностику выбранной записи и сопутствующих событий.`;
    }

    const diagnoseBtn = document.getElementById('btn-slc-modal-diagnose');
    if (diagnoseBtn) {
      diagnoseBtn.onclick = async () => {
        aiExplanation.innerHTML = `<div class="spinner-border spinner-border-sm text-info me-2"></div>Анализ выбранной записи...`;
        try {
          const res = await fetch('/api/v1/system_logs/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              channel: entry.channel || currentChannel,
              timestamp: entry.timestamp,
              event_id: entry.event_id || 0,
              provider: entry.provider || entry.source || '',
              level: entry.level || '',
              message: entry.message || '',
              target_entry: entry,
              query_text: `Диагностика события ${entry.provider || entry.source} (ID ${entry.event_id || 0}): ${entry.message || ''}`,
            }),
          });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const report = await res.json();
          aiExplanation.innerHTML = `
            <div class="mb-2"><strong class="text-info">Сводка:</strong> ${escapeHtml(report.summary)}</div>
            <div class="mb-2"><strong class="text-warning">Причина / Анализ:</strong> ${escapeHtml(report.root_cause)}</div>
            <h6 class="small text-uppercase text-muted fw-bold mb-1">Рекомендации:</h6>
            <ul class="mb-0 ps-3">
              ${(report.recommendations || []).map(r => `<li>${escapeHtml(r)}</li>`).join('')}
            </ul>
          `;
        } catch (e) {
          aiExplanation.innerHTML = `<div class="text-danger">Ошибка диагностики: ${escapeHtml(e.message)}</div>`;
        }
      };
    }

    if (window.bootstrap?.Modal) {
      const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
      bsModal.show();
    }
  }

  async function loadIncidents() {
    const listEl = document.getElementById('slc-incidents-list');
    if (!listEl) return;
    listEl.innerHTML = '<div class="text-center text-muted py-4"><div class="spinner-border spinner-border-sm text-info me-2"></div>Группировка инцидентов...</div>';

    try {
      const res = await fetch('/api/v1/system_logs/incidents?window_seconds=25.0');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const incidents = data.incidents || [];

      if (incidents.length === 0) {
        listEl.innerHTML = '<div class="slc-card p-3 text-center text-muted">Связанных цепочек инцидентов и каскадных сбоев не обнаружено.</div>';
        return;
      }

      listEl.innerHTML = incidents.map(inc => `
        <div class="slc-card mb-2 shadow-sm border-danger">
          <div class="slc-card-header text-danger d-flex justify-content-between align-items-center py-1.5 px-3">
            <strong>${escapeHtml(inc.incident_title || 'Каскадный сбой')}</strong>
            <span class="badge bg-danger">${inc.events_count} событий</span>
          </div>
          <div class="p-2.5">
            <p class="small mb-1">${escapeHtml(inc.summary || '')}</p>
            <div class="small font-monospace text-muted">Временное окно: ${escapeHtml(inc.time_window || '')}</div>
          </div>
        </div>
      `).join('');
    } catch (e) {
      listEl.innerHTML = `<div class="alert alert-danger">Ошибка загрузки инцидентов: ${escapeHtml(e.message)}</div>`;
    }
  }

  async function loadTimeline() {
    const listEl = document.getElementById('slc-timeline-list');
    if (!listEl) return;
    listEl.innerHTML = '<div class="text-center text-muted py-4"><div class="spinner-border spinner-border-sm text-info me-2"></div>Формирование временной шкалы...</div>';

    try {
      const res = await fetch('/api/v1/system_logs/timeline');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const points = data.timeline || [];

      if (points.length === 0) {
        listEl.innerHTML = '<div class="slc-card p-3 text-center text-muted">Данные временной шкалы отсутствуют.</div>';
        return;
      }

      listEl.innerHTML = points.map(p => `
        <div class="d-flex align-items-center gap-2 mb-1">
          <span class="font-monospace small" style="width: 120px; color: var(--text-muted);">${escapeHtml(p.time_slot)}</span>
          <div class="progress flex-grow-1" style="height: 12px; background: var(--surface-2);">
            <div class="progress-bar bg-info" style="width: ${Math.min(100, p.count * 4)}%;"></div>
          </div>
          <span class="font-monospace small fw-bold" style="width: 40px; color: #0284c7;">${p.count}</span>
        </div>
      `).join('');
    } catch (e) {
      listEl.innerHTML = `<div class="alert alert-danger">Ошибка таймлайна: ${escapeHtml(e.message)}</div>`;
    }
  }

  function setMode(mode) {
    currentMode = mode;
    const tableContainer = document.getElementById('slc-table-container');
    const auditContainer = document.getElementById('slc-audit-container');
    const ragContainer = document.getElementById('slc-rag-container');
    const incidentsContainer = document.getElementById('slc-incidents-container');
    const timelineContainer = document.getElementById('slc-timeline-container');
    const rawContainer = document.getElementById('slc-raw-container');
    const activityContainer = document.getElementById('slc-activity-container');
    const filterRow = document.getElementById('slc-filter-row');

    if (tableContainer) tableContainer.classList.add('d-none');
    if (auditContainer) auditContainer.classList.add('d-none');
    if (ragContainer) ragContainer.classList.add('d-none');
    if (incidentsContainer) incidentsContainer.classList.add('d-none');
    if (timelineContainer) timelineContainer.classList.add('d-none');
    if (rawContainer) rawContainer.classList.add('d-none');
    if (activityContainer) activityContainer.classList.add('d-none');
    if (filterRow) filterRow.classList.remove('d-none');

    document.querySelectorAll('#slc-mode-tabs button').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
    });

    if (mode === 'live' || mode === 'errors') {
      if (tableContainer) tableContainer.classList.remove('d-none');
      loadEvents();
    } else if (mode === 'audit') {
      if (auditContainer) auditContainer.classList.remove('d-none');
      loadAuditDigest();
    } else if (mode === 'rag') {
      if (ragContainer) ragContainer.classList.remove('d-none');
      if (filterRow) filterRow.classList.add('d-none');
    } else if (mode === 'incidents') {
      if (incidentsContainer) incidentsContainer.classList.remove('d-none');
      loadIncidents();
    } else if (mode === 'timeline') {
      if (timelineContainer) timelineContainer.classList.remove('d-none');
      loadTimeline();
    } else if (mode === 'raw') {
      if (rawContainer) rawContainer.classList.remove('d-none');
      if (tableContainer) tableContainer.classList.remove('d-none');
    } else if (mode === 'activity') {
      if (activityContainer) activityContainer.classList.remove('d-none');
      if (filterRow) filterRow.classList.add('d-none');
      loadSccActivityLogs();
    }
  }

  /**
   * Экспорт текущих событий.
   */
  function exportEvents(format = 'json') {
    if (!cachedEvents || cachedEvents.length === 0) {
      if (window.toast) window.toast.warning('Экспорт событий', 'Нет загруженных событий для экспорта.');
      return;
    }
    let content = '';
    let mime = 'application/json';
    let ext = 'json';

    if (format === 'json') {
      content = JSON.stringify(cachedEvents, null, 2);
    } else {
      mime = 'text/csv';
      ext = 'csv';
      const headers = ['timestamp', 'level', 'event_id', 'provider', 'process_id', 'message'];
      const rows = cachedEvents.map(e => headers.map(h => `"${String(e[h] || '').replace(/"/g, '""')}"`).join(','));
      content = [headers.join(','), ...rows].join('\n');
    }

    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system_logs_${currentChannel}_${Date.now()}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Инициализация вкладки System Logs & Activity Center.
   */
  function initSystemControlTab() {
    fetchStatus();
    scanChannels();
    loadEvents();

    if (window.registerTabPoller) {
      window.registerTabPoller('tab-system-control_logs', loadEvents, 4000, { immediate: true });
    }

    if (isSCCInitialized) return;
    isSCCInitialized = true;

    // Главная кнопка обновления шапки
    const refreshBtn = document.getElementById('btn-scc-refresh');
    if (refreshBtn) {
      refreshBtn.onclick = () => {
        fetchStatus();
        loadEvents();
      };
    }

    // Кнопка обновления потока логов
    const slcRefreshBtn = document.getElementById('btn-slc-refresh');
    if (slcRefreshBtn) {
      slcRefreshBtn.onclick = () => {
        loadEvents();
      };
    }

    // Кнопка сканирования источников
    const slcScanBtn = document.getElementById('btn-slc-scan');
    if (slcScanBtn) {
      slcScanBtn.onclick = () => {
        scanChannels(true);
      };
    }

    // Кнопка аудита
    const auditBtn = document.getElementById('btn-slc-audit');
    if (auditBtn) {
      auditBtn.onclick = () => {
        setMode('audit');
      };
    }

    // Фильтр каналов в дереве
    const channelFilterInput = document.getElementById('slc-channel-filter-input');
    if (channelFilterInput) {
      channelFilterInput.oninput = (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = cachedChannels.filter(c => {
          const name = (c.channel_name || c.display_name || c.name || '').toLowerCase();
          const desc = (c.description || '').toLowerCase();
          return name.includes(query) || desc.includes(query);
        });
        renderChannelTree(filtered);
      };
    }

    // Переключение режимов работы (Live, Audit, RAG, Incidents, Timeline, Raw, Activity)
    document.querySelectorAll('#slc-mode-tabs button').forEach(btn => {
      btn.onclick = () => {
        const mode = btn.getAttribute('data-mode') || 'live';
        setMode(mode);
      };
    });

    // Фильтры потока
    const searchInput = document.getElementById('slc-search-input');
    if (searchInput) {
      let debounceTimer = null;
      searchInput.oninput = () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(loadEvents, 300);
      };
    }

    const levelSelect = document.getElementById('slc-level-select');
    if (levelSelect) levelSelect.onchange = loadEvents;

    const hoursSelect = document.getElementById('slc-hours-select');
    if (hoursSelect) hoursSelect.onchange = loadEvents;

    const limitSelect = document.getElementById('slc-limit-select');
    if (limitSelect) limitSelect.onchange = loadEvents;

    const eventIdInput = document.getElementById('slc-eventid-input');
    if (eventIdInput) {
      let debounceTimer = null;
      eventIdInput.oninput = () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(loadEvents, 300);
      };
    }

    // Live Auto-refresh switch
    const liveSwitch = document.getElementById('slc-live-switch');
    if (liveSwitch) {
      liveSwitch.onchange = (e) => {
        if (e.target.checked) {
          if (liveIntervalTimer) clearInterval(liveIntervalTimer);
          liveIntervalTimer = setInterval(loadEvents, 3000);
        } else {
          if (liveIntervalTimer) clearInterval(liveIntervalTimer);
          liveIntervalTimer = null;
        }
      };
    }

    // Экспорт событий
    const exportJson = document.getElementById('btn-slc-export-json');
    if (exportJson) {
      exportJson.onclick = (e) => {
        e.preventDefault();
        exportEvents('json');
      };
    }

    const exportCsv = document.getElementById('btn-slc-export-csv');
    if (exportCsv) {
      exportCsv.onclick = (e) => {
        e.preventDefault();
        exportEvents('csv');
      };
    }

    // RAG Search actions
    const ragSearchBtn = document.getElementById('btn-slc-rag-search');
    if (ragSearchBtn) ragSearchBtn.onclick = runRagSearch;

    const ragInput = document.getElementById('slc-rag-input');
    if (ragInput) {
      ragInput.onkeydown = (e) => {
        if (e.key === 'Enter') runRagSearch();
      };
    }

    const ragRebuildBtn = document.getElementById('btn-slc-rag-rebuild');
    if (ragRebuildBtn) ragRebuildBtn.onclick = rebuildRagIndex;

    // AI Ask Action
    const askAiBtn = document.getElementById('btn-slc-ask-ai');
    if (askAiBtn) {
      askAiBtn.onclick = () => {
        const topEvents = cachedEvents.slice(0, 10).map(e => `[${e.level}] ${e.provider}: ${e.message}`).join('\n');
        const prompt = `Проведи диагностику следующих системных логов Windows (Канал: ${currentChannel}):\n${topEvents}`;
        if (window.sendChatMessage) {
          window.sendChatMessage(prompt);
        } else if (window.toast) {
          window.toast.info('ИИ Анализ', 'Запрос направлен в чат-ассистент.');
        }
      };
    }

    // Application activity refresh
    const refreshActivityBtn = document.getElementById('btn-scc-refresh-logs');
    if (refreshActivityBtn) refreshActivityBtn.onclick = loadSccActivityLogs;
  }

  // Экспорт для динамического загрузчика
  window.initSystemControlTab = initSystemControlTab;

  // Автостарт при готовности DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSystemControlTab);
  } else {
    initSystemControlTab();
  }
})();
