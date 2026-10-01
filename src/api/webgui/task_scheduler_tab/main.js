/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/task_scheduler_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initTaskSchedulerTab } from '/src/api/webgui/task_scheduler_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/task_scheduler_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

/**
 * task_scheduler_tab/main.js — Управление задачами Windows Task Scheduler
 * Updated: 2026-10-01 06:00:00
 */

import { registerTabPoller } from '/html/js/tab-core.js';

let isInitialized = false;
let tasksList = [];

export async function fetchTaskSchedulerSummary() {
  try {
    const res = await fetch('/api/task-scheduler/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderTasks(data);
  } catch (err) {
    console.warn('[TaskScheduler] Ошибка получения списка задач:', err);
  }
}

function renderTasks(data) {
  tasksList = data.tasks || [];

  const totalEl = document.getElementById('ts-total-count');
  const readyEl = document.getElementById('ts-ready-count');
  const runningEl = document.getElementById('ts-running-count');
  const disabledEl = document.getElementById('ts-disabled-count');

  const readyCount = tasksList.filter(t => (t.status || '').toLowerCase().includes('ready') || (t.status || '').toLowerCase().includes('готов')).length;
  const runningCount = tasksList.filter(t => (t.status || '').toLowerCase().includes('running') || (t.status || '').toLowerCase().includes('работ')).length;
  const disabledCount = tasksList.filter(t => (t.status || '').toLowerCase().includes('disabled') || (t.status || '').toLowerCase().includes('отключ')).length;

  if (totalEl) totalEl.textContent = tasksList.length;
  if (readyEl) readyEl.textContent = readyCount;
  if (runningEl) runningEl.textContent = runningCount;
  if (disabledEl) disabledEl.textContent = disabledCount;

  applyTaskFilters();
}

function applyTaskFilters() {
  const tbody = document.getElementById('ts-tbody');
  const searchInput = document.getElementById('ts-search-input');
  const badge = document.getElementById('ts-table-badge');

  if (!tbody) return;

  const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

  const filtered = tasksList.filter(t => {
    if (!query) return true;
    return (t.name || t.task_name || '').toLowerCase().includes(query);
  });

  if (badge) badge.textContent = `${filtered.length} из ${tasksList.length} задач`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Задачи не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.slice(0, 150).map(t => {
    const tName = t.name || t.task_name || 'Task';
    const status = t.status || 'Ready';
    const isReady = status.toLowerCase().includes('ready') || status.toLowerCase().includes('готов');
    const isRunning = status.toLowerCase().includes('running') || status.toLowerCase().includes('работ');
    const isDisabled = status.toLowerCase().includes('disabled') || status.toLowerCase().includes('отключ');

    let badgeClass = 'bg-secondary';
    if (isRunning) badgeClass = 'bg-info text-dark';
    else if (isReady) badgeClass = 'bg-success';
    else if (isDisabled) badgeClass = 'bg-dark border border-secondary text-muted';

    return `
      <tr>
        <td class="fw-semibold text-light font-monospace small">${tName}</td>
        <td class="text-muted small">${t.next_run_time || '-'}</td>
        <td><span class="badge ${badgeClass}">${status}</span></td>
        <td class="small text-muted">${t.schedule_type || 'Custom'}</td>
        <td class="text-end">
          <button class="btn btn-xs btn-outline-primary py-0 px-2 ts-action-btn" data-task="${tName}" data-action="schtasks_run" title="Запустить немедленно">
            <i class="bi bi-play-fill"></i>
          </button>
          <button class="btn btn-xs btn-outline-warning py-0 px-2 ts-action-btn" data-task="${tName}" data-action="${isDisabled ? 'schtasks_enable' : 'schtasks_disable'}" title="${isDisabled ? 'Включить' : 'Отключить'}">
            <i class="bi ${isDisabled ? 'bi-check-circle' : 'bi-pause-fill'}"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('.ts-action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const taskName = btn.dataset.task;
      const act = btn.dataset.action;
      executeTaskAction(taskName, act);
    });
  });
}

async function executeTaskAction(taskName, action) {
  if (window.toast) window.toast.info('Планировщик', `${action}: ${taskName}`);
  try {
    const res = await fetch('/api/task-scheduler/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_name: taskName, action: action, dry_run: false })
    });
    const result = await res.json();
    if (res.ok) {
      if (window.toast) window.toast.success('Успех', `${taskName}: выполнено`);
      fetchTaskSchedulerSummary();
    } else {
      if (window.toast) window.toast.error('Ошибка', result.detail || 'Сбой операции');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initTaskSchedulerTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('ts-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchTaskSchedulerSummary);

  const searchInput = document.getElementById('ts-search-input');
  if (searchInput) searchInput.addEventListener('input', applyTaskFilters);

  registerTabPoller('tab-task-scheduler', fetchTaskSchedulerSummary, 15000, { immediate: true });
}

window.initTaskSchedulerTab = initTaskSchedulerTab;
