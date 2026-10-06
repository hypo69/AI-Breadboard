/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/services_manager_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initServicesManagerTab } from '/src/api/webgui/services_manager_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/services_manager_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 11:15:30
 * =============================================================================
 */

/**
 * services_manager_tab/main.js — Управление системными службами Windows
 * Updated: 2026-10-04 11:15:30
 */

const registerTabPoller = window.registerTabPoller || function() {};

let isInitialized = false;
let servicesList = [];
let currentFilter = 'all';

export async function fetchServicesSummary() {
  try {
    const res = await fetch('/api/services-manager/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderServices(data);
  } catch (err) {
    console.warn('[ServicesManager] Ошибка получения списка служб:', err);
  }
}

function renderServices(data) {
  servicesList = data.services || [];

  const totalEl = document.getElementById('svc-total-count');
  const runningEl = document.getElementById('svc-running-count');
  const stoppedEl = document.getElementById('svc-stopped-count');
  const autoEl = document.getElementById('svc-auto-count');

  const runningCount = servicesList.filter(s => (s.state || '').toLowerCase().includes('running') || s.state === '4').length;
  const stoppedCount = servicesList.filter(s => (s.state || '').toLowerCase().includes('stopped') || s.state === '1').length;
  const autoCount = servicesList.filter(s => (s.start_type || '').toLowerCase().includes('auto')).length;

  if (totalEl) totalEl.textContent = servicesList.length;
  if (runningEl) runningEl.textContent = runningCount;
  if (stoppedEl) stoppedEl.textContent = stoppedCount;
  if (autoEl) autoEl.textContent = autoCount;

  applyServiceFilters();
}

function applyServiceFilters() {
  const tbody = document.getElementById('svc-tbody');
  const searchInput = document.getElementById('svc-search-input');
  const badge = document.getElementById('svc-table-badge');

  if (!tbody) return;

  const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

  const filtered = servicesList.filter(s => {
    const isRunning = (s.state || '').toLowerCase().includes('running') || s.state === '4';
    if (currentFilter === 'running' && !isRunning) return false;
    if (currentFilter === 'stopped' && isRunning) return false;

    if (query) {
      const matchName = (s.name || '').toLowerCase().includes(query);
      const matchDisp = (s.display_name || '').toLowerCase().includes(query);
      return matchName || matchDisp;
    }
    return true;
  });

  if (badge) badge.textContent = `${filtered.length} из ${servicesList.length} служб`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Службы не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.slice(0, 150).map(s => {
    const isRunning = (s.state || '').toLowerCase().includes('running') || s.state === '4';
    return `
      <tr>
        <td class="fw-bold text-info font-monospace">${s.name}</td>
        <td>${s.display_name || s.name}</td>
        <td>
          <span class="badge ${isRunning ? 'bg-success' : 'bg-secondary'}">
            ${isRunning ? 'Running' : 'Stopped'}
          </span>
        </td>
        <td class="small text-muted">${s.start_type || 'Manual'}</td>
        <td class="font-monospace small text-muted">${s.pid || '-'}</td>
        <td class="text-end">
          <button class="btn btn-xs ${isRunning ? 'btn-outline-danger' : 'btn-outline-success'} py-0 px-2 svc-action-btn" 
                  data-service="${s.name}" data-action="${isRunning ? 'sc_stop' : 'sc_start'}">
            <i class="bi ${isRunning ? 'bi-stop-fill' : 'bi-play-fill'}"></i> ${isRunning ? 'Стоп' : 'Старт'}
          </button>
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('.svc-action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const sName = btn.dataset.service;
      const sAct = btn.dataset.action;
      executeServiceCmd(sName, sAct);
    });
  });
}

async function executeServiceCmd(serviceName, action) {
  if (window.toast) window.toast.info('Команда отправлена', `${action}: ${serviceName}`);
  try {
    const res = await fetch('/api/services-manager/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ service_name: serviceName, action: action, dry_run: false })
    });
    const result = await res.json();
    if (res.ok) {
      if (window.toast) window.toast.success('Успех', `${serviceName}: команда выполнена`);
      fetchServicesSummary();
    } else {
      if (window.toast) window.toast.error('Ошибка', result.detail || 'Сбой операции');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initServicesManagerTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('svc-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchServicesSummary);

  const searchInput = document.getElementById('svc-search-input');
  if (searchInput) searchInput.addEventListener('input', applyServiceFilters);

  const filterAll = document.getElementById('svc-filter-all');
  const filterRunning = document.getElementById('svc-filter-running');
  const filterStopped = document.getElementById('svc-filter-stopped');

  [filterAll, filterRunning, filterStopped].forEach(btn => {
    if (!btn) return;
    btn.addEventListener('click', () => {
      [filterAll, filterRunning, filterStopped].forEach(b => b?.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.id.replace('svc-filter-', '');
      applyServiceFilters();
    });
  });

  registerTabPoller('tab-services-manager', fetchServicesSummary, 10000, { immediate: true });
}

window.initServicesManagerTab = initServicesManagerTab;
