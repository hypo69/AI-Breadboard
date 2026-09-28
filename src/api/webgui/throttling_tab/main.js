/**
 * =============================================================================
 * Process Name: Windows Kernel Quality & Throttling Logic
 * =============================================================================
 * Description:
 *   Клиентский контроллер вкладки качества ядра и троттлинга:
 *   DPC/ISR задержки, PROCHOT троттлинг, PCIe шина GPU и дампы BSOD.
 *
 * File: main.js
 * Project: AI-Breadboard
 * Module: WebInterface.ThrottlingTab
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

  async function fetchKernelThrottling() {
    try {
      const data = await apiFetch('/api/v1/system/diagnostics/throttling');
      if (!data) return;

      setText('diag-dpc-latency-val', `${data.dpc_latency_pct.toFixed(2)}%`);
      const dpcSub = document.getElementById('diag-dpc-latency-sub');
      if (dpcSub) {
        if (data.dpc_status === 'severe') {
          dpcSub.innerHTML = '<span class="badge bg-danger-subtle text-danger border border-danger">Критическая латентность DPC</span>';
        } else if (data.dpc_status === 'elevated') {
          dpcSub.innerHTML = '<span class="badge bg-warning-subtle text-warning border border-warning">Повышенная задержка DPC</span>';
        } else {
          dpcSub.innerHTML = '<span class="badge bg-success-subtle text-success border border-success">Оптимально (< 1.5%)</span>';
        }
      }

      setText('diag-isr-latency-val', `${data.interrupt_latency_pct.toFixed(2)}%`);
      setText('diag-uptime-val', data.uptime_formatted || '--');

      const thVal = document.getElementById('diag-throttling-status-val');
      const thSub = document.getElementById('diag-throttling-status-sub');
      if (thVal && thSub) {
        if (data.thermal_throttling_detected) {
          thVal.textContent = 'PROCHOT Active';
          thVal.className = 'fs-4 fw-bold text-danger mt-1';
          thSub.textContent = i18n.t('auto__cpu_4cc69f');
        } else if (data.power_limit_throttling_detected) {
          thVal.textContent = 'Power Limit PL1/PL2';
          thVal.className = 'fs-4 fw-bold text-warning mt-1';
          thSub.textContent = i18n.t('auto___960395');
        } else {
          thVal.textContent = i18n.t('auto_inactive__592780');
          thVal.className = 'fs-4 fw-bold text-success mt-1';
          thSub.textContent = i18n.t('auto___4ed77a');
        }
      }

      // GPU PCIe Link
      if (data.gpu_pcie_link) {
        setText('diag-gpu-pcie-name', data.gpu_pcie_link.gpu_name || 'GPU Accelerator');
        setText('diag-gpu-pcie-speed', data.gpu_pcie_link.current_link_speed || 'PCIe 3.0 / 4.0');
        setText('diag-gpu-pcie-width', data.gpu_pcie_link.current_link_width || 'x16 Lanes');
        setText('diag-gpu-pcie-status', data.gpu_pcie_link.status || i18n.t('auto___9d07d9'));
      }

      // BSOD Minidump
      const bsodContainer = document.getElementById('diag-bsod-container');
      if (bsodContainer && data.last_bsod_crashes) {
        setText('diag-bsod-count', `${data.last_bsod_crashes.length} сбоев`);
        if (data.last_bsod_crashes.length === 0) {
          bsodContainer.innerHTML = `
            <div class="text-center py-4 text-success small">
              <i class="bi bi-check-circle-fill fs-5 d-block mb-1 text-successi18n.t('auto__i_bsod_minidump_div_else_bsodcontainer_innerhtml_data_last_bsod_crashes_map_c_div_class__41ad74')p-2 mb-1.5 rounded bg-black bg-opacity-40 border border-danger-subtle d-flex align-items-center justify-content-between">
              <div>
                <strong class="text-danger"><i class="bi bi-file-earmark-binary me-1"></i>${escapeHtml(c.file_name)}</strong>
                <div class="small text-muted font-monospace">${escapeHtml(c.timestamp)} (${c.size_kb} KB)</div>
              </div>
              <span class="badge bg-danger">Crash Dump</span>
            </div>
          `).join('');
        }
      }
    } catch (err) {
      console.warn('[ThrottlingTab] fetchKernelThrottling error:', err);
    }
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('btn-diag-throttling-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => fetchKernelThrottling();
    }

    const autoSwitch = document.getElementById('diag-throttling-auto-refresh');
    if (autoSwitch) {
      autoSwitch.onchange = (e) => {
        if (e.target.checked) {
          autoRefreshTimer = setInterval(fetchKernelThrottling, 5000);
        } else if (autoRefreshTimer) {
          clearInterval(autoRefreshTimer);
          autoRefreshTimer = null;
        }
      };
    }
  }

  async function init() {
    bindEvents();
    await fetchKernelThrottling();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 10);
  }
})();
