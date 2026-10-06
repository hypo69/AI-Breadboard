/**
 * =============================================================================
 * Process Name: Windows Task Scheduler Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля Планировщика задач Windows.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/task_scheduler_tab/main.js?v=20261006_v2" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initTaskSchedulerTab } from '/windows/api/webgui/task_scheduler_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/task_scheduler_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 12:35:00
 * =============================================================================
 */

/**
 * task_scheduler_tab/main.js — Управление задачами Windows Task Scheduler
 * Updated: 2026-10-06 12:35:00
 */

const registerTabPoller = window.registerTabPoller || function() {};

let isInitialized = false;
let tasksList = [];

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export async function fetchTaskSchedulerSummary() {
  const refreshBtn = document.getElementById('ts-refresh-btn');
  if (refreshBtn) {
    const icon = refreshBtn.querySelector('i');
    if (icon) icon.classList.add('spin-animation');
  }

  try {
    const res = await fetch('/api/task-scheduler/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderTasks(data);
  } catch (err) {
    console.warn('[TaskScheduler] Ошибка получения списка задач:', err);
    const tbody = document.getElementById('ts-tbody');
    if (tbody && tasksList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">Ошибка загрузки задач: ${escapeHtml(err.message)}</td></tr>`;
    }
  } finally {
    if (refreshBtn) {
      const icon = refreshBtn.querySelector('i');
      if (icon) icon.classList.remove('spin-animation');
    }
  }
}

function renderTasks(data) {
  tasksList = data.tasks || [];

  const totalEl = document.getElementById('ts-total-count');
  const readyEl = document.getElementById('ts-ready-count');
  const runningEl = document.getElementById('ts-running-count');
  const disabledEl = document.getElementById('ts-disabled-count');

  const readyCount = data.ready_tasks !== undefined
    ? data.ready_tasks
    : tasksList.filter(t => {
        const st = (t.state || t.status || '').toLowerCase();
        return st.includes('ready') || st.includes('готов');
      }).length;

  const runningCount = data.running_tasks !== undefined
    ? data.running_tasks
    : tasksList.filter(t => {
        const st = (t.state || t.status || '').toLowerCase();
        return st.includes('running') || st.includes('работ') || st.includes('выполн');
      }).length;

  const disabledCount = data.disabled_tasks !== undefined
    ? data.disabled_tasks
    : tasksList.filter(t => {
        const st = (t.state || t.status || '').toLowerCase();
        return st.includes('disabled') || st.includes('отключ');
      }).length;

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
    const name = (t.name || t.task_name || '').toLowerCase();
    const path = (t.task_path || '').toLowerCase();
    const act = (t.action || '').toLowerCase();
    return name.includes(query) || path.includes(query) || act.includes(query);
  });

  if (badge) badge.textContent = `${filtered.length} из ${tasksList.length} задач`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Задачи не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.slice(0, 300).map(t => {
    const tName = t.name || t.task_name || (t.task_path ? t.task_path.split('\\').pop() : 'Task');
    const tPath = t.task_path || tName;
    const status = t.state || t.status || 'Ready';
    const statusLower = status.toLowerCase();
    const isReady = statusLower.includes('ready') || statusLower.includes('готов');
    const isRunning = statusLower.includes('running') || statusLower.includes('работ') || statusLower.includes('выполн');
    const isDisabled = statusLower.includes('disabled') || statusLower.includes('отключ');

    let badgeClass = 'bg-secondary';
    if (isRunning) badgeClass = 'bg-info text-dark';
    else if (isReady) badgeClass = 'bg-success';
    else if (isDisabled) badgeClass = 'bg-danger-subtle text-danger border border-danger fw-bold';

    const scheduleType = t.schedule_type || 'Custom';
    const nextRun = t.next_run_time || '-';

    return `
      <tr>
        <td class="fw-semibold text-light font-monospace small" title="${escapeHtml(tPath)}">
          <div>${escapeHtml(tName)}</div>
          ${tPath !== tName ? `<div class="text-muted" style="font-size: 0.75rem;">${escapeHtml(tPath)}</div>` : ''}
        </td>
        <td class="text-muted small">${escapeHtml(nextRun)}</td>
        <td><span class="badge ${badgeClass}">${escapeHtml(status)}</span></td>
        <td class="small text-muted">${escapeHtml(scheduleType)}</td>
        <td class="text-end">
          <button class="btn btn-xs btn-outline-primary py-0 px-2 ts-action-btn" data-task="${escapeHtml(tPath)}" data-action="schtasks_run" title="Запустить немедленно">
            <i class="bi bi-play-fill"></i>
          </button>
          <button class="btn btn-xs ${isDisabled ? 'btn-outline-success' : 'btn-outline-warning'} py-0 px-2 ts-action-btn" data-task="${escapeHtml(tPath)}" data-action="${isDisabled ? 'schtasks_enable' : 'schtasks_disable'}" title="${isDisabled ? 'Включить' : 'Отключить'}">
            <i class="bi ${isDisabled ? 'bi-check-circle' : 'bi-pause-fill'}"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('.ts-action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const taskTarget = btn.dataset.task;
      const act = btn.dataset.action;
      executeTaskAction(taskTarget, act);
    });
  });
}

async function executeTaskAction(taskTarget, action) {
  if (window.toast) window.toast.info('Планировщик', `${action}: ${taskTarget}`);
  try {
    const res = await fetch('/api/task-scheduler/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_path: taskTarget,
        task_name: taskTarget,
        action: action,
        dry_run: false,
        confirmed_by_user: true
      })
    });
    const result = await res.json();
    if (res.ok && (result.status === 'SUCCESS' || result.status === 'DRY_RUN_SUCCESS')) {
      if (window.toast) window.toast.success('Успех', `${taskTarget}: ${result.message || 'выполнено'}`);
      fetchTaskSchedulerSummary();
    } else {
      if (window.toast) window.toast.error('Ошибка', result.message || result.detail || 'Сбой операции');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initTaskSchedulerTab() {
  if (!isInitialized) {
    isInitialized = true;

    const refreshBtn = document.getElementById('ts-refresh-btn');
    if (refreshBtn) refreshBtn.addEventListener('click', fetchTaskSchedulerSummary);

    const searchInput = document.getElementById('ts-search-input');
    if (searchInput) searchInput.addEventListener('input', applyTaskFilters);

    registerTabPoller('tab-task-scheduler', fetchTaskSchedulerSummary, 15000, { immediate: true });
  }

  fetchTaskSchedulerSummary();
}

window.initTaskSchedulerTab = initTaskSchedulerTab;
