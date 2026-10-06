/**
 * =============================================================================
 * Process Name: Windows Web Interface - Taskbar Tab Controller
 * =============================================================================
 * Description:
 *   Клиентский контроллер интерактивного управления панелью задач, окнами
 *   и историей изменений в telemetry.db с поддержкой Rollback.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/taskbar_tab/main.js?v=20261006_v2" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/taskbar_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 17:58:00
 * =============================================================================
 */

let _windowsCache = [];
let _commandsCache = [];
let _historyCache = [];

export async function init() {
  bindEvents();
  await refreshAll();
}

function bindEvents() {
  document.getElementById('btn-refresh-taskbar-data')?.addEventListener('click', () => refreshAll());
  document.getElementById('btn-restart-explorer-quick')?.addEventListener('click', () => restartExplorer());
  document.getElementById('btn-rollback-last-quick')?.addEventListener('click', () => rollbackLast());
  document.getElementById('btn-refresh-history')?.addEventListener('click', () => loadHistory());
  document.getElementById('input-search-windows')?.addEventListener('input', () => renderWindowsTable());
  document.getElementById('btn-batch-minimize-all')?.addEventListener('click', () => executeBatchWindowAction('minimize_all'));
  document.getElementById('btn-batch-restore-all')?.addEventListener('click', () => executeBatchWindowAction('restore_all'));
  document.getElementById('form-taskbar-settings')?.addEventListener('submit', (e) => saveTaskbarSettings(e));
  document.getElementById('form-launch-app')?.addEventListener('submit', (e) => handleLaunchApp(e));
  document.getElementById('btn-refresh-pinned')?.addEventListener('click', () => loadPinnedApps());
  
  const range = document.getElementById('range-ux-progress');
  const label = document.getElementById('label-progress-val');
  if (range && label) {
    range.addEventListener('input', () => { label.textContent = `${range.value}%`; });
  }
  document.getElementById('btn-apply-ux-progress')?.addEventListener('click', () => handleApplyUxProgress());

  document.getElementById('filter-cmd-category')?.addEventListener('change', () => renderCommandsTable());
  document.getElementById('filter-cmd-risk')?.addEventListener('change', () => renderCommandsTable());
}

export async function refreshAll() {
  await Promise.all([
    loadSummary(),
    loadWindows(),
    loadSettings(),
    loadPinnedApps(),
    loadHistory(),
    loadCommandCatalog(),
  ]);
}

async function loadSummary() {
  try {
    const res = await fetch('/api/v1/taskbar/summary');
    if (!res.ok) return;
    const data = await res.json();

    const rectEl = document.getElementById('metric-tb-rect');
    if (rectEl) {
      rectEl.textContent = `${data.taskbar_rect.width}x${data.taskbar_rect.height} px`;
    }

    const alignEl = document.getElementById('metric-tb-align');
    if (alignEl) {
      alignEl.textContent = data.settings.alignment === 1 ? 'По центру' : 'По левому краю';
    }

    const winEl = document.getElementById('metric-tb-windows');
    if (winEl) {
      winEl.textContent = `${data.visible_windows_count} / ${data.windows_count}`;
    }

    const fgEl = document.getElementById('metric-tb-fg');
    if (fgEl) {
      fgEl.textContent = data.foreground_window?.title || '—';
      fgEl.title = data.foreground_window?.title || '';
    }

    const osBadge = document.getElementById('tb-os-badge');
    if (osBadge) {
      osBadge.textContent = data.is_win11 ? 'Windows 11 (Center/Left Taskbar)' : 'Windows 10 / Classic';
    }
  } catch (err) {
    console.error('Ошибка загрузки summary:', err);
  }
}

async function loadWindows() {
  const tbody = document.getElementById('tbody-windows-list');
  try {
    const res = await fetch('/api/v1/taskbar/windows?only_visible=false&only_taskbar=false');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    _windowsCache = await res.json();
    renderWindowsTable();
    populateWindowSelects();
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-danger p-3 text-center">Ошибка: ${err.message}</td></tr>`;
    }
  }
}

function renderWindowsTable() {
  const tbody = document.getElementById('tbody-windows-list');
  const filter = (document.getElementById('input-search-windows')?.value || '').toLowerCase();
  if (!tbody) return;

  const filtered = _windowsCache.filter(w => {
    if (!filter) return w.title;
    return w.title.toLowerCase().includes(filter) || w.process_name.toLowerCase().includes(filter) || String(w.hwnd).includes(filter);
  });

  const badge = document.getElementById('badge-windows-count');
  if (badge) badge.textContent = filtered.length;

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-muted p-4 text-center">Окна по фильтру не найдены</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(w => {
    const isFg = w.is_foreground ? '<span class="badge bg-warning text-dark me-1">Фокус</span>' : '';
    const stateBadge = w.is_minimized 
      ? '<span class="badge bg-secondary">Свернуто</span>' 
      : w.is_maximized 
        ? '<span class="badge bg-success">Развернуто</span>' 
        : '<span class="badge bg-info text-dark">Нормальное</span>';

    return `
      <tr class="${w.is_foreground ? 'table-active' : ''}">
        <td><code class="user-select-all">${w.hwnd}</code></td>
        <td class="text-truncate" style="max-width: 250px;" title="${escapeHtml(w.title)}">
          ${isFg}<strong>${escapeHtml(w.title || '(Без названия)')}</strong>
        </td>
        <td>
          <div class="fw-semibold text-truncate" style="max-width: 140px;">${escapeHtml(w.process_name || '—')}</div>
          <div class="text-muted small">PID: ${w.process_id}</div>
        </td>
        <td><small class="text-muted">${w.rect.width} × ${w.rect.height}</small></td>
        <td>${stateBadge}</td>
        <td class="text-end">
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-primary" onclick="window._taskbarActions.activate(${w.hwnd})" title="Активировать"><i class="bi bi-lightning-fill"></i></button>
            <button class="btn btn-outline-secondary" onclick="window._taskbarActions.minimize(${w.hwnd})" title="Свернуть"><i class="bi bi-dash"></i></button>
            <button class="btn btn-outline-secondary" onclick="window._taskbarActions.maximize(${w.hwnd})" title="Развернуть"><i class="bi bi-square"></i></button>
            <button class="btn btn-outline-secondary" onclick="window._taskbarActions.restore(${w.hwnd})" title="Восстановить"><i class="bi bi-window"></i></button>
            <button class="btn btn-outline-danger" onclick="window._taskbarActions.close(${w.hwnd})" title="Закрыть"><i class="bi bi-x-lg"></i></button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function populateWindowSelects() {
  const sel = document.getElementById('select-ux-target-window');
  if (!sel) return;
  const named = _windowsCache.filter(w => w.title);
  sel.innerHTML = named.map(w => `<option value="${w.hwnd}">${w.hwnd} — ${escapeHtml(w.title.slice(0, 40))} (${w.process_name})</option>`).join('');
}

// Window Actions
window._taskbarActions = {
  activate: async (hwnd) => {
    await fetch(`/api/v1/taskbar/windows/${hwnd}/activate`, { method: 'POST' });
    await loadWindows();
    await loadHistory();
  },
  minimize: async (hwnd) => {
    await fetch(`/api/v1/taskbar/windows/${hwnd}/minimize`, { method: 'POST' });
    await loadWindows();
    await loadHistory();
  },
  maximize: async (hwnd) => {
    await fetch(`/api/v1/taskbar/windows/${hwnd}/maximize`, { method: 'POST' });
    await loadWindows();
    await loadHistory();
  },
  restore: async (hwnd) => {
    await fetch(`/api/v1/taskbar/windows/${hwnd}/restore`, { method: 'POST' });
    await loadWindows();
    await loadHistory();
  },
  close: async (hwnd) => {
    await fetch(`/api/v1/taskbar/windows/${hwnd}`, { method: 'DELETE' });
    await loadWindows();
    await loadHistory();
  }
};

async function executeBatchWindowAction(action) {
  try {
    const res = await fetch('/api/v1/taskbar/windows/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    if (res.ok) {
      if (window.toast) window.toast.success('Действие выполнено', `Пакетное действие: ${action}`);
      await loadWindows();
      await loadHistory();
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка', err.message);
  }
}

async function loadSettings() {
  try {
    const res = await fetch('/api/v1/taskbar/settings');
    if (!res.ok) return;
    const s = await res.json();

    const alignVal = s.alignment === 1 ? '1' : '0';
    const alignRadio = document.querySelector(`input[name="tb-alignment"][value="${alignVal}"]`);
    if (alignRadio) alignRadio.checked = true;

    const selSearch = document.getElementById('select-search-mode');
    if (selSearch) selSearch.value = String(s.search_mode);

    setCheck('switch-auto-hide', s.auto_hide);
    setCheck('switch-widgets', s.widgets_visible);
    setCheck('switch-task-view', s.task_view_visible);
    setCheck('switch-copilot', s.copilot_visible);
    setCheck('switch-badges', s.badges_enabled);
  } catch (err) {
    console.error('Ошибка настроек:', err);
  }
}

function setCheck(id, val) {
  const el = document.getElementById(id);
  if (el) el.checked = Boolean(val);
}

async function saveTaskbarSettings(e) {
  e.preventDefault();
  const alignRadio = document.querySelector('input[name="tb-alignment"]:checked');
  const alignment = alignRadio ? parseInt(alignRadio.value, 10) : 1;
  const search_mode = parseInt(document.getElementById('select-search-mode')?.value || '1', 10);
  const auto_hide = document.getElementById('switch-auto-hide')?.checked || false;
  const widgets_visible = document.getElementById('switch-widgets')?.checked || false;
  const task_view_visible = document.getElementById('switch-task-view')?.checked || false;
  const copilot_visible = document.getElementById('switch-copilot')?.checked || false;
  const badges_enabled = document.getElementById('switch-badges')?.checked || false;
  const restart_explorer = document.getElementById('switch-restart-explorer')?.checked || false;

  try {
    const res = await fetch('/api/v1/taskbar/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        alignment,
        search_mode,
        auto_hide,
        widgets_visible,
        task_view_visible,
        copilot_visible,
        badges_enabled,
        restart_explorer,
      })
    });
    if (res.ok) {
      if (window.toast) window.toast.success('Настройки сохранены', 'Параметры панели задач успешно зафиксированы в telemetry.db');
      await refreshAll();
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка сохранения', err.message);
  }
}

async function restartExplorer() {
  if (!confirm('Перезапустить процесс Explorer? Экран на 1-2 секунды обновится.')) return;
  try {
    const res = await fetch('/api/v1/taskbar/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ restart_explorer: true })
    });
    if (res.ok && window.toast) {
      window.toast.success('Explorer перезапущен', 'Оболочка Windows успешно перезапущена');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка', err.message);
  }
}

async function loadPinnedApps() {
  const container = document.getElementById('pinned-apps-container');
  try {
    const res = await fetch('/api/v1/taskbar/apps');
    if (!res.ok) return;
    const apps = await res.json();
    if (!container) return;

    if (apps.length === 0) {
      container.innerHTML = `<div class="text-muted small p-3 text-center">Нет закрепленных ярлыков</div>`;
      return;
    }

    container.innerHTML = `<div class="list-group list-group-flush">${apps.map(a => `
      <div class="list-group-item d-flex justify-content-between align-items-center p-2">
        <div class="d-flex align-items-center gap-2">
          <i class="bi bi-app text-primary"></i>
          <div>
            <div class="fw-semibold small">${escapeHtml(a.name)}</div>
            <div class="text-muted font-monospace" style="font-size: 0.72rem;">${escapeHtml(a.target_path || a.link_path)}</div>
          </div>
        </div>
      </div>
    `).join('')}</div>`;
  } catch (err) {
    if (container) container.innerHTML = `<div class="text-danger small p-2">Ошибка: ${err.message}</div>`;
  }
}

async function handleLaunchApp(e) {
  e.preventDefault();
  const path = document.getElementById('launch-app-path')?.value || '';
  const args = document.getElementById('launch-app-args')?.value || '';
  const admin = document.getElementById('launch-app-admin')?.checked || false;

  try {
    const res = await fetch('/api/v1/taskbar/apps/launch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_path: path, arguments: args || null, admin })
    });
    const data = await res.json();
    if (res.ok) {
      if (window.toast) window.toast.success('Приложение запущено', data.message);
      document.getElementById('launch-app-path').value = '';
      setTimeout(() => { loadWindows(); loadHistory(); }, 1000);
    } else {
      if (window.toast) window.toast.error('Ошибка запуска', data.detail || 'Сбой');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка сети', err.message);
  }
}

async function handleApplyUxProgress() {
  const hwnd = parseInt(document.getElementById('select-ux-target-window')?.value || '0', 10);
  const state = document.getElementById('select-ux-progress-state')?.value || 'normal';
  const val = parseInt(document.getElementById('range-ux-progress')?.value || '50', 10);

  if (!hwnd) {
    if (window.toast) window.toast.warning('Внимание', 'Выберите целевое окно');
    return;
  }

  try {
    const res = await fetch('/api/v1/taskbar/ux/progress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hwnd, state, completed: val, total: 100 })
    });
    if (res.ok && window.toast) {
      window.toast.success('ITaskbarList3', `Прогресс ${val}% передан окну HWND ${hwnd}`);
      await loadHistory();
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка', err.message);
  }
}

// History & Rollback
async function loadHistory() {
  const tbody = document.getElementById('tbody-history-list');
  try {
    const res = await fetch('/api/v1/taskbar/history?limit=50');
    if (!res.ok) return;
    _historyCache = await res.json();
    renderHistoryTable();
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-danger p-3 text-center">Ошибка: ${err.message}</td></tr>`;
    }
  }
}

function renderHistoryTable() {
  const tbody = document.getElementById('tbody-history-list');
  const badge = document.getElementById('badge-history-count');
  if (badge) badge.textContent = _historyCache.length;
  if (!tbody) return;

  if (_historyCache.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-muted p-4 text-center">История в telemetry.db пуста</td></tr>`;
    return;
  }

  tbody.innerHTML = _historyCache.map(h => {
    const rolledBadge = h.is_rolled_back 
      ? '<span class="badge bg-secondary">Откачено</span>' 
      : '<span class="badge bg-success-subtle text-success border border-success-subtle">Активно</span>';

    const canRollback = !h.is_rolled_back && h.previous_state;
    const timeShort = (h.timestamp || '').replace('T', ' ').slice(0, 19);

    let detailsStr = '';
    if (h.previous_state || h.new_state) {
      detailsStr = `<small class="text-muted font-monospace">${escapeHtml(JSON.stringify(h.new_state || h.details || {}).slice(0, 60))}</small>`;
    } else if (h.details) {
      detailsStr = `<small class="text-muted">${escapeHtml(JSON.stringify(h.details).slice(0, 60))}</small>`;
    }

    return `
      <tr class="${h.is_rolled_back ? 'opacity-75' : ''}">
        <td><code>#${h.id}</code></td>
        <td><small>${escapeHtml(timeShort)}</small></td>
        <td>
          <div class="fw-semibold"><code>${escapeHtml(h.command_id)}</code></div>
          <small class="text-muted">${escapeHtml(h.action_type)} ${h.target_hwnd ? `(HWND: ${h.target_hwnd})` : ''}</small>
        </td>
        <td>${detailsStr}</td>
        <td>${rolledBadge}</td>
        <td class="text-end">
          ${canRollback ? `
            <button class="btn btn-outline-warning btn-sm py-0 px-2" onclick="window._rollbackAction(${h.id})" title="Откатить это изменение">
              <i class="bi bi-arrow-counterclockwise me-1"></i> Откат
            </button>
          ` : '<span class="text-muted small">—</span>'}
        </td>
      </tr>
    `;
  }).join('');
}

window._rollbackAction = async (historyId) => {
  if (!confirm(`Откатить действие #${historyId}? Предыдущее состояние будет восстановлено.`)) return;
  try {
    const res = await fetch(`/api/v1/taskbar/history/${historyId}/rollback`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      if (window.toast) window.toast.success('Откат выполнен', data.message);
      await refreshAll();
    } else {
      if (window.toast) window.toast.error('Ошибка отката', data.detail || 'Сбой');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка', err.message);
  }
};

async function rollbackLast() {
  try {
    const res = await fetch('/api/v1/taskbar/history/rollback-last', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      if (window.toast) window.toast.success('Откат выполнен', data.message);
      await refreshAll();
    } else {
      if (window.toast) window.toast.error('Ошибка отката', data.detail || 'Сбой');
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка', err.message);
  }
}

async function loadCommandCatalog() {
  try {
    const res = await fetch('/api/v1/taskbar/commands');
    if (!res.ok) return;
    _commandsCache = await res.json();
    renderCommandsTable();
  } catch (err) {
    console.error('Ошибка каталога команд:', err);
  }
}

function renderCommandsTable() {
  const tbody = document.getElementById('tbody-commands-list');
  const cat = document.getElementById('filter-cmd-category')?.value || '';
  const risk = document.getElementById('filter-cmd-risk')?.value || '';
  if (!tbody) return;

  const filtered = _commandsCache.filter(c => {
    if (cat && c.category.toLowerCase() !== cat.toLowerCase()) return false;
    if (risk && c.risk.toLowerCase() !== risk.toLowerCase()) return false;
    return true;
  });

  const badge = document.getElementById('badge-commands-count');
  if (badge) badge.textContent = filtered.length;

  tbody.innerHTML = filtered.map(c => {
    const riskBadge = c.risk === 'safe' 
      ? '<span class="badge bg-success-subtle text-success border border-success-subtle">safe</span>'
      : c.risk === 'caution'
        ? '<span class="badge bg-warning-subtle text-warning border border-warning-subtle">caution</span>'
        : c.risk === 'admin'
          ? '<span class="badge bg-danger-subtle text-danger border border-danger-subtle">admin</span>'
          : '<span class="badge bg-danger text-white">high</span>';

    const apiStr = c.api.win32 || c.api.com || c.api.registry || c.api.powershell || '—';

    return `
      <tr>
        <td><code>${escapeHtml(c.id)}</code></td>
        <td><span class="badge bg-secondary-subtle text-secondary">${escapeHtml(c.execution_class)}</span></td>
        <td>${riskBadge}</td>
        <td>${escapeHtml(c.description)}</td>
        <td class="font-monospace small text-muted text-truncate" style="max-width: 200px;" title="${escapeHtml(apiStr)}">${escapeHtml(apiStr)}</td>
        <td class="text-end">
          <button class="btn btn-outline-primary btn-sm py-0 px-2" onclick="window._executeCommandDirect('${c.id}')" title="Выполнить">
            <i class="bi bi-play"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

window._executeCommandDirect = async (cmdId) => {
  const meta = _commandsCache.find(c => c.id === cmdId);
  if (meta?.requires_confirmation) {
    if (!confirm(`Команда ${cmdId} имеет повышенный риск (${meta.risk}). Подтвердить запуск?`)) return;
  }
  try {
    const res = await fetch('/api/v1/taskbar/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmdId, params: {}, confirmed_by_user: true })
    });
    const data = await res.json();
    if (res.ok && window.toast) {
      window.toast.success(`Команда ${cmdId}`, data.message || 'Выполнено успешно');
      await loadHistory();
    }
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка', err.message);
  }
};

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => init());
} else {
  init();
}
