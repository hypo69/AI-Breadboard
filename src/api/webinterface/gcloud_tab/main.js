// =============================================================================
// Process Name: Google Cloud Monitor Web Tab Module
// =============================================================================
// Description:
//   Client-side JavaScript controller for the Google Cloud Monitor
//   administrative web interface tab.
//
// File: main.js
// Project: ai-breadboard
// Package: src.api.webinterface.gcloud_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function() {
  let isGcloudInitialized = false;

  async function fetchStatus() {
    try {
      const res = await fetch('/api/gcloud/status');
      if (!res.ok) return;
      const data = await res.json();

      const badge = document.getElementById('gcloud-status-badge');
      const projectEl = document.getElementById('gcloud-project-id');
      const authTypeEl = document.getElementById('gcloud-auth-type');
      const emailEl = document.getElementById('gcloud-client-email');

      if (badge) {
        badge.className = data.authenticated ? 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2' : 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
        badge.innerText = data.authenticated ? (data.is_mock ? '● Mock Режим' : '● GCP Подключен') : '● Не авторизован';
      }

      if (projectEl) projectEl.innerText = data.project_id || 'default-project';
      if (authTypeEl) authTypeEl.innerText = (data.auth_type || 'service_account').toUpperCase();
      if (emailEl) emailEl.innerText = data.client_email || 'local-service-account';
    } catch (e) {
      console.error('[GCloudTab] Failed to fetch status:', e);
    }
  }

  async function fetchLogs() {
    try {
      const res = await fetch('/api/gcloud/logs?limit=40');
      if (!res.ok) return;
      const logs = await res.json();

      const terminal = document.getElementById('gcloud-log-terminal-output');
      const countBadge = document.getElementById('gcloud-logs-count-badge');
      if (countBadge) countBadge.innerText = `${logs.length} строк`;

      if (terminal) {
        if (!Array.isArray(logs) || logs.length === 0) {
          terminal.innerText = 'Журнал Cloud Logging пуст.';
          return;
        }
        terminal.innerHTML = logs.map(l => {
          const sev = (l.severity || 'INFO').toUpperCase();
          const color = sev === 'ERROR' || sev === 'CRITICAL' ? '#f87171' : (sev === 'WARNING' ? '#fbbf24' : '#94a3b8');
          return `<div style="color: ${color};">[${l.timestamp || ''}] [${sev}] ${l.resource_type ? '[' + l.resource_type + '] ' : ''}${l.message || ''}</div>`;
        }).join('');
      }
    } catch (e) {
      console.error('[GCloudTab] Failed to fetch logs:', e);
    }
  }

  async function runDiagnostics() {
    try {
      const res = await fetch('/api/gcloud/diagnostic');
      if (!res.ok) return;
      const report = await res.json();

      const scoreEl = document.getElementById('gcloud-health-score');
      const titleEl = document.getElementById('gcloud-diag-summary-title');
      const descEl = document.getElementById('gcloud-diag-summary-desc');
      const recList = document.getElementById('gcloud-recommendations-list');

      if (scoreEl) scoreEl.innerText = `${report.health_score || 100}/100`;
      if (titleEl) titleEl.innerText = `Статус: ${report.overall_status || 'HEALTHY'}`;
      if (descEl) descEl.innerText = report.summary || 'Все сервисы Google Cloud функционируют в штатном режиме.';

      if (recList && Array.isArray(report.recommendations)) {
        recList.innerHTML = report.recommendations.map(r => `
          <li class="list-group-item bg-transparent text-light border-secondary py-1 px-0">• ${r}</li>
        `).join('');
      }
    } catch (e) {
      console.error('[GCloudTab] Diagnostic error:', e);
    }
  }

  function initGCloudTab() {
    fetchStatus();
    fetchLogs();
    runDiagnostics();

    if (!isGcloudInitialized) {
      const refreshBtn = document.getElementById('btn-gcloud-refresh');
      if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
          fetchStatus();
          fetchLogs();
          runDiagnostics();
        });
      }

      const configBtn = document.getElementById('btn-gcloud-config');
      if (configBtn) {
        configBtn.addEventListener('click', () => {
          if (typeof window.openAppConfigModal === 'function') {
            window.openAppConfigModal('gcloud_monitor');
          }
        });
      }
      isGcloudInitialized = true;
    }
  }

  window.initGCloudTab = initGCloudTab;
})();
