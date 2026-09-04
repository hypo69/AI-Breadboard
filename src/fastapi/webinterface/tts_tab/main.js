// TTS Tab Configuration and Testing Logic
// Called via window.initTtsTab() when tab is loaded

'use strict';

function ttsFetch(url, options = {}) {
  return window.api
    ? window.api.fetch(url, options)
    : fetch(url, options).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      });
}

function ttsNotify(msg, type = 'info') {
  if (typeof showNotification === 'function') {
    showNotification(msg, type);
  } else {
    console.log(`[${type}] ${msg}`);
  }
}

// Available voices dictionary
const ADMIN_VOICE_MAP = {
  'browser': [], // Populated dynamically from window.speechSynthesis
  'gtts': [
    { value: 'ru', label: 'Русский (Google TTS)' }
  ],
  'edge-tts': [
    { value: 'ru-RU-DmitryNeural', label: 'Дмитрий (Microsoft Edge)' },
    { value: 'ru-RU-SvetlanaNeural', label: 'Светлана (Microsoft Edge)' }
  ],
  'silero': [
    { value: 'eugene', label: 'Евгений (Silero)' },
    { value: 'aidar', label: 'Айдар (Silero)' },
    { value: 'baya', label: 'Бая (Silero)' },
    { value: 'kseniya', label: 'Ксения (Silero)' },
    { value: 'xenia', label: 'Ксения v2 (Silero)' },
    { value: 'random', label: 'Рандомный (Silero)' }
  ]
};

function getFriendlyVoiceName(system, voice) {
  if (system === 'edge-tts') {
    if (voice === 'ru-RU-DmitryNeural') return 'Дмитрий (Microsoft Edge)';
    if (voice === 'ru-RU-SvetlanaNeural') return 'Светлана (Microsoft Edge)';
    return `Edge (${voice})`;
  }
  if (system === 'silero') {
    const names = {
      eugene: 'Евгений (Silero)',
      aidar: 'Айдар (Silero)',
      baya: 'Бая (Silero)',
      kseniya: 'Ксения (Silero)',
      xenia: 'Ксения v2 (Silero)',
      random: 'Рандомный (Silero)'
    };
    return names[voice] || `Silero (${voice})`;
  }
  if (system === 'gtts') {
    return 'Google TTS (Базовый)';
  }
  if (system === 'browser') {
    return `Браузерный (${voice || 'По умолчанию'})`;
  }
  return `${system} — ${voice}`;
}

async function initTtsTab() {
  const engineSelect = document.getElementById('admin-tts-engine');
  const voiceSelect = document.getElementById('admin-tts-voice');
  const voiceContainer = document.getElementById('admin-voice-select-container');
  const btnSpeak = document.getElementById('btn-admin-tts-speak');
  const btnSave = document.getElementById('btn-admin-tts-save');
  const ttsStatus = document.getElementById('admin-tts-status');
  const statusText = document.getElementById('admin-status-text');
  const playerContainer = document.getElementById('admin-tts-player-container');
  const audioPlayer = document.getElementById('admin-tts-audio-player');
  const activeVoiceContainer = document.getElementById('admin-active-voice-container');
  const activeVoiceName = document.getElementById('admin-active-voice-name');

  if (!engineSelect || !voiceSelect) {
    console.error('TTS Settings Tab DOM elements not found.');
    return;
  }

  function updateActiveBadge(system, voice) {
    if (system && voice) {
      activeVoiceName.textContent = getFriendlyVoiceName(system, voice);
      activeVoiceContainer.style.display = 'block';
    } else {
      activeVoiceContainer.style.display = 'none';
    }
  }

  // Populate voices based on selected engine
  function populateVoices() {
    const engine = engineSelect.value;
    const voices = ADMIN_VOICE_MAP[engine] || [];
    
    voiceSelect.innerHTML = '';
    
    if (voices.length === 0) {
      voiceContainer.style.display = 'none';
    } else {
      voiceContainer.style.display = 'block';
      voices.forEach(voice => {
        const opt = document.createElement('option');
        opt.value = voice.value;
        opt.textContent = voice.label;
        voiceSelect.appendChild(opt);
      });
    }
  }

  // Load browser speech synthesis voices if available
  function loadBrowserVoices() {
    if ('speechSynthesis' in window) {
      const voices = window.speechSynthesis.getVoices();
      ADMIN_VOICE_MAP['browser'] = voices
        .filter(v => v.lang.startsWith('ru'))
        .map(v => ({ value: v.name, label: `Браузер: ${v.name}` }));
      
      if (ADMIN_VOICE_MAP['browser'].length === 0) {
        ADMIN_VOICE_MAP['browser'].push({ value: 'default', label: 'Браузер по умолчанию' });
      }
      
      if (engineSelect.value === 'browser') {
        populateVoices();
      }
    }
  }

  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = loadBrowserVoices;
    loadBrowserVoices();
  }

  engineSelect.addEventListener('change', populateVoices);
  populateVoices(); // Initial run

  // Fetch current user settings
  try {
    const settings = await ttsFetch('/auth/settings');
    if (settings) {
      if (settings.tts_system) {
        engineSelect.value = settings.tts_system;
        populateVoices();
      }
      if (settings.tts_voice) {
        voiceSelect.value = settings.tts_voice;
      }
      updateActiveBadge(settings.tts_system, settings.tts_voice);
    }
  } catch (e) {
    console.error('Failed to load active TTS settings:', e);
  }

  // Speak button handler
  btnSpeak.addEventListener('click', async () => {
    const text = document.getElementById('admin-tts-text').value.trim();
    if (!text) {
      ttsNotify('Пожалуйста, введите текст для озвучки', 'warning');
      return;
    }

    const engine = engineSelect.value;
    const voice = voiceSelect.value;

    if (engine === 'browser') {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const cleanText = text.replace(/<[^>]*>/g, '').replace(/[*_`#]/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'ru-RU';
        
        const voices = window.speechSynthesis.getVoices();
        const selectedVoice = voices.find(v => v.name === voice);
        if (selectedVoice) {
          utterance.voice = selectedVoice;
        }
        
        ttsStatus.classList.remove('d-none');
        statusText.textContent = 'Воспроизведение браузером...';
        
        utterance.onend = () => ttsStatus.classList.add('d-none');
        utterance.onerror = () => ttsStatus.classList.add('d-none');
        
        window.speechSynthesis.speak(utterance);
        playerContainer.classList.add('d-none');
      } else {
        ttsNotify('Ваш браузер не поддерживает Web Speech API', 'danger');
      }
      return;
    }

    // Server-side synthesis
    ttsStatus.classList.remove('d-none');
    statusText.textContent = 'Синтез аудиофайла на сервере...';
    btnSpeak.disabled = true;
    playerContainer.classList.add('d-none');

    try {
      const queryParams = new URLSearchParams({
        text: text,
        system: engine,
        voice: voice
      });

      const audioUrl = `/api/tts/synthesize?${queryParams.toString()}`;
      
      audioPlayer.src = audioUrl;
      audioPlayer.load();

      audioPlayer.oncanplaythrough = () => {
        ttsStatus.classList.add('d-none');
        btnSpeak.disabled = false;
        playerContainer.classList.remove('d-none');
        audioPlayer.play().catch(err => console.log('Audio autoplay blocked or failed:', err));
      };

      audioPlayer.onerror = (err) => {
        console.error('Audio element error:', err);
        statusText.textContent = 'Ошибка загрузки аудиофайла';
        btnSpeak.disabled = false;
        setTimeout(() => ttsStatus.classList.add('d-none'), 3000);
      };

    } catch (err) {
      console.error(err);
      statusText.textContent = 'Ошибка сети';
      btnSpeak.disabled = false;
      setTimeout(() => ttsStatus.classList.add('d-none'), 3000);
    }
  });

  // Save Settings handler
  btnSave.addEventListener('click', async () => {
    const engine = engineSelect.value;
    const voice = voiceSelect.value;
    
    btnSave.disabled = true;
    const originalText = btnSave.innerHTML;
    btnSave.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Сохранение...';

    try {
      const payload = {
        tts_enabled: 1,
        tts_system: engine,
        tts_voice: voice
      };

      const response = await fetch('/auth/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        updateActiveBadge(engine, voice);
        ttsNotify('Настройки TTS успешно применены по умолчанию!', 'success');
      } else {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Ошибка сохранения настроек');
      }
    } catch (err) {
      console.error(err);
      ttsNotify('Не удалось сохранить настройки: ' + err.message, 'danger');
    } finally {
      btnSave.disabled = false;
      btnSave.innerHTML = originalText;
    }
  });
}

window.initTtsTab = initTtsTab;
