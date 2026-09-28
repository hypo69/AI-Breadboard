/**
 * Auth Handler Module - Обработка аутентификации и пароля
 */

export function setupAuthHandlers() {
  setupPasswordModal();
  setupPasswordVerification();
}

function setupPasswordModal() {
  const modal = document.getElementById('passwordModal');
  const loginBtn = document.getElementById('login-btn');
  const closeBtn = document.getElementById('closePasswordModal');
  const adminPassword = document.getElementById('admin-password');

  if (loginBtn) {
    loginBtn.addEventListener('click', verifyPassword);
  }

  if (adminPassword) {
    adminPassword.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        verifyPassword();
      }
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      if (modal) {
        const m = bootstrap.Modal.getInstance(modal);
        if (m) m.hide();
      }
    });
  }

  // Show modal on load if not authenticated
  setTimeout(() => {
    const isAuthenticated = localStorage.getItem('admin_authenticatedi18n.t('auto__if_isauthenticated_showpasswordmodal_500_function_setuppasswordverification_const_isauthenticated_localstorage_getitem__b95cbb')admin_authenticated');
  const adminPassword = document.getElementById('admin-password');

  if (isAuthenticated && adminPassword) {
    adminPassword.value = '';
    localStorage.removeItem('admin_authenticated');
  }
}

async function verifyPassword() {
  const passwordInput = document.getElementById('admin-password');
  const passwordError = document.getElementById('password-error');
  const modal = document.getElementById('passwordModal');

  if (!passwordInput.value) {
    if (passwordError) {
      passwordError.classList.remove('d-none');
      passwordError.textContent = i18n.t('auto___d97ab1');
    }
    return;
  }

  try {
    const response = await fetch('/api/admin/verify-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_password_passwordinput_value_if_response_ok_if_modal_const_m_bootstrap_modal_getinstance_modal_if_m_m_hide_localstorage_setitem__23ecc6')admin_authenticated', 'true');
      passwordInput.value = '';
      if (passwordError) passwordError.classList.add('d-none');
    } else {
      if (passwordError) {
        passwordError.classList.remove('d-none');
        passwordError.textContent = i18n.t('auto___e97cb7');
      }
      passwordInput.value = '';
      passwordInput.focus();
    }
  } catch (error) {
    console.error('Password verification error:', error);
    if (passwordError) {
      passwordError.classList.remove('d-none');
      passwordError.textContent = i18n.t('auto___5ba23e');
    }
  }
}

function showPasswordModal() {
  const modal = document.getElementById('passwordModal');
  if (modal) {
    const m = new bootstrap.Modal(modal, { backdrop: 'static', keyboard: false });
    m.show();
    const passwordInput = document.getElementById('admin-password');
    if (passwordInput) {
      passwordInput.focus();
    }
  }
}

export { verifyPassword, showPasswordModal };
