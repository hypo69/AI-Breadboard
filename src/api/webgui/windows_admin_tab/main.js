// =============================================================================
// Process Name: Windows System Administrator Web Tab Module
// =============================================================================
// Description:
//   Client-side JavaScript controller for the Windows System Administrator
//   administrative web interface tab.
//
// File: main.js
// Project: ai-breadboard
// Package: src.api.webinterface.windows_admin_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function() {
  let isWinAdminInitialized = false;

  async function fetchStatus() {
    try {
      const res = await fetch('/api/sysadmin/status');
      if (!res.ok) return;
      const data = await res.json();
      
      const hostEl = document.getElementById('winadmin-hostname');
      const adEl = document.getElementById('winadmin-ad-status');
      const userCountEl = document.getElementById('winadmin-user-count');
      const eventCountEl = document.getElementById('winadmin-event-count');

      if (hostEl) hostEl.innerText = `${data.hostname || 'LOCAL'} / ${data.domain || 'WORKGROUP'}`;
      if (adEl) {
        adEl.innerText = data.ad_connected ? `AD: ${data.ad_status}` : 'Локальный режим';
        adEl.className = data.ad_connected ? 'winadmin-value text-success' : 'winadmin-value text-info';
      }
      if (userCountEl) userCountEl.innerText = data.user_count || 0;
      if (eventCountEl) eventCountEl.innerText = data.event_count || 0;
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch status:', e);
    }
  }

  async function fetchUsers() {
    try {
      const res = await fetch('/api/sysadmin/users');
      if (!res.ok) return;
      const data = await res.json();
      const users = data.users || [];
      
      const tbody = document.getElementById('winadmin-users-tbody');
      const badge = document.getElementById('winadmin-users-badge');
      if (badge) badge.innerText = `${users.length} сессий`;

      if (tbody) {
        if (users.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted p-3">Нет активных сессий</td></tr>';
          return;
        }
        tbody.innerHTML = users.map(u => `
          <tr>
            <td class="fw-semibold text-white"><i class="bi bi-person me-1"></i> ${u.username}</td>
            <td class="font-monospace">${u.session_id}</td>
            <td><span class="badge ${u.status === 'Active' ? 'bg-success-subtle text-success' : 'bg-secondary'}">${u.status}</span></td>
            <td class="font-monospace text-muted">${u.ip_address || '127.0.0.1'}</td>
            <td style="text-align: right;">
              <button class="btn btn-sm btn-outline-danger py-0 px-2 btn-disconnect-user" data-user="${u.username}">
                Отключить
              </button>
            </td>
          </tr>
        `).join('');

        tbody.querySelectorAll('.btn-disconnect-user').forEach(btn => {
          btn.onclick = async () => {
            const user = btn.getAttribute('data-user');
            if (confirm(`Отключить сессию пользователя ${user}?`)) {
              await fetch(`/api/sysadmin/users/${user}/disconnect`, { method: 'POST' });
              fetchUsers();
              fetchStatus();
            }
          };
        });
      }
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch users:', e);
    }
  }

  async function fetchEvents() {
    try {
      const res = await fetch('/api/sysadmin/events?hours=24');
      if (!res.ok) return;
      const data = await res.json();
      const events = data.events || [];
      
      const tbody = document.getElementById('winadmin-events-tbody');
      const badge = document.getElementById('winadmin-events-badge');
      if (badge) badge.innerText = `${events.length} записей`;

      if (tbody) {
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted p-3">События не зафиксированы</td></tr>';
          return;
        }
        tbody.innerHTML = events.slice(0, 30).map(e => `
          <tr>
            <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
            <td class="font-monospace fw-semibold text-info">${e.event_id}</td>
            <td><span class="badge ${e.level === 'Warning' ? 'bg-warning-subtle text-warning' : (e.level === 'Error' ? 'bg-danger-subtle text-danger' : 'bg-info-subtle text-info')}">${e.level}</span></td>
            <td class="small text-light">${e.source}: ${e.description}</td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch events:', e);
    }
  }

  function initWindowsAdminTab() {
    console.log('[WinAdminTab] Initializing Windows Sysadmin tab...');
    fetchStatus();
    fetchUsers();
    fetchEvents();

    if (!isWinAdminInitialized) {
      const refreshBtn = document.getElementById('btn-winadmin-refresh');
      const configBtn = document.getElementById('btn-winadmin-config');

      if (refreshBtn) {
        refreshBtn.onclick = () => {
          fetchStatus();
          fetchUsers();
          fetchEvents();
        };
      }

      if (configBtn) {
        configBtn.onclick = () => {
          if (typeof window.openAppConfigModal === 'function') {
            window.openAppConfigModal('windows_sysadmin', 'Windows System Administrator');
          }
        };
      }

      isWinAdminInitialized = true;
    }
  }

  window.initWindowsAdminTab = initWindowsAdminTab;
})();
