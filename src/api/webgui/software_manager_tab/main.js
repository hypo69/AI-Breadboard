/**
 * =============================================================================
 * Process Name: Windows Software Manager Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/software_manager_tab/main.js?v=20261004_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initSoftwareManagerTab } from '/src/api/webgui/software_manager_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/software_manager_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-04 12:40:00
 * =============================================================================
 */

/**
 * software_manager_tab/main.js — Управление пакетами и программами (winget, msiexec)
 * Updated: 2026-10-04 12:40:00
 */

const registerTabPoller = window.registerTabPoller || function() {};

let isInitialized = false;
let packagesList = [];

export async function fetchSoftwareSummary() {
  try {
    const res = await fetch('/api/software-manager/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderSoftware(data);
  } catch (err) {
    console.warn('[SoftwareManager] Ошибка получения списка ПО:', err);
    const tbody = document.getElementById('sw-tbody');
    if (tbody && packagesList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">Ошибка загрузки данных: ${err.message}</td></tr>`;
    }
  }
}

function renderSoftware(data) {
  packagesList = data.packages || [];

  const installedEl = document.getElementById('sw-installed-count');
  const upgradesEl = document.getElementById('sw-upgrades-count');
  const sourcesEl = document.getElementById('sw-sources-count');

  if (installedEl) installedEl.textContent = data.total_packages ?? packagesList.length;
  if (upgradesEl) upgradesEl.textContent = data.updates_available_count ?? data.upgrades_count ?? 0;
  if (sourcesEl) sourcesEl.textContent = data.sources_count ?? (data.winget_available ? 'winget' : 'MSI');

  applySoftwareFilters();
}

function applySoftwareFilters() {
  const tbody = document.getElementById('sw-tbody');
  const searchInput = document.getElementById('sw-search-input');
  const badge = document.getElementById('sw-table-badge');

  if (!tbody) return;

  const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

  const filtered = packagesList.filter(p => {
    if (!query) return true;
    const nameMatch = (p.name || '').toLowerCase().includes(query);
    const idMatch = (p.package_id || p.id || '').toLowerCase().includes(query);
    return nameMatch || idMatch;
  });

  if (badge) badge.textContent = `${filtered.length} из ${packagesList.length} пакетов`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Пакеты не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.slice(0, 150).map(p => {
    const name = p.name || 'Application';
    const id = p.package_id || p.id || '-';
    const ver = p.version || '-';
    const avail = p.available_version || p.latest_version || '-';
    const source = p.source || 'winget';
    const hasUpgrade = avail && avail !== '-' && avail !== ver;

    return `
      <tr>
        <td class="fw-semibold text-light">${name}</td>
        <td class="font-monospace text-info small">${id}</td>
        <td class="text-muted small">${ver}</td>
        <td>
          <span class="badge ${hasUpgrade ? 'bg-warning text-dark' : 'bg-secondary'}">
            ${avail}
          </span>
        </td>
        <td class="small text-muted">${source}</td>
        <td class="text-end">
          ${hasUpgrade ? `
            <button class="btn btn-xs btn-outline-warning py-0 px-2 sw-action-btn" data-id="${id}" data-action="upgrade" title="Обновить пакет">
              <i class="bi bi-arrow-up-circle"></i> Обновить
            </button>
          ` : `
            <button class="btn btn-xs btn-outline-danger py-0 px-2 sw-action-btn" data-id="${id}" data-action="uninstall" title="Удалить пакет">
              <i class="bi bi-trash"></i>
            </button>
          `}
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('.sw-action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const pkgId = btn.dataset.id;
      const act = btn.dataset.action;
      executeSoftwareAction(pkgId, act);
    });
  });
}

async function executeSoftwareAction(packageId, action) {
  if (window.toast) window.toast.info('Пакетный менеджер', `${action}: ${packageId}`);
  try {
    const res = await fetch('/api/software-manager/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ package_id: packageId, action: action, dry_run: false, confirmed_by_user: true })
    });
    const result = await res.json();
    if (res.ok) {
      if (window.toast) window.toast.success('Успех', `${packageId}: выполнено`);
      fetchSoftwareSummary();
    } else {
      if (window.toast) window.toast.error('Ошибка', result.detail || result.message || 'Сбой операции');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

export function initSoftwareManagerTab() {
  if (isInitialized) {
    fetchSoftwareSummary();
    return;
  }
  isInitialized = true;

  const refreshBtn = document.getElementById('sw-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchSoftwareSummary);

  const checkUpgradesBtn = document.getElementById('sw-check-upgrades-btn');
  if (checkUpgradesBtn) checkUpgradesBtn.addEventListener('click', () => {
    if (window.toast) window.toast.info('Проверка', 'Поиск доступных обновлений...');
    fetchSoftwareSummary();
  });

  const searchInput = document.getElementById('sw-search-input');
  if (searchInput) searchInput.addEventListener('input', applySoftwareFilters);

  registerTabPoller('tab-software-manager', fetchSoftwareSummary, 30000, { immediate: true });
  fetchSoftwareSummary();
}

window.initSoftwareManagerTab = initSoftwareManagerTab;
window.fetchSoftwareSummary = fetchSoftwareSummary;

if (document.getElementById('tab-software-manager') && document.getElementById('sw-tbody')) {
  initSoftwareManagerTab();
}
