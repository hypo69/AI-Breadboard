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
          disksTbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">Физических накопителей не обнаружено</td></tr>';
        } else {
          const formatBytesLocal = (bytes) => {
            if (bytes == null || bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
          };

          const formatPohLocal = (hours) => {
            if (hours == null || hours <= 0) return null;
            const days = Math.floor(hours / 24);
            const years = (hours / (24 * 365.25)).toFixed(1);
            if (days >= 365) return `${hours.toLocaleString()} ч (≈ ${years} г)`;
            if (days >= 1) return `${hours.toLocaleString()} ч (${days} д)`;
            return `${hours.toLocaleString()} ч`;
          };

          disksTbody.innerHTML = data.disks_wear.map(d => {
            const diskName = d.name || d.model || d.device_id || 'Физический диск';
            const devId = d.device_id ? `<span class="badge bg-secondary-subtle text-light border border-secondary me-1.5">${escapeHtml(d.device_id)}</span>` : '';
            const isSsd = (d.media_type && d.media_type.toUpperCase().includes('SSD')) || (d.bus_type && d.bus_type.toUpperCase().includes('NVME'));
            const diskIcon = isSsd ? 'bi-device-ssd text-info' : 'bi-hdd text-primary';
            const typeBus = [d.media_type, d.bus_type].filter(Boolean).join(' / ') || 'Storage';
            const partsBadge = d.partitions && d.partitions !== '—'
              ? `<span class="badge bg-primary-subtle text-info border border-info-subtle font-monospace">${escapeHtml(d.partitions)}</span>`
              : '<span class="text-muted">—</span>';
            const freeGbStr = d.free_gb != null ? `${d.free_gb} GB` : '<span class="text-muted">—</span>';
            const healthPct = d.health_pct != null ? d.health_pct : 100;
            const healthColor = healthPct >= 80 ? 'success' : (healthPct >= 50 ? 'warning' : 'danger');

            // Наработка и дата первого включения
            const pohFormatted = formatPohLocal(d.power_on_hours);
            const pohHtml = pohFormatted
              ? `<div class="font-monospace text-info">${pohFormatted}</div><div class="small text-muted font-monospace mt-0.5">Старт: ${escapeHtml(d.first_power_on || '—')}</div>`
              : '<span class="text-muted font-monospace small">Сессия ОС</span>';

            // Объемы ввода/вывода (запись и чтение)
            const ioHtml = `
              <div class="font-monospace text-light" title="Записано данных">
                <i class="bi bi-arrow-up-circle text-warning me-1"></i>${formatBytesLocal(d.bytes_written)}
              </div>
              <div class="small font-monospace text-info mt-0.5" title="Прочитано данных">
                <i class="bi bi-arrow-down-circle text-info me-1"></i>${formatBytesLocal(d.bytes_read)}
              </div>
            `;

            return `
            <tr>
              <td class="fw-bold text-white">
                <div class="d-flex align-items-center">
                  <i class="bi ${diskIcon} me-2 fs-6"></i>
                  <div>
                    <div class="text-truncate" style="max-width: 250px;" title="${escapeHtml(diskName)}">${escapeHtml(diskName)}</div>
                    <div class="small text-muted font-monospace mt-0.5">${devId}${d.serial_number && d.serial_number !== 'N/A' ? `<span class="text-secondary">S/N: ${escapeHtml(d.serial_number)}</span>` : ''}</div>
                  </div>
                </div>
              </td>
              <td class="text-muted font-monospace"><span class="badge bg-dark border border-secondary text-light">${escapeHtml(typeBus)}</span></td>
              <td>${partsBadge}</td>
              <td style="text-align: right;" class="text-light font-monospace">${d.total_gb} GB</td>
              <td style="text-align: right;" class="text-success font-monospace">${freeGbStr}</td>
              <td>${pohHtml}</td>
              <td style="text-align: right;">${ioHtml}</td>
              <td>
                <div class="d-flex align-items-center gap-1.5">
                  <div class="about-sys-progress-track flex-grow-1" style="height: 6px; min-width: 55px;">
                    <div class="about-sys-progress-bar bg-${healthColor}" style="width: ${healthPct}%;"></div>
                  </div>
                  <span class="small font-monospace text-${healthColor} ms-1">${healthPct}%</span>
                </div>
              </td>
              <td><span class="badge bg-${healthColor}-subtle text-${healthColor} border border-${healthColor}">${escapeHtml(d.status || 'OK')}</span></td>
            </tr>
          `;}).join('');
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
