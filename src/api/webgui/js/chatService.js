/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Chatservice Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля chatService.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/js/chatService.js?v=20261001_v1" type="module"></script>
 *
 * File: chatService.js
 * Project: ai-breadboard
 * Package: src/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

// Shared Chat Service Module
// Exposes window.chatService to unify API calling and message/error formatting.

class AudioQueuePlayer {
  constructor(chunks, userSettings) {
    this.chunks = chunks;
    this.userSettings = userSettings;
    this.currentIndex = 0;
    this.isPlaying = false;
    this.audioElements = new Map(); // index -> Audio
    this.activeAudio = null;
    
    // Prefetch first few chunks
    this._prefetch(0);
    this._prefetch(1);
    this._prefetch(2);
  }

  _prefetch(index) {
    if (index >= this.chunks.length || this.audioElements.has(index)) return;
    
    const text = this.chunks[index];
    const queryParams = new URLSearchParams({
      text: text,
      system: this.userSettings.tts_system,
      voice: this.userSettings.tts_voice
    });
    const audioUrl = `/api/tts/synthesize?${queryParams.toString()}`;
    const audio = new Audio(audioUrl);
    audio.load();
    this.audioElements.set(index, audio);
  }

  async play() {
    this.isPlaying = true;
    while (this.currentIndex < this.chunks.length && this.isPlaying) {
      // Prefetch upcoming chunks
      this._prefetch(this.currentIndex);
      this._prefetch(this.currentIndex + 1);
      this._prefetch(this.currentIndex + 2);
      this._prefetch(this.currentIndex + 3);

      const audio = this.audioElements.get(this.currentIndex);
      if (!audio) {
        this.currentIndex++;
        continue;
      }

      this.activeAudio = audio;
      window.chatServiceAudio = audio; // for global pause/stop integration
      
      const playPromise = new Promise((resolve) => {
        audio.onended = () => resolve();
        audio.onerror = (e) => {
          console.error(`Audio error for chunk ${this.currentIndex}:`, e);
          this.stop(); // Останавливаем всю очередь при ошибке загрузки
          resolve();
        };
      });

      try {
        await audio.play();
        await playPromise;
      } catch (err) {
        console.error("Audio playback interrupted or failed:", err);
      }
      
      this.currentIndex++;
    }
    this.isPlaying = false;
  }

  stop() {
    this.isPlaying = false;
    if (this.activeAudio) {
      try {
        this.activeAudio.pause();
        this.activeAudio.src = "";
      } catch (e) {}
    }
    this.audioElements.clear();
  }
}

window.chatService = {
  /**
   * Stops any currently playing audio or speech synthesis.
   */
  stop() {
    if (window.chatServiceQueue) {
      try {
        window.chatServiceQueue.stop();
        window.chatServiceQueue = null;
      } catch (e) {
        console.error("Error stopping chatServiceQueue:", e);
      }
    }
    if (window.chatServiceAudio) {
      try {
        window.chatServiceAudio.pause();
        window.chatServiceAudio.src = "";
        window.chatServiceAudio = null;
      } catch (e) {
        console.error("Error stopping chatServiceAudio:", e);
      }
    }
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {
        console.error("Error cancelling speechSynthesis:", e);
      }
    }
  },
  _abortController: null,

  /**
   * Sends a chat message to the /api/chat backend.
   * Resolves to the text reply or throws the parsed error object/string.
   * 
   * @param {string} message 
   * @returns {Promise<any>}
   */
  async sendChatMessage(message, onChunk, history = [], generationConfig = {}) {
    // Останавливаем любую активную озвучку перед отправкой нового сообщения
    this.stop();
    
    // Прерываем предыдущий запрос, если он еще выполняется
    if (this._abortController) {
      try {
        this._abortController.abort();
      } catch (e) {}
    }
    this._abortController = new AbortController();

    let fullText = '';
    let voiceText = '';
    
    const effectiveGenConfig = { ...generationConfig };
    if (!effectiveGenConfig.model && window.activeModelName) {
      effectiveGenConfig.model = window.activeModelName;
    }
    if (!effectiveGenConfig.search_engine && window.activeSearchEngine) {
      effectiveGenConfig.search_engine = window.activeSearchEngine;
    }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/jsoni18n.t('auto__body_json_stringify_message_history_generation_config_effectivegenconfig_signal_this_abortcontroller_signal_if_response_ok_let_data_try_data_await_response_json_catch_e_throw_new_error_http_response_status_response_statustext_throw_data_detail_data_const_reader_response_body_getreader_const_decoder_new_textdecoder__5884f7')utf-8');
      let buffer = '';
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();
        
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          if (trimmed.startsWith('data: ')) {
            try {
              const data = JSON.parse(trimmed.substring(6));
              if (data.error) {
                throw new Error(data.error);
              }
              if (data.text || data.status || data.voice || data.prompt_dump) {
                if (data.text) fullText += data.text;
                if (data.voice) {
                  voiceText += data.voice;
                }
                if (onChunk) {
                  onChunk(data.text || '', data.status || '', data.voice || '', data.prompt_dump || '');
                }
              }
            } catch (e) {
              console.error('Parsing SSE error:', e, trimmed);
              throw e;
            }
          }
        }
      }
      
      if (buffer && buffer.trim().startsWith('data: ')) {
        const data = JSON.parse(buffer.trim().substring(6));
        if (data.error) throw new Error(data.error);
        if (data.text || data.status || data.voice) {
          if (data.text) fullText += data.text;
          if (data.voice) voiceText += data.voice;
          if (onChunk) onChunk(data.text || '', data.status || '', data.voice || '');
        }
      }
    } catch (e) {
      if (e.name === 'AbortErrori18n.t('auto__promise_sendchatmessage_catch_finally_ui_return_new_promise_throw_e_let_followupquery_null_const_nextqueryregex_next_query_next_query_i_const_match_fulltext_match_nextqueryregex_if_match_followupquery_match_1_trim_fulltext_fulltext_replace_match_0__c1d409')');
    }

    return { text: fullText, voice: voiceText, followUp: followUpQuery };
  },


  /**
   * Formats chat messages. 
   * Converts objects into stringified JSON inside pre tags for rich rendering.
   * 
   * @param {any} text 
   * @returns {string|HTMLElement}
   */
  formatMessage(text) {
    if (typeof text === 'object' && text !== null) {
      // Если это просто объект с ответом { text, voice }, отображаем только текст
      if (text.text !== undefined) {
        return text.text;
      }
      return `<pre style="white-space: pre-wrap; background: #2b2b2b; color: #ff7070; padding: 10px; border-radius: 5px; margin: 5px 0; font-family: monospace;">${JSON.stringify(text, null, 2)}</pre>`;
    }
    return text;
  },

  /**
   * Reads the given text aloud using the browser SpeechSynthesis API or backend TTS.
   * 
   * @param {string|object} text 
   */
  async speak(text) {
    if (!text) return;
    
    // Останавливаем все предыдущие аудиопотоки
    this.stop();

    let cleanText = '';
    if (typeof text === 'objecti18n.t('auto__text_null_if_text_voice_text_text_text_voice_sendchatmessage_cleantext_text_voice_text_text_else_const_title_text_title_ru_text_title_const_rec_text_why_watch_text_plot__7f1edb')i18n.t('auto__cleantext_title_rec_else_const_trimmed_text_trim_if_trimmed_startswith__1d5693'){') && trimmed.endsWith('}')) {
        try {
          const card = JSON.parse(trimmed);
          const title = card.title_ru || card.title;
          const rec = card.why_watch || card.plot || 'i18n.t('auto__cleantext_title_rec_catch_e_cleantext_trimmed_else_strip_code_blocks_cleantext_trimmed_replace_s_s_g__36ece1')');
        // Strip HTML tags
        cleanText = cleanText.replace(/<[^>]*>/g, '');
        // Strip Markdown formatting
        cleanText = cleanText.replace(/[*_`#]/g, '');
      }
    }
    
    if (!cleanText.trim()) return;

    let userSettings = null;
    try {
      const response = await fetch('/auth/settings');
      if (response.ok) {
        userSettings = await response.json();
        if (userSettings.tts_enabled === 1 && userSettings.tts_system && userSettings.tts_system !== 'browser') {
          // Разбиваем текст по абзацам и предложениям на более мелкие чанки (~150-200 символов)
          const paragraphs = cleanText
            .split(/\n+/)
            .map(p => p.trim())
            .filter(p => p.length > 0);
          
          let chunks = [];
          for (const para of paragraphs) {
            const sentences = para.match(/[^.!?]+[.!?]*/g) || [para];
            let currentChunk = "";
            for (const sentence of sentences) {
              const trimmedSentence = sentence.trim();
              if (!trimmedSentence) continue;
              if ((currentChunk + " " + trimmedSentence).length > 200) {
                chunks.push(currentChunk.trim());
                currentChunk = trimmedSentence;
              } else {
                currentChunk = (currentChunk + " " + trimmedSentence).trim();
              }
            }
            if (currentChunk) {
              chunks.push(currentChunk.trim());
            }
          }
          chunks = chunks.filter(c => c.length > 0);

          if (chunks.length > 0) {
            window.chatServiceQueue = new AudioQueuePlayer(chunks, userSettings);
            await window.chatServiceQueue.play();
          }
          return;
        }
      }
    } catch (e) {
      console.error('Failed to speak using backend TTS, falling back to browser:', e);
    }

    if ('speechSynthesis' in window) {
      window.currentUtterance = new SpeechSynthesisUtterance(cleanText);
      
      // Dynamic language detection for Web Speech API fallback
      const hasHebrew = /[\u0590-\u05FF]/.test(cleanText);
      const hasCyrillic = /[\u0400-\u04FF]/.test(cleanText);
      window.currentUtterance.lang = hasHebrew ? 'he-IL' : (hasCyrillic ? 'ru-RU' : 'en-USi18n.t('auto__if_usersettings_usersettings_tts_voice_const_voices_window_speechsynthesis_getvoices_const_selectedvoice_voices_find_v_v_name_usersettings_tts_voice_if_selectedvoice_window_currentutterance_voice_selectedvoice_if_selectedvoice_lang_window_currentutterance_lang_selectedvoice_lang_window_speechsynthesis_speak_window_currentutterance_function_formatsearchengine_engine_if_engine_return_2113dc')';
  let eng = engine;
  let mdl = '';
  if (engine.includes(':') && !engine.startsWith('ollama:') && !engine.startsWith('foundry:')) {
    const parts = engine.split(':');
    eng = parts[0];
    mdl = parts.slice(1).join(':');
  }
  const map = {
    'gemini_cli': '💻 gemini_cli',
    'gemini': '♊ gemini',
    'agy': '🚀 agy',
    'langchain': '🦜 langchain',
    'playwright': '🎭 playwright'
  };
  const iconAndName = map[eng] || `🔍 ${eng}`;
  if (mdl && !mdl.startsWith('chromium')) {
    return `${iconAndName} (${mdl})`;
  }
  return iconAndName;
}

window.formatSearchEngine = formatSearchEngine;

window.updateChatBadges = function(modelName, searchEngine) {
  if (modelName !== undefined && modelName !== null) {
    window.activeModelName = modelName;
  }
  if (searchEngine !== undefined && searchEngine !== null) {
    window.activeSearchEngine = searchEngine;
  }

  const curModel = window.activeModelName || '';
  const curSearch = window.activeSearchEngine || '';

  const modelBadges = document.querySelectorAll('#chat-model-badge, #chat-popup-model-badge');
  modelBadges.forEach(badge => {
    if (curModel) {
      badge.innerHTML = `<i class="bi bi-cpu-fill text-info me-1"></i> <span>${curModel}</span>`;
      badge.title = `Активная модель ИИ: ${curModel} (клик для перехода к настройкам моделей)`;
      badge.style.display = 'inline-flex';
    } else {
      badge.innerHTML = `<i class="bi bi-cpu text-muted me-1"></i> <span class="text-secondary">По умолчанию (сервер)</span>`;
      badge.title = `Используется модель по умолчанию сервера (клик для выбора модели)`;
      badge.style.display = 'inline-flex';
    }

    if (!badge._hasClickBound) {
      badge._hasClickBound = true;
      badge.style.cursor = 'pointer';
      badge.onclick = () => {
        // Try activating models tab if present
        const modelsTabBtn = document.querySelector('button[data-bs-target="#tab-models"]');
        if (modelsTabBtn) {
          const tab = new bootstrap.Tab(modelsTabBtn);
          tab.show();
        } else {
          // Open settings modal
          const modalEl = document.getElementById('userSettingsModal');
          if (modalEl && window.bootstrap) {
            const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
            modal.show();
          }
        }
      };
    }
  });

  const searchBadges = document.querySelectorAll('#chat-search-badge, #chat-popup-search-badge');
  searchBadges.forEach(badge => {
    if (curSearch) {
      badge.innerHTML = `<i class="bi bi-globe2 text-warning me-1"></i> <span>${formatSearchEngine(curSearch)}</span>`;
      badge.title = `Провайдер веб-поиска: ${curSearch}`;
      badge.style.display = 'inline-flex';
    } else {
      badge.style.display = 'none';
    }
  });

  const savedCardBadge = document.getElementById('saved-default-model-badge');
  if (savedCardBadge) {
    if (curModel) {
      savedCardBadge.textContent = curModel;
      savedCardBadge.className = 'badge bg-success font-monospace px-2 py-1i18n.t('auto__savedcardbadge_title_curmodel_else_savedcardbadge_textcontent__2ea27d')Не задана (системный fallback)';
      savedCardBadge.className = 'badge bg-secondary font-monospace px-2 py-1';
      savedCardBadge.title = i18n.t('auto___fd8ee7');
    }
  }

  // Update chat message input state based on model selection
  const msgInputs = document.querySelectorAll('#message-input, #chat-popup-input');
  const sendButtons = document.querySelectorAll('#send-button, #chat-popup-send-btn');
  
  msgInputs.forEach(input => {
    if (!curModel) {
      input.disabled = true;
      input.placeholder = i18n.t('auto__api__da6213');
      input.classList.add('is-invalid');
    } else {
      input.disabled = false;
      input.placeholder = i18n.t('auto___ed1075');
      input.classList.remove('is-invalidi18n.t('auto__sendbuttons_foreach_btn_btn_disabled_curmodel_document_addeventlistener__bc2e69')DOMContentLoaded', async () => {
  try {
    let modelName = '';
    let searchEngine = '';
    const response = await fetch('/auth/settings');
    if (response.ok) {
      const settings = await response.json();
      modelName = settings.model || '';
      searchEngine = settings.search_engine || '';
    }
    if (!modelName) {
      try {
        const activeResp = await fetch('/api/chat/active-modeli18n.t('auto__if_activeresp_ok_const_activedata_await_activeresp_json_if_activedata_activedata_model_modelname_activedata_display_activedata_provider_activedata_provider_activedata_model_activedata_model_catch_window_activemodelname_modelname_window_activesearchengine_searchengine_window_updatechatbadges_modelname_searchengine_dom_settimeout_window_updatechatbadges_500_settimeout_window_updatechatbadges_1500_catch_e_console_error__2cc750')Failed to load active model / search badge:', e);
  }
});
