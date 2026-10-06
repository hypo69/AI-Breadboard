/**
 * =============================================================================
 * Process Name: Windows Peripherals Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/peripherals_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/peripherals_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 00:20:00
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

  async function fetchPeripheralsNetwork() {
    try {
      const data = await apiFetch('/api/v1/system/diagnostics/peripherals');
      if (!data) return;

      // Wi-Fi
      if (data.wifi_telemetry) {
        const w = data.wifi_telemetry;
        setText('diag-wifi-ssid', w.ssid || 'Не подключено');
        setText('diag-wifi-bssid', w.bssid || '--');
        setText('diag-wifi-signal', `${w.signal_pct}% (${w.rssi_dbm} dBm)`);
        setText('diag-wifi-channel', w.channel || '--');
        setText('diag-wifi-radio', w.radio_type || '--');
        setText('diag-wifi-auth', w.auth_cipher || '--');

        const wifiBadge = document.getElementById('diag-wifi-status-badge');
        if (wifiBadge) {
          if (w.is_connected) {
            wifiBadge.className = 'badge bg-success-subtle text-success border border-success';
            wifiBadge.textContent = 'Wi-Fi Подключено';
          } else {
            wifiBadge.className = 'badge bg-secondary';
            wifiBadge.textContent = 'Wi-Fi Отключено';
          }
        }
      }

      // Audio Endpoints
      const audioContainer = document.getElementById('diag-audio-container');
      if (audioContainer && data.audio_endpoints) {
        setText('diag-audio-count', `${data.audio_endpoints.length} устр.`);
        if (data.audio_endpoints.length === 0) {
          audioContainer.innerHTML = '<div class="text-center py-4 text-muted small">Аудиоустройств не обнаружено</div>';
        } else {
          audioContainer.innerHTML = data.audio_endpoints.map(a => `
            <div class="p-2 mb-1 rounded bg-black bg-opacity-30 border border-secondary-subtle d-flex align-items-center justify-content-between">
              <div>
                <strong class="text-white"><i class="bi bi-speaker me-1.5 text-warning"></i>${escapeHtml(a.name)}</strong>
                <div class="small text-muted">${escapeHtml(a.type)}</div>
              </div>
              <span class="badge ${a.is_default ? 'bg-info text-dark fw-bold' : 'bg-secondary'}">${a.is_default ? 'По умолчанию' : 'Доступно'}</span>
            </div>
          `).join('');
        }
      }

      // USB PnP Table
      const usbTbody = document.getElementById('diag-usb-tbody');
      if (usbTbody && data.usb_devices) {
        setText('diag-usb-count', `${data.usb_devices.length} устройств`);
        if (data.usb_devices.length === 0) {
          usbTbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">USB устройств не обнаружено</td></tr>';
        } else {
          usbTbody.innerHTML = data.usb_devices.map(u => `
            <tr>
              <td class="fw-bold text-white"><i class="bi bi-usb-symbol text-info me-1.5"></i>${escapeHtml(u.name)}</td>
              <td class="font-monospace text-warning">${escapeHtml(u.vendor_id)}</td>
              <td class="font-monospace text-info">${escapeHtml(u.product_id)}</td>
              <td class="text-muted small">${escapeHtml(u.device_class || 'USB Device')}</td>
              <td><span class="badge ${u.has_problem ? 'bg-danger' : 'bg-success-subtle text-success border border-success'}">${escapeHtml(u.status)}</span></td>
              <td class="small text-muted font-monospace text-truncate" style="max-width: 220px;" title="${escapeHtml(u.device_id)}">${escapeHtml(u.device_id)}</td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.warn('[PeripheralsTab] fetchPeripheralsNetwork error:', err);
    }
  }

  const POLL_ID = 'peripherals';

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
      window.unregisterTabPoller(`tab-peripherals_${POLL_ID}`);
    }
    if (autoRefreshTimer) {
      clearInterval(autoRefreshTimer);
      autoRefreshTimer = null;
    }
  }

  function applyPoller(freq, runInitial = false) {
    stopPolling();
    if (freq === 'start' || freq === 'manual') {
      if (runInitial) fetchPeripheralsNetwork();
      return;
    }

    const intervalSec = parseInt(freq, 10);
    if (isNaN(intervalSec) || intervalSec <= 0) return;

    const intervalMs = intervalSec * 1000;
    const pollerId = `tab-peripherals_${POLL_ID}`;

    if (window.registerTabPoller) {
      window.registerTabPoller('tab-peripherals', fetchPeripheralsNetwork, intervalMs, { pollerId, immediate: runInitial });
    } else {
      if (runInitial) fetchPeripheralsNetwork();
      autoRefreshTimer = setInterval(() => {
        if (window.isTabActive ? window.isTabActive('tab-peripherals') : true) {
          fetchPeripheralsNetwork();
        }
      }, intervalMs);
    }
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('btn-diag-peripherals-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => fetchPeripheralsNetwork();
    }

    const select = document.getElementById('diag-peripherals-poll-freq');
    if (select) {
      select.onchange = (e) => {
        const newFreq = e.target.value;
        setFrequency(newFreq);
        if (newFreq !== 'manual' && newFreq !== 'start') {
          fetchPeripheralsNetwork();
        }
        if (window.showToast) {
          const label = select.options[select.selectedIndex]?.text || newFreq;
          window.showToast(`Частота опроса периферии: ${label}`, 'info');
        }
      };
    }
  }

  async function init() {
    bindEvents();
    const currentFreq = getFrequency();
    const select = document.getElementById('diag-peripherals-poll-freq');
    if (select) select.value = currentFreq;
    applyPoller(currentFreq, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 10);
  }
})();
