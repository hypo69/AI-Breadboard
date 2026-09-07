// Options Page Script for AI-Breadboard Chrome Extension

document.addEventListener('DOMContentLoaded', async () => {
  applyI18n();
  await loadOptions();

  document.getElementById('options-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveOptions();
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

async function loadOptions() {
  chrome.storage.sync.get(
    {
      serverUrl: 'http://localhost:8000',
      language: 'default',
      customPrompt: '',
      subfolder: 'web_pages',
      autoSendChat: true
    },
    (items) => {
      document.getElementById('server-url').value = items.serverUrl;
      document.getElementById('prompt-lang').value = items.language;
      document.getElementById('custom-prompt').value = items.customPrompt;
      document.getElementById('subfolder').value = items.subfolder;
      document.getElementById('auto-send-chat').checked = items.autoSendChat !== false;
    }
  );
}

async function saveOptions() {
  const serverUrl = document.getElementById('server-url').value.trim() || 'http://localhost:8000';
  const language = document.getElementById('prompt-lang').value;
  const customPrompt = document.getElementById('custom-prompt').value.trim();
  const subfolder = document.getElementById('subfolder').value.trim() || 'web_pages';
  const autoSendChat = document.getElementById('auto-send-chat').checked;

  chrome.storage.sync.set(
    {
      serverUrl,
      language,
      customPrompt,
      subfolder,
      autoSendChat
    },
    () => {
      const status = document.getElementById('status-message');
      if (status) {
        status.textContent = chrome.i18n.getMessage('optionsSaved') || 'Настройки успешно сохранены!';
        status.className = 'status-message success';
        setTimeout(() => {
          status.className = 'status-message d-none';
        }, 3000);
      }
    }
  );
}
