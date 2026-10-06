/**
 * =============================================================================
 * Process Name: Windows Boot Recovery Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/boot_recovery_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initBootRecoveryTab } from '/windows/api/webgui/boot_recovery_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/boot_recovery_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 11:15:30
 * =============================================================================
 */

/**
 * boot_recovery_tab/main.js — Управление BCD, загрузчиком и средой WinRE
 * Updated: 2026-10-04 11:15:30
 */

const registerTabPoller = window.registerTabPoller || function() {};

let isInitialized = false;

export async function fetchBootRecoverySummary() {
  try {
    const res = await fetch('/api/boot-recovery/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderBootSummary(data);
  } catch (err) {
    console.warn('[BootRecovery] Ошибка получения сводки:', err);
  }
}

function renderBootSummary(data) {
  const winreStatusEl = document.getElementById('br-winre-status');
  const bcdTimeoutEl = document.getElementById('br-bcd-timeout');
  const currentLoaderEl = document.getElementById('br-current-loader');
  const tbody = document.getElementById('br-entries-tbody');
  const badge = document.getElementById('br-entries-badge');

  if (winreStatusEl) winreStatusEl.textContent = data.winre_enabled ? 'Включена' : 'Отключена';
  if (bcdTimeoutEl) bcdTimeoutEl.textContent = `${data.timeout ?? 30} сек`;
  if (currentLoaderEl) currentLoaderEl.textContent = data.current_guid || '{current}';

  if (!tbody) return;

  const entries = data.bcd_entries || [
    { guid: '{bootmgr}', description: 'Windows Boot Manager', device: 'partition=\\Device\\HarddiskVolume1', path: '\\EFI\\Microsoft\\Boot\\bootmgfw.efi' },
    { guid: '{current}', description: 'Windows 11 Pro', device: 'partition=C:', path: '\\Windows\\system32\\winload.efi' }
  ];

  if (badge) badge.textContent = `${entries.length} записей`;

  tbody.innerHTML = entries.map(e => `
    <tr>
      <td class="fw-bold text-info font-monospace">${e.guid}</td>
      <td>${e.description || '-'}</td>
      <td class="small text-muted">${e.device || '-'}</td>
      <td class="small font-monospace">${e.path || '-'}</td>
      <td class="text-end">
        <button class="btn btn-xs btn-outline-info py-0 px-1" title="Инфо о записи">
          <i class="bi bi-info-circle"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

async function executeBootAction(customAction = null) {
  const actionSelect = document.getElementById('br-action-select');
  const dryRunSwitch = document.getElementById('br-dry-run-switch');
  const output = document.getElementById('br-console-output');

  const op = customAction || (actionSelect ? actionSelect.value : 'reagentc_info');
  const dryRun = dryRunSwitch ? dryRunSwitch.checked : true;

  if (output) output.textContent = `[${new Date().toLocaleTimeString()}] Выполнение команды: ${op} (DryRun: ${dryRun})...\n`;

  try {
    const res = await fetch('/api/boot-recovery/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: op, dry_run: dryRun })
    });
    const result = await res.json();
    if (output) output.textContent += JSON.stringify(result, null, 2);
    if (window.toast) {
      if (res.ok) window.toast.success('Команда выполнена', `Статус: ${result.status || 'OK'}`);
      else window.toast.error('Ошибка', result.detail || 'Сбой выполнения');
    }
  } catch (err) {
    if (output) output.textContent += `\nОшибка запроса: ${err.message}`;
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initBootRecoveryTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('br-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchBootRecoverySummary);

  const winreEnableBtn = document.getElementById('br-winre-enable-btn');
  if (winreEnableBtn) winreEnableBtn.addEventListener('click', () => executeBootAction('reagentc_enable'));

  const winreInfoBtn = document.getElementById('br-winre-info-btn');
  if (winreInfoBtn) winreInfoBtn.addEventListener('click', () => executeBootAction('reagentc_info'));

  const execBtn = document.getElementById('br-execute-btn');
  if (execBtn) execBtn.addEventListener('click', () => executeBootAction());

  const clearBtn = document.getElementById('br-clear-log-btn');
  if (clearBtn) clearBtn.addEventListener('click', () => {
    const out = document.getElementById('br-console-output');
    if (out) out.textContent = 'Консоль очищена.';
  });

  registerTabPoller('tab-boot-recovery', fetchBootRecoverySummary, 15000, { immediate: true });
}

window.initBootRecoveryTab = initBootRecoveryTab;
