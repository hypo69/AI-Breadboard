/**
 * =============================================================================
 * Process Name: Windows Process Leak Hunter Logic
 * =============================================================================
 * Description:
 *   Клиентский контроллер вкладки глубокой диагностики процессов:
 *   утечки дескрипторов Handles, GDI/USER объектов, Page Faults и фильтрация.
 *
 * File: main.js
 * Project: AI-Breadboard
 * Module: WebInterface.ProcessLeaksTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

(function () {
  'use strict';

  let rawLeakProcesses = [];
  let leakFilter = 'all';
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

  async function fetchProcessLeaks() {
    try {
      const data = await apiFetch('/api/v1/system/diagnostics/leaks?limit=100');
      if (!data) return;

      setText('diag-leaks-total-proc', data.total_processes);
      setText('diag-leaks-suspicious-count', data.suspicious_count);

      if (data.top_handle_hogs && data.top_handle_hogs.length > 0) {
        const topH = data.top_handle_hogs[0];
        setText('diag-leaks-peak-handles', `${topH.handles_count.toLocaleString()} шт.`);
        setText('diag-leaks-peak-handles-proc', `Процесс: ${topH.name} (PID ${topH.pid})`);
      }
      if (data.top_gdi_hogs && data.top_gdi_hogs.length > 0) {
        const topG = data.top_gdi_hogs[0];
        setText('diag-leaks-peak-gdi', `${topG.gdi_objects.toLocaleString()} шт.`);
        setText('diag-leaks-peak-gdi-proc', `Процесс: ${topG.name} (PID ${topG.pid})`);
      }

      rawLeakProcesses = data.all_processes || [];
      renderProcessLeaksTable(rawLeakProcesses);
    } catch (err) {
      console.warn('[ProcessLeaksTab] fetchProcessLeaks error:', err);
    }
  }

  function renderProcessLeaksTable(processes) {
    const tbody = document.getElementById('diag-leaks-tbody');
    if (!tbody) return;

    const query = (document.getElementById('diag-leaks-search')?.value || '').trim().toLowerCase();

    let filtered = processes.filter(p => {
      if (query && !p.name.toLowerCase().includes(query) && !String(p.pid).includes(query)) {
        return false;
      }
      if (leakFilter === 'suspicious') return p.leak_risk_score !== 'normal';
      if (leakFilter === 'gdi') return p.gdi_objects > 500;
      if (leakFilter === 'handles') return p.handles_count > 1500;
      return true;
    });

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" class="text-center py-4 text-muted">Процессов по заданным критериям не найдено</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map(p => {
      let riskBadge = '<span class="diag-badge-normal">Норма</span>';
      if (p.leak_risk_score === 'critical') {
        riskBadge = '<span class="diag-badge-critical">Критический</span>';
      } else if (p.leak_risk_score === 'warning') {
        riskBadge = '<span class="diag-badge-warning">Внимание</span>';
      }

      const reasons = (p.leak_risk_reasons && p.leak_risk_reasons.length > 0)
        ? p.leak_risk_reasons.map(r => `<span class="badge bg-dark border border-secondary text-warning me-1">${escapeHtml(r)}</span>`).join('')
        : '<span class="text-muted small">Штатное поведение</span>';

      return `
        <tr>
          <td><span class="text-info font-monospace">${p.pid}</span></td>
          <td class="fw-bold text-white text-truncate" style="max-width: 180px;">${escapeHtml(p.name)}</td>
          <td style="text-align: right;" class="${p.handles_count > 1500 ? 'text-danger fw-bold' : 'text-light'}">${p.handles_count.toLocaleString()}</td>
          <td style="text-align: right;" class="${p.gdi_objects > 800 ? 'text-danger fw-bold' : 'text-light'}">${p.gdi_objects.toLocaleString()}</td>
          <td style="text-align: right;" class="${p.user_objects > 400 ? 'text-warning' : 'text-light'}">${p.user_objects.toLocaleString()}</td>
          <td style="text-align: right;" class="text-muted font-monospace">${p.page_faults_total.toLocaleString()}</td>
          <td style="text-align: right;" class="text-warning">${p.memory_mb.toFixed(1)} MB</td>
          <td style="text-align: right;" class="text-muted">${p.threads_count}</td>
          <td>${riskBadge}</td>
          <td>${reasons}</td>
        </tr>
      `;
    }).join('');
  }

  function bindEvents() {
    const leakFilters = document.getElementById('diag-leaks-filter-group');
    if (leakFilters) {
      leakFilters.querySelectorAll('button').forEach(btn => {
        btn.onclick = () => {
          leakFilters.querySelectorAll('button').forEach(b => {
            b.classList.remove('active', 'btn-info', 'btn-danger');
            b.classList.add('btn-outline-secondary');
          });
          const f = btn.getAttribute('data-filter') || 'all';
          btn.classList.add('active', f === 'suspicious' ? 'btn-danger' : 'btn-info');
          btn.classList.remove('btn-outline-secondary');
          leakFilter = f;
          renderProcessLeaksTable(rawLeakProcesses);
        };
      });
    }

    const leakSearch = document.getElementById('diag-leaks-search');
    if (leakSearch) {
      leakSearch.oninput = () => renderProcessLeaksTable(rawLeakProcesses);
    }

    const btnLeaksRefresh = document.getElementById('btn-diag-leaks-refresh');
    if (btnLeaksRefresh) {
      btnLeaksRefresh.onclick = () => fetchProcessLeaks();
    }

    const autoSwitch = document.getElementById('diag-leaks-auto-refresh');
    if (autoSwitch) {
      autoSwitch.onchange = (e) => {
        if (e.target.checked) {
          autoRefreshTimer = setInterval(fetchProcessLeaks, 5000);
        } else if (autoRefreshTimer) {
          clearInterval(autoRefreshTimer);
          autoRefreshTimer = null;
        }
      };
    }
  }

  async function init() {
    bindEvents();
    await fetchProcessLeaks();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 10);
  }
})();
