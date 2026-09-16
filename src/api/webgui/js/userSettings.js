/**
 * userSettings.js — User Profile & Settings Management
 * Supports Google OAuth synchronization, profile status, language & theme controls.
 */

'use strict';

export function executeUserAction(actionType) {
  // Ensure chat tab is active
  if (typeof window.switchToTab === 'function') {
    window.switchToTab('chat');
  } else if (typeof window.switchTab === 'function') {
    window.switchTab('tab-chat');
  } else {
    const chatTabBtn = document.querySelector('[data-bs-target="#tab-chat"], [data-tab="tab-chat"]');
    if (chatTabBtn && window.bootstrap?.Tab) {
      bootstrap.Tab.getOrCreateInstance(chatTabBtn).show();
    }
  }

  const msgInput = document.getElementById('message-input');
  const sendBtn = document.getElementById('send-button');

  const send = () => {
    if (typeof window.sendChatMessage === 'function') {
      window.sendChatMessage();
    } else if (sendBtn) {
      sendBtn.click();
    }
  };

  if (actionType === 'mail') {
    if (msgInput) {
      msgInput.value = 'Проверь мою почту Gmail и покажи последние непрочитанные письма.';
      setTimeout(send, 100);
    }
  } else if (actionType === 'docs') {
    const query = prompt('Введите поисковый запрос для поиска документов в Google Docs / Drive:');
    if (query && query.trim() && msgInput) {
      msgInput.value = `Найди в Google Docs / Google Drive документы по запросу: "${query.trim()}".`;
      setTimeout(send, 100);
    }
  } else if (actionType === 'sheets') {
    const query = prompt('Введите ID таблицы или команду для Google Sheets (например: "Прочитай данные из таблицы ID диапазон A1:D10" или "Добавь строку"):');
    if (query && query.trim() && msgInput) {
      msgInput.value = `Google Sheets: ${query.trim()}`;
      setTimeout(send, 100);
    }
  } else if (actionType === 'news') {
    if (msgInput) {
      msgInput.value = 'Подготовь для меня свежий дайджест самых релевантных новостей по моим интересам.';
      setTimeout(send, 100);
    }
  } else if (actionType === 'facebook') {
    const text = prompt('Введите текст публикации для Facebook (и при желании ссылку через пробел):');
    if (text && text.trim() && msgInput) {
      msgInput.value = `Опубликуй пост в Facebook с текстом: "${text.trim()}".`;
      setTimeout(send, 100);
    }
  }
}

export async function initUserSettings() {
  await refreshUserProfile();

  // Bind User Menu Action Buttons
  document.querySelectorAll('#user-menu-btn-mail, #nav-btn-check-mail, .action-btn-mail').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      executeUserAction('mail');
    });
  });

  document.querySelectorAll('#user-menu-btn-docs, #nav-btn-search-gdocs, .action-btn-docs').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      executeUserAction('docs');
    });
  });

  document.querySelectorAll('#user-menu-btn-sheets, #nav-btn-gsheets, .action-btn-sheets').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      executeUserAction('sheets');
    });
  });

  document.querySelectorAll('#user-menu-btn-news, #nav-btn-news-digest, .action-btn-news').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      executeUserAction('news');
    });
  });

  document.querySelectorAll('#user-menu-btn-facebook, #nav-btn-facebook-post, .action-btn-facebook').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      executeUserAction('facebook');
    });
  });

  // Handle Google Login Click
  document.querySelectorAll('.btn-google-login, #user-settings-google-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const nextUrl = window.location.pathname + window.location.search;
      window.location.href = `/auth/google?next=${encodeURIComponent(nextUrl)}`;
    });
  });

  // Handle Logout Click
  document.querySelectorAll('.btn-user-logout, #user-settings-logout-btn').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        await fetch('/auth/logout', { method: 'POST' });
      } catch (err) {
        console.error('Logout error:', err);
      } finally {
        window.location.href = '/';
      }
    });
  });

  // Re-sync modal fields on modal show
  const modalEl = document.getElementById('userSettingsModal');
  if (modalEl) {
    modalEl.addEventListener('show.bs.modal', async () => {
      await refreshUserProfile();
      const savedLang = localStorage.getItem('app_language') || 'ru';
      document.querySelectorAll('.lang-selector').forEach((s) => {
        s.value = savedLang;
      });
      const savedTheme = localStorage.getItem('theme') || 'system';
      document.querySelectorAll('.theme-selector').forEach((s) => {
        s.value = savedTheme;
      });
    });
  }
}

export function isUserAdmin() {
  if (!window.currentUser) return false;
  return Boolean(window.currentUser.is_admin || (window.currentUser.role && String(window.currentUser.role).toLowerCase() === 'admin'));
}

export async function refreshUserProfile() {
  try {
    const res = await fetch('/auth/check');
    if (!res.ok) return;
    const data = await res.json();
    window.currentUser = data;

    const authCard = document.getElementById('user-settings-auth-card');
    const guestCard = document.getElementById('user-settings-guest-card');
    const navGoogleBtn = document.getElementById('nav-google-btn');
    const userSettingsBtn = document.getElementById('user-settings-btn');
    const navAvatar = document.getElementById('nav-user-avatar');
    const navIcon = document.getElementById('nav-user-icon');
    const navLabel = document.getElementById('nav-user-label');

    if (data && data.authenticated) {
      // User is authenticated
      if (authCard) authCard.classList.remove('d-none');
      if (guestCard) guestCard.classList.add('d-none');

      // Navbar: show user profile pill, hide Google register button
      if (navGoogleBtn) navGoogleBtn.classList.add('d-none');
      if (userSettingsBtn) {
        userSettingsBtn.classList.remove('d-none');
        userSettingsBtn.classList.add('d-flex');
      }

      const name = data.name || data.email || 'Пользователь';
      const email = data.email || '';
      const picture = data.picture || '';
      const role = data.role || (data.is_admin ? 'Admin' : 'User');
      const hasGoogle = Boolean(data.has_google);

      // Update modal fields
      const avatarEl = document.getElementById('user-settings-avatar');
      const nameEl = document.getElementById('user-settings-name');
      const emailEl = document.getElementById('user-settings-email');
      const roleBadge = document.getElementById('user-settings-role-badge');
      const googleBadge = document.getElementById('user-settings-google-badge');

      if (avatarEl) {
        if (picture) {
          avatarEl.src = picture;
          avatarEl.classList.remove('d-none');
        } else {
          avatarEl.classList.add('d-none');
        }
      }
      if (nameEl) nameEl.textContent = name;
      if (emailEl) emailEl.textContent = email;
      if (roleBadge) {
        roleBadge.textContent = role;
        roleBadge.className = `badge ${role.toLowerCase() === 'admin' ? 'bg-danger' : 'bg-primary'}`;
      }
      const isOauthEnabled = data.oauth_enabled !== false;

      if (googleBadge) {
        if (hasGoogle) {
          googleBadge.innerHTML = '<i class="bi bi-google text-danger me-1"></i>Google OAuth: <span class="text-success fw-bold">Синхронизирован</span>';
        } else if (isOauthEnabled) {
          googleBadge.innerHTML = '<i class="bi bi-google text-muted me-1"></i>Google OAuth: <span class="text-warning">Не подключен</span> <button type="button" class="btn btn-sm btn-outline-danger ms-2 py-0 px-2 btn-google-login">Синхронизировать</button>';
        } else {
          googleBadge.innerHTML = '<i class="bi bi-google text-muted me-1"></i>Google OAuth: <span class="text-muted">Отключен</span>';
        }
      }

      // Update dropdown header elements if present
      const menuWrapper = document.getElementById('user-menu-dropdown-wrapper');
      const menuDisplayName = document.getElementById('user-menu-display-name');
      const menuDisplayEmail = document.getElementById('user-menu-display-email');
      if (menuWrapper) {
        menuWrapper.classList.remove('d-none');
        menuWrapper.classList.add('d-flex');
      }
      if (menuDisplayName) menuDisplayName.textContent = name;
      if (menuDisplayEmail) menuDisplayEmail.textContent = email;

      // Update navbar button
      if (navAvatar && picture) {
        navAvatar.src = picture;
        navAvatar.classList.remove('d-none');
        if (navIcon) navIcon.classList.add('d-none');
      }
      if (navLabel) {
        const shortName = name.split(' ')[0] || name;
        navLabel.textContent = shortName;
      }
    } else {
      // Guest / unauthenticated
      if (authCard) authCard.classList.add('d-none');
      if (guestCard) guestCard.classList.remove('d-none');

      const isOauthEnabled = data && data.oauth_enabled !== false;

      // Navbar: show full Google register/sign-in button only if OAuth is enabled, else show user settings gear/pill
      if (navGoogleBtn) {
        if (isOauthEnabled) {
          navGoogleBtn.classList.remove('d-none');
          navGoogleBtn.classList.add('d-flex');
        } else {
          navGoogleBtn.classList.add('d-none');
          navGoogleBtn.classList.remove('d-flex');
        }
      }
      const menuWrapper = document.getElementById('user-menu-dropdown-wrapper');
      if (menuWrapper) {
        if (isOauthEnabled) {
          menuWrapper.classList.add('d-none');
          menuWrapper.classList.remove('d-flex');
        } else {
          menuWrapper.classList.remove('d-none');
          menuWrapper.classList.add('d-flex');
        }
      }
      if (userSettingsBtn) {
        if (isOauthEnabled) {
          userSettingsBtn.classList.add('d-none');
          userSettingsBtn.classList.remove('d-flex');
        } else {
          userSettingsBtn.classList.remove('d-none');
          userSettingsBtn.classList.add('d-flex');
        }
      }

      // Guest card google login button adjustment
      const guestGoogleBtn = guestCard ? guestCard.querySelector('.btn-google-login') : null;
      if (guestGoogleBtn) {
        if (isOauthEnabled) {
          guestGoogleBtn.classList.remove('d-none');
        } else {
          guestGoogleBtn.classList.add('d-none');
        }
      }

      if (navAvatar) navAvatar.classList.add('d-none');
      if (navIcon) navIcon.classList.remove('d-none');
      if (navLabel) navLabel.textContent = 'User Settings';
    }
  } catch (err) {
    console.error('Failed to refresh user profile:', err);
  }
}

window.initUserSettings = initUserSettings;
window.refreshUserProfile = refreshUserProfile;
window.isUserAdmin = isUserAdmin;
window.executeUserAction = executeUserAction;
