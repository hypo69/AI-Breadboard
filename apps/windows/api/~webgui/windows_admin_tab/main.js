/**
 * =============================================================================
 * Process Name: Windows Windows Admin Tab - Main Script
 * =============================================================================
 * Description:
 *   Клиентский скрипт управления интерфейсом модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/~webgui/windows_admin_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: windows/api/~webgui/windows_admin_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:04:40
 * =============================================================================
 */

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

      if (hostEl) hostEl.innerText = `${data.hostname || 'LOCAL'} / ${data.domain || 'WORKGROUPi18n.t('auto__if_usercountel_usercountel_innertext_data_total_accounts_data_user_count_0_data_active_users_0_if_userbreakdownel_userbreakdownel_innertext_data_hidden_users_0_if_adstatusel_adstatusel_innertext_data_ad_connected__727ca8')Подключен' : i18n.t('auto___40fea1');
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
      const badge = document.getElementById('winadmin-users-badgei18n.t('auto__if_badge_badge_innertext_accounts_length_data_total_accounts_length_if_tbody_if_accounts_length_0_tbody_innerhtml__bb02f2')<tr><td colspan="6" class="text-center text-muted p-3">Учетные записи по выбранному фильтру не найдены</td></tr>i18n.t('auto__return_tbody_innerhtml_accounts_map_u_idx_const_badges_if_u_is_admin_badges_push__f76aa4')<span class="badge badge-admin me-1">Admin</span>');
          if (u.is_hidden) badges.push('<span class="badge badge-hidden me-1">Скрытый</span>');
          if (!u.enabled) badges.push('<span class="badge badge-disabled me-1">Отключен</span>i18n.t('auto__let_statusbadge__542bd2')<span class="badge bg-secondary">Офлайн</span>';
          if (u.is_logged_in) {
            statusBadge = '<span class="badge bg-success-subtle text-success border border-success">● В сети</span>';
          } else if (!u.enabled) {
            statusBadge = '<span class="badge bg-dark text-muted">Отключен</span>';
          }

          // Ресурсы
          const resInfo = u.process_count > 0 
            ? `<span class="text-infoi18n.t('auto__u_process_count_span_span_class__c12739')text-muted">(${u.memory_rss_mb} MB)</span>`
            : '<span class="text-muted">-</span>';

          // Профиль
          const profInfo = u.profile_size_mb > 0 
            ? `<span title="${u.profile_path}">${u.profile_size_mb} MB</span>`
            : (u.profile_path ? `<span class="text-muted" title="${u.profile_path}">Локальный</span>` : '<span class="text-muted">-</span>i18n.t('auto__const_groupsstr_u_groups_u_groups_length_0_u_groups_join__ce06f0'), ') : 'Users';

          return `
            <tr class="winadmin-user-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto__ai__a425d1')>
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
                <button class="btn btn-xs btn-outline-info py-0 px-2 btn-inspect-user me-1" data-user="${u.name}" title=i18n.t('auto___80659e')>
                  Досье
                </button>
                ${u.is_logged_in ? `
                  <button class="btn btn-xs btn-outline-danger py-0 px-1.5 btn-disconnect-user" data-user="${u.name}" title=i18n.t('auto___c0b220')>
                    Выход
                  </button>
                ` : ''}
              </td>
            </tr>
          `;
        }).join('i18n.t('auto__tbody_queryselectorall__ef80d8').winadmin-user-row').forEach(row => {
          row.onclick = (evt) => {
            if (evt.target.closest('.btn-disconnect-user')) return;
            const idx = parseInt(row.getAttribute('data-idx'), 10);
            const u = accounts[idx];
            if (!u) return;

            openUserDossier(u);
          };
        });

        // Кнопки i18n.t('auto___003172')
        tbody.querySelectorAll('.btn-inspect-user').forEach(btn => {
          btn.onclick = (evt) => {
            evt.stopPropagation();
            const username = btn.getAttribute('data-user');
            const u = accounts.find(a => a.name === username);
            if (u) openUserDossier(u);
          };
        });

        // Кнопки i18n.t('auto___c42457')
        tbody.querySelectorAll('.btn-disconnect-user').forEach(btn => {
          btn.onclick = async (evt) => {
            evt.stopPropagation();
            const user = btn.getAttribute('data-useri18n.t('auto__if_confirm_user_await_fetch_api_sysadmin_users_user_disconnect_method__bfb547')POST' });
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
      { label: i18n.t('auto___a79f8a'), value: u.name },
      { label: i18n.t('auto___ce2153'), value: u.full_name || i18n.t('auto___5696d9') },
      { label: i18n.t('auto___f5441f'), value: u.description || i18n.t('auto___f2f7a8') },
      { label: i18n.t('auto_sid__1240a2'), value: u.sid || 'N/A' },
      { label: i18n.t('auto___3d10ce'), value: `${u.account_type} (${u.is_admin ? i18n.t('auto___36d00f') : i18n.t('auto___a2c84d')})` },
      { label: i18n.t('auto___d1bf08'), value: u.is_hidden ? i18n.t('auto__specialaccounts_built_in__bda138') : i18n.t('auto___f82a82') },
      { label: i18n.t('auto___55b5a4'), value: u.enabled ? i18n.t('auto___8d2fab') : i18n.t('auto___f262f3') },
      { label: i18n.t('auto___7527d9'), value: (u.groups && u.groups.length > 0) ? u.groups.join(', ') : 'Users' },
      { label: i18n.t('auto___d96f4c'), value: u.profile_path || i18n.t('auto___07a838') },
      { label: i18n.t('auto___845157'), value: `${u.profile_size_mb} MB` },
      { label: i18n.t('auto___0fb011'), value: u.password_last_set || 'N/A' },
      { label: i18n.t('auto___644d9f'), value: String(u.bad_password_count || 0) },
      { label: i18n.t('auto___86bfe4'), value: u.last_logon || i18n.t('auto___e5abe5') },
      { label: i18n.t('auto___010d55'), value: `${u.process_count} (RAM: ${u.memory_rss_mb} MB, CPU: ${u.cpu_percent}%)` }
    ];

    const badges = [
      { text: u.is_logged_in ? 'Online' : 'Offline', class: u.is_logged_in ? 'badge bg-success' : 'badge bg-secondary' }
    ];
    if (u.is_admin) badges.push({ text: i18n.t('auto___36d00f'), class: 'badge bg-warning text-dark' });
    if (u.is_hidden) badges.push({ text: i18n.t('auto___1bde0d'), class: 'badge bg-purple text-white' });
    if (!u.enabled) badges.push({ text: i18n.t('auto___cadea0'), class: 'badge bg-danger' });

    window.AITableModal.show({
      icon: '👤i18n.t('auto__title_u_name_subtitle_u_full_name_u_full_name__f3dccb') | ' : ''}SID: ${u.sid}`,
      tableType: 'user_account',
      badges: badges,
      metadata: metadata,
      rawTitle: i18n.t('auto___85acdf'),
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
      const badge = document.getElementById('winadmin-events-badgei18n.t('auto__if_badge_badge_innertext_events_length_if_tbody_if_events_length_0_tbody_innerhtml__a27213')<tr><td colspan="4" class="text-center text-muted p-3">События не зафиксированы</td></tr>';
          return;
        }
        const displayEvents = events.slice(0, 30);
        tbody.innerHTML = displayEvents.map((e, idx) => `
          <tr class="winadmin-event-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto__ai__638c45')>
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
                icon: '📋i18n.t('auto__title_e_event_id_e_source_subtitle_e_level_e_timestamp__53be63')'}`,
                tableType: 'generic',
                badges: [
                  { text: e.level || 'Info', class: 'badge bg-info text-dark' }
                ],
                metadata: [
                  { label: 'Event ID', value: String(e.event_id) },
                  { label: i18n.t('auto__provider_598756'), value: e.source },
                  { label: i18n.t('auto___e7d258'), value: e.level },
                  { label: i18n.t('auto___4eba0e'), value: e.timestamp }
                ],
                rawTitle: i18n.t('auto___617ac7'),
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
      const configBtn = document.getElementById('btn-winadmin-configi18n.t('auto__if_refreshbtn_refreshbtn_onclick_fetchstatus_fetchaccounts_currentuserfilter_fetchevents_const_filtergroup_document_getelementbyid__866c68')winadmin-user-filters');
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
