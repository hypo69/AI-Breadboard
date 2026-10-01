/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/admin_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/admin_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

// System Admin Tab — Central Management Logic

'use strict';

async function initSystemAdminTab() {
  console.log(i18n.t('auto___a221c4'));
  await refreshSystemDashboard();
  await refreshSchedulersConfig();
  await refreshTelemetryStats();
}

async function refreshSystemDashboard() {
  try {
    // 1. Загрузка дисков
    const drivesData = await window.api.fetch('/api/control/rescan', { method: 'GET' }).catch(() => ({ drives: [], details: [] }));
    const drives = Array.isArray(drivesData.drives) ? drivesData.drives : [];
    const details = Array.isArray(drivesData.details) ? drivesData.details : [];
    const drivesCountEl = document.getElementById('sys-drives-count');
    const drivesListEl = document.getElementById('sys-drives-listi18n.t('auto__if_drivescountel_drivescountel_textcontent_drives_length_if_driveslistel_driveslistel_textcontent_drives_join__3ff5a0'), ') || i18n.t('auto___647cdf');

    const detailedContainer = document.getElementById('sys-drives-detailed-container');
    if (detailedContainer) {
      if (details.length === 0 && drives.length === 0) {
        detailedContainer.innerHTML = '<div class="col-12 text-muted small">Накопители не обнаружены или доступ ограничен.</div>';
      } else if (details.length > 0) {
        detailedContainer.innerHTML = details.map(d => {
          const percent = d.percent || 0;
          const barClass = percent > 90 ? 'bg-danger' : percent > 75 ? 'bg-warning' : 'bg-primary';
          return `
            <div class="col-lg-4 col-md-6">
              <div class="card bg-body-tertiary border-secondary-subtle h-100 p-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <span class="fw-bold text-primary"><i class="bi bi-hdd me-1"></i>${d.device || d.mountpoint}</span>
                  <span class="badge bg-secondary-subtle text-body">${d.fstype || 'NTFS'}</span>
                </div>
                <div class="d-flex justify-content-between small text-muted mb-1i18n.t('auto__span_strong_d_used_gb_gb_strong_span_span_strong_d_free_gb_gb_strong_span_div_div_class__983178')progress mb-2" style="height: 8px;">
                  <div class="progress-bar ${barClass}" role="progressbar" style="width: ${percent}%;" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
                <div class="d-flex justify-content-between small text-mutedi18n.t('auto__span_d_total_gb_gb_span_span_class__3ec252')fw-semibold">${percent}%</span>
                </div>
              </div>
            </div>
          `;
        }).join('');
      } else {
        detailedContainer.innerHTML = drives.map(drv => `
          <div class="col-lg-3 col-md-4 col-sm-6">
            <div class="card bg-body-tertiary border-secondary-subtle p-2 text-center">
              <span class="fw-bold text-primary"><i class="bi bi-hdd me-1"></i>${drv}</span>
            </div>
          </div>
        `).join('i18n.t('auto__2_const_pluginsdata_await_window_api_fetch__92fa6f')/api/admin/plugins').catch(() => ({ plugins: [] }));
    const plugins = pluginsData.plugins || [];
    const pluginsCountEl = document.getElementById('sys-plugins-count');
    const pluginsActiveEl = document.getElementById('sys-plugins-active-counti18n.t('auto__const_activecount_plugins_filter_p_p_enabled_length_if_pluginscountel_pluginscountel_textcontent_plugins_length_if_pluginsactiveel_pluginsactiveel_textcontent_activecount_plugins_length_catch_err_console_error__4c417e')Ошибка загрузки системного дашборда:', err);
  }
}

async function rescanStorageDrives() {
  try {
    if (typeof showNotification === 'function') showNotification(i18n.t('auto___3b7943'), 'info');
    const result = await window.api.fetch('/api/control/rescan', { method: 'GET' });
    const drivesList = Array.isArray(result.drives) ? result.drives.join(', ') : 'OK';
    if (typeof showNotification === 'functioni18n.t('auto__shownotification_driveslist__172c39')success');
    await refreshSystemDashboard();
  } catch (e) {
    if (typeof showNotification === 'functioni18n.t('auto__shownotification_e_message__c23014')danger');
  }
}

async function actualizeAiModels() {
  try {
    if (typeof showNotification === 'function') showNotification(i18n.t('auto___cc9c52'), 'info');
    await window.api.fetch('/api/keys/actualize-all', { method: 'POST' }).catch(() => {});
    if (typeof showNotification === 'function') showNotification(i18n.t('auto___897b20'), 'success');
    await refreshSystemDashboard();
  } catch (e) {
    if (typeof showNotification === 'functioni18n.t('auto__shownotification_e_message__c23014')danger');
  }
}

async function refreshTelemetryStats() {
  try {
    const res = await fetch('/api/telemetry/stats?days=30');
    if (!res.ok) return;
    const stats = await res.json();

    // 1. Ngrok Tunnel Status
    const tunnel = stats.tunnel_status || {};
    const badgeEl = document.getElementById('ngrok-status-badge');
    const urlTextEl = document.getElementById('ngrok-public-url-text');
    const alertEl = document.getElementById('ngrok-info-alert');

    if (tunnel.is_active && tunnel.public_url) {
      if (badgeEl) {
        badgeEl.className = 'badge bg-success-subtle text-success';
        badgeEl.textContent = i18n.t('auto___2b2a43');
      }
      if (urlTextEl) {
        urlTextEl.innerHTML = `<a href="${tunnel.public_url}" target="_blank" class="text-success text-decoration-none fw-bold">${tunnel.public_url}</a>`;
      }
      if (alertEl) alertEl.className = 'alert alert-success py-2 px-3 small d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3';
    } else {
      if (badgeEl) {
        badgeEl.className = 'badge bg-danger-subtle text-danger border border-danger-subtle';
        badgeEl.textContent = i18n.t('auto___bff0e2');
      }
      if (urlTextEl) {
        urlTextEl.textContent = i18n.t('auto__launchers_run_ngrok_ps1__28a0a5');
      }
      if (alertEl) alertEl.className = 'alert alert-danger py-2 px-3 small d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3';
    }

    // 2. Event & User metrics
    const totalEl = document.getElementById('telemetry-total-events');
    const usersEl = document.getElementById('telemetry-active-usersi18n.t('auto__if_totalel_totalel_textcontent_stats_total_events_0_tolocalestring_if_usersel_usersel_textcontent_stats_active_users_count_0_3_tab_views_const_tabsel_document_getelementbyid__a12c86')telemetry-tabs-breakdown');
    if (tabsEl) {
      const tabEntries = Object.entries(stats.tab_views || {});
      if (tabEntries.length === 0) {
        tabsEl.innerHTML = '<span class="text-muted">Нет данных</span>';
      } else {
        tabsEl.innerHTML = tabEntries.slice(0, 4).map(([tab, info]) => `
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="badge bg-secondary-subtle text-body">${tab}</span>
            <span class="fw-semibold">${info.count} раз</span>
          </div>
        `).join('');
      }
    }

    // 4. Click actions
    const clicksEl = document.getElementById('telemetry-clicks-breakdown');
    if (clicksEl) {
      const clickEntries = Object.entries(stats.top_clicks || {});
      if (clickEntries.length === 0) {
        clicksEl.innerHTML = '<span class="text-muted">Нет кликов</span>';
      } else {
        clicksEl.innerHTML = clickEntries.slice(0, 4).map(([target, info]) => `
          <div class="d-flex justify-content-between align-items-center mb-1 text-truncate" title="${target}">
            <span class="text-truncate me-1" style="max-width: 140px;">${info.action || target}</span>
            <span class="badge bg-primary-subtle text-primary">${info.count}</span>
          </div>
        `).join('');
      }
    }

    // 5. Recent events table
    const tbody = document.getElementById('telemetry-events-tbody');
    if (tbody) {
      const recent = stats.recent_events || [];
      if (recent.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Пока нет зарегистрированных событий активности.</td></tr>';
      } else {
        tbody.innerHTML = recent.map(ev => {
          const dt = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '-';
          const userName = ev.name || ev.email || `ID ${ev.user_id}`;
          const typeBadge = ev.event_type === 'tab_view' ? 'bg-info-subtle text-info' : ev.event_type === 'click' ? 'bg-primary-subtle text-primary' : 'bg-secondary-subtle text-secondary';
          const durStr = ev.duration_ms > 0 ? `${(ev.duration_ms / 1000).toFixed(1)}s` : '-';
          return `
            <tr>
              <td class="text-muted font-monospace small">${dt}</td>
              <td class="fw-semibold">${userName}</td>
              <td><span class="badge ${typeBadge}">${ev.event_type || 'action'}</span></td>
              <td><span class="badge bg-light text-dark border">${ev.tab_name || '-'}</span></td>
              <td class="text-truncate" style="max-width: 250px;" title="${ev.target_element || ''}">${ev.action || ev.target_element || '-'}</td>
              <td class="text-muted">${durStr}</td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (e) {
    console.debug('Failed to load telemetry stats:', e);
  }
}

function switchToTab(tabName) {
  if (typeof window.switchTab === 'function') {
    window.switchTab(tabName);
    return;
  }
  const cleanName = tabName.replace(/^tab-/, '');
  const triggerEl = document.querySelector(`[data-bs-target="#tab-${cleanName}"], [data-tab="${cleanName}"]`);
  if (triggerEl && typeof bootstrap !== 'undefined' && bootstrap.Tab) {
    const tab = new bootstrap.Tab(triggerEl);
    tab.show();
  }
}

// Schedulers Management Logic
async function refreshSchedulersConfig() {
  try {
    const res = await window.api.fetch('/api/admin/schedulers');
    if (!res || !res.config) return;
    
    const cfg = res.config;
    const status = res.status || {};

    const masterEl = document.getElementById('sched-master-switch');
    const ragEnabledEl = document.getElementById('sched-rag-enabled');
    const ragIntervalEl = document.getElementById('sched-rag-interval');
    const emailEnabledEl = document.getElementById('sched-email-enabled');
    const emailIntervalEl = document.getElementById('sched-email-interval');
    const badgeEl = document.getElementById('sched-main-badge');
    const ragLastRunEl = document.getElementById('sched-rag-last-run');
    const emailLastRunEl = document.getElementById('sched-email-last-run');

    if (masterEl) masterEl.checked = cfg.enabled !== false;
    if (ragEnabledEl) ragEnabledEl.checked = cfg.rag_reindex?.enabled !== false;
    if (ragIntervalEl) ragIntervalEl.value = cfg.rag_reindex?.interval_hours || 24;
    
    if (emailEnabledEl) emailEnabledEl.checked = cfg.email_check?.enabled !== false;
    if (emailIntervalEl) emailIntervalEl.value = cfg.email_check?.interval_minutes || 5;

    if (badgeEl) {
      if (status.running && cfg.enabled) {
        badgeEl.className = 'badge bg-success-subtle text-success';
        badgeEl.textContent = i18n.t('auto___44037b');
      } else {
        badgeEl.className = 'badge bg-secondary-subtle text-secondary';
        badgeEl.textContent = i18n.t('auto___cadea0');
      }
    }

    if (ragLastRunEl) {
      ragLastRunEl.textContent = status.last_rag_run ? new Date(status.last_rag_run).toLocaleString() : i18n.t('auto___f5bf59');
    }
    if (emailLastRunEl) {
      emailLastRunEl.textContent = status.last_email_run ? new Date(status.last_email_run).toLocaleString() : i18n.t('auto___f5bf59');
    }
  } catch (err) {
    console.error(i18n.t('auto___6ab546'), err);
  }
}

async function saveSchedulersConfig() {
  try {
    const masterEl = document.getElementById('sched-master-switch');
    const ragEnabledEl = document.getElementById('sched-rag-enabled');
    const ragIntervalEl = document.getElementById('sched-rag-interval');
    const emailEnabledEl = document.getElementById('sched-email-enabled');
    const emailIntervalEl = document.getElementById('sched-email-interval');

    const payload = {
      enabled: masterEl ? masterEl.checked : true,
      rag_reindex: {
        enabled: ragEnabledEl ? ragEnabledEl.checked : true,
        interval_hours: parseFloat(ragIntervalEl ? ragIntervalEl.value : 24) || 24
      },
      email_check: {
        enabled: emailEnabledEl ? emailEnabledEl.checked : true,
        interval_minutes: parseFloat(emailIntervalEl ? emailIntervalEl.value : 5) || 5
      }
    };

    if (typeof showNotification === 'function') showNotification(i18n.t('auto___2258d5'), 'info');

    const res = await window.api.fetch('/api/admin/schedulers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (typeof showNotification === 'function') {
      showNotification(i18n.t('auto___7be3e0'), 'success');
    }
    await refreshSchedulersConfig();
  } catch (err) {
    if (typeof showNotification === 'functioni18n.t('auto__shownotification_err_message__a712c7')danger');
    }
  }
}

async function triggerSchedulerJob(jobName) {
  try {
    if (typeof showNotification === 'functioni18n.t('auto__shownotification__1090db')${jobName}'...`, 'info');
    }

    const res = await window.api.fetch(`/api/admin/schedulers/trigger/${jobName}`, {
      method: 'POST'
    });

    if (jobName === 'rag') {
      const count = res.result?.updated_count ?? 0;
      if (typeof showNotification === 'functioni18n.t('auto__shownotification_rag_count__e5b479')success');
      }
    } else if (jobName === 'email') {
      const count = res.count ?? 0;
      if (typeof showNotification === 'functioni18n.t('auto__shownotification_count__16072d')success');
      }
    }

    await refreshSchedulersConfig();
  } catch (err) {
    if (typeof showNotification === 'functioni18n.t('auto__shownotification_err_message__988ad4')danger');
    }
  }
}

window.initAdminTab = initSystemAdminTab;
window.rescanStorageDrives = rescanStorageDrives;
window.actualizeAiModels = actualizeAiModels;
window.switchToTab = switchToTab;
window.refreshTelemetryStats = refreshTelemetryStats;
window.refreshSchedulersConfig = refreshSchedulersConfig;
window.saveSchedulersConfig = saveSchedulersConfig;
window.triggerSchedulerJob = triggerSchedulerJob;

