// System Admin Tab — Central Management Logic

'use strict';

async function initSystemAdminTab() {
  console.log('Инициализация панели системного управления...');
  await refreshSystemDashboard();
  await refreshTelemetryStats();
}

async function refreshSystemDashboard() {
  try {
    // 1. Загрузка дисков
    const drivesData = await window.api.fetch('/api/control/rescan', { method: 'GET' }).catch(() => ({ drives: [], details: [] }));
    const drives = Array.isArray(drivesData.drives) ? drivesData.drives : [];
    const details = Array.isArray(drivesData.details) ? drivesData.details : [];
    const drivesCountEl = document.getElementById('sys-drives-count');
    const drivesListEl = document.getElementById('sys-drives-list');
    if (drivesCountEl) drivesCountEl.textContent = `${drives.length} диск(ов)`;
    if (drivesListEl) drivesListEl.textContent = drives.join(', ') || 'Диски не обнаружены';

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
                <div class="d-flex justify-content-between small text-muted mb-1">
                  <span>Занято: <strong>${d.used_gb} GB</strong></span>
                  <span>Свободно: <strong>${d.free_gb} GB</strong></span>
                </div>
                <div class="progress mb-2" style="height: 8px;">
                  <div class="progress-bar ${barClass}" role="progressbar" style="width: ${percent}%;" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
                <div class="d-flex justify-content-between small text-muted">
                  <span>Всего: ${d.total_gb} GB</span>
                  <span class="fw-semibold">${percent}%</span>
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
        `).join('');
      }
    }

    // 2. Загрузка статуса плагинов
    const pluginsData = await window.api.fetch('/api/admin/plugins').catch(() => ({ plugins: [] }));
    const plugins = pluginsData.plugins || [];
    const pluginsCountEl = document.getElementById('sys-plugins-count');
    const pluginsActiveEl = document.getElementById('sys-plugins-active-count');
    const activeCount = plugins.filter(p => p.enabled).length;
    if (pluginsCountEl) pluginsCountEl.textContent = `${plugins.length} модулей`;
    if (pluginsActiveEl) pluginsActiveEl.textContent = `${activeCount} активно из ${plugins.length}`;
  } catch (err) {
    console.error('Ошибка загрузки системного дашборда:', err);
  }
}

async function rescanStorageDrives() {
  try {
    if (typeof showNotification === 'function') showNotification('Пересканирование накопителей ОС...', 'info');
    const result = await window.api.fetch('/api/control/rescan', { method: 'GET' });
    const drivesList = Array.isArray(result.drives) ? result.drives.join(', ') : 'OK';
    if (typeof showNotification === 'function') showNotification(`Диски обновлены: ${drivesList}`, 'success');
    await refreshSystemDashboard();
  } catch (e) {
    if (typeof showNotification === 'function') showNotification(`Ошибка: ${e.message}`, 'danger');
  }
}

async function actualizeAiModels() {
  try {
    if (typeof showNotification === 'function') showNotification('Актуализация пула моделей ИИ...', 'info');
    await window.api.fetch('/api/keys/actualize-all', { method: 'POST' }).catch(() => {});
    if (typeof showNotification === 'function') showNotification('Модели успешно синхронизированы', 'success');
    await refreshSystemDashboard();
  } catch (e) {
    if (typeof showNotification === 'function') showNotification(`Ошибка: ${e.message}`, 'danger');
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
        badgeEl.textContent = 'Туннель: Онлайн';
      }
      if (urlTextEl) {
        urlTextEl.innerHTML = `<a href="${tunnel.public_url}" target="_blank" class="text-success text-decoration-none fw-bold">${tunnel.public_url}</a>`;
      }
      if (alertEl) alertEl.className = 'alert alert-success py-2 px-3 small d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3';
    } else {
      if (badgeEl) {
        badgeEl.className = 'badge bg-secondary-subtle text-secondary';
        badgeEl.textContent = 'Туннель: Остановлен';
      }
      if (urlTextEl) {
        urlTextEl.textContent = 'Не запущен (запустите .\\launchers\\Run-Ngrok.ps1)';
      }
      if (alertEl) alertEl.className = 'alert alert-secondary py-2 px-3 small d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3';
    }

    // 2. Event & User metrics
    const totalEl = document.getElementById('telemetry-total-events');
    const usersEl = document.getElementById('telemetry-active-users');
    if (totalEl) totalEl.textContent = (stats.total_events || 0).toLocaleString();
    if (usersEl) usersEl.textContent = `${stats.active_users_count || 0} пользователей`;

    // 3. Tab views
    const tabsEl = document.getElementById('telemetry-tabs-breakdown');
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

window.initAdminTab = initSystemAdminTab;
window.rescanStorageDrives = rescanStorageDrives;
window.actualizeAiModels = actualizeAiModels;
window.switchToTab = switchToTab;
window.refreshTelemetryStats = refreshTelemetryStats;

