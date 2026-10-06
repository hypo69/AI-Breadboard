/**
 * =============================================================================
 * Process Name: Windows Servicing Integrity Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/servicing_integrity_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initServicingIntegrityTab } from '/windows/api/webgui/servicing_integrity_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/servicing_integrity_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 11:15:30
 * =============================================================================
 */

/**
 * servicing_integrity_tab/main.js — Обслуживание образов DISM и целостность SFC
 * Updated: 2026-10-04 11:15:30
 */

const registerTabPoller = window.registerTabPoller || function() {};

let isInitialized = false;

export async function fetchServicingSummary() {
  try {
    const res = await fetch('/api/servicing-integrity/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderServicingSummary(data);
  } catch (err) {
    console.warn('[ServicingIntegrity] Ошибка получения сводки:', err);
  }
}

function renderServicingSummary(data) {
  const winsxsSizeEl = document.getElementById('si-winsxs-size');
  const cleanupRecommendedEl = document.getElementById('si-cleanup-recommended');
  const sfcStatusEl = document.getElementById('si-sfc-status');
  const dismStatusEl = document.getElementById('si-dism-status');

  if (winsxsSizeEl) winsxsSizeEl.textContent = data.winsxs_size || '8.4 GB';
  if (cleanupRecommendedEl) cleanupRecommendedEl.textContent = data.cleanup_recommended ? 'Да' : 'Нет';
  if (sfcStatusEl) sfcStatusEl.textContent = data.sfc_status || 'OK';
  if (dismStatusEl) dismStatusEl.textContent = data.dism_health || 'Healthy';
}

async function executeServicingAction(customAction = null) {
  const actionSelect = document.getElementById('si-action-select');
  const dryRunSwitch = document.getElementById('si-dry-run-switch');
  const output = document.getElementById('si-console-output');

  const op = customAction || (actionSelect ? actionSelect.value : 'dism_check_health');
  const dryRun = dryRunSwitch ? dryRunSwitch.checked : true;

  if (output) output.textContent = `[${new Date().toLocaleTimeString()}] Запуск операции обслуживания: ${op} (DryRun: ${dryRun})...\nПожалуйста, подождите...\n`;

  try {
    const res = await fetch('/api/servicing-integrity/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: op, dry_run: dryRun })
    });
    const result = await res.json();
    if (output) output.textContent += JSON.stringify(result, null, 2);
    if (window.toast) {
      if (res.ok) window.toast.success('Операция завершена', `Статус: ${result.status || 'OK'}`);
      else window.toast.error('Ошибка', result.detail || 'Сбой обслуживания');
    }
  } catch (err) {
    if (output) output.textContent += `\nОшибка запроса: ${err.message}`;
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initServicingIntegrityTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('si-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchServicingSummary);

  const dismCheckBtn = document.getElementById('si-dism-check-btn');
  if (dismCheckBtn) dismCheckBtn.addEventListener('click', () => executeServicingAction('dism_check_health'));

  const sfcScanBtn = document.getElementById('si-sfc-scan-btn');
  if (sfcScanBtn) sfcScanBtn.addEventListener('click', () => executeServicingAction('sfc_scannow'));

  const winsxsCleanBtn = document.getElementById('si-winsxs-clean-btn');
  if (winsxsCleanBtn) winsxsCleanBtn.addEventListener('click', () => executeServicingAction('dism_start_component_cleanup'));

  const execBtn = document.getElementById('si-execute-btn');
  if (execBtn) execBtn.addEventListener('click', () => executeServicingAction());

  const clearBtn = document.getElementById('si-clear-log-btn');
  if (clearBtn) clearBtn.addEventListener('click', () => {
    const out = document.getElementById('si-console-output');
    if (out) out.textContent = 'Журнал очищен.';
  });

  registerTabPoller('tab-servicing-integrity', fetchServicingSummary, 20000, { immediate: true });
}

window.initServicingIntegrityTab = initServicingIntegrityTab;
