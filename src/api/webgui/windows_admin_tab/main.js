// =============================================================================
// Process Name: Windows System Administrator Web Tab Module
// =============================================================================
// Description:
//   Клиентский контроллер вкладки Windows System Administrator:
//   - Отображение всех локальных и доменных учетных записей Windows
//   - Обнаружение скрытых пользователей (SpecialAccounts UserList)
//   - Подробная телеметрия ресурсов (память, CPU, процессы, профили на диске)
//   - Фильтрация (Все, В сети, Скрытые, Администраторы)
//   - Интерактивное досье с поддержкой AI-аудита прав и безопасности
//
// File: main.js
// Project: ai-breadboard
// Package: src.api.webgui.windows_admin_tab
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

(function() {
  let isWinAdminInitialized = false;
  let currentUserFilter = 'all';

  async function fetchStatus() {
    try {
      const res = await fetch('/api/sysadmin/status');
      if (!res.ok) return;
      const data = await res.json();
      
      const hostEl = document.getElementById('winadmin-hostname');
      const userCountEl = document.getElementById('winadmin-user-count');
      const userBreakdownEl = document.getElementById('winadmin-user-breakdown');
      const adStatusEl = document.getElementById('winadmin-ad-status');
      const eventsCountEl = document.getElementById('winadmin-events-count');

      if (hostEl) hostEl.innerText = `${data.hostname || 'LOCAL'} / ${data.domain || 'WORKGROUP'}`;
      if (userCountEl) {
        userCountEl.innerText = `${data.total_accounts || data.user_count || 0} (${data.active_users || 0} онлайн)`;
      }
      if (userBreakdownEl) {
        userBreakdownEl.innerText = `${data.hidden_users || 0} скрытых`;
      }
      if (adStatusEl) adStatusEl.innerText = data.ad_connected ? 'Подключен' : 'Локальный хост';
      if (eventsCountEl) eventsCountEl.innerText = data.event_count || 0;
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch status:', e);
    }
  }

  async function fetchAccounts(filterType = currentUserFilter) {
    try {
      const res = await fetch(`/api/sysadmin/accounts?filter_type=${encodeURIComponent(filterType)}`);
      if (!res.ok) return;
      const data = await res.json();
      const accounts = data.accounts || [];
      
      const tbody = document.getElementById('winadmin-users-tbody');
      const badge = document.getElementById('winadmin-users-badge');
      if (badge) badge.innerText = `${accounts.length} аккаунтов (${data.total || accounts.length} всего)`;

      if (tbody) {
        if (accounts.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted p-3">Учетные записи по выбранному фильтру не найдены</td></tr>';
          return;
        }

        tbody.innerHTML = accounts.map((u, idx) => {
          // Вычисление бейджей
          const badges = [];
          if (u.is_admin) badges.push('<span class="badge badge-admin me-1">Admin</span>');
          if (u.is_hidden) badges.push('<span class="badge badge-hidden me-1">Скрытый</span>');
          if (!u.enabled) badges.push('<span class="badge badge-disabled me-1">Отключен</span>');

          // Статус
          let statusBadge = '<span class="badge bg-secondary">Офлайн</span>';
          if (u.is_logged_in) {
            statusBadge = '<span class="badge bg-success-subtle text-success border border-success">● В сети</span>';
          } else if (!u.enabled) {
            statusBadge = '<span class="badge bg-dark text-muted">Отключен</span>';
          }

          // Ресурсы
          const resInfo = u.process_count > 0 
            ? `<span class="text-info">${u.process_count} проц.</span> <span class="text-muted">(${u.memory_rss_mb} MB)</span>`
            : '<span class="text-muted">-</span>';

          // Профиль
          const profInfo = u.profile_size_mb > 0 
            ? `<span title="${u.profile_path}">${u.profile_size_mb} MB</span>`
            : (u.profile_path ? `<span class="text-muted" title="${u.profile_path}">Локальный</span>` : '<span class="text-muted">-</span>');

          // Группы
          const groupsStr = (u.groups && u.groups.length > 0) ? u.groups.join(', ') : 'Users';

          return `
            <tr class="winadmin-user-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для просмотра полного досье пользователя и AI-аудита">
              <td>
                <div class="d-flex align-items-center gap-1.5">
                  <i class="bi bi-person-badge text-info"></i>
                  <div>
                    <span class="fw-semibold text-white">${u.name}</span>
                    <div class="mt-0.5">${badges.join('')}</div>
                  </div>
                </div>
              </td>
              <td>
                <div class="text-truncate text-secondary" style="max-width: 140px;" title="${groupsStr}">${groupsStr}</div>
                <div class="font-monospace text-muted small text-truncate" style="max-width: 130px;" title="${u.sid}">${u.sid.slice(-10) || '-'}</div>
              </td>
              <td class="small">
                ${profInfo}
              </td>
              <td class="small font-monospace">
                ${resInfo}
              </td>
              <td>${statusBadge}</td>
              <td style="text-align: right;">
                <button class="btn btn-xs btn-outline-info py-0 px-2 btn-inspect-user me-1" data-user="${u.name}" title="Досье и метрики">
                  Досье
                </button>
                ${u.is_logged_in ? `
                  <button class="btn btn-xs btn-outline-danger py-0 px-1.5 btn-disconnect-user" data-user="${u.name}" title="Отключить сессию">
                    Выход
                  </button>
                ` : ''}
              </td>
            </tr>
          `;
        }).join('');

        // Клик по строке для открытия досье
        tbody.querySelectorAll('.winadmin-user-row').forEach(row => {
          row.onclick = (evt) => {
            if (evt.target.closest('.btn-disconnect-user')) return;
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const u = accounts[idx];
            if (!u) return;

            openUserDossier(u);
          };
        });

        // Кнопки "Досье"
        tbody.querySelectorAll('.btn-inspect-user').forEach(btn => {
          btn.onclick = (evt) => {
            evt.stopPropagation();
            const username = btn.getAttribute('data-user');
            const u = accounts.find(a => a.name === username);
            if (u) openUserDossier(u);
          };
        });

        // Кнопки "Выход"
        tbody.querySelectorAll('.btn-disconnect-user').forEach(btn => {
          btn.onclick = async (evt) => {
            evt.stopPropagation();
            const user = btn.getAttribute('data-user');
            if (confirm(`Отключить сессию пользователя ${user}?`)) {
              await fetch(`/api/sysadmin/users/${user}/disconnect`, { method: 'POST' });
              fetchAccounts();
              fetchStatus();
            }
          };
        });
      }
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch accounts:', e);
    }
  }

  function openUserDossier(u) {
    if (!window.AITableModal) return;

    const metadata = [
      { label: 'Имя пользователя', value: u.name },
      { label: 'Полное имя', value: u.full_name || 'Не указано' },
      { label: 'Описание', value: u.description || 'Отсутствует' },
      { label: 'SID пользователя', value: u.sid || 'N/A' },
      { label: 'Тип аккаунта', value: `${u.account_type} (${u.is_admin ? 'Администратор' : 'Обычный'})` },
      { label: 'Скрытая учетная запись', value: u.is_hidden ? 'Да (SpecialAccounts / Built-in)' : 'Нет' },
      { label: 'Учетная запись включена', value: u.enabled ? 'Да' : 'Отключена' },
      { label: 'Членство в группах', value: (u.groups && u.groups.length > 0) ? u.groups.join(', ') : 'Users' },
      { label: 'Путь к профилю', value: u.profile_path || 'Не создан' },
      { label: 'Размер профиля на диске', value: `${u.profile_size_mb} MB` },
      { label: 'Последняя смена пароля', value: u.password_last_set || 'N/A' },
      { label: 'Неверных попыток пароля', value: String(u.bad_password_count || 0) },
      { label: 'Последний вход в систему', value: u.last_logon || 'Не зафиксирован' },
      { label: 'Активных процессов', value: `${u.process_count} (RAM: ${u.memory_rss_mb} MB, CPU: ${u.cpu_percent}%)` }
    ];

    const badges = [
      { text: u.is_logged_in ? 'Online' : 'Offline', class: u.is_logged_in ? 'badge bg-success' : 'badge bg-secondary' }
    ];
    if (u.is_admin) badges.push({ text: 'Администратор', class: 'badge bg-warning text-dark' });
    if (u.is_hidden) badges.push({ text: 'Скрытый', class: 'badge bg-purple text-white' });
    if (!u.enabled) badges.push({ text: 'Отключен', class: 'badge bg-danger' });

    window.AITableModal.show({
      icon: '👤',
      title: `Учетная запись: ${u.name}`,
      subtitle: `${u.full_name ? u.full_name + ' | ' : ''}SID: ${u.sid}`,
      tableType: 'user_account',
      badges: badges,
      metadata: metadata,
      rawTitle: 'Полная конфигурация и метрики пользователя',
      rawContent: JSON.stringify(u, null, 2),
      requestData: {
        username: u.name,
        is_admin: u.is_admin,
        is_hidden: u.is_hidden,
        groups: u.groups,
        process_count: u.process_count,
        memory_rss_mb: u.memory_rss_mb,
        profile_path: u.profile_path
      }
    });
  }

  async function fetchEvents() {
    try {
      const res = await fetch('/api/sysadmin/events?hours=24');
      if (!res.ok) return;
      const data = await res.json();
      const events = data.events || [];
      
      const tbody = document.getElementById('winadmin-events-tbody');
      const badge = document.getElementById('winadmin-events-badge');
      if (badge) badge.innerText = `${events.length} записей`;

      if (tbody) {
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted p-3">События не зафиксированы</td></tr>';
          return;
        }
        const displayEvents = events.slice(0, 30);
        tbody.innerHTML = displayEvents.map((e, idx) => `
          <tr class="winadmin-event-row" data-idx="${idx}" style="cursor: pointer;" title="Нажмите для AI-диагностики события">
            <td class="font-monospace text-muted small">${e.timestamp?.slice(11, 19) || ''}</td>
            <td class="font-monospace fw-semibold text-info">${e.event_id}</td>
            <td><span class="badge ${e.level === 'Warning' ? 'bg-warning-subtle text-warning' : (e.level === 'Error' ? 'bg-danger-subtle text-danger' : 'bg-info-subtle text-info')}">${e.level}</span></td>
            <td class="small text-light">${e.source}: ${e.description}</td>
          </tr>
        `).join('');

        tbody.querySelectorAll('.winadmin-event-row').forEach(row => {
          row.onclick = () => {
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const e = displayEvents[idx];
            if (!e) return;

            if (window.AITableModal) {
              window.AITableModal.show({
                icon: '📋',
                title: `Событие #${e.event_id} (${e.source})`,
                subtitle: `Уровень: ${e.level} | ${e.timestamp || ''}`,
                tableType: 'generic',
                badges: [
                  { text: e.level || 'Info', class: 'badge bg-info text-dark' }
                ],
                metadata: [
                  { label: 'Event ID', value: String(e.event_id) },
                  { label: 'Источник / Provider', value: e.source },
                  { label: 'Уровень важности', value: e.level },
                  { label: 'Время регистрации', value: e.timestamp }
                ],
                rawTitle: 'Текст сообщения журнала',
                rawContent: e.description || '',
                requestData: {
                  event_id: e.event_id,
                  source: e.source,
                  level: e.level,
                  description: e.description
                }
              });
            }
          };
        });
      }
    } catch (e) {
      console.error('[WinAdminTab] Failed to fetch events:', e);
    }
  }

  function initWindowsAdminTab() {
    console.log('[WinAdminTab] Initializing Windows Sysadmin User Metrics & Security tab...');
    fetchStatus();
    fetchAccounts('all');
    fetchEvents();

    if (!isWinAdminInitialized) {
      const refreshBtn = document.getElementById('btn-winadmin-refresh');
      const configBtn = document.getElementById('btn-winadmin-config');

      if (refreshBtn) {
        refreshBtn.onclick = () => {
          fetchStatus();
          fetchAccounts(currentUserFilter);
          fetchEvents();
        };
      }

      // Фильтры пользователей
      const filterGroup = document.getElementById('winadmin-user-filters');
      if (filterGroup) {
        filterGroup.querySelectorAll('.winadmin-filter-btn').forEach(btn => {
          btn.onclick = () => {
            filterGroup.querySelectorAll('.winadmin-filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentUserFilter = btn.getAttribute('data-filter') || 'all';
            fetchAccounts(currentUserFilter);
          };
        });
      }

      if (configBtn) {
        configBtn.onclick = () => {
          if (typeof window.openAppConfigModal === 'function') {
            window.openAppConfigModal('windows_sysadmin', 'Windows System Administrator');
          }
        };
      }

      isWinAdminInitialized = true;
    }
  }

  window.initWindowsAdminTab = initWindowsAdminTab;
})();
