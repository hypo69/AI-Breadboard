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
    { value: 'ru', label: i18n.t('auto__google_tts__7a64a4') },
    { value: 'en', label: 'English (Google TTS)' },
    { value: 'he', label: 'עברית (Google TTS)' },
    { value: 'de', label: 'Deutsch (Google TTS)' },
    { value: 'fr', label: 'Français (Google TTS)' },
    { value: 'es', label: 'Español (Google TTS)' }
  ],
  'edge-tts': [
    { value: 'ru-RU-DmitryNeural', label: i18n.t('auto__ru__b17f23') },
    { value: 'ru-RU-SvetlanaNeural', label: i18n.t('auto__ru__561ddc') },
    { value: 'en-US-JennyNeural', label: 'Jenny (US - Female)' },
    { value: 'en-US-GuyNeural', label: 'Guy (US - Male)' },
    { value: 'en-US-AriaNeural', label: 'Aria (US - Female)' },
    { value: 'en-GB-SoniaNeural', label: 'Sonia (UK - Female)' },
    { value: 'en-GB-RyanNeural', label: 'Ryan (UK - Male)' },
    { value: 'he-IL-AvriNeural', label: 'Avri (HE - אברי)' },
    { value: 'he-IL-HilaNeural', label: 'Hila (HE - הילה)' },
    { value: 'de-DE-KatjaNeural', label: 'Katja (DE - Female)' },
    { value: 'de-DE-ConradNeural', label: 'Conrad (DE - Male)' },
    { value: 'fr-FR-DeniseNeural', label: 'Denise (FR - Female)' },
    { value: 'fr-FR-HenriNeural', label: 'Henri (FR - Male)' },
    { value: 'es-ES-ElviraNeural', label: 'Elvira (ES - Female)' },
    { value: 'es-ES-AlvaroNeural', label: 'Alvaro (ES - Male)' }
  ],
  'silero': [
    { value: 'eugene', label: i18n.t('auto__silero_ru__f99bbd') },
    { value: 'aidar', label: i18n.t('auto__silero_ru__608b29') },
    { value: 'baya', label: i18n.t('auto__silero_ru__d225bb') },
    { value: 'kseniya', label: i18n.t('auto__silero_ru__806161') },
    { value: 'xenia', label: i18n.t('auto__v2_silero_ru__f4517c') },
    { value: 'random', label: i18n.t('auto__silero_ru__fbfae5') }
  ]
};

function getFriendlyVoiceName(system, voice) {
  if (system === 'edge-tts') {
    const found = ADMIN_VOICE_MAP['edge-tts'].find(v => v.value === voice);
    return found ? `Edge: ${found.label}` : `Edge (${voice})`;
  }
  if (system === 'silero') {
    const found = ADMIN_VOICE_MAP['silero'].find(v => v.value === voice);
    return found ? found.label : `Silero (${voice})`;
  }
  if (system === 'gtts') {
    const found = ADMIN_VOICE_MAP['gtts'].find(v => v.value === voice);
    return found ? found.label : `Google TTS (${voice})`;
  }
  if (system === 'browseri18n.t('auto__return_voice__265617')По умолчанию'})`;
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
        .map(v => ({ value: v.name, label: `[${v.lang}] ${v.name}` }));
      
      if (ADMIN_VOICE_MAP['browser'].length === 0) {
        ADMIN_VOICE_MAP['browser'].push({ value: 'default', label: i18n.t('auto___6677a9') });
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
      ttsNotify(i18n.t('auto___3eeddc'), 'warning');
      return;
    }

    const engine = engineSelect.value;
    const voice = voiceSelect.value;

    if (engine === 'browser') {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const cleanText = text.replace(/<[^>]*>/g, '').replace(/[*_`#]/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        const voices = window.speechSynthesis.getVoices();
        const selectedVoice = voices.find(v => v.name === voice);
        if (selectedVoice) {
          utterance.voice = selectedVoice;
          if (selectedVoice.lang) {
            utterance.lang = selectedVoice.lang;
          }
        }
        
        ttsStatus.classList.remove('d-none');
        statusText.textContent = i18n.t('auto___0bd0fc');
        
        utterance.onend = () => ttsStatus.classList.add('d-none');
        utterance.onerror = () => ttsStatus.classList.add('d-none');
        
        window.speechSynthesis.speak(utterance);
        playerContainer.classList.add('d-none');
      } else {
        ttsNotify(i18n.t('auto__web_speech_api_542e33'), 'danger');
      }
      return;
    }

    // Server-side synthesis
    ttsStatus.classList.remove('d-none');
    statusText.textContent = i18n.t('auto___dd2293');
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
        statusText.textContent = i18n.t('auto___57cd75');
        btnSpeak.disabled = false;
        setTimeout(() => ttsStatus.classList.add('d-none'), 3000);
      };

    } catch (err) {
      console.error(err);
      statusText.textContent = i18n.t('auto___c00aca');
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
        ttsNotify(i18n.t('auto__tts__141e91'), 'success');
      } else {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || i18n.t('auto___65e520'));
      }
    } catch (err) {
      console.error(err);
      ttsNotify(i18n.t('auto___6eda4f') + err.message, 'danger');
    } finally {
      btnSave.disabled = false;
      btnSave.innerHTML = originalText;
    }
  });
}

window.initTtsTab = initTtsTab;
