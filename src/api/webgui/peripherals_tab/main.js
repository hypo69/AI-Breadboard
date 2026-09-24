/**
 * =============================================================================
 * Process Name: Windows Peripherals & Network Logic
 * =============================================================================
 * Description:
 *   Клиентский контроллер вкладки сети и периферии:
 *   Wi-Fi RF метрики (RSSI, BSSID), аудио устройства и USB PnP дерево.
 *
 * File: main.js
 * Project: AI-Breadboard
 * Module: WebInterface.PeripheralsTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
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

  function bindEvents() {
    const btnRefresh = document.getElementById('btn-diag-peripherals-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => fetchPeripheralsNetwork();
    }

    const autoSwitch = document.getElementById('diag-peripherals-auto-refresh');
    if (autoSwitch) {
      autoSwitch.onchange = (e) => {
        if (e.target.checked) {
          autoRefreshTimer = setInterval(fetchPeripheralsNetwork, 5000);
        } else if (autoRefreshTimer) {
          clearInterval(autoRefreshTimer);
          autoRefreshTimer = null;
        }
      };
    }
  }

  async function init() {
    bindEvents();
    await fetchPeripheralsNetwork();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 10);
  }
})();
