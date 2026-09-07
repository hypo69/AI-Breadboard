// Popup Script for AI-Breadboard Chrome Extension

document.addEventListener('DOMContentLoaded', async () => {
  // Apply i18n
  applyI18n();

  // Load settings and check connection
  const settings = await getSettings();
  const serverUrl = (settings.serverUrl || 'http://localhost:8000').replace(/\/+$/, '');
  
  checkServerStatus(serverUrl);

  // Wire event handlers
  document.getElementById('btn-analyze')?.addEventListener('click', async () => {
    chrome.runtime.sendMessage({ action: 'analyze_current_tab' });
    window.close();
  });

  document.getElementById('btn-save')?.addEventListener('click', async () => {
    chrome.runtime.sendMessage({ action: 'save_current_tab' });
    window.close();
  });

  document.getElementById('btn-open-chat')?.addEventListener('click', async () => {
    chrome.tabs.create({ url: `${serverUrl}/` });
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
}

function setElemText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

async function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get({ serverUrl: 'http://localhost:8000' }, (items) => resolve(items));
  });
}

async function checkServerStatus(serverUrl) {
  const statusEl = document.getElementById('server-status');
  const textEl = document.getElementById('status-text');
  if (!statusEl || !textEl) return;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);

    const res = await fetch(`${serverUrl}/api/control/health`, {
      method: 'GET',
      signal: controller.signal
    }).catch(async () => {
      // Fallback check on root or docs
      return await fetch(`${serverUrl}/docs`, { method: 'HEAD', signal: controller.signal });
    });

    clearTimeout(timeoutId);

    if (res && (res.ok || res.status < 500)) {
      statusEl.className = 'status-badge connected';
      textEl.textContent = chrome.i18n.getMessage('popupConnected') || 'Подключен';
    } else {
      throw new Error('Not reachable');
    }
  } catch (err) {
    statusEl.className = 'status-badge disconnected';
    textEl.textContent = chrome.i18n.getMessage('popupDisconnected') || 'Отключен';
  }
}
