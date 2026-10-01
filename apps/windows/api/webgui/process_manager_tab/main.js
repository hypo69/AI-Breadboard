/**
 * =============================================================================
 * Process Name: Windows Process Manager Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/process_manager_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initProcessManagerTab } from '/windows/api/webgui/process_manager_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/process_manager_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

/**
 * process_manager_tab/main.js — Управление процессами Windows (tasklist, taskkill)
 * Updated: 2026-10-01 06:00:00
 */

import { registerTabPoller } from '/html/js/tab-core.js';

let isInitialized = false;
let processList = [];

export async function fetchProcessManagerSummary() {
  try {
    const res = await fetch('/api/process-manager/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderProcesses(data);
  } catch (err) {
    console.warn('[ProcessManager] Ошибка получения процессов:', err);
  }
}

function renderProcesses(data) {
  processList = data.processes || [];

  const totalEl = document.getElementById('pm-total-count');
  const threadsEl = document.getElementById('pm-threads-count');
  const ramEl = document.getElementById('pm-ram-usage');
  const handlesEl = document.getElementById('pm-handles-count');

  if (totalEl) totalEl.textContent = processList.length;
  if (threadsEl) threadsEl.textContent = data.total_threads || '--';
  if (ramEl) ramEl.textContent = data.total_memory || '--';
  if (handlesEl) handlesEl.textContent = data.total_handles || '--';

  applyProcessFilters();
}

function applyProcessFilters() {
  const tbody = document.getElementById('pm-tbody');
  const searchInput = document.getElementById('pm-search-input');
  const badge = document.getElementById('pm-table-badge');

  if (!tbody) return;

  const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

  const filtered = processList.filter(p => {
    if (!query) return true;
    const nameMatch = (p.name || p.image_name || '').toLowerCase().includes(query);
    const pidMatch = String(p.pid || '').includes(query);
    return nameMatch || pidMatch;
  });

  if (badge) badge.textContent = `${filtered.length} из ${processList.length} процессов`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Процессы не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.slice(0, 150).map(p => {
    const pid = p.pid || '-';
    const name = p.name || p.image_name || 'process.exe';
    const mem = p.mem_usage || p.memory || '-';
    const session = p.session_name || 'Console';
    const status = p.status || 'Running';

    return `
      <tr>
        <td class="font-monospace text-warning small">${pid}</td>
        <td class="fw-semibold text-light">${name}</td>
        <td class="text-muted small">${session}</td>
        <td class="text-info font-monospace small">${mem}</td>
        <td><span class="badge bg-success">${status}</span></td>
        <td class="text-end">
          <button class="btn btn-xs btn-outline-danger py-0 px-2 pm-kill-btn" data-pid="${pid}" data-name="${name}" title="Завершить процесс (taskkill)">
            <i class="bi bi-x-circle"></i> Завершить
          </button>
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('.pm-kill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const pid = btn.dataset.pid;
      const name = btn.dataset.name;
      killProcess(pid, name);
    });
  });
}

async function killProcess(pid, name) {
  if (!confirm(`Вы действительно хотите завершить процесс ${name} (PID: ${pid})?`)) return;

  try {
    const res = await fetch('/api/process-manager/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pid: parseInt(pid, 10), action: 'taskkill', force: true, dry_run: false })
    });
    const result = await res.json();
    if (res.ok) {
      if (window.toast) window.toast.success('Процесс завершен', `${name} (PID: ${pid})`);
      fetchProcessManagerSummary();
    } else {
      if (window.toast) window.toast.error('Ошибка завершения', result.detail || 'Отказано в доступе');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initProcessManagerTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('pm-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchProcessManagerSummary);

  const searchInput = document.getElementById('pm-search-input');
  if (searchInput) searchInput.addEventListener('input', applyProcessFilters);

  registerTabPoller('tab-process-manager', fetchProcessManagerSummary, 5000, { immediate: true });
}

window.initProcessManagerTab = initProcessManagerTab;
