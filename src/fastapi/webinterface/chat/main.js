// ── CHAT.JS ───────────────────────────────────────────────────────────────────

let chatHistory = [];

function initChatTab() {
  const chatWindow = document.getElementById('chat-window');
  if (chatWindow && chatWindow.children.length === 0) {
    const welcome = document.createElement('div');
    welcome.className = 'message bot-message';
    welcome.innerHTML = '<strong>AI Assistant</strong>: Добро пожаловать! Задайте любой вопрос в поле ввода.';
    chatWindow.appendChild(welcome);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  const sendBtn = document.getElementById('send-button');
  const msgInput = document.getElementById('message-input');

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

  // Listen for browser extension messages directly if present
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

function addMessage(sender, text) {
  const win = document.getElementById('chat-window');
  if (!win) return null;

  const el = document.createElement('div');
  el.className = 'message ' + (sender === 'user' ? 'user-message' : 'bot-message');

  const displayText = parseContentToHtml(text);
  const timeStr = new Date().toLocaleTimeString();
  el.innerHTML = `<strong>${sender === 'user' ? 'Вы' : 'AI Assistant'}</strong> (${timeStr}): <div class="message-content">${displayText}</div>`;
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

  if (!input || !btn) return;

  const msg = input.value.trim();
  if (!msg) return;

  const topK = topKInput ? (parseInt(topKInput.value, 10) || 3) : 3;
  const minScore = minScoreInput ? (parseFloat(minScoreInput.value) || 0.45) : 0.45;

  input.value = '';
  input.disabled = true;
  btn.disabled = true;

  setStatus('Отправка запроса...', true);
  addMessage('user', msg);

  const win = document.getElementById('chat-window');
  const botMessageEl = document.createElement('div');
  botMessageEl.className = 'message bot-message';
  const timeStr = new Date().toLocaleTimeString();
  botMessageEl.innerHTML = `<strong>AI Assistant</strong> (${timeStr}): <div class="bot-text"><span class="text-muted">⏳ Ожидание ответа...</span></div>`;
  if (win) {
    win.appendChild(botMessageEl);
    win.scrollTop = win.scrollHeight;
  }
  const textDiv = botMessageEl.querySelector('.bot-text');

  let fullReply = '';
  let started = false;

  try {
    const generationConfig = {
      top_k: topK,
      min_score: minScore,
      threshold: minScore
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
      chatHistory,
      generationConfig
    );

    const finalReply = replyObj.text || fullReply;
    if (textDiv) {
      textDiv.innerHTML = parseContentToHtml(finalReply);
    }

    chatHistory.push({ role: 'user', parts: [msg] });
    chatHistory.push({ role: 'model', parts: [finalReply] });

    setStatus('', false);
  } catch (err) {
    const errText = err instanceof Error ? err.message : (typeof err === 'object' && err !== null ? JSON.stringify(err) : String(err));
    if (textDiv) {
      textDiv.innerHTML = `<span style="color: #ff7070;">Ошибка: ${errText}</span>`;
    }
    setStatus('Ошибка исполнения', true);
    setTimeout(() => setStatus('', false), 4000);
  } finally {
    input.disabled = false;
    btn.disabled = false;
    input.focus();
    if (win) win.scrollTop = win.scrollHeight;
  }
}

