// ── CHAT.JS ───────────────────────────────────────────────────────────────────

const STORAGE_KEY_SESSIONS = 'breadboard_chat_sessions_v2';
const STORAGE_KEY_ACTIVE_SESSION_ID = 'breadboard_active_session_id';
const STORAGE_KEY_SIDEBAR_COLLAPSED = 'breadboard_chat_sidebar_collapsed';
const LEGACY_STORAGE_KEY = 'breadboard_chat_history';

let sessions = [];
let activeSessionId = null;

/**
 * Generates a clean, human-friendly title based on the first prompt (ChatGPT-style).
 */
function generateSessionTitle(prompt) {
  if (!prompt || typeof prompt !== 'string') return 'Новый чат';

  let clean = prompt
    .replace(/^```[\s\S]*?```/g, '')
    .replace(/<[^>]*>/g, '')
    .replace(/[*_#`[\]()]/g, '')
    .trim();

  if (!clean) return 'Новый чат';

  // Take the first line or first sentence
  const firstLine = clean.split('\n')[0].trim();
  const sentenceMatch = firstLine.match(/^(.+?)(?:[.!?]|$)/);
  let text = sentenceMatch ? sentenceMatch[1].trim() : firstLine;

  if (text.length > 36) {
    text = text.substring(0, 36).trim();
    const lastSpace = text.lastIndexOf(' ');
    if (lastSpace > 15) {
      text = text.substring(0, lastSpace);
    }
    text += '...';
  }

  // Capitalize first character
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function saveSessions() {
  try {
    localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sessions));
    if (activeSessionId) {
      localStorage.setItem(STORAGE_KEY_ACTIVE_SESSION_ID, activeSessionId);
    }
  } catch (err) {
    console.warn('Failed to save chat sessions to localStorage:', err);
  }
}

function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_SESSIONS);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        sessions = parsed;
        const savedActiveId = localStorage.getItem(STORAGE_KEY_ACTIVE_SESSION_ID);
        if (savedActiveId && sessions.some((s) => s.id === savedActiveId)) {
          activeSessionId = savedActiveId;
        } else {
          activeSessionId = sessions[0].id;
        }
        return;
      }
    }

    // Migrate from legacy single-session chat history if present
    const legacyRaw = localStorage.getItem(LEGACY_STORAGE_KEY);
    if (legacyRaw) {
      try {
        const legacyLog = JSON.parse(legacyRaw);
        if (Array.isArray(legacyLog) && legacyLog.length > 0) {
          const firstUserMsg = legacyLog.find((m) => m.sender === 'user');
          const title = firstUserMsg ? generateSessionTitle(firstUserMsg.text) : 'Предыдущий диалог';
          const legacyHistory = [];
          for (const item of legacyLog) {
            legacyHistory.push({
              role: item.sender === 'user' ? 'user' : 'model',
              parts: [item.text || item.voiceText || '']
            });
          }

          const legacySession = {
            id: 'session_' + Date.now(),
            title: title,
            isCustomTitle: false,
            createdAt: Date.now(),
            updatedAt: Date.now(),
            messages: legacyLog,
            chatHistory: legacyHistory
          };
          sessions = [legacySession];
          activeSessionId = legacySession.id;
          saveSessions();
          return;
        }
      } catch (e) {
        console.warn('Failed to migrate legacy chat history:', e);
      }
    }

    // Default clean initial session
    createNewSession('Новый чат', true);
  } catch (err) {
    console.warn('Failed to load chat sessions:', err);
    sessions = [];
    createNewSession('Новый чат', true);
  }
}

function getActiveSession() {
  if (!activeSessionId || sessions.length === 0) {
    return createNewSession('Новый чат', true);
  }
  let session = sessions.find((s) => s.id === activeSessionId);
  if (!session) {
    session = sessions[0];
    activeSessionId = session.id;
  }
  return session;
}

function createNewSession(title = 'Новый чат', makeActive = true) {
  const newSession = {
    id: 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7),
    title: title,
    isCustomTitle: false,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages: [],
    chatHistory: []
  };

  sessions.unshift(newSession);
  if (makeActive) {
    activeSessionId = newSession.id;
  }
  saveSessions();
  renderSessionsList();
  renderActiveSessionMessages();
  return newSession;
}

function switchSession(sessionId) {
  if (sessionId === activeSessionId) return;
  const session = sessions.find((s) => s.id === sessionId);
  if (!session) return;

  activeSessionId = sessionId;
  saveSessions();
  renderSessionsList();
  renderActiveSessionMessages();

  const msgInput = document.getElementById('message-input');
  if (msgInput) msgInput.focus();
}

function renameSession(sessionId, newTitle = null) {
  const session = sessions.find((s) => s.id === sessionId);
  if (!session) return;

  let title = newTitle;
  if (title === null) {
    title = prompt('Введите новое название диалога:', session.title);
  }

  if (title && title.trim()) {
    session.title = title.trim();
    session.isCustomTitle = true;
    session.updatedAt = Date.now();
    saveSessions();
    renderSessionsList();
    if (session.id === activeSessionId) {
      updateCurrentSessionHeader();
    }
  }
}

function deleteSession(sessionId) {
  const index = sessions.findIndex((s) => s.id === sessionId);
  if (index === -1) return;

  sessions.splice(index, 1);
  if (sessions.length === 0) {
    createNewSession('Новый чат', true);
  } else if (activeSessionId === sessionId) {
    activeSessionId = sessions[0].id;
    renderActiveSessionMessages();
  }

  saveSessions();
  renderSessionsList();
}

function clearCurrentSession() {
  const session = getActiveSession();
  if (!session) return;

  session.messages = [];
  session.chatHistory = [];
  session.title = 'Новый чат';
  session.isCustomTitle = false;
  session.updatedAt = Date.now();

  saveSessions();
  renderSessionsList();
  renderActiveSessionMessages();
}

function clearAllSessions() {
  if (!confirm('Вы уверены, что хотите удалить ВСЕ сохраненные диалоги?')) return;

  sessions = [];
  try {
    localStorage.removeItem(STORAGE_KEY_SESSIONS);
    localStorage.removeItem(STORAGE_KEY_ACTIVE_SESSION_ID);
    localStorage.removeItem(LEGACY_STORAGE_KEY);
  } catch (e) {}

  createNewSession('Новый чат', true);
}

function updateCurrentSessionHeader() {
  const titleEl = document.getElementById('chat-current-title');
  const session = getActiveSession();
  if (titleEl && session) {
    titleEl.textContent = session.title || 'Новый чат';
    titleEl.title = session.title || 'Новый чат';
  }
}

function renderSessionsList() {
  const listEl = document.getElementById('chat-sessions-list');
  const countEl = document.getElementById('chat-sessions-count');
  if (!listEl) return;

  listEl.innerHTML = '';
  if (countEl) {
    countEl.textContent = `${sessions.length} ${sessions.length === 1 ? 'чат' : (sessions.length < 5 ? 'чата' : 'чатов')}`;
  }

  updateCurrentSessionHeader();

  sessions.forEach((session) => {
    const item = document.createElement('div');
    const isActive = session.id === activeSessionId;
    item.className = 'chat-session-item d-flex align-items-center justify-content-between p-1 px-2 rounded mb-1' + (isActive ? ' active' : '');
    item.dataset.sessionId = session.id;

    item.innerHTML = `
      <div class="chat-session-title d-flex align-items-center gap-1 text-truncate flex-grow-1 me-1" title="${session.title}">
        <i class="bi bi-chat-text ${isActive ? 'text-primary' : 'text-muted'} flex-shrink-0"></i>
        <span class="text-truncate">${session.title}</span>
      </div>
      <div class="chat-session-actions d-flex align-items-center gap-1 flex-shrink-0">
        <button class="btn btn-sm btn-link text-muted p-0 btn-rename" title="Переименовать" type="button">
          <i class="bi bi-pencil" style="font-size: 0.8rem;"></i>
        </button>
        <button class="btn btn-sm btn-link text-danger p-0 btn-delete" title="Удалить" type="button">
          <i class="bi bi-trash" style="font-size: 0.8rem;"></i>
        </button>
      </div>
    `;

    item.addEventListener('click', (e) => {
      if (e.target.closest('.btn-rename') || e.target.closest('.btn-delete')) return;
      switchSession(session.id);
    });

    const renameBtn = item.querySelector('.btn-rename');
    if (renameBtn) {
      renameBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        renameSession(session.id);
      });
    }

    const deleteBtn = item.querySelector('.btn-delete');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm(`Удалить диалог "${session.title}"?`)) {
          deleteSession(session.id);
        }
      });
    }

    listEl.appendChild(item);
  });
}

function renderActiveSessionMessages() {
  const chatWindow = document.getElementById('chat-window');
  if (!chatWindow) return;

  chatWindow.innerHTML = '';
  const session = getActiveSession();

  if (session && session.messages && session.messages.length > 0) {
    for (const msg of session.messages) {
      addMessageToDom(msg.sender, msg.text, msg.voiceText, msg.timeStr, msg.mode);
    }
  } else {
    const welcome = document.createElement('div');
    welcome.className = 'message bot-message';
    welcome.innerHTML = '<strong>AI Assistant</strong>: Добро пожаловать! Задайте любой вопрос в поле ввода.';
    chatWindow.appendChild(welcome);
  }

  chatWindow.scrollTop = chatWindow.scrollHeight;
  updateCurrentSessionHeader();
}

function initChatTab() {
  loadSessions();
  renderSessionsList();
  renderActiveSessionMessages();

  // Bind Sidebar Toggle
  const sidebar = document.getElementById('chat-sidebar');
  const sidebarToggleBtn = document.getElementById('chat-sidebar-toggle-btn');
  if (sidebar && sidebarToggleBtn) {
    const isCollapsed = localStorage.getItem(STORAGE_KEY_SIDEBAR_COLLAPSED) === 'true';
    if (isCollapsed) {
      sidebar.classList.add('collapsed');
      sidebar.style.display = 'none';
    }

    sidebarToggleBtn.addEventListener('click', () => {
      const isCurrentlyCollapsed = sidebar.classList.toggle('collapsed');
      sidebar.style.display = isCurrentlyCollapsed ? 'none' : 'flex';
      localStorage.setItem(STORAGE_KEY_SIDEBAR_COLLAPSED, isCurrentlyCollapsed);
    });
  }

  // Bind New Session Button
  const newSessionBtn = document.getElementById('chat-new-session-btn');
  if (newSessionBtn) {
    newSessionBtn.addEventListener('click', () => {
      createNewSession('Новый чат', true);
      const msgInput = document.getElementById('message-input');
      if (msgInput) msgInput.focus();
    });
  }

  // Bind Clear Current / Clear All buttons
  const clearBtn = document.getElementById('chat-clear-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (confirm('Очистить сообщения текущего диалога?')) {
        clearCurrentSession();
      }
    });
  }

  const clearAllBtn = document.getElementById('chat-clear-all-sessions-btn');
  if (clearAllBtn) {
    clearAllBtn.addEventListener('click', () => {
      clearAllSessions();
    });
  }

  const renameCurrentBtn = document.getElementById('chat-rename-current-btn');
  if (renameCurrentBtn) {
    renameCurrentBtn.addEventListener('click', () => {
      if (activeSessionId) {
        renameSession(activeSessionId);
      }
    });
  }

  // Bind Input and Controls
  const sendBtn = document.getElementById('send-button');
  const msgInput = document.getElementById('message-input');
  const ragToggle = document.getElementById('chat-rag-toggle');
  const topKInput = document.getElementById('chat-top-k');
  const minScoreInput = document.getElementById('chat-min-score');

  const updateRagInputsState = (enabled) => {
    if (topKInput) {
      topKInput.disabled = !enabled;
      topKInput.style.opacity = enabled ? '1' : '0.5';
    }
    if (minScoreInput) {
      minScoreInput.disabled = !enabled;
      minScoreInput.style.opacity = enabled ? '1' : '0.5';
    }
  };

  if (ragToggle) {
    const savedRagPref = localStorage.getItem('chat_rag_enabled');
    if (savedRagPref !== null) {
      ragToggle.checked = savedRagPref === 'true';
      updateRagInputsState(ragToggle.checked);
    }
    fetch('/auth/settings')
      .then((res) => (res.ok ? res.json() : null))
      .then((settings) => {
        if (settings && typeof settings.rag_enabled !== 'undefined') {
          const isEnabled = settings.rag_enabled !== 0;
          ragToggle.checked = isEnabled;
          localStorage.setItem('chat_rag_enabled', isEnabled);
          updateRagInputsState(isEnabled);
        }
      })
      .catch(() => {});

    ragToggle.addEventListener('change', async (e) => {
      const isEnabled = e.target.checked;
      localStorage.setItem('chat_rag_enabled', isEnabled);
      updateRagInputsState(isEnabled);
      try {
        await fetch('/auth/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rag_enabled: isEnabled ? 1 : 0 })
        });
      } catch (err) {
        console.error('Error saving RAG setting:', err);
      }
    });
  }

  const modeSelect = document.getElementById('chat-output-mode');
  if (modeSelect) {
    const savedMode = localStorage.getItem('chat_output_mode');
    if (savedMode) {
      modeSelect.value = savedMode;
    }
    modeSelect.addEventListener('change', (e) => {
      localStorage.setItem('chat_output_mode', e.target.value);
      if (e.target.value === 'text_only' && window.chatService?.stop) {
        window.chatService.stop();
      }
    });
  }

  if (sendBtn) {
    sendBtn.addEventListener('click', sendMessage);
  }
  if (msgInput) {
    msgInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        sendMessage();
      }
    });
  }

  // Check for pending external chat payload (from Chrome extension or URL parameters)
  try {
    const pending = sessionStorage.getItem('pending_breadboard_chat');
    if (pending) {
      const payload = JSON.parse(pending);
      sessionStorage.removeItem('pending_breadboard_chat');
      setTimeout(() => handleExternalChatPrompt(payload), 300);
    } else {
      const urlParams = new URLSearchParams(window.location.search);
      const promptParam = urlParams.get('prompt') || urlParams.get('message');
      if (promptParam) {
        setTimeout(() => {
          handleExternalChatPrompt({
            prompt: promptParam,
            autoSend: urlParams.get('autosend') !== 'false'
          });
        }, 300);
      }
    }
  } catch (e) {
    console.error('Error checking pending chat payload:', e);
  }
}

function handleExternalChatPrompt(payload) {
  if (!payload || !payload.prompt) return;

  const chatTabBtn = document.querySelector('[data-bs-target="#tab-chat"]');
  if (chatTabBtn && window.bootstrap?.Tab) {
    bootstrap.Tab.getOrCreateInstance(chatTabBtn).show();
  }

  const msgInput = document.getElementById('message-input');
  if (msgInput) {
    msgInput.value = payload.prompt;
    if (payload.autoSend !== false) {
      setTimeout(() => {
        sendMessage();
      }, 150);
    }
  }
}

if (typeof window !== 'undefined') {
  window.initChatTab = initChatTab;
  window.handleExternalChatPrompt = handleExternalChatPrompt;
  window.clearChatHistory = clearCurrentSession;
  window.createNewSession = createNewSession;
  window.switchSession = switchSession;
  window.renameSession = renameSession;
  window.deleteSession = deleteSession;

  if (typeof chrome !== 'undefined' && chrome.runtime?.onMessage) {
    chrome.runtime.onMessage.addListener((msg) => {
      if (msg && msg.action === 'breadboard_external_chat_prompt') {
        handleExternalChatPrompt(msg);
      }
    });
  }
}

function parseContentToHtml(text) {
  if (!text) return '';

  let cleaned = text.trim();
  const codeBlockRegex = /^```(?:html|xml)?\s*([\s\S]*?)\s*```$/i;
  const match = cleaned.match(codeBlockRegex);
  if (match) {
    cleaned = match[1];
  }

  if (window.marked && typeof window.marked.parse === 'function') {
    return window.marked.parse(cleaned);
  }

  return cleaned
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

function addMessageToDom(sender, text, voiceText = null, timeStr = null, outputMode = null) {
  const win = document.getElementById('chat-window');
  if (!win) return null;

  const el = document.createElement('div');
  el.className = 'message ' + (sender === 'user' ? 'user-message' : 'bot-message');

  const displayText = parseContentToHtml(text);
  const formattedTime = timeStr || new Date().toLocaleTimeString();

  if (sender === 'user') {
    el.innerHTML = `<strong>Вы</strong> (${formattedTime}): <div class="message-content">${displayText}</div>`;
  } else {
    const modeBadge = outputMode === 'voice_only' ? '<span class="badge bg-secondary-subtle text-secondary me-1"><i class="bi bi-volume-up"></i> Голос</span>' : '';
    el.innerHTML = `
      <div class="d-flex align-items-center justify-content-between mb-1">
        <div><strong>AI Assistant</strong> ${modeBadge}<span class="text-muted">(${formattedTime})</span></div>
        <button class="btn btn-sm btn-outline-secondary py-0 px-2 btn-speak-message" title="Озвучить ответ" type="button">
          <i class="bi bi-volume-up"></i>
        </button>
      </div>
      <div class="message-content">${displayText || (voiceText ? `<em><i class="bi bi-soundwave me-1"></i>${parseContentToHtml(voiceText)}</em>` : '')}</div>
    `;
    const speakBtn = el.querySelector('.btn-speak-message');
    if (speakBtn) {
      speakBtn.addEventListener('click', () => {
        if (window.chatService?.speak) {
          window.chatService.speak(voiceText || text);
        }
      });
    }
  }

  win.appendChild(el);
  win.scrollTop = win.scrollHeight;
  return el;
}

function setStatus(statusText, isVisible = true) {
  const indicator = document.getElementById('chat-status-indicator');
  const textEl = document.getElementById('chat-status-text');
  if (!indicator || !textEl) return;

  if (isVisible) {
    textEl.textContent = statusText || 'Обработка запроса...';
    indicator.classList.remove('d-none');
  } else {
    indicator.classList.add('d-none');
  }
}

async function sendMessage() {
  const input = document.getElementById('message-input');
  const btn = document.getElementById('send-button');
  const topKInput = document.getElementById('chat-top-k');
  const minScoreInput = document.getElementById('chat-min-score');
  const modeSelect = document.getElementById('chat-output-mode');
  const ragToggle = document.getElementById('chat-rag-toggle');

  if (!input || !btn) return;

  if (!window.activeModelName) {
    input.disabled = true;
    btn.disabled = true;
    input.placeholder = 'Ни одна модель не выбрана. Выберите модель во вкладке «Модели и API».';
    input.classList.add('is-invalid');
    return;
  }

  const msg = input.value.trim();
  if (!msg) return;

  const session = getActiveSession();
  if (!session) return;

  const topK = topKInput ? parseInt(topKInput.value, 10) || 3 : 3;
  const minScore = minScoreInput ? parseFloat(minScoreInput.value) || 0.45 : 0.45;
  const outputMode = modeSelect ? modeSelect.value : 'text_and_voice';
  const shouldSpeak = outputMode === 'voice_only' || outputMode === 'text_and_voice';
  const isRagEnabled = ragToggle ? ragToggle.checked : true;

  input.value = '';
  input.disabled = true;
  btn.disabled = true;

  setStatus('Отправка запроса...', true);
  const userTimeStr = new Date().toLocaleTimeString();

  // Clear welcome placeholder if this is the first message
  const chatWin = document.getElementById('chat-window');
  if (chatWin && session.messages.length === 0) {
    chatWin.innerHTML = '';
  }

  addMessageToDom('user', msg, null, userTimeStr);
  session.messages.push({ sender: 'user', text: msg, timeStr: userTimeStr });

  // Auto-name the session based on the first query if not customized
  if ((!session.title || session.title === 'Новый чат' || session.title === 'Предыдущий диалог') && !session.isCustomTitle) {
    session.title = generateSessionTitle(msg);
    renderSessionsList();
  }

  saveSessions();

  const win = document.getElementById('chat-window');
  const botMessageEl = document.createElement('div');
  botMessageEl.className = 'message bot-message';
  const timeStr = new Date().toLocaleTimeString();
  const modeBadge = outputMode === 'voice_only' ? '<span class="badge bg-secondary-subtle text-secondary me-1"><i class="bi bi-volume-up"></i> Голос</span>' : '';
  botMessageEl.innerHTML = `
    <div class="d-flex align-items-center justify-content-between mb-1">
      <div><strong>AI Assistant</strong> ${modeBadge}<span class="text-muted">(${timeStr})</span></div>
      <button class="btn btn-sm btn-outline-secondary py-0 px-2 btn-speak-message d-none" title="Озвучить ответ" type="button">
        <i class="bi bi-volume-up"></i>
      </button>
    </div>
    <div class="bot-text"><span class="text-muted">⏳ Ожидание ответа...</span></div>
  `;
  if (win) {
    win.appendChild(botMessageEl);
    win.scrollTop = win.scrollHeight;
  }
  const textDiv = botMessageEl.querySelector('.bot-text');
  const speakBtn = botMessageEl.querySelector('.btn-speak-message');

  let fullReply = '';
  let started = false;

  try {
    const generationConfig = {
      top_k: topK,
      min_score: minScore,
      threshold: minScore,
      rag_enabled: isRagEnabled,
      output_mode: outputMode,
      tts_enabled: shouldSpeak,
      model: window.activeModelName || undefined,
      search_engine: window.activeSearchEngine || undefined
    };

    const replyObj = await window.chatService.sendChatMessage(
      msg,
      (chunk, status) => {
        if (status) {
          setStatus(status, true);
        }
        if (chunk) {
          if (!started) {
            if (textDiv) textDiv.textContent = '';
            started = true;
          }
          fullReply += chunk;
          if (textDiv) {
            textDiv.innerHTML = parseContentToHtml(fullReply);
          }
        }
        if (win) win.scrollTop = win.scrollHeight;
      },
      session.chatHistory || [],
      generationConfig
    );

    const finalReply = replyObj.text || fullReply;
    if (textDiv) {
      if (outputMode === 'voice_only' && !finalReply.trim() && replyObj.voice) {
        textDiv.innerHTML = `<em><i class="bi bi-soundwave me-1"></i>${parseContentToHtml(replyObj.voice)}</em>`;
      } else {
        textDiv.innerHTML = parseContentToHtml(finalReply);
      }
    }

    if (speakBtn) {
      speakBtn.classList.remove('d-none');
      speakBtn.addEventListener('click', () => {
        if (window.chatService?.speak) {
          window.chatService.speak(replyObj || finalReply);
        }
      });
    }

    // Auto-speak response if mode is voice_only or text_and_voice
    if (shouldSpeak && window.chatService?.speak) {
      window.chatService.speak(replyObj || finalReply);
    }

    if (!session.chatHistory) session.chatHistory = [];
    session.chatHistory.push({ role: 'user', parts: [msg] });
    session.chatHistory.push({ role: 'model', parts: [finalReply || replyObj.voice || ''] });

    session.messages.push({
      sender: 'bot',
      text: finalReply,
      voiceText: replyObj.voice || null,
      timeStr: timeStr,
      mode: outputMode
    });
    session.updatedAt = Date.now();
    saveSessions();

    setStatus('', false);
  } catch (err) {
    const errText = err instanceof Error ? err.message : typeof err === 'object' && err !== null ? JSON.stringify(err) : String(err);
    if (textDiv) {
      textDiv.innerHTML = `<span style="color: #ff7070;">Ошибка: ${errText}</span>`;
    }
    setStatus('Ошибка исполнения', true);
    setTimeout(() => setStatus('', false), 4000);
  } finally {
    if (window.activeModelName) {
      input.disabled = false;
      btn.disabled = false;
      input.placeholder = 'Введите сообщение...';
      input.classList.remove('is-invalid');
      input.focus();
    } else {
      input.disabled = true;
      btn.disabled = true;
      input.placeholder = 'Ни одна модель не выбрана. Выберите модель во вкладке «Модели и API».';
      input.classList.add('is-invalid');
    }
    if (win) win.scrollTop = win.scrollHeight;
  }
}

