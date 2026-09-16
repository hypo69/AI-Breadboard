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
    const isAuthenticated = localStorage.getItem('admin_authenticated');
    if (!isAuthenticated) {
      showPasswordModal();
    }
  }, 500);
}

function setupPasswordVerification() {
  // Проверка аутентификации при загрузке
  const isAuthenticated = localStorage.getItem('admin_authenticated');
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
      passwordError.textContent = 'Пароль не может быть пустым';
    }
    return;
  }

  try {
    const response = await fetch('/api/admin/verify-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: passwordInput.value })
    });

    if (response.ok) {
      // Пароль верен
      if (modal) {
        const m = bootstrap.Modal.getInstance(modal);
        if (m) m.hide();
      }
      localStorage.setItem('admin_authenticated', 'true');
      passwordInput.value = '';
      if (passwordError) passwordError.classList.add('d-none');
    } else {
      if (passwordError) {
        passwordError.classList.remove('d-none');
        passwordError.textContent = 'Неверный пароль';
      }
      passwordInput.value = '';
      passwordInput.focus();
    }
  } catch (error) {
    console.error('Password verification error:', error);
    if (passwordError) {
      passwordError.classList.remove('d-none');
      passwordError.textContent = 'Ошибка проверки пароля';
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
