/**
 * userSettings.js — User Profile & Settings Management
 * Supports Google OAuth synchronization, profile status, language & theme controls.
 */

'use strict';

export async function initUserSettings() {
  await refreshUserProfile();

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
        window.location.reload();
      } catch (err) {
        console.error('Logout error:', err);
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

export async function refreshUserProfile() {
  try {
    const res = await fetch('/auth/check');
    if (!res.ok) return;
    const data = await res.json();

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
      if (googleBadge) {
        if (hasGoogle) {
          googleBadge.innerHTML = '<i class="bi bi-google text-danger me-1"></i>Google OAuth: <span class="text-success fw-bold">Синхронизирован</span>';
        } else {
          googleBadge.innerHTML = '<i class="bi bi-google text-muted me-1"></i>Google OAuth: <span class="text-warning">Не подключен</span> <button type="button" class="btn btn-sm btn-outline-danger ms-2 py-0 px-2 btn-google-login">Синхронизировать</button>';
        }
      }

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

      // Navbar: show full Google register/sign-in button, hide user profile pill
      if (navGoogleBtn) {
        navGoogleBtn.classList.remove('d-none');
        navGoogleBtn.classList.add('d-flex');
      }
      if (userSettingsBtn) {
        userSettingsBtn.classList.add('d-none');
        userSettingsBtn.classList.remove('d-flex');
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
