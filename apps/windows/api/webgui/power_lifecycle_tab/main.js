/**
 * =============================================================================
 * Process Name: Windows Web Interface - Power Lifecycle Tab Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом вкладки Power Lifecycle:
 *   выборка и визуализация реконструированных сессий питания, аптайма,
 *   истории перезагрузок (1074, 41, 6008) и ключевых системных событий.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/html/power_lifecycle_tab/main.js?v=20261008_v2" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/power_lifecycle_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 04:25:00
 * =============================================================================
 */

let allSessions = [];
let allEvents = [];
let uptimeSeconds = 0;
let uptimeInterval = null;

/**
 * Инициализирует вкладку жизненного цикла питания.
 */
export async function initPowerLifecycleTab() {
  setupEventListeners();
  await loadPowerData();
  startUptimeCounter();
}

/**
 * Устанавливает слушатели событий элементов управления.
 */
function setupEventListeners() {
  const refreshBtn = document.getElementById('pwr-refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      refreshBtn.disabled = true;
      refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Обновление...';
      try {
        await loadPowerData();
        if (window.toast) window.toast.success('Обновлено', 'Данные сессий питания успешно обновлены');
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i><span>Обновить данные</span>';
      }
    });
  }

  const rebuildBtn = document.getElementById('pwr-rebuild-btn');
  if (rebuildBtn) {
    rebuildBtn.addEventListener('click', async () => {
      rebuildBtn.disabled = true;
      rebuildBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Сканирование...';
      try {
        const res = await fetch('/api/v1/power/rebuild', { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderSummary(data);
        await loadPowerData();
        if (window.toast) window.toast.success('Event Log пересканирован', `Реконструировано сессий: ${data.total_sessions_count}`);
      } catch (err) {
        console.error('[PowerLifecycle] Ошибка пересканирования:', err);
        if (window.toast) window.toast.error('Ошибка', 'Не удалось пересканировать журналы: ' + err.message);
      } finally {
        rebuildBtn.disabled = false;
        rebuildBtn.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i><span>Пересканировать Event Log</span>';
      }
    });
  }

  // Фильтры сессий
  const sessionsSearch = document.getElementById('pwr-sessions-search');
  if (sessionsSearch) {
    sessionsSearch.addEventListener('input', () => filterAndRenderSessions());
  }

  const filterType = document.getElementById('pwr-filter-type');
  if (filterType) {
    filterType.addEventListener('change', () => filterAndRenderSessions());
  }

  const filterUnexpected = document.getElementById('pwr-filter-unexpected-only');
  if (filterUnexpected) {
    filterUnexpected.addEventListener('change', () => filterAndRenderSessions());
  }

  // Фильтры событий
  const eventsSearch = document.getElementById('pwr-events-search');
  if (eventsSearch) {
    eventsSearch.addEventListener('input', () => filterAndRenderEvents());
  }

  const filterEid = document.getElementById('pwr-event-id-filter');
  if (filterEid) {
    filterEid.addEventListener('change', () => filterAndRenderEvents());
  }
}

/**
 * Загружает сводку, сессии и события через API.
 */
async function loadPowerData() {
  try {
    // 1. Сводка
    const sumRes = await fetch('/api/v1/power/summary');
    if (sumRes.ok) {
      const summary = await sumRes.json();
      renderSummary(summary);
    }

    // 2. Сессии
    const sessRes = await fetch('/api/v1/power/sessions?limit=100');
    if (sessRes.ok) {
      allSessions = await sessRes.json();
      filterAndRenderSessions();
    }

    // 3. События
    const evRes = await fetch('/api/v1/power/events?limit=200');
    if (evRes.ok) {
      allEvents = await evRes.json();
      filterAndRenderEvents();
    }
  } catch (err) {
    console.error('[PowerLifecycle] Ошибка загрузки данных:', err);
  }
}

/**
 * Отрисовывает верхние карточки сводки.
 * @param {Object} summary
 */
function renderSummary(summary) {
  if (!summary) return;

  const curBootEl = document.getElementById('pwr-current-boot');
  if (curBootEl) curBootEl.textContent = `Загрузка: ${summary.current_boot_time || '--'}`;

  const curUptimeEl = document.getElementById('pwr-current-uptime');
  if (curUptimeEl) {
    curUptimeEl.textContent = summary.current_uptime_human || '--';
    uptimeSeconds = summary.current_uptime_seconds || 0;
  }

  const totalSessionsEl = document.getElementById('pwr-total-sessions');
  if (totalSessionsEl) totalSessionsEl.textContent = summary.total_sessions_count;

  const totalBadge = document.getElementById('pwr-total-sessions-badge');
  if (totalBadge) totalBadge.textContent = `${summary.total_sessions_count} Сессий`;

  const cleanCountEl = document.getElementById('pwr-clean-count');
  if (cleanCountEl) cleanCountEl.textContent = summary.clean_shutdowns_count;

  const cleanRatioEl = document.getElementById('pwr-clean-ratio');
  if (cleanRatioEl) {
    const total = summary.total_sessions_count || 1;
    const ratio = Math.round((summary.clean_shutdowns_count / total) * 100);
    cleanRatioEl.textContent = `${ratio} %`;
  }

  const lastInitEl = document.getElementById('pwr-last-initiator');
  if (lastInitEl) {
    lastInitEl.textContent = `Инициатор: ${summary.last_initiator || 'Штатный'}`;
  }

  const unexpCountEl = document.getElementById('pwr-unexpected-count');
  if (unexpCountEl) unexpCountEl.textContent = summary.unexpected_shutdowns_count;

  const unexpBadge = document.getElementById('pwr-unexpected-badge');
  if (unexpBadge) {
    unexpBadge.textContent = `${summary.unexpected_shutdowns_count} Сбоев`;
    if (summary.unexpected_shutdowns_count > 0) {
      unexpBadge.className = 'badge bg-danger font-monospace';
    } else {
      unexpBadge.className = 'badge bg-success font-monospace';
    }
  }

  const bsodEl = document.getElementById('pwr-bsod-count');
  if (bsodEl) bsodEl.textContent = `BSOD (1001): ${summary.bsod_count || 0}`;
}

/**
 * Фильтрует и отрисовывает таблицу сессий питания.
 */
function filterAndRenderSessions() {
  const tbody = document.getElementById('pwr-sessions-tbody');
  const counter = document.getElementById('pwr-sessions-counter');
  if (!tbody) return;

  const searchVal = (document.getElementById('pwr-sessions-search')?.value || '').toLowerCase().trim();
  const typeFilter = document.getElementById('pwr-filter-type')?.value || '';
  const unexpOnly = document.getElementById('pwr-filter-unexpected-only')?.checked || false;

  const filtered = allSessions.filter(s => {
    if (unexpOnly && !s.unexpected_shutdown) return false;
    if (typeFilter) {
      if (typeFilter === 'Active' && s.shutdown_type !== 'Active') return false;
      if (typeFilter === 'Restart' && s.shutdown_type !== 'Restart') return false;
      if (typeFilter === 'Shutdown' && s.shutdown_type !== 'Shutdown' && s.shutdown_type !== 'PowerOff') return false;
      if (typeFilter === 'Unexpected' && !s.unexpected_shutdown) return false;
      if (typeFilter === 'BSOD' && s.shutdown_type !== 'BSOD' && !s.bugcheck) return false;
    }

    if (searchVal) {
      const init = (s.initiator || '').toLowerCase();
      const proc = (s.process || '').toLowerCase();
      const reason = (s.reason || '').toLowerCase();
      const code = (s.reason_code || '').toLowerCase();
      const sId = (s.session_id || '').toLowerCase();
      if (!init.includes(searchVal) && !proc.includes(searchVal) && !reason.includes(searchVal) && !code.includes(searchVal) && !sId.includes(searchVal)) {
        return false;
      }
    }
    return true;
  });

  if (counter) counter.textContent = `Найдено: ${filtered.length}`;

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center py-4 text-muted">
          Сессии питания, удовлетворяющие критериям фильтрации, не найдены.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map(s => {
    let statusBadge = '<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle">Неизвестно</span>';
    if (s.shutdown_type === 'Active') {
      statusBadge = '<span class="badge bg-success-subtle text-success border border-success-subtle">🟢 Активная</span>';
    } else if (s.shutdown_type === 'Restart') {
      statusBadge = '<span class="badge bg-primary-subtle text-primary border border-primary-subtle">↻ Перезагрузка</span>';
    } else if (s.shutdown_type === 'Shutdown' || s.shutdown_type === 'PowerOff') {
      statusBadge = '<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle">⏻ Выключение</span>';
    } else if (s.shutdown_type === 'BSOD' || s.bugcheck) {
      statusBadge = `<span class="badge bg-danger text-white">🚨 BSOD ${escapeHtml(s.bugcheck || '')}</span>`;
    } else if (s.unexpected_shutdown) {
      statusBadge = '<span class="badge bg-danger-subtle text-danger border border-danger-subtle">⚠️ Сбой / 41</span>';
    }

    let initiatorHtml = '<span class="text-muted">--</span>';
    if (s.initiator || s.process) {
      const initName = s.initiator ? `<span class="fw-semibold text-primary">${escapeHtml(s.initiator)}</span>` : '';
      const procName = s.process ? `<span class="badge pwr-proc-badge font-monospace ms-1">${escapeHtml(s.process)}</span>` : '';
      initiatorHtml = `<div class="d-flex align-items-center flex-wrap">${initName} ${procName}</div>`;
      if (s.initiator_chain && s.initiator_chain.length > 1) {
        initiatorHtml += `<div class="small text-muted font-monospace mt-0.5" style="font-size: 0.72rem;">🔗 ${escapeHtml(s.initiator_chain.join(' → '))}</div>`;
      }
    }

    let reasonHtml = '<span class="text-muted">--</span>';
    if (s.reason || s.reason_code) {
      const codeBadge = s.reason_code ? `<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle font-monospace me-1">${escapeHtml(s.reason_code)}</span>` : '';
      reasonHtml = `<div>${codeBadge}<span>${escapeHtml(s.reason || '')}</span></div>`;
      if (s.comment) {
        reasonHtml += `<div class="small text-muted font-italic mt-0.5">💬 ${escapeHtml(s.comment)}</div>`;
      }
    }

    return `
      <tr>
        <td class="font-monospace text-primary small fw-bold">${escapeHtml(s.session_id)}</td>
        <td class="font-monospace small">${escapeHtml(s.boot_time)}</td>
        <td class="font-monospace small text-muted">${s.shutdown_time ? escapeHtml(s.shutdown_time) : '<span class="text-success fw-bold">Сейчас</span>'}</td>
        <td class="font-monospace fw-semibold">${escapeHtml(s.uptime_human || '--')}</td>
        <td>${statusBadge}</td>
        <td>${initiatorHtml}</td>
        <td>${reasonHtml}</td>
        <td class="text-center">
          <button class="btn btn-xs btn-outline-info p-1 px-2 pwr-detail-btn" data-session-id="${escapeHtml(s.session_id)}" title="Посмотреть подробную хронологию">
            <i class="bi bi-eye"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  // Навешиваем слушатели на кнопки деталей
  tbody.querySelectorAll('.pwr-detail-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const sId = btn.dataset.sessionId;
      showSessionDetailModal(sId);
    });
  });
}

/**
 * Фильтрует и отрисовывает таблицу событий Event Log.
 */
function filterAndRenderEvents() {
  const tbody = document.getElementById('pwr-events-tbody');
  const counter = document.getElementById('pwr-events-counter');
  if (!tbody) return;

  const searchVal = (document.getElementById('pwr-events-search')?.value || '').toLowerCase().trim();
  const eidFilter = document.getElementById('pwr-event-id-filter')?.value || '';

  const filtered = allEvents.filter(e => {
    if (eidFilter && String(e.event_id) !== String(eidFilter)) return false;
    if (searchVal) {
      const prov = (e.provider || '').toLowerCase();
      const user = (e.user || '').toLowerCase();
      const proc = (e.process || '').toLowerCase();
      const reason = (e.reason || '').toLowerCase();
      const msg = (e.details?.message || '').toLowerCase();
      if (!prov.includes(searchVal) && !user.includes(searchVal) && !proc.includes(searchVal) && !reason.includes(searchVal) && !msg.includes(searchVal)) {
        return false;
      }
    }
    return true;
  });

  if (counter) counter.textContent = `Событий: ${filtered.length}`;

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center py-4 text-muted">
          События журнала, удовлетворяющие критериям поиска, не найдены.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map(e => {
    let eidBadge = `<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle font-monospace">${e.event_id}</span>`;
    if (e.event_id === 1074) {
      eidBadge = '<span class="badge bg-warning-subtle text-warning-emphasis border border-warning font-monospace fw-bold">1074 User32</span>';
    } else if (e.event_id === 41) {
      eidBadge = '<span class="badge bg-danger-subtle text-danger border border-danger font-monospace fw-bold">41 Kernel-Power</span>';
    } else if (e.event_id === 6008) {
      eidBadge = '<span class="badge bg-danger-subtle text-danger border border-danger font-monospace fw-bold">6008 EventLog</span>';
    } else if (e.event_id === 12 || e.event_id === 6005 || e.event_id === 6009) {
      eidBadge = `<span class="badge bg-success-subtle text-success border border-success font-monospace">${e.event_id} Boot</span>`;
    } else if (e.event_id === 13 || e.event_id === 6006) {
      eidBadge = `<span class="badge bg-info-subtle text-info border border-info font-monospace">${e.event_id} Clean</span>`;
    } else if (e.event_id === 1001) {
      eidBadge = '<span class="badge bg-danger text-white font-monospace fw-bold">1001 BSOD</span>';
    }

    let userProc = '<span class="text-muted">--</span>';
    if (e.user || e.process) {
      userProc = `<div class="fw-semibold text-primary">${escapeHtml(e.user || '')}</div>`;
      if (e.process) userProc += `<div class="font-monospace small text-muted">${escapeHtml(e.process)}</div>`;
    }

    const desc = e.reason || e.details?.message || '--';

    return `
      <tr>
        <td class="font-monospace small">${escapeHtml(e.timestamp)}</td>
        <td>${eidBadge}</td>
        <td class="small text-muted font-monospace">${escapeHtml(e.provider)}</td>
        <td><span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle">${escapeHtml(e.event_type)}</span></td>
        <td>${userProc}</td>
        <td class="small">${escapeHtml(desc)}</td>
        <td class="text-center">
          ${e.raw_xml ? `
            <button class="btn btn-xs btn-outline-secondary p-1 px-2 pwr-xml-btn" data-xml="${escapeHtml(e.raw_xml)}" title="Просмотреть XML">
              <i class="bi bi-code-square"></i>
            </button>
          ` : '<span class="text-muted">-</span>'}
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('.pwr-xml-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const xml = btn.dataset.xml;
      showXmlModal(xml);
    });
  });
}

/**
 * Открывает модальное окно деталей конкретной сессии питания.
 * @param {string} sessionId
 */
function showSessionDetailModal(sessionId) {
  const session = allSessions.find(s => s.session_id === sessionId);
  if (!session) return;

  const modalTitle = document.getElementById('pwr-modal-title');
  const modalBody = document.getElementById('pwr-modal-body');
  if (modalTitle) modalTitle.textContent = `Сессия питания: ${session.session_id}`;

  if (modalBody) {
    let eventsListHtml = '<div class="text-muted small">Нет связанных событий</div>';
    if (session.events && session.events.length > 0) {
      eventsListHtml = session.events.map(ev => `
        <div class="pwr-detail-card p-2 mb-2">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="badge bg-primary-subtle text-primary border border-primary-subtle font-monospace">Event ${ev.event_id}</span>
            <span class="font-monospace small text-muted">${escapeHtml(ev.timestamp)}</span>
          </div>
          <div class="small fw-semibold text-primary">${escapeHtml(ev.provider || '')}</div>
          <div class="small mt-1">${escapeHtml(ev.reason || ev.details?.message || '')}</div>
          ${ev.process ? `<div class="small text-muted font-monospace mt-1">Процесс: ${escapeHtml(ev.process)} | Пользователь: ${escapeHtml(ev.user || '--')}</div>` : ''}
        </div>
      `).join('');
    }

    modalBody.innerHTML = `
      <div class="row g-3 mb-3">
        <div class="col-6">
          <div class="pwr-detail-card p-2.5">
            <div class="text-muted small">🚀 Время старта (Boot):</div>
            <div class="font-monospace fw-bold text-info mt-1">${escapeHtml(session.boot_time)}</div>
          </div>
        </div>
        <div class="col-6">
          <div class="pwr-detail-card p-2.5">
            <div class="text-muted small">⏹️ Завершение работы:</div>
            <div class="font-monospace fw-bold ${session.shutdown_time ? '' : 'text-success'} mt-1">
              ${session.shutdown_time ? escapeHtml(session.shutdown_time) : 'Сессия активна'}
            </div>
          </div>
        </div>
      </div>

      <div class="pwr-detail-card p-3 mb-3">
        <h6 class="fw-bold text-warning mb-2"><i class="bi bi-sliders me-1.5"></i>Параметры завершения</h6>
        <div class="row g-2 small">
          <div class="col-4 text-muted">Тип завершения:</div>
          <div class="col-8 fw-semibold">${escapeHtml(session.shutdown_type)}</div>
          
          <div class="col-4 text-muted">Аптайм сессии:</div>
          <div class="col-8 font-monospace fw-bold">${escapeHtml(session.uptime_human || '--')}</div>

          <div class="col-4 text-muted">Инициатор:</div>
          <div class="col-8">${escapeHtml(session.initiator || 'SYSTEM / Hardware')}</div>

          <div class="col-4 text-muted">Процесс:</div>
          <div class="col-8 font-monospace text-info">${escapeHtml(session.process || '--')}</div>

          <div class="col-4 text-muted">Код причины:</div>
          <div class="col-8 font-monospace text-secondary">${escapeHtml(session.reason_code || '--')}</div>

          <div class="col-4 text-muted">Текст причины:</div>
          <div class="col-8">${escapeHtml(session.reason || '--')}</div>

          ${session.comment ? `
            <div class="col-4 text-muted">Комментарий:</div>
            <div class="col-8 font-italic">${escapeHtml(session.comment)}</div>
          ` : ''}

          ${session.bugcheck ? `
            <div class="col-4 text-danger fw-bold">BSOD BugCheck:</div>
            <div class="col-8 text-danger font-monospace fw-bold">${escapeHtml(session.bugcheck)}</div>
          ` : ''}
        </div>
      </div>

      ${session.initiator_chain && session.initiator_chain.length > 0 ? `
        <div class="pwr-detail-card p-3 mb-3">
          <h6 class="fw-bold text-info mb-2"><i class="bi bi-diagram-3 me-1.5"></i>Корреляция цепочки вызова</h6>
          <div class="d-flex align-items-center flex-wrap gap-1 font-monospace small">
            ${session.initiator_chain.map((step, idx) => `
              <span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle p-2">${escapeHtml(step)}</span>
              ${idx < session.initiator_chain.length - 1 ? '<i class="bi bi-arrow-right text-muted"></i>' : ''}
            `).join('')}
          </div>
        </div>
      ` : ''}

      <div class="pwr-detail-card p-3">
        <h6 class="fw-bold mb-2"><i class="bi bi-list-nested me-1.5"></i>Хронология событий в рамках сессии</h6>
        <div style="max-height: 250px; overflow-y: auto;">
          ${eventsListHtml}
        </div>
      </div>
    `;

    const modalEl = document.getElementById('pwrSessionDetailModal');
    if (modalEl && window.bootstrap) {
      const modal = new window.bootstrap.Modal(modalEl);
      modal.show();
    }
  }
}

/**
 * Открывает модальное окно просмотра XML события.
 * @param {string} xmlString
 */
function showXmlModal(xmlString) {
  const pre = document.getElementById('pwr-xml-content');
  if (pre) pre.textContent = xmlString;

  const modalEl = document.getElementById('pwrXmlDetailModal');
  if (modalEl && window.bootstrap) {
    const modal = new window.bootstrap.Modal(modalEl);
    modal.show();
  }
}

/**
 * Запускает локальный секундный таймер для активного аптайма.
 */
function startUptimeCounter() {
  if (uptimeInterval) clearInterval(uptimeInterval);
  uptimeInterval = setInterval(() => {
    uptimeSeconds += 1;
    const curUptimeEl = document.getElementById('pwr-current-uptime');
    if (curUptimeEl && uptimeSeconds > 0) {
      const days = Math.floor(uptimeSeconds / 86400);
      const hours = Math.floor((uptimeSeconds % 86400) / 3600);
      const minutes = Math.floor((uptimeSeconds % 3600) / 60);
      const sec = Math.floor(uptimeSeconds % 60);
      const parts = [];
      if (days > 0) parts.push(`${days}д`);
      if (hours > 0 || days > 0) parts.push(`${hours}ч`);
      if (minutes > 0 || hours > 0 || days > 0) parts.push(`${minutes}м`);
      parts.push(`${sec}с`);
      curUptimeEl.textContent = parts.join(' ');
    }
  }, 1000);
}

/**
 * Экранирует HTML строку.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Автозапуск при загрузке страницы
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPowerLifecycleTab);
} else {
  initPowerLifecycleTab();
}
