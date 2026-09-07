/**
 * =============================================================================
 * Process Name: Workspace Multi-RAG Pipeline and Search
 * =============================================================================
 * Description:
 *   Handles workspace storage file checklist, cleaning and TF-IDF build
 *   pipeline, semantic search, and quick upload to user storage.
 *
 * File: userRagPipeline.js
 * Project: AI Breadboard
 * Module: RAGTab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

import { formatBytes, escapeHtml } from './utils.js';
import { getActiveUserRagId, loadUserRags, selectUserRag } from './userRagCollections.js';

/**
 * Fetch files from user storage and render checkbox selection list.
 *
 * @param {string[]} attachedFiles - Array of filenames currently attached to this collection.
 * @returns {Promise<void>}
 */
export async function loadUserStorageFiles(attachedFiles) {
  const checklistContainer = document.getElementById('user-rag-files-checklist');
  if (!checklistContainer) return;

  try {
    const res = await fetch('/api/user/files?subfolder=files');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const files = data.files || [];

    if (files.length === 0) {
      checklistContainer.innerHTML = `
        <div class="text-muted small p-2 text-center">
          В личном хранилище нет файлов.<br>Нажмите «Загрузить файлы» ниже.
        </div>
      `;
      return;
    }

    checklistContainer.innerHTML = files.map(f => {
      const isChecked = attachedFiles.length === 0 || attachedFiles.includes(f.name);
      return `
        <label class="d-flex align-items-center justify-content-between p-1 px-2 rounded hover-bg border-bottom border-light-subtle small cursor-pointer">
          <div class="d-flex align-items-center gap-2">
            <input class="form-check-input mt-0" type="checkbox" value="${escapeHtml(f.name)}" ${isChecked ? 'checked' : ''}>
            <span class="text-truncate font-monospace" style="max-width: 280px;">${escapeHtml(f.name)}</span>
          </div>
          <span class="text-muted small">${formatBytes(f.size_bytes)}</span>
        </label>
      `;
    }).join('');
  } catch (err) {
    checklistContainer.innerHTML = `<div class="alert alert-danger p-2 small mb-0">Ошибка списка файлов: ${escapeHtml(err.message)}</div>`;
  }
}

/**
 * Build active collection index through cleaner and TF-IDF pipeline.
 *
 * @returns {Promise<void>}
 */
export async function buildActiveUserRag() {
  const activeUserRagId = getActiveUserRagId();
  if (!activeUserRagId) return;

  const btn = document.getElementById('btn-build-active-rag');
  const statusAlert = document.getElementById('user-rag-build-status-alert');
  const checkboxes = document.querySelectorAll('#user-rag-files-checklist input[type="checkbox"]:checked');
  const selectedFiles = Array.from(checkboxes).map(cb => cb.value);

  if (btn) btn.disabled = true;
  if (statusAlert) {
    statusAlert.className = 'alert alert-info p-2 small mt-2 mb-0 d-block';
    statusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Выполняется очистка (rag_cleaner) и индексация документов...';
  }

  try {
    const res = await fetch(`/api/user/rags/${encodeURIComponent(activeUserRagId)}/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        files: selectedFiles.length > 0 ? selectedFiles : null,
        provider: 'local_tfidf'
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    if (statusAlert) {
      statusAlert.className = 'alert alert-success p-2 small mt-2 mb-0 d-block';
      statusAlert.innerHTML = `✅ Успешно! Создано <strong>${data.chunks_count}</strong> чанков из <strong>${data.processed_files?.length || 0}</strong> файлов.`;
    }

    await loadUserRags();
  } catch (err) {
    if (statusAlert) {
      statusAlert.className = 'alert alert-danger p-2 small mt-2 mb-0 d-block';
      statusAlert.textContent = `Ошибка сборки RAG: ${err.message}`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Perform semantic search in the active workspace collection.
 *
 * @returns {Promise<void>}
 */
export async function executeActiveUserRagSearch() {
  const activeUserRagId = getActiveUserRagId();
  if (!activeUserRagId) return;

  const queryInput = document.getElementById('active-rag-search-query');
  const resultsContainer = document.getElementById('active-rag-search-results');
  const btn = document.getElementById('btn-active-rag-search');
  const query = queryInput?.value.trim();

  if (!query) return;
  if (btn) btn.disabled = true;
  if (resultsContainer) {
    resultsContainer.innerHTML = '<div class="text-center text-muted small py-3"><span class="spinner-border spinner-border-sm me-1"></span>Поиск...</div>';
  }

  try {
    const res = await fetch(`/api/user/rags/${encodeURIComponent(activeUserRagId)}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        top_k: 5,
        min_score: 0.0
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    const results = data.results || [];
    if (results.length === 0) {
      resultsContainer.innerHTML = '<div class="text-center text-muted small py-3">Ничего не найдено по данному запросу.</div>';
      return;
    }

    resultsContainer.innerHTML = results.map((item) => {
      const scorePercent = Math.round((item.score || 0) * 100);
      return `
        <div class="card mb-2 border border-secondary-subtle bg-body">
          <div class="card-header py-1 px-2 d-flex justify-content-between align-items-center bg-body-tertiary">
            <span class="small fw-semibold text-truncate" style="max-width: 70%;">
              <i class="bi bi-file-earmark-text text-primary me-1"></i> ${escapeHtml(item.source_file || '')}
            </span>
            <span class="badge bg-primary-subtle text-primary border border-primary-subtle">${scorePercent}% match</span>
          </div>
          <div class="card-body p-2 small">
            <div class="text-secondary font-monospace" style="font-size: 0.8rem; white-space: pre-wrap;">${escapeHtml(item.text)}</div>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    if (resultsContainer) {
      resultsContainer.innerHTML = `<div class="alert alert-danger p-2 small mb-0">Ошибка поиска: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Handle quick file upload directly into user workspace storage.
 *
 * @param {Event} event - Input change event.
 * @returns {Promise<void>}
 */
export async function handleQuickUploadToUserStorage(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;

  const statusAlert = document.getElementById('user-rag-build-status-alert');
  if (statusAlert) {
    statusAlert.className = 'alert alert-info p-2 small mt-2 mb-0 d-block';
    statusAlert.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Загрузка ${files.length} файл(ов)...`;
  }

  try {
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('subfolder', 'files');

      const res = await fetch('/api/user/files/upload', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error(`Ошибка загрузки ${file.name}`);
    }

    if (statusAlert) {
      statusAlert.className = 'alert alert-success p-2 small mt-2 mb-0 d-block';
      statusAlert.innerHTML = `Загружено <strong>${files.length}</strong> файлов.`;
    }

    const activeUserRagId = getActiveUserRagId();
    if (activeUserRagId) {
      selectUserRag(activeUserRagId);
    }
  } catch (err) {
    if (statusAlert) {
      statusAlert.className = 'alert alert-danger p-2 small mt-2 mb-0 d-block';
      statusAlert.textContent = err.message;
    }
  } finally {
    event.target.value = '';
  }
}
