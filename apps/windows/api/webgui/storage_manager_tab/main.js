/**
 * =============================================================================
 * Process Name: Windows Storage Manager Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/storage_manager_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initStorageManagerTab } from '/windows/api/webgui/storage_manager_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/storage_manager_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 00:20:00
 * =============================================================================
 */

/**
 * storage_manager_tab/main.js — Управление накопителями, разделами и томами
 * Updated: 2026-10-04 11:15:30
 */

const registerTabPoller = window.registerTabPoller || function() {};

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

const POLL_ID = 'storage_manager';
let timerId = null;

function getFrequency() {
  try {
    const saved = localStorage.getItem(`poll_freq_${POLL_ID}`);
    if (saved) return saved;
  } catch (_) {}
  return 'manual';
}

function setFrequency(freq) {
  try {
    localStorage.setItem(`poll_freq_${POLL_ID}`, freq);
  } catch (_) {}
  applyPoller(freq, false);
}

function stopPolling() {
  if (window.unregisterTabPoller) {
    window.unregisterTabPoller(`tab-storage-manager_${POLL_ID}`);
  }
  if (timerId) {
    clearInterval(timerId);
    timerId = null;
  }
}

function applyPoller(freq, runInitial = false) {
  stopPolling();
  if (freq === 'start' || freq === 'manual') {
    if (runInitial) fetchStorageSummary();
    return;
  }

  const intervalSec = parseInt(freq, 10);
  if (isNaN(intervalSec) || intervalSec <= 0) return;

  const intervalMs = intervalSec * 1000;
  const pollerId = `tab-storage-manager_${POLL_ID}`;

  if (window.registerTabPoller) {
    window.registerTabPoller('tab-storage-manager', fetchStorageSummary, intervalMs, { pollerId, immediate: runInitial });
  } else {
    if (runInitial) fetchStorageSummary();
    timerId = setInterval(() => {
      if (window.isTabActive ? window.isTabActive('tab-storage-manager') : true) {
        fetchStorageSummary();
      }
    }, intervalMs);
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

  const select = document.getElementById('sm-poll-freq');
  if (select) {
    const currentFreq = getFrequency();
    select.value = currentFreq;
    select.onchange = (e) => {
      const newFreq = e.target.value;
      setFrequency(newFreq);
      if (newFreq !== 'manual' && newFreq !== 'start') {
        fetchStorageSummary();
      }
      if (window.showToast) {
        const label = select.options[select.selectedIndex]?.text || newFreq;
        window.showToast(`Частота опроса хранилища: ${label}`, 'info');
      }
    };
    applyPoller(currentFreq, true);
  } else {
    applyPoller(getFrequency(), true);
  }
}

window.initStorageManagerTab = initStorageManagerTab;
