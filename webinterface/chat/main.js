// ── CHAT.JS ───────────────────────────────────────────────────────────────────

let currentMediaPath = null;
let chatHistory = [];
let isDebugMode = false; // По умолчанию PROD режим
let systemInstruction = null; // Хранит системную инструкцию

function clearChatHistory() {
  chatHistory = [];
  try {
    localStorage.removeItem('chat_history');
  } catch (e) {}
  const chatWindow = document.getElementById('chat-window');
  if (!chatWindow) return;
  chatWindow.innerHTML = '';
  const welcome = document.createElement('div');
  welcome.className = 'message bot-message';
  welcome.innerHTML = '<strong>Ai Ассистент</strong> (System): История очищена. Можете начать новый разговор.';
  chatWindow.appendChild(welcome);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function initChatTab() {
  const chatWindow = document.getElementById('chat-window');
  if (chatWindow) {
    // Приветственное сообщение
    const welcome = document.createElement('div');
    welcome.className = 'message bot-message';
    welcome.innerHTML = '<strong>Ai Ассистент</strong> (System): Добро пожаловать в чат! Можете спрашивать о фильмах и сериалах — я покажу путь к файлу и смогу открыть его в плеере.';
    chatWindow.appendChild(welcome);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Загрузка сохраненной истории из localStorage
    try {
      const stored = localStorage.getItem('chat_history');
      if (stored) {
        const rawHistory = JSON.parse(stored) || [];
        const isCleanText = (t) => {
          if (!t) return false;
          const s = String(t).trim();
          if (s.startsWith('❌') || s.startsWith('Ошибка') || s.startsWith('Error') || s.includes('В локальной базе ничего не найдено') || s.includes('DEBUG MODE')) {
            return false;
          }
          return true;
        };

        const sanitized = [];
        for (let i = 0; i < rawHistory.length; i++) {
          const u = rawHistory[i];
          if (u.role === 'user' && isCleanText(u.parts && u.parts[0])) {
            if (i + 1 < rawHistory.length && rawHistory[i + 1].role === 'model' && isCleanText(rawHistory[i + 1].parts && rawHistory[i + 1].parts[0])) {
              sanitized.push(u);
              sanitized.push(rawHistory[i + 1]);
              i++;
            }
          }
        }
        chatHistory = sanitized;
        try {
          localStorage.setItem('chat_history', JSON.stringify(chatHistory));
        } catch (e) {}

        chatHistory.forEach((msg, idx) => {
          const role = msg.role === 'model' ? 'bot' : 'user';
          const text = msg.parts[0];
          const query = (role === 'bot' && idx > 0) ? chatHistory[idx - 1].parts[0] : '';
          addMessage(role, text, query);
        });
      }
    } catch (e) {
      console.error('Failed to load chat history:', e);
      chatHistory = [];
    }

    // Загрузка системной инструкции
    loadSystemInstruction();

    // Инициализация тулбара моделей, провайдеров и поиска
    initChatDebuggerToolbar();

    // Обновление бейджей модели и провайдера поиска
    if (typeof window.updateChatBadges === 'function') {
      window.updateChatBadges();
    }

    // Обработчик скачивания торрентов
    chatWindow.addEventListener('click', async (e) => {
      const btn = e.target.closest('.download-torrent-btn');
      if (!btn) return;
      
      const url = btn.getAttribute('data-url');
      const source = btn.getAttribute('data-source');
      const title = btn.getAttribute('data-title');
      
      btn.disabled = true;
      const originalHtml = btn.innerHTML;
      btn.textContent = '⏳ Добавление...';
      
      try {
        const response = await fetch('/api/torrents/download', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, source, title })
        });
        
        if (response.ok) {
          btn.textContent = '✅ Добавлено в qBittorrent';
          btn.classList.remove('btn-outline-success');
          btn.classList.add('btn-success');
        } else {
          const errData = await response.json();
          alert('Ошибка при добавлении торрента: ' + (errData.detail || response.statusText));
          btn.disabled = false;
          btn.innerHTML = originalHtml;
        }
      } catch (err) {
        alert('Ошибка соединения с сервером: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = originalHtml;
      }
    });
  }


  // Event listeners for chat
  const sendBtn = document.getElementById('send-button');
  const msgInput = document.getElementById('message-input');
  const debugModeSelector = document.getElementById('chat-mode-debug');

  if (sendBtn) sendBtn.addEventListener('click', sendMessage);
  if (msgInput) msgInput.addEventListener('keypress', e => { if (e.key==='Enter') sendMessage(); });
  if (debugModeSelector) debugModeSelector.addEventListener('change', (e) => {
    isDebugMode = e.target.value === 'debug';
  });

  const clearHistoryBtn = document.getElementById('clear-history-btn');
  if (clearHistoryBtn) clearHistoryBtn.addEventListener('click', clearChatHistory);

  const saveHistoryBtn = document.getElementById('save-history-rag-btn');
  if (saveHistoryBtn) saveHistoryBtn.addEventListener('click', saveFullHistoryToRag);

  const chatAlgoBtn = document.getElementById('chat-algo-btn');
  if (chatAlgoBtn) {
    chatAlgoBtn.addEventListener('click', () => {
      if (typeof window.showChatLogicModal === 'function') {
        window.showChatLogicModal();
      } else {
        window.open('/html/assets/chat_and_rag_logic.svg', '_blank');
      }
    });
  }

  // Media controls handlers
  document.getElementById('btn-toggle-player-body')?.addEventListener('click', togglePlayerBody);
  document.getElementById('btn-close-player')?.addEventListener('click', closeMediaControls);

  // Initialize CosmicPlayer
  initCosmicPlayer();
}

let chatGroupedModels = {};

async function initChatDebuggerToolbar() {
  const modelSelect = document.getElementById('chat-model-select');
  const searchSelect = document.getElementById('chat-search-select');
  const setDefaultBtn = document.getElementById('btn-chat-set-default');

  if (!modelSelect) return;

  // 1. Загрузка списка доступных моделей
  try {
    const res = await fetch('/api/chat/models');
    if (res.ok) {
      const data = await res.json();
      chatGroupedModels = data.models || {};
      if (Array.isArray(chatGroupedModels)) {
        chatGroupedModels = { 'gemini': chatGroupedModels };
      }
    }
  } catch (e) {
    console.error('[ChatDebugger] Ошибка загрузки моделей:', e);
  }

  // 2. Загрузка текущих настроек пользователя и поиска
  let currentModel = window.activeModelName || '';
  let currentSearch = window.activeSearchEngine || 'gemini_cli';
  let searchConfig = {};

  try {
    const sRes = await fetch('/auth/settings');
    if (sRes.ok) {
      const settings = await sRes.json();
      if (settings.model) currentModel = settings.model;
      if (settings.search_engine) currentSearch = settings.search_engine;
    }
  } catch (e) {
    console.error('[ChatDebugger] Ошибка загрузки настроек пользователя:', e);
  }

  try {
    if (window.api && window.api.fetch) {
      const cfg = await window.api.fetch('/api/admin/web-search/config');
      if (cfg) {
        searchConfig = cfg;
        if (cfg.engine && !currentSearch) {
          currentSearch = cfg.engine;
        }
      }
    }
  } catch (e) {
    console.error('[ChatDebugger] Ошибка загрузки конфига веб-поиска:', e);
  }

  // 3. Заполнение иерархического списка моделей ИИ (optgroups по провайдерам)
  function populateHierarchicalModels(modelsGrouped, targetModel = '') {
    modelSelect.innerHTML = '';

    const providerMeta = {
      'gemini': { label: '✨ Google Gemini', order: 1 },
      'agy': { label: '🚀 Google Antigravity (AGY)', order: 2 },
      'foundry': { label: '⚙️ Microsoft Foundry', order: 3 },
      'ollama': { label: '🦙 Ollama (Local)', order: 4 }
    };

    const providers = Object.keys(modelsGrouped).sort((a, b) => {
      const oA = providerMeta[a]?.order ?? 99;
      const oB = providerMeta[b]?.order ?? 99;
      return oA - oB;
    });

    let totalModels = 0;
    let firstModel = '';

    providers.forEach(p => {
      const list = modelsGrouped[p] || [];
      if (!Array.isArray(list) || list.length === 0) return;

      const optgroup = document.createElement('optgroup');
      optgroup.label = providerMeta[p]?.label || `🤖 ${p.toUpperCase()}`;

      list.forEach(m => {
        totalModels++;
        if (!firstModel) firstModel = m;
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        optgroup.appendChild(opt);
      });

      modelSelect.appendChild(optgroup);
    });

    if (totalModels === 0) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'Нет доступных моделей';
      modelSelect.appendChild(opt);
    } else if (targetModel) {
      modelSelect.value = targetModel;
      if (!modelSelect.value && firstModel) {
        modelSelect.value = firstModel;
      }
    } else if (firstModel) {
      modelSelect.value = firstModel;
    }
  }

  // 4. Заполнение иерархического списка провайдеров и моделей веб-поиска (optgroups)
  function populateHierarchicalSearchEngines(modelsGrouped, targetSearch = 'gemini_cli', cfg = {}) {
    if (!searchSelect) return;
    searchSelect.innerHTML = '';

    const geminiList = modelsGrouped.gemini || ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-3.1-flash-lite'];
    const geminiCliList = modelsGrouped.gemini_cli || ['gemini-3.1-flash-lite', 'gemini-2.5-flash', 'gemini-2.5-pro'];
    const agyList = modelsGrouped.agy || ['agy-flash', 'agy-pro', 'agy-gemma-4-26b-a4b-it'];

    const searchStructure = [
      {
        label: '💻 Google Gemini CLI',
        engine: 'gemini_cli',
        models: geminiCliList,
        defaultModel: cfg.gemini_cli_model || 'gemini-3.1-flash-lite'
      },
      {
        label: '♊ Google Gemini Grounding',
        engine: 'gemini',
        models: geminiList,
        defaultModel: cfg.gemini_model || 'gemini-2.5-flash'
      },
      {
        label: '🚀 Google Antigravity (AGY)',
        engine: 'agy',
        models: agyList,
        defaultModel: cfg.agy_model || 'agy-flash'
      },
      {
        label: '🦜 LangChain MCP Agent',
        engine: 'langchain',
        models: ['gemini-2.5-flash', 'ollama:qwen2.5:7b'],
        defaultModel: 'gemini-2.5-flash'
      },
      {
        label: '🎭 Playwright Browser MCP',
        engine: 'playwright',
        models: ['chromium'],
        defaultModel: 'chromium'
      }
    ];

    let targetEngine = targetSearch;
    let targetMdl = '';
    if (targetSearch && targetSearch.includes(':') && !targetSearch.startsWith('ollama:') && !targetSearch.startsWith('foundry:')) {
      const p = targetSearch.split(':');
      targetEngine = p[0];
      targetMdl = p.slice(1).join(':');
    }

    let selectedValueToSet = '';

    searchStructure.forEach(group => {
      const optgroup = document.createElement('optgroup');
      optgroup.label = group.label;

      group.models.forEach(m => {
        const opt = document.createElement('option');
        const val = `${group.engine}:${m}`;
        opt.value = val;
        opt.textContent = m;
        optgroup.appendChild(opt);

        if (group.engine === targetEngine) {
          if (targetMdl && m === targetMdl) {
            selectedValueToSet = val;
          } else if (group.defaultModel && m === group.defaultModel && !selectedValueToSet) {
            selectedValueToSet = val;
          } else if (!selectedValueToSet) {
            selectedValueToSet = val;
          }
        }
      });

      searchSelect.appendChild(optgroup);
    });

    if (selectedValueToSet) {
      searchSelect.value = selectedValueToSet;
    }
  }

  populateHierarchicalModels(chatGroupedModels, currentModel);
  populateHierarchicalSearchEngines(chatGroupedModels, currentSearch, searchConfig);

  // Синхронизация бейджей
  if (typeof window.updateChatBadges === 'function') {
    window.updateChatBadges(modelSelect.value, searchSelect ? searchSelect.value : currentSearch);
  }

  // Обработчик смены модели в иерархическом списке
  modelSelect.onchange = () => {
    if (typeof window.updateChatBadges === 'function') {
      window.updateChatBadges(modelSelect.value, searchSelect ? searchSelect.value : undefined);
    }
  };

  // Обработчик смены поискового движка
  if (searchSelect) {
    searchSelect.onchange = () => {
      if (typeof window.updateChatBadges === 'function') {
        window.updateChatBadges(modelSelect.value, searchSelect.value);
      }
    };
  }

  const setDefaultModelBtn = document.getElementById('btn-chat-set-default-model');
  const setDefaultSearchBtn = document.getElementById('btn-chat-set-default-search');

  // Обработчик кнопки «Дефолтная модель внутренней генерации»
  if (setDefaultModelBtn) {
    setDefaultModelBtn.onclick = async () => {
      const chosenModel = modelSelect.value;

      if (!chosenModel) {
        alert('Выберите модель перед сохранением!');
        return;
      }

      setDefaultModelBtn.disabled = true;
      const origText = setDefaultModelBtn.innerHTML;
      setDefaultModelBtn.innerHTML = '⏳ Сохранение...';

      try {
        await fetch('/auth/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: chosenModel })
        });

        if (typeof window.updateChatBadges === 'function') {
          window.updateChatBadges(chosenModel, undefined);
        }

        const otherModelSelect = document.getElementById('admin-model-select');
        if (otherModelSelect) otherModelSelect.value = chosenModel;
        const modelsTabSelect = document.getElementById('models-tab-select');
        if (modelsTabSelect) modelsTabSelect.value = chosenModel;

        setDefaultModelBtn.classList.remove('btn-outline-warning');
        setDefaultModelBtn.classList.add('btn-success');
        setDefaultModelBtn.innerHTML = '<i class="bi bi-check-circle-fill"></i> Установлена!';
        setTimeout(() => {
          setDefaultModelBtn.classList.remove('btn-success');
          setDefaultModelBtn.classList.add('btn-outline-warning');
          setDefaultModelBtn.innerHTML = origText;
          setDefaultModelBtn.disabled = false;
        }, 2500);

      } catch (err) {
        console.error('[ChatDebugger] Ошибка сохранения дефолтной модели:', err);
        alert('Ошибка сохранения модели: ' + err.message);
        setDefaultModelBtn.disabled = false;
        setDefaultModelBtn.innerHTML = origText;
      }
    };
  }

  // Обработчик кнопки «Дефолтный модуль веб-поиска»
  if (setDefaultSearchBtn) {
    setDefaultSearchBtn.onclick = async () => {
      const rawSearchVal = searchSelect ? searchSelect.value : 'gemini_cli';

      let chosenSearchEngine = rawSearchVal;
      let chosenSearchModel = '';
      if (rawSearchVal.includes(':') && !rawSearchVal.startsWith('ollama:') && !rawSearchVal.startsWith('foundry:')) {
        const parts = rawSearchVal.split(':');
        chosenSearchEngine = parts[0];
        chosenSearchModel = parts.slice(1).join(':');
      }

      setDefaultSearchBtn.disabled = true;
      const origText = setDefaultSearchBtn.innerHTML;
      setDefaultSearchBtn.innerHTML = '⏳ Сохранение...';

      try {
        // 1. Сохраняем поисковый движок в настройках пользователя
        await fetch('/auth/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ search_engine: rawSearchVal })
        });

        // 2. Сохраняем поисковый движок и его модель в конфигурации веб-поиска (если админ)
        try {
          if (window.api && window.api.fetch) {
            const searchPayload = { engine: chosenSearchEngine };
            if (chosenSearchEngine === 'gemini') searchPayload.gemini_model = chosenSearchModel;
            if (chosenSearchEngine === 'gemini_cli') searchPayload.gemini_cli_model = chosenSearchModel;
            if (chosenSearchEngine === 'agy') searchPayload.agy_model = chosenSearchModel;

            await window.api.fetch('/api/admin/web-search/config', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(searchPayload)
            });
          }
        } catch (searchErr) {
          console.warn('[ChatDebugger] Ошибка сохранения движка поиска:', searchErr);
        }

        // 3. Обновляем глобальные бейджи и селекторы
        if (typeof window.updateChatBadges === 'function') {
          window.updateChatBadges(undefined, rawSearchVal);
        }

        const searchTabEngine = document.getElementById('search-tab-engine-selector');
        if (searchTabEngine) searchTabEngine.value = chosenSearchEngine;

        setDefaultSearchBtn.classList.remove('btn-outline-info');
        setDefaultSearchBtn.classList.add('btn-success');
        setDefaultSearchBtn.innerHTML = '<i class="bi bi-check-circle-fill"></i> Установлен!';
        setTimeout(() => {
          setDefaultSearchBtn.classList.remove('btn-success');
          setDefaultSearchBtn.classList.add('btn-outline-info');
          setDefaultSearchBtn.innerHTML = origText;
          setDefaultSearchBtn.disabled = false;
        }, 2500);

      } catch (err) {
        console.error('[ChatDebugger] Ошибка сохранения дефолтного поиска:', err);
        alert('Ошибка сохранения поиска: ' + err.message);
        setDefaultSearchBtn.disabled = false;
        setDefaultSearchBtn.innerHTML = origText;
      }
    };
  }
}

// Export init function for main.js
if (typeof window !== 'undefined') {
  window.initChatTab = initChatTab;
  window.initChatDebuggerToolbar = initChatDebuggerToolbar;
}

async function saveFullHistoryToRag() {
  if (!chatHistory || chatHistory.length === 0) {
    alert('История чата пуста!');
    return;
  }
  
  // Формируем структурированный текст истории диалога
  let fullChatText = "";
  chatHistory.forEach(msg => {
    const roleName = msg.role === 'user' ? 'Пользователь' : 'Ассистент';
    const text = msg.parts[0] || "";
    fullChatText += `${roleName}: ${text}\n\n`;
  });
  
  const timestamp = new Date().toLocaleString('ru-RU');
  const defaultTitle = `Диалог от ${timestamp}`;
  const defaultVoice = `История диалога с ассистентом, сохраненная ${timestamp}.`;
  
  // Заполняем поля модального окна
  document.getElementById('saveHistoryTitleInput').value = defaultTitle;
  document.getElementById('saveHistoryTextInput').value = fullChatText.trim();
  document.getElementById('saveHistoryVoiceInput').value = defaultVoice;
  
  const modalEl = document.getElementById('saveHistoryModal');
  if (!modalEl) return;
  
  const modal = new bootstrap.Modal(modalEl);
  modal.show();
  
  // Настраиваем кнопку подтверждения сохранения
  const confirmBtn = document.getElementById('btn-save-history-confirm');
  if (confirmBtn) {
    confirmBtn.onclick = async () => {
      const title = document.getElementById('saveHistoryTitleInput').value.trim();
      const text = document.getElementById('saveHistoryTextInput').value.trim();
      const voice = document.getElementById('saveHistoryVoiceInput').value.trim();
      
      if (!title || !text) {
        alert('Заголовок и содержимое диалога не могут быть пустыми!');
        return;
      }
      
      confirmBtn.disabled = true;
      confirmBtn.innerHTML = '⏳ Сохранение...';
      
      try {
        const r = await fetch('/api/chat/save-rag', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            query: title,
            chat_text: text,
            voice_text: voice
          })
        });
        
        if (r.ok) {
          alert('✅ История чата успешно сохранена в архив RAG!');
          modal.hide();
        } else {
          const errData = await r.json().catch(() => ({}));
          alert('Ошибка при сохранении: ' + (errData.detail || r.statusText));
        }
      } catch (err) {
        alert('Ошибка сети: ' + err.message);
      } finally {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = 'Сохранить в RAG';
      }
    };
  }
}

function togglePlayerBody() {
  const body = document.getElementById('media-player-body');
  const btn = document.getElementById('btn-toggle-player-body');
  if (body.classList.contains('d-none')) {
    body.classList.remove('d-none');
    btn.textContent = 'Свернуть плеер';
  } else {
    body.classList.add('d-none');
    btn.textContent = 'Развернуть плеер';
  }
}

let cosmicHls = null;
let cosmicHistory = [];

function initCosmicPlayer() {
  const streamForm = document.getElementById('cosmic-stream-form');
  const streamUrlInput = document.getElementById('cosmic-stream-url');
  const badges = document.querySelectorAll('#cosmic-provider-badges [data-prov]');
  
  if (streamForm) {
    streamForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const url = streamUrlInput.value.trim();
      if (url) loadCosmicVideo(url);
    });
  }

  badges.forEach(badge => {
    badge.addEventListener('click', () => {
      const prov = badge.getAttribute('data-prov');
      let demo = '';
      if (prov === 'youtube') demo = 'https://www.youtube.com/watch?v=aqz-KE-bpKQ';
      else if (prov === 'vk') demo = 'https://vk.com/video-22822305_456239018';
      else if (prov === 'rutube') demo = 'https://rutube.ru/video/e7cfcb8cb4310d54026fb4bd56e828d1/';
      else if (prov === 'direct') demo = 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8';
      
      if (demo) {
        streamUrlInput.value = demo;
        loadCosmicVideo(demo);
      }
    });
  });

  // Load history from localStorage
  try {
    cosmicHistory = JSON.parse(localStorage.getItem('cosmic_history_chat') || '[]');
  } catch(e) {}
  renderCosmicHistory();

  // Custom Controls Event Listeners
  const playBtn = document.getElementById('cosmic-play-btn');
  const stopBtn = document.getElementById('cosmic-stop-btn');
  const muteBtn = document.getElementById('cosmic-mute-btn');
  const volSlider = document.getElementById('cosmic-volume-slider');
  const speedSel = document.getElementById('cosmic-speed-select');
  const fullBtn = document.getElementById('cosmic-fullscreen-btn');
  const progContainer = document.getElementById('cosmic-progress-container');
  const videoEl = document.getElementById('cosmic-video-element');

  if (videoEl) {
    videoEl.addEventListener('timeupdate', () => {
      const cur = videoEl.currentTime;
      const dur = videoEl.duration || 0;
      if (dur > 0) {
        document.getElementById('cosmic-progress-bar').style.width = `${(cur / dur) * 100}%`;
      }
      document.getElementById('cosmic-time-current').textContent = formatTime(cur);
      document.getElementById('cosmic-time-duration').textContent = formatTime(dur);
    });

    videoEl.addEventListener('loadedmetadata', () => {
      document.getElementById('cosmic-time-duration').textContent = formatTime(videoEl.duration);
    });
  }

  playBtn?.addEventListener('click', () => {
    if (videoEl.paused) {
      videoEl.play();
      playBtn.textContent = '⏸';
    } else {
      videoEl.pause();
      playBtn.textContent = '▶';
    }
  });

  stopBtn?.addEventListener('click', () => {
    videoEl.pause();
    videoEl.currentTime = 0;
    playBtn.textContent = '▶';
  });

  volSlider?.addEventListener('input', (e) => {
    videoEl.volume = e.target.value;
    if (muteBtn) muteBtn.textContent = e.target.value === '0' ? '🔇' : '🔊';
  });

  muteBtn?.addEventListener('click', () => {
    if (videoEl.muted) {
      videoEl.muted = false;
      volSlider.value = videoEl.volume;
      muteBtn.textContent = '🔊';
    } else {
      videoEl.muted = true;
      volSlider.value = 0;
      muteBtn.textContent = '🔇';
    }
  });

  speedSel?.addEventListener('change', (e) => {
    videoEl.playbackRate = parseFloat(e.target.value);
  });

  progContainer?.addEventListener('click', (e) => {
    const rect = progContainer.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    videoEl.currentTime = pct * videoEl.duration;
  });

  fullBtn?.addEventListener('click', () => {
    const wrapper = document.getElementById('cosmic-video-wrapper');
    if (!document.fullscreenElement) {
      wrapper.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen();
    }
  });
}

function formatTime(sec) {
  if (isNaN(sec)) return '0:00';
  const mins = Math.floor(sec / 60);
  const secs = Math.floor(sec % 60);
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

function loadCosmicVideo(url, title = null) {
  // Clear existing HLS or frames
  const embed = document.getElementById('cosmic-embed-player');
  const videoWrapper = document.getElementById('cosmic-video-wrapper');
  const placeholder = document.getElementById('cosmic-player-placeholder');
  const videoEl = document.getElementById('cosmic-video-element');
  const glow = document.getElementById('cosmic-ambient-glow');

  embed.classList.add('hidden');
  embed.src = '';
  videoWrapper.classList.add('hidden');
  videoEl.pause();
  videoEl.src = '';
  placeholder.classList.add('hidden');

  if (cosmicHls) {
    cosmicHls.destroy();
    cosmicHls = null;
  }

  // Parse URL
  const parsed = parseVideoUrl(url);
  const resolvedTitle = title || parsed.defaultTitle;
  
  document.getElementById('now-playing-title').textContent = resolvedTitle;

  const colors = {
    youtube: 'radial-gradient(circle, rgba(255, 0, 0, 0.15) 0%, transparent 60%)',
    vk: 'radial-gradient(circle, rgba(74, 118, 168, 0.15) 0%, transparent 60%)',
    rutube: 'radial-gradient(circle, rgba(235, 95, 30, 0.15) 0%, transparent 60%)',
    direct: 'radial-gradient(circle, rgba(121, 40, 202, 0.15) 0%, transparent 60%)'
  };
  glow.style.background = colors[parsed.provider] || colors.direct;

  if (parsed.type === 'embed') {
    embed.src = parsed.embedUrl;
    embed.classList.remove('hidden');
  } else if (parsed.type === 'html5') {
    videoWrapper.classList.remove('hidden');
    if (url.includes('.m3u8')) {
      if (typeof Hls !== 'undefined' && Hls.isSupported()) {
        cosmicHls = new Hls();
        cosmicHls.loadSource(url);
        cosmicHls.attachMedia(videoEl);
        cosmicHls.on(Hls.Events.MANIFEST_PARSED, () => videoEl.play());
      } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
        videoEl.src = url;
        videoEl.play();
      }
    } else {
      videoEl.src = url;
      videoEl.play();
    }
  } else {
    // Iframe fallback
    embed.src = url;
    embed.classList.remove('hidden');
  }

  // Save to history list
  addToCosmicHistory(url, resolvedTitle, parsed.provider);
}

function parseVideoUrl(url) {
  const ytReg = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
  const ytMatch = url.match(ytReg);
  if (ytMatch) {
    return {
      provider: 'youtube',
      type: 'embed',
      embedUrl: `https://www.youtube.com/embed/${ytMatch[1]}?autoplay=1&rel=0`,
      defaultTitle: `YouTube (${ytMatch[1]})`
    };
  }

  const vkReg = /vk\.com\/video(-?\d+)_(\d+)/;
  const vkMatch = url.match(vkReg);
  if (vkMatch) {
    return {
      provider: 'vk',
      type: 'embed',
      embedUrl: `https://vk.com/video_ext.php?oid=${vkMatch[1]}&id=${vkMatch[2]}&autoplay=1`,
      defaultTitle: `VK Video (${vkMatch[1]}_${vkMatch[2]})`
    };
  }

  const rutubeReg = /rutube\.ru\/(?:video|play\/embed)\/([a-f0-9]{32})/;
  const rutubeMatch = url.match(rutubeReg);
  if (rutubeMatch) {
    return {
      provider: 'rutube',
      type: 'embed',
      embedUrl: `https://rutube.ru/play/embed/${rutubeMatch[1]}?autoplay=1`,
      defaultTitle: `RuTube Video`
    };
  }

  if (url.includes('.m3u8') || url.includes('.mp4')) {
    return {
      provider: 'direct',
      type: 'html5',
      defaultTitle: url.includes('.m3u8') ? 'Поток HLS' : 'Прямой файл MP4'
    };
  }

  return {
    provider: 'direct',
    type: 'iframe_fallback',
    defaultTitle: 'Веб-фрейм'
  };
}

function addToCosmicHistory(url, title, provider) {
  cosmicHistory = cosmicHistory.filter(h => h.url !== url);
  cosmicHistory.unshift({ url, title, provider });
  if (cosmicHistory.length > 5) cosmicHistory.pop();
  localStorage.setItem('cosmic_history_chat', JSON.stringify(cosmicHistory));
  renderCosmicHistory();
}

function renderCosmicHistory() {
  const container = document.getElementById('cosmic-history-list');
  if (!container) return;
  
  if (cosmicHistory.length === 0) {
    container.innerHTML = '<div class="text-muted small text-center py-2">История пуста</div>';
    return;
  }

  container.innerHTML = cosmicHistory.map(h => `
    <div class="p-1 border rounded bg-dark small cursor-pointer text-truncate cosmic-hist-item" style="cursor:pointer; font-size:0.75rem;" data-url="${h.url}" data-title="${h.title.replace(/"/g, '&quot;')}">
      📁 [${h.provider.toUpperCase()}] ${h.title}
    </div>
  `).join('');

  container.querySelectorAll('.cosmic-hist-item').forEach(item => {
    item.addEventListener('click', () => {
      const url = item.getAttribute('data-url');
      const title = item.getAttribute('data-title');
      document.getElementById('cosmic-stream-url').value = url;
      loadCosmicVideo(url, title);
    });
  });
}

async function sendMessage() {
  const input = document.getElementById('message-input');
  const btn   = document.getElementById('send-button');
  const msg   = input.value.trim();
  if (!msg) return;
  
  // Определяем режим чата до любой логики
  const modeSelector = document.getElementById('chat-mode-selector');
  const chatMode = modeSelector ? modeSelector.value : 'story';

  input.value = '';
  btn.disabled = true; btn.textContent = 'Отправка…';

  const lowMsg = msg.toLowerCase().trim();
  const playCommands = ['включи просмотр', 'запусти просмотр', 'просмотр', 'включи видео', 'открой плеер', 'включить просмотр'];
  if (playCommands.includes(lowMsg)) {
    addMessage('user', msg);
    if (currentMediaPath) {
      openMediaPlayer();
      const body = document.getElementById('media-player-body');
      if (body) {
        body.classList.remove('d-none');
        const btnToggle = document.getElementById('btn-toggle-player-body');
        if (btnToggle) btnToggle.textContent = 'Свернуть плеер';
      }
      const videoEl = document.getElementById('cosmic-video-element');
      if (videoEl && videoEl.src) {
        videoEl.play().catch(() => {});
      }
      
      const reply = "Запускаю просмотр во встроенном плеере.";
      addMessage('bot', reply);
      window.chatService.speak(reply);
      
      btn.disabled = false;
      btn.textContent = 'Отправить';
      return;
    } else {
      const reply = "Медиафайл для воспроизведения не выбран. Пожалуйста, сначала найдите фильм или сериал.";
      addMessage('bot', reply);
      window.chatService.speak(reply);
      
      btn.disabled = false;
      btn.textContent = 'Отправить';
      return;
    }
  }

  // Если режим DEBUG - отправляем запрос в бэкенд, но он вернёт полный промпт вместо ответа модели
  if (isDebugMode) {
    // Показываем запрос пользователя
    addMessage('user', msg);
    
    const win = document.getElementById('chat-window');
    const botMessageEl = document.createElement('div');
    botMessageEl.className = 'message bot-message';
    botMessageEl.innerHTML = `<strong>Ai Ассистент (DEBUG)</strong> (${new Date().toLocaleTimeString()}): <div class="bot-text">⏳ Формирование промпта...</div>`;
    win.appendChild(botMessageEl);
    win.scrollTop = win.scrollHeight;
    const textDiv = botMessageEl.querySelector('.bot-text');

    let fullReply = '';
    let started = false;

    try {
      const selectedModel = document.getElementById('chat-model-select')?.value || undefined;
      const selectedSearch = document.getElementById('chat-search-select')?.value || undefined;

      const replyObj = await window.chatService.sendChatMessage(msg, (chunk, status, voice) => {
        if (status) {
          textDiv.innerHTML = `<span style="color: #8b949e; font-style: italic;">⚙️ ${status}</span>`;
        }
        if (chunk) {
          if (!started) {
            textDiv.textContent = '';
            started = true;
          }
          fullReply += chunk;
          textDiv.innerHTML = parseContentToHtml(fullReply);
        }
        win.scrollTop = win.scrollHeight;
      }, chatHistory, {
        chat_mode: chatMode,
        debug_mode: true,
        model: selectedModel,
        search_engine: selectedSearch
      });

      // В DEBUG режиме не сохраняем запрос и ответ в историю диалога

      // В DEBUG режиме мы получаем полный промпт в тексте
      textDiv.innerHTML = `<div style="background: rgba(255, 235, 59, 0.1); border: 1px solid #ffeb3b; border-radius: 8px; padding: 15px; margin-top: 10px;">
        <div style="color: #fbc02d; font-weight: bold; margin-bottom: 10px; font-size: 1.1em;">⚠️ DEBUG MODE: Полный промпт (не отправлялся в модель)</div>
        <pre style="background: #fff9c4; padding: 10px; border-radius: 5px; font-size: 0.85em; overflow-x: auto; white-space: pre-wrap; font-family: monospace; border: 1px solid #f57f17;">${fullReply.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
        <div style="color: #fbc02d; margin-top: 10px; font-size: 0.9em;">
          <strong>Чтобы отправить запрос в модель, переключитесь в режим PROD</strong>
        </div>
      </div>`;

      // Не сохраняем ответ в историю в DEBUG режиме, так как это не реальный ответ модели
    } catch (err) {
      if (!started) {
        textDiv.textContent = '';
      }
      let errText;
      if (err instanceof Error) {
        errText = err.message;
      } else if (typeof err === 'object' && err !== null) {
        errText = JSON.stringify(err);
      } else {
        errText = String(err);
      }
      textDiv.innerHTML = `<span style="color: #ff7070;">Ошибка: ${errText}</span>`;
    }
    finally { btn.disabled = false; btn.textContent = 'Отправить'; }
    return;
  }

  // Показываем запрос пользователя
  addMessage('user', msg);

  const win = document.getElementById('chat-window');
  const botMessageEl = document.createElement('div');
  botMessageEl.className = 'message bot-message';
  botMessageEl.innerHTML = `<strong>Ai Ассистент</strong> (${new Date().toLocaleTimeString()}): <div class="bot-text">⏳ Ожидание ответа...</div>`;
  win.appendChild(botMessageEl);
  win.scrollTop = win.scrollHeight;
  const textDiv = botMessageEl.querySelector('.bot-text');

  let fullReply = '';
  let started = false;
  
  const isAdminChat = !!document.getElementById('tab-rag') || window.location.pathname.includes('/admin') || window.location.href.includes('/admin');

  try {
    const selectedModel = document.getElementById('chat-model-select')?.value || undefined;
    const selectedSearch = document.getElementById('chat-search-select')?.value || undefined;

    const replyObj = await window.chatService.sendChatMessage(msg, (chunk, status, voice, promptDump) => {
      if (status) {
        textDiv.innerHTML = `<span style="color: #8b949e; font-style: italic;">⚙️ ${status}</span>`;
      }
      if (isAdminChat && promptDump && !botMessageEl.querySelector('.prompt-dump-details')) {
         const details = document.createElement('details');
         details.className = 'prompt-dump-details';
         details.style.cssText = 'margin-bottom: 10px; font-size: 0.85em; background: #0d1117; padding: 10px; border-radius: 6px; border: 1px solid #30363d; box-shadow: inset 0 1px 4px rgba(0,0,0,0.8);';
         details.innerHTML = `<summary style="cursor: pointer; color: #e3b341; font-weight: bold; user-select: none;">🔍 Просмотр сформированного промпта (Admin)</summary><pre style="white-space: pre-wrap; margin-top: 10px; color: #00ff66; font-family: 'Consolas', 'Courier New', Courier, monospace; font-size: 0.95em; line-height: 1.4; max-height: 300px; overflow-y: auto;">${promptDump.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>`;
         botMessageEl.insertBefore(details, textDiv);
      }
      if (chunk) {
        if (!started) {
          textDiv.textContent = '';
          started = true;
        }
        fullReply += chunk;
        textDiv.innerHTML = parseContentToHtml(fullReply);
      }
      win.scrollTop = win.scrollHeight;
    }, chatHistory, {
      chat_mode: chatMode,
      debug_mode: isDebugMode,
      model: selectedModel,
      search_engine: selectedSearch
    });

    const reply = replyObj.text;
    const voiceReply = replyObj.voice || reply;
    const followUp = replyObj.followUp;

    const card = tryParseMovieCard(reply);
    if (card) {
      textDiv.innerHTML = renderMovieCardHtml(card);
      window.chatService.speak(card);
    } else {
      const isAdminChat = !!document.getElementById('tab-rag') || window.location.pathname.includes('/admin') || window.location.href.includes('/admin');
      if (isAdminChat && replyObj.voice && replyObj.voice !== reply) {
        textDiv.innerHTML = parseContentToHtml("**[Текст для чата]:**\n" + reply + "\n\n**[Текст для диктора]:**\n" + voiceReply);
      } else {
        textDiv.innerHTML = parseContentToHtml(isAdminChat ? voiceReply : reply);
      }
      window.chatService.speak(voiceReply);
    }

    // Save valid conversation turns to history
    const isErrorOrEmpty = !reply || 
      reply.trim().startsWith('❌') || 
      reply.trim().startsWith('Ошибка') || 
      reply.trim().startsWith('Error') || 
      reply.includes('В локальной базе ничего не найдено') || 
      reply.includes('DEBUG MODE');

    if (!isErrorOrEmpty) {
      chatHistory.push({ role: 'user', parts: [msg] });
      chatHistory.push({ role: 'model', parts: [reply] });
      try {
        localStorage.setItem('chat_history', JSON.stringify(chatHistory));
      } catch (e) {}
    }

    // Добавляем кнопку "Сохранить в RAG" только в интерфейсе администратора
    addRagButton(botMessageEl, msg, reply, voiceReply);

    if (typeof fullReply === 'string' && !card) {
      await parseFilmTags(fullReply, botMessageEl);
    }
    
    // Automatically trigger follow-up query to emulate a dialog
    if (followUp) {
      document.getElementById('message-input').value = followUp;
      setTimeout(() => {
        const btn = document.getElementById('send-button');
        if (btn && !btn.disabled) btn.click();
      }, 1500);
    }
  } catch (err) {
    if (!started) {
      textDiv.textContent = '';
    }
    let errText;
    if (err instanceof Error) {
      errText = err.message;
    } else if (typeof err === 'object' && err !== null) {
      errText = JSON.stringify(err);
    } else {
      errText = String(err);
    }
    textDiv.innerHTML = `<span style="color: #ff7070;">Ошибка: ${errText}</span>`;
  }
  finally { btn.disabled = false; btn.textContent = 'Отправить'; }
}

function tryParseMovieCard(text) {
  const trimmed = text.trim();
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    try {
      const data = JSON.parse(trimmed);
      if (data.title || data.title_ru) return data;
    } catch (e) {}
  }
  const match = text.match(/\{[\s\S]*?\}/);
  if (match) {
    try {
      const data = JSON.parse(match[0]);
      if (data.title || data.title_ru) return data;
    } catch (e) {}
  }
  return null;
}

function renderMovieCardHtml(card) {
  const title = card.title_ru || card.title;
  const subtitle = card.title_orig || '';
  const year = card.year || '';
  const category = card.main_category || '';
  const genres = card.genres ? card.genres.join(', ') : '';
  const directors = card.directors ? card.directors.join(', ') : '';
  const cast = card.cast ? card.cast.slice(0, 5).join(', ') : '';
  const plot = card.plot || '';
  const whyWatch = card.why_watch || '';
  
  let ratingHtml = '';
  if (card.rating) {
    if (card.rating.imdb) ratingHtml += `<span class="badge bg-warning text-dark me-1">IMDb: ${card.rating.imdb}</span>`;
    if (card.rating.кинопоиск) ratingHtml += `<span class="badge bg-danger text-white me-1">КП: ${card.rating.кинопоиск}</span>`;
    if (card.rating.tmdb) ratingHtml += `<span class="badge bg-primary text-white">TMDB: ${card.rating.tmdb}</span>`;
  }

  return `
    <div class="p-3 text-white card-media-custom" style="border-radius: 10px; background: rgba(88, 166, 255, 0.08); border: 1px solid rgba(88, 166, 255, 0.2); max-width: 480px; margin-top: 10px;">
      <h5 class="mb-1 text-info">${title}</h5>
      <div class="small text-muted mb-2">${subtitle} ${year ? `(${year})` : ''}</div>
      <div class="mb-2">${ratingHtml}</div>
      ${category ? `<div class="small text-muted mb-1" style="font-size: 0.8rem;"><strong>Категория:</strong> ${category}</div>` : ''}
      ${genres ? `<div class="small text-muted mb-1" style="font-size: 0.8rem;"><strong>Жанры:</strong> ${genres}</div>` : ''}
      ${directors ? `<div class="small text-muted mb-1" style="font-size: 0.8rem;"><strong>Режиссер:</strong> ${directors}</div>` : ''}
      ${cast ? `<div class="small text-muted mb-2" style="font-size: 0.8rem;"><strong>В ролях:</strong> ${cast}...</div>` : ''}
      ${plot ? `<p class="small text-secondary mb-2" style="font-size: 0.85rem; line-height: 1.4;">${plot}</p>` : ''}
      ${whyWatch ? `<div class="small text-info mb-2" style="font-size: 0.8rem;"><strong>Рекомендация:</strong> ${whyWatch}</div>` : ''}
      <div class="d-flex justify-content-end mt-2">
        <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="playMovieDirect('${title.replace(/'/g, "\\'")}')">
          <i class="bi bi-play-fill"></i> Запустить фильм
        </button>
      </div>
    </div>
  `;
}

window.playMovieDirect = async (title) => {
  try {
    const r = await fetch('/api/media/by-title', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title})
    });
    if (r.ok) {
      const data = await r.json();
      if (data.path) {
        // Expand player bar
        const body = document.getElementById('media-player-body');
        const btn = document.getElementById('btn-toggle-player-body');
        if (body) body.classList.remove('d-none');
        if (btn) btn.textContent = 'Свернуть плеер';
        
        // Load direct stream or file path
        const isUrl = data.path.startsWith('http://') || data.path.startsWith('https://');
        const streamUrl = isUrl ? data.path : `/api/media/stream?path=${encodeURIComponent(data.path)}`;
        loadCosmicVideo(streamUrl, data.title || title);
      } else {
        showFilmNotFoundCard(title);
      }
    } else {
      showFilmNotFoundCard(title);
    }
  } catch (e) {
    console.error(e);
    showFilmNotFoundCard(title);
  }
};

function parseContentToHtml(text) {
  if (!text) return '';
  
  // Clean markdown code blocks if the content is wrapped in them
  let cleaned = text.trim();
  const codeBlockRegex = /^```(?:html|xml)?\s*([\s\S]*?)\s*```$/i;
  const match = cleaned.match(codeBlockRegex);
  if (match) {
    cleaned = match[1];
  }

  let html = cleaned;
  if (window.marked && typeof window.marked.parse === 'function') {
    html = window.marked.parse(cleaned);
  } else {
    // Basic fallback for formatting if marked is not loaded
    html = cleaned
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }
  return replaceFilmTagsWithLinks(html);
}

function addRagButton(botMessageEl, query, reply, voiceReply) {
  const isAdminChat = !!document.getElementById('tab-rag') || window.location.pathname.includes('/admin') || window.location.href.includes('/admin');
  if (!isAdminChat) return;

  // Check if button already exists to avoid duplicates
  if (botMessageEl.querySelector('.rag-btn-container')) return;

  const ragBtnContainer = document.createElement('div');
  ragBtnContainer.className = 'mt-2 text-end rag-btn-container d-flex justify-content-end gap-1';
  
  // 1. Button: Archive RAG
  const archiveBtn = document.createElement('button');
  archiveBtn.className = 'btn btn-xs btn-outline-secondary py-1 px-2';
  archiveBtn.style.fontSize = '0.75rem';
  archiveBtn.innerHTML = '💾 В архив RAG';
  archiveBtn.onclick = async () => {
    archiveBtn.disabled = true;
    instantBtn.disabled = true;
    archiveBtn.innerHTML = '⏳ Сохранение...';
    try {
      const r = await fetch('/api/chat/save-rag', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query: query, chat_text: reply, voice_text: voiceReply || reply })
      });
      if (r.ok) {
        archiveBtn.innerHTML = '✅ Сохранено в архив';
        archiveBtn.classList.remove('btn-outline-secondary');
        archiveBtn.classList.add('btn-success');
        instantBtn.remove();
      } else {
        const errData = await r.json().catch(() => ({}));
        alert('Ошибка при сохранении: ' + (errData.detail || r.statusText));
        archiveBtn.innerHTML = '❌ Ошибка';
        archiveBtn.disabled = false;
        instantBtn.disabled = false;
      }
    } catch (err) {
      alert('Ошибка сети: ' + err.message);
      archiveBtn.innerHTML = '❌ Ошибка сети';
      archiveBtn.disabled = false;
      instantBtn.disabled = false;
    }
  };

  // 2. Button: Instant RAG
  const instantBtn = document.createElement('button');
  instantBtn.className = 'btn btn-xs btn-outline-primary py-1 px-2';
  instantBtn.style.fontSize = '0.75rem';
  instantBtn.innerHTML = '⚡ Мгновенно в RAG';
  instantBtn.onclick = async () => {
    archiveBtn.disabled = true;
    instantBtn.disabled = true;
    instantBtn.innerHTML = '⏳ Индексация...';
    try {
      const r = await fetch('/api/chat/save-rag-instant', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query: query, chat_text: reply, voice_text: voiceReply || reply })
      });
      if (r.ok) {
        instantBtn.innerHTML = '⚡✅ Проиндексировано';
        instantBtn.classList.remove('btn-outline-primary');
        instantBtn.classList.add('btn-success');
        archiveBtn.remove();
      } else {
        const errData = await r.json().catch(() => ({}));
        alert('Ошибка при сохранении в RAG: ' + (errData.detail || r.statusText));
        instantBtn.innerHTML = '❌ Ошибка';
        archiveBtn.disabled = false;
        instantBtn.disabled = false;
      }
    } catch (err) {
      alert('Ошибка сети: ' + err.message);
      instantBtn.innerHTML = '❌ Ошибка сети';
      archiveBtn.disabled = false;
      instantBtn.disabled = false;
    }
  };

  // 3. Button: Delete turn from history
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'btn btn-xs btn-outline-danger py-1 px-2';
  deleteBtn.style.fontSize = '0.75rem';
  deleteBtn.innerHTML = '🗑️ Удалить';
  deleteBtn.onclick = () => {
    if (confirm('Удалить эту пару сообщений из истории диалога?')) {
      // Remove from DOM
      const prev = botMessageEl.previousElementSibling;
      if (prev && prev.classList.contains('user-message')) {
        prev.remove();
      }
      botMessageEl.remove();
      
      // Remove from memory
      for (let i = 0; i < chatHistory.length - 1; i++) {
        if (chatHistory[i].role === 'user' && chatHistory[i].parts[0] === query &&
            chatHistory[i+1].role === 'model' && chatHistory[i+1].parts[0] === reply) {
          chatHistory.splice(i, 2);
          break;
        }
      }
      // Update local storage
      try {
        localStorage.setItem('chat_history', JSON.stringify(chatHistory));
      } catch (e) {}
    }
  };

  ragBtnContainer.appendChild(archiveBtn);
  ragBtnContainer.appendChild(instantBtn);
  ragBtnContainer.appendChild(deleteBtn);
  botMessageEl.appendChild(ragBtnContainer);
}

function addMessage(sender, text, query = '') {
  const win = document.getElementById('chat-window');
  const el  = document.createElement('div');
  el.className = 'message ' + (sender === 'user' ? 'user-message' : 'bot-message');
  
  let displayText;
  if (typeof text === 'object' && text !== null) {
    displayText = window.chatService.formatMessage(text);
  } else {
    displayText = parseContentToHtml(text);
  }
  
  el.innerHTML = `<strong>${sender === 'user' ? 'Вы' : 'Бот'}</strong> (${new Date().toLocaleTimeString()}): ${displayText}`;
  win.appendChild(el); win.scrollTop = win.scrollHeight;

  if (sender === 'bot' && query) {
    addRagButton(el, query, text, text);
  }
}

// ── Film Tag Parsing & Media Player ───────────────────────────────────────────

const FILM_TAG_REGEX = /<film>(.*?)<\/film>/gi;

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function replaceFilmTagsWithLinks(text) {
  if (!text) return '';
  return text.replace(FILM_TAG_REGEX, (match, title) => {
    const cleanTitle = title.replace(/'/g, "\\'");
    const safeTitle = escapeHtml(title);
    return `<span class="film-interactive-chip" title="Film: ${safeTitle}">` +
      `<span class="film-chip-title" onclick="playMovieDirect('${cleanTitle}')">` +
        `<i class="bi bi-film me-1"></i>${safeTitle}` +
      `</span>` +
      `<button type="button" class="film-chip-btn film-chip-play" onclick="playMovieDirect('${cleanTitle}')" title="Play in media player">` +
        `<i class="bi bi-play-fill"></i>` +
      `</button>` +
      `<button type="button" class="film-chip-btn film-chip-youtube" onclick="window.openYouTubeForFilm('${cleanTitle}')" title="Watch trailer/video on YouTube">` +
        `<i class="bi bi-youtube"></i>` +
      `</button>` +
      `<button type="button" class="film-chip-btn film-chip-online" onclick="window.openOnlineCinemaForFilm('${cleanTitle}')" title="Watch online (Yandex Video / Cinemas)">` +
        `<i class="bi bi-globe"></i>` +
      `</button>` +
      `<button type="button" class="film-chip-btn film-chip-torrent" onclick="window.openTorrentsTab('${cleanTitle}')" title="Search torrent releases">` +
        `<i class="bi bi-download"></i>` +
      `</button>` +
    `</span>`;
  });
}

async function parseFilmTags(text, botMessageEl) {
  const matches = [...text.matchAll(FILM_TAG_REGEX)];
  if (matches.length === 0) return;

  // Check first matched title
  const filmTitle = matches[0][1].trim();
  const found = await findAndShowMedia(filmTitle);
  if (!found) {
    showFilmNotFoundCard(filmTitle, botMessageEl);
  }
}

async function findAndShowMedia(title) {
  try {
    const r = await fetch('/api/media/by-title', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title})
    });
    if (!r.ok) return false;
    const data = await r.json();
    if (!data.path) return false;

    currentMediaPath = data.path;
    const controls = document.getElementById('media-controls');
    if (controls) {
      document.getElementById('now-playing-title').textContent = data.title || title;
      controls.classList.remove('d-none');
    }
    
    // Automatically trigger toggle for previewing
    const body = document.getElementById('media-player-body');
    const btn = document.getElementById('btn-toggle-player-body');
    if (body) body.classList.remove('d-none');
    if (btn) btn.textContent = 'Свернуть плеер';
    
    const isUrl = data.path.startsWith('http://') || data.path.startsWith('https://');
    const streamUrl = isUrl ? data.path : `/api/media/stream?path=${encodeURIComponent(data.path)}`;
    loadCosmicVideo(streamUrl, data.title || title);
    return true;
  } catch (e) {
    console.error('findAndShowMedia:', e);
    return false;
  }
}

function showFilmNotFoundCard(title, botMessageEl) {
  const targetParent = botMessageEl || document.getElementById('chat-window');
  if (!targetParent) return;

  // Check for duplicate card for the same title
  const existingCard = targetParent.querySelector(`[data-film-card="${title.toLowerCase()}"]`);
  if (existingCard) return;

  const safeId = 'torrent-res-' + Math.random().toString(36).substring(2, 9);
  const cleanTitle = title.replace(/'/g, "\\'");

  const cardDiv = document.createElement('div');
  cardDiv.className = 'mt-2 film-not-found-card';
  cardDiv.setAttribute('data-film-card', title.toLowerCase());
  cardDiv.innerHTML = `
    <div class="card border-warning border-opacity-50 text-white shadow-sm" style="border-radius: 10px; background: rgba(33, 37, 41, 0.95);">
      <div class="card-body p-3">
        <div class="d-flex align-items-center gap-2 mb-2">
          <span class="fs-5 text-warning">🔍</span>
          <div>
            <div class="fw-bold text-warning small">Фильм «${escapeHtml(title)}» не найден на локальных дисках</div>
            <div class="text-muted" style="font-size: 0.75rem;">Смотрите онлайн, на YouTube или найдите раздачу на торрент-трекерах:</div>
          </div>
        </div>
        <div class="d-flex flex-wrap gap-2 mt-2">
          <button class="btn btn-sm btn-outline-danger py-1 px-2" style="font-size: 0.8rem;" onclick="window.openYouTubeForFilm('${cleanTitle}')" title="Смотреть трейлер или видео">
            <i class="bi bi-youtube me-1"></i> YouTube
          </button>
          <button class="btn btn-sm btn-outline-info py-1 px-2" style="font-size: 0.8rem;" onclick="window.openOnlineCinemaForFilm('${cleanTitle}')" title="Поиск онлайн видео">
            <i class="bi bi-globe me-1"></i> Онлайн-кинотеатры
          </button>
          <button class="btn btn-sm btn-outline-primary py-1 px-2" style="font-size: 0.8rem;" onclick="window.openKinopoiskForFilm('${cleanTitle}')" title="Открыть страницу на Кинопоиске">
            <i class="bi bi-film me-1"></i> Кинопоиск
          </button>
          <button class="btn btn-sm btn-outline-warning py-1 px-2" style="font-size: 0.8rem;" onclick="window.searchTorrentForFilm('${cleanTitle}', '${safeId}')" title="Искать раздачи">
            <i class="bi bi-magnet me-1"></i> Торренты
          </button>
          <button class="btn btn-sm btn-outline-secondary py-1 px-2" style="font-size: 0.8rem;" onclick="window.searchWebForFilm('${cleanTitle}')" title="Спросить у AI">
            <i class="bi bi-search me-1"></i> Инфо в веб
          </button>
        </div>
        <div id="${safeId}" class="mt-2 d-none"></div>
      </div>
    </div>
  `;

  if (botMessageEl) {
    botMessageEl.appendChild(cardDiv);
  } else {
    targetParent.appendChild(cardDiv);
    targetParent.scrollTop = targetParent.scrollHeight;
  }
}

window.searchTorrentForFilm = async (title, targetId) => {
  const container = document.getElementById(targetId);
  if (!container) return;

  container.classList.remove('d-none');
  container.innerHTML = '<div class="text-muted small py-2"><span class="spinner-border spinner-border-sm me-2"></span>Поиск раздач на трекерах (Rutracker, NNMClub)...</div>';

  try {
    const res = await fetch(`/api/torrents/search?query=${encodeURIComponent(title)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const torrents = data.torrents || data.results || (Array.isArray(data) ? data : []);

    if (torrents.length === 0) {
      container.innerHTML = '<div class="small text-muted py-1">❌ На трекерах раздач не найдено. Попробуйте поискать во вкладке «Торренты».</div>';
      return;
    }

    let html = `<div class="small text-info mb-2 fw-semibold">Найдено раздач: ${torrents.length}</div><div class="list-group list-group-flush border-top border-secondary border-opacity-50">`;
    torrents.slice(0, 5).forEach(t => {
      const tTitle = t.title || t.name || 'Раздача';
      const tSize = t.size || t.size_str || '—';
      const tSeeds = t.seeds !== undefined ? t.seeds : '—';
      const tSource = t.source || t.tracker || 'Tracker';
      const tUrl = t.url || t.magnet || t.download_url || '';

      html += `
        <div class="list-group-item bg-transparent text-white border-secondary border-opacity-25 px-0 py-2 d-flex justify-content-between align-items-center">
          <div style="max-width: 75%;">
            <div class="fw-semibold text-truncate small" title="${escapeHtml(tTitle)}">${escapeHtml(tTitle)}</div>
            <div class="text-muted" style="font-size: 0.75rem;">
              <span class="badge bg-secondary text-white me-1">${escapeHtml(tSource)}</span>
              💾 ${escapeHtml(tSize)} | ⬆️ Сиды: ${escapeHtml(String(tSeeds))}
            </div>
          </div>
          <button class="btn btn-sm btn-outline-success download-torrent-btn" 
                  data-url="${encodeURIComponent(tUrl)}" 
                  data-source="${escapeHtml(tSource)}" 
                  data-title="${escapeHtml(tTitle)}"
                  style="font-size: 0.75rem; white-space: nowrap;">
            📥 Скачать
          </button>
        </div>
      `;
    });
    html += '</div>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="small text-danger">Ошибка поиска торрентов: ${escapeHtml(err.message)}</div>`;
  }
};

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

window.searchWebForFilm = (title) => {
  const msgInput = document.getElementById('message-input');
  if (msgInput) {
    msgInput.value = `найди в интернете информацию о фильме ${title}`;
    const sendBtn = document.getElementById('send-button');
    if (sendBtn) sendBtn.click();
  }
};

window.openTorrentsTab = (title) => {
  const tabBtn = document.querySelector('[data-bs-target="#tab-torrents"]');
  if (tabBtn) {
    tabBtn.click();
  } else {
    window.searchWebForFilm(`скачать торрент ${title}`);
  }
};

function openMediaPlayer() {
  if (!currentMediaPath) return;
  // Открываем в новой вкладке с локальным плеером
  const encoded = encodeURIComponent(currentMediaPath);
  window.open(`/html/player/index.html?file=${encoded}`, '_blank');
}

function closeMediaControls() {
  const controls = document.getElementById('media-controls');
  controls.classList.add('d-none');
  currentMediaPath = null;
}

// ── DEBUG MODE HELPERS ───────────────────────────────────────────────────────

async function loadSystemInstruction() {
  try {
    const response = await fetch('/auth/settings');
    if (response.ok) {
      const settings = await response.json();
      systemInstruction = settings.system_instruction || null;
    }
  } catch (e) {
    console.error('Failed to load system instruction:', e);
    systemInstruction = null;
  }
}
