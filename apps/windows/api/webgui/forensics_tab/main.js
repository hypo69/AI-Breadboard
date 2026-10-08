/**
 * =============================================================================
 * Process Name: Windows Forensics Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/forensics_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/forensics_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 02:00:00
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
        setText('diag-fg-proc', `Процесс: ${data.foreground_window.process_name || 'unknown'} (PID: ${data.foreground_window.pid || 0})`);
      }

      setText('diag-user-idle-time', `${data.user_idle_seconds.toFixed(1)} сек`);
      const statusBadge = document.getElementById('diag-user-status-badge');
      if (statusBadge) {
        if (data.user_idle_seconds > 300) {
          statusBadge.className = 'badge bg-warning-subtle text-warning border border-warning';
          statusBadge.textContent = 'Пользователь отошел (>5 мин)';
        } else {
          statusBadge.className = 'badge bg-success-subtle text-success border border-success';
          statusBadge.textContent = 'Пользователь за ПК';
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
                ${a.is_active_now ? 'Захват камеры' : 'В доступе'}
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
                ${a.is_active_now ? 'Запись звука' : 'В доступе'}
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
        setText('diag-userassist-count', `${data.userassist_top_apps.length} программ`);
        if (data.userassist_top_apps.length === 0) {
          uaTbody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-muted">Данных UserAssist в реестре не обнаружено</td></tr>';
        } else {
          uaTbody.innerHTML = data.userassist_top_apps.map(a => `
            <tr>
              <td class="fw-bold text-white"><i class="bi bi-app text-info me-1.5"></i>${escapeHtml(a.name)}</td>
              <td style="text-align: right;" class="text-info font-monospace">${a.run_count} раз</td>
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

  const POLL_ID = 'forensics';

  function getFrequency() {
    try {
      const saved = localStorage.getItem(`poll_freq_${POLL_ID}`);
      if (saved) return saved;
    } catch (_) {}
    return 'manual';
  }

  function setFrequency(freq) {
    try {
      localStorage.setItem(`poll_freq_${POLL_ID}`, freq);
    } catch (_) {}
    applyPoller(freq, false);
  }

  function stopPolling() {
    if (window.unregisterTabPoller) {
      window.unregisterTabPoller(`tab-forensics_${POLL_ID}`);
    }
    if (autoRefreshTimer) {
      clearInterval(autoRefreshTimer);
      autoRefreshTimer = null;
    }
  }

  function applyPoller(freq, runInitial = false) {
    stopPolling();
    if (freq === 'start' || freq === 'manual') {
      if (runInitial && (window.isTabActive ? window.isTabActive('tab-forensics') : true)) {
        fetchForensicsActivity();
      }
      return;
    }

    const intervalSec = parseInt(freq, 10);
    if (isNaN(intervalSec) || intervalSec <= 0) return;

    const intervalMs = intervalSec * 1000;
    const pollerId = `tab-forensics_${POLL_ID}`;

    if (window.registerTabPoller) {
      window.registerTabPoller('tab-forensics', fetchForensicsActivity, intervalMs, { pollerId, immediate: runInitial });
    } else {
      if (runInitial && (window.isTabActive ? window.isTabActive('tab-forensics') : true)) {
        fetchForensicsActivity();
      }
      autoRefreshTimer = setInterval(() => {
        if (window.isTabActive ? window.isTabActive('tab-forensics') : true) {
          fetchForensicsActivity();
        }
      }, intervalMs);
    }
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('btn-diag-forensics-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => fetchForensicsActivity();
    }

    const select = document.getElementById('diag-forensics-poll-freq');
    if (select) {
      select.onchange = (e) => {
        const newFreq = e.target.value;
        setFrequency(newFreq);
        if (newFreq !== 'manual' && newFreq !== 'start') {
          fetchForensicsActivity();
        }
        if (window.showToast) {
          const label = select.options[select.selectedIndex]?.text || newFreq;
          window.showToast(`Частота опроса форензики: ${label}`, 'info');
        }
      };
    }
  }

  async function initForensicsTab() {
    bindEvents();
    const currentFreq = getFrequency();
    const select = document.getElementById('diag-forensics-poll-freq');
    if (select) select.value = currentFreq;
    applyPoller(currentFreq, true);
  }

  window.initForensicsTab = initForensicsTab;
  window.activateForensicsTab = () => {
    applyPoller(getFrequency(), true);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      if (window.isTabActive ? window.isTabActive('tab-forensics') : false) {
        initForensicsTab();
      } else {
        bindEvents();
      }
    });
  } else {
    if (window.isTabActive ? window.isTabActive('tab-forensics') : false) {
      initForensicsTab();
    } else {
      bindEvents();
    }
  }
})();
