// Options Page Script for AI-Breadboard Chrome Extension

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
    console.error('Failed to load extension config.json in options:', err);
  }
  _configCache = { serverUrl: '', subfolder: 'web_pages', autoSendChat: true, language: 'default' };
  return _configCache;
}

document.addEventListener('DOMContentLoaded', async () => {
  applyI18n();
  const config = await getAppConfig();
  await loadOptions(config);

  const settings = await getSettings(config);
  const serverUrl = (settings.serverUrl || config.serverUrl || '').replace(/\/+$/, '');
  
  if (serverUrl) {
    await checkUserAuth(serverUrl);
  }

  document.getElementById('opt-btn-google-login')?.addEventListener('click', () => {
    if (!serverUrl) return;
    chrome.windows.create({
      url: `${serverUrl}/auth/google?next=/auth/extension-callback`,
      type: 'popup',
      width: 480,
      height: 640
    });
  });

  document.getElementById('opt-btn-logout')?.addEventListener('click', async () => {
    if (!serverUrl) return;
    try {
      await fetch(`${serverUrl}/auth/logout`, { method: 'POST', credentials: 'include' });
    } catch (e) {}
    chrome.storage.local.remove(['user']);
    await checkUserAuth(serverUrl);
  });

  document.getElementById('options-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveOptions(config);
  });
});

function applyI18n() {
  const getMsg = (key, def) => chrome.i18n.getMessage(key) || def;

  setElemText('txt-options-title', getMsg('optionsTitle', 'Настройки расширения AI-Breadboard'));
  setElemText('lbl-server-url', getMsg('optionsServerUrl', 'URL сервера AI-Breadboard'));
  setElemText('lbl-language', getMsg('optionsLanguage', 'Язык запроса (Промпта)'));
  setElemText('lbl-custom-prompt', getMsg('optionsCustomPrompt', 'Пользовательский шаблон запроса (опционально)'));
  setElemText('txt-save', getMsg('optionsSave', 'Сохранить настройки'));
}

function setElemText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

async function getSettings(config) {
  return new Promise((resolve) => {
    chrome.storage.sync.get(
      {
        serverUrl: config.serverUrl || '',
        language: config.language || 'default',
        customPrompt: '',
        subfolder: config.subfolder || 'web_pages',
        autoSendChat: config.autoSendChat !== false
      },
      (items) => resolve(items)
    );
  });
}

async function checkUserAuth(serverUrl) {
  const userCard = document.getElementById('opt-user-card');
  const guestCard = document.getElementById('opt-guest-card');
  const userNameEl = document.getElementById('opt-user-name');
  const userEmailEl = document.getElementById('opt-user-email');
  const userAvatarEl = document.getElementById('opt-user-avatar');

  try {
    const res = await fetch(`${serverUrl}/auth/check`, {
      method: 'GET',
      credentials: 'include'
    });

    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.email) {
        if (userCard) userCard.classList.remove('d-none');
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
    console.warn('Options auth check error:', err);
  }

  if (userCard) userCard.classList.add('d-none');
  if (guestCard) guestCard.classList.remove('d-none');
}

async function loadOptions(config) {
  chrome.storage.sync.get(
    {
      serverUrl: config.serverUrl || '',
      language: config.language || 'default',
      customPrompt: '',
      subfolder: config.subfolder || 'web_pages',
      autoSendChat: config.autoSendChat !== false
    },
    (items) => {
      const inputServer = document.getElementById('server-url');
      if (inputServer) {
        inputServer.value = items.serverUrl || config.serverUrl || '';
        inputServer.placeholder = config.serverUrl || '';
      }
      document.getElementById('prompt-lang').value = items.language;
      document.getElementById('custom-prompt').value = items.customPrompt;
      document.getElementById('subfolder').value = items.subfolder;
      document.getElementById('auto-send-chat').checked = items.autoSendChat !== false;
    }
  );
}

async function saveOptions(config) {
  const serverUrl = document.getElementById('server-url').value.trim() || config.serverUrl || '';
  const language = document.getElementById('prompt-lang').value;
  const customPrompt = document.getElementById('custom-prompt').value.trim();
  const subfolder = document.getElementById('subfolder').value.trim() || config.subfolder || 'web_pages';
  const autoSendChat = document.getElementById('auto-send-chat').checked;

  chrome.storage.sync.set(
    {
      serverUrl,
      language,
      customPrompt,
      subfolder,
      autoSendChat
    },
    async () => {
      const status = document.getElementById('status-message');
      if (status) {
        status.textContent = chrome.i18n.getMessage('optionsSaved') || 'Настройки успешно сохранены!';
        status.className = 'status-message success';
        setTimeout(() => {
          status.className = 'status-message d-none';
        }, 3000);
      }
      if (serverUrl) {
        await checkUserAuth(serverUrl.replace(/\/+$/, ''));
      }
    }
  );
}
