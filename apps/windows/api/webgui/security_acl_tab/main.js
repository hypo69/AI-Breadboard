/**
 * =============================================================================
 * Process Name: Windows Security Acl Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/security_acl_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initSecurityAclTab } from '/windows/api/webgui/security_acl_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/security_acl_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 11:15:30
 * =============================================================================
 */

/**
 * security_acl_tab/main.js — Управление правами доступа и дескрипторами безопасности (icacls, takeown)
 * Updated: 2026-10-04 11:15:30
 */

const registerTabPoller = window.registerTabPoller || function() {};

let isInitialized = false;

export async function inspectPathAcl() {
  const pathInput = document.getElementById('acl-path-input');
  const path = pathInput ? pathInput.value.trim() : 'C:\\Windows\\System32';

  try {
    const res = await fetch(`/api/security-acl/summary?path=${encodeURIComponent(path)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderAclSummary(data);
  } catch (err) {
    console.warn('[SecurityACL] Ошибка получения ACL:', err);
  }
}

function renderAclSummary(data) {
  const ownerEl = document.getElementById('acl-owner-val');
  const inheritEl = document.getElementById('acl-inherit-val');
  const aceCountEl = document.getElementById('acl-ace-count');
  const tbody = document.getElementById('acl-tbody');
  const badge = document.getElementById('acl-badge');

  if (ownerEl) ownerEl.textContent = data.owner || 'NT AUTHORITY\\SYSTEM';
  if (inheritEl) inheritEl.textContent = data.inheritance_enabled ? 'Включено' : 'Отключено';

  const aces = data.aces || [
    { principal: 'NT AUTHORITY\\SYSTEM', permissions: 'Full Control', type: 'Allow', inheritance: 'Inherited' },
    { principal: 'BUILTIN\\Administrators', permissions: 'Full Control', type: 'Allow', inheritance: 'Inherited' },
    { principal: 'BUILTIN\\Users', permissions: 'Read & Execute', type: 'Allow', inheritance: 'Inherited' }
  ];

  if (aceCountEl) aceCountEl.textContent = aces.length;
  if (badge) badge.textContent = `${aces.length} записей`;

  if (!tbody) return;

  tbody.innerHTML = aces.map(a => `
    <tr>
      <td class="fw-semibold text-light">${a.principal || '-'}</td>
      <td class="text-info font-monospace small">${a.permissions || 'Read'}</td>
      <td><span class="badge ${a.type === 'Allow' ? 'bg-success' : 'bg-danger'}">${a.type || 'Allow'}</span></td>
      <td class="small text-muted">${a.inheritance || 'Direct'}</td>
    </tr>
  `).join('');
}

async function executeAclAction(customAction = null) {
  const pathInput = document.getElementById('acl-path-input');
  const userInput = document.getElementById('acl-user-input');
  const permSelect = document.getElementById('acl-perm-select');
  const dryRunSwitch = document.getElementById('acl-dry-run-switch');
  const output = document.getElementById('acl-console-output');

  const path = pathInput ? pathInput.value.trim() : 'C:\\Windows\\System32';
  const user = userInput ? userInput.value.trim() : 'Administrators';
  const perm = permSelect ? permSelect.value : 'F';
  const action = customAction || 'icacls_grant';
  const dryRun = dryRunSwitch ? dryRunSwitch.checked : true;

  if (output) output.textContent = `[${new Date().toLocaleTimeString()}] Выполнение ${action} для "${path}"...\n`;

  try {
    const res = await fetch('/api/security-acl/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: path, user: user, permission: perm, action: action, dry_run: dryRun })
    });
    const result = await res.json();
    if (output) output.textContent += JSON.stringify(result, null, 2);
    if (window.toast) {
      if (res.ok) window.toast.success('Права обновлены', `Статус: ${result.status || 'OK'}`);
      else window.toast.error('Ошибка', result.detail || 'Сбой выполнения icacls');
    }
  } catch (err) {
    if (output) output.textContent += `\nОшибка запроса: ${err.message}`;
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initSecurityAclTab() {
  if (isInitialized) return;
  isInitialized = true;

  const inspectBtn = document.getElementById('acl-inspect-btn');
  if (inspectBtn) inspectBtn.addEventListener('click', inspectPathAcl);

  const takeownBtn = document.getElementById('acl-takeown-btn');
  if (takeownBtn) takeownBtn.addEventListener('click', () => executeAclAction('takeown'));

  const grantBtn = document.getElementById('acl-grant-btn');
  if (grantBtn) grantBtn.addEventListener('click', () => executeAclAction('icacls_grant'));

  const clearBtn = document.getElementById('acl-clear-log-btn');
  if (clearBtn) clearBtn.addEventListener('click', () => {
    const out = document.getElementById('acl-console-output');
    if (out) out.textContent = 'Консоль очищена.';
  });

  registerTabPoller('tab-security-acl', inspectPathAcl, 20000, { immediate: true });
}

window.initSecurityAclTab = initSecurityAclTab;
