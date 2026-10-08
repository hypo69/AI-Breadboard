/**
 * =============================================================================
 * Process Name: Windows Accounts & Identity Tab - Client Controller
 * =============================================================================
 * Description:
 *   Клиентский JavaScript контроллер для вкладки управления пользователями,
 *   группами, правами LSA, журналом событий безопасности, инспекцией процессов
 *   и каталогом операций.
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/accounts_identity_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-08 01:51:00
 * =============================================================================
 */

let _usersCache = [];
let _groupsCache = [];
let _eventsCache = [];
let _catalogCache = [];
let _currentEventFilter = 'all';

/**
 * Инициализация контроллера вкладки Accounts & Identity
 */
export async function initAccountsIdentityTab() {
  bindEvents();
  await loadAllIdentityData();
}

/**
 * Привязка обработчиков событий
 */
function bindEvents() {
  const refreshBtn = document.getElementById('btn-refresh-identity');
  if (refreshBtn) refreshBtn.onclick = () => loadAllIdentityData();

  const refreshEventsBtn = document.getElementById('btn-refresh-events');
  if (refreshEventsBtn) refreshEventsBtn.onclick = () => loadSecurityEvents();

  const openCreateUserModalBtn = document.getElementById('btn-open-create-user-modal');
  if (openCreateUserModalBtn) {
    openCreateUserModalBtn.onclick = () => {
      const modalEl = document.getElementById('createUserModal');
      if (modalEl && window.bootstrap) {
        const modal = new window.bootstrap.Modal(modalEl);
        modal.show();
      }
    };
  }

  const submitCreateUserBtn = document.getElementById('btn-submit-create-user');
  if (submitCreateUserBtn) submitCreateUserBtn.onclick = handleCreateUserSubmit;

  const filterUsersInput = document.getElementById('filter-users-input');
  if (filterUsersInput) {
    filterUsersInput.oninput = (e) => filterUsersTable(e.target.value);
  }

  const filterEventsInput = document.getElementById('filter-events-input');
  if (filterEventsInput) {
    filterEventsInput.oninput = (e) => filterEventsTable(e.target.value);
  }

  const filterCatalogInput = document.getElementById('filter-catalog-input');
  if (filterCatalogInput) {
    filterCatalogInput.oninput = (e) => filterCatalogTable(e.target.value);
  }

  // Быстрые фильтры журнала событий
  const eventsFilterToolbar = document.getElementById('events-quick-filters');
  if (eventsFilterToolbar) {
    eventsFilterToolbar.querySelectorAll('.event-filter-btn').forEach(btn => {
      btn.onclick = () => {
        eventsFilterToolbar.querySelectorAll('.event-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        _currentEventFilter = btn.getAttribute('data-filter') || 'all';
        applyEventsFilter();
      };
    });
  }

  // Быстрые проверки безопасности
  const btnWhoIsAdmin = document.getElementById('btn-check-who-is-admin');
  if (btnWhoIsAdmin) btnWhoIsAdmin.onclick = runWhoIsAdminCheck;

  const btnServiceLogon = document.getElementById('btn-check-service-logon');
  if (btnServiceLogon) btnServiceLogon.onclick = runServiceLogonCheck;

  const btnRdp = document.getElementById('btn-check-rdp');
  if (btnRdp) btnRdp.onclick = runRdpCheck;

  const btnOrphaned = document.getElementById('btn-check-orphaned');
  if (btnOrphaned) btnOrphaned.onclick = runOrphanedCheck;

  // Инспектор PID
  const btnExplainPid = document.getElementById('btn-explain-pid');
  if (btnExplainPid) btnExplainPid.onclick = handleExplainPid;
}

/**
 * Загрузка всех данных с бэкенда
 */
async function loadAllIdentityData() {
  await Promise.allSettled([
    loadCurrentToken(),
    loadUsers(),
    loadGroups(),
    loadSecurityEvents(),
    loadPasswordPolicy(),
    loadCatalog(),
  ]);
}

/**
 * Загрузка контекста текущего пользователя
 */
async function loadCurrentToken() {
  const badgeEl = document.getElementById('ai-current-token-badge');
  try {
    const res = await fetch('/api/windows/identity/current');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const isElevated = data.is_elevated ? '<span class="badge bg-danger ms-1">Elevated (Admin)</span>' : '<span class="badge bg-secondary ms-1">Standard</span>';
    const integrityBadge = `<span class="badge bg-primary ms-1">${data.integrity_level}</span>`;
    if (badgeEl) {
      badgeEl.innerHTML = `Текущий токен: <strong>${data.domain}\\${data.user_name}</strong> (SID: <code>${data.user_sid}</code>) | Целостность: ${integrityBadge} ${isElevated}`;
    }
  } catch (err) {
    if (badgeEl) badgeEl.innerHTML = `<span class="text-danger">Ошибка контекста: ${err.message}</span>`;
  }
}

/**
 * Загрузка пользователей
 */
async function loadUsers() {
  const tbody = document.getElementById('users-table-body');
  const statTotal = document.getElementById('stat-total-users');
  const statAdmins = document.getElementById('stat-total-admins');
  const statSessions = document.getElementById('stat-active-sessions');

  try {
    const [resUsers, resAdmins, resSessions] = await Promise.all([
      fetch('/api/windows/identity/users'),
      fetch('/api/windows/identity/who-is-admin'),
      fetch('/api/windows/identity/sessions'),
    ]);

    _usersCache = resUsers.ok ? await resUsers.json() : [];
    const admins = resAdmins.ok ? await resAdmins.json() : [];
    const sessions = resSessions.ok ? await resSessions.json() : [];

    if (statTotal) statTotal.textContent = _usersCache.length;
    if (statAdmins) statAdmins.textContent = admins.length;
    if (statSessions) statSessions.textContent = sessions.length;

    renderUsersTable(_usersCache);
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger py-3">Ошибка загрузки пользователей: ${err.message}</td></tr>`;
    }
  }
}

/**
 * Отрисовка таблицы пользователей
 */
function renderUsersTable(users) {
  const tbody = document.getElementById('users-table-body');
  if (!tbody) return;

  if (!users || users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3">Пользователи не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = users.map(u => {
    const statusBadge = u.enabled
      ? '<span class="badge bg-success bg-opacity-75">Включен</span>'
      : '<span class="badge bg-danger bg-opacity-75">Отключен</span>';
    const pwdBadge = u.password_never_expires
      ? '<span class="badge bg-info text-dark">Бессрочный</span>'
      : '<span class="badge bg-secondary">Ограничен</span>';

    return `
      <tr>
        <td class="fw-bold">
          <i class="bi bi-person-circle me-1 text-primary"></i> ${escapeHtml(u.name)}
        </td>
        <td>${escapeHtml(u.full_name || '—')}</td>
        <td><code class="small">${escapeHtml(u.sid || '—')}</code></td>
        <td>${statusBadge}</td>
        <td>${pwdBadge}</td>
        <td>${u.account_expires ? escapeHtml(u.account_expires) : 'Никогда'}</td>
        <td>${u.last_logon ? escapeHtml(u.last_logon) : '—'}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary py-0 px-1" onclick="window._explainUserDossier('${escapeHtml(u.name)}')" title="Открыть досье Principal">
            <i class="bi bi-file-text"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger py-0 px-1 ms-1" onclick="window._deleteUserAction('${escapeHtml(u.name)}')" title="Удалить пользователя">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Фильтрация пользователей
 */
function filterUsersTable(query) {
  const q = (query || '').toLowerCase().trim();
  if (!q) {
    renderUsersTable(_usersCache);
    return;
  }
  const filtered = _usersCache.filter(u =>
    (u.name && u.name.toLowerCase().includes(q)) ||
    (u.full_name && u.full_name.toLowerCase().includes(q)) ||
    (u.sid && u.sid.toLowerCase().includes(q))
  );
  renderUsersTable(filtered);
}

/**
 * Загрузка групп
 */
async function loadGroups() {
  const tbody = document.getElementById('groups-table-body');
  const statGroups = document.getElementById('stat-total-groups');
  try {
    const res = await fetch('/api/windows/identity/groups');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    _groupsCache = await res.json();
    if (statGroups) statGroups.textContent = _groupsCache.length;

    if (!tbody) return;
    if (_groupsCache.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Группы не найдены</td></tr>';
      return;
    }

    tbody.innerHTML = _groupsCache.map(g => {
      const typeBadge = g.is_admin
        ? '<span class="badge bg-danger">ADMIN GROUP</span>'
        : '<span class="badge bg-secondary">Локальная</span>';
      const membersCount = (g.members || []).length;
      return `
        <tr>
          <td class="fw-bold"><i class="bi bi-shield me-1 text-primary"></i> ${escapeHtml(g.name)}</td>
          <td><code class="small">${escapeHtml(g.sid || '—')}</code></td>
          <td class="text-muted small">${escapeHtml(g.description || '—')}</td>
          <td>${typeBadge}</td>
          <td><span class="badge bg-light text-dark border">${membersCount} уч.</span></td>
          <td class="text-end">
            <button class="btn btn-sm btn-outline-info py-0 px-1" onclick="window._viewGroupMembers('${escapeHtml(g.name)}')" title="Участники">
              <i class="bi bi-people"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-3">Ошибка загрузки групп: ${err.message}</td></tr>`;
    }
  }
}

/**
 * Загрузка журнала событий безопасности Windows
 */
async function loadSecurityEvents() {
  const tbody = document.getElementById('events-table-body');
  const badge = document.getElementById('events-count-badge');
  const statBadge = document.getElementById('stat-security-events');

  try {
    const res = await fetch('/api/windows/identity/audit?limit=100');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    _eventsCache = await res.json();

    if (badge) badge.textContent = `${_eventsCache.length} записей`;
    if (statBadge) statBadge.textContent = _eventsCache.length;

    applyEventsFilter();
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Ошибка загрузки журнала безопасности: ${err.message}</td></tr>`;
    }
  }
}

/**
 * Применение фильтров к событиям безопасности
 */
function applyEventsFilter() {
  const q = (document.getElementById('filter-events-input')?.value || '').toLowerCase().trim();
  let filtered = _eventsCache;

  if (_currentEventFilter === 'logon') {
    filtered = filtered.filter(e => [4624, 4625].includes(e.event_id));
  } else if (_currentEventFilter === 'accounts') {
    filtered = filtered.filter(e => [4720, 4722, 4725, 4726, 4731, 4732, 4733, 4734, 4735, 4738].includes(e.event_id));
  } else if (_currentEventFilter === 'password') {
    filtered = filtered.filter(e => [4723, 4724].includes(e.event_id));
  } else if (_currentEventFilter === 'lockout') {
    filtered = filtered.filter(e => e.event_id === 4740);
  }

  if (q) {
    filtered = filtered.filter(e =>
      String(e.event_id).includes(q) ||
      (e.event_name && e.event_name.toLowerCase().includes(q)) ||
      (e.target_account && e.target_account.toLowerCase().includes(q)) ||
      (e.caller_account && e.caller_account.toLowerCase().includes(q)) ||
      (e.description && e.description.toLowerCase().includes(q))
    );
  }

  renderEventsTable(filtered);
}

/**
 * Поиск по текстовому запросу в журнале событий
 */
function filterEventsTable(query) {
  applyEventsFilter();
}

/**
 * Отрисовка таблицы журнала событий безопасности
 */
function renderEventsTable(events) {
  const tbody = document.getElementById('events-table-body');
  if (!tbody) return;

  if (!events || events.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">События безопасности по выбранному фильтру не найдены</td></tr>';
    return;
  }

  tbody.innerHTML = events.map((e, idx) => {
    let eidBadge = `<span class="badge bg-secondary">${e.event_id}</span>`;
    if (e.event_id === 4624) {
      eidBadge = '<span class="badge bg-success">4624</span>';
    } else if (e.event_id === 4625 || e.event_id === 4740 || e.event_id === 4726 || e.event_id === 4734) {
      eidBadge = `<span class="badge bg-danger">${e.event_id}</span>`;
    } else if (e.event_id === 4724 || e.event_id === 4738) {
      eidBadge = `<span class="badge bg-warning text-dark">${e.event_id}</span>`;
    } else if (e.event_id === 4720 || e.event_id === 4731 || e.event_id === 4732) {
      eidBadge = `<span class="badge bg-primary">${e.event_id}</span>`;
    }

    const shortTime = e.timestamp ? e.timestamp.replace('T', ' ').slice(0, 19) : '—';
    const descText = e.description ? escapeHtml(e.description) : '—';

    return `
      <tr class="event-log-row" data-idx="${idx}" style="cursor: pointer;" onclick="window._showEventDetail(${idx})" title="Нажмите для просмотра полной информации">
        <td class="font-monospace text-muted small">${escapeHtml(shortTime)}</td>
        <td>${eidBadge}</td>
        <td class="fw-semibold text-primary">${escapeHtml(e.event_name)}</td>
        <td class="fw-bold">${escapeHtml(e.target_account || '—')}</td>
        <td class="text-muted small">${escapeHtml(e.caller_account || '—')}</td>
        <td class="small text-truncate" style="max-width: 320px;" title="${descText}">${descText}</td>
        <td class="text-end">
          <button class="btn btn-xs btn-outline-info py-0 px-2" onclick="event.stopPropagation(); window._showEventDetail(${idx})" title="Подробнее">
            Инфо
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Просмотр детальной информации о событии
 */
window._showEventDetail = function (idx) {
  const event = _eventsCache[idx];
  if (!event) return;

  if (window.AITableModal) {
    window.AITableModal.show({
      icon: '🛡️',
      title: `Событие аудита: #${event.event_id} - ${event.event_name}`,
      subtitle: `Время: ${event.timestamp} | Целевой аккаунт: ${event.target_account || 'N/A'}`,
      tableType: 'generic',
      badges: [
        { text: `Event ${event.event_id}`, class: 'badge bg-primary' },
        { text: event.event_name, class: 'badge bg-info text-dark' }
      ],
      metadata: [
        { label: 'Event ID', value: String(event.event_id) },
        { label: 'Событие', value: event.event_name },
        { label: 'Время регистрации', value: event.timestamp },
        { label: 'Целевая учетная запись', value: event.target_account || '—' },
        { label: 'Инициатор (Caller)', value: event.caller_account || '—' },
        { label: 'Статус аудита', value: event.status || 'Success' }
      ],
      rawTitle: 'Полное сообщение журнала безопасности',
      rawContent: event.description || '',
      requestData: {
        event_id: event.event_id,
        event_name: event.event_name,
        target_account: event.target_account,
        caller_account: event.caller_account,
        description: event.description
      }
    });
  } else {
    alert(`Событие #${event.event_id} (${event.event_name})\n\nВремя: ${event.timestamp}\nЦелевой аккаунт: ${event.target_account}\nИнициатор: ${event.caller_account}\n\nОписание:\n${event.description}`);
  }
};

/**
 * Загрузка политики паролей
 */
async function loadPasswordPolicy() {
  const container = document.getElementById('password-policy-container');
  if (!container) return;
  try {
    const res = await fetch('/api/windows/identity/auth/policies');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const pol = await res.json();
    container.innerHTML = `
      <ul class="list-group list-group-flush">
        <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-1">
          <span>Мин. длина пароля:</span>
          <strong>${pol.min_password_length} симв.</strong>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-1">
          <span>Макс. возраст пароля:</span>
          <strong>${pol.max_password_age_days} дней</strong>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-1">
          <span>Глубина истории:</span>
          <strong>${pol.password_history_length}</strong>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-1">
          <span>Порог блокировки:</span>
          <strong>${pol.lockout_threshold === 0 ? 'Отключен' : pol.lockout_threshold + ' попыток'}</strong>
        </li>
      </ul>
    `;
  } catch (err) {
    container.innerHTML = `<div class="text-danger">Ошибка политики: ${err.message}</div>`;
  }
}

/**
 * Загрузка каталога операций
 */
async function loadCatalog() {
  const tbody = document.getElementById('catalog-table-body');
  try {
    const res = await fetch('/api/windows/identity/catalog');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    _catalogCache = await res.json();
    renderCatalogTable(_catalogCache);
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-3">Ошибка загрузки каталога: ${err.message}</td></tr>`;
    }
  }
}

function renderCatalogTable(items) {
  const tbody = document.getElementById('catalog-table-body');
  if (!tbody) return;
  tbody.innerHTML = items.map(op => {
    let riskBadge = '<span class="badge bg-success">SAFE</span>';
    if (op.risk_level.includes('ADMIN')) riskBadge = '<span class="badge bg-warning text-dark">ADMIN</span>';
    if (op.risk_level.includes('DANGEROUS')) riskBadge = '<span class="badge bg-danger">DANGEROUS</span>';
    if (op.risk_level.includes('ADVANCED')) riskBadge = '<span class="badge bg-dark">ADVANCED</span>';

    return `
      <tr>
        <td class="text-muted fw-bold">${op.id}</td>
        <td class="fw-semibold">${escapeHtml(op.name_ru)}</td>
        <td class="small text-muted">${escapeHtml(op.subsystem_name_ru)}</td>
        <td class="small"><code>${escapeHtml(op.mechanism)}</code></td>
        <td class="small"><code>${escapeHtml(op.win32_api || op.ps_or_cli || '—')}</code></td>
        <td>${riskBadge}</td>
      </tr>
    `;
  }).join('');
}

function filterCatalogTable(query) {
  const q = (query || '').toLowerCase().trim();
  if (!q) {
    renderCatalogTable(_catalogCache);
    return;
  }
  const filtered = _catalogCache.filter(op =>
    op.name_ru.toLowerCase().includes(q) ||
    op.subsystem_name_ru.toLowerCase().includes(q) ||
    op.mechanism.toLowerCase().includes(q) ||
    (op.win32_api && op.win32_api.toLowerCase().includes(q))
  );
  renderCatalogTable(filtered);
}

/**
 * Создание пользователя
 */
async function handleCreateUserSubmit() {
  const username = document.getElementById('create-user-name')?.value?.trim();
  const password = document.getElementById('create-user-pwd')?.value || null;
  const fullName = document.getElementById('create-user-fullname')?.value?.trim() || '';
  const description = document.getElementById('create-user-desc')?.value?.trim() || '';

  if (!username) {
    if (window.toast) window.toast.error('Ошибка', 'Введите имя пользователя');
    return;
  }

  try {
    const res = await fetch('/api/windows/identity/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        password: password || undefined,
        full_name: fullName,
        description,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Не удалось создать пользователя');

    if (window.toast) window.toast.success('Успех', `Пользователь '${username}' создан`);
    
    // Закрытие модального окна
    const modalEl = document.getElementById('createUserModal');
    if (modalEl && window.bootstrap) {
      const modal = window.bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
    }
    document.getElementById('create-user-form')?.reset();
    await loadUsers();
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка создания', err.message);
  }
}

/**
 * Удаление пользователя
 */
window._deleteUserAction = async function (username) {
  if (!confirm(`Вы уверены, что хотите удалить пользователя '${username}'?`)) return;
  try {
    const res = await fetch(`/api/windows/identity/users/${encodeURIComponent(username)}`, {
      method: 'DELETE',
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Ошибка удаления');
    if (window.toast) window.toast.success('Удалено', `Пользователь '${username}' удален`);
    await loadUsers();
  } catch (err) {
    if (window.toast) window.toast.error('Ошибка удаления', err.message);
  }
};

/**
 * Досье Principal и история событий безопасности
 */
window._explainUserDossier = async function (identifier) {
  const modalEl = document.getElementById('principalDossierModal');
  const titleEl = document.getElementById('dossier-modal-title');
  const treeEl = document.getElementById('dossier-tree-view');
  const eventsCountEl = document.getElementById('dossier-events-count');
  const eventsTbody = document.getElementById('dossier-user-events-tbody');

  if (titleEl) titleEl.textContent = `Досье Principal: ${identifier}`;
  if (treeEl) treeEl.textContent = 'Формирование досье безопасности...';
  if (eventsCountEl) eventsCountEl.textContent = '0';
  if (eventsTbody) eventsTbody.innerHTML = '<tr><td colspan="5" class="text-center py-3 text-muted">Загрузка журнала событий...</td></tr>';

  // Переключение на вкладку дерева по умолчанию
  const firstTabBtn = document.getElementById('dossier-tree-tab');
  if (firstTabBtn && window.bootstrap) {
    const tabTrigger = new window.bootstrap.Tab(firstTabBtn);
    tabTrigger.show();
  }

  if (modalEl && window.bootstrap) {
    const modal = new window.bootstrap.Modal(modalEl);
    modal.show();
  }

  try {
    const res = await fetch(`/api/windows/identity/explain/${encodeURIComponent(identifier)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Формирование дерева
    const lines = [
      `Principal (${data.name})`,
      '│',
      `├── SID: ${data.sid}`,
      `├── Domain: ${data.domain}`,
      `├── Type: ${data.principal_type}`,
      `├── Source: ${data.source}`,
      `├── Administrator: ${data.is_admin ? 'YES (🟢)' : 'NO'}`,
      `├── Built-in: ${data.is_built_in ? 'YES' : 'NO'}`,
      `├── Orphaned: ${data.is_orphaned ? 'YES (⚠️)' : 'NO'}`,
      '│',
      '├── Account Details',
      `│   ├── Enabled: ${data.account ? (data.account.enabled ? 'YES' : 'NO (Disabled)') : 'N/A'}`,
      `│   ├── Password Expires: ${data.account ? (data.account.password_expires || 'Never') : 'N/A'}`,
      `│   └── Last Logon: ${data.account ? (data.account.last_logon || 'N/A') : 'N/A'}`,
      '│',
      `├── Groups (${(data.groups || []).length})`,
      ...(data.groups || []).map(g => `│   ├── ${g.name} ${g.is_admin ? '[ADMIN]' : ''} (${g.sid})`),
      '│',
      `├── LSA Rights & Privileges (${(data.rights || []).length})`,
      ...(data.rights || []).slice(0, 10).map(r => `│   ├── ${r}`),
      '│',
      `├── Profile: ${data.profile ? data.profile.profile_path : 'None'}`,
      `├── Active Sessions: ${(data.sessions || []).length}`,
      `└── Running Processes: ${(data.processes || []).length}`,
    ];

    if (treeEl) treeEl.textContent = lines.join('\n');

    // Рендеринг событий пользователя
    const auditEvents = data.audit_events || [];
    if (eventsCountEl) eventsCountEl.textContent = String(auditEvents.length);

    if (eventsTbody) {
      if (auditEvents.length === 0) {
        eventsTbody.innerHTML = '<tr><td colspan="5" class="text-center py-3 text-muted">События безопасности для данного пользователя не зафиксированы в Security Log</td></tr>';
      } else {
        eventsTbody.innerHTML = auditEvents.map(ev => {
          let badgeClass = 'bg-secondary';
          if (ev.event_id === 4624) badgeClass = 'bg-success';
          if (ev.event_id === 4625 || ev.event_id === 4740) badgeClass = 'bg-danger';
          if (ev.event_id === 4724) badgeClass = 'bg-warning text-dark';

          const shortTime = ev.timestamp ? ev.timestamp.replace('T', ' ').slice(0, 19) : '—';
          return `
            <tr>
              <td class="text-muted">${escapeHtml(shortTime)}</td>
              <td><span class="badge ${badgeClass}">${ev.event_id}</span></td>
              <td class="fw-semibold text-primary">${escapeHtml(ev.event_name)}</td>
              <td>${escapeHtml(ev.caller_account || ev.target_account || '—')}</td>
              <td class="small text-truncate" style="max-width: 300px;" title="${escapeHtml(ev.description)}">${escapeHtml(ev.description)}</td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (err) {
    if (treeEl) treeEl.textContent = `Ошибка получения досье: ${err.message}`;
    if (eventsTbody) eventsTbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-3">Ошибка загрузки событий: ${err.message}</td></tr>`;
  }
};

/**
 * Просмотр участников группы
 */
window._viewGroupMembers = function (groupName) {
  const group = _groupsCache.find(g => g.name.toLowerCase() === groupName.toLowerCase());
  if (!group) return;
  const members = (group.members || []).join('\n') || 'Нет участников';
  alert(`Участники группы ${groupName}:\n\n${members}`);
};

/**
 * Проверка Who is Admin?
 */
async function runWhoIsAdminCheck() {
  const outputEl = document.getElementById('security-audit-results');
  if (outputEl) outputEl.innerHTML = '<div class="text-muted text-center py-3">Анализ администраторов системы...</div>';
  try {
    const res = await fetch('/api/windows/identity/who-is-admin');
    const admins = await res.json();
    if (!admins || admins.length === 0) {
      if (outputEl) outputEl.innerHTML = '<div>Администраторы не найдены</div>';
      return;
    }
    const html = admins.map(a => `
      <div class="mb-2 pb-1 border-bottom">
        <div class="fw-bold text-danger"><i class="bi bi-shield-lock-fill me-1"></i> ${escapeHtml(a.username)} <span class="badge bg-secondary">${a.is_direct ? 'Прямой доступ' : 'Вложенное членство'}</span></div>
        <div class="small text-muted font-monospace">SID: ${a.sid}</div>
        <div class="small text-primary">Цепочка: ${(a.path_to_admin || []).join(' → ')}</div>
      </div>
    `).join('');
    if (outputEl) outputEl.innerHTML = html;
  } catch (err) {
    if (outputEl) outputEl.innerHTML = `<div class="text-danger">Ошибка: ${err.message}</div>`;
  }
}

/**
 * Проверка Logon as Service
 */
async function runServiceLogonCheck() {
  const outputEl = document.getElementById('security-audit-results');
  if (outputEl) outputEl.innerHTML = '<div class="text-muted text-center py-3">Поиск аккаунтов с SeServiceLogonRight...</div>';
  try {
    const res = await fetch('/api/windows/identity/who-can-logon-as-service');
    const list = await res.json();
    if (!list || list.length === 0) {
      if (outputEl) outputEl.innerHTML = '<div class="text-success">Специфических сервисных учетных записей не назначено.</div>';
      return;
    }
    const html = `<h6>Аккаунты с правом SeServiceLogonRight:</h6>` + list.map(a => `<div class="font-monospace text-primary mb-1">• ${escapeHtml(a)}</div>`).join('');
    if (outputEl) outputEl.innerHTML = html;
  } catch (err) {
    if (outputEl) outputEl.innerHTML = `<div class="text-danger">Ошибка: ${err.message}</div>`;
  }
}

/**
 * Проверка RDP
 */
async function runRdpCheck() {
  const outputEl = document.getElementById('security-audit-results');
  if (outputEl) outputEl.innerHTML = '<div class="text-muted text-center py-3">Поиск аккаунтов с доступом к RDP...</div>';
  try {
    const res = await fetch('/api/windows/identity/who-can-rdp');
    const list = await res.json();
    const html = `<h6>Аккаунты и группы с доступом к Remote Desktop:</h6>` + list.map(a => `<div class="font-monospace text-warning-emphasis mb-1">• ${escapeHtml(a)}</div>`).join('');
    if (outputEl) outputEl.innerHTML = html;
  } catch (err) {
    if (outputEl) outputEl.innerHTML = `<div class="text-danger">Ошибка: ${err.message}</div>`;
  }
}

/**
 * Проверка осиротевших записей
 */
async function runOrphanedCheck() {
  const outputEl = document.getElementById('security-audit-results');
  if (outputEl) outputEl.innerHTML = '<div class="text-muted text-center py-3">Поиск осиротевших SID и профилей...</div>';
  try {
    const [resSids, resProfiles] = await Promise.all([
      fetch('/api/windows/identity/orphaned-sids'),
      fetch('/api/windows/identity/orphaned-profiles'),
    ]);
    const sids = await resSids.json();
    const profiles = await resProfiles.json();

    if ((!sids || sids.length === 0) && (!profiles || profiles.length === 0)) {
      if (outputEl) outputEl.innerHTML = '<div class="text-success"><i class="bi bi-check-circle-fill me-1"></i> Осиротевших SID и профилей в системе не обнаружено.</div>';
      return;
    }

    let html = '<h6>Осиротевшие субъекты:</h6>';
    for (const s of sids) {
      html += `<div class="text-danger font-monospace mb-1">⚠️ SID: ${s.sid} (${s.location})</div>`;
    }
    for (const p of profiles) {
      html += `<div class="text-warning font-monospace mb-1">📁 Профиль без пользователя: ${p.profile_path} (SID: ${p.sid})</div>`;
    }
    if (outputEl) outputEl.innerHTML = html;
  } catch (err) {
    if (outputEl) outputEl.innerHTML = `<div class="text-danger">Ошибка: ${err.message}</div>`;
  }
}

/**
 * Исследование PID
 */
async function handleExplainPid() {
  const input = document.getElementById('input-explain-pid');
  const outputEl = document.getElementById('pid-dossier-output');
  const pidVal = parseInt(input?.value || '0', 10);

  if (!pidVal || isNaN(pidVal)) {
    if (window.toast) window.toast.error('Ошибка', 'Укажите корректный PID процесса');
    return;
  }

  if (outputEl) {
    outputEl.style.display = 'block';
    outputEl.textContent = `Исследование процесса PID ${pidVal}...`;
  }

  try {
    const res = await fetch(`/api/windows/identity/explain-pid/${pidVal}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const acc = data.account || {};
    const privs = data.privileges || [];
    const groups = data.groups || [];

    const lines = [
      `PID ${data.pid}`,
      '│',
      `├── Process: ${data.process_name}`,
      `├── Parent: ${data.parent_name} (PID ${data.parent_pid})`,
      '│',
      '├── Account',
      `│   ├── ${acc.domain}\\${acc.user}`,
      `│   └── SID: ${acc.sid}`,
      '│',
      `├── Groups (${groups.length})`,
      ...groups.map(g => `│   ├── ${g}`),
      '│',
      `├── Integrity: ${data.integrity}`,
      `├── Elevated: ${data.elevated ? 'YES (🟢)' : 'NO'}`,
      '│',
      `├── Privileges (${privs.length})`,
      ...privs.map(p => `│   ├── ${p}`),
      '│',
      '└── Session',
      '    ├── Console',
      `    └── Session ID: ${data.session_id}`,
    ];

    if (outputEl) outputEl.textContent = lines.join('\n');
  } catch (err) {
    if (outputEl) outputEl.textContent = `Ошибка исследования PID ${pidVal}: ${err.message}`;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Автозапуск при загрузке вкладки
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAccountsIdentityTab);
} else {
  initAccountsIdentityTab();
}
