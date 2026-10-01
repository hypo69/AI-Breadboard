/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/gcloud_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/gcloud_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

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
        badge.innerText = data.authenticated ? (data.is_mock ? i18n.t('auto__mock__235d2e') : i18n.t('auto__gcp__eddf8b')) : i18n.t('auto___c815fa');
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
      const countBadge = document.getElementById('gcloud-logs-count-badgei18n.t('auto__if_countbadge_countbadge_innertext_logs_length_if_terminal_if_array_isarray_logs_logs_length_0_terminal_innertext__9e2f50')Журнал Cloud Logging пуст.';
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
      const recList = document.getElementById('gcloud-recommendations-listi18n.t('auto__if_scoreel_scoreel_innertext_report_health_score_100_100_if_titleel_titleel_innertext_report_overall_status__25e2fe')HEALTHY'}`;
      if (descEl) descEl.innerText = report.summary || i18n.t('auto__google_cloud__2d1c52');

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
