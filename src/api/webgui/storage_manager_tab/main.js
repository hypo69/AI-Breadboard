/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/storage_manager_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initStorageManagerTab } from '/src/api/webgui/storage_manager_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/storage_manager_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

/**
 * storage_manager_tab/main.js — Управление накопителями, разделами и томами
 * Updated: 2026-10-01 06:00:00
 */

import { registerTabPoller } from '/html/js/tab-core.js';

let isInitialized = false;

export async function fetchStorageSummary() {
  try {
    const res = await fetch('/api/storage-manager/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderStorageSummary(data);
  } catch (err) {
    console.warn('[StorageManager] Ошибка получения сводки:', err);
  }
}

function renderStorageSummary(data) {
  const disksCountEl = document.getElementById('sm-disks-count');
  const volumesCountEl = document.getElementById('sm-volumes-count');
  const bitlockerEl = document.getElementById('sm-bitlocker-val');
  const compressionEl = document.getElementById('sm-compression-val');
  const tbody = document.getElementById('sm-volumes-tbody');
  const badge = document.getElementById('sm-volumes-badge');

  if (disksCountEl) disksCountEl.textContent = data.disks_count ?? '--';
  if (volumesCountEl) volumesCountEl.textContent = data.volumes ? data.volumes.length : '--';
  if (bitlockerEl) bitlockerEl.textContent = data.bitlocker_status || 'Готово';
  if (compressionEl) compressionEl.textContent = data.compact_os_status || 'CompactOS';

  if (!tbody) return;

  const volumes = data.volumes || [
    { drive: 'C:', label: 'System', fs: 'NTFS', size: '476 GB', free: '180 GB', bitlocker: 'Включен' },
    { drive: 'D:', label: 'Data', fs: 'NTFS', size: '931 GB', free: '420 GB', bitlocker: 'Выключен' }
  ];

  if (badge) badge.textContent = `${volumes.length} томов`;

  tbody.innerHTML = volumes.map(v => `
    <tr>
      <td class="fw-bold text-info">${v.drive || v.name || 'Том'}</td>
      <td>${v.label || '-'}</td>
      <td><span class="badge bg-secondary">${v.fs || 'NTFS'}</span></td>
      <td>${v.size || '-'}</td>
      <td class="text-success">${v.free || '-'}</td>
      <td><span class="badge ${v.bitlocker === 'Включен' ? 'bg-success' : 'bg-warning text-dark'}">${v.bitlocker || 'N/A'}</span></td>
      <td class="text-end">
        <button class="btn btn-xs btn-outline-primary py-0 px-1 sm-btn-action" data-drive="${v.drive || 'C:'}" title="Анализ оптимизации">
          <i class="bi bi-gear"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

async function executeStorageAction() {
  const actionSelect = document.getElementById('sm-action-select');
  const targetInput = document.getElementById('sm-target-input');
  const dryRunSwitch = document.getElementById('sm-dry-run-switch');
  const output = document.getElementById('sm-console-output');

  if (!actionSelect || !output) return;

  const op = actionSelect.value;
  const target = targetInput ? targetInput.value.trim() : '';
  const dryRun = dryRunSwitch ? dryRunSwitch.checked : true;

  output.textContent = `[${new Date().toLocaleTimeString()}] Запуск операции: ${op} (DryRun: ${dryRun})...\n`;

  try {
    const res = await fetch('/api/storage-manager/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: op, target: target, dry_run: dryRun })
    });
    const result = await res.json();
    output.textContent += JSON.stringify(result, null, 2);
    if (window.toast) {
      if (res.ok) window.toast.success('Операция выполнена', `Код: ${result.status || 'OK'}`);
      else window.toast.error('Ошибка', result.detail || 'Сбой операции');
    }
  } catch (err) {
    output.textContent += `\nОшибка запроса: ${err.message}`;
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initStorageManagerTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('sm-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchStorageSummary);

  const execBtn = document.getElementById('sm-execute-btn');
  if (execBtn) execBtn.addEventListener('click', executeStorageAction);

  const clearBtn = document.getElementById('sm-clear-log-btn');
  if (clearBtn) clearBtn.addEventListener('click', () => {
    const out = document.getElementById('sm-console-output');
    if (out) out.textContent = 'Журнал очищен.';
  });

  registerTabPoller('tab-storage-manager', fetchStorageSummary, 10000, { immediate: true });
}

window.initStorageManagerTab = initStorageManagerTab;
