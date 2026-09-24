/**
 * =============================================================================
 * Process Name: Windows Storage & Battery Wear Logic
 * =============================================================================
 * Description:
 *   Клиентский контроллер вкладки износа накопителей и батареи:
 *   SMART состояние дисков, остаточный ресурс SSD и деградация аккумулятора.
 *
 * File: main.js
 * Project: AI-Breadboard
 * Module: WebInterface.StorageWearTab
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

  async function fetchStorageBatteryWear() {
    try {
      const data = await apiFetch('/api/v1/system/diagnostics/storage-battery');
      if (!data) return;

      // Disks
      const disksTbody = document.getElementById('diag-wear-disks-tbody');
      if (disksTbody && data.disks_wear) {
        setText('diag-wear-disks-count', `${data.disks_wear.length} дисков`);
        if (data.disks_wear.length === 0) {
          disksTbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Разделов накопителей не обнаружено</td></tr>';
        } else {
          disksTbody.innerHTML = data.disks_wear.map(d => `
            <tr>
              <td class="fw-bold text-white"><i class="bi bi-hdd-network text-primary me-1.5"></i>${escapeHtml(d.drive_letter)}</td>
              <td class="text-muted font-monospace">${escapeHtml(d.fstype)}</td>
              <td style="text-align: right;" class="text-light font-monospace">${d.total_gb} GB</td>
              <td style="text-align: right;" class="text-success font-monospace">${d.free_gb} GB</td>
              <td>
                <div class="d-flex align-items-center gap-1.5">
                  <div class="about-sys-progress-track flex-grow-1" style="height: 6px; min-width: 60px;">
                    <div class="about-sys-progress-bar bg-success" style="width: ${d.health_pct}%;"></div>
                  </div>
                  <span class="small font-monospace text-success ms-1">${d.health_pct}%</span>
                </div>
              </td>
              <td><span class="badge bg-success-subtle text-success border border-success">${escapeHtml(d.status)}</span></td>
            </tr>
          `).join('');
        }
      }

      // Battery
      const batContainer = document.getElementById('diag-battery-details-container');
      const batSourceBadge = document.getElementById('diag-battery-source-badge');
      if (batContainer && data.battery_wear) {
        const b = data.battery_wear;
        if (batSourceBadge) {
          batSourceBadge.textContent = b.power_source || 'AC Mains';
        }
        if (!b.has_battery) {
          batContainer.innerHTML = `
            <div class="text-center py-4 text-muted small">
              <i class="bi bi-plug-fill fs-4 text-info d-block mb-1"></i>
              Стационарный компьютер — питание напрямую от электросети
            </div>
          `;
        } else {
          batContainer.innerHTML = `
            <table class="about-sys-spec-table">
              <tbody>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-battery-charging me-1.5 text-warning"></i>Уровень заряда</td>
                  <td class="about-sys-spec-val fw-bold text-white">${b.percent}% (${b.is_charging ? 'Заряжается' : 'Разряд'})</td>
                </tr>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-shield-shaded me-1.5 text-info"></i>Заводская емкость</td>
                  <td class="about-sys-spec-val font-monospace">${b.design_capacity_mwh ? b.design_capacity_mwh + ' mWh' : '--'}</td>
                </tr>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-battery-full me-1.5 text-success"></i>Текущая емкость</td>
                  <td class="about-sys-spec-val font-monospace">${b.full_charge_capacity_mwh ? b.full_charge_capacity_mwh + ' mWh' : '--'}</td>
                </tr>
                <tr>
                  <td class="about-sys-spec-key"><i class="bi bi-heart-pulse me-1.5 text-danger"></i>Деградация (Износ)</td>
                  <td class="about-sys-spec-val ${b.wear_level_pct > 20 ? 'text-danger fw-bold' : 'text-success'}">
                    ${b.wear_level_pct}% износа
                  </td>
                </tr>
              </tbody>
            </table>
          `;
        }
      }
    } catch (err) {
      console.warn('[StorageWearTab] fetchStorageBatteryWear error:', err);
    }
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('btn-diag-wear-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => fetchStorageBatteryWear();
    }

    const autoSwitch = document.getElementById('diag-wear-auto-refresh');
    if (autoSwitch) {
      autoSwitch.onchange = (e) => {
        if (e.target.checked) {
          autoRefreshTimer = setInterval(fetchStorageBatteryWear, 10000);
        } else if (autoRefreshTimer) {
          clearInterval(autoRefreshTimer);
          autoRefreshTimer = null;
        }
      };
    }
  }

  async function init() {
    bindEvents();
    await fetchStorageBatteryWear();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 10);
  }
})();
