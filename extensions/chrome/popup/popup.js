// Popup Script for AI-Breadboard Chrome Extension

let _configCache = null;

async function getAppConfig() {
  if (_configCache) return _configCache;
  try {
    const res = await fetch(chrome.runtime.getURL('config.json'));
    if (res.ok) {
      _configCache = await res.json();
      return _configCache;
    }
  } catch (err) {
    console.error('Failed to load extension config.json in popup:', err);
  }
  _configCache = { serverUrl: '', chatWindow: { width: 520, height: 780 } };
  return _configCache;
}

async function getSettings() {
  const config = await getAppConfig();
  return new Promise((resolve) => {
    chrome.storage.sync.get({ serverUrl: config.serverUrl || '' }, (items) => resolve(items));
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  // Apply i18n
  applyI18n();

  // Load settings and check connection & auth
  const config = await getAppConfig();
  const settings = await getSettings();
  const serverUrl = (settings.serverUrl || config.serverUrl || '').replace(/\/+$/, '');
  
  if (serverUrl) {
    await checkServerStatus(serverUrl);
    await checkUserAuth(serverUrl);
  } else {
    setServerDisconnected();
  }

  // Wire event handlers
  document.getElementById('btn-google-login')?.addEventListener('click', async () => {
    if (!serverUrl) return;
    chrome.windows.create({
      url: `${serverUrl}/auth/google?next=/auth/extension-callback`,
      type: 'popup',
      width: 480,
      height: 640
    });
    window.close();
  });

  document.getElementById('btn-logout')?.addEventListener('click', async () => {
    if (!serverUrl) return;
    await performLogout(serverUrl);
  });

  document.getElementById('btn-analyze')?.addEventListener('click', async () => {
    chrome.runtime.sendMessage({ action: 'analyze_current_tab' });
    window.close();
  });

  document.getElementById('btn-save')?.addEventListener('click', async () => {
    chrome.runtime.sendMessage({ action: 'save_current_tab' });
    window.close();
  });

  document.getElementById('btn-open-chat')?.addEventListener('click', async () => {
    if (!serverUrl) return;
    const winWidth = (config.chatWindow && config.chatWindow.width) || 520;
    const winHeight = (config.chatWindow && config.chatWindow.height) || 780;
    chrome.windows.create({
      url: `${serverUrl}/`,
      type: 'popup',
      width: winWidth,
      height: winHeight,
      focused: true
    });
    window.close();
  });

  document.getElementById('btn-options')?.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
});

function applyI18n() {
  const getMsg = (key, def) => chrome.i18n.getMessage(key) || def;

  setElemText('txt-title', getMsg('popupTitle', 'AI-Breadboard'));
  setElemText('txt-analyze', getMsg('popupAnalyzeCurrent', 'Проанализировать в чате'));
  setElemText('txt-save', getMsg('popupSaveCurrent', 'Сохранить страницу'));
  setElemText('txt-open-chat', getMsg('popupOpenChat', 'Открыть AI Чат'));
  setElemText('txt-options', getMsg('popupOptions', 'Настройки'));
  setElemText('txt-google-login', getMsg('popupGoogleLogin', 'Войти через Google'));
}

function setElemText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setServerDisconnected() {
  const statusEl = document.getElementById('server-status');
  const textEl = document.getElementById('status-text');
  if (statusEl) statusEl.className = 'status-badge disconnected';
  if (textEl) textEl.textContent = chrome.i18n.getMessage('popupDisconnected') || 'Отключен';
}

async function checkServerStatus(serverUrl) {
  const statusEl = document.getElementById('server-status');
  const textEl = document.getElementById('status-text');
  if (!statusEl || !textEl) return;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    const res = await fetch(`${serverUrl}/api/control/health`, {
      method: 'GET',
      credentials: 'include',
      signal: controller.signal
    }).catch(async () => {
      return await fetch(`${serverUrl}/`, { method: 'HEAD', credentials: 'include', signal: controller.signal });
    });

    clearTimeout(timeoutId);

    if (res && (res.ok || res.status < 500)) {
      statusEl.className = 'status-badge connected';
      textEl.textContent = chrome.i18n.getMessage('popupConnected') || 'Подключен';
    } else {
      throw new Error('Not reachable');
    }
  } catch (err) {
    setServerDisconnected();
  }
}

async function checkUserAuth(serverUrl) {
  const profileCard = document.getElementById('user-profile-card');
  const guestCard = document.getElementById('guest-login-card');
  const userNameEl = document.getElementById('user-name');
  const userEmailEl = document.getElementById('user-email');
  const userAvatarEl = document.getElementById('user-avatar');

  try {
    const res = await fetch(`${serverUrl}/auth/check`, {
      method: 'GET',
      credentials: 'include'
    });

    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.email) {
        if (profileCard) profileCard.classList.remove('d-none');
        if (guestCard) guestCard.classList.add('d-none');

        if (userNameEl) userNameEl.textContent = data.name || data.email;
        if (userEmailEl) userEmailEl.textContent = data.email;
        if (userAvatarEl && data.picture) {
          userAvatarEl.src = data.picture;
        }

        chrome.storage.local.set({ user: data });
        return;
      }
    }
  } catch (err) {
    console.warn('Auth check error:', err);
  }

  if (profileCard) profileCard.classList.add('d-none');
  if (guestCard) guestCard.classList.remove('d-none');
  chrome.storage.local.remove(['user']);
}

async function performLogout(serverUrl) {
  try {
    await fetch(`${serverUrl}/auth/logout`, {
      method: 'POST',
      credentials: 'include'
    });
  } catch (err) {}
  
  chrome.storage.local.remove(['user']);
  await checkUserAuth(serverUrl);
}
