// User Interface Main JS
import { initI18n, switchLang, applyTranslations } from '../js/i18n.js';

window.switchLang = switchLang;
window.applyTranslations = applyTranslations;

// API module
window.api = {
  async fetch(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
      let msg = response.statusText;
      try {
        const data = await response.json();
        msg = data.detail || msg;
      } catch {}
      throw new Error(`${response.status} ${msg}`);
    }
    return response.json();
  },
  
  // Torrent download
  torrent: {
    async add(source, downloadDir) {
      return this.fetch('/api/torrents/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, download_dir: downloadDir })
      });
    },
    
    async getStatus(hash) {
      return this.fetch(`/api/torrents/status/${hash}`);
    }
  },
  
  // Auth module
  auth: {
    async check() {
      try {
        const response = await fetch('/auth/check');
        return await response.json();
      } catch {
        return { authenticated: false };
      }
    },
    
    loginWithGoogle() {
      // Direct redirect to Google OAuth - no fetch due to CORS
      window.location.href = '/auth/google?next=' + encodeURIComponent(window.location.pathname + window.location.search);
    },
    
    async register(email, password, name) {
      return this.fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name })
      });
    },

    async verify(email, code) {
      return this.fetch('/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code })
      });
    },

    async loginEmail(email, password) {
      return this.fetch('/auth/login/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
    },
    
    logout() {
      return fetch('/auth/logout', { method: 'POST' });
    }
  }
};

// ── TORRENT LINK DETECTION ─────────────────────────────────────────────────

// Регулярки для поиска торрент-ссылок
const TORRENT_PATTERNS = [
  /magnet:\?[^<>\s]+/gi,  // magnet ссылки
  /https?:\/\/[^\s<>]+\.torrent/gi,  // URL к .torrent файлу
];

function findTorrentLinks(text) {
  const links = [];
  for (const pattern of TORRENT_PATTERNS) {
    const matches = text.match(pattern);
    if (matches) {
      links.push(...matches);
    }
  }
  return [...new Set(links)]; // Уникальные
}

// Обработка торрент-ссылки
async function handleTorrentLink(link, downloadDir = 'D:/Downloads') {
  try {
    console.log('[Torrent] Adding:', link);
    
    // Показываем индикатор загрузки
    showNotification('Добавление торрента...', 'info');
    
    // Отправляем на сервер
    const result = await window.api.torrent.add(link, downloadDir);
    
    if (result.error) {
      showNotification('Ошибка: ' + result.error, 'danger');
      return null;
    }
    
    // Показываем результат
    const typeText = result.is_series ? 'сериал' : 'фильм';
    const categoryText = result.is_series ? '01 serials' : '02 films';
    
    showNotification(
      `Добавлено: ${result.name}\nПапка: ${categoryText}\nКатегория: ${result.category}`,
      'success'
    );
    
    // Слушаем статус загрузки и открываем плеер
    if (result.torrent_hash) {
      monitorTorrentAndPlay(result.torrent_hash, result.save_path);
    }
    
    return result;
  } catch (e) {
    console.error('[Torrent] Error:', e);
    showNotification('Ошибка добавления торрента: ' + e.message, 'danger');
    return null;
  }
}

// Мониторинг загрузки торрента и автовоспроизведение
async function monitorTorrentAndPlay(torrentHash, savePath) {
  const maxChecks = 60; // Максимум 60 проверок (около 5 минут)
  let checkCount = 0;
  
  const checkInterval = setInterval(async () => {
    checkCount++;
    
    try {
      const status = await window.api.torrent.getStatus(torrentHash);
      
      if (status.error) {
        clearInterval(checkInterval);
        return;
      }
      
      // Проверяем состояние загрузки
      const state = status.state;
      const progress = status.progress;
      
      console.log(`[Torrent] ${status.name}: ${state} (${progress}%)`);
      
      // Загрузка завершена
      if (state === 'uploading' || state === 'paused' || state === 'stalledUP' || progress >= 100) {
        clearInterval(checkInterval);
        
        if (progress >= 99.9 || state === 'uploading') {
          // Ищем первый видеофайл в папке загрузки
          const mediaFile = await findFirstMediaFile(savePath);
          
          if (mediaFile) {
            showNotification('Загрузка завершена! Открываю плеер...', 'success');
            
            // Переключаем на вкладку плеера
            const playerTab = document.querySelector('[data-bs-target="#tab-player"]');
            const chatTab = document.querySelector('[data-bs-target="#tab-chat"]');
            if (playerTab) {
              playerTab.click();
            }
            
            // Добавляем файл в плеер и запускаем
            await addMediaFileAndPlay(mediaFile);
          } else {
            showNotification('Загрузка завершена, но видеофайл не найден', 'warning');
          }
        }
      }
      
    } catch (e) {
      console.error('[Torrent] Monitor error:', e);
    }
    
    if (checkCount >= maxChecks) {
      clearInterval(checkInterval);
      showNotification('Превышено время ожидания загрузки', 'warning');
    }
  }, 5000); // Проверяем каждые 5 секунд
}

// Поиск первого видеофайла в папке
async function findFirstMediaFile(dirPath) {
  try {
    const files = await window.api.fetch('/api/media/files');
    if (!files || !files.length) return null;
    
    // Ищем файл в указанной директории
    for (const f of files) {
      if (f.path && f.path.toLowerCase().startsWith(dirPath.toLowerCase())) {
        return f;
      }
    }
    return null;
  } catch (e) {
    console.error('[Torrent] Find media error:', e);
    return null;
  }
}

// Добавить файл и начать воспроизведение
async function addMediaFileAndPlay(file) {
  // Добавляем в начало списка
  mediaFiles.unshift(file);
  renderFileList();
  playFile(0);
}

// Уведомления
function showNotification(message, type = 'info') {
  // Создаём уведомление
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
  notification.style.zIndex = '9999';
  notification.style.maxWidth = '400px';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  // Автоскрытие через 5 секунд
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

document.addEventListener('DOMContentLoaded', async () => {
  console.log('User interface initializing...');
  
  // Initialize i18n
  const savedLang = localStorage.getItem('app_language') || 'ru';
  await initI18n(savedLang);
  
  // Setup language selector
  const langSelector = document.getElementById('lang-selector');
  if (langSelector) {
    langSelector.value = savedLang;
    langSelector.addEventListener('change', (e) => {
      switchLang(e.target.value);
    });
  }
  
  // Initialize auth
  await initAuth();
  
  // Initialize player
  initPlayer();
  
  // Initialize chat
  initChat();
  
  // Apply translations
  applyTranslations();
  
  console.log('User interface ready');
});

// ── AUTH MODULE ─────────────────────────────────────────────────────────────

async function initAuth() {
  const loginTriggerBtn = document.getElementById('login-trigger-btn');
  const googleSignInBtn = document.getElementById('google-signin-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const userProfile = document.getElementById('user-profile');
  const userAvatar = document.getElementById('user-avatar');
  const userName = document.getElementById('user-name');

  // Modal forms
  const formLogin = document.getElementById('form-login');
  const formRegister = document.getElementById('form-register');
  const formVerify = document.getElementById('form-verify');
  
  // Modal wrappers
  const authLoginDiv = document.getElementById('auth-form-login');
  const authRegisterDiv = document.getElementById('auth-form-register');
  const authVerifyDiv = document.getElementById('auth-form-verify');
  const authAlert = document.getElementById('auth-alert');
  
  // Navigation links
  const goToRegister = document.getElementById('go-to-register');
  const goToLogin = document.getElementById('go-to-login');
  const verifyCancel = document.getElementById('verify-cancel');

  let currentVerifyEmail = '';

  function showError(msg) {
    if (authAlert) {
      authAlert.textContent = msg;
      authAlert.classList.remove('d-none');
    }
  }

  function hideError() {
    if (authAlert) {
      authAlert.classList.add('d-none');
    }
  }

  function switchForm(formName) {
    hideError();
    authLoginDiv?.classList.add('d-none');
    authRegisterDiv?.classList.add('d-none');
    authVerifyDiv?.classList.add('d-none');

    if (formName === 'login') {
      authLoginDiv?.classList.remove('d-none');
    } else if (formName === 'register') {
      authRegisterDiv?.classList.remove('d-none');
    } else if (formName === 'verify') {
      authVerifyDiv?.classList.remove('d-none');
    }
  }

  // Set up navigations
  goToRegister?.addEventListener('click', (e) => {
    e.preventDefault();
    switchForm('register');
  });

  goToLogin?.addEventListener('click', (e) => {
    e.preventDefault();
    switchForm('login');
  });

  verifyCancel?.addEventListener('click', (e) => {
    e.preventDefault();
    switchForm('login');
  });

  // Submit Login
  formLogin?.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
      await window.api.auth.loginEmail(email, password);
      window.location.reload();
    } catch (err) {
      console.error(err);
      if (err.message.includes('403') || err.message.includes('не подтверждена')) {
        currentVerifyEmail = email;
        switchForm('verify');
      } else {
        showError(err.message || 'Ошибка входа');
      }
    }
  });

  // Submit Register
  formRegister?.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
      await window.api.auth.register(email, password, name);
      currentVerifyEmail = email;
      switchForm('verify');
    } catch (err) {
      console.error(err);
      showError(err.message || 'Ошибка регистрации');
    }
  });

  // Submit Verify
  formVerify?.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();
    const code = document.getElementById('verify-code').value;

    try {
      await window.api.auth.verify(currentVerifyEmail, code);
      switchForm('login');
      showNotification('Почта подтверждена! Теперь вы можете войти.', 'success');
    } catch (err) {
      console.error(err);
      showError(err.message || 'Неверный код подтверждения');
    }
  });

  async function updateAuthUI(authData) {
    if (authData.authenticated) {
      userProfile?.classList.remove('d-none');
      loginTriggerBtn?.classList.add('d-none');
      document.querySelectorAll('.auth-only').forEach(el => el.classList.remove('d-none'));
      
      if (authData.name) {
        userName.textContent = authData.name;
      } else if (authData.email) {
        userName.textContent = authData.email.split('@')[0];
      }
      if (authData.picture) {
        userAvatar.src = authData.picture;
      }
      
      setupCabinet();
      setupSettings();
    } else {
      userProfile?.classList.add('d-none');
      loginTriggerBtn?.classList.remove('d-none');
      document.querySelectorAll('.auth-only').forEach(el => el.classList.add('d-none'));
    }
  }
  
  const authData = await window.api.auth.check();
  await updateAuthUI(authData);
  
  googleSignInBtn?.addEventListener('click', () => {
    window.api.auth.loginWithGoogle();
  });
  
  logoutBtn?.addEventListener('click', async () => {
    try {
      await window.api.auth.logout();
      window.location.reload();
    } catch (e) {
      console.error('Logout failed:', e);
    }
  });
}

// ── CABINET MODULE ───────────────────────────────────────────────────────────

async function setupCabinet() {
  const avatar = document.getElementById('cab-avatar');
  const nameEl = document.getElementById('cab-name');
  const emailEl = document.getElementById('cab-email');
  const roleEl = document.getElementById('cab-role');
  const dateEl = document.getElementById('cab-created-at');
  
  const linkedDiv = document.getElementById('tg-status-linked');
  const unlinkedDiv = document.getElementById('tg-status-unlinked');
  const tgUserEl = document.getElementById('cab-tg-username');
  
  const genBtn = document.getElementById('btn-gen-link-token');
  const codeArea = document.getElementById('tg-link-code-area');
  const codeEl = document.getElementById('tg-link-code');

  try {
    const data = await window.api.fetch('/auth/cabinet');
    if (avatar && data.picture) avatar.src = data.picture;
    if (nameEl) nameEl.textContent = data.name || 'Без имени';
    if (emailEl) emailEl.textContent = data.email;
    if (roleEl) {
      roleEl.textContent = data.role === 'admin' ? 'Администратор' : 'Пользователь';
      roleEl.className = data.role === 'admin' ? 'badge bg-danger' : 'badge bg-secondary';
    }
    if (dateEl && data.created_at) {
      const date = new Date(data.created_at);
      dateEl.textContent = date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU');
    }

    if (data.telegram_username) {
      linkedDiv?.classList.remove('d-none');
      unlinkedDiv?.classList.add('d-none');
      if (tgUserEl) tgUserEl.textContent = data.telegram_username.startsWith('@') ? data.telegram_username : `@${data.telegram_username}`;
    } else {
      linkedDiv?.classList.add('d-none');
      unlinkedDiv?.classList.remove('d-none');
    }
  } catch (e) {
    console.error('Failed to load cabinet data:', e);
  }

  genBtn?.addEventListener('click', async () => {
    try {
      const res = await window.api.fetch('/auth/link-token', { method: 'POST' });
      if (res.token) {
        if (codeEl) codeEl.textContent = res.token;
        codeArea?.classList.remove('d-none');
        showNotification('Код привязки успешно сгенерирован', 'success');
      }
    } catch (e) {
      showNotification('Не удалось получить код привязки: ' + e.message, 'danger');
    }
  });
}

// ── SETTINGS MODULE ──────────────────────────────────────────────────────────

async function setupSettings() {
  const form = document.getElementById('settings-form');
  const themeSelect = document.getElementById('settings-theme');
  const langSelect = document.getElementById('settings-lang');
  const ttsCheckbox = document.getElementById('settings-tts');
  const ttsSystemSelect = document.getElementById('settings-tts-system');
  const ttsVoiceSelect = document.getElementById('settings-tts-voice');
  const ttsVoiceContainer = document.getElementById('settings-tts-voice-container');
  const instructionText = document.getElementById('settings-instruction');

  const populateBrowserVoices = () => {
    const optBrowser = document.getElementById('optgroup-browser');
    if (optBrowser && 'speechSynthesis' in window) {
      optBrowser.innerHTML = '';
      const voices = window.speechSynthesis.getVoices();
      const ruVoices = voices.filter(v => v.lang.startsWith('ru'));
      if (ruVoices.length === 0) {
        const opt = document.createElement('option');
        opt.value = 'default';
        opt.textContent = 'По умолчанию (Браузерный)';
        optBrowser.appendChild(opt);
      } else {
        ruVoices.forEach(v => {
          const opt = document.createElement('option');
          opt.value = v.name;
          opt.textContent = v.name;
          optBrowser.appendChild(opt);
        });
      }
    }
  };

  const toggleVoiceVisibility = () => {
    if (ttsSystemSelect && ttsVoiceContainer && ttsVoiceSelect) {
      const val = ttsSystemSelect.value;
      if (val === 'gtts') {
        ttsVoiceContainer.style.display = 'none';
      } else {
        ttsVoiceContainer.style.display = 'block';
        const optEdge = document.getElementById('optgroup-edge');
        const optSilero = document.getElementById('optgroup-silero');
        const optBrowser = document.getElementById('optgroup-browser');
        if (optEdge && optSilero && optBrowser) {
          if (val === 'edge-tts') {
            optEdge.style.display = '';
            optSilero.style.display = 'none';
            optBrowser.style.display = 'none';
            if (ttsVoiceSelect.value !== 'ru-RU-DmitryNeural' && ttsVoiceSelect.value !== 'ru-RU-SvetlanaNeural') {
              ttsVoiceSelect.value = 'ru-RU-DmitryNeural';
            }
          } else if (val === 'silero') {
            optEdge.style.display = 'none';
            optSilero.style.display = '';
            optBrowser.style.display = 'none';
            const sileroVoices = ['eugene', 'aidar', 'baya', 'kseniya', 'xenia', 'random'];
            if (!sileroVoices.includes(ttsVoiceSelect.value)) {
              ttsVoiceSelect.value = 'eugene';
            }
          } else if (val === 'browser') {
            optEdge.style.display = 'none';
            optSilero.style.display = 'none';
            optBrowser.style.display = '';
            populateBrowserVoices();
          }
        }
      }
    }
  };

  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
      populateBrowserVoices();
      toggleVoiceVisibility();
    };
    populateBrowserVoices();
  }

  ttsSystemSelect?.addEventListener('change', toggleVoiceVisibility);

  try {
    const settings = await window.api.fetch('/auth/settings');
    if (themeSelect && settings.theme) themeSelect.value = settings.theme;
    if (langSelect && settings.language) langSelect.value = settings.language;
    if (ttsCheckbox) ttsCheckbox.checked = settings.tts_enabled === 1;
    if (ttsSystemSelect && settings.tts_system) {
      ttsSystemSelect.value = settings.tts_system;
    }
    
    // Make sure options are populated before setting value
    if (ttsSystemSelect && ttsSystemSelect.value === 'browser') {
      populateBrowserVoices();
    }
    
    if (ttsVoiceSelect && settings.tts_voice) {
      ttsVoiceSelect.value = settings.tts_voice;
    }
    if (instructionText && settings.system_instruction) instructionText.value = settings.system_instruction;
    
    toggleVoiceVisibility();

    // Apply theme immediately
    applyTheme(themeSelect?.value || 'dark');
  } catch (e) {
    console.error('Failed to load settings:', e);
  }

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const payload = {
        theme: themeSelect?.value || 'dark',
        language: langSelect?.value || 'ru',
        tts_enabled: ttsCheckbox?.checked ? 1 : 0,
        tts_system: ttsSystemSelect?.value || 'edge-tts',
        tts_voice: ttsVoiceSelect?.value || 'ru-RU-DmitryNeural',
        system_instruction: instructionText?.value || ''
      };
      await window.api.fetch('/auth/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      showNotification('Настройки сохранены', 'success');
      
      // Apply theme immediately
      applyTheme(payload.theme);
      
      // Switch i18n language
      if (window.switchLang) {
        window.switchLang(payload.language);
      }
    } catch (e) {
      showNotification('Ошибка сохранения настроек: ' + e.message, 'danger');
    }
  });
}

// Apply theme immediately to body
function applyTheme(theme) {
  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    theme = prefersDark ? 'dark' : 'light';
  }
  
  if (theme === 'light') {
    document.body.style.background = '#f6f8fa';
    document.body.style.color = '#24292f';
  } else {
    document.body.style.background = '#0d1117';
    document.body.style.color = '#c9d1d9';
  }
}

// ── PLAYER MODULE ───────────────────────────────────────────────────────────

let mediaFiles = [];
let currentIndex = -1;

function initPlayer() {
  const fileList = document.getElementById('file-list');
  const video = document.getElementById('video');
  const prevBtn = document.getElementById('btn-prev');
  const nextBtn = document.getElementById('btn-next');
  
  // Load media files
  loadMediaFiles();
  
  prevBtn?.addEventListener('click', () => playPrev());
  nextBtn?.addEventListener('click', () => playNext());
  
  // Handle video ended
  video?.addEventListener('ended', () => playNext());
  
  // Загрузка директории из localStorage
  const savedDir = localStorage.getItem('torrent_download_dir');
  if (savedDir) {
    document.getElementById('download-dir').value = savedDir;
  }
  
  // Сохранение директории и обновление списка файлов
  document.getElementById('download-dir')?.addEventListener('change', (e) => {
    localStorage.setItem('torrent_download_dir', e.target.value);
  });
  
  document.getElementById('btn-refresh-files')?.addEventListener('click', () => {
    loadMediaFiles();
    showNotification('Список файлов обновлён', 'success');
  });

  initPlayerChatPopup();
}

function initPlayerChatPopup() {
  console.log('initPlayerChatPopup: Инициализация...');
  const chatToggleBtn = document.getElementById('chat-toggle-btn');
  const chatPopup = document.getElementById('chat-popup');
  const chatCloseBtn = document.getElementById('chat-close-btn');
  const chatPopupSend = document.getElementById('chat-popup-send');
  const chatPopupInput = document.getElementById('chat-popup-input');
  const chatPopupMessages = document.getElementById('chat-popup-messages');

  console.log('initPlayerChatPopup: Найденные элементы:', {
    chatToggleBtn: !!chatToggleBtn,
    chatPopup: !!chatPopup,
    chatCloseBtn: !!chatCloseBtn,
    chatPopupSend: !!chatPopupSend,
    chatPopupInput: !!chatPopupInput,
    chatPopupMessages: !!chatPopupMessages
  });

  if (chatToggleBtn && chatPopup) {
    chatToggleBtn.addEventListener('click', (e) => {
      console.log('initPlayerChatPopup: Клик по кнопке чата');
      e.preventDefault();
      e.stopPropagation();
      chatPopup.classList.toggle('show');
      console.log('initPlayerChatPopup: Текущие классы окна чата:', chatPopup.className);
      if (chatPopup.classList.contains('show')) {
        chatPopupInput.focus();
      }
    });
  } else {
    console.error('initPlayerChatPopup: Кнопка или окно чата не найдены!');
  }

  if (chatCloseBtn && chatPopup) {
    chatCloseBtn.addEventListener('click', (e) => {
      console.log('initPlayerChatPopup: Клик по кнопке закрытия');
      e.preventDefault();
      e.stopPropagation();
      chatPopup.classList.remove('show');
    });
  }

  async function sendPopupMessage() {
    const msg = chatPopupInput.value.trim();
    if (!msg) return;

    console.log('initPlayerChatPopup: Отправка сообщения:', msg);
    addPopupMessage('user', msg);
    chatPopupInput.value = '';
    chatPopupSend.disabled = true;
    chatPopupSend.textContent = '⏳';

    try {
      const reply = await window.chatService.sendChatMessage(msg);
      addPopupMessage('bot', reply);
      window.chatService.speak(reply);
    } catch (e) {
      console.error('initPlayerChatPopup: Ошибка отправки:', e);
      addPopupMessage('bot', e);
    } finally {
      chatPopupSend.disabled = false;
      chatPopupSend.textContent = 'Отправить';
    }
  }

  function addPopupMessage(sender, text) {
    const el = document.createElement('div');
    el.className = `chat-popup-msg ${sender}`;
    
    let displayText;
    if (typeof text === 'object' && text !== null) {
      displayText = window.chatService.formatMessage(text);
    } else {
      displayText = text;
    }
    
    el.innerHTML = `<strong>${sender === 'user' ? 'Вы' : 'Ai Ассистент'}</strong>: ${displayText}`;
    chatPopupMessages.appendChild(el);
    chatPopupMessages.scrollTop = chatPopupMessages.scrollHeight;
  }

  if (chatPopupSend) {
    chatPopupSend.addEventListener('click', sendPopupMessage);
  }
  if (chatPopupInput) {
    chatPopupInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendPopupMessage();
    });
  }
}

async function loadMediaFiles() {
  try {
    const files = await window.api.fetch('/api/media/files');
    mediaFiles = files || [];
    renderFileList();
  } catch (e) {
    console.error('Failed to load media files:', e);
    document.getElementById('file-list').innerHTML = 
      '<div class="text-danger p-3" data-i18n="player.loadError">Ошибка загрузки файлов</div>';
  }
}

function renderFileList() {
  const list = document.getElementById('file-list');
  if (!mediaFiles.length) {
    list.innerHTML = '<div class="text-muted text-center p-3" data-i18n="player.noFiles">Нет файлов</div>';
    return;
  }
  
  list.innerHTML = mediaFiles.map((file, i) => `
    <div class="file-item ${i === currentIndex ? 'active' : ''}" data-index="${i}">
      <i class="bi bi-film"></i> ${escapeHtml(file.name || file.path)}
    </div>
  `).join('');
  
  // Add click handlers
  list.querySelectorAll('.file-item').forEach(item => {
    item.addEventListener('click', () => {
      const idx = parseInt(item.dataset.index);
      playFile(idx);
    });
  });
}

function playFile(index) {
  if (index < 0 || index >= mediaFiles.length) return;
  
  currentIndex = index;
  const file = mediaFiles[index];
  const video = document.getElementById('video');
  
  // Build streaming URL
  const filePath = encodeURIComponent(file.path || file);
  video.src = `/api/media/stream?path=${filePath}`;
  
  document.getElementById('current-file').textContent = file.name || file.path;
  renderFileList();
  
  video.play().catch(e => console.error('Play error:', e));
}

function playNext() {
  if (currentIndex < mediaFiles.length - 1) {
    playFile(currentIndex + 1);
  }
}

function playPrev() {
  if (currentIndex > 0) {
    playFile(currentIndex - 1);
  }
}

// ── CHAT MODULE ─────────────────────────────────────────────────────────────

function initChat() {
  const sendBtn = document.getElementById('send-button');
  const input = document.getElementById('message-input');
  
  sendBtn?.addEventListener('click', sendMessage);
  input?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  // Также слушаем входящие сообщения от бота
  setupBotMessageHandler();
}

// Слушатель для перехвата сообщений от бота
function setupBotMessageHandler() {
  const originalAddMessage = addMessage;
  addMessage = function(text, sender, isError = false) {
    originalAddMessage(text, sender, isError);
    
    // Проверяем сообщения от бота на торрент-ссылки и теги <film>
    if (sender === 'assistant' && !isError) {
      checkAndProcessTorrentLinks(text);
      checkAndProcessFilmTags(text);
    }
  };
}

// Проверка и обработка торрент-ссылок
async function checkAndProcessTorrentLinks(text) {
  const links = findTorrentLinks(text);
  
  if (links.length > 0) {
    // Показываем кнопки для каждой найденной ссылки
    for (const link of links) {
      const shouldDownload = confirm(`Найдена торрент-ссылка:\n${link}\n\nДобавить на загрузку?`);
      
      if (shouldDownload) {
        // Загружаем в директорию по умолчанию
        const downloadDir = localStorage.getItem('torrent_download_dir') || 'D:/Downloads';
        await handleTorrentLink(link, downloadDir);
      }
    }
  }
}

// Проверка и обработка тегов <film>
async function checkAndProcessFilmTags(text) {
  const filmMatches = [...text.matchAll(/<film>(.*?)<\/film>/gi)];
  
  for (const match of filmMatches) {
    const filmTitle = match[1];
    if (confirm(`Запустить фильм/сериал в плеере: ${filmTitle}?`)) {
      await launchFilm(filmTitle);
    }
  }
}

// Запуск фильма по названию
async function launchFilm(title) {
  try {
    showNotification(`Поиск файла: ${title}...`, 'info');
    const result = await window.api.fetch('/api/media/by-title', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    });
    
    if (result.path) {
      showNotification(`Запуск: ${title}`, 'success');
      // Переключаем на плеер
      document.querySelector('[data-bs-target="#tab-player"]')?.click();
      // Ищем файл в списке и играем
      const fileIndex = mediaFiles.findIndex(f => f.path === result.path);
      if (fileIndex !== -1) {
        playFile(fileIndex);
      } else {
        // Если файла нет в текущем списке, пробуем просто загрузить этот путь как новый файл
        await addMediaFileAndPlay({ path: result.path, name: title });
      }
    } else {
      showNotification(`Файл не найден: ${title}`, 'danger');
    }
  } catch (e) {
    console.error('[Player] Launch error:', e);
    showNotification('Ошибка запуска: ' + e.message, 'danger');
  }
}

async function sendMessage() {
  const input = document.getElementById('message-input');
  const chatWindow = document.getElementById('chat-window');
  const message = input.value.trim();
  
  if (!message) return;
  
  // Clear input
  input.value = '';
  
  // Hide empty message
  document.getElementById('chat-empty')?.remove();
  
  // Add user message
  addMessage(message, 'user');
  
  // Show typing indicator
  const typingId = addTypingIndicator();
  
  try {
    const reply = await window.chatService.sendChatMessage(message);
    removeTypingIndicator(typingId);
    addMessage(reply, 'assistant');
    window.chatService.speak(reply);
  } catch (e) {
    removeTypingIndicator(typingId);
    addMessage(e, 'assistant', true);
  }
}

window.openYouTubeForFilm = (title) => {
  const q = encodeURIComponent(`${title} фильм трейлер`);
  window.open(`https://www.youtube.com/results?search_query=${q}`, '_blank');
};

window.openOnlineCinemaForFilm = (title) => {
  const q = encodeURIComponent(`${title} смотреть онлайн`);
  window.open(`https://yandex.ru/video/search?text=${q}`, '_blank');
};

window.openKinopoiskForFilm = (title) => {
  const q = encodeURIComponent(title);
  window.open(`https://www.kinopoisk.ru/index.php?kp_query=${q}`, '_blank');
};

function replaceFilmTagsWithLinks(text) {
  if (!text) return '';
  return text.replace(/<film>(.*?)<\/film>/gi, (match, title) => {
    const cleanTitle = title.replace(/'/g, "\\'");
    return `<span class="film-interactive-chip" title="Film: ${title}">` +
      `<span class="film-chip-title" onclick="launchFilm('${cleanTitle}')">` +
        `<i class="bi bi-film me-1"></i>${title}` +
      `</span>` +
      `<button type="button" class="film-chip-btn film-chip-play" onclick="launchFilm('${cleanTitle}')" title="Play in media player">` +
        `<i class="bi bi-play-fill"></i>` +
      `</button>` +
      `<button type="button" class="film-chip-btn film-chip-youtube" onclick="window.openYouTubeForFilm('${cleanTitle}')" title="Watch trailer/video on YouTube">` +
        `<i class="bi bi-youtube"></i>` +
      `</button>` +
      `<button type="button" class="film-chip-btn film-chip-online" onclick="window.openOnlineCinemaForFilm('${cleanTitle}')" title="Watch online (Yandex Video / Cinemas)">` +
        `<i class="bi bi-globe"></i>` +
      `</button>` +
    `</span>`;
  });
}

function parseContentToHtml(text) {
  if (!text) return '';
  let html = text;
  if (window.marked && typeof window.marked.parse === 'function') {
    html = window.marked.parse(text);
  } else {
    // Basic fallback for formatting if marked is not loaded
    html = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }
  return replaceFilmTagsWithLinks(html);
}

function addMessage(text, sender, isError = false) {
  const chatWindow = document.getElementById('chat-window');
  const div = document.createElement('div');
  div.className = `chat-message ${sender}`;
  if (isError) div.style.color = '#f85149';
  
  if (typeof text === 'object' && text !== null) {
    div.innerHTML = window.chatService.formatMessage(text);
  } else {
    div.innerHTML = parseContentToHtml(text);
  }
  
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addTypingIndicator() {
  const chatWindow = document.getElementById('chat-window');
  const id = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.id = id;
  div.className = 'chat-message assistant';
  div.innerHTML = '<i class="bi bi-three-dots"></i> Печатает...';
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  document.getElementById(id)?.remove();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
// ── SET CATEGORY FROM DB ───────────────────────────────────────────────────

// Функция для вызова назначения категорий из интерфейса
async function assignCategoriesFromDB() {
  try {
    showNotification('Назначение категорий...', 'info');
    const result = await window.api.fetch('/api/torrents/assign-categories', { method: 'POST' });
    showNotification(result.result || 'Категории назначены', 'success');
  } catch (e) {
    showNotification('Ошибка: ' + e.message, 'danger');
  }
}