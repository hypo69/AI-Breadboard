/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Forensics Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт для форензики, активности окон, UserAssist, PowerShell
 *   Script Block Logging и событий Sysmon.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/html/forensics_tab/main.js?v=20261006_v2" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/forensics_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 06:10:00
 * =============================================================================
 */

(function () {
  'use strict';

  let autoRefreshTimer = null;

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text !== null && text !== undefined ? String(text) : '--';
  }

  async function apiFetch(url) {
    if (window.api && typeof window.api.fetch === 'function') {
      return await window.api.fetch(url);
    }
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return await res.json();
  }

  async function fetchForensicsActivity() {
    try {
      const data = await apiFetch('/api/v1/system/diagnostics/forensics');
      if (!data) return;

      if (data.foreground_window) {
        setText('diag-fg-title', data.foreground_window.title || 'Рабочий стол Windows');
        setText('diag-fg-proc', `Процесс: ${data.foreground_window.process_name || 'explorer.exe'} (PID: ${data.foreground_window.pid || 0})`);
      }

      setText('diag-user-idle-time', `${Number(data.user_idle_seconds || 0).toFixed(1)} сек`);
      const statusBadge = document.getElementById('diag-user-status-badge');
      if (statusBadge) {
        if (data.user_idle_seconds > 300) {
          statusBadge.className = 'badge bg-warning-subtle text-warning border border-warning';
          statusBadge.textContent = 'Простой > 5 мин';
        } else {
          statusBadge.className = 'badge bg-success-subtle text-success border border-success';
          statusBadge.textContent = 'Активен';
        }
      }

      // Camera Apps
      const camContainer = document.getElementById('diag-cam-access-list');
      if (camContainer) {
        if (data.camera_active_apps && data.camera_active_apps.length > 0) {
          camContainer.innerHTML = data.camera_active_apps.map(a => `
            <div class="d-flex align-items-center justify-content-between py-1 border-bottom border-secondary-subtle">
              <span class="text-truncate" style="max-width: 140px;">${escapeHtml(a.app_name)}</span>
              <span class="badge ${a.is_active_now ? 'bg-danger' : 'bg-secondary'}" style="font-size: 0.65rem;">
                ${a.is_active_now ? 'АКТИВНА' : 'Не активна'}
              </span>
            </div>
          `).join('');
        } else {
          camContainer.innerHTML = '<span class="text-muted small">Нет активных обращений к камере</span>';
        }
      }

      // Mic Apps
      const micContainer = document.getElementById('diag-mic-access-list');
      if (micContainer) {
        if (data.microphone_active_apps && data.microphone_active_apps.length > 0) {
          micContainer.innerHTML = data.microphone_active_apps.map(a => `
            <div class="d-flex align-items-center justify-content-between py-1 border-bottom border-secondary-subtle">
              <span class="text-truncate" style="max-width: 140px;">${escapeHtml(a.app_name)}</span>
              <span class="badge ${a.is_active_now ? 'bg-danger' : 'bg-secondary'}" style="font-size: 0.65rem;">
                ${a.is_active_now ? 'АКТИВЕН' : 'Не активен'}
              </span>
            </div>
          `).join('');
        } else {
          micContainer.innerHTML = '<span class="text-muted small">Нет активных обращений к микрофону</span>';
        }
      }

      // UserAssist Apps Table
      const uaTbody = document.getElementById('diag-userassist-tbody');
      if (uaTbody && data.userassist_top_apps) {
        setText('diag-userassist-count', `${data.userassist_top_apps.length} приложений`);
        if (data.userassist_top_apps.length === 0) {
          uaTbody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-muted">Данных UserAssist в реестре не обнаружено</td></tr>';
        } else {
          uaTbody.innerHTML = data.userassist_top_apps.map(a => `
            <tr>
              <td class="fw-bold text-white"><i class="bi bi-app text-info me-1.5"></i>${escapeHtml(a.name)}</td>
              <td style="text-align: right;" class="text-info font-monospace">${a.run_count}</td>
              <td style="text-align: right;" class="text-warning font-monospace">${a.focus_formatted}</td>
              <td class="small text-muted text-truncate" style="max-width: 280px;" title="${escapeHtml(a.path)}">${escapeHtml(a.path)}</td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.warn('[ForensicsTab] fetchForensicsActivity error:', err);
    }
  }

  async function fetchPowerShellScripts() {
    const tbody = document.getElementById('diag-powershell-tbody');
    const countBadge = document.getElementById('diag-powershell-count');

    try {
      const resp = await fetch('/api/v1/tc/telemetry/powershell-scripts?limit=20');
      if (!resp.ok) return;
      const data = await resp.json();
      const blocks = data.script_blocks || [];

      if (countBadge) countBadge.textContent = `${blocks.length} блоков`;

      if (tbody) {
        if (blocks.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Блоков выполнения PowerShell скриптов не зафиксировано</td></tr>';
          return;
        }

        tbody.innerHTML = blocks.map(b => {
          const time = b.time_created || b.timestamp || '--';
          const eventId = b.event_id || 4104;
          const path = b.script_path || b.path || 'Interactive / Console';
          const text = escapeHtml(b.script_block_text || b.text || '');

          return `
            <tr>
              <td class="font-monospace small text-muted text-nowrap">${time}</td>
              <td><span class="badge bg-warning text-dark">ID ${eventId}</span></td>
              <td class="small text-truncate text-info" style="max-width: 180px;" title="${escapeHtml(path)}">${escapeHtml(path)}</td>
              <td class="small text-light text-break font-monospace" style="max-width: 380px;">${text}</td>
            </tr>
          `;
        }).join('');
      }
    } catch (err) {
      console.warn('[ForensicsTab] fetchPowerShellScripts error:', err);
    }
  }

  async function fetchSysmonEvents() {
    const tbody = document.getElementById('diag-sysmon-tbody');
    const countBadge = document.getElementById('diag-sysmon-count');

    try {
      const resp = await fetch('/api/v1/tc/telemetry/sysmon?limit=20');
      if (!resp.ok) return;
      const data = await resp.json();
      const events = data.events || [];

      if (countBadge) countBadge.textContent = `${events.length} событий`;

      if (tbody) {
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Событий Sysmon в канале не обнаружено (или служба Sysmon не установлена)</td></tr>';
          return;
        }

        tbody.innerHTML = events.map(ev => {
          const time = ev.time_created || ev.timestamp || '--';
          const eventId = ev.event_id || 1;
          const proc = ev.image || ev.process_name || 'Sysmon';
          const desc = ev.command_line || ev.target_filename || ev.hashes || JSON.stringify(ev);

          return `
            <tr>
              <td class="font-monospace small text-muted text-nowrap">${time}</td>
              <td><span class="badge bg-danger">ID ${eventId}</span></td>
              <td class="small text-truncate text-white fw-bold" style="max-width: 180px;" title="${escapeHtml(proc)}">${escapeHtml(proc)}</td>
              <td class="small text-light text-break font-monospace" style="max-width: 380px;">${escapeHtml(desc)}</td>
            </tr>
          `;
        }).join('');
      }
    } catch (err) {
      console.warn('[ForensicsTab] fetchSysmonEvents error:', err);
    }
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('btn-diag-forensics-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => {
        fetchForensicsActivity();
        fetchPowerShellScripts();
        fetchSysmonEvents();
      };
    }

    const autoSwitch = document.getElementById('diag-forensics-auto-refresh');
    if (autoSwitch) {
      autoSwitch.onchange = (e) => {
        if (e.target.checked) {
          autoRefreshTimer = setInterval(() => {
            fetchForensicsActivity();
            fetchPowerShellScripts();
            fetchSysmonEvents();
          }, 3000);
        } else if (autoRefreshTimer) {
          clearInterval(autoRefreshTimer);
          autoRefreshTimer = null;
        }
      };
    }
  }

  async function init() {
    bindEvents();
    await Promise.all([
      fetchForensicsActivity(),
      fetchPowerShellScripts(),
      fetchSysmonEvents(),
    ]);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 10);
  }
})();
