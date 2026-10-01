/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/event_logs_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initEventLogsTab } from '/src/api/webgui/event_logs_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/event_logs_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

/**
 * event_logs_tab/main.js — Журналы событий Windows (wevtutil)
 * Updated: 2026-10-01 06:00:00
 */

import { registerTabPoller } from '/html/js/tab-core.js';

let isInitialized = false;
let eventsList = [];

export async function fetchEventLogsSummary() {
  const channelSelect = document.getElementById('el-channel-select');
  const channel = channelSelect ? channelSelect.value : 'System';

  try {
    const res = await fetch(`/api/event-logs/summary?channel=${encodeURIComponent(channel)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderEventLogs(data);
  } catch (err) {
    console.warn('[EventLogs] Ошибка получения событий:', err);
  }
}

function renderEventLogs(data) {
  eventsList = data.events || [];

  const critEl = document.getElementById('el-critical-count');
  const errEl = document.getElementById('el-error-count');
  const warnEl = document.getElementById('el-warn-count');
  const logsCountEl = document.getElementById('el-logs-count');

  if (critEl) critEl.textContent = data.critical_count ?? 0;
  if (errEl) errEl.textContent = data.error_count ?? 0;
  if (warnEl) warnEl.textContent = data.warning_count ?? 0;
  if (logsCountEl) logsCountEl.textContent = data.channels_count || '3';

  applyEventFilters();
}

function applyEventFilters() {
  const tbody = document.getElementById('el-tbody');
  const searchInput = document.getElementById('el-search-input');
  const badge = document.getElementById('el-table-badge');

  if (!tbody) return;

  const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

  const filtered = eventsList.filter(e => {
    if (!query) return true;
    const msgMatch = (e.message || '').toLowerCase().includes(query);
    const provMatch = (e.provider || '').toLowerCase().includes(query);
    const idMatch = String(e.id || e.event_id || '').includes(query);
    return msgMatch || provMatch || idMatch;
  });

  if (badge) badge.textContent = `${filtered.length} из ${eventsList.length} событий`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">События не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.slice(0, 150).map(e => {
    const level = (e.level || 'Information').toLowerCase();
    let badgeClass = 'bg-secondary';
    if (level.includes('crit')) badgeClass = 'bg-danger';
    else if (level.includes('err')) badgeClass = 'bg-danger text-white';
    else if (level.includes('warn')) badgeClass = 'bg-warning text-dark';
    else if (level.includes('info')) badgeClass = 'bg-info text-dark';

    return `
      <tr>
        <td><span class="badge ${badgeClass}">${e.level || 'Info'}</span></td>
        <td class="text-muted small">${e.time_created || e.time || '-'}</td>
        <td class="fw-semibold text-light small">${e.provider || 'Windows'}</td>
        <td class="font-monospace text-warning small">${e.id || e.event_id || '-'}</td>
        <td class="text-light small text-truncate" style="max-width: 450px;">${e.message || '-'}</td>
      </tr>
    `;
  }).join('');
}

export function initEventLogsTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('el-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchEventLogsSummary);

  const channelSelect = document.getElementById('el-channel-select');
  if (channelSelect) channelSelect.addEventListener('change', fetchEventLogsSummary);

  const searchInput = document.getElementById('el-search-input');
  if (searchInput) searchInput.addEventListener('input', applyEventFilters);

  registerTabPoller('tab-event-logs', fetchEventLogsSummary, 10000, { immediate: true });
}

window.initEventLogsTab = initEventLogsTab;
