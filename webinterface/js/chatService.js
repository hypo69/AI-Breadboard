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
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history, generation_config: generationConfig }),
        signal: this._abortController.signal
      });
      
      if (!response.ok) {
        let data;
        try {
          data = await response.json();
        } catch (e) {
          throw new Error(`Ошибка сервера (HTTP ${response.status}): ${response.statusText}`);
        }
        throw (data.detail || data);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
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
      if (e.name === 'AbortError') {
        // Возвращаем Promise, который никогда не зарезолвится.
        // Это остановит старый вызов sendChatMessage() на месте, не вызывая catch/finally в UI-скриптах,
        // так как они уже перекрыты новым запросом.
        return new Promise(() => {});
      }
      throw e;
    }
    
    let followUpQuery = null;
    const nextQueryRegex = /\[NEXT_QUERY\](.*?)\[\/NEXT_QUERY\]/i;
    const match = fullText.match(nextQueryRegex);
    if (match) {
      followUpQuery = match[1].trim();
      fullText = fullText.replace(match[0], '');
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
    if (typeof text === 'object' && text !== null) {
      if (text.voice || text.text) {
        // Если это объект { text, voice } из sendChatMessage
        cleanText = text.voice || text.text;
      } else {
        // Если это карточка фильма
        const title = text.title_ru || text.title;
        const rec = text.why_watch || text.plot || '';
        cleanText = `Найдено: ${title}. ${rec}`;
      }
    } else {
      const trimmed = text.trim();
      if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
        try {
          const card = JSON.parse(trimmed);
          const title = card.title_ru || card.title;
          const rec = card.why_watch || card.plot || '';
          cleanText = `Найдено: ${title}. ${rec}`;
        } catch (e) {
          cleanText = trimmed;
        }
      } else {
        // Strip code blocks
        cleanText = trimmed.replace(/```[\s\S]*?```/g, '');
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
      window.currentUtterance.lang = 'ru-RU';
      
      if (userSettings && userSettings.tts_voice) {
        const voices = window.speechSynthesis.getVoices();
        const selectedVoice = voices.find(v => v.name === userSettings.tts_voice);
        if (selectedVoice) {
          window.currentUtterance.voice = selectedVoice;
        }
      }
      
      window.speechSynthesis.speak(window.currentUtterance);
    }
  }
};

// Форматирование отображаемого названия поискового движка
function formatSearchEngine(engine) {
  if (!engine) return '';
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

  if (curModel) {
    const modelBadges = document.querySelectorAll('#chat-model-badge, #chat-popup-model-badge');
    modelBadges.forEach(badge => {
      badge.textContent = curModel;
      badge.title = `Выбранная модель ИИ: ${curModel}`;
      badge.style.display = 'inline-block';
    });
  }

  if (curSearch) {
    const searchBadges = document.querySelectorAll('#chat-search-badge, #chat-popup-search-badge');
    searchBadges.forEach(badge => {
      badge.textContent = formatSearchEngine(curSearch);
      badge.title = `Провайдер веб-поиска: ${curSearch}`;
      badge.style.display = 'inline-block';
    });
  }
};

// Автоматически загружаем настройки и обновляем бейджи модели и поиска при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch('/auth/settings');
    if (response.ok) {
      const settings = await response.json();
      const modelName = settings.model || '';
      const searchEngine = settings.search_engine || '';
      window.activeModelName = modelName;
      window.activeSearchEngine = searchEngine;
      
      window.updateChatBadges(modelName, searchEngine);
      // На случай если DOM элементы добавились/отрендерились позже
      setTimeout(() => window.updateChatBadges(), 500);
      setTimeout(() => window.updateChatBadges(), 1500);
    }
  } catch (e) {
    console.error('Failed to load active model / search badge:', e);
  }
});
