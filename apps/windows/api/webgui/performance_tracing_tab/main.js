/**
 * =============================================================================
 * Process Name: Windows Performance Tracing Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/performance_tracing_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initPerformanceTracingTab } from '/windows/api/webgui/performance_tracing_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/performance_tracing_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 11:15:30
 * =============================================================================
 */

/**
 * performance_tracing_tab/main.js — ETW трассировка и счетчики производительности (logman, typeperf)
 * Updated: 2026-10-04 11:15:30
 */

const registerTabPoller = window.registerTabPoller || function() {};

let isInitialized = false;
let sessionsList = [];

export async function fetchPerformanceSummary() {
  try {
    const res = await fetch('/api/performance-tracing/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderPerformance(data);
  } catch (err) {
    console.warn('[PerformanceTracing] Ошибка получения сводки:', err);
  }
}

function renderPerformance(data) {
  sessionsList = data.sessions || [
    { name: 'EventLog-Application', type: 'Trace', buffer_size: '64 KB', status: 'Running' },
    { name: 'EventLog-System', type: 'Trace', buffer_size: '64 KB', status: 'Running' },
    { name: 'Diagtrack-Listener', type: 'Trace', buffer_size: '128 KB', status: 'Running' }
  ];

  const sessionsCountEl = document.getElementById('pt-sessions-count');
  const countersCountEl = document.getElementById('pt-counters-count');
  const collectorsCountEl = document.getElementById('pt-collectors-count');
  const tbody = document.getElementById('pt-tbody');
  const badge = document.getElementById('pt-badge');

  if (sessionsCountEl) sessionsCountEl.textContent = sessionsList.length;
  if (countersCountEl) countersCountEl.textContent = data.counters_count || '120+';
  if (collectorsCountEl) collectorsCountEl.textContent = data.collectors_count || '4';
  if (badge) badge.textContent = `${sessionsList.length} сессий`;

  if (!tbody) return;

  tbody.innerHTML = sessionsList.map(s => `
    <tr>
      <td class="fw-semibold text-light">${s.name}</td>
      <td><span class="badge bg-secondary">${s.type || 'Trace'}</span></td>
      <td class="font-monospace small text-muted">${s.buffer_size || '64 KB'}</td>
      <td><span class="badge bg-success">${s.status || 'Running'}</span></td>
      <td class="text-end">
        <button class="btn btn-xs btn-outline-info py-0 px-2" title="Свойства сессии">
          <i class="bi bi-info-circle"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

async function executeTraceAction(customAction = null) {
  const actionSelect = document.getElementById('pt-action-select');
  const dryRunSwitch = document.getElementById('pt-dry-run-switch');
  const output = document.getElementById('pt-console-output');

  const action = customAction || (actionSelect ? actionSelect.value : 'typeperf_cpu_sample');
  const dryRun = dryRunSwitch ? dryRunSwitch.checked : true;

  if (output) output.textContent = `[${new Date().toLocaleTimeString()}] Запуск трассировки: ${action}...\n`;

  try {
    const res = await fetch('/api/performance-tracing/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: action, dry_run: dryRun })
    });
    const result = await res.json();
    if (output) output.textContent += JSON.stringify(result, null, 2);
    if (window.toast) {
      if (res.ok) window.toast.success('Трассировка', `Замер выполнен: ${result.status || 'OK'}`);
      else window.toast.error('Ошибка', result.detail || 'Сбой замера');
    }
  } catch (err) {
    if (output) output.textContent += `\nОшибка запроса: ${err.message}`;
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initPerformanceTracingTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('pt-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchPerformanceSummary);

  const sampleBtn = document.getElementById('pt-quick-sample-btn');
  if (sampleBtn) sampleBtn.addEventListener('click', () => executeTraceAction('typeperf_cpu_sample'));

  const execBtn = document.getElementById('pt-execute-btn');
  if (execBtn) execBtn.addEventListener('click', () => executeTraceAction());

  const clearBtn = document.getElementById('pt-clear-log-btn');
  if (clearBtn) clearBtn.addEventListener('click', () => {
    const out = document.getElementById('pt-console-output');
    if (out) out.textContent = 'Консоль очищена.';
  });

  registerTabPoller('tab-performance-tracing', fetchPerformanceSummary, 15000, { immediate: true });
}

window.initPerformanceTracingTab = initPerformanceTracingTab;
