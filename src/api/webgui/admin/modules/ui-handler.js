/**
 * UI Handler Module - Работа с модалями, уведомлениями и помощью
 */

let helpContent = {};

export function setupUIHandlers() {
  initHelpContent();
  setupModalHandlers();
}

function initHelpContent() {
  helpContent = {
    'overview': `<h4>🚀 Обзор проекта</h4><p>ai-breadboard — интегрированная среда для работы с AI, RAG и системным управлением.</p>`,
    'google_oauth': `<h4>🔑 Google OAuth и аккаунты</h4><p>Интеграция с Gmail, Drive, Sheets и Docs через OAuth 2.0 и Service Accounts.</p>`,
    'ai_models': `<h4>🤖 ИИ Провайдеры и Модели</h4><p>Облачные (Gemini, OpenAI, Groq) и локальные (Ollama, Foundry, DirectML) модели.</p>`,
    'gdrive_sync': `<h4>☁️ Google Drive Sync</h4><p>Автоматическая синхронизация баз данных и файлов с Google Drive.</p>`,
    'rag_knowledge': `<h4>📚 База знаний и RAG</h4><p>Загрузка и поиск по вашим документам (PDF, Word, TXT, CSV, JSON).</p>`,
    'rag': `<h4>🧠 RAG-индекс (Векторный поиск)</h4>
<p><strong>1. База RAG:</strong> Индексирует системные базы знаний, системные инструкции и документы.</p>
<p><strong>2. Загрузка документов:</strong> Позволяет загрузить внешние <code>.json</code>, <code>.txt</code>, <code>.md</code>, <code>.pdf</code> файлы или сканировать директории напрямую в RAG-индекс.</p>
<p><strong>3. Чат-RAG:</strong> Индексирует историю сохраненных диалогов и ответов ассистента.</p>`,
    'voice_tts': `<h4>🎙️ Голос и Озвучка</h4><p>Голосовой ввод (Whisper/WebSpeech) и синтез речи (Edge TTS).</p>`,
    'plugins_skills': `<h4>🔌 Плагины, Навыки и MCP</h4><p>Telegram-бот, IFTTT, распознавание счетов и расширение через MCP.</p>`,
    'storage_disks': `<h4>💾 Диски и Хранилище</h4><p>Сканирование накопителей, проверка целостности и консолидация дублей.</p>`,
    'troubleshooting': `<h4>❓ Решение проблем (FAQ)</h4><p>Ответы на частые вопросы и устранение ошибок подключения.</p>`
  };
  
  window.HELP_CONTENT = helpContent;
}

function setupModalHandlers() {
  // Help modal
  const helpBtn = document.getElementById('help-btn');
  if (helpBtn) {
    helpBtn.addEventListener('click', () => {
      showHelpModal('overview');
    });
  }

  // Chat logic modal
  const chatLogicBtn = document.getElementById('chat-logic-btn');
  if (chatLogicBtn) {
    chatLogicBtn.addEventListener('click', () => {
      showChatLogicModal();
    });
  }
}

export function showHelpModal(key) {
  const content = helpContent[key] || '<p>Информация не найдена</p>';
  const contentDiv = document.getElementById('help-modal-content');
  if (contentDiv) {
    contentDiv.innerHTML = content;
  }
  
  const modal = document.getElementById('help-modal');
  if (modal) {
    const m = new bootstrap.Modal(modal);
    m.show();
  }
}

export function showChatLogicModal() {
  const modalEl = document.getElementById('chat-logic-modal');
  if (modalEl) {
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }
}

export function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
  notification.style.zIndex = '9999';
  notification.style.maxWidth = '400px';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

export { initHelpContent, setupModalHandlers };
