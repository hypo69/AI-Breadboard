/**
 * =============================================================================
 * Process Name: Windows Process Manager Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт интерактивного диспетчера задач Windows (Task Manager)
 *   с поддержкой группировки Apps, Background processes и Windows processes.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/process_manager_tab/main.js?v=20261008_v1" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initProcessManagerTab } from '/windows/api/webgui/process_manager_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/process_manager_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 02:10:00
 * =============================================================================
 */

const registerTabPoller = window.registerTabPoller || function() {};

let isInitialized = false;
let currentReport = null;
let currentCategoryFilter = 'all';
let expandedGroups = new Set();
let allExpanded = false;

/**
 * Загрузка категоризированных процессов с бэкенда
 */
export async function fetchProcessManagerSummary() {
  try {
    const res = await fetch('/api/process-manager/categorized');
    if (!res.ok) {
      // Fallback на /summary
      const fallbackRes = await fetch('/api/process-manager/summary');
      if (!fallbackRes.ok) throw new Error(`HTTP ${res.status}`);
      currentReport = await fallbackRes.json();
    } else {
      currentReport = await res.json();
    }
    renderProcessManager(currentReport);
  } catch (err) {
    console.warn('[ProcessManager] Ошибка получения процессов:', err);
  }
}

/**
 * Рендеринг карточек статистики и таблицы процессов
 */
function renderProcessManager(report) {
  if (!report) return;

  const appsList = report.apps || [];
  const bgList = report.background_processes || [];
  const winList = report.windows_processes || [];

  const appsCountEl = document.getElementById('pm-apps-count');
  const bgCountEl = document.getElementById('pm-bg-count');
  const winCountEl = document.getElementById('pm-win-count');
  const totalCountEl = document.getElementById('pm-total-count');
  const ramUsageEl = document.getElementById('pm-ram-usage');

  const totalProcs = report.total_processes || (appsList.length + bgList.length + winList.length);
  const totalMemMb = report.total_memory_used_mb || 0;

  if (appsCountEl) appsCountEl.textContent = report.apps_count !== undefined ? report.apps_count : appsList.length;
  if (bgCountEl) bgCountEl.textContent = report.background_count !== undefined ? report.background_count : bgList.length;
  if (winCountEl) winCountEl.textContent = report.windows_count !== undefined ? report.windows_count : winList.length;
  if (totalCountEl) totalCountEl.textContent = totalProcs;

  if (ramUsageEl) {
    const memStr = totalMemMb >= 1024 ? `${(totalMemMb / 1024).toFixed(1)} GB` : `${Math.round(totalMemMb)} MB`;
    ramUsageEl.textContent = `Память: ${memStr}`;
  }

  applyProcessFilters();
}

/**
 * Применение фильтров поиска и категорий
 */
function applyProcessFilters() {
  if (!currentReport) return;

  const tbody = document.getElementById('pm-tbody');
  const searchInput = document.getElementById('pm-search-input');
  const badge = document.getElementById('pm-table-badge');

  if (!tbody) return;

  const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

  const apps = currentReport.apps || [];
  const bg = currentReport.background_processes || [];
  const win = currentReport.windows_processes || [];

  // Фильтрация групп по строке поиска
  function filterGroup(group) {
    if (!query) return true;
    const nameMatch = (group.name || '').toLowerCase().includes(query);
    const friendlyMatch = (group.friendly_name || '').toLowerCase().includes(query);
    const pidMatch = String(group.main_pid || '').includes(query);
    const titlesMatch = (group.window_titles || []).some(t => t.toLowerCase().includes(query));
    const subMatch = (group.subprocesses || []).some(sub => 
      (sub.name || '').toLowerCase().includes(query) ||
      String(sub.pid || '').includes(query) ||
      (sub.username || '').toLowerCase().includes(query)
    );
    return nameMatch || friendlyMatch || pidMatch || titlesMatch || subMatch;
  }

  const filteredApps = (currentCategoryFilter === 'all' || currentCategoryFilter === 'app') ? apps.filter(filterGroup) : [];
  const filteredBg = (currentCategoryFilter === 'all' || currentCategoryFilter === 'background') ? bg.filter(filterGroup) : [];
  const filteredWin = (currentCategoryFilter === 'all' || currentCategoryFilter === 'windows') ? win.filter(filterGroup) : [];

  const totalShown = filteredApps.length + filteredBg.length + filteredWin.length;
  if (badge) {
    badge.textContent = `${totalShown} групп (${currentReport.total_processes || totalShown} процессов)`;
  }

  if (totalShown === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Процессы не найдены</td></tr>';
    return;
  }

  let html = '';

  // Секция 1: Apps (Интерактивные приложения с окнами)
  if (filteredApps.length > 0) {
    html += `
      <tr class="table-active">
        <td colspan="6" class="py-2 px-3 fw-bold text-primary">
          <i class="bi bi-window-stack me-1.5"></i> Apps (${filteredApps.length})
        </td>
      </tr>
    `;
    html += filteredApps.map(g => renderGroupRow(g, 'app', 'App')).join('');
  }

  // Секция 2: Background processes (Фоновые процессы)
  if (filteredBg.length > 0) {
    html += `
      <tr class="table-active">
        <td colspan="6" class="py-2 px-3 fw-bold text-info">
          <i class="bi bi-gear-wide-connected me-1.5"></i> Background processes (${filteredBg.length})
        </td>
      </tr>
    `;
    html += filteredBg.map(g => renderGroupRow(g, 'background', 'Background process')).join('');
  }

  // Секция 3: Windows processes (Процессы Windows)
  if (filteredWin.length > 0) {
    html += `
      <tr class="table-active">
        <td colspan="6" class="py-2 px-3 fw-bold text-warning">
          <i class="bi bi-microsoft me-1.5"></i> Windows processes (${filteredWin.length})
        </td>
      </tr>
    `;
    html += filteredWin.map(g => renderGroupRow(g, 'windows', 'Windows process')).join('');
  }

  tbody.innerHTML = html;
  attachEventListeners(tbody);
}

/**
 * Рендеринг строки группы процессов (Task Manager style)
 */
function renderGroupRow(group, category, typeLabel) {
  const groupId = `grp-${category}-${group.name.replace(/[^a-zA-Z0-9_-]/g, '_')}-${group.main_pid}`;
  const isExpanded = allExpanded || expandedGroups.has(groupId);
  const count = group.instance_count || (group.subprocesses ? group.subprocesses.length : 1);
  const countBadge = count > 1 ? ` <span class="text-muted small">(${count})</span>` : '';
  const chevron = count > 1 || (group.subprocesses && group.subprocesses.length > 0)
    ? `<i class="bi bi-chevron-right pm-chevron ${isExpanded ? 'expanded' : ''}" data-group-id="${groupId}"></i>`
    : `<span style="display:inline-block; width:20px;"></span>`;

  const memMb = group.total_memory_mb || 0;
  const memStr = memMb >= 1024 ? `${(memMb / 1024).toFixed(1)} GB` : `${Math.round(memMb)} MB`;
  const cpuStr = (group.total_cpu_percent !== undefined) ? `${group.total_cpu_percent.toFixed(1)}%` : '0.0%';

  const iconClass = category === 'app' ? 'bi-app-indicator text-primary' : (category === 'windows' ? 'bi-microsoft text-warning' : 'bi-cpu text-info');

  let subRowsHtml = '';
  if (isExpanded && group.subprocesses && group.subprocesses.length > 0) {
    subRowsHtml = group.subprocesses.map(sub => {
      const subMem = sub.memory_mb >= 1024 ? `${(sub.memory_mb / 1024).toFixed(1)} GB` : `${Math.round(sub.memory_mb)} MB`;
      const titleInfo = sub.window_title ? `<div class="text-light small mt-0.5 text-truncate" style="max-width: 380px;"><i class="bi bi-window text-secondary me-1"></i>${escapeHtml(sub.window_title)}</div>` : '';
      return `
        <tr class="pm-sub-row" data-parent-group="${groupId}">
          <td class="ps-4 py-1.5">
            <div class="d-flex align-items-center gap-2">
              <i class="bi bi-arrow-return-right text-muted small"></i>
              <div>
                <span class="text-light">${escapeHtml(sub.name)}</span>
                ${titleInfo}
              </div>
            </div>
          </td>
          <td class="font-monospace text-warning small py-1.5">${sub.pid}</td>
          <td class="py-1.5"><span class="pm-type-tag text-muted">${typeLabel}</span></td>
          <td class="font-monospace text-light small py-1.5">${sub.cpu_percent.toFixed(1)}%</td>
          <td class="font-monospace text-info small py-1.5">${subMem}</td>
          <td class="text-end py-1.5">
            <button class="btn btn-xs btn-outline-danger py-0 px-1.5 pm-kill-btn" data-pid="${sub.pid}" data-name="${sub.name}" title="Завершить процесс PID: ${sub.pid}">
              <i class="bi bi-x"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }

  return `
    <tr class="pm-group-header" data-group-id="${groupId}">
      <td class="py-2">
        <div class="d-flex align-items-center">
          ${chevron}
          <i class="bi ${iconClass} me-2"></i>
          <span class="fw-semibold text-white">${escapeHtml(group.friendly_name || group.name)}</span>
          ${countBadge}
        </div>
      </td>
      <td class="font-monospace text-muted small py-2">${group.main_pid || '-'}</td>
      <td class="py-2"><span class="pm-type-tag">${typeLabel}</span></td>
      <td class="font-monospace text-light small py-2">${cpuStr}</td>
      <td class="font-monospace text-success small py-2">${memStr}</td>
      <td class="text-end py-2">
        <button class="btn btn-xs btn-outline-danger py-0 px-2 pm-kill-btn" data-pid="${group.main_pid}" data-name="${group.name}" data-tree="true" title="Завершить дерево процессов (${count})">
          <i class="bi bi-x-circle me-1"></i>Завершить
        </button>
      </td>
    </tr>
    ${subRowsHtml}
  `;
}

/**
 * Навешивание обработчиков событий
 */
function attachEventListeners(tbody) {
  // Клик по строке группы для раскрытия
  tbody.querySelectorAll('.pm-group-header').forEach(header => {
    header.addEventListener('click', (e) => {
      if (e.target.closest('.pm-kill-btn')) return;
      const groupId = header.dataset.groupId;
      if (expandedGroups.has(groupId)) {
        expandedGroups.delete(groupId);
      } else {
        expandedGroups.add(groupId);
      }
      applyProcessFilters();
    });
  });

  // Завершение процессов
  tbody.querySelectorAll('.pm-kill-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const pid = btn.dataset.pid;
      const name = btn.dataset.name;
      const killTree = btn.dataset.tree === 'true';
      killProcess(pid, name, killTree);
    });
  });
}

/**
 * Завершение процесса или дерева процессов через API
 */
async function killProcess(pid, name, killTree = false) {
  const treeMsg = killTree ? ' (и все дочерние процессы)' : '';
  if (!confirm(`Вы действительно хотите завершить ${name} [PID: ${pid}]${treeMsg}?`)) return;

  try {
    const res = await fetch('/api/process-manager/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pid: parseInt(pid, 10), kill_tree: killTree, dry_run: false, confirmed_by_user: true })
    });
    const result = await res.json();
    if (res.ok && result.status === 'SUCCESS') {
      if (window.toast) window.toast.success('Процесс завершен', `${name} (PID: ${pid})`);
      fetchProcessManagerSummary();
    } else {
      if (window.toast) window.toast.error('Ошибка завершения', result.message || result.detail || 'Отказано в доступе');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

/**
 * Экранирование спецсимволов HTML
 */
function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/**
 * Инициализация вкладки Process Manager
 */
export function initProcessManagerTab() {
  if (isInitialized) return;
  isInitialized = true;

  const refreshBtn = document.getElementById('pm-refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', fetchProcessManagerSummary);

  const searchInput = document.getElementById('pm-search-input');
  if (searchInput) searchInput.addEventListener('input', applyProcessFilters);

  // Фильтры по карточкам
  const cardApps = document.getElementById('pm-filter-card-apps');
  const cardBg = document.getElementById('pm-filter-card-bg');
  const cardWin = document.getElementById('pm-filter-card-win');
  const cardAll = document.getElementById('pm-filter-card-all');

  if (cardApps) cardApps.addEventListener('click', () => setCategoryFilter('app'));
  if (cardBg) cardBg.addEventListener('click', () => setCategoryFilter('background'));
  if (cardWin) cardWin.addEventListener('click', () => setCategoryFilter('windows'));
  if (cardAll) cardAll.addEventListener('click', () => setCategoryFilter('all'));

  // Фильтры по радиокнопкам
  document.querySelectorAll('input[name="pm-cat-filter"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      currentCategoryFilter = e.target.value;
      applyProcessFilters();
    });
  });

  // Кнопка развернуть / свернуть все
  const toggleExpandBtn = document.getElementById('pm-toggle-expand-btn');
  const expandText = document.getElementById('pm-expand-btn-text');
  if (toggleExpandBtn) {
    toggleExpandBtn.addEventListener('click', () => {
      allExpanded = !allExpanded;
      if (expandText) expandText.textContent = allExpanded ? 'Свернуть все' : 'Развернуть все';
      applyProcessFilters();
    });
  }

  registerTabPoller('tab-process-manager', fetchProcessManagerSummary, 5000, { immediate: true });
}

function setCategoryFilter(cat) {
  currentCategoryFilter = cat;
  const radio = document.querySelector(`input[name="pm-cat-filter"][value="${cat}"]`);
  if (radio) radio.checked = true;
  applyProcessFilters();
}

window.initProcessManagerTab = initProcessManagerTab;
