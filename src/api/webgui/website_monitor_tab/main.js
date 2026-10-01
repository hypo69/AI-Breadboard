/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/website_monitor_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/website_monitor_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

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
      const diagSummary = document.getElementById('webmon-diag-summaryi18n.t('auto__if_data_technical_if_availel_availel_innertext_data_technical_availability_pct_100_data_technical_avg_latency_ms_0_ms_if_data_search_console_if_ctrel_ctrel_innertext_data_search_console_avg_ctr_0_if_healthel_healthel_innertext_data_health_score_100_100_if_diagtitle_diagtitle_innertext_data_status__104fb0')OK'}`;
      if (diagSummary) diagSummary.innerText = data.summary || i18n.t('auto___22d6f7');
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
          <tr class="webmon-page-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto__ai__87205c')>
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
                icon: '🌐i18n.t('auto__title_p_page_path__01335c')/i18n.t('auto__subtitle_p_screen_page_views_p_views_0_p_active_users_p_users_0_tabletype__e12727')website',
                badges: [
                  { text: `${p.screen_page_views || 0} views`, class: 'badge bg-info text-dark' },
                  { text: `${p.active_users || 0} users`, class: 'badge bg-success' }
                ],
                metadata: [
                  { label: i18n.t('auto_url__7264d7'), value: p.page_path || '/' },
                  { label: i18n.t('auto___5a181e'), value: String(p.screen_page_views || p.views || 0) },
                  { label: i18n.t('auto___5596dd'), value: String(p.active_users || p.users || 0) },
                  { label: i18n.t('auto___65611b'), value: p.bounce_rate ? `${p.bounce_rate}%` : 'N/A' },
                  { label: i18n.t('auto___8a980a'), value: p.avg_session_duration ? `${p.avg_session_duration} сек` : 'N/A' }
                ],
                rawTitle: i18n.t('auto___ae0dfa'),
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
