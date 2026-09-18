// =============================================================================
// Process Name: Website Intelligence Monitor Web Tab Module
// =============================================================================
// Description:
//   Client-side JavaScript controller for the Website Intelligence Monitor
//   administrative web interface tab.
//
// File: main.js
// Project: ai-breadboard
// Package: src.api.webinterface.website_monitor_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function() {
  let isWebmonInitialized = false;

  async function fetchRealtime() {
    try {
      const res = await fetch('/api/v1/website-monitor/realtime');
      if (!res.ok) return;
      const data = await res.json();

      const usersEl = document.getElementById('webmon-realtime-users');
      if (usersEl) usersEl.innerText = data.active_users || 0;
    } catch (e) {
      console.error('[WebsiteMonitorTab] Failed to fetch realtime:', e);
    }
  }

  async function fetchSummary() {
    try {
      const res = await fetch('/api/v1/website-monitor/summary');
      if (!res.ok) return;
      const data = await res.json();

      const availEl = document.getElementById('webmon-availability');
      const ctrEl = document.getElementById('webmon-ctr-score');
      const healthEl = document.getElementById('webmon-health-score');
      const diagTitle = document.getElementById('webmon-diag-title');
      const diagSummary = document.getElementById('webmon-diag-summary');

      if (data.technical) {
        if (availEl) availEl.innerText = `${data.technical.availability_pct || 100}% (${data.technical.avg_latency_ms || 0} ms)`;
      }
      if (data.search_console) {
        if (ctrEl) ctrEl.innerText = `${data.search_console.avg_ctr || 0}%`;
      }
      if (healthEl) healthEl.innerText = `${data.health_score || 100}/100`;

      if (diagTitle) diagTitle.innerText = `Статус: ${data.status || 'OK'}`;
      if (diagSummary) diagSummary.innerText = data.summary || 'Все веб-сервисы и каналы трафика функционируют стабильно.';
    } catch (e) {
      console.error('[WebsiteMonitorTab] Failed to fetch summary:', e);
    }
  }

  async function fetchPages() {
    try {
      const res = await fetch('/api/v1/website-monitor/pages?limit=8');
      if (!res.ok) return;
      const pages = await res.json();

      const tbody = document.getElementById('webmon-pages-table-body');
      if (tbody) {
        if (!Array.isArray(pages) || pages.length === 0) {
          tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted p-3">Нет данных о просмотрах.</td></tr>';
          return;
        }
        tbody.innerHTML = pages.map((p, idx) => `
          <tr class="webmon-page-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-анализа страницы">
            <td class="text-info text-truncate" style="max-width: 240px;" title="${p.page_path || '/'}">${p.page_path || '/'}</td>
            <td class="text-end text-light">${p.screen_page_views || p.views || 0}</td>
            <td class="text-end text-secondary">${p.active_users || p.users || 0}</td>
          </tr>
        `).join('');

        tbody.querySelectorAll('.webmon-page-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const p = pages[idx];
            if (!p) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '🌐',
                title: `Веб-страница ${p.page_path || '/'}`,
                subtitle: `Просмотров: ${p.screen_page_views || p.views || 0} | Пользователей: ${p.active_users || p.users || 0}`,
                tableType: 'website',
                badges: [
                  { text: `${p.screen_page_views || 0} views`, class: 'badge bg-info text-dark' },
                  { text: `${p.active_users || 0} users`, class: 'badge bg-success' }
                ],
                metadata: [
                  { label: 'URL / Путь страницы', value: p.page_path || '/' },
                  { label: 'Просмотры страниц', value: String(p.screen_page_views || p.views || 0) },
                  { label: 'Активные пользователи', value: String(p.active_users || p.users || 0) },
                  { label: 'Показатель отказов', value: p.bounce_rate ? `${p.bounce_rate}%` : 'N/A' },
                  { label: 'Средняя длительность', value: p.avg_session_duration ? `${p.avg_session_duration} сек` : 'N/A' }
                ],
                rawTitle: 'Аналитика веб-страницы',
                rawContent: JSON.stringify(p, null, 2),
                requestData: {
                  url: p.page_path,
                  views: p.screen_page_views || p.views,
                  users: p.active_users || p.users
                }
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[WebsiteMonitorTab] Failed to fetch pages:', e);
    }
  }

  async function fetchTrafficSources() {
    try {
      const res = await fetch('/api/v1/website-monitor/traffic-sources');
      if (!res.ok) return;
      const channels = await res.json();

      const container = document.getElementById('webmon-traffic-channels');
      if (container && Array.isArray(channels)) {
        container.innerHTML = channels.slice(0, 5).map(c => `
          <div class="d-flex justify-content-between align-items-center py-1 border-bottom border-secondary-subtle small">
            <span class="text-light">${c.channel_group || c.name || 'Organic'}</span>
            <span class="badge bg-secondary">${c.sessions || c.users || 0} сессий</span>
          </div>
        `).join('');
      }
    } catch (e) {
      console.error('[WebsiteMonitorTab] Failed to fetch traffic sources:', e);
    }
  }

  function initWebsiteMonitorTab() {
    fetchRealtime();
    fetchSummary();
    fetchPages();
    fetchTrafficSources();

    if (!isWebmonInitialized) {
      const refreshBtn = document.getElementById('btn-webmon-refresh');
      if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
          fetchRealtime();
          fetchSummary();
          fetchPages();
          fetchTrafficSources();
        });
      }

      const configBtn = document.getElementById('btn-webmon-config');
      if (configBtn) {
        configBtn.addEventListener('click', () => {
          if (typeof window.openAppConfigModal === 'function') {
            window.openAppConfigModal('website_monitor');
          }
        });
      }
      isWebmonInitialized = true;
    }
  }

  window.initWebsiteMonitorTab = initWebsiteMonitorTab;
})();
