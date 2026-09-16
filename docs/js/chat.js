// Chat Widget for ai-breadboard Documentation
(function() {
  document.addEventListener('DOMContentLoaded', () => {
    // 1. Create and inject chat elements
    const chatContainer = document.createElement('div');
    chatContainer.id = 'doc-chat-widget';
    chatContainer.innerHTML = `
      <button class="chat-toggle-btn" id="chat-toggle-btn" title="Открыть чат Code Helper">💬</button>
      <div class="chat-popup" id="chat-popup">
        <div class="chat-popup-header">
          <span>💻 Code Helper (Docs Chat)</span>
          <div class="chat-window-controls">
            <button class="chat-window-btn maximize" id="chat-max-btn" title="Развернуть">▉▉</button>
            <button class="chat-window-btn minimize" id="chat-min-btn" title="Свернуть">_</button>
            <button class="chat-window-btn close" id="chat-close-btn" title="Закрыть">✕</button>
          </div>
        </div>
        <div class="chat-popup-messages" id="chat-popup-messages">
          <div class="chat-popup-msg bot">
            <strong>Code Helper</strong>: Привет! Я ассистент разработчика ai-breadboard. Задайте мне вопрос по коду или документации проекта.
          </div>
        </div>
        <div class="chat-popup-input-area">
          <input type="text" id="chat-popup-input" placeholder="Задайте вопрос по проекту...">
          <button id="chat-popup-send">Отправить</button>
        </div>
      </div>
    `;
    document.body.appendChild(chatContainer);

    // 2. Element References
    const toggleBtn = document.getElementById('chat-toggle-btn');
    const popup = document.getElementById('chat-popup');
    const closeBtn = document.getElementById('chat-close-btn');
    const maxBtn = document.getElementById('chat-max-btn');
    const minBtn = document.getElementById('chat-min-btn');
    const sendBtn = document.getElementById('chat-popup-send');
    const inputField = document.getElementById('chat-popup-input');
    const messagesContainer = document.getElementById('chat-popup-messages');

    let isMaximized = false;

    // 3. UI State Actions
    function setMaximizedState(max) {
      isMaximized = max;
      if (max) {
        popup.classList.add('maximized');
        maxBtn.textContent = '□';
      } else {
        popup.classList.remove('maximized');
        maxBtn.textContent = '▉▉';
      }
    }

    toggleBtn.addEventListener('click', () => {
      popup.classList.toggle('show');
      if (popup.classList.contains('show')) {
        inputField.focus();
        setMaximizedState(false);
      }
    });

    closeBtn.addEventListener('click', () => {
      popup.classList.remove('show');
    });

    maxBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      setMaximizedState(!isMaximized);
    });

    minBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      setMaximizedState(false);
    });

    // 4. Send Message logic
    async function sendMessage() {
      const msg = inputField.value.trim();
      if (!msg) return;

      addMessage('user', msg);
      inputField.value = '';
      sendBtn.disabled = true;
      sendBtn.textContent = '⏳';

      try {
        const response = await fetch('https://kino.davidka.net/api/chat/code-helper', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ message: msg })
        });

        if (!response.ok) {
          throw new Error(`Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        addMessage('bot', data.text || 'Нет ответа от ассистента.');
      } catch (err) {
        addMessage('bot', `Ошибка: ${err.message}`);
      } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Отправить';
        inputField.focus();
      }
    }

    function addMessage(sender, text) {
      const msgEl = document.createElement('div');
      msgEl.className = `chat-popup-msg ${sender}`;
      
      // Simple HTML escaping and formatting
      const formattedText = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');

      msgEl.innerHTML = `<strong>${sender === 'user' ? 'Вы' : 'Code Helper'}</strong>: ${formattedText}`;
      messagesContainer.appendChild(msgEl);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // 5. Input Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage();
    });
  });
})();
