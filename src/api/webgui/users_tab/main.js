/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/users_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/users_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

// =============================================================================
// Webinterface: Users Tab Logic
// Module: webinterface/users_tab/main.js
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

'use strict';

(function () {
  const state = {
    users: [],
    stats: {
      total: 0,
      active: 0,
      admins: 0,
      telegram: 0
    },
    filterRole: '',
    filterStatus: '',
    searchQuery: '',
    editingUserId: null,
    savingUserId: null,
    isLoading: false,
    initialized: false
  };

  // Helper API fetch
  async function apiFetch(url, options = {}) {
    if (window.api && typeof window.api.fetch === 'function') {
      return window.api.fetch(url, options);
    }
    const res = await fetch(url, options);
    if (!res.ok) {
      let errMsg = `HTTP ${res.status}`;
      try {
        const errData = await res.json();
        if (errData && errData.detail) {
          errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
        }
      } catch (_) {}
      throw new Error(errMsg);
    }
    return res.json();
  }

  // Show notification
  function showStatusAlert(msg, type = 'info') {
    const alertBox = document.getElementById('users-alert-box');
    const alertMsg = document.getElementById('users-alert-message');
    if (!alertBox || !alertMsg) return;

    alertBox.className = `alert alert-${type} alert-dismissible fade show mb-3`;
    alertMsg.innerHTML = msg;
    alertBox.classList.remove('d-none');

    setTimeout(() => {
      alertBox.classList.add('d-none');
    }, 5000);
  }

  // Generate secure password
  function generatePassword(length = 12) {
    const charset = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%&*';
    let pwd = '';
    const randomValues = new Uint32Array(length);
    window.crypto.getRandomValues(randomValues);
    for (let i = 0; i < length; i++) {
      pwd += charset[randomValues[i] % charset.length];
    }
    return pwd;
  }

  // Escape HTML
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Format datetime
  function formatDate(isoStr) {
    if (!isoStr) return '<span class="text-muted">—</span>';
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return escapeHtml(isoStr);
      return `<span title="${escapeHtml(isoStr)}">${d.toLocaleDateString('ru-RU')} <small class="text-muted">${d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}</small></span>`;
    } catch (_) {
      return escapeHtml(isoStr);
    }
  }

  // Load Users List from Backend
  async function loadUsers() {
    state.isLoading = true;
    const tableBody = document.getElementById('users-table-body');
    const countBadge = document.getElementById('users-count-badge');

    if (tableBody && (!state.users || state.users.length === 0)) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-4 text-muted">
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
            Загрузка списка пользователей...
          </td>
        </tr>`;
    }

    try {
      const params = new URLSearchParams();
      if (state.searchQuery) params.append('q', state.searchQuery);
      if (state.filterRole) params.append('role', state.filterRole);
      if (state.filterStatus) params.append('status', state.filterStatus);

      const url = `/api/admin/users?${params.toString()}`;
      const data = await apiFetch(url);

      state.users = data.users || [];
      if (data.stats) {
        state.stats = data.stats;
      }

      renderStats();
      renderTable();
    } catch (err) {
      console.error('[UsersTab] Error loading users:i18n.t('auto__err_showstatusalert_err_message__259d09')danger');
      if (tableBody) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="8" class="text-center py-4 text-danger">
              <i class="bi bi-exclamation-octagon fs-4 d-block mb-1"></i>
              Не удалось загрузить пользователей: ${escapeHtml(err.message)}
            </td>
          </tr>`;
      }
    } finally {
      state.isLoading = false;
    }
  }

  // Render Metric Cards
  function renderStats() {
    const totalEl = document.getElementById('stat-total-users');
    const activeEl = document.getElementById('stat-active-users');
    const adminEl = document.getElementById('stat-admin-users');
    const tgEl = document.getElementById('stat-tg-users');

    if (totalEl) totalEl.textContent = state.stats.total || 0;
    if (activeEl) activeEl.textContent = state.stats.active || 0;
    if (adminEl) adminEl.textContent = state.stats.admins || 0;
    if (tgEl) tgEl.textContent = state.stats.telegram || 0;
  }

  // Render Users Table
  function renderTable() {
    const tableBody = document.getElementById('users-table-body');
    const countBadge = document.getElementById('users-count-badge');
    if (!tableBody) return;

    if (countBadge) {
      countBadge.textContent = `Показано: ${state.users.length} из ${state.stats.total || state.users.length}`;
    }

    if (state.users.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-5 text-muted">
            <i class="bi bi-person-x fs-2 d-block mb-2 text-secondary"></i>
            Пользователи не найдены.
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = state.users.map((user) => {
      const isRoot = user.id === 1;
      const isAdmin = Boolean(user.is_admin || user.role === 'admin');
      const isActive = Boolean(user.is_active);
      const isEmailVerified = Boolean(user.is_email_verified);
      const hasPassword = Boolean(user.has_password);
      const isRowEditing = (state.editingUserId === user.id);
      const isSaving = (state.savingUserId === user.id);

      // User Initials or Avatar
      let avatarHtml = '';
      if (user.picture) {
        avatarHtml = `<img src="${escapeHtml(user.picture)}" class="rounded-circle me-2 flex-shrink-0" style="width:36px;height:36px;object-fit:cover;" alt="avatar">`;
      } else {
        const initial = (user.name || user.email || 'U').charAt(0).toUpperCase();
        const bgClass = isAdmin ? 'bg-warning text-dark' : 'bg-primary text-white';
        avatarHtml = `<div class="rounded-circle ${bgClass} d-flex align-items-center justify-content-center me-2 flex-shrink-0 fw-bold" style="width:36px;height:36px;font-size:14px;">${escapeHtml(initial)}</div>`;
      }

      // Password column
      const pwdHtml = hasPassword
        ? `<span class="badge bg-success-subtle text-success border border-success-subtle" title=i18n.t('auto___568825')><i class="bi bi-key-filli18n.t('auto__i_span_span_class__8abff5')badge bg-warning-subtle text-warning border border-warning-subtle" title=i18n.t('auto__oauth_tg__f81793')><i class="bi bi-dash-circlei18n.t('auto__i_span_email_verified_badge_const_emailverifiedbadge_isemailverified_i_class__f74fef')bi bi-patch-check-fill text-success ms-1" title=i18n.t('auto_email__2056c7')></i>`
        : `<i class="bi bi-question-circle text-muted ms-1" title=i18n.t('auto_email__d7d8b2')></i>`;

      // If this row is in inline-edit mode:
      if (isRowEditing) {
        return `
          <tr data-user-id="${user.id}" class="table-active border-primary">
            <td class="text-center text-muted fw-bold align-middle">${user.id}</td>
            <td class="align-middle">
              <div class="d-flex align-items-center">
                ${avatarHtml}
                <div class="w-100">
                  <div class="input-group input-group-sm mb-1">
                    <span class="input-group-text text-muted"><i class="bi bi-person"></i></span>
                    <input type="text" class="form-control inline-edit-name" value="${escapeHtml(user.name || '')}" placeholder=i18n.t('auto___a79f8a')>
                  </div>
                  <div class="input-group input-group-sm">
                    <span class="input-group-text text-muted"><i class="bi bi-envelope"></i></span>
                    <input type="email" class="form-control inline-edit-email" value="${escapeHtml(user.email || '')}" placeholder="Email">
                  </div>
                </div>
              </div>
            </td>
            <td class="text-center align-middle">
              <select class="form-select form-select-sm inline-edit-role" ${isRoot ? 'disabled' : ''}>
                <option value="user" ${user.role === 'user' ? 'selected' : ''}>👤 User</option>
                <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>🛡️ Admin</option>
                <option value="guest" ${user.role === 'guest' ? 'selected' : ''}>👀 Guest</option>
              </select>
            </td>
            <td class="text-center align-middle">
              <select class="form-select form-select-sm inline-edit-status" ${isRoot ? 'disabled' : ''}>
                <option value="1" ${isActive ? 'selected' : ''}>🟢 Активен</option>
                <option value="0" ${!isActive ? 'selected' : ''}>🔴 Блок</option>
              </select>
            </td>
            <td class="align-middle">
              <div class="input-group input-group-sm">
                <span class="input-group-text text-info"><i class="bi bi-telegram"></i></span>
                <input type="text" class="form-control inline-edit-tg" value="${escapeHtml(user.telegram_username || '')}" placeholder="Username">
              </div>
            </td>
            <td class="text-center align-middle">${pwdHtml}</td>
            <td class="small align-middle">
              <div><span class="text-mutedi18n.t('auto__span_formatdate_user_created_at_div_td_td_class__085b04')text-center align-middle">
              <div class="d-flex justify-content-center gap-1">
                <button class="btn btn-success btn-sm btn-save-inline" data-id="${user.id}" title=i18n.t('auto__enter__8f6294') ${isSaving ? 'disabled' : ''}>
                  ${isSaving ? '<span class="spinner-border spinner-border-sm"></span>' : '<i class="bi bi-check-lg"></i>'}
                </button>
                <button class="btn btn-outline-secondary btn-sm btn-cancel-inline" data-id="${user.id}" title=i18n.t('auto__esc__c1fe34') ${isSaving ? 'disabled' : ''}>
                  <i class="bi bi-x-lg"></i>
                </button>
              </div>
            </td>
          </tr>
        `;
      }

      // Normal view mode with DIRECT editable table fields:
      const roleSelectHtml = `
        <select class="form-select form-select-sm bg-dark border-secondary user-table-role-select text-center ${isAdmin ? 'text-warning fw-bold' : 'text-info'}"
          data-user-id="${user.id}"
          ${isRoot ? 'disabled title=i18n.t('auto__root_e84a4a')' : 'title=i18n.t('auto___8fe52e')'}>
          <option value="user" ${user.role === 'user' ? 'selected' : ''} class="text-info">👤 User</option>
          <option value="admin" ${isAdmin ? 'selected' : ''} class="text-warning">🛡️ Admin</option>
          <option value="guest" ${user.role === 'guest' ? 'selected' : ''} class="text-secondary">👀 Guest</option>
        </select>
      `;

      const statusSelectHtml = `
        <select class="form-select form-select-sm bg-dark border-secondary user-table-status-select text-center ${isActive ? 'text-success' : 'text-danger'}"
          data-user-id="${user.id}"
          ${isRoot ? 'disabled title=i18n.t('auto__root_b0e6c8')' : 'title=i18n.t('auto___ed143b')'}>
          <option value="1" ${isActive ? 'selected' : ''} class="text-successi18n.t('auto__option_option_value__152f29')0" ${!isActive ? 'selected' : ''} class="text-danger">🔴 Блок</option>
        </select>
      `;

      // Telegram column
      let tgHtml = '<span class="text-muted small">—</span>';
      if (user.telegram_username) {
        tgHtml = `<a href="https://t.me/${escapeHtml(user.telegram_username)}" target="_blank" class="text-info text-decoration-none small d-flex align-items-center gap-1" title=i18n.t('auto__telegram_7e4345')>
          <i class="bi bi-telegram"></i> @${escapeHtml(user.telegram_username)}
        </a>`;
      } else if (user.telegram_id) {
        tgHtml = `<span class="text-muted small" title="Telegram ID"><i class="bi bi-telegram text-info"></i> ID: ${escapeHtml(user.telegram_id)}</span>`;
      }

      return `
        <tr data-user-id="${user.id}">
          <td class="text-center text-muted fw-bold align-middle">${user.id}</td>
          <td class="align-middle">
            <div class="d-flex align-items-center justify-content-between">
              <div class="d-flex align-items-center">
                ${avatarHtml}
                <div>
                  <div class="fw-bold text-white user-cell-name" title=i18n.t('auto___8a4c6d') style="cursor: pointer;">
                    ${escapeHtml(user.name || i18n.t('auto___cdf641'))}
                    <i class="bi bi-pencil-fill text-muted ms-1 opacity-25 hover-opacity-100" style="font-size:10px;"></i>
                  </div>
                  <div class="small text-muted d-flex align-items-center user-cell-email" title=i18n.t('auto___8a4c6d') style="cursor: pointer;">
                    ${escapeHtml(user.email)} ${emailVerifiedBadge}
                  </div>
                </div>
              </div>
            </div>
          </td>
          <td class="text-center align-middle" style="min-width: 130px;">${roleSelectHtml}</td>
          <td class="text-center align-middle" style="min-width: 125px;">${statusSelectHtml}</td>
          <td class="align-middle" style="min-width: 140px;">
            <div class="d-flex align-items-center justify-content-between">
              <div class="user-cell-tg" title=i18n.t('auto___8a4c6d') style="cursor: pointer;">${tgHtml}</div>
            </div>
          </td>
          <td class="text-center align-middle">${pwdHtml}</td>
          <td class="small align-middle">
            <div><span class="text-mutedi18n.t('auto__span_formatdate_user_created_at_div_user_last_login_div_span_class__cb208c')text-muted">Вход:</span> ${formatDate(user.last_login)}</div>` : ''}
          </td>
          <td class="text-center align-middle">
            <div class="btn-group btn-group-sm" role="group">
              <button class="btn btn-outline-warning btn-inline-edit" data-id="${user.id}" title=i18n.t('auto___b2fb8d')>
                <i class="bi bi-pencil-square"></i>
              </button>
              <button class="btn btn-outline-info btn-pwd-user" data-id="${user.id}" data-name="${escapeHtml(user.name || user.email)}" title=i18n.t('auto___3fda03')>
                <i class="bi bi-key-fill"></i>
              </button>
              <button class="btn btn-outline-light btn-details-user" data-id="${user.id}" title=i18n.t('auto___97bd04')>
                <i class="bi bi-info-circle-fill"></i>
              </button>
              <button class="btn btn-outline-secondary btn-edit-user-modal" data-id="${user.id}" title=i18n.t('auto___039ae4')>
                <i class="bi bi-sliders"></i>
              </button>
              <button class="btn btn-outline-danger btn-delete-user" data-id="${user.id}" data-name="${escapeHtml(user.name || user.email)}" ${isRoot ? 'disabled title=i18n.t('auto__root_1c90df')' : 'title=i18n.t('auto___86ea33')'}>
                <i class="bi bi-trash-fill"></i>
              </button>
            </div>
          </td>
        </tr>`;
    }).join('');

    attachTableEvents();
  }

  // Attach Table Action Button Events
  function attachTableEvents() {
    // Direct Table Role Selector Change
    document.querySelectorAll('.user-table-role-select').forEach(sel => {
      sel.addEventListener('change', async (e) => {
        const userId = parseInt(e.target.getAttribute('data-user-id'), 10);
        const newRole = e.target.value;
        const isAdmin = (newRole === 'admin') ? 1 : 0;
        await handleUpdateField(userId, { role: newRole, is_admin: isAdmin }, `Роль изменена на "${newRole}"`);
      });
    });

    // Direct Table Status Selector Change
    document.querySelectorAll('.user-table-status-select').forEach(sel => {
      sel.addEventListener('change', async (e) => {
        const userId = parseInt(e.target.getAttribute('data-user-id'), 10);
        const newStatus = parseInt(e.target.value, 10);
        await handleUpdateField(userId, { is_active: newStatus }, `Статус изменен на "${newStatus ? i18n.t('auto___667904') : i18n.t('auto___2c998b')}"`);
      });
    });

    // Double-click row or name/email/tg to enter inline-edit mode
    document.querySelectorAll('#users-table-body tr').forEach(row => {
      const userId = parseInt(row.getAttribute('data-user-id'), 10);
      if (!userId) return;

      const nameEl = row.querySelector('.user-cell-name');
      const emailEl = row.querySelector('.user-cell-email');
      const tgEl = row.querySelector('.user-cell-tg');

      [nameEl, emailEl, tgEl].forEach(el => {
        if (el) {
          el.addEventListener('dblclick', () => {
            state.editingUserId = userId;
            renderTable();
          });
        }
      });
    });

    // Inline Edit Button
    document.querySelectorAll('.btn-inline-edit').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        state.editingUserId = userId;
        renderTable();
      });
    });

    // Inline Cancel Button
    document.querySelectorAll('.btn-cancel-inline').forEach(btn => {
      btn.addEventListener('click', () => {
        state.editingUserId = null;
        renderTable();
      });
    });

    // Inline Save Button
    document.querySelectorAll('.btn-save-inline').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        await saveInlineRow(userId);
      });
    });

    // Enter & Escape key handling in inline inputs
    document.querySelectorAll('.inline-edit-name, .inline-edit-email, .inline-edit-tg').forEach(inp => {
      inp.addEventListener('keydown', async (e) => {
        const tr = inp.closest('tr');
        const userId = tr ? parseInt(tr.getAttribute('data-user-id'), 10) : null;
        if (!userId) return;

        if (e.key === 'Enter') {
          e.preventDefault();
          await saveInlineRow(userId);
        } else if (e.key === 'Escape') {
          e.preventDefault();
          state.editingUserId = null;
          renderTable();
        }
      });
    });

    // Modal Edit User Button
    document.querySelectorAll('.btn-edit-user-modal').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        openEditModal(userId);
      });
    });

    // Change Password Button
    document.querySelectorAll('.btn-pwd-user').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        const userName = e.currentTarget.getAttribute('data-name');
        openPasswordModal(userId, userName);
      });
    });

    // View Details Button
    document.querySelectorAll('.btn-details-user').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        openDetailsModal(userId);
      });
    });

    // Delete User Button
    document.querySelectorAll('.btn-delete-user').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        const userName = e.currentTarget.getAttribute('data-name');
        openDeleteModal(userId, userName);
      });
    });
  }

  // Save Inline Row Changes
  async function saveInlineRow(userId) {
    const row = document.querySelector(`tr[data-user-id="${userId}"]`);
    if (!row) return;

    const nameInput = row.querySelector('.inline-edit-name');
    const emailInput = row.querySelector('.inline-edit-email');
    const roleSelect = row.querySelector('.inline-edit-role');
    const statusSelect = row.querySelector('.inline-edit-status');
    const tgInput = row.querySelector('.inline-edit-tg');

    const name = nameInput ? nameInput.value.trim() : '';
    const email = emailInput ? emailInput.value.trim() : '';
    const role = roleSelect ? roleSelect.value : 'user';
    const isActive = statusSelect ? parseInt(statusSelect.value, 10) : 1;
    const tg = tgInput ? tgInput.value.trim().replace(/^@/, '') : '';

    if (!email) {
      showStatusAlert(i18n.t('auto_email__a16736'), 'warning');
      return;
    }
    if (!name) {
      showStatusAlert(i18n.t('auto___2e7abb'), 'warning');
      return;
    }

    const payload = {
      name: name,
      email: email,
      role: role,
      is_admin: (role === 'admin') ? 1 : 0,
      is_active: isActive,
      telegram_username: tg
    };

    state.savingUserId = userId;
    const saveBtn = row.querySelector('.btn-save-inline');
    if (saveBtn) saveBtn.disabled = true;

    try {
      const res = await apiFetch(`/api/admin/users/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_payload_state_editinguserid_null_showstatusalert_userid_strong_escapehtml_name_strong__4195bd')successi18n.t('auto__loadusers_catch_err_showstatusalert_err_message__55dca6')danger');
    } finally {
      state.savingUserId = null;
      if (saveBtn) saveBtn.disabled = false;
    }
  }

  // Update a Single Field or Subset of Fields
  async function handleUpdateField(userId, payload, successMsg = i18n.t('auto___927e83')) {
    try {
      const res = await apiFetch(`/api/admin/users/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_payload_update_local_state_user_const_user_state_users_find_u_u_id_userid_if_user_res_user_object_assign_user_res_user_showstatusalert_userid_successmsg__35129d')successi18n.t('auto__loadusers_catch_err_showstatusalert_err_message__fc6bc6')danger');
      loadUsers();
    }
  }

  // Open Edit Modal
  function openEditModal(userId) {
    const user = state.users.find(u => u.id === userId);
    if (!user) return;

    const isEditAdmin = Boolean(user.is_admin || user.role === 'admin');
    document.getElementById('edit-user-id').value = user.id;
    document.getElementById('edit-user-id-badge').textContent = user.id;
    document.getElementById('edit-user-email').value = user.email || '';
    document.getElementById('edit-user-name').value = user.name || '';
    
    const editAdminSw = document.getElementById('edit-user-is-admin');
    const editRoleLabel = document.getElementById('edit-role-label');
    if (editAdminSw) {
      editAdminSw.checked = isEditAdmin;
      editAdminSw.disabled = (userId === 1);
      if (editRoleLabel) {
        editRoleLabel.textContent = isEditAdmin ? i18n.t('auto__admin__5514eb') : i18n.t('auto__user__e187b8');
        editRoleLabel.className = isEditAdmin ? 'text-warning' : 'text-info';
      }
    }

    document.getElementById('edit-user-is-active').checked = Boolean(user.is_active);
    document.getElementById('edit-user-verified').checked = Boolean(user.is_email_verified);

    const modalEl = document.getElementById('modal-edit-user');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }

  // Open Password Modal
  function openPasswordModal(userId, userName) {
    document.getElementById('pwd-user-id').value = userId;
    document.getElementById('pwd-user-target').textContent = `${userName} (ID #${userId})`;
    document.getElementById('pwd-input-val').value = '';

    const modalEl = document.getElementById('modal-password-user');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }

  // Open Details Modal
  async function openDetailsModal(userId) {
    const modalEl = document.getElementById('modal-details-user');
    const contentEl = document.getElementById('details-user-content');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();

    contentEl.innerHTML = `
      <div class="text-center py-4 text-muted">
        <div class="spinner-border spinner-border-sm text-primary me-2" role="statusi18n.t('auto__div_div_try_const_data_await_apifetch_api_admin_users_userid_const_u_data_user_const_s_data_settings_const_perms_data_permissions_contentel_innerhtml_div_class__ae4d03')row g-3">
          <div class="col-md-6">
            <h6 class="text-primary border-bottom pb-1 mb-2i18n.t('auto__h6_table_class__678bf0')table table-sm table-borderless small mb-0">
              <tr><td class="text-muted" style="width:120px;">ID:</td><td class="fw-bold">${u.id}</td></tr>
              <tr><td class="text-muted">Email:</td><td>${escapeHtml(u.email)} ${u.is_email_verified ? '<span class="badge bg-success">Verified</span>' : '<span class="badge bg-secondary">Unverified</span>'}</td></tr>
              <tr><td class="text-muted">Имя:</td><td>${escapeHtml(u.name || '—')}</td></tr>
              <tr><td class="text-mutedi18n.t('auto__td_td_span_class__dc79c5')badge bg-info text-dark">${escapeHtml(u.role || 'user')}</span> ${u.is_admin ? '<span class="badge bg-warning text-dark">Admin</span>' : ''}</td></tr>
              <tr><td class="text-muted">Статус:</td><td>${u.is_active ? '<span class="text-success">Активен</span>' : '<span class="text-danger">Заблокирован</span>'}</td></tr>
              <tr><td class="text-muted">Пароль:</td><td>${u.has_password ? '<span class="text-success">Установлен</span>' : '<span class="text-muted">Не задан</span>'}</td></tr>
              <tr><td class="text-muted">Создан:</td><td>${escapeHtml(u.created_at || '—')}</td></tr>
              <tr><td class="text-muted">Последний вход:</td><td>${escapeHtml(u.last_login || '—')}</td></tr>
            </table>
          </div>
          <div class="col-md-6">
            <h6 class="text-info border-bottom pb-1 mb-2i18n.t('auto__telegram_h6_table_class__0125bd')table table-sm table-borderless small mb-0">
              <tr><td class="text-muted" style="width:130px;">Telegram ID:</td><td>${u.telegram_id ? escapeHtml(u.telegram_id) : '<span class="text-muted">Не привязан</span>'}</td></tr>
              <tr><td class="text-muted">TG Username:</td><td>${u.telegram_username ? `@${escapeHtml(u.telegram_username)}` : '<span class="text-muted">—</span>'}</td></tr>
              <tr><td class="text-muted">Тема UI:</td><td>${escapeHtml(s.theme || 'dark')}</td></tr>
              <tr><td class="text-muted">Язык:</td><td>${escapeHtml(s.language || 'ru')}</td></tr>
              <tr><td class="text-muted">TTS голос:</td><td>${escapeHtml(s.tts_voice || 'ru-RU-DmitryNeural')} (${escapeHtml(s.tts_system || 'edge-tts')})</td></tr>
              <tr><td class="text-muted">Модель чата:</td><td>${escapeHtml(s.model || i18n.t('auto___469631'))}</td></tr>
            </table>
          </div>
          <div class="col-12 mt-3">
            <h6 class="text-warning border-bottom pb-1 mb-2i18n.t('auto__h6_div_class__731671')d-flex flex-wrap gap-1">
              ${perms.length > 0 ? perms.map(p => `<span class="badge bg-secondary">${escapeHtml(p)}</span>`).join('') : '<span class="text-muted small">Нет явных разрешений</span>'}
            </div>
          </div>
          ${s.system_instruction ? `
          <div class="col-12 mt-2">
            <h6 class="border-bottom pb-1 mb-1i18n.t('auto__h6_pre_class__6a6e25')bg-body-tertiary p-2 rounded border small font-monospace" style="max-height:120px;overflow-y:auto;">${escapeHtml(s.system_instruction)}</pre>
          </div>` : ''}
        </div>`;
    } catch (err) {
      contentEl.innerHTML = `<div class="text-danger py-3">Ошибка загрузки данных: ${escapeHtml(err.message)}</div>`;
    }
  }

  // Open Delete Modal
  function openDeleteModal(userId, userName) {
    document.getElementById('delete-user-id').value = userId;
    document.getElementById('delete-user-name-target').textContent = `${userName} (ID #${userId})`;

    const modalEl = document.getElementById('modal-delete-user');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }

  // Initialize Event Listeners
  function initListeners() {
    // Open Create User Modal
    const btnOpenCreate = document.getElementById('btn-open-create-user');
    if (btnOpenCreate) {
      btnOpenCreate.addEventListener('click', () => {
        const form = document.getElementById('form-create-user');
        if (form) form.reset();
        document.getElementById('create-user-is-admin').checked = false;
        const createRoleLabel = document.getElementById('create-role-label');
        if (createRoleLabel) {
          createRoleLabel.textContent = i18n.t('auto__user__e187b8');
          createRoleLabel.className = 'text-info';
        }
        document.getElementById('create-user-is-active').checked = true;
        document.getElementById('create-user-verified').checked = true;
        const modalEl = document.getElementById('modal-create-user');
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
      });
    }

    // Dynamic Switch Hints
    const createAdminSw = document.getElementById('create-user-is-admin');
    const createRoleLabel = document.getElementById('create-role-label');
    if (createAdminSw && createRoleLabel) {
      createAdminSw.addEventListener('change', (e) => {
        createRoleLabel.textContent = e.target.checked ? i18n.t('auto__admin__5514eb') : i18n.t('auto__user__e187b8');
        createRoleLabel.className = e.target.checked ? 'text-warning' : 'text-info';
      });
    }

    const editAdminSw = document.getElementById('edit-user-is-admin');
    const editRoleLabel = document.getElementById('edit-role-label');
    if (editAdminSw && editRoleLabel) {
      editAdminSw.addEventListener('change', (e) => {
        editRoleLabel.textContent = e.target.checked ? i18n.t('auto__admin__5514eb') : i18n.t('auto__user__e187b8');
        editRoleLabel.className = e.target.checked ? 'text-warning' : 'text-info';
      });
    }

    // Refresh Users Button
    const btnRefresh = document.getElementById('btn-refresh-users');
    if (btnRefresh) {
      btnRefresh.addEventListener('click', () => {
        loadUsers();
      });
    }

    // Search Input with Debounce
    const searchInput = document.getElementById('users-search-input');
    const searchClear = document.getElementById('users-search-clear');
    let debounceTimeout = null;

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        if (searchClear) {
          searchClear.classList.toggle('d-none', !val);
        }
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
          state.searchQuery = val.trim();
          loadUsers();
        }, 300);
      });
    }

    if (searchClear) {
      searchClear.addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        searchClear.classList.add('d-none');
        state.searchQuery = '';
        loadUsers();
      });
    }

    // Role Filter
    const filterRole = document.getElementById('users-filter-role');
    if (filterRole) {
      filterRole.addEventListener('change', (e) => {
        state.filterRole = e.target.value;
        loadUsers();
      });
    }

    // Status Filter
    const filterStatus = document.getElementById('users-filter-status');
    if (filterStatus) {
      filterStatus.addEventListener('change', (e) => {
        state.filterStatus = e.target.value;
        loadUsers();
      });
    }

    // Generator button for create modal
    const btnGenCreatePwd = document.getElementById('btn-gen-create-password');
    if (btnGenCreatePwd) {
      btnGenCreatePwd.addEventListener('click', () => {
        const pwdInput = document.getElementById('create-user-password');
        if (pwdInput) pwdInput.value = generatePassword(12);
      });
    }

    // Generator button for password change modal
    const btnGenPwdVal = document.getElementById('btn-gen-pwd-val');
    if (btnGenPwdVal) {
      btnGenPwdVal.addEventListener('click', () => {
        const pwdInput = document.getElementById('pwd-input-val');
        if (pwdInput) pwdInput.value = generatePassword(12);
      });
    }

    // Create User Form Submit
    const formCreate = document.getElementById('form-create-user');
    if (formCreate) {
      formCreate.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('btn-submit-create-user');
        if (submitBtn) submitBtn.disabled = true;

        const isAdmin = document.getElementById('create-user-is-admin').checked ? 1 : 0;
        const payload = {
          email: document.getElementById('create-user-email').value.trim(),
          name: document.getElementById('create-user-name').value.trim(),
          password: document.getElementById('create-user-password').value.trim(),
          role: isAdmin ? 'admin' : 'user',
          is_admin: isAdmin,
          is_active: document.getElementById('create-user-is-active').checked ? 1 : 0,
          is_email_verified: document.getElementById('create-user-verified').checked ? 1 : 0
        };

        try {
          await apiFetch('/api/admin/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          const modalEl = document.getElementById('modal-create-useri18n.t('auto__const_modal_bootstrap_modal_getinstance_modalel_if_modal_modal_hide_showstatusalert_escapehtml_payload_name__146fc1')successi18n.t('auto__loadusers_catch_err_showstatusalert_err_message__fd85a0')danger');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Edit User Form Submit (Modal)
    const formEdit = document.getElementById('form-edit-user');
    if (formEdit) {
      formEdit.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('btn-submit-edit-user');
        if (submitBtn) submitBtn.disabled = true;

        const userId = parseInt(document.getElementById('edit-user-id').value, 10);
        const isAdmin = document.getElementById('edit-user-is-admin').checked ? 1 : 0;
        const payload = {
          email: document.getElementById('edit-user-email').value.trim(),
          name: document.getElementById('edit-user-name').value.trim(),
          role: isAdmin ? 'admin' : 'user',
          is_admin: isAdmin,
          is_active: document.getElementById('edit-user-is-active').checked ? 1 : 0,
          is_email_verified: document.getElementById('edit-user-verified').checked ? 1 : 0
        };

        try {
          await apiFetch(`/api/admin/users/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          const modalEl = document.getElementById('modal-edit-useri18n.t('auto__const_modal_bootstrap_modal_getinstance_modalel_if_modal_modal_hide_showstatusalert_userid__ca6a3c')successi18n.t('auto__loadusers_catch_err_showstatusalert_err_message__6c7aa0')danger');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Change Password Form Submit
    const formPwd = document.getElementById('form-password-user');
    if (formPwd) {
      formPwd.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('btn-submit-pwd-user');
        if (submitBtn) submitBtn.disabled = true;

        const userId = parseInt(document.getElementById('pwd-user-id').value, 10);
        const newPassword = document.getElementById('pwd-input-val').value.trim();

        try {
          await apiFetch(`/api/admin/users/${userId}/password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: newPassword })
          });
          const modalEl = document.getElementById('modal-password-useri18n.t('auto__const_modal_bootstrap_modal_getinstance_modalel_if_modal_modal_hide_showstatusalert_userid__2c7322')successi18n.t('auto__loadusers_catch_err_showstatusalert_err_message__298e60')danger');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Delete User Confirm Button
    const btnConfirmDelete = document.getElementById('btn-confirm-delete-user');
    if (btnConfirmDelete) {
      btnConfirmDelete.addEventListener('click', async () => {
        btnConfirmDelete.disabled = true;
        const userId = parseInt(document.getElementById('delete-user-id').value, 10);

        try {
          await apiFetch(`/api/admin/users/${userId}`, { method: 'DELETE' });
          const modalEl = document.getElementById('modal-delete-useri18n.t('auto__const_modal_bootstrap_modal_getinstance_modalel_if_modal_modal_hide_showstatusalert_userid__50e877')successi18n.t('auto__loadusers_catch_err_showstatusalert_err_message__77346f')danger');
        } finally {
          btnConfirmDelete.disabled = false;
        }
      });
    }

    // Orphaned Directories Check Button
    const btnCheckOrphaned = document.getElementById('btn-check-orphaned-dirs');
    if (btnCheckOrphaned) {
      btnCheckOrphaned.addEventListener('click', () => {
        const modalEl = document.getElementById('modal-orphaned-dirs');
        if (modalEl) {
          const modal = new bootstrap.Modal(modalEl);
          modal.show();
          loadOrphanedDirs();
        }
      });
    }

    // Orphaned Directories Refresh Button
    const btnRefreshOrphaned = document.getElementById('btn-refresh-orphaned-dirs');
    if (btnRefreshOrphaned) {
      btnRefreshOrphaned.addEventListener('click', () => {
        loadOrphanedDirs();
      });
    }

    // Cleanup All Orphaned Directories Button
    const btnCleanupAll = document.getElementById('btn-cleanup-all-orphaned');
    if (btnCleanupAll) {
      btnCleanupAll.addEventListener('click', async () => {
        if (!confirm(i18n.t('auto___8ada4a'))) {
          return;
        }
        btnCleanupAll.disabled = true;
        try {
          const res = await apiFetch('/api/admin/users/orphaned-dirs/clean', {
            method: 'POST',
            headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_showstatusalert_res_total_deleted_formatbytes_res_freed_bytes__e1c8c3')successi18n.t('auto__loadorphaneddirs_catch_err_showstatusalert_err_message__b60db7')danger');
        } finally {
          btnCleanupAll.disabled = false;
        }
      });
    }
  }

  // Format bytes helper
  function formatBytes(bytes, decimals = 1) {
    if (!bytes || bytes <= 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  // Load Orphaned Directories from Backend
  async function loadOrphanedDirs() {
    const tbody = document.getElementById('orphaned-dirs-tbody');
    const countEl = document.getElementById('orphaned-dirs-count');
    const sizeEl = document.getElementById('orphaned-dirs-size');
    const filesEl = document.getElementById('orphaned-dirs-files');
    const btnCleanupAll = document.getElementById('btn-cleanup-all-orphaned');

    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-muted">
            <div class="spinner-border spinner-border-sm text-warning me-2" role="status"></div>
            Сканирование хранилища data/users/...
          </td>
        </tr>`;
    }

    try {
      const data = await apiFetch('/api/admin/users/orphaned-dirs');
      const dirs = data.orphaned_dirs || [];

      if (countEl) countEl.textContent = data.total || 0;
      if (sizeEl) sizeEl.textContent = formatBytes(data.total_size_bytes || 0);
      if (filesEl) filesEl.textContent = data.total_files || 0;

      if (btnCleanupAll) {
        btnCleanupAll.disabled = (dirs.length === 0);
      }

      if (!tbody) return;

      if (dirs.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" class="text-center py-4 text-success">
              <i class="bi bi-check-circle-fill fs-4 d-block mb-1"></i>
              Мертвых директорий не обнаружено. Все папки соответствуют активным пользователям.
            </td>
          </tr>`;
        return;
      }

      tbody.innerHTML = dirs.map(d => {
        const badgeClass = d.is_test_dir ? 'bg-secondary' : 'bg-warning text-dark';
        return `
          <tr data-dir-name="${escapeHtml(d.name)}">
            <td class="font-monospace fw-bold text-light">
              <i class="bi bi-folder text-warning me-1"></i>${escapeHtml(d.name)}
            </td>
            <td>
              <span class="badge ${badgeClass} small">${escapeHtml(d.reason)}</span>
            </td>
            <td class="text-center">${d.files_count}</td>
            <td class="text-center">${formatBytes(d.size_bytes)}</td>
            <td class="small">${formatDate(d.modified_at)}</td>
            <td class="text-center">
              <button class="btn btn-outline-danger btn-sm py-0 px-2 btn-delete-single-orphaned" data-dir="${escapeHtml(d.name)}" title=i18n.t('auto___e36849')>
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>`;
      }).join('');

      // Add click listeners to single delete buttons
      tbody.querySelectorAll('.btn-delete-single-orphaned').forEach(btn => {
        btn.addEventListener('click', async () => {
          const dirName = btn.getAttribute('data-dir');
          if (!dirName) return;
          if (!confirm(`Удалить мертвую директорию "${dirName}"?`)) return;

          btn.disabled = true;
          try {
            const res = await apiFetch('/api/admin/users/orphaned-dirs/clean', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ dirs: [dirName] })
            });
            showStatusAlert(`Директория "${dirName}" успешно удалена.`, 'successi18n.t('auto__loadorphaneddirs_catch_err_showstatusalert_dirname_err_message__d5bd3a')danger');
            btn.disabled = false;
          }
        });
      });
    } catch (err) {
      console.error('[UsersTab] Error loading orphaned dirs:', err);
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" class="text-center py-4 text-danger">
              <i class="bi bi-exclamation-octagon fs-4 d-block mb-1"></i>
              Ошибка сканирования: ${escapeHtml(err.message)}
            </td>
          </tr>`;
      }
    }
  }

  // Global Init Function
  function initUsersTab() {
    console.log('[UsersTab] Initializing user management tab with inline editing...');
    if (!state.initialized) {
      initListeners();
      state.initialized = true;
    }
    loadUsers();
  }

  // Register globally
  window.initUsersTab = initUsersTab;
})();
