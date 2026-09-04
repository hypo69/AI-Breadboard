// System Admin Tab — Central Management Logic

'use strict';

async function initSystemAdminTab() {
  console.log('Инициализация панели системного управления...');
  await refreshSystemDashboard();
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

function switchToTab(tabName) {
  const triggerEl = document.querySelector(`[data-bs-target="#tab-${tabName}"]`);
  if (triggerEl) {
    const tab = new bootstrap.Tab(triggerEl);
    tab.show();
  }
}

window.initAdminTab = initSystemAdminTab;
window.rescanStorageDrives = rescanStorageDrives;
window.actualizeAiModels = actualizeAiModels;
window.switchToTab = switchToTab;
