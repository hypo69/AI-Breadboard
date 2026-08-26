// Instructions Tab - UI Logic
// Инициализируется через window.initInstructionsTab() из admin/main.js

'use strict';

import { initI18n, switchLang, applyTranslations } from '../js/i18n.js';

window.switchLang = switchLang;
window.applyTranslations = applyTranslations;

// ── Helpers ────────────────────────────────────────────────────────────────

function adminFetch(url, options = {}) {
  return window.api
    ? window.api.fetch(url, options)
    : fetch(url, options).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      });
}

function notify(msg, type = 'info') {
  if (typeof showNotification === 'function') {
    showNotification(msg, type);
  } else {
    console.log(`[${type}] ${msg}`);
  }
}

// ── Mode Management ───────────────────────────────────────────────────────
let currentMode = 'chat';

function switchMode(mode) {
  currentMode = mode;
  document.getElementById('mode-chat').classList.toggle('active', mode === 'chat');
  document.getElementById('mode-narrator').classList.toggle('active', mode === 'narrator');

  // Обновить заголовок редактора
  const modeLabel = mode === 'chat' ? '💬 Chat' : '🎙️ Narrator';
  const editorTitle = document.getElementById('editor-mode-label');
  if (editorTitle) editorTitle.textContent = modeLabel;

  loadInstruction();
  refreshVersions();
}

// ── Instructions API ──────────────────────────────────────────────────────
async function loadInstruction() {
  try {
    const data = await adminFetch(`/api/admin/instructions?mode=${currentMode}`);
    const editor = document.getElementById('instruction-editor');
    if (data && data.content !== undefined) {
      editor.value = data.content;
    } else {
      editor.value = '';
    }
    updateStats();
    const fileInfo = document.getElementById('active-file-info');
    if (fileInfo && data.file) {
      fileInfo.textContent = data.file;
    }
  } catch (e) {
    notify('Ошибка загрузки инструкции: ' + e.message, 'danger');
    document.getElementById('instruction-editor').value = '';
  }
}

async function saveInstruction() {
  const content = document.getElementById('instruction-editor').value.trim();
  if (!content) {
    notify('Инструкция не может быть пустой', 'warning');
    return;
  }

  const btn = document.getElementById('btn-save');
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Сохранение...';

  try {
    const data = await adminFetch('/api/admin/instructions/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: currentMode, content })
    });
    notify(`Инструкция сохранена: ${data.version || ''}`, 'success');
    await refreshVersions();
  } catch (e) {
    notify('Ошибка сохранения: ' + e.message, 'danger');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

async function checkInModel() {
  const content = document.getElementById('instruction-editor').value.trim();
  const prompt = "Привет! Подтверди, что ты получил инструкцию и готов к работе. Ответь только: 'Понял, готов к работе!'";

  const btn = document.getElementById('btn-check-model');
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Проверка...';

  try {
    const result = await adminFetch('/api/admin/instructions/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: currentMode, prompt, instruction: content })
    });

    const statusEl = document.getElementById('token-preview');
    let tokenInfo = '';
    if (result.token_count) {
      tokenInfo = `<br>Использовано токенов: ${result.token_count}`;
    }

    if (result.response) {
      statusEl.innerHTML = `<strong>Ответ модели:</strong><br>${escapeHtml(result.response)}${tokenInfo}`;
      notify('Проверка завершена', 'success');
    } else {
      statusEl.innerHTML = 'Ошибка: нет ответа от модели';
      notify('Ошибка проверки', 'danger');
    }
  } catch (e) {
    document.getElementById('token-preview').innerHTML = `<strong class="text-danger">Ошибка проверки: ${e.message}</strong>`;
    notify('Ошибка проверки: ' + e.message, 'danger');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

async function refreshVersions() {
  const list = document.getElementById('versions-list');
  list.innerHTML = '<div class="list-group-item text-muted"><i class="bi bi-hourglass-split"></i> Загрузка...</div>';

  try {
    const data = await adminFetch(`/api/admin/instructions/versions?mode=${currentMode}`);

    if (!data.versions || !data.versions.length) {
      list.innerHTML = '<div class="list-group-item text-muted">Нет сохранённых версий</div>';
      return;
    }

    list.innerHTML = data.versions.map(v => `
      <button type="button"
        class="list-group-item list-group-item-action d-flex justify-content-between align-items-center ${v.is_active ? 'list-group-item-success' : ''}"
        onclick="useVersion('${escapeAttr(v.filename)}', '${escapeAttr(v.mode)}')">
        <div class="me-2 overflow-hidden">
          <div class="d-flex align-items-center gap-2 mb-1">
            <strong>${v.mode === 'chat' ? '💬' : '🎙️'} ${escapeHtml(v.filename)}</strong>
            ${v.is_active ? '<span class="badge bg-success">Активная</span>' : ''}
          </div>
          <small class="text-muted">${new Date(v.created_at).toLocaleString('ru-RU')} · ${v.size} байт</small>
          <div class="text-muted small text-truncate" style="max-width:480px;">${escapeHtml(v.preview || '')}</div>
        </div>
        <i class="bi bi-arrow-right-circle${v.is_active ? '-fill text-success' : ' text-secondary'}"></i>
      </button>
    `).join('');
  } catch (e) {
    list.innerHTML = `<div class="list-group-item text-danger">Ошибка загрузки версий: ${e.message}</div>`;
  }
}

async function useVersion(filename, mode) {
  try {
    await adminFetch('/api/admin/instructions/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, filename })
    });

    if (mode === currentMode) {
      await loadInstruction();
    }
    await refreshVersions();
    notify(`Версия ${filename} активирована`, 'success');
  } catch (e) {
    notify('Ошибка активации: ' + e.message, 'danger');
  }
}

async function previewPrompt() {
  const content = document.getElementById('instruction-editor').value.trim();
  const preview = `
    <strong>Контекст системной инструкции (${currentMode === 'chat' ? '💬 Chat' : '🎙️ Narrator'}):</strong><br>
    <pre style="white-space:pre-wrap;max-height:400px;overflow-y:auto;">${escapeHtml(content.substring(0, 1000))}${content.length > 1000 ? '\n...' : ''}</pre>
    <strong>Тестовый запрос:</strong><br>
    "Привет! Подтверди, что ты получил инструкцию и готов к работе."
  `;

  const modal = new bootstrap.Modal(document.getElementById('prompt-preview-modal'));
  document.getElementById('prompt-preview-content').innerHTML = preview;
  modal.show();
}

// ── Stats ─────────────────────────────────────────────────────────────────
function updateStats() {
  const content = document.getElementById('instruction-editor').value;

  document.getElementById('char-count').textContent = content.length;

  const words = content.trim().split(/\s+/).filter(w => w.length > 0);
  document.getElementById('word-count').textContent = words.length;

  const estimatedTokens = Math.ceil(content.length / 3);
  document.getElementById('token-estimate').textContent = '~' + estimatedTokens;

  return estimatedTokens;
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML.replace(/\n/g, '<br>');
}

function escapeAttr(text) {
  if (!text) return '';
  return text.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ── Initialization ────────────────────────────────────────────────────────
let initialized = false;

async function initInstructionsTab() {
  if (initialized) return;
  initialized = true;

  console.log('[InstructionsTab] Initializing...');

  const savedLang = localStorage.getItem('app_language') || 'ru';
  try {
    await initI18n(savedLang);
    console.log('[InstructionsTab] i18n initialized');
  } catch (e) {
    console.error('[InstructionsTab] i18n init error:', e);
  }

  // Load instruction for current mode
  await loadInstruction();

  // Load versions
  await refreshVersions();

  // Stats on input
  document.getElementById('instruction-editor').addEventListener('input', updateStats);

  try {
    applyTranslations();
  } catch (e) {
    console.error('[InstructionsTab] applyTranslations error:', e);
  }

  console.log('[InstructionsTab] Initialized successfully');
}

// ── Экспорт в window (необходим для inline onclick в HTML при type="module") ──
window.initInstructionsTab = initInstructionsTab;
window.switchMode          = switchMode;
window.saveInstruction     = saveInstruction;
window.checkInModel        = checkInModel;
window.refreshVersions     = refreshVersions;
window.useVersion          = useVersion;
window.previewPrompt       = previewPrompt;