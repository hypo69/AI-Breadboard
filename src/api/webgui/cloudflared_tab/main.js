// =============================================================================
// Process Name: Cloudflared Monitor Web Tab Module
// =============================================================================
// Description:
//   Client-side JavaScript controller for the Cloudflare Tunnel Monitor
//   administrative web interface tab.
//
// File: main.js
// Project: ai-breadboard
// Package: src.api.webinterface.cloudflared_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function() {
  let isCfInitialized = false;

  async function fetchTunnelStatus() {
    try {
      const res = await fetch('/api/cloudflared/status');
      if (!res.ok) return;
      const data = await res.json();
      
      const badge = document.getElementById('cf-daemon-badge');
      const ingressEl = document.getElementById('cf-ingress-url');
      const endpointEl = document.getElementById('cf-endpoint-status');
      const usageEl = document.getElementById('cf-process-usage');
      const healthEl = document.getElementById('cf-health-score');

      if (badge) {
        badge.className = data.daemon_running ? 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2' : 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
        badge.innerText = data.daemon_running ? '● Туннель активен' : '● Туннель остановлен';
      }

      if (ingressEl) ingressEl.innerText = data.public_url || 'https://kino.davidka.net';
      if (endpointEl) {
        endpointEl.innerText = data.endpoint_reachable ? `Доступен (${data.latency_ms || 0} ms)` : 'Недоступен';
        endpointEl.className = data.endpoint_reachable ? 'cf-value text-success' : 'cf-value text-danger';
      }
      if (usageEl) {
        usageEl.innerText = `${data.cpu_percent || 0}% / ${data.memory_mb || 0} MB`;
      }
      if (healthEl) {
        healthEl.innerText = `${data.health_score || 100}/100`;
      }
    } catch (e) {
      console.error('[CloudflaredTab] Failed to fetch status:', e);
    }
  }

  async function fetchLogs() {
    try {
      const res = await fetch('/api/cloudflared/logs?limit=50');
      if (!res.ok) return;
      const data = await res.json();
      const logs = data.logs || [];
      
      const terminal = document.getElementById('cf-log-terminal-output');
      const countBadge = document.getElementById('cf-log-count-badge');
      if (countBadge) countBadge.innerText = `${logs.length} строк`;

      if (terminal) {
        if (logs.length === 0) {
          terminal.innerText = 'Журнал cloudflared пуст.';
          return;
        }
        terminal.innerHTML = logs.map(l => {
          const color = l.level === 'error' ? '#f87171' : (l.level === 'warn' ? '#fbbf24' : '#94a3b8');
          return `<div style="color: ${color};">[${l.time || ''}] [${(l.level || 'INFO').toUpperCase()}] ${l.msg || l.message || ''}</div>`;
        }).join('');
      }
    } catch (e) {
      console.error('[CloudflaredTab] Failed to fetch logs:', e);
    }
  }

  async function runDiagnostics() {
    try {
      const res = await fetch('/api/cloudflared/diagnostic');
      if (!res.ok) return;
      const report = await res.json();

      const titleEl = document.getElementById('cf-diag-summary-title');
      const descEl = document.getElementById('cf-diag-summary-desc');
      const recList = document.getElementById('cf-recommendations-list');

      if (titleEl) titleEl.innerText = `Здоровье: ${report.status || 'OK'} (${report.health_score || 100}/100)`;
      if (descEl) descEl.innerText = report.summary || 'Все туннельные соединения стабильны.';

      if (recList && Array.isArray(report.recommendations)) {
        recList.innerHTML = report.recommendations.map(r => `
          <li class="list-group-item bg-transparent text-light border-secondary py-1 px-0">• ${r}</li>
        `).join('');
      }
    } catch (e) {
      console.error('[CloudflaredTab] Diagnostic error:', e);
    }
  }

  function initCloudflaredTab() {
    console.log('[CloudflaredTab] Initializing Cloudflared Monitor tab...');
    fetchTunnelStatus();
    fetchLogs();

    if (!isCfInitialized) {
      const refreshBtn = document.getElementById('btn-cf-refresh');
      const configBtn = document.getElementById('btn-cf-config');
      const diagBtn = document.getElementById('btn-cf-run-diagnostics');
      const testBtn = document.getElementById('btn-cf-test-endpoint');

      if (refreshBtn) {
        refreshBtn.onclick = () => {
          fetchTunnelStatus();
          fetchLogs();
        };
      }

      if (diagBtn) diagBtn.onclick = runDiagnostics;

      if (testBtn) {
        testBtn.onclick = async () => {
          testBtn.disabled = true;
          testBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Проверка...';
          try {
            const res = await fetch('/api/cloudflared/test-endpoint');
            const data = await res.json();
            const msg = `Результат проверки Ingress:\nДоступен: ${data.reachable ? 'ДА' : 'НЕТ'}\nКод ответа: ${data.status_code || 'N/A'}\nЗадержка: ${data.response_time_ms || 0} ms`;
            window.showToast?.(msg, data.reachable ? 'success' : 'warning') || alert(msg);
          } catch (e) {
            window.showToast?.('Ошибка проверки эндпоинта: ' + e.message, 'danger') || alert('Ошибка проверки эндпоинта: ' + e.message);
          } finally {
            testBtn.disabled = false;
            testBtn.innerHTML = '<i class="bi bi-broadcast me-1"></i> Проверить Ingress';
            fetchTunnelStatus();
          }
        };
      }

      if (configBtn) {
        configBtn.onclick = () => {
          if (typeof window.openAppConfigModal === 'function') {
            window.openAppConfigModal('cloudflared_monitor', 'Cloudflare Tunnel Monitor');
          }
        };
      }

      isCfInitialized = true;
    }
  }

  window.initCloudflaredTab = initCloudflaredTab;
})();
