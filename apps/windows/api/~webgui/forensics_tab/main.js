/**
 * =============================================================================
 * Process Name: Windows Forensics Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/forensics_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/forensics_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
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
        setText('diag-fg-title', data.foreground_window.title || i18n.t('auto__windows_2c9c53'));
        setText('diag-fg-proci18n.t('auto__data_foreground_window_process_name__e5a705')unknown'} (PID: ${data.foreground_window.pid || 0})`);
      }

      setText('diag-user-idle-timei18n.t('auto__data_user_idle_seconds_tofixed_1_const_statusbadge_document_getelementbyid__c17959')diag-user-status-badge');
      if (statusBadge) {
        if (data.user_idle_seconds > 300) {
          statusBadge.className = 'badge bg-warning-subtle text-warning border border-warning';
          statusBadge.textContent = i18n.t('auto__5__fad944');
        } else {
          statusBadge.className = 'badge bg-success-subtle text-success border border-success';
          statusBadge.textContent = i18n.t('auto___34f9a7');
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
                ${a.is_active_now ? i18n.t('auto___bc790a') : i18n.t('auto___0e9e53')}
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
                ${a.is_active_now ? i18n.t('auto___d75908') : i18n.t('auto___0e9e53')}
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
        setText('diag-userassist-counti18n.t('auto__data_userassist_top_apps_length_if_data_userassist_top_apps_length_0_uatbody_innerhtml__b713ff')<tr><td colspan="4" class="text-center py-4 text-muted">Данных UserAssist в реестре не обнаружено</td></tr>';
        } else {
          uaTbody.innerHTML = data.userassist_top_apps.map(a => `
            <tr>
              <td class="fw-bold text-white"><i class="bi bi-app text-info me-1.5"></i>${escapeHtml(a.name)}</td>
              <td style="text-align: right;" class="text-info font-monospacei18n.t('auto__a_run_count_td_td_style__303c05')text-align: right;" class="text-warning font-monospace">${a.focus_formatted}</td>
              <td class="small text-muted text-truncate" style="max-width: 280px;" title="${escapeHtml(a.path)}">${escapeHtml(a.path)}</td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.warn('[ForensicsTab] fetchForensicsActivity error:', err);
    }
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('btn-diag-forensics-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => fetchForensicsActivity();
    }

    const autoSwitch = document.getElementById('diag-forensics-auto-refresh');
    if (autoSwitch) {
      autoSwitch.onchange = (e) => {
        if (e.target.checked) {
          autoRefreshTimer = setInterval(fetchForensicsActivity, 3000);
        } else if (autoRefreshTimer) {
          clearInterval(autoRefreshTimer);
          autoRefreshTimer = null;
        }
      };
    }
  }

  async function init() {
    bindEvents();
    await fetchForensicsActivity();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 10);
  }
})();
