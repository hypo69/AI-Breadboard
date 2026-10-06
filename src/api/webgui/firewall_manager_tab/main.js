/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/firewall_manager_tab/main.js?v=20261001_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initFirewallManagerTab } from '/src/api/webgui/firewall_manager_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/firewall_manager_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 11:15:30
 * =============================================================================
 */

/**
 * firewall_manager_tab/main.js — Управление брандмауэром Windows (netsh advfirewall)
 * Updated: 2026-10-04 11:15:30
 */

const registerTabPoller = window.registerTabPoller || function() {};

let isInitialized = false;
let rulesList = [];

export async function fetchFirewallSummary() {
  try {
    const res = await fetch('/api/firewall-manager/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderFirewall(data);
  } catch (err) {
    console.warn('[FirewallManager] Ошибка получения правил:', err);
  }
}

function renderFirewall(data) {
  rulesList = data.rules || [];

  const domEl = document.getElementById('fw-domain-status');
  const privEl = document.getElementById('fw-private-status');
  const pubEl = document.getElementById('fw-public-status');
  const rulesCountEl = document.getElementById('fw-rules-count');

  if (domEl) domEl.textContent = data.domain_profile || 'ON';
  if (privEl) privEl.textContent = data.private_profile || 'ON';
  if (pubEl) pubEl.textContent = data.public_profile || 'ON';
  if (rulesCountEl) rulesCountEl.textContent = rulesList.length;

  applyFirewallFilters();
}

function applyFirewallFilters() {
  const tbody = document.getElementById('fw-tbody');
  const searchInput = document.getElementById('fw-search-input');
  const badge = document.getElementById('fw-table-badge');

  if (!tbody) return;

  const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

  const filtered = rulesList.filter(r => {
    if (!query) return true;
    const nameMatch = (r.name || r.rule_name || '').toLowerCase().includes(query);
    const portMatch = String(r.port || r.local_port || '').includes(query);
    return nameMatch || portMatch;
  });

  if (badge) badge.textContent = `${filtered.length} из ${rulesList.length} правил`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">Правила не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.slice(0, 150).map(r => {
    const name = r.name || r.rule_name || 'Firewall Rule';
    const dir = r.direction || 'In';
    const action = r.action || 'Allow';
    const port = r.local_port || r.port || 'Any';
    const proto = r.protocol || 'TCP';
    const profile = r.profile || 'All';
    const enabled = r.enabled ?? true;

    const isAllow = action.toLowerCase().includes('allow') || action.toLowerCase().includes('разреш');

    return `
      <tr>
        <td class="fw-semibold text-light">${name}</td>
        <td><span class="badge ${dir === 'In' ? 'bg-primary' : 'bg-info'}">${dir}</span></td>
        <td><span class="badge ${isAllow ? 'bg-success' : 'bg-danger'}">${action}</span></td>
        <td class="font-monospace small text-muted">${proto}:${port}</td>
        <td class="small text-muted">${profile}</td>
        <td><span class="badge ${enabled ? 'bg-success' : 'bg-secondary'}">${enabled ? 'Включено' : 'Выключено'}</span></td>
        <td class="text-end">
          <button class="btn btn-xs ${enabled ? 'btn-outline-warning' : 'btn-outline-success'} py-0 px-2 fw-toggle-btn" 
                  data-name="${name}" data-action="${enabled ? 'disable_rule' : 'enable_rule'}">
            <i class="bi ${enabled ? 'bi-pause-fill' : 'bi-play-fill'}"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('.fw-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const rName = btn.dataset.name;
      const rAct = btn.dataset.action;
      executeFirewallAction(rName, rAct);
    });
  });
}

async function executeFirewallAction(ruleName, action) {
  try {
    const res = await fetch('/api/firewall-manager/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_name: ruleName, action: action, dry_run: false })
    });
    const result = await res.json();
    if (res.ok) {
      if (window.toast) window.toast.success('Брандмауэр', `${ruleName}: обновлено`);
      fetchFirewallSummary();
    } else {
      if (window.toast) window.toast.error('Ошибка', result.detail || 'Сбой операции');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initFirewallManagerTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('fw-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchFirewallSummary);

  const resetBtn = document.getElementById('fw-reset-defaults-btn');
  if (resetBtn) resetBtn.addEventListener('click', () => {
    if (confirm('Сбросить правила брандмауэра к значениям по умолчанию?')) {
      executeFirewallAction('all', 'reset_defaults');
    }
  });

  const searchInput = document.getElementById('fw-search-input');
  if (searchInput) searchInput.addEventListener('input', applyFirewallFilters);

  registerTabPoller('tab-firewall-manager', fetchFirewallSummary, 15000, { immediate: true });
}

window.initFirewallManagerTab = initFirewallManagerTab;
