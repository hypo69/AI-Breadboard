/**
 * =============================================================================
 * Process Name: Windows Log Settings Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля настройки параметров
 *   и иерархического каталога журналов событий Windows по 7 доменам телеметрии.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/log_settings_tab/main.js?v=20261008_v2" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initLogSettingsTab } from '/windows/api/webgui/log_settings_tab/main.js';
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/log_settings_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 02:35:00
 * =============================================================================
 */

const registerTabPoller = window.registerTabPoller || function() {};
const isTabActive = window.isTabActive || (() => true);

let isInitialized = false;
let channelsData = [];
let catalogData = [];
let domainsData = [];
let eventsData = [];
let selectedEvent = null;

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Загрузка сводки по 7 доменам телеметрии
 */
export async function fetchDomainsSummary() {
  if (!isTabActive('tab-log-settings')) return;

  try {
    const res = await fetch('/api/v1/log-settings/domains');
    if (!res.ok) return;
    const data = await res.json();
    domainsData = data.domains || [];

    renderDomainsCards(domainsData);

    const sysmonBadge = document.getElementById('ls-sysmon-badge');
    if (sysmonBadge) {
      if (data.sysmon_installed) {
        sysmonBadge.textContent = 'Sysmon: Активен ✅';
        sysmonBadge.className = 'badge bg-success font-monospace';
      } else {
        sysmonBadge.textContent = 'Sysmon: Не установлен';
        sysmonBadge.className = 'badge bg-secondary font-monospace';
      }
    }

    const totalRecords = domainsData.reduce((acc, d) => acc + (d.total_records || 0), 0);
    const totalRecordsStat = document.getElementById('ls-total-records-stat');
    if (totalRecordsStat) {
      totalRecordsStat.textContent = `Всего в журналах: ${totalRecords.toLocaleString()} записей`;
    }
  } catch (err) {
    console.debug('[LogSettings] Ошибка загрузки доменов:', err);
  }
}

/**
 * Отрисовка карточек 7 доменов телеметрии
 */
function renderDomainsCards(domains) {
  const container = document.getElementById('ls-domains-cards-grid');
  if (!container) return;

  if (!domains || domains.length === 0) {
    container.innerHTML = '<div class="col-12 text-center text-muted py-3">Домены не найдены.</div>';
    return;
  }

  container.innerHTML = domains.map(d => {
    const recordsStr = (d.total_records || 0).toLocaleString();
    const isActive = d.status === 'Active' || d.status === 'Активен';
    const badgeBg = isActive ? 'bg-success' : 'bg-secondary';

    return `
      <div class="col-12 col-sm-6 col-lg-3">
        <div class="card bg-dark text-white border-secondary h-100 shadow-sm p-3 ls-domain-card" data-domain-id="${d.id}" style="cursor: pointer; transition: transform 0.15s ease, border-color 0.15s ease;">
          <div class="d-flex justify-content-between align-items-start mb-1">
            <strong class="text-light fs-6 text-truncate">${escapeHtml(d.title)}</strong>
            <span class="badge ${badgeBg} font-monospace" style="font-size: 0.68rem;">${escapeHtml(d.status)}</span>
          </div>
          <div class="small text-muted mb-2 text-truncate" style="font-size: 0.75rem;" title="${escapeHtml(d.description)}">
            ${escapeHtml(d.description)}
          </div>
          <div class="d-flex justify-content-between align-items-center mt-auto pt-2 border-top border-secondary small font-monospace">
            <span class="text-info">${d.channels_count} каналов</span>
            <span class="text-warning">${recordsStr} записей</span>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // Клик по карточке домена фильтрует каталог
  container.querySelectorAll('.ls-domain-card').forEach(card => {
    card.addEventListener('click', () => {
      const domId = card.dataset.domainId;
      const select = document.getElementById('ls-catalog-domain-select');
      if (select) {
        select.value = domId;
        fetchEventCatalog();
      }
    });
  });
}

/**
 * Загрузка каталога провайдеров
 */
export async function fetchEventCatalog() {
  const domainSelect = document.getElementById('ls-catalog-domain-select');
  const searchInput = document.getElementById('ls-catalog-search-input');

  const domain = domainSelect ? domainSelect.value : '';
  const search = searchInput ? searchInput.value.trim() : '';

  try {
    const params = new URLSearchParams();
    if (domain) params.append('domain', domain);
    if (search) params.append('search', search);

    const res = await fetch(`/api/v1/log-settings/catalog?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    catalogData = data.catalog || [];
    renderCatalogTable(catalogData);
  } catch (err) {
    console.warn('[LogSettings] Ошибка каталога:', err);
  }
}

/**
 * Отрисовка таблицы каталога провайдеров
 */
function renderCatalogTable(catalog) {
  const tbody = document.getElementById('ls-catalog-tbody');
  const countLabel = document.getElementById('ls-catalog-count');
  if (!tbody) return;

  if (countLabel) countLabel.textContent = `${catalog.length} провайдеров`;

  if (!catalog || catalog.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Провайдеры по заданным критериям не найдены.</td></tr>';
    return;
  }

  tbody.innerHTML = catalog.map(e => {
    let volBadge = 'bg-secondary';
    if (e.volume_rating === 'Extreme') volBadge = 'bg-danger';
    else if (e.volume_rating === 'High') volBadge = 'bg-warning text-dark';
    else if (e.volume_rating === 'Medium') volBadge = 'bg-info text-dark';
    else if (e.volume_rating === 'Low') volBadge = 'bg-success';

    const eventsList = Object.entries(e.key_events || {}).map(([id, desc]) => {
      return `<span class="badge bg-black border border-secondary text-warning font-monospace me-1 mb-1" title="${escapeHtml(desc)}">ID ${id}</span>`;
    }).join('');

    const targets = (e.correlation_targets || []).map(t => {
      return `<span class="badge bg-secondary-subtle text-light font-monospace me-1" style="font-size: 0.68rem;">#${escapeHtml(t)}</span>`;
    }).join('');

    return `
      <tr>
        <td>
          <div class="fw-bold text-light font-monospace" style="font-size: 0.8rem;">${escapeHtml(e.provider)}</div>
          <div class="small text-info font-monospace text-truncate" style="max-width: 260px; font-size: 0.72rem;">${escapeHtml(e.channel)}</div>
          <div class="small text-muted text-truncate" style="max-width: 260px; font-size: 0.7rem;" title="${escapeHtml(e.description)}">${escapeHtml(e.description)}</div>
        </td>
        <td>
          <span class="badge bg-dark border border-secondary text-light">${escapeHtml(e.domain_title || e.domain)}</span>
        </td>
        <td>
          <div class="d-flex flex-wrap" style="max-width: 280px;">${eventsList}</div>
        </td>
        <td>
          <span class="badge ${volBadge}">${escapeHtml(e.volume_rating)}</span>
          <div class="small text-muted font-monospace mt-1" style="font-size: 0.7rem;">${(e.record_count || 0).toLocaleString()} rec</div>
        </td>
        <td>
          <div class="small text-light font-monospace">${escapeHtml(e.recommended_collector)}</div>
          <div class="small text-muted" style="font-size: 0.7rem;">
            ${e.realtime_support ? '<span class="text-success">ETW/Stream</span>' : '<span class="text-secondary">Pull</span>'}
            • <span class="text-warning">${escapeHtml(e.privilege_required)}</span>
          </div>
        </td>
        <td>
          <div class="d-flex flex-wrap">${targets}</div>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Загрузка сводки и списка параметров всех каналов
 */
export async function fetchChannelsList() {
  if (!isTabActive('tab-log-settings')) return;

  try {
    const res = await fetch('/api/v1/log-settings/channels');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    channelsData = data.channels || [];
    renderChannelsCards(channelsData);
    renderChannelsTable(channelsData);
  } catch (err) {
    console.warn('[LogSettings] Ошибка загрузки каналов:', err);
  }
}

/**
 * Загрузка статуса политик аудита и сборщика телеметрии
 */
export async function fetchAuditStatus() {
  if (!isTabActive('tab-log-settings')) return;

  try {
    const res = await fetch('/api/v1/log-settings/audit-status');
    if (!res.ok) return;
    const data = await res.json();

    const cmdStatusEl = document.getElementById('ls-cmdline-status');
    const cmdBadgeEl = document.getElementById('ls-audit-cmdline-badge');
    if (cmdStatusEl) {
      cmdStatusEl.textContent = data.cmdline_audit_enabled ? 'Включен ✅' : 'Отключен ⚠️';
      cmdStatusEl.className = `fs-4 fw-bold mt-1 ${data.cmdline_audit_enabled ? 'text-success' : 'text-warning'}`;
    }
    if (cmdBadgeEl) {
      cmdBadgeEl.textContent = data.cmdline_audit_enabled ? 'АКТИВЕН' : 'НЕ АКТИВЕН';
      cmdBadgeEl.className = `badge ${data.cmdline_audit_enabled ? 'bg-success' : 'bg-warning text-dark'}`;
    }

    const bmIdEl = document.getElementById('ls-bookmark-id');
    const bmTimeEl = document.getElementById('ls-bookmark-time');
    const dbEventsBadge = document.getElementById('ls-db-events-badge');
    const bmCurrIdEl = document.getElementById('ls-bm-curr-id');
    const bmDbCountEl = document.getElementById('ls-bm-db-count');

    if (bmIdEl) bmIdEl.textContent = data.last_bookmark_record_id ? `ID: ${data.last_bookmark_record_id.toLocaleString()}` : 'ID: Начало';
    if (bmTimeEl) bmTimeEl.textContent = `Закладка: ${data.last_bookmark_timestamp || 'Не задана'}`;
    if (dbEventsBadge) dbEventsBadge.textContent = `${data.db_security_events_count.toLocaleString()} в БД`;
    if (bmCurrIdEl) bmCurrIdEl.textContent = data.last_bookmark_record_id ? data.last_bookmark_record_id.toLocaleString() : 'Нет (tail)';
    if (bmDbCountEl) bmDbCountEl.textContent = data.db_security_events_count.toLocaleString();

    const privStatusEl = document.getElementById('ls-sec-priv-status');
    if (privStatusEl) {
      if (data.security_channel_accessible) {
        privStatusEl.className = 'alert alert-success border-success p-2 small mb-0 d-flex align-items-center gap-2';
        privStatusEl.innerHTML = '<i class="bi bi-shield-check fs-5"></i><span>Доступ к каналу Security разрешен. Привилегии SeSecurityPrivilege активны.</span>';
      } else {
        privStatusEl.className = 'alert alert-danger border-danger p-2 small mb-0 d-flex align-items-center gap-2';
        privStatusEl.innerHTML = '<i class="bi bi-shield-x fs-5"></i><span>Доступ к каналу Security ограничен. Требуется запуск с правами Администратора.</span>';
      }
    }
  } catch (err) {
    console.debug('[LogSettings] Ошибка проверки аудита:', err);
  }
}

/**
 * Отрисовка верхних карточек
 */
function renderChannelsCards(channels) {
  const sec = channels.find(c => c.channel_name === 'Security') || {};

  const secSizeEl = document.getElementById('ls-sec-size');
  const secProgEl = document.getElementById('ls-sec-progress');
  const secRecordsEl = document.getElementById('ls-sec-records');
  const secStatusEl = document.getElementById('ls-sec-status');

  if (secSizeEl) secSizeEl.textContent = `${sec.file_size_mb || 0} / ${sec.max_size_mb || 20} MB`;
  if (secProgEl) {
    const pct = sec.usage_pct || 0;
    secProgEl.style.width = `${Math.min(100, pct)}%`;
    secProgEl.className = `progress-bar ${pct > 90 ? 'bg-danger' : (pct > 75 ? 'bg-warning' : 'bg-info')}`;
  }
  if (secRecordsEl) secRecordsEl.textContent = `Записей: ${(sec.record_count || 0).toLocaleString()}`;
  if (secStatusEl) secStatusEl.textContent = sec.is_enabled ? 'Активен' : 'Отключен';
}

/**
 * Отрисовка таблицы каналов
 */
function renderChannelsTable(channels) {
  const tbody = document.getElementById('ls-channels-tbody');
  const countLabel = document.getElementById('ls-table-count');
  if (!tbody) return;

  const filterInput = document.getElementById('ls-channel-filter-input');
  const filterQuery = (filterInput ? filterInput.value : '').toLowerCase().trim();

  const filtered = channels.filter(c => {
    if (!filterQuery) return true;
    return c.channel_name.toLowerCase().includes(filterQuery) ||
           (c.description || '').toLowerCase().includes(filterQuery);
  });

  if (countLabel) countLabel.textContent = `${filtered.length} из ${channels.length}`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">Каналы не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(c => {
    const pct = c.usage_pct || 0;
    const isFull = pct >= 95.0;
    const badgeColor = isFull ? 'bg-danger' : (pct > 75 ? 'bg-warning text-dark' : 'bg-success');
    const rotPolicy = c.auto_backup ? 'Auto-Backup (Архивация)' : (c.retention ? 'Retention (Удержание)' : 'FIFO (Перезапись)');

    return `
      <tr>
        <td>
          <div class="fw-bold text-light font-monospace">${escapeHtml(c.channel_name)}</div>
          <div class="small text-muted text-truncate" style="max-width: 280px; font-size: 0.72rem;" title="${escapeHtml(c.description)}">
            ${escapeHtml(c.description || c.log_file_path)}
          </div>
        </td>
        <td>
          <span class="font-monospace text-light">${c.file_size_mb} MB</span>
          <span class="text-muted small">/ ${c.max_size_mb} MB</span>
        </td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <div class="progress flex-grow-1 bg-secondary" style="height: 6px;">
              <div class="progress-bar ${pct > 90 ? 'bg-danger' : (pct > 70 ? 'bg-warning' : 'bg-info')}" style="width: ${Math.min(100, pct)}%;"></div>
            </div>
            <span class="badge ${badgeColor} font-monospace" style="font-size: 0.7rem;">${pct}%</span>
          </div>
        </td>
        <td class="font-monospace text-info">${(c.record_count || 0).toLocaleString()}</td>
        <td class="font-monospace text-secondary small" style="font-size: 0.72rem;">
          ${c.oldest_record_id ? `${c.oldest_record_id.toLocaleString()}..${c.newest_record_id.toLocaleString()}` : '--'}
        </td>
        <td>
          <span class="badge bg-secondary-subtle text-light border border-secondary small" style="font-size: 0.72rem;">${rotPolicy}</span>
        </td>
        <td>
          ${c.is_enabled ? '<span class="badge bg-success">Вкл</span>' : '<span class="badge bg-secondary">Выкл</span>'}
        </td>
        <td class="text-end">
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-info py-0 px-2 ls-btn-config" data-channel="${escapeHtml(c.channel_name)}" title="Настроить параметры">
              <i class="bi bi-gear"></i>
            </button>
            <button class="btn btn-outline-danger py-0 px-2 ls-btn-clear" data-channel="${escapeHtml(c.channel_name)}" title="Очистить журнал">
              <i class="bi bi-trash3"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('.ls-btn-config').forEach(btn => {
    btn.addEventListener('click', () => openConfigModal(btn.dataset.channel));
  });

  tbody.querySelectorAll('.ls-btn-clear').forEach(btn => {
    btn.addEventListener('click', () => openClearModal(btn.dataset.channel));
  });
}

/**
 * Открытие модального окна настройки параметров канала
 */
function openConfigModal(channelName) {
  const channel = channelsData.find(c => c.channel_name === channelName);
  if (!channel) return;

  document.getElementById('ls-modal-channel-name').value = channel.channel_name;
  document.getElementById('ls-modal-channel-title').textContent = channel.channel_name;
  document.getElementById('ls-modal-channel-path').textContent = channel.log_file_path || 'Стандартный путь Winevt\\Logs';
  document.getElementById('ls-modal-maxsize-input').value = channel.max_size_mb || 20;
  document.getElementById('ls-modal-enabled-switch').checked = channel.is_enabled !== false;
  document.getElementById('ls-modal-autobackup-switch').checked = !!channel.auto_backup;
  document.getElementById('ls-modal-retention-switch').checked = !!channel.retention;

  const modalEl = document.getElementById('ls-config-modal');
  if (modalEl && window.bootstrap) {
    const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}

/**
 * Сохранение параметров конфигурации канала
 */
async function saveChannelConfig() {
  const channelName = document.getElementById('ls-modal-channel-name').value;
  const maxSizeMb = parseInt(document.getElementById('ls-modal-maxsize-input').value, 10);
  const isEnabled = document.getElementById('ls-modal-enabled-switch').checked;
  const autoBackup = document.getElementById('ls-modal-autobackup-switch').checked;
  const retention = document.getElementById('ls-modal-retention-switch').checked;

  const saveBtn = document.getElementById('ls-modal-save-btn');
  const origHtml = saveBtn ? saveBtn.innerHTML : '';
  if (saveBtn) saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Сохранение...';

  try {
    const res = await fetch('/api/v1/log-settings/channel/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        channel_name: channelName,
        max_size_mb: maxSizeMb || null,
        is_enabled: isEnabled,
        auto_backup: autoBackup,
        retention: retention,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    if (window.toast) {
      window.toast.success('Параметры обновлены', data.message || `Настройки журнала ${channelName} сохранены.`);
    }

    const modalEl = document.getElementById('ls-config-modal');
    if (modalEl && window.bootstrap) {
      window.bootstrap.Modal.getInstance(modalEl)?.hide();
    }

    await fetchChannelsList();
  } catch (err) {
    if (window.toast) {
      window.toast.error('Ошибка сохранения', err.message);
    }
  } finally {
    if (saveBtn) saveBtn.innerHTML = origHtml;
  }
}

/**
 * Открытие модального окна очистки журнала
 */
function openClearModal(channelName) {
  document.getElementById('ls-clear-modal-channel-name').value = channelName;
  document.getElementById('ls-clear-modal-title').textContent = channelName;

  const nowStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const cleanName = channelName.replace(/[^a-zA-Z0-9]/g, '_');
  document.getElementById('ls-clear-backup-path-input').value = `C:\\Windows\\Temp\\evtx_backup_${cleanName}_${nowStr}.evtx`;

  const modalEl = document.getElementById('ls-clear-modal');
  if (modalEl && window.bootstrap) {
    const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}

/**
 * Подтверждение очистки журнала
 */
async function confirmClearChannel() {
  const channelName = document.getElementById('ls-clear-modal-channel-name').value;
  const withBackup = document.getElementById('ls-clear-backup-checkbox').checked;
  const backupPath = withBackup ? document.getElementById('ls-clear-backup-path-input').value : null;

  const clearBtn = document.getElementById('ls-confirm-clear-btn');
  const origHtml = clearBtn ? clearBtn.innerHTML : '';
  if (clearBtn) clearBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Очистка...';

  try {
    const res = await fetch('/api/v1/log-settings/channel/clear', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        channel_name: channelName,
        backup_path: backupPath,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    if (window.toast) {
      window.toast.success('Журнал очищен', data.message || `Журнал ${channelName} очищен.`);
    }

    const modalEl = document.getElementById('ls-clear-modal');
    if (modalEl && window.bootstrap) {
      window.bootstrap.Modal.getInstance(modalEl)?.hide();
    }

    await fetchChannelsList();
  } catch (err) {
    if (window.toast) {
      window.toast.error('Ошибка очистки', err.message);
    }
  } finally {
    if (clearBtn) clearBtn.innerHTML = origHtml;
  }
}

/**
 * Переключение аудита CommandLine в реестре
 */
async function toggleCmdlineAudit(enable = true) {
  try {
    const res = await fetch('/api/v1/log-settings/audit-status/cmdline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: enable }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    if (window.toast) {
      window.toast.success('Политика обновлена', data.message);
    }
    await fetchAuditStatus();
  } catch (err) {
    if (window.toast) {
      window.toast.error('Ошибка изменения политики', err.message);
    }
  }
}

/**
 * Запуск инкрементального сбора в telemetry.db
 */
async function runCollector() {
  const batchSelect = document.getElementById('ls-collect-batch-size');
  const batchSize = batchSelect ? batchSelect.value : 500;
  const banner = document.getElementById('ls-collector-result-banner');

  const btn = document.getElementById('ls-run-collector-btn');
  const origHtml = btn ? btn.innerHTML : '';
  if (btn) btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Сбор...';

  try {
    const res = await fetch(`/api/v1/log-settings/collector/collect?limit=${batchSize}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    if (banner) {
      banner.className = 'small mt-2 text-success';
      banner.textContent = data.message || `Собрано ${data.total_events_ingested} событий.`;
      banner.classList.remove('d-none');
    }

    if (window.toast) {
      window.toast.success('Телеметрия обновлена', data.message);
    }

    await fetchAuditStatus();
    await fetchDomainsSummary();
  } catch (err) {
    if (banner) {
      banner.className = 'small mt-2 text-danger';
      banner.textContent = `Ошибка сбора: ${err.message}`;
      banner.classList.remove('d-none');
    }
    if (window.toast) {
      window.toast.error('Ошибка сбора', err.message);
    }
  } finally {
    if (btn) btn.innerHTML = origHtml;
  }
}

/**
 * Сброс закладки
 */
async function resetBookmark(customRecordId = null) {
  try {
    const res = await fetch('/api/v1/log-settings/collector/reset-bookmark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel: 'Security', record_id: customRecordId }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    if (window.toast) {
      window.toast.success('Закладка сброшена', data.message);
    }
    await fetchAuditStatus();
  } catch (err) {
    if (window.toast) {
      window.toast.error('Ошибка сброса закладки', err.message);
    }
  }
}

/**
 * Построение графа происхождения процессов (Process Provenance Graph)
 */
export async function buildProcessProvenance() {
  const input = document.getElementById('ls-prov-process-input');
  const processName = input ? input.value.trim() : '';
  const container = document.getElementById('ls-prov-tree-view');
  if (!container) return;

  container.innerHTML = '<div class="text-center text-warning py-4"><div class="spinner-border spinner-border-sm me-2"></div>Построение графа происхождения процессов...</div>';

  try {
    const params = new URLSearchParams();
    if (processName) params.append('process_name', processName);
    params.append('hours', '72');

    const res = await fetch(`/api/v1/log-settings/provenance/process?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const nodes = data.nodes || [];
    const links = data.links || [];

    if (nodes.length === 0) {
      container.innerHTML = `
        <div class="text-center text-muted py-5">
          <i class="bi bi-info-circle fs-3 text-secondary d-block mb-2"></i>
          События создания процессов (Event 4688) для <strong>${escapeHtml(processName || 'хоста')}</strong> не найдены в telemetry.db.<br>
          <small class="text-secondary">Убедитесь, что аудит CommandLine включен и выполнен сбор новых событий.</small>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="mb-3 d-flex justify-content-between align-items-center">
        <span class="badge bg-warning text-dark font-monospace">${nodes.length} Узлов (Nodes)</span>
        <span class="badge bg-info text-dark font-monospace">${links.length} Связей (Spawns / Forks)</span>
      </div>
      <div class="d-flex flex-column gap-2">
        ${nodes.map(n => {
          let typeBadge = 'bg-primary';
          if (n.type === 'parent_process') typeBadge = 'bg-info text-dark';
          else if (n.type === 'service') typeBadge = 'bg-success';

          return `
            <div class="p-2 bg-dark rounded border border-secondary d-flex align-items-center justify-content-between flex-wrap gap-2">
              <div class="d-flex align-items-center gap-2">
                <span class="badge ${typeBadge} font-monospace" style="font-size: 0.72rem;">${escapeHtml(n.role || n.type)}</span>
                <strong class="text-light font-monospace">${escapeHtml(n.name)}</strong>
                ${n.pid ? `<span class="badge bg-secondary font-monospace">PID ${n.pid}</span>` : ''}
              </div>
              <div class="small text-muted font-monospace">${escapeHtml(n.user || '')} • ${escapeHtml(n.timestamp || '')}</div>
              ${n.command_line ? `<div class="w-100 bg-black p-1.5 rounded font-monospace small text-success text-break" style="font-size: 0.72rem;">${escapeHtml(n.command_line)}</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="text-center text-danger py-4">Ошибка: ${escapeHtml(err.message)}</div>`;
  }
}

/**
 * Загрузка жизненного цикла ОС (Power / Boot / Crash Timeline)
 */
export async function fetchPowerLifecycle() {
  const select = document.getElementById('ls-lifecycle-hours-select');
  const hours = select ? select.value : 72;
  const container = document.getElementById('ls-lifecycle-timeline');
  if (!container) return;

  container.innerHTML = '<div class="text-center text-muted py-4"><div class="spinner-border spinner-border-sm text-danger me-2"></div>Реконструкция жизненного цикла ОС...</div>';

  try {
    const res = await fetch(`/api/v1/log-settings/lifecycle/power?hours=${hours}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const timeline = data.timeline || [];

    if (timeline.length === 0) {
      container.innerHTML = '<div class="text-center text-muted py-4">События жизненного цикла за указанный период не найдены.</div>';
      return;
    }

    container.innerHTML = timeline.map(item => {
      let badgeClass = 'border-info text-info';
      if (item.severity === 'critical') badgeClass = 'border-danger text-danger bg-danger-subtle';
      else if (item.severity === 'warning') badgeClass = 'border-warning text-warning bg-warning-subtle';

      return `
        <div class="mb-3 position-relative pb-2 border-bottom border-secondary">
          <div class="d-flex align-items-center gap-2 mb-1">
            <span class="fs-5">${item.icon}</span>
            <span class="badge border ${badgeClass} font-monospace" style="font-size: 0.72rem;">${escapeHtml(item.phase)}</span>
            <span class="badge bg-dark border border-secondary font-monospace" style="font-size: 0.72rem;">ID ${item.event_id}</span>
            <span class="small text-secondary font-monospace ms-auto">${escapeHtml(item.timestamp)}</span>
          </div>
          <div class="text-light small fw-medium">${escapeHtml(item.message)}</div>
          <div class="text-muted font-monospace small" style="font-size: 0.72rem;">Источник: ${escapeHtml(item.provider)}</div>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<div class="text-center text-danger py-4">Ошибка: ${escapeHtml(err.message)}</div>`;
  }
}

/**
 * Загрузка событий для инспектора
 */
export async function fetchInspectorEvents() {
  const channelSelect = document.getElementById('ls-insp-channel-select');
  const levelSelect = document.getElementById('ls-insp-level-select');
  const userInput = document.getElementById('ls-insp-user-input');
  const processInput = document.getElementById('ls-insp-process-input');
  const searchInput = document.getElementById('ls-insp-search-input');

  const channel = channelSelect ? channelSelect.value : 'Security';
  const level = levelSelect ? levelSelect.value : '';
  const user = userInput ? userInput.value.trim() : '';
  const process = processInput ? processInput.value.trim() : '';
  const search = searchInput ? searchInput.value.trim() : '';

  const activeEidBtn = document.querySelector('.ls-quick-eid-btn.active');
  const eventId = activeEidBtn ? parseInt(activeEidBtn.dataset.eid, 10) || 0 : 0;

  const tbody = document.getElementById('ls-events-tbody');
  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Загрузка событий...</td></tr>';
  }

  try {
    const params = new URLSearchParams({
      channel: channel,
      event_id: eventId,
      level: level,
      user: user,
      process: process,
      search: search,
      limit: 100,
    });

    const res = await fetch(`/api/v1/log-settings/events?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    eventsData = data.events || [];
    renderInspectorEvents(eventsData);
  } catch (err) {
    console.warn('[LogSettings] Ошибка чтения событий:', err);
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-4">Ошибка: ${escapeHtml(err.message)}</td></tr>`;
    }
  }
}

/**
 * Отрисовка списка событий в инспекторе
 */
function renderInspectorEvents(events) {
  const tbody = document.getElementById('ls-events-tbody');
  const countLabel = document.getElementById('ls-events-count-label');
  if (!tbody) return;

  if (countLabel) countLabel.textContent = `Событий: ${events.length}`;

  if (events.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">События по заданным фильтрам не найдены.</td></tr>';
    return;
  }

  tbody.innerHTML = events.map((ev, idx) => {
    const eid = ev.event_id || 0;
    const lvl = ev.level || 'Information';
    const ts = ev.timestamp || '';
    const msg = ev.message || ev.raw_data || '';
    const proc = ev.process_name || ev.provider || '';

    let lvlBadge = 'bg-secondary';
    if (lvl === 'Error' || lvl === 'Critical') lvlBadge = 'bg-danger';
    else if (lvl === 'Warning') lvlBadge = 'bg-warning text-dark';
    else if (lvl === 'Information') lvlBadge = 'bg-info text-dark';

    return `
      <tr class="ls-event-row" data-index="${idx}" style="cursor: pointer;">
        <td class="font-monospace text-secondary text-truncate" style="max-width: 140px;">${escapeHtml(ts)}</td>
        <td>
          <span class="badge bg-dark border border-secondary font-monospace">${eid}</span>
        </td>
        <td>
          <span class="badge ${lvlBadge} small" style="font-size: 0.7rem;">${escapeHtml(lvl)}</span>
        </td>
        <td>
          <div class="text-truncate text-light fw-medium" style="max-width: 320px;" title="${escapeHtml(msg)}">${escapeHtml(msg)}</div>
          ${proc ? `<div class="small text-muted text-truncate font-monospace" style="font-size: 0.72rem;">${escapeHtml(proc)}</div>` : ''}
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('.ls-event-row').forEach(row => {
    row.addEventListener('click', () => {
      tbody.querySelectorAll('.ls-event-row').forEach(r => r.classList.remove('table-active'));
      row.classList.add('table-active');
      const idx = parseInt(row.dataset.index, 10);
      showEventDetail(eventsData[idx]);
    });
  });

  if (events.length > 0) {
    const firstRow = tbody.querySelector('.ls-event-row');
    if (firstRow) firstRow.classList.add('table-active');
    showEventDetail(events[0]);
  }
}

/**
 * Отображение подробных сведений о событии в панели инспектора
 */
function showEventDetail(ev) {
  if (!ev) return;
  selectedEvent = ev;

  const emptyEl = document.getElementById('ls-detail-empty');
  const contentEl = document.getElementById('ls-detail-content');
  if (emptyEl) emptyEl.classList.add('d-none');
  if (contentEl) contentEl.classList.remove('d-none');

  document.getElementById('ls-detail-eid-badge').textContent = `ID ${ev.event_id || 0}`;
  document.getElementById('ls-detail-time').textContent = ev.timestamp || '--';
  document.getElementById('ls-detail-user').textContent = ev.subject_user || ev.target_user || (ev.event_data?.SubjectUserName || ev.event_data?.TargetUserName || 'SYSTEM / N/A');
  
  const procName = ev.process_name || ev.event_data?.NewProcessName || ev.provider || '--';
  const pid = ev.process_id || ev.event_data?.NewProcessId || '';
  document.getElementById('ls-detail-process').textContent = pid ? `${procName} (PID ${pid})` : procName;

  const cmdLine = ev.command_line || ev.event_data?.CommandLine || 'Не зафиксирована или аудит CommandLine выключен';
  document.getElementById('ls-detail-cmdline').textContent = cmdLine;

  const parent = ev.parent_process_name || ev.event_data?.ParentProcessName || (ev.parent_process_id ? `PID ${ev.parent_process_id}` : '--');
  document.getElementById('ls-detail-parent').textContent = parent;

  document.getElementById('ls-detail-msg').textContent = ev.message || '--';
  document.getElementById('ls-detail-raw').textContent = JSON.stringify(ev, null, 2);
}

/**
 * Инициализация всех слушателей и элементов вкладки
 */
export function initLogSettingsTab() {
  if (isInitialized) return;
  isInitialized = true;

  // Кнопка обновления всех параметров
  document.getElementById('ls-refresh-all-btn')?.addEventListener('click', () => {
    fetchDomainsSummary();
    fetchEventCatalog();
    fetchChannelsList();
    fetchAuditStatus();
  });

  document.getElementById('ls-reload-channels-btn')?.addEventListener('click', () => fetchChannelsList());

  // Поиск по списку каналов
  document.getElementById('ls-channel-filter-input')?.addEventListener('input', () => {
    renderChannelsTable(channelsData);
  });

  // Фильтры каталога провайдеров
  document.getElementById('ls-catalog-domain-select')?.addEventListener('change', fetchEventCatalog);
  document.getElementById('ls-catalog-search-input')?.addEventListener('input', fetchEventCatalog);

  // Provenance граф
  document.getElementById('ls-prov-build-btn')?.addEventListener('click', buildProcessProvenance);

  // Хронология жизненного цикла
  document.getElementById('ls-lifecycle-hours-select')?.addEventListener('change', fetchPowerLifecycle);
  document.getElementById('ls-lifecycle-reload-btn')?.addEventListener('click', fetchPowerLifecycle);

  // Пресеты размеров в модальном окне
  document.querySelectorAll('.ls-preset-size-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const mb = btn.dataset.mb;
      const input = document.getElementById('ls-modal-maxsize-input');
      if (input) input.value = mb;
    });
  });

  // Сохранение конфигурации канала
  document.getElementById('ls-modal-save-btn')?.addEventListener('click', saveChannelConfig);

  // Очистка канала
  document.getElementById('ls-confirm-clear-btn')?.addEventListener('click', confirmClearChannel);
  document.getElementById('ls-clear-backup-checkbox')?.addEventListener('change', (e) => {
    const pathGroup = document.getElementById('ls-clear-backup-path-group');
    if (pathGroup) pathGroup.style.display = e.target.checked ? 'flex' : 'none';
  });

  // Управление аудитом CommandLine
  document.getElementById('ls-toggle-cmdline-btn')?.addEventListener('click', async () => {
    const isCurrentlyEnabled = document.getElementById('ls-cmdline-status')?.textContent.includes('Включен');
    await toggleCmdlineAudit(!isCurrentlyEnabled);
  });
  document.getElementById('ls-enable-cmdline-btn')?.addEventListener('click', () => toggleCmdlineAudit(true));
  document.getElementById('ls-disable-cmdline-btn')?.addEventListener('click', () => toggleCmdlineAudit(false));

  // Управление сборщиком
  document.getElementById('ls-collect-btn')?.addEventListener('click', runCollector);
  document.getElementById('ls-run-collector-btn')?.addEventListener('click', runCollector);

  // Сброс закладки
  document.getElementById('ls-reset-bm-btn')?.addEventListener('click', () => resetBookmark(null));
  document.getElementById('ls-set-custom-bm-btn')?.addEventListener('click', () => {
    const val = document.getElementById('ls-custom-record-id-input')?.value;
    const num = val ? parseInt(val, 10) : null;
    resetBookmark(num);
  });

  // Быстрые фильтры Event ID
  document.querySelectorAll('.ls-quick-eid-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ls-quick-eid-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      fetchInspectorEvents();
    });
  });

  // Инспектор событий
  document.getElementById('ls-insp-fetch-btn')?.addEventListener('click', fetchInspectorEvents);
  document.getElementById('ls-insp-channel-select')?.addEventListener('change', fetchInspectorEvents);
  document.getElementById('ls-insp-level-select')?.addEventListener('change', fetchInspectorEvents);

  // Первоначальная загрузка
  fetchDomainsSummary();
  fetchEventCatalog();
  fetchChannelsList();
  fetchAuditStatus();
  fetchPowerLifecycle();

  // Регистрация поллера (каждые 20 секунд при активной вкладке)
  registerTabPoller('tab-log-settings', () => {
    fetchDomainsSummary();
    fetchChannelsList();
    fetchAuditStatus();
  }, 20000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLogSettingsTab);
} else {
  initLogSettingsTab();
}
