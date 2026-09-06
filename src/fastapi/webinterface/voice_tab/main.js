// ── VOICE_TAB MAIN.JS ───────────────────────────────────────────────────────

(function () {
  let isInitialized = false;
  let tabMediaRecorder = null;
  let tabAudioChunks = [];
  let tabRecordingStartTime = 0;
  let tabTimerInterval = null;
  let lastAnalysisData = null;
  let lastAudioFilename = 'voice_recording';

  function initVoiceTab() {
    if (isInitialized) return;
    isInitialized = true;
    setupEventListeners();
  }

  window.initVoiceTab = initVoiceTab;

  function setupEventListeners() {
    const recordBtn = document.getElementById('btn-vtab-record-toggle');
    const cancelBtn = document.getElementById('btn-vtab-record-cancel');
    const fileInput = document.getElementById('vtab-file-input');
    const dropzone = document.getElementById('vtab-dropzone');
    const saveRagBtn = document.getElementById('vtab-btn-save-rag');

    if (recordBtn) {
      recordBtn.addEventListener('click', toggleRecording);
    }
    if (cancelBtn) {
      cancelBtn.addEventListener('click', cancelRecording);
    }
    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          const file = e.target.files[0];
          analyzeAudioBlob(file, file.name);
          fileInput.value = '';
        }
      });
    }
    if (dropzone) {
      ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.add('border-info', 'bg-info', 'bg-opacity-10');
        }, false);
      });

      ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.remove('border-info', 'bg-info', 'bg-opacity-10');
        }, false);
      });

      dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
          const file = dt.files[0];
          analyzeAudioBlob(file, file.name);
        }
      }, false);
    }
    if (saveRagBtn) {
      saveRagBtn.addEventListener('click', saveResultToRag);
    }
  }

  async function toggleRecording() {
    if (tabMediaRecorder && tabMediaRecorder.state === 'recording') {
      stopRecording();
    } else {
      await startRecording();
    }
  }

  async function startRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Доступ к микрофону не поддерживается в вашем браузере.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      tabAudioChunks = [];

      let options = {};
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        options = { mimeType: 'audio/webm;codecs=opus' };
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        options = { mimeType: 'audio/ogg;codecs=opus' };
      }

      tabMediaRecorder = new MediaRecorder(stream, options);

      tabMediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          tabAudioChunks.push(e.data);
        }
      };

      tabMediaRecorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        if (tabAudioChunks.length > 0) {
          const mime = tabMediaRecorder.mimeType || 'audio/webm';
          const blob = new Blob(tabAudioChunks, { type: mime });
          const fname = `voice_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '_')}.webm`;
          analyzeAudioBlob(blob, fname);
        }
      };

      tabMediaRecorder.start(250);
      tabRecordingStartTime = Date.now();

      // UI state update
      const recordBtn = document.getElementById('btn-vtab-record-toggle');
      const cancelBtn = document.getElementById('btn-vtab-record-cancel');
      const btnText = document.getElementById('vtab-record-btn-text');
      const statusLabel = document.getElementById('vtab-record-status-label');
      const timerBadge = document.getElementById('vtab-record-timer');
      const micCircle = document.getElementById('vtab-mic-circle');

      if (recordBtn) {
        recordBtn.className = 'btn btn-danger px-4 py-2 rounded-pill fw-bold shadow-sm';
      }
      if (btnText) btnText.textContent = 'Остановить и разобрать';
      if (cancelBtn) cancelBtn.classList.remove('d-none');
      if (statusLabel) statusLabel.textContent = 'Идет запись речи...';
      if (timerBadge) {
        timerBadge.classList.remove('d-none');
        timerBadge.textContent = '00:00';
      }
      if (micCircle) {
        micCircle.classList.add('bg-danger', 'bg-opacity-25');
        micCircle.style.transform = 'scale(1.1)';
      }

      clearInterval(tabTimerInterval);
      tabTimerInterval = setInterval(() => {
        const elapsedSec = Math.floor((Date.now() - tabRecordingStartTime) / 1000);
        const m = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
        const s = String(elapsedSec % 60).padStart(2, '0');
        if (timerBadge) timerBadge.textContent = `${m}:${s}`;
      }, 500);

    } catch (err) {
      console.error('Microphone error:', err);
      alert(`Не удалось включить микрофон: ${err.message}`);
    }
  }

  function stopRecording() {
    resetRecordingUi();
    if (tabMediaRecorder && tabMediaRecorder.state === 'recording') {
      tabMediaRecorder.stop();
    }
  }

  function cancelRecording() {
    resetRecordingUi();
    if (tabMediaRecorder) {
      if (tabMediaRecorder.state === 'recording') {
        tabMediaRecorder.onstop = null;
        tabMediaRecorder.stop();
      }
      tabAudioChunks = [];
    }
  }

  function resetRecordingUi() {
    clearInterval(tabTimerInterval);
    const cancelBtn = document.getElementById('btn-vtab-record-cancel');
    const btnText = document.getElementById('vtab-record-btn-text');
    const statusLabel = document.getElementById('vtab-record-status-label');
    const timerBadge = document.getElementById('vtab-record-timer');
    const micCircle = document.getElementById('vtab-mic-circle');

    if (cancelBtn) cancelBtn.classList.add('d-none');
    if (btnText) btnText.textContent = 'Начать запись';
    if (statusLabel) statusLabel.textContent = 'Нажмите для начала записи';
    if (timerBadge) timerBadge.classList.add('d-none');
    if (micCircle) {
      micCircle.classList.remove('bg-danger', 'bg-opacity-25');
      micCircle.style.transform = 'scale(1)';
    }
  }

  async function analyzeAudioBlob(audioBlob, filename) {
    lastAudioFilename = filename;
    const playerContainer = document.getElementById('vtab-player-container');
    const audioElement = document.getElementById('vtab-audio-element');
    const filenameLabel = document.getElementById('vtab-current-filename');
    const loadingState = document.getElementById('vtab-loading');
    const emptyState = document.getElementById('vtab-empty-state');
    const analysisContent = document.getElementById('vtab-analysis-content');
    const saveRagBtn = document.getElementById('vtab-btn-save-rag');

    // Show audio player
    if (playerContainer && audioElement) {
      const audioUrl = URL.createObjectURL(audioBlob);
      audioElement.src = audioUrl;
      if (filenameLabel) filenameLabel.textContent = filename;
      playerContainer.classList.remove('d-none');
    }

    if (emptyState) emptyState.classList.add('d-none');
    if (analysisContent) analysisContent.classList.add('d-none');
    if (loadingState) loadingState.classList.remove('d-none');
    if (saveRagBtn) saveRagBtn.classList.add('d-none');

    const model = document.getElementById('vtab-model-select')?.value || 'gemini-2.5-flash';
    const lang = document.getElementById('vtab-lang-select')?.value || 'ru';
    const apiKey = document.getElementById('vtab-api-key')?.value || '';

    const formData = new FormData();
    formData.append('file', audioBlob, filename);
    formData.append('model', model);
    formData.append('language', lang);
    if (apiKey) formData.append('api_key', apiKey);

    try {
      const res = await fetch('/api/audio/diarize', {
        method: 'POST',
        body: formData,
      });

      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || 'Analysis error');

      lastAnalysisData = json.data || {};
      renderResults(lastAnalysisData);
      if (saveRagBtn) saveRagBtn.classList.remove('d-none');
    } catch (err) {
      console.error('[VoiceTab] Diarization failed:', err);
      if (analysisContent) {
        analysisContent.innerHTML = `
          <div class="alert alert-danger p-3 mb-0">
            <h6 class="fw-bold mb-1"><i class="bi bi-exclamation-triangle-fill me-2"></i>Ошибка анализа аудио</h6>
            <p class="mb-0 small">${escapeHtml(err.message)}</p>
          </div>
        `;
        analysisContent.classList.remove('d-none');
      }
    } finally {
      if (loadingState) loadingState.classList.add('d-none');
    }
  }

  function renderResults(data) {
    const analysisContent = document.getElementById('vtab-analysis-content');
    if (!analysisContent) return;

    const summary = data.summary || '';
    const keyPoints = data.key_points || [];
    const actionItems = data.action_items || [];
    const transcript = data.transcript || [];
    const speakers = data.speakers || [];

    const speakerColors = [
      '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'
    ];

    let keyPointsHtml = '';
    if (keyPoints.length > 0) {
      keyPointsHtml = `
        <div class="card bg-body-tertiary border-0 mb-3 shadow-sm">
          <div class="card-body p-3">
            <h6 class="fw-bold text-info mb-2"><i class="bi bi-key-fill me-2"></i>Ключевые темы и решения</h6>
            <ul class="mb-0 ps-3 small text-body-secondary">
              ${keyPoints.map(kp => `<li class="mb-1">${escapeHtml(kp)}</li>`).join('')}
            </ul>
          </div>
        </div>
      `;
    }

    let actionItemsHtml = '';
    if (actionItems.length > 0) {
      actionItemsHtml = `
        <div class="card bg-body-tertiary border-0 mb-3 shadow-sm">
          <div class="card-body p-3">
            <h6 class="fw-bold text-success mb-2"><i class="bi bi-check2-square me-2"></i>Задачи и договоренности (Action Items)</h6>
            <ul class="list-unstyled mb-0 small">
              ${actionItems.map(ai => `
                <li class="d-flex align-items-start gap-2 mb-1">
                  <span class="badge bg-success bg-opacity-25 text-success font-monospace">TODO</span>
                  <span>${escapeHtml(ai)}</span>
                </li>
              `).join('')}
            </ul>
          </div>
        </div>
      `;
    }

    let transcriptHtml = '';
    if (transcript.length > 0) {
      transcriptHtml = `
        <div class="card bg-body-tertiary border-0 shadow-sm">
          <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center py-2">
            <span class="fw-semibold small"><i class="bi bi-chat-quote-fill me-2 text-warning"></i>Стенограмма по собеседникам (${speakers.length || 2} участников)</span>
          </div>
          <div class="card-body p-3 d-flex flex-column gap-2" style="max-height: 400px; overflow-y: auto;">
            ${transcript.map((t, idx) => {
              const sp = t.speaker || `Собеседник ${idx % 2 + 1}`;
              const col = speakerColors[idx % speakerColors.length];
              const ts = t.timestamp ? `<span class="badge bg-dark text-muted font-monospace">${escapeHtml(t.timestamp)}</span>` : '';
              return `
                <div class="p-2 rounded bg-body border-start border-3 shadow-sm" style="border-left-color: ${col} !important;">
                  <div class="d-flex align-items-center justify-content-between mb-1">
                    <span class="fw-bold small" style="color: ${col};"><i class="bi bi-person-fill me-1"></i>${escapeHtml(sp)}</span>
                    ${ts}
                  </div>
                  <div class="small text-body">${escapeHtml(t.text)}</div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    analysisContent.innerHTML = `
      ${summary ? `
        <div class="alert alert-primary mb-3 shadow-sm">
          <h6 class="fw-bold mb-1"><i class="bi bi-card-text me-2"></i>Краткая сводка (Executive Summary)</h6>
          <p class="mb-0 small">${escapeHtml(summary)}</p>
        </div>
      ` : ''}
      ${keyPointsHtml}
      ${actionItemsHtml}
      ${transcriptHtml}
    `;

    analysisContent.classList.remove('d-none');
  }

  async function saveResultToRag() {
    if (!lastAnalysisData) return;

    try {
      const res = await fetch('/api/audio/save-to-rag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `Голосовая запись: ${lastAudioFilename}`,
          summary: lastAnalysisData.summary || '',
          transcript: lastAnalysisData.transcript || [],
          key_points: lastAnalysisData.key_points || [],
          action_items: lastAnalysisData.action_items || [],
          markdown_report: lastAnalysisData.markdown_report || '',
        }),
      });

      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || 'Save error');

      alert(`✓ ${json.message || 'Разговор успешно сохранен в базу знаний RAG!'}`);
    } catch (err) {
      console.error('[VoiceTab] Failed to save in RAG:', err);
      alert(`Ошибка сохранения в RAG: ${err.message}`);
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initVoiceTab);
  } else {
    initVoiceTab();
  }
})();
