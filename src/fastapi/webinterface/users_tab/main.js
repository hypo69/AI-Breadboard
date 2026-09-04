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
      console.error('[UsersTab] Error loading users:', err);
      showStatusAlert(`Ошибка загрузки пользователей: ${err.message}`, 'danger');
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

      // User Initials or Avatar
      let avatarHtml = '';
      if (user.picture) {
        avatarHtml = `<img src="${escapeHtml(user.picture)}" class="rounded-circle me-2" style="width:36px;height:36px;object-fit:cover;" alt="avatar">`;
      } else {
        const initial = (user.name || user.email || 'U').charAt(0).toUpperCase();
        const bgClass = isAdmin ? 'bg-warning text-dark' : 'bg-primary text-white';
        avatarHtml = `<div class="rounded-circle ${bgClass} d-flex align-items-center justify-content-center me-2 fw-bold" style="width:36px;height:36px;font-size:14px;">${escapeHtml(initial)}</div>`;
      }

      // Interactive Role Switch
      const roleSwitchHtml = `
        <div class="form-check form-switch d-inline-flex align-items-center justify-content-center m-0 gap-1" title="${isRoot ? 'Нельзя изменить роль Root' : (isAdmin ? 'Права Администратора активны. Нажмите для переключения на Пользователя.' : 'Обычный пользователь. Нажмите для выдачи прав Администратора.')}">
          <input class="form-check-input role-toggle-switch" type="checkbox" role="switch"
            id="role-switch-${user.id}"
            data-user-id="${user.id}"
            ${isAdmin ? 'checked' : ''}
            ${isRoot ? 'disabled' : ''} style="cursor: ${isRoot ? 'not-allowed' : 'pointer'};">
          <label class="form-check-label small fw-bold ms-1 ${isAdmin ? 'text-warning' : 'text-info'}" for="role-switch-${user.id}" style="cursor: ${isRoot ? 'not-allowed' : 'pointer'};">
            ${isAdmin ? '<i class="bi bi-shield-lock-fill"></i> Admin' : '<i class="bi bi-person-fill"></i> User'}
          </label>
        </div>
      `;

      // Status badge & toggle button
      const statusBadge = isActive
        ? `<span class="badge bg-success bg-opacity-75"><i class="bi bi-check-circle-fill"></i> Активен</span>`
        : `<span class="badge bg-danger bg-opacity-75"><i class="bi bi-slash-circle-fill"></i> Заблокирован</span>`;

      // Telegram column
      let tgHtml = '<span class="text-muted small">—</span>';
      if (user.telegram_username) {
        tgHtml = `<a href="https://t.me/${escapeHtml(user.telegram_username)}" target="_blank" class="text-info text-decoration-none small d-flex align-items-center gap-1">
          <i class="bi bi-telegram"></i> @${escapeHtml(user.telegram_username)}
        </a>`;
      } else if (user.telegram_id) {
        tgHtml = `<span class="text-muted small"><i class="bi bi-telegram text-info"></i> ID: ${escapeHtml(user.telegram_id)}</span>`;
      }

      // Password column
      const pwdHtml = hasPassword
        ? `<span class="badge bg-dark border border-success text-success" title="Пароль установлен"><i class="bi bi-key-fill"></i> Задан</span>`
        : `<span class="badge bg-dark border border-warning text-warning" title="Пароль не установлен (OAuth/TG)"><i class="bi bi-dash-circle"></i> Нет</span>`;

      // Email verified badge
      const emailVerifiedBadge = isEmailVerified
        ? `<i class="bi bi-patch-check-fill text-success ms-1" title="Email подтвержден"></i>`
        : `<i class="bi bi-question-circle text-muted ms-1" title="Email не подтвержден"></i>`;

      return `
        <tr data-user-id="${user.id}">
          <td class="text-center text-muted fw-bold">${user.id}</td>
          <td>
            <div class="d-flex align-items-center">
              ${avatarHtml}
              <div>
                <div class="fw-bold text-white">${escapeHtml(user.name || 'Без имени')}</div>
                <div class="small text-muted d-flex align-items-center">
                  ${escapeHtml(user.email)} ${emailVerifiedBadge}
                </div>
              </div>
            </div>
          </td>
          <td class="text-center">${roleSwitchHtml}</td>
          <td class="text-center">
            <div>${statusBadge}</div>
          </td>
          <td>${tgHtml}</td>
          <td class="text-center">${pwdHtml}</td>
          <td class="small">
            <div><span class="text-muted">Создан:</span> ${formatDate(user.created_at)}</div>
            ${user.last_login ? `<div><span class="text-muted">Вход:</span> ${formatDate(user.last_login)}</div>` : ''}
          </td>
          <td class="text-center">
            <div class="btn-group btn-group-sm" role="group">
              <button class="btn btn-outline-secondary btn-edit-user" data-id="${user.id}" title="Редактировать">
                <i class="bi bi-pencil-fill"></i>
              </button>
              <button class="btn btn-outline-info btn-pwd-user" data-id="${user.id}" data-name="${escapeHtml(user.name || user.email)}" title="Сменить пароль">
                <i class="bi bi-key-fill"></i>
              </button>
              <button class="btn btn-outline-light btn-details-user" data-id="${user.id}" title="Настройки и профиль">
                <i class="bi bi-info-circle-fill"></i>
              </button>
              <button class="btn ${isActive ? 'btn-outline-warning' : 'btn-outline-success'} btn-toggle-active-user" data-id="${user.id}" data-active="${isActive ? '1' : '0'}" ${isRoot ? 'disabled title="Нельзя деактивировать Root"' : `title="${isActive ? 'Заблокировать' : 'Активировать'}"`}>
                <i class="bi ${isActive ? 'bi-lock-fill' : 'bi-unlock-fill'}"></i>
              </button>
              <button class="btn btn-outline-danger btn-delete-user" data-id="${user.id}" data-name="${escapeHtml(user.name || user.email)}" ${isRoot ? 'disabled title="Нельзя удалить Root"' : 'title="Удалить"'}>
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
    // Role Toggle Switch
    document.querySelectorAll('.role-toggle-switch').forEach(sw => {
      sw.addEventListener('change', async (e) => {
        const userId = parseInt(e.target.getAttribute('data-user-id'), 10);
        await handleToggleRole(userId, e.target);
      });
    });

    // Edit User
    document.querySelectorAll('.btn-edit-user').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        openEditModal(userId);
      });
    });

    // Change Password
    document.querySelectorAll('.btn-pwd-user').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        const userName = e.currentTarget.getAttribute('data-name');
        openPasswordModal(userId, userName);
      });
    });

    // View Details
    document.querySelectorAll('.btn-details-user').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        openDetailsModal(userId);
      });
    });

    // Toggle Active
    document.querySelectorAll('.btn-toggle-active-user').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        await handleToggleActive(userId);
      });
    });

    // Delete User
    document.querySelectorAll('.btn-delete-user').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const userId = parseInt(e.currentTarget.getAttribute('data-id'), 10);
        const userName = e.currentTarget.getAttribute('data-name');
        openDeleteModal(userId, userName);
      });
    });
  }

  // Toggle Role Handler
  async function handleToggleRole(userId, switchEl) {
    const originalChecked = !switchEl.checked;
    try {
      const res = await apiFetch(`/api/admin/users/${userId}/toggle-role`, { method: 'POST' });
      const user = state.users.find(u => u.id === userId);
      if (user) {
        user.role = res.role;
        user.is_admin = res.is_admin;
      }
      const roleText = res.is_admin ? 'Администратор (admin)' : 'Пользователь (user)';
      showStatusAlert(`Роль пользователя #${userId} изменена на: <strong>${roleText}</strong>`, 'success');
      loadUsers();
    } catch (err) {
      if (switchEl) switchEl.checked = originalChecked;
      showStatusAlert(`Ошибка изменения роли: ${err.message}`, 'danger');
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
        editRoleLabel.textContent = isEditAdmin ? 'Администратор (admin)' : 'Пользователь (user)';
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
        <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
        Загрузка профиля пользователя...
      </div>`;

    try {
      const data = await apiFetch(`/api/admin/users/${userId}`);
      const u = data.user || {};
      const s = data.settings || {};
      const perms = data.permissions || [];

      contentEl.innerHTML = `
        <div class="row g-3">
          <div class="col-md-6">
            <h6 class="text-primary border-bottom border-secondary pb-1 mb-2">👤 Основные данные</h6>
            <table class="table table-dark table-sm table-borderless small mb-0">
              <tr><td class="text-muted" style="width:120px;">ID:</td><td class="fw-bold">${u.id}</td></tr>
              <tr><td class="text-muted">Email:</td><td>${escapeHtml(u.email)} ${u.is_email_verified ? '<span class="badge bg-success">Verified</span>' : '<span class="badge bg-secondary">Unverified</span>'}</td></tr>
              <tr><td class="text-muted">Имя:</td><td>${escapeHtml(u.name || '—')}</td></tr>
              <tr><td class="text-muted">Роль:</td><td><span class="badge bg-info text-dark">${escapeHtml(u.role || 'user')}</span> ${u.is_admin ? '<span class="badge bg-warning text-dark">Admin</span>' : ''}</td></tr>
              <tr><td class="text-muted">Статус:</td><td>${u.is_active ? '<span class="text-success">Активен</span>' : '<span class="text-danger">Заблокирован</span>'}</td></tr>
              <tr><td class="text-muted">Пароль:</td><td>${u.has_password ? '<span class="text-success">Установлен</span>' : '<span class="text-muted">Не задан</span>'}</td></tr>
              <tr><td class="text-muted">Создан:</td><td>${escapeHtml(u.created_at || '—')}</td></tr>
              <tr><td class="text-muted">Последний вход:</td><td>${escapeHtml(u.last_login || '—')}</td></tr>
            </table>
          </div>
          <div class="col-md-6">
            <h6 class="text-info border-bottom border-secondary pb-1 mb-2">✈️ Telegram & Настройки</h6>
            <table class="table table-dark table-sm table-borderless small mb-0">
              <tr><td class="text-muted" style="width:130px;">Telegram ID:</td><td>${u.telegram_id ? escapeHtml(u.telegram_id) : '<span class="text-muted">Не привязан</span>'}</td></tr>
              <tr><td class="text-muted">TG Username:</td><td>${u.telegram_username ? `@${escapeHtml(u.telegram_username)}` : '<span class="text-muted">—</span>'}</td></tr>
              <tr><td class="text-muted">Тема UI:</td><td>${escapeHtml(s.theme || 'dark')}</td></tr>
              <tr><td class="text-muted">Язык:</td><td>${escapeHtml(s.language || 'ru')}</td></tr>
              <tr><td class="text-muted">TTS голос:</td><td>${escapeHtml(s.tts_voice || 'ru-RU-DmitryNeural')} (${escapeHtml(s.tts_system || 'edge-tts')})</td></tr>
              <tr><td class="text-muted">Модель чата:</td><td>${escapeHtml(s.model || 'По умолчанию')}</td></tr>
            </table>
          </div>
          <div class="col-12 mt-3">
            <h6 class="text-warning border-bottom border-secondary pb-1 mb-2">🛡️ Разрешения системы</h6>
            <div class="d-flex flex-wrap gap-1">
              ${perms.length > 0 ? perms.map(p => `<span class="badge bg-secondary">${escapeHtml(p)}</span>`).join('') : '<span class="text-muted small">Нет явных разрешений</span>'}
            </div>
          </div>
          ${s.system_instruction ? `
          <div class="col-12 mt-2">
            <h6 class="text-light border-bottom border-secondary pb-1 mb-1">📝 Пользовательская системная инструкция</h6>
            <pre class="bg-black p-2 rounded border border-secondary text-info small" style="max-height:120px;overflow-y:auto;">${escapeHtml(s.system_instruction)}</pre>
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

  // Toggle Active Handler
  async function handleToggleActive(userId) {
    try {
      const res = await apiFetch(`/api/admin/users/${userId}/toggle-active`, { method: 'POST' });
      const user = state.users.find(u => u.id === userId);
      if (user) {
        user.is_active = res.is_active;
        renderTable();
      }
      showStatusAlert(`Статус пользователя #${userId} изменён на: ${res.is_active ? 'Активен' : 'Заблокирован'}`, 'success');
      loadUsers();
    } catch (err) {
      showStatusAlert(`Ошибка изменения статуса: ${err.message}`, 'danger');
    }
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
          createRoleLabel.textContent = 'Пользователь (user)';
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
        createRoleLabel.textContent = e.target.checked ? 'Администратор (admin)' : 'Пользователь (user)';
        createRoleLabel.className = e.target.checked ? 'text-warning' : 'text-info';
      });
    }

    const editAdminSw = document.getElementById('edit-user-is-admin');
    const editRoleLabel = document.getElementById('edit-role-label');
    if (editAdminSw && editRoleLabel) {
      editAdminSw.addEventListener('change', (e) => {
        editRoleLabel.textContent = e.target.checked ? 'Администратор (admin)' : 'Пользователь (user)';
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
          const modalEl = document.getElementById('modal-create-user');
          const modal = bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();

          showStatusAlert(`Пользователь ${escapeHtml(payload.name)} успешно создан!`, 'success');
          loadUsers();
        } catch (err) {
          showStatusAlert(`Ошибка создания пользователя: ${err.message}`, 'danger');
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Edit User Form Submit
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
          const modalEl = document.getElementById('modal-edit-user');
          const modal = bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();

          showStatusAlert(`Данные пользователя #${userId} успешно обновлены!`, 'success');
          loadUsers();
        } catch (err) {
          showStatusAlert(`Ошибка обновления: ${err.message}`, 'danger');
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
          const modalEl = document.getElementById('modal-password-user');
          const modal = bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();

          showStatusAlert(`Пароль для пользователя #${userId} успешно установлен!`, 'success');
          loadUsers();
        } catch (err) {
          showStatusAlert(`Ошибка установки пароля: ${err.message}`, 'danger');
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
          const modalEl = document.getElementById('modal-delete-user');
          const modal = bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();

          showStatusAlert(`Пользователь #${userId} успешно удалён.`, 'success');
          loadUsers();
        } catch (err) {
          showStatusAlert(`Ошибка удаления пользователя: ${err.message}`, 'danger');
        } finally {
          btnConfirmDelete.disabled = false;
        }
      });
    }
  }

  // Global Init Function
  function initUsersTab() {
    console.log('[UsersTab] Initializing user management tab...');
    if (!state.initialized) {
      initListeners();
      state.initialized = true;
    }
    loadUsers();
  }

  // Register globally
  window.initUsersTab = initUsersTab;
})();
